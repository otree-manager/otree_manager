from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from otree_manager.om.models import OTreeInstance, User

from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.forms import PasswordResetForm

from otree_manager.om.forms import (
    AddUserForm,
    ChangeKeyForm,
    EditUserForm,
)


@login_required
def change_key_file(request):
    if request.method == 'POST':
        form = ChangeKeyForm(request.POST or None, request.FILES or None, instance=request.user)
        if form.is_valid():
            user = form.save()
            return HttpResponseRedirect(reverse('index'))
    else:
        form = ChangeKeyForm()

    context = {'form': form}
    return render(request, 'om/user/change_key_file.html', context)


@login_required
def change_password(request):
    return render(request, 'om/user/password_change.html', {})


@login_required
def password_change_done(request):
    return render(request, 'om/user/password_change_done.html', {})


def password_reset(request):
    return render(request, 'om/user/reset_password.html', {})


@login_required
@permission_required('om.add_users', login_url='user/login/', raise_exception=True)
def new_user(request):
    if request.method == 'POST':
        form = AddUserForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            reset_form = PasswordResetForm({'email': new_user.email})
            assert reset_form.is_valid()
            reset_form.save(
                request=request,
                use_https=request.is_secure(),
                subject_template_name='om/emails/user_registration_subject.txt',
                email_template_name='om/emails/user_registration.html',
            )
            return HttpResponseRedirect(reverse('list_users'))
    else:
        form = AddUserForm()
    return render(request, 'om/user/new.html', {'form': form})


@login_required
@permission_required('om.delete_users', login_url='user/login/', raise_exception=True)
def delete_user(request, user_id):
    if not request.user.is_superuser:
        return HttpResponseRedirect(reverse('index'))

    user_inst = User.objects.get(id=user_id)
    user_count = User.objects.all().count()
    instances = OTreeInstance.objects.filter(owned_by=user_inst)

    delete_ok = user_count > 1 and instances.count() == 0 and user_inst != request.user

    if not delete_ok:
        return HttpResponseRedirect(reverse('edit_user', args=(user_id,)))
    else:
        user_inst.remove_public_key()
        user_inst.delete()

    return HttpResponseRedirect(reverse('list_users'))


@login_required
def edit_user(request, user_id):
    if not request.user.is_superuser:
        return HttpResponseRedirect(reverse('index'))

    user_inst = User.objects.get(id=user_id)
    user_count = User.objects.all().count()
    form = EditUserForm(request.POST or None, instance=user_inst)

    instances = OTreeInstance.objects.filter(owned_by=user_inst)

    delete_ok = user_count > 1 and instances.count() == 0 and user_inst != request.user

    if request.method == "POST":
        if form.is_valid():
            user = form.save()
            return HttpResponseRedirect(reverse('list_users'))

    return render(request, 'om/user/edit.html',
                  {'form': form, 'containers': instances, 'user': user_inst, 'delete_ok': delete_ok})


@login_required
def list_users(request):
    if not request.user.is_superuser:
        return HttpResponseRedirect(reverse('index'))
    else:
        user_list = User.objects.all().order_by('last_name')
        return render(request, 'om/user/list.html', {'user_list': user_list})
