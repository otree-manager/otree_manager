from django.forms import ModelForm, CheckboxSelectMultiple, ChoiceField, Form, CharField, PasswordInput, ValidationError
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

class Add_New_Instance_Form(ModelForm):
    class Meta:
        model = oTreeInstance
        fields = ['name', 'owned_by']


class Change_OTree_Password(Form):
    password_1 = CharField(label="Password", max_length="100", widget=PasswordInput)
    password_2 = CharField(label="Password confirmation", max_length="100", widget=PasswordInput)

    error_messages = {
        'password_mismatch': _("The two password fields didn't match."),
    }

    def __init__(self, instance_id, post_data=None, *args, **kwargs):
        self.instance = oTreeInstance.objects.get(id=instance_id)
        self.cleaned_data = { 'password': None }
        if post_data:
            print(post_data)
            self.password_1 = post_data['password_1']
            self.password_2 = post_data['password_2']

        super().__init__(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.password_2_clean():
            return self.cleaned_data
        else:
            raise ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )

    def is_valid(self):
        return self.clean()

    def password_2_clean(self):
        if self.password_1 and self.password_2 and self.password_1 == self.password_2:
            self.cleaned_data["password"] = self.password_1
            return True
        else:
            return False

    def save(self, commit="True"):
        password = self.cleaned_data.get('password')
        self.instance.set_otree_password(password)
        return self.instance


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