import threading
import subprocess

def run_async(cmd_list, name, callback):
    def run_in_thread(cmd_list, name, callback):
        proc = subprocess.Popen(cmd_list, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        result, error = proc.communicate()
        result_utf8 = result.decode('utf-8').rstrip()
        error_utf8 = error.decode('utf-8').rstrip()
        callback(name, proc.returncode, result_utf8, error_utf8)
        return

    thread = threading.Thread(target=run_in_thread, args=(cmd_list, name, callback))
    thread.start()
    return thread

def when_done(name=None, returncode=None, result=None, error=None):
    print('name:', name)
    print('code:', returncode)
    print('res: ', result)
    print('err:', error)

if __name__ == '__main__':
    run_async(['dokku', 'apps:list', '--quiet'], 'list_apps', when_done)
    print('this has terminated!')