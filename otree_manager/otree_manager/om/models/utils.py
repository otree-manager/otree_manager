import os

def path_and_filename(instance, filename):
    file_path = 'keyfiles/keyfile_id_{0}'.format(instance.id)
    if os.path.isfile(file_path):
        os.remove(file_path)
    return file_path