from .views import FeatureDisabled

class DemoMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.disabled_views = [
            'PasswordResetView',
            'delete_user',
        ]

    def __call__(self, request):
        # 'intercepting request before view'


        response = self.get_response(request)

        # 'intercepting after view'


        return response


    def process_view(self, request, view_func, view_args, view_kwargs):
        if view_func.__name__ in self.disabled_views:
            print('disabled view: %s' % view_func.__name__)
            return FeatureDisabled.as_view()


    def process_template_response(self, request, response):
        return response
