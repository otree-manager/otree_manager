from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse

from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Permission

from django.contrib.auth.forms import PasswordResetForm

from .models import oTreeInstance, User
from .forms import Add_New_Instance_Form, Add_User_Form, Change_OTree_Password

from .dokku import DokkuManager


def get_permissions(user, instance=None):
    if instance != None:
        can_view = (instance.owned_by == user) or user.groups.filter(name='Admins').exists()
    else:
        can_view = False

    perms = {
        'can_view': can_view,
        'can_restart': user.has_perm('dm.can_restart'),
        'can_delete': user.has_perm('dm.can_delete'),
        'can_add_user': user.has_perm('dm.add_users'),
        'can_add_instance': user.has_perm('dm.add_otreeinstance'),
        'can_reset': user.has_perm('dm.can_reset'),
    }

    return perms


@login_required
def index(request):
    if request.user.groups.filter(name='Admins').exists():
        show_instances = oTreeInstance.objects.order_by('name').all()
    else:
        show_instances = oTreeInstance.objects.filter(owned_by=request.user).order_by('name')
    perms = get_permissions(request.user)
    context = { 'instances': show_instances, 'permissions': perms, 'user': request.user }
    return render(request, 'dm/index.html', context)


@login_required
@permission_required('dm.add_otreeinstance', login_url='/login/', raise_exception=True)
def new_app(request):
    if request.method == 'POST':
        # handle data posted
        form = Add_New_Instance_Form(request.POST)
        if form.is_valid():
            new_instance = form.save()
            new_instance.create_dokku_app(request.user.id)
            return HttpResponseRedirect('/')
    else:
        form = Add_New_Instance_Form(initial = {'enabled_plugins': [1, 2] })

    return render(request, 'dm/new_app.html', {'form': form})


@login_required
def change_password(request):
    return render(request, 'dm/change_password.html', {})


@login_required
def password_change_done(request):
    return render(request, 'dm/password_change_done.html', {})


def password_reset(request):
    return render(request, 'dm/reset_password.html', {})


@login_required
def change_otree_password(request, instance_id):
    if request.method == 'POST':
        inst = oTreeInstance.objects.get(id=instance_id)
        form = Change_OTree_Password(request.POST or None, instance = inst)
        if form.is_valid():
            user = form.save()
            return HttpResponseRedirect('/')

        else:
            form = Change_OTree_Password(request.POST)
    else:
        form = Change_OTree_Password()

    return render(request, 'dm/change_otree_password.html', {'form': form})

@login_required
@permission_required('dm.add_users', login_url='login', raise_exception=True)
def new_user(request):
    if request.method == 'POST':
        form = Add_User_Form(request.POST)
        if form.is_valid():
            new_user = form.save()
            reset_form = PasswordResetForm({'email': new_user.email})
            assert reset_form.is_valid()
            reset_form.save(
                request=request,
                use_https=request.is_secure(),
                subject_template_name='dm/emails/user_registration_subject.txt',
                email_template_name='dm/emails/user_registration.html',
            )
            return HttpResponseRedirect('/')
    else:
        form = Add_User_Form()
    return render(request, 'dm/new_user.html', {'form': form})


@login_required
def detail(request, instance_id=None):
    if instance_id == None:
        return HttpResponseRedirect('/')

    inst = oTreeInstance.objects.get(id=instance_id)
    perms = get_permissions(request.user, inst)
    if not perms['can_view']:
        return HttpResponseRedirect('/')

    inst.refresh_from_dokku(request.user.id)

    return render(request, 'dm/detail.html', {'instance': inst, 'permissions': perms })


@login_required
def delete(request, instance_id=None):
    if instance_id == None:
        return HttpResponseRedirect('/')

    
    inst = oTreeInstance.objects.get(id=instance_id)
    perms = get_permissions(request.user, inst)
    if not perms['can_delete']:
        return HttpResponseRedirect('/')
    print('try destroy')
    inst.destroy_dokku_app(request.user.id)
    
    return HttpResponseRedirect('/')


@login_required
def reset_otree_password(request, instance_id=None):
    if instance_id == None:
        return HttpResponseRedirect('/')
    
    inst = oTreeInstance.objects.get(id=instance_id)
    print('otree password reset')


    inst.set_default_environment(request.user.id)
    # do stuff

    return HttpResponseRedirect(reverse('detail', args=(instance_id,)))


@login_required
def reset_database(request, instance_id=None):
    if instance_id == None:
        return HttpResponseRedirect('/')

    inst = oTreeInstance.objects.get(id=instance_id)
    perms = get_permissions(request.user, inst)
    if not perms['can_reset']:
        return HttpResponseRedirect('/')

    print('otree database reset')

    inst.reset_database(request.user.id)
    return HttpResponseRedirect(reverse('detail', args=(instance_id,)))