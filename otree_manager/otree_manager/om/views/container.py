from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from otree_manager.om.models import OTreeInstance
from otree_manager.om.utils import get_room_url
from otree_manager.om.forms import (
    AddNewInstanceForm,
    ChangeOTreePasswordForm,
    ChangeScalingForm,
    ChangeRoomForm
)
import zipfile
import time
import io

"""Container related views"""

@login_required
def download_shortcuts(request, instance_name, os):
    """Provides a zip file with shortcuts for opening common browsers in kiosk mode"""
    
    def gen_shortcut(url, label, operating_system):
        """Generates shortcut based on operating system and participant label"""
        arguments = "--kiosk --app="
        shebang = "#!/bin/bash"
        filename = ""

        if operating_system == "mac":
            browser_path = "/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome"

            content = "%s \n\n %s %s%s%s" % (shebang, browser_path, arguments, url, label)
            filename = "client_%s.command" % label

        if operating_system == "win":
            browser_path = "start chrome.exe"

            content = "%s %s%s%s" % (browser_path, arguments, url, label)
            filename = "client_%s.bat" % label

        if operating_system == "linux":
            filename = "client_%s.sh" % label
            chromium_cmd = "/usr/bin/chromium %s%s%s" % (arguments, url, label)
            chrome_cmd = "/usr/bin/google-chrome %s%s%s" % (arguments, url, label)

            content = """%s
if [ -f /usr/bin/chromium ]; then
    %s
elif [ -f /usr/bin/google-chrome ]; then
    %s
else
    echo "Neither Chromium nor Google Chrome could not be found at /usr/bin/*"
fi
""" % (shebang, chromium_cmd, chrome_cmd)

        return filename, content

    def zip_shortcuts(p_url, participant_labels, operating_system):
        """Adds an OS-specific shortcut for each participant label to the zip for download."""
        # create Zip file in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, mode='w', compression=zipfile.ZIP_DEFLATED) as zip:
            # for each participant label, creat a shortcut for the selected OS and add it as a file to the zip
            for label in participant_labels:
                filename, content = gen_shortcut(p_url, label, operating_system)
                zip_info = zipfile.ZipInfo(filename, date_time=time.localtime())
                zip_info.external_attr = 0o100755 << 16
                zip.writestr(zip_info, content)

        return zip_buffer

    # make sure OS is correctly specified
    if os not in ["win", "mac", "linux"]:
        return HttpResponse(404)

    # gather all information, generate zip and form the http response (i.e. make it a downloadable file)
    inst = OTreeInstance.objects.get(name=instance_name)
    url = "%s?participant_label=" % get_room_url(request, inst)
    data = zip_shortcuts(url, inst.get_participant_labels(), os)
    zip_filename = "%s_%s_shortcuts.zip" % (instance_name, inst.otree_room_name)
    response = HttpResponse(data.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = "attachement; filename=%s" % zip_filename

    return response


@login_required
@permission_required('om.add_otreeinstance', login_url='user/login/', raise_exception=True)
def new_app(request):
    """View to creat a new otree container"""

    if request.method == 'POST':
        # handle data received from filled-in form
        form = AddNewInstanceForm(request.POST)
        if form.is_valid():
            new_instance = form.save()
            new_instance.create_container(request.user.id)
            return HttpResponseRedirect(reverse('index'))
    else:
        # if it is not a POST request, send an empty form instead (GET)
        form = AddNewInstanceForm(initial={'enabled_plugins': [1, 2]})

    return render(request, 'om/container/new.html', {'form': form})


@login_required
def change_otree_password(request, instance_id):
    """oTree Web Interface password change view """
    if request.method == 'POST':
        # handle data of filled-in form
        inst = OTreeInstance.objects.get(id=instance_id)
        form = ChangeOTreePasswordForm(request.POST or None, instance=inst)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('detail', args=(instance_id,)))

        else:
            # if there are errors in the form, return with partially filled in form and errors
            form = ChangeOTreePasswordForm(request.POST)
    else:
        # if GET: prepare empty form
        form = ChangeOTreePasswordForm()

    return render(request, 'om/container/change_password.html', {'form': form})


@login_required
def scale_app(request, instance_id):
    """Container Scaling view"""
    inst = OTreeInstance.objects.get(id=instance_id)
    form = ChangeScalingForm(request.POST or None, instance=inst)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('detail', args=(instance_id,)))

    return render(request, 'om/container/scale.html', {'form': form, 'instance_id': instance_id})


@login_required
def change_otree_room(request, instance_id):
    """View for changing oTree room details"""
    inst = OTreeInstance.objects.get(id=instance_id)
    form = ChangeRoomForm(request.POST or None, request.FILES or None, instance=inst)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('detail', args=(instance_id,)))

    return render(request, 'om/container/change_room.html', {'form': form})


@login_required
def detail(request, instance_id=None):
    """Container detail page view"""
    # must provide an instance id
    if instance_id is None:
        return HttpResponseRedirect(reverse('index'))
    
    inst = OTreeInstance.objects.get(id=instance_id)
    
    # make sure only the owner and super users can access detail pages
    if not inst.owned_by == request.user and not request.user.is_superuser:
        return HttpResponseRedirect(reverse('index'))

    # refresh data from dokku (will be run in background)
    inst.refresh_from_dokku(request.user.id)
    
    # prepare participant label string
    plabel = ", ".join(inst.get_participant_labels())

    # for urls, make sure to show the right protocol
    prefix = 'https' if request.is_secure() else 'http'
    
    # get Lobby URL
    lurl = reverse('lobby_overview', args=[inst.name])
    lobby_url = "%s://%s%s" % (prefix, settings.DOKKU_DOMAIN, lurl)
    
    # get container URL
    app_url = "%s://%s.%s" %(prefix, inst.name, settings.DOKKU_DOMAIN)

    return render(request, 'om/container/detail.html',
                  {'instance': inst, 'otree_participant_labels': plabel, 'container_url': app_url, 'lobby_url': lobby_url})


@login_required
def delete(request, instance_id=None):
    """Delete instance view"""
    if instance_id is None:
        return HttpResponseRedirect(reverse('index'))
    
    inst = OTreeInstance.objects.get(id=instance_id)
    
    # only super-users can delete containers
    if not request.user.is_superuser:
        return HttpResponseRedirect(reverse('index'))
    
    # tell instance to destroy itself (in background)
    inst.destroy_dokku_app(request.user.id)

    return HttpResponseRedirect(reverse('index'))


@login_required
def reset_otree_password(request, instance_id=None):
    """otree passwort reset view"""
    if instance_id is None:
        return HttpResponseRedirect(reverse('index'))

    inst = OTreeInstance.objects.get(id=instance_id)

    # quickest way for a reset is to reset the environment variables to default
    # I have to seperate this at some point so we do not use scaling settings etc when resetting the password
    inst.set_default_environment(request.user.id)

    return HttpResponseRedirect(reverse('detail', args=(instance_id,)))


@login_required
def reset_database(request, instance_id=None):
    """Reset Database view"""
    if instance_id is None:
        return HttpResponseRedirect(reverse('index'))

    inst = OTreeInstance.objects.get(id=instance_id)
    if not request.user.is_superuser and not inst.owned_by == request.user:
        return HttpResponseRedirect(reverse('index'))

    inst.reset_database(request.user.id)
    
    return HttpResponseRedirect(reverse('detail', args=(instance_id,)))


@login_required
def restart_app(request, instance_id=None):
    """Restart container view"""
    if instance_id is None:
        return HttpResponseRedirect(reverse('index'))

    inst = OTreeInstance.objects.get(id=instance_id)
    if not request.user.is_superuser and not inst.owned_by == request.user:
        return HttpResponseRedirect(reverse('index'))

    inst.restart_container(request.user.id)
    return HttpResponseRedirect(reverse('detail', args=(instance_id,)))
