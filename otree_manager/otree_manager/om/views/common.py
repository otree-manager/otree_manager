from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from otree_manager.om.models import OTreeInstance

"""Common base views"""

@login_required
def index(request):
    """Index page after login."""
    
    # If a no ssh key is set, it must be the first login of a new user. So redirect to add ssh key.
    if not request.user.public_key_set:
        return HttpResponseRedirect(reverse('change_key_file'))

    # super-users see all instances, others only their own
    if request.user.is_superuser:
        show_instances = OTreeInstance.objects.order_by('-deployed', '-name').all()
    else:
        show_instances = OTreeInstance.objects.filter(owned_by=request.user).order_by('-deployed', '-name')

    context = {'instances': show_instances, 'user': request.user}
    return render(request, 'om/index.html', context)

def about(request):
    """About page"""
    return render(request, 'om/about.html', {})
