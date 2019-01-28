import os
from django.conf import settings

"""These functions are shared by multiple functions and classes throughout the project"""

# plugins we allow to be created
PLUGINS = ('redis', 'postgres')

def path_and_filename(instance, filename=None):
    """Yields a full path with filename for ssh key file upload handling"""
    
    # Note that filename parameter is set by the file upload form
    # thus we have to make sure the function is defined accordingly.
    # we role our own naming / numbering scheme below and ignore the uploaded file's name
    file_path = 'keyfiles/keyfile_id_{0}'.format(instance.id)
    if os.path.isfile(file_path):
        os.remove(file_path)
    return file_path

def get_room_url(request, inst):
    """Builds oTree room URLs"""
    prefix = 'https' if request.is_secure() else 'http'
    return "%s://%s.%s/room/%s/" % (prefix, inst.name, settings.DOKKU_DOMAIN, inst.otree_room_name)

def command_friendly_kv_pair(dict):
    """Converts a dictionary into a list of key=value pairs for use in subprocess run"""
    # subprocess.run expects parameters to be in the foo=bar format. We build this format here and return a list
    output = []
    for key, value in dict.items():
        output.append('%s=%s' % (key, value))
    return output