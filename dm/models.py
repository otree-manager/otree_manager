from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class oTreeInstance(models.Model):
	class Meta:
		permissions = (
			('can_restart', "Can restart the oTree instance"),
			('can_delete', "Can delete the oTree instance")
		)

	owned_by = models.ForeignKey(User, on_delete=models.CASCADE)
	name = models.CharField(max_length=16)

	def __str__(self):
		return self.name