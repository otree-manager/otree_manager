from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import User
from django.conf import settings

# Create your models here.
def get_full_name(self):
	return "%s %s" % (self.first_name, self.last_name)

User.add_to_class("__str__", get_full_name)

class Plugin(models.Model):
	verbose_name = models.CharField(max_length=200)
	name = models.CharField(max_length=50)
	core = models.BooleanField(default=True)

	def __str__(self):
		return self.verbose_name

class oTreeInstance(models.Model):
	class Meta:
		permissions = (
			('can_restart', "Can restart the oTree instance"),
			('can_delete', "Can delete the oTree instance")
		)

	owned_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Experimenter")
	name = models.CharField(
		max_length=32, 
		validators=[
			RegexValidator(regex='^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$', 
				message='name is not suitable',
				code='invalid')
		]
	)
	deployed = models.BooleanField(default=False)

	enabled_plugins = models.ManyToManyField(Plugin)

	def __str__(self):
		return self.name

	def git_url(self):
		git_url = "dokku@%s:%s" % (settings.DOKKU_DOMAIN, self.name)
		return git_url

	def url(self):
		return "http://%s.%s" % (self.name, settings.DOKKU_DOMAIN)