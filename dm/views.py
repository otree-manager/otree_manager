from django.shortcuts import render
from django.http import HttpResponseRedirect

from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Permission

from .models import oTreeInstance
from .forms import AddNewForm


def get_permissions(user, instance):
	perms = {
		'can_view': (instance.owned_by == user) or user.groups.filter(name='Admins').exists(),
		'can_restart': user.has_perm('dm.can_restart'),
		'can_delete': user.has_perm('dm.can_delete'),
	}

	return perms

# Create your views here.
@login_required
def index(request):
	if request.user.groups.filter(name='Admins').exists():
		show_instances = oTreeInstance.objects.order_by('name').all()
	else:
		show_instances = oTreeInstance.objects.filter(owned_by=request.user).order_by('name')
	context = { 'instances': show_instances, 'user_can_add_instance': request.user.has_perm('dm.add_otreeinstance') }
	return render(request, 'dm/index.html', context)

@login_required
@permission_required('dm.add_otreeinstance', login_url='/login/', raise_exception=True)
def new(request):
	if request.method == 'POST':
		# handle data posted
		form = AddNewForm(request.POST)
		if form.is_valid():
			new_instance = form.save()
			return HttpResponseRedirect('/')
	else:
		form = AddNewForm()
	return render(request, 'dm/new.html', {'form': form})

@login_required
def detail(request, instance_id=None):
	if instance_id == None:
		return HttpResponseRedirect('/')

	else:
		inst = oTreeInstance.objects.get(id=instance_id)
		perms = get_permissions(request.user, inst)
		print(perms)
		if not perms['can_view']:
			return HttpResponseRedirect('/')

		return render(request, 'dm/detail.html', {'instance': inst, 'permissions': perms })
