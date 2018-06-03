from django.shortcuts import render
from django.http import HttpResponse

from .models import Experimenter, oTreeInstance

# Create your views here.
def index(request):
	context = { }
	return render(request, 'dm/index.html', context)