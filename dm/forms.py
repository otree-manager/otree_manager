from django import forms 
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import UsernameField

from django.contrib.auth.models import Group
from django.utils.crypto import get_random_string

from django.core.mail import send_mail
import gettext

from .models import oTreeInstance, User
from .choices import *

UserModel = get_user_model()
_ = gettext.gettext



class Add_New_Instance_Form(forms.ModelForm):
    class Meta:
        model = oTreeInstance
        fields = ['name', 'owned_by']


class Change_OTree_Password(forms.ModelForm):

    password_2 = forms.CharField(label="Password confirmation", max_length="100", widget=forms.PasswordInput())

    class Meta:
        model = oTreeInstance
        fields = ['otree_admin_password', 'password_2']
        widgets = {
            'otree_admin_password': forms.PasswordInput()
        }


    error_messages = {
        'password_mismatch': _("The two password fields didn't match."),
    }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('otree_admin_password')
        password_2 = cleaned_data.get('password_2')

        if password != password_2 or not password or not password_2:
            raise forms.ValidationError(self.error_messages['password_mismatch'], code="invalid password")

        return cleaned_data


    def save(self, commit=True):
        inst = super().save()
        inst.set_environment()
        return inst


class Change_Scaling_Form(forms.ModelForm):
    class Meta:
        model = oTreeInstance
        fields = ['web_dynos', 'worker_dynos']

    def save(self, commit=True):
        inst = super().save()
        inst.scale_dokku_app()
        return inst
        

class Add_User_Form(forms.ModelForm):
    """
    A form that creates a user, with no privileges, from the given username
    """

    role = forms.ChoiceField(
        label="Role",
        choices=ROLES,
        initial=1,
    )

    class Meta:
        model = UserModel
        fields = (UserModel.USERNAME_FIELD, 'first_name', 'last_name', 'email')
        field_classes = {UserModel.USERNAME_FIELD: UsernameField}

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)

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