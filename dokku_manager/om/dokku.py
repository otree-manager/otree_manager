from django.conf import settings

from .choices import *

import threading
import subprocess

class ThreadResult:
    def __init__(self, reference=None, returncode=None, result=None, error=None, otree_instance=None):
        self.reference = reference
        self.returncode = returncode
        self.result = result
        self.error = error
        self.otree_instance = otree_instance
        self.when_done()

class ListAppsResult(ThreadResult):
    def when_done(self):
        print('name:', self.reference)
        print('code:', self.returncode)
        print('res: ', self.result)
        print('err:', self.error)

class CreateAppResult(ThreadResult):
    def when_done(self):
        if self.returncode == 1:
            print(self.reference, 'failed')
            return False

        self.otree_instance.app_created = True
        self.otree_instance.save()
        self.otree_instance.refresh_from_dokku()
        print(self.otree_instance.name, 'created')
        self.otree_instance.create_plugin('redis')
        self.otree_instance.create_plugin('postgres')

class UpdateInstanceResult(ThreadResult):
    def get_report_as_dict(self):
        report_dict = {
            'app_dir': '',
            'git_sha': '',
            'deploy_source': '',
            'deployed': False,
        }

        if self.returncode == 0:
            lines = self.result.split('\n')[:-1]
        else:
            lines = self.error.split('\n')

        if lines[0].strip() == "not deployed":
            return report_dict

        report_dict["deployed"] = True

        for line in lines:
            split = [text.strip() for text in line.split(':')]
            if split[0] == 'App dir':
                report_dict['app_dir'] = split[1]
            if split[0] == 'Git sha':
                report_dict['git_sha'] = split[1]
            if split[0] == 'Deploy source':
                report_dict['deploy_source'] = split[1]

        return report_dict

    def when_done(self):
        if self.returncode == 1:
            if self.error.strip() != "not deployed":
                print(self.reference, 'failed')
                print(self.result, self.error)
                return False

        report_dict = self.get_report_as_dict()
        # update instance
        self.otree_instance.git_sha = report_dict['git_sha']
        self.otree_instance.deployed = report_dict['deployed']
        self.otree_instance.deploy_source = report_dict['deploy_source']
        self.otree_instance.app_dir = report_dict['app_dir']
        self.otree_instance.save()

        print(self.otree_instance.name, 'updated')

class CreatePluginResult(ThreadResult):
    def when_done(self):
        if self.returncode == 1:
            print(self.reference, 'failed')
            print(self.error)
            return False

        self.otree_instance.link_plugin(self.reference[7:])
        print(self.otree_instance.name, self.reference, 'succeeded')

class LinkPluginResult(ThreadResult):
    def when_done(self):
        if self.returncode == 1:
            print(self.reference, 'failed')
            print(self.error)
            return False

        print(self.otree_instance.name, self.reference, 'succeeded')


class DokkuManager:
    def run_async(self, cmd_list, name, callback, otree_instance=None):
        def run_in_thread(cmd_list, name, callback, otree_instance):
            proc = subprocess.Popen(cmd_list, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            result, error = proc.communicate()
            result_utf8 = result.decode('utf-8').rstrip()
            error_utf8 = error.decode('utf-8').rstrip()
            return callback(name, proc.returncode, result_utf8, error_utf8, otree_instance)

        thread = threading.Thread(target=run_in_thread, args=(cmd_list, name, callback, otree_instance))
        thread.start()
        return thread

    def list_apps(self):
        return self.run_async(['dokku', 'apps:list', '--quiet'], 'list_apps', ListAppResult)

    def update_instance(self, otree_instance):
        return self.run_async(['dokku', '--quiet', 'apps:report', otree_instance.name], 'update_instance', UpdateInstanceResult, otree_instance)

    def create_app(self, otree_instance):
        return self.run_async(['dokku', '--quiet', 'apps:create', otree_instance.name], 'create_app', CreateAppResult, otree_instance)

    def create_plugin(self, name, otree_instance):
        if name in PLUGINS:
            cmd = "%s:create" % name
            plugin_instance_name = "%s_%s" % (otree_instance.name, name)
            reference = "create_%s" % name

        return self.run_async(['dokku', '--quiet', cmd, plugin_instance_name], reference, CreatePluginResult, otree_instance)

    def link_plugin(self, name, otree_instance):
        if name in PLUGINS:
            cmd = "%s:link" % name
            plugin_instance_name = "%s_%s" % (otree_instance.name, name)
            reference = "link_%s" % name

        return self.run_async(['dokku', '--quiet', cmd, plugin_instance_name, otree_instance.name], reference, LinkPluginResult, otree_instance)