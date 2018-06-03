from django.db import models

# Create your models here.

class Experimenter(models.Model):
	is_admin = models.BooleanField(default=False)
	name = models.CharField(max_length=32)

class oTreeInstance(models.Model):
	owned_by = models.ForeignKey(Experimenter, on_delete=models.CASCADE)
	name = models.CharField(max_length=16)