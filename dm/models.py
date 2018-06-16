from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser
from django.conf import settings

from .choices import *

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

channel_layer = get_channel_layer()


class User(AbstractUser):
    def __str__(self):
        return "%s %s" % (self.first_name, self.last_name)

    ws_channel = models.CharField(max_length=255, blank=True)

class oTreeInstance(models.Model):
    class Meta:
        permissions = (
            ('can_restart', "Can restart the oTree instance"),
            ('can_delete', "Can delete the oTree instance")
        )

    name = models.CharField(
        max_length=32, 
        validators=[
            RegexValidator(regex='^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$', 
                message='name is not suitable',
                code='invalid')
        ]
    )
    owned_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Experimenter")    
    
    deployed = models.BooleanField(default=False)
    git_sha = models.CharField(max_length=200, blank=True)
    deploy_source = models.CharField(max_length=200, blank=True)
    app_dir = models.CharField(max_length=200, blank=True)


    def __str__(self):
        return self.name

    def git_url(self):
        git_url = "dokku@%s:%s" % (settings.DOKKU_DOMAIN, self.name)
        return git_url

    def url(self):
        return "http://%s.%s" % (self.name, settings.DOKKU_DOMAIN)

    def refresh_from_dokku(self, user_id):
        async_to_sync(channel_layer.send)(
            "dokku_tasks",
            {
                "type": "update.app.report",
                "user_id": user_id,
                "instance_name": self.name
            },
        )

    def create_dokku_app(self, user_id):
        async_to_sync(channel_layer.send)(
            "dokku_tasks",
            {
                "type": "create.app",
                "user_id": user_id,
                "instance_name": self.name
            },
        )

    def destroy_dokku_app(self, user_id, delete_self=True):
        async_to_sync(channel_layer.send)(
            "dokku_tasks",
            {
                "type": "destroy.app",
                "user_id": user_id,
                "instance_name": self.name
            },
        )
        num_delete, _ = self.delete()
        



        
