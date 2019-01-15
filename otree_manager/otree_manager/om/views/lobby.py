from django.shortcuts import render
from otree_manager.om.models import OTreeInstance
from otree_manager.om.utils import get_room_url


def lobby(request, instance_name, participant_label):
    try:
        inst = OTreeInstance.objects.get(name=instance_name)
    except OTreeInstance.DoesNotExist:
        return render(request, 'om/lobby/index.html', {'redirect_url': ''})

    if not inst.deployed:
        return render(request, 'om/lobby/index.html', {'redirect_url': '', 'error_msg': 'oTree not deployed'})

    room_url = get_room_url(request, inst)
    if not room_url:
        return render(request, 'om/lobby/index.html', {'redirect_url': '', 'error_msg': 'invalid room name'})

    if not inst.participant_label_valid(participant_label):
        return render(request, 'om/lobby/index.html', {'redirect_url': '', 'error_msg': 'invalid participant label'})

    redirect_url = "%s?participant_label=%s" % (room_url, participant_label)
    return render(request, 'om/lobby/index.html', {'redirect_url': redirect_url, 'error_msg': None})


def lobby_overview(request, instance_name):
    try:
        inst = OTreeInstance.objects.get(name=instance_name)
    except OTreeInstance.DoesNotExist:
        return render(request, 'om/lobby/index.html', {'redirect_url': ''})

    return render(request, 'om/lobby/overview.html',
                  {'instance': inst, 'participant_labels': inst.get_participant_labels()})
