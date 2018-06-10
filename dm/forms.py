from django.forms import ModelForm, CheckboxSelectMultiple, ChoiceField
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import UsernameField

from django.contrib.auth.models import Group
from django.utils.crypto import get_random_string

from django.core.mail import send_mail

from .models import oTreeInstance
from .choices import *

UserModel = get_user_model()

class Add_New_Instance_Form(ModelForm):
    class Meta:
        model = oTreeInstance
        fields = ['name', 'owned_by', 'enabled_plugins']
        widgets = {'enabled_plugins': CheckboxSelectMultiple }

class Add_User_Form(ModelForm):
    """
    A form that creates a user, with no privileges, from the given username
    """

    role = ChoiceField(
        label="Role",
        choices=ROLES,
        initial=1,
    )

    class Meta:
        model = UserModel
        fields = (UserModel.USERNAME_FIELD, 'first_name', 'last_name', 'email')
        field_classes = {UserModel.USERNAME_FIELD: UsernameField}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self._meta.model.USERNAME_FIELD in self.fields:
            self.fields[self._meta.model.USERNAME_FIELD].widget.attrs.update({'autofocus': True})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(get_random_string())
        user.save()

        if self.cleaned_data.get("role") == 2:
            admin_group = Group.objects.get(name='Admins')
            user.groups.add(admin_group)

        # default to experimenter group
        experimenter_group = Group.objects.get(name='Experimenters')
        user.groups.add(experimenter_group)

        if commit:
            user.save()
        return user