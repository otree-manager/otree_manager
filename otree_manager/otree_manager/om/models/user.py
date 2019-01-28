from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core import validators
from django.utils.translation import gettext_lazy as _
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from otree_manager.om.utils import path_and_filename
import logging
"""Implements user object and helpers"""

# make channel layer available 'globally'
channel_layer = get_channel_layer()

class CustomUsernameValidator(validators.RegexValidator):
    """Regular expression validator for usernames"""
    regex = r'^[A-Za-z0-9](?:[A-Za-z0-9\-]{0,61}[A-Za-z0-9])?$'
    message = _(
        'Enter a valid username. This value may contain only letters, '
        'numbers, and - characters. It cannot begin or end with a dash (-).'
    )
    flags = 0


class User(AbstractUser):
    """Main User object, extending the AbstractUser class"""
    class Meta:
        app_label = 'om'

    # usernames must be unique, as they are also used for ssh key association by dokku
    username_validator = CustomUsernameValidator()
    username = models.CharField(
        _('username'),
        max_length=63,
        unique=True,
        help_text=_('Required. 63 characters or fewer. Letters, digits and - only.'),
        validators=[username_validator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )

    def __str__(self):
        return "%s %s" % (self.first_name, self.last_name)

    # web socket channel the user last connected to (needed to pass throuh notifications from background processes)
    ws_channel = models.CharField(max_length=255, blank=True)

    # ssh key file details
    public_key_set = models.BooleanField(default=False)
    public_key_file = models.FileField(upload_to=path_and_filename)


    REQUIRED_FIELDS = ['first_name', 'last_name', 'email']

    def remove_public_key(self):
        """Triggers background procress to remove ssh key file"""
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
        """Triggers background procress to set public key file (removes old if one is set)"""
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
