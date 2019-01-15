from django.shortcuts import render
from otree_manager.om.models import OTreeInstance
from otree_manager.om.utils import get_room_url

"""Lobby Feature Views"""


def lobby(request, instance_name, participant_label):
    """Lobby view for individual participant"""
    # make sure the requested instance exists
    try:
        inst = OTreeInstance.objects.get(name=instance_name)
    except OTreeInstance.DoesNotExist:
        return render(request, 'om/lobby/index.html', {'redirect_url': ''})

    # make sure it is deployed
    if not inst.deployed:
        return render(request, 'om/lobby/index.html', {'redirect_url': '', 'error_msg': 'oTree not deployed'})

    # check if room is set up
    room_url = get_room_url(request, inst)
    if not room_url:
        return render(request, 'om/lobby/index.html', {'redirect_url': '', 'error_msg': 'invalid room name'})

    # make sure participant label exists
    if not inst.participant_label_valid(participant_label):
        return render(request, 'om/lobby/index.html', {'redirect_url': '', 'error_msg': 'invalid participant label'})

    # finally prepare redirection URL and render template
    redirect_url = "%s?participant_label=%s" % (room_url, participant_label)
    return render(request, 'om/lobby/index.html', {'redirect_url': redirect_url, 'error_msg': None})


def lobby_overview(request, instance_name):
    """Lobby overview page, showing all clients"""
    try:
        inst = OTreeInstance.objects.get(name=instance_name)
    except OTreeInstance.DoesNotExist:
        return render(request, 'om/lobby/index.html', {'redirect_url': ''})

    return render(request, 'om/lobby/overview.html',
                  {'instance': inst, 'participant_labels': inst.get_participant_labels()})
