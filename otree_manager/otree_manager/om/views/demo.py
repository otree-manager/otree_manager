from django.views import View
from django.shortcuts import render

class FeatureDisabled(View):
    """This view is exclusively called from the demo middleware"""
    # all requests are served the feature disabled template.
    template_name = "om/demo/FeatureDisabled.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        return render(request, self.template_name)