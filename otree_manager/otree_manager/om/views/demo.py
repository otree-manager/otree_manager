from django.http import HttpResponse
#from django.views.generic.base import TemplateView
from django.views import View
from django.shortcuts import render

class FeatureDisabled(View):
    template_name = "om/demo/FeatureDisabled.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        return render(request, self.template_name)