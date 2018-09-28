from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse

from django.contrib.auth.decorators import login_required, permission_required
from django.conf import settings


from django.contrib.auth.forms import PasswordResetForm

import zipfile
import time
import io

from .models import oTreeInstance, User
from .forms import (
    Add_New_Instance_Form, 
    Add_User_Form, 
    Change_OTree_Password, 
    Change_Scaling_Form, 
    Change_Key_Form, 
    Edit_User_Form,
    Change_Room_Form
)


def get_room_url(request, inst):
    prefix = 'https' if request.is_secure() else 'http'
    return "%s://%s.%s/room/%s/" % (prefix, inst.name, settings.DOKKU_DOMAIN, inst.otree_room_name)


@login_required
def index(request):
    if not request.user.public_key_set:
        return HttpResponseRedirect(reverse('change_key_file'))

    if request.user.is_superuser:
        show_instances = oTreeInstance.objects.order_by('-deployed', '-name').all()
    else:
        show_instances = oTreeInstance.objects.filter(owned_by=request.user).order_by('-deployed', '-name')
    context = { 'instances': show_instances, 'user': request.user }
    return render(request, 'om/index.html', context)

def lobby(request, instance_name, participant_label):
    try:
        inst = oTreeInstance.objects.get(name=instance_name)
    except oTreeInstance.DoesNotExist:
        return render(request, 'om/lobby.html', { 'redirect_url': '' })

    if not inst.deployed:
        return render(request, 'om/lobby.html', { 'redirect_url': '', 'error_msg': 'oTree not deployed' })

    room_url = get_room_url(request, inst)
    if not room_url:
        return render(request, 'om/lobby.html', { 'redirect_url': '', 'error_msg': 'invalid room name' })

    if not inst.participant_label_valid(participant_label):
        return render(request, 'om/lobby.html', { 'redirect_url': '', 'error_msg': 'invalid participant label' })

    prefix = 'https' if request.is_secure() else 'http'
    room_url = "%s://%s.%s/" % (prefix, inst.name, settings.DOKKU_DOMAIN)
    redirect_url = "%s?participant_label=%s" % (room_url, participant_label)
    return render(request, 'om/lobby.html', { 'redirect_url': redirect_url, 'error_msg': None })

def lobby_overview(request, instance_name):
    try:
        inst = oTreeInstance.objects.get(name=instance_name)
    except oTreeInstance.DoesNotExist:
        return render(request, 'om/lobby.html', { 'redirect_url': '' })

    return render(request, 'om/lobby_overview.html', { 'instance': inst, 'participant_labels': inst.get_participant_labels() })


@login_required
def download_shortcuts(request, instance_name, os):
    def gen_shortcut(url, label, os):
        arguments = "--kiosk --app="
        shebang = "#!/bin/bash"

        if os == "mac":
            browser_path = "/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome"

            content = "%s \n\n %s %s%s%s" % (shebang, browser_path, arguments, url, label)
            filename = "client_%s.command" % label

        if os == "win":
            browser_path = "start chrome.exe"

            content = "%s %s%s%s" % (browser_path, arguments, url, label)
            filename = "client_%s.bat" % label

        if os == "linux":
            filename = "client_%s.sh" % label
            chromium_cmd = "/usr/bin/chromium %s%s%s" % (arguments, url, label)
            chrome_cmd = "/usr/bin/google-chrome %s%s%s" % (arguments, url, label)

            content = """%s
if [ -f /usr/bin/chromium ]; then
    %s
elif [ -f /usr/bin/google-chrome ]; then
    %s
else
    echo "Chromium and google chome could not be found at /usr/bin/*"
fi
""" % (shebang, chromium_cmd, chrome_cmd)

        return (filename, content)

    def zip_shortcuts(url, participant_labels, os):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, mode='w', compression=zipfile.ZIP_DEFLATED) as zip:
            for label in participant_labels:
                filename, content = gen_shortcut(url, label, os)
                zip_info = zipfile.ZipInfo(filename, date_time=time.localtime())
                zip_info.external_attr = 0o100755 << 16
                zip.writestr(zip_info, content)

        return zip_buffer

    if not os in ["win", "mac", "linux"]:
        return HttpResponse(404)


    inst = oTreeInstance.objects.get(name=instance_name)
    url = "%s?participant_label=" % get_room_url(request, inst)
    data = zip_shortcuts(url, inst.get_participant_labels(), os)

    zip_filename = "%s_%s_shortcuts.zip" % (instance_name, inst.otree_room_name)

    response = HttpResponse(data.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = "attachement; filename=%s" % zip_filename   
    return response

@login_required
def change_key_file(request):
    if request.method == 'POST':
        form = Change_Key_Form(request.POST or None, request.FILES or None, instance=request.user)
        if form.is_valid():
            user = form.save()
            return HttpResponseRedirect(reverse('index'))
    else:
        form = Change_Key_Form()

    context = { 'form': form }
    return render(request, 'om/change_key_file.html', context)

@login_required
@permission_required('om.add_otreeinstance', login_url='user/login/', raise_exception=True)
def new_app(request):
    if request.method == 'POST':
        # handle data posted
        form = Add_New_Instance_Form(request.POST)
        if form.is_valid():
            new_instance = form.save()
            new_instance.create_dokku_app(request.user.id)
            return HttpResponseRedirect(reverse('index'))
    else:
        form = Add_New_Instance_Form(initial = {'enabled_plugins': [1, 2] })

    return render(request, 'om/new_app.html', {'form': form})


@login_required
def change_password(request):
    return render(request, 'om/change_password.html', {})


@login_required
def password_change_done(request):
    return render(request, 'om/password_change_done.html', {})


def password_reset(request):
    return render(request, 'om/reset_password.html', {})


@login_required
def change_otree_password(request, instance_id):
    if request.method == 'POST':
        inst = oTreeInstance.objects.get(id=instance_id)
        form = Change_OTree_Password(request.POST or None, instance = inst)
        if form.is_valid():
            inst = form.save()
            return HttpResponseRedirect(reverse('detail', args=(instance_id,)))

        else:
            form = Change_OTree_Password(request.POST)
    else:
        form = Change_OTree_Password()

    return render(request, 'om/change_otree_password.html', {'form': form})

@login_required
def scale_app(request, instance_id):
    inst = oTreeInstance.objects.get(id=instance_id)
    form = Change_Scaling_Form(request.POST or None, instance = inst)
    
    if request.method == 'POST':
        if form.is_valid():
            user = form.save()
            return HttpResponseRedirect(reverse('detail', args=(instance_id,)))

    return render(request, 'om/scale_app.html', {'form': form, 'instance_id':instance_id})


@login_required
def change_otree_room(request, instance_id):
    inst = oTreeInstance.objects.get(id=instance_id)
    form = Change_Room_Form(request.POST or None, request.FILES or None, instance = inst)
    if request.method == 'POST':
        if form.is_valid():
            inst = form.save()
            return HttpResponseRedirect(reverse('detail', args=(instance_id,)))

    return render(request, 'om/change_otree_room.html', { 'form': form })


@login_required
@permission_required('om.add_users', login_url='user/login/', raise_exception=True)
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
                subject_template_name='om/emails/user_registration_subject.txt',
                email_template_name='om/emails/user_registration.html',
            )
            return HttpResponseRedirect(reverse('list_users'))
    else:
        form = Add_User_Form()
    return render(request, 'om/new_user.html', {'form': form})

@login_required
@permission_required('om.delete_users', login_url='user/login/', raise_exception=True)
def delete_user(request, user_id):
    if not request.user.is_superuser:
        return HttpResponseRedirect(reverse('index'))

    user_inst = User.objects.get(id=user_id) 
    user_count = User.objects.all().count()
    instances = oTreeInstance.objects.filter(owned_by=user_inst)

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
    form = Edit_User_Form(request.POST or None, instance = user_inst)

    instances = oTreeInstance.objects.filter(owned_by=user_inst)

    delete_ok = user_count > 1 and instances.count() == 0 and user_inst != request.user

    if request.method == "POST":
        if form.is_valid():
            user = form.save()
            return HttpResponseRedirect(reverse('list_users'))

    return render(request, 'om/edit_user.html', { 'form': form, 'containers': instances, 'user': user_inst, 'delete_ok': delete_ok })

@login_required
def list_users(request):
    if not request.user.is_superuser:
        return HttpResponseRedirect(reverse('index'))
    else:
        user_list = User.objects.all().order_by('last_name')
        return render(request, 'om/list_users.html', { 'user_list': user_list })


@login_required
def detail(request, instance_id=None):
    if instance_id == None:
        return HttpResponseRedirect(reverse('index'))

    inst = oTreeInstance.objects.get(id=instance_id)
    if not inst.owned_by == request.user and not request.user.is_superuser:
        return HttpResponseRedirect(reverse('index'))

    inst.refresh_from_dokku(request.user.id)

    plabel = ", ".join(inst.get_participant_labels())

    #lurl = inst.get_lobby_url()
    lurl = reverse('lobby_overview', args=[inst.name])

    return render(request, 'om/detail.html', {'instance': inst, 'otree_participant_labels': plabel, 'lobby_url': lurl })


@login_required
def delete(request, instance_id=None):
    if instance_id == None:
        return HttpResponseRedirect(reverse('index'))

    
    inst = oTreeInstance.objects.get(id=instance_id)
    if not request.user.is_superuser:
        return HttpResponseRedirect(reverse('index'))
    print('try destroy')
    inst.destroy_dokku_app(request.user.id)
    
    return HttpResponseRedirect(reverse('index'))


@login_required
def reset_otree_password(request, instance_id=None):
    if instance_id == None:
        return HttpResponseRedirect(reverse('index'))
    
    inst = oTreeInstance.objects.get(id=instance_id)
    print('otree password reset')

    inst.set_default_environment(request.user.id)

    return HttpResponseRedirect(reverse('detail', args=(instance_id,)))


@login_required
def reset_database(request, instance_id=None):
    if instance_id == None:
        return HttpResponseRedirect(reverse('index'))

    inst = oTreeInstance.objects.get(id=instance_id)

    if not request.user.is_superuser and not inst.owned_by == request.user:
        return HttpResponseRedirect(reverse('index'))

    print('otree database reset')

    inst.reset_database(request.user.id)
    return HttpResponseRedirect(reverse('detail', args=(instance_id,)))

@login_required
def restart_app(request, instance_id=None):
    if instance_id == None:
        return HttpResponseRedirect(reverse('index'))

    inst = oTreeInstance.objects.get(id=instance_id)
    if not request.user.is_superuser and not inst.owned_by == request.user:
        return HttpResponseRedirect(reverse('index'))

    print('restart app')

    inst.restart_dokku_app(request.user.id)
    return HttpResponseRedirect(reverse('detail', args=(instance_id,)))

def imprint(request):
    return render(request, 'om/imprint.html', {})

def privacy(request):
    return render(request, 'om/privacy.html', {})
