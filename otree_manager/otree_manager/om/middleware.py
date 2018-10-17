from .views import FeatureDisabled

class DemoMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.disabled_views = [
            'PasswordChangeDoneView',
            'PasswordResetDoneView',
            'PasswordResetConfirmView',
            'PasswordResetCompleteView',
            'delete_user',
            'delete',
        ]
        self.disabled_post_views = [
            'PasswordChangeView',
            'PasswordResetView',
            'new_user',
            'change_key_file',
            'edit_user',
            'new_app',
            'change_otree_password',
            'reset_otree_password',
            'scale_app',
            'change_otree_room'
        ]

    def __call__(self, request):
        # 'intercepting request before view'


        response = self.get_response(request)

        # 'intercepting after view'


        return response


    def process_view(self, request, view_func, view_args, view_kwargs):
        print('disabled view: %s, method: %s' % (view_func.__name__, request.method))
        # disable some views completely (i.e. for all request methods)
        if view_func.__name__ in self.disabled_views:
            return FeatureDisabled.as_view()(request)

        # for some views we only disable POST methods:
        if view_func.__name__ in self.disabled_post_views:
            if request.method == "POST":
                return FeatureDisabled.as_view()(request)


    def process_template_response(self, request, response):
        return response
