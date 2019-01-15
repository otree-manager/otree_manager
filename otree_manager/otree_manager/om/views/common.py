from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from otree_manager.om.models import OTreeInstance


@login_required
def index(request):
    if not request.user.public_key_set:
        return HttpResponseRedirect(reverse('change_key_file'))

    if request.user.is_superuser:
        show_instances = OTreeInstance.objects.order_by('-deployed', '-name').all()
    else:
        show_instances = OTreeInstance.objects.filter(owned_by=request.user).order_by('-deployed', '-name')
    context = {'instances': show_instances, 'user': request.user}
    return render(request, 'om/index.html', context)


def imprint(request):
    return render(request, 'om/imprint.html', {})


def privacy(request):
    return render(request, 'om/privacy.html', {})
