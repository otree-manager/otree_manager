from django.db import models
from django.contrib.auth.models import AbstractUser
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .utils import path_and_filename

channel_layer = get_channel_layer()


class User(AbstractUser):
    class Meta:
        app_label = 'om'

    def __str__(self):
        return "%s %s" % (self.first_name, self.last_name)

    ws_channel = models.CharField(max_length=255, blank=True)

    public_key_set = models.BooleanField(default=False)
    public_key_file = models.FileField(upload_to=path_and_filename)

    REQUIRED_FIELDS = ['first_name', 'last_name', 'email']

    def remove_public_key(self):
        async_to_sync(channel_layer.send)(
            "otree_manager_tasks",
            {
                "type": "user.remove.key",
                "user_id": self.id,
                "user_name": self.username,
                "user_verbose_name": self.__str__(),
            },
        )
        self.public_key_set = False
        self.save()

    def set_public_key(self):
        if self.public_key_set:
            self.remove_public_key()

        async_to_sync(channel_layer.send)(
            "otree_manager_tasks",
            {
                "type": "user.add.key",
                "user_id": self.id,
                "user_name": self.username,
                "user_verbose_name": self.__str__(),
                "key_path": self.public_key_file.path,
            },
        )
        self.public_key_set = True
        self.save()

