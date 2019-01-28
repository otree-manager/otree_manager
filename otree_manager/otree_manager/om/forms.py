from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UsernameField
from django.utils.crypto import get_random_string
from django.core.files.storage import default_storage
from .models import OTreeInstance
import gettext
import subprocess
import re
import os

"""This file specifies custom forms for oTree manager"""

UserModel = get_user_model()
_ = gettext.gettext

# Error messages to be used
error_messages = {
    'password_mismatch': _("The two password fields didn't match."),
    'file_size': _("The file is too large (max 1kb)."),
    'keyfile_pattern': _("The file seems to have a non-standard pattern."),
    'invalid_file': _("The file is not a valid rsa public key file."),
    'no_labels': _("Could not read labels from file."),
    'invalid_domain_name': _("The name may only contain a-z, A-Z, 0-9 and dashes. Dashes cannot be first or last.")
}


class EditUserForm(forms.ModelForm):
    """Form for editing user details"""
    class Meta:
        model = UserModel
        fields = ['username', 'first_name', 'last_name', 'email', 'is_superuser']

    pass


class ChangeRoomForm(forms.ModelForm):
    """Form for changing room details"""
    labels_file = forms.FileField()

    class Meta:
        model = OTreeInstance
        fields = ['otree_room_name', 'labels_file']

    def clean_labels_file(self):
        """Checks if labels file appears to be suitable"""
        participant_label_file = self.cleaned_data.get('labels_file', False)
        # print(participant_label_file)

        if participant_label_file.size > 1024:
            raise forms.ValidationError(error_messages['file_size'], code="invalid file")

        if not participant_label_file:
            raise forms.ValidationError(error_messages['no_labels'], code="invalid file")

        return participant_label_file

    def save(self, commit=True):
        """Adds labels read from file to instance object"""
        inst = super().save()

        # read labels from newly uploaded file
        labels = []
        for line in self.cleaned_data.get('labels_file', []):
            label = line.decode('utf-8').strip()
            if label:
                labels.append(label)
                
        # store the labels on the instance
        inst.set_participant_labels(labels)
        return inst


class ChangeKeyForm(forms.ModelForm):
    """Form for handling ssh key changes"""
    class Meta:
        model = UserModel
        fields = ['public_key_file']

    def clean_public_key_file(self):
        """Checks if ssh key file is suitable"""
        public_key_file = self.cleaned_data.get('public_key_file', False)

        # reject files over 1kb
        if public_key_file.size > 1024:
            raise forms.ValidationError(error_messages['file_size'], code="invalid file")

        # check against regular expression first (quick and dirty)
        content = public_key_file.read().decode('utf-8')
        pattern = re.compile("ssh-rsa AAAA[0-9A-Za-z+/]+[=]{0,3}( [^@]+@[^@]+)?")
        if not pattern.match(content):
            raise forms.ValidationError(error_messages['keyfile_pattern'], code="invalid file")

        # after passing initial checks, store on drive temporarily
        filename = public_key_file.name
        file_obj = public_key_file
        file_path = 'tmp/' + filename

        with default_storage.open(file_path, 'wb+') as destination:
            for chunk in file_obj.chunks():
                destination.write(chunk)

        # as an additional check, check for the output of ssh-keygen on the file
        # I could not find a way to run ssh-keygen on the file blob in memory, that is why I write it to disk shortly
        # maybe I can come up with a better solution in the future
        proc = subprocess.run(['ssh-keygen', '-l', '-f', file_path])
        # clean up
        if os.path.isfile(file_path):
            os.remove(file_path)


        # check outcome
        if proc.returncode != 0:
            # notify user of error then return
            raise forms.ValidationError(error_messages['invalid_file'], code="invalid file")
        return public_key_file

    def save(self, commit=True):
        """Add ssh key file to user object on save"""
        user = super().save()
        user.set_public_key()
        return user


class AddNewInstanceForm(forms.ModelForm):
    """Form for creating new otree containers"""
    class Meta:
        model = OTreeInstance
        fields = ['name', 'owned_by']


class ChangeOTreePasswordForm(forms.ModelForm):
    """Form for changing otree webinterface password"""
    password_2 = forms.CharField(label="Password confirmation", max_length="100", widget=forms.PasswordInput())

    class Meta:
        model = OTreeInstance
        fields = ['otree_admin_password', 'password_2']
        widgets = {
            'otree_admin_password': forms.PasswordInput()
        }

    def clean(self):
        """Clean up password inputs and make sure they match"""
        cleaned_data = super().clean()
        password = cleaned_data.get('otree_admin_password')
        password_2 = cleaned_data.get('password_2')

        if password != password_2 or not password or not password_2:
            raise forms.ValidationError(error_messages['password_mismatch'], code="invalid password")

        return cleaned_data

    def save(self, commit=True):
        """Update environment variables if webinterface password has been changed"""
        inst = super().save()
        inst.set_environment()
        return inst


class ChangeScalingForm(forms.ModelForm):
    """Form for changing the number of web and worker processes"""
    class Meta:
        model = OTreeInstance
        fields = ['web_processes', 'worker_processes']

    def save(self, commit=True):
        """Scale instance on saving"""
        inst = super().save()
        inst.scale_container()
        return inst


class AddUserForm(forms.ModelForm):
    """Form to add new users to the system"""
    class Meta:
        model = UserModel
        fields = (UserModel.USERNAME_FIELD, 'first_name', 'last_name', 'email', 'is_superuser')
        field_classes = {UserModel.USERNAME_FIELD: UsernameField}

    def save(self, commit=True):
        """Set a random password on creation of new users"""
        user = super().save(commit=False)
        user.set_password(get_random_string())

        if commit:
            user.save()
        return user
