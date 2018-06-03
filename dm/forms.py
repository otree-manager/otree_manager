from django.forms import ModelForm
from .models import oTreeInstance

class AddNewForm(ModelForm):
	class Meta:
		model = oTreeInstance
		fields = ['name', 'owned_by']
	