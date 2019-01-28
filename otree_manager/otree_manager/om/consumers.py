from channels.consumer import SyncConsumer
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from .models import User, OTreeInstance
from .utils import PLUGINS, command_friendly_kv_pair
import json
import time
import subprocess

"""
This file implements the two consumer types. One is for websockets, the other for dokku background tasks.
"""

class Notifications(WebsocketConsumer):
    def connect(self):
        """On connect, store the websocket channel for each user"""
        self.accept()
        self.scope["user"].ws_channel = self.channel_name
        self.scope["user"].save()

    def disconnect(self, close_code):
        """On disconnect, free up the channel variable"""
        self.scope["user"].ws_channel = ''

    def ws_forward(self, event):
        """Forwards a message from a background task (channel layer) to the user through websocket"""
        self.send(json.dumps(event))


class OTree_Manager_Tasks(SyncConsumer):
    """Handles all dokku related tasks on a background worker"""

    def create_app(self, event):
        """Creates a new oTree container with plugins and correct scaling"""
        
        print('received create app task')
        proc = subprocess.run(['dokku', '--quiet', 'apps:create', event["instance_name"]])
        if proc.returncode != 0:
            # notify user of error then return
            self._notify_user(event, "create_app", proc.returncode)
            return False

        # success
        self._notify_user(event, "create_app", proc.returncode)

        # create plugins
        async_to_sync(self.channel_layer.send)("otree_manager_tasks", {
            'type': 'create_plugin',
            'instance_name': event["instance_name"],
            'user_id': event["user_id"],
            'plugin_name': 'redis'
        })
        async_to_sync(self.channel_layer.send)("otree_manager_tasks", {
            'type': 'create_plugin',
            'instance_name': event["instance_name"],
            'user_id': event["user_id"],
            'plugin_name': 'postgres'
        })
        
        # scale to defaults
        async_to_sync(self.channel_layer.send)("otree_manager_tasks", {
            'type': 'scale_app',
            'instance_name': event["instance_name"],
            'user_id': event["user_id"],
            'var_dict': {
                'web': '1',
                'worker': '1',
            }
        })

        # set default environment
        inst = OTreeInstance.objects.get(name=event["instance_name"])
        inst.set_default_environment()

    def scale_app(self, event):
        """Sets the number of web and worker processes."""
        
        print('received scale app task')
        cmd = ['dokku', '--quiet', 'ps:scale', event["instance_name"]]
        print(cmd)

        # get command friendly foo=bar pairs from dictionary
        cmd.append(command_friendly_kv_pair(event['var_dict']))
        print(cmd)
        
        proc = subprocess.run(cmd)
        if proc.returncode != 0:
            # notify user of error then return
            self._notify_user(event, "scale_app", proc.returncode)
            return False

        # success
        self._notify_user(event, "scale_app", proc.returncode)

    def update_app_report(self, event):
        """Update app details based on dokku information"""
        proc = subprocess.run(['dokku', '--quiet', 'apps:report', event["instance_name"]],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        report_dict = {
            'app_dir': '',
            'git_sha': '',
            'deploy_source': '',
            'deployed': False,
        }

        # successful reports go to stdout, while "not deployed" is considered an error and goes to stderr
        # read both into the same variable so there is no need to differentiate below
        if proc.returncode == 0:
            lines = proc.stdout.decode('utf-8').split('\n')[:-1]
        else:
            lines = proc.stderr.decode('utf-8').split('\n')

        # extract useful data from lines
        if lines[0].strip() != "not deployed":
            report_dict["deployed"] = True
            for line in lines:
                split = [text.strip() for text in line.split(':')]
                if split[0] == 'App dir':
                    report_dict['app_dir'] = split[1]
                if split[0] == 'Git sha':
                    report_dict['git_sha'] = split[1]
                if split[0] == 'Deploy source':
                    report_dict['deploy_source'] = split[1]

        # update instance
        otree_instance = OTreeInstance.objects.get(name=event["instance_name"])
        otree_instance.git_sha = report_dict['git_sha']
        otree_instance.deployed = report_dict['deployed']
        otree_instance.deploy_source = report_dict['deploy_source']
        otree_instance.app_dir = report_dict['app_dir']
        otree_instance.save()

        # possibly remove later
        time.sleep(1)

        # push the report to the current user, updates the values on the detail page if they are not current
        self._push_report(event["user_id"], report_dict)


    def destroy_app(self, event):
        """Delete an app and deconstruct its dependencies"""
        print('received destroy app task')
        proc = subprocess.run(['dokku', '--quiet', '--force', 'apps:destroy', event["instance_name"]])
        if proc.returncode != 0:
            # notify user of error then return
            self._notify_user(event, "destroy_app", proc.returncode)
            return False

        # success
        self._notify_user(event, "destroy_app", proc.returncode)

        # destroy plugins
        async_to_sync(self.channel_layer.send)("otree_manager_tasks", {
            'type': 'destroy_plugin',
            'instance_name': event["instance_name"],
            'user_id': event["user_id"],
            'plugin_name': 'redis'
        })
        async_to_sync(self.channel_layer.send)("otree_manager_tasks", {
            'type': 'destroy_plugin',
            'instance_name': event["instance_name"],
            'user_id': event["user_id"],
            'plugin_name': 'postgres'
        })

    def create_plugin(self, event):
        """Create plugin containers"""
        print('received create plugins event')

        # check if requested plugin is in list of allowed plugins (typically redis and postgres)
        if not event['plugin_name'] in PLUGINS:
            return False

        cmd = "%s:create" % event["plugin_name"]
        plugin_name = "%s_%s" % (event["instance_name"], event["plugin_name"])

        proc = subprocess.run(['dokku', '--quiet', cmd, plugin_name])
        if proc.returncode != 0:
            # notify user through websocket
            self._notify_user(event, "create_plugin", proc.returncode)
            return False

        # if created successfully, we link it
        async_to_sync(self.channel_layer.send)("otree_manager_tasks", {
            'type': 'link_plugin',
            'instance_name': event["instance_name"],
            'user_id': event["user_id"],
            'plugin_name': event['plugin_name']
        })

    def link_plugin(self, event):
        """Links newly created plugins to existing app containers"""
        
        print('received link plugin event')

        # again, do not do anything if plugin type is not allowed
        # actually, this should never happen if linking is called programmatically after creation
        if not event['plugin_name'] in PLUGINS:
            return False

        cmd = "%s:link" % event["plugin_name"]
        plugin_name = "%s_%s" % (event["instance_name"], event["plugin_name"])

        proc = subprocess.run(['dokku', '--quiet', cmd, plugin_name, event["instance_name"]])

        # notify user through websocket
        self._notify_user(event, "link_plugin", proc.returncode)

    def destroy_plugin(self, event):
        """Removes plugins associated with an app if the app is deleted"""

        print('received destroy plugin event')

        # maybe I should rather check if the plugin provided is actually associated with the app
        if not event['plugin_name'] in PLUGINS:
            return False

        cmd = "%s:destroy" % event["plugin_name"]
        plugin_name = "%s_%s" % (event["instance_name"], event["plugin_name"])

        proc = subprocess.run(['dokku', '--quiet', '--force', cmd, plugin_name])

        # notify user through websocket
        self._notify_user(event, 'destroy_plugin', proc.returncode)

    def set_env(self, event):
        """Sets environmental variables from env dictionary"""

        print('received set env command')
        cmd = ['dokku', '--quiet', 'config:set', event["instance_name"]]

        # get command friendly foo=bar pairs from dictionary
        cmd.append(command_friendly_kv_pair(event['var_dict']))

        proc = subprocess.run(cmd, stdout=subprocess.PIPE)

        # notify user through websocket
        self._notify_user(event, 'set_env', proc.returncode)

    def reset_database(self, event):
        """Reset the database"""
        
        print('received reset database task')
        proc = subprocess.run(['dokku', 'run', event["instance_name"], 'otree', 'resetdb', '--noinput'])
        if proc.returncode != 0:
            # notify user of error then return
            self._notify_user(event, "reset_database", proc.returncode)
            return False

        # success
        self._notify_user(event, "reset_database", proc.returncode)

    def restart_app(self, event):
        """Restarts an app"""

        print('received restart task')
        proc = subprocess.run(['dokku', 'ps:restart', event["instance_name"]])
        if proc.returncode != 0:
            # notify user of error then return
            self._notify_user(event, "restart_app", proc.returncode)
            return False

        # success
        self._notify_user(event, "restart_app", proc.returncode)

    def user_add_key(self, event):
        """Adds an ssh key to a user object"""

        print('received user add key event')
        proc = subprocess.run(['sudo', 'dokku', 'ssh-keys:add', event['user_name'], event['key_path']])
        if proc.returncode != 0:
            # notify user of error then return
            self._notify_user(event, "add_key", proc.returncode)
            return False

        # success
        self._notify_user(event, "add_key", proc.returncode)

    def user_remove_key(self, event):
        """Removes an ssh key from a user object"""

        print('received user remove key event')
        proc = subprocess.run(['sudo', 'dokku', 'ssh-keys:remove', event['user_name']])

        if proc.returncode != 0:
            # notify user of error then return
            self._notify_user(event, "remove_key", proc.returncode)
            return False

        # success
        self._notify_user(event, "remove_key", proc.returncode)

    def add_git_permission(self, event):
        """Adds git permissions to a user object"""
        
        print('received user add acl event')
        proc = subprocess.run(['sudo', 'dokku', 'acl:add', event["instance_name"], event['user_name']])
        if proc.returncode != 0:
            # notify user of error then return
            self._notify_user(event, "add_acl", proc.returncode)
            return False

        # success
        self._notify_user(event, "add_acl", proc.returncode)

    def _notify_user(self, event, situation, returncode):
        """Handles notification forwarding from dokku background worker to browser via websockets"""
        
        # Do not forward notifications with user id == -1
        if event['user_id'] == -1:
            return False

        # Prepare nice user-facing (error) messages, rather than passing through raw error codes
        result, message = self._get_message(event, situation, returncode)
        
        # get user object to notify and send notification via websocket channel
        user = User.objects.get(id=event["user_id"])
        async_to_sync(self.channel_layer.send)(user.ws_channel, {
            'type': 'ws.forward',
            'kind': 'notification',
            'result': result,
            'message': message
        })

    def _push_report(self, user_id, report_dict):
        """Forwards app detail updates to detail page"""
        print(user_id, report_dict)
        user = User.objects.get(id=user_id)
        async_to_sync(self.channel_layer.send)(user.ws_channel, {
            'type': 'ws.forward',
            'kind': 'report',
            'report': report_dict
        })

    def _get_message(self, event, situation, returncode):
        """translates internal situation descriptions into user friendly messages"""
        
        # determine report type
        result = "success" if returncode == 0 else "error"

        # messages
        message_dict = {
            "success": {
                "set_env": "Environment variables have been set for {}.",
                "link_plugin": "Plugin {} has been created and linked to {} successfully.",
                "destroy_plugin": "Plugin {} has been destroyed successfully.",
                "create_plugin": "",
                "create_app": "App {} was created successfully.",
                "destroy_app": "App {} was destroyed successfully.",
                "reset_database": "Database for app {} was reset successfully.",
                "restart_app": "App {} was restarted successfully.",
                "scale_app": "Workers for app {} have been adjusted successfully.",
                "add_acl": "{0} has been granted Git permissions for app {1}.",
                "add_key": "Public key for {} has been set.",
                "remove_key": "Public key for {} has been removed.",
            },
            "warning": {

            },
            "error": {
                "set_env": "An error occured while setting environment variables for {}.",
                "link_plugin": "An error occured while linking plugin {} to {}.",
                "destroy_plugin": "An error occured while destroying plugin {}.",
                "create_plugin": "An error occured while creating plugin {}.",
                "create_app": "An error occured while creating {}.",
                "destroy_app": "An error occured while deleting {}.",
                "reset_database": "An error occured while resetting database for {}.",
                "restart_app": "An error occured while restarting {}.",
                "scale_app": "Workers for app {} could not be adjusted.",
                "add_acl": "Git permissions for app {1} could not be granted to {0}.",
                "add_key": "Public key for {} could not be set.",
                "remove_key": "Public key for {} could not be removed.",
            },
            "info": {

            }
        }
        # user friendly messages will be filled with variable information, this dictionary specifies replacements
        string_input_dict = {
            "set_env": (event.get("instance_name", ''),),
            "link_plugin": (event.get("plugin_name", ''), event.get("instance_name", '')),
            "destroy_plugin": (event.get("plugin_name", ''),),
            "create_plugin": (event.get("plugin_name", ''),),
            "create_app": (event.get("instance_name", ''),),
            "destroy_app": (event.get("instance_name", ''),),
            "reset_database": (event.get("instance_name", ''),),
            "restart_app": (event.get("instance_name", ''),),
            "scale_app": (event.get("instance_name", ''),),
            "add_acl": (event.get("user_verbose_name", ''), event.get("instance_name", '')),
            "add_key": (event.get("user_verbose_name", ''),),
            "remove_key": (event.get("user_verbose_name", ''),),
        }
        # take the correct message template, then fill in variable information before returning
        message_template = message_dict[result][situation]
        return result, message_template.format(*string_input_dict[situation])
