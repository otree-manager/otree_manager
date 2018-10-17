from django.http import HttpResponse
from django.views.generic.base import TemplateView

class FeatureDisabled(TemplateView):
    template_name = "om/demo/FeatureDisabled.html"

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     return context