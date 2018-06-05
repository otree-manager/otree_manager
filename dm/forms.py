from django.forms import ModelForm, CheckboxSelectMultiple
from .models import oTreeInstance

class AddNewForm(ModelForm):
	class Meta:
		model = oTreeInstance
		fields = ['name', 'owned_by', 'enabled_plugins']
		widgets = {'enabled_plugins': CheckboxSelectMultiple }