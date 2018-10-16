import os

def path_and_filename(instance, filename):
    file_path = 'keyfiles/keyfile_id_{0}'.format(instance.id)
    if os.path.isfile(file_path):
        os.remove(file_path)
    return file_path

def get_room_url(request, inst):
    prefix = 'https' if request.is_secure() else 'http'
    return "%s://%s.%s/room/%s/" % (prefix, inst.name, settings.DOKKU_DOMAIN, inst.otree_room_name)

