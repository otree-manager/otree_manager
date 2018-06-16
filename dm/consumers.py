from channels.consumer import SyncConsumer
from channels.generic.websocket import WebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import async_to_sync

from .models import User, oTreeInstance
from .choices import PLUGINS

import json
import time
import subprocess

class Notifications(WebsocketConsumer):
    def connect(self):
        self.accept()
        self.scope["user"].ws_channel = self.channel_name
        self.scope["user"].save()

    def disconnect(self, close_code):
        self.scope["user"].ws_channel = ''

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        action = text_data_json['action']
        message = text_data_json['message']

        #if action == 'run' and message == "long_task":
        #    async_to_sync(self.channel_layer.send)(
        #        "long_task",
        #        {
        #            "type": "test.print",
        #            "user_id": self.scope["user"].id,
        #        },
        #    )

    def ws_forward(self, event):
        """Forwards a message from a background task (channel layer) to the user through websocket"""
        self.send(json.dumps(event))

 
class Dokku_Tasks(SyncConsumer):
    """Handles all dokku related tasks on a background worker"""
    def create_app(self, event):
        print('received create app task')

        proc = subprocess.run(['dokku', '--quiet', 'apps:create', event["instance_name"]])
        if proc.returncode != 0:
            result = 'error'
            message = "An error occured while creating %s." % event["instance_name"]
            
            # notify user of error then return
            self._notify_user(event["user_id"], result, message)
            return False

        # success
        result = 'success'
        message = "App %s was created successfully. <br/>Databases will now be created and linked." % event["instance_name"]

        self._notify_user(event["user_id"], result, message)

        # create plugins
        async_to_sync(self.channel_layer.send)("dokku_tasks", {
            'type': 'create_plugin',
            'instance_name': event["instance_name"],
            'user_id': event["user_id"],
            'plugin_name': 'redis'
        })
        async_to_sync(self.channel_layer.send)("dokku_tasks", {
            'type': 'create_plugin',
            'instance_name': event["instance_name"],
            'user_id': event["user_id"],
            'plugin_name': 'postgres'
        })


    def update_app_report(self, event):
        proc = subprocess.run(['dokku', '--quiet', 'apps:report', event["instance_name"]], 
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
        report_dict = {
            'app_dir': '',
            'git_sha': '',
            'deploy_source': '',
            'deployed': False,
        }

        if proc.returncode == 0:
            lines = proc.stdout.decode('utf-8').split('\n')[:-1]
        else:
            lines = proc.stderr.decode('utf-8').split('\n')

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
        otree_instance = oTreeInstance.objects.get(name=event["instance_name"])
        otree_instance.git_sha = report_dict['git_sha']
        otree_instance.deployed = report_dict['deployed']
        otree_instance.deploy_source = report_dict['deploy_source']
        otree_instance.app_dir = report_dict['app_dir']
        otree_instance.save()

        time.sleep(2)

        self._push_report(event["user_id"], report_dict)



    def destroy_app(self, event):
        print('received destroy app task')
        proc = subprocess.run(['dokku', '--quiet', '--force', 'apps:destroy', event["instance_name"]])
        if proc.returncode != 0:
            result = 'error'
            message = "An error occured while deleting %s." % event["instance_name"]
            # notify user of error then return
            self._notify_user(event["user_id"], result, message)
            return False

        # success
        result = 'success'
        message = "App %s was destroyed successfully. <br/>Databases will now be removed." % event["instance_name"]

        self._notify_user(event["user_id"], result, message)

        # destroy plugins
        async_to_sync(self.channel_layer.send)("dokku_tasks", {
            'type': 'destroy_plugin',
            'instance_name': event["instance_name"],
            'user_id': event["user_id"],
            'plugin_name': 'redis'
        })
        async_to_sync(self.channel_layer.send)("dokku_tasks", {
            'type': 'destroy_plugin',
            'instance_name': event["instance_name"],
            'user_id': event["user_id"],
            'plugin_name': 'postgres'
        }) 


    def create_plugin(self, event):
        print('received create plugins event')

        if not event['plugin_name'] in PLUGINS:
            return False

        cmd = "%s:create" % event["plugin_name"]
        plugin_name = "%s_%s" % (event["instance_name"], event["plugin_name"])

        proc = subprocess.run(['dokku', '--quiet', cmd, plugin_name])
        if proc.returncode != 0:
            result = 'error'
            message = "An error occured while creating plugin %s." % plugin_name

            # notify user through websocket
            self._notify_user(event["user_id"], result, message)
            return False

        # if created successfully, we link it
        async_to_sync(self.channel_layer.send)("dokku_tasks", {
            'type': 'link_plugin',
            'instance_name': event["instance_name"],
            'user_id': event["user_id"],
            'plugin_name': event['plugin_name']
        })


    def link_plugin(self, event):
        print('received link plugin event')

        if not event['plugin_name'] in PLUGINS:
            return False

        cmd = "%s:link" % event["plugin_name"]
        plugin_name = "%s_%s" % (event["instance_name"], event["plugin_name"])

        proc = subprocess.run(['dokku', '--quiet', cmd, plugin_name, event["instance_name"]])
        if proc.returncode == 0:
            result = 'success'
            message = "Plugin %s has been created and linked to %s successfully." % (plugin_name, event["instance_name"])
        else:
            result = 'error'
            message = "An error occured while linking plugin %s to %s." % (plugin_name, event["instance_name"])

        # notify user through websocket
        self._notify_user(event["user_id"], result, message)


    def destroy_plugin(self, event):
        print('received destroy plugin event')

        if not event['plugin_name'] in PLUGINS:
            return False

        cmd = "%s:destroy" % event["plugin_name"]
        plugin_name = "%s_%s" % (event["instance_name"], event["plugin_name"])

        proc = subprocess.run(['dokku', '--quiet', '--force', cmd, plugin_name])
        if proc.returncode == 0:
            result = 'success'
            message = "Plugin %s has been destroyed successfully." % plugin_name
        else:
            result = 'error'
            message = "An error occured while destroying plugin %s." % plugin_name

        # notify user through websocket
        self._notify_user(event["user_id"], result, message)



    def _notify_user(self, user_id, result, message):
        #print(user_id, result, message)
        user = User.objects.get(id=user_id)
        async_to_sync(self.channel_layer.send)(user.ws_channel, {
            'type': 'ws.forward', 
            'kind': 'notification', 
            'result': result, 
            'message': message
        })

    def _push_report(self, user_id, report_dict):
        print(user_id, report_dict)
        user = User.objects.get(id=user_id)
        async_to_sync(self.channel_layer.send)(user.ws_channel, {
            'type': 'ws.forward', 
            'kind': 'report', 
            'report': report_dict
        })