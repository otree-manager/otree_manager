from .views import FeatureDisabled

"""Implementation of Demo mode middleware to restrict access to certain features"""

class DemoMiddleware:
    """Middle ware used to restrict access to certain functions in demo mode"""
    def __init__(self, get_response):
        self.get_response = get_response
        
        # define views which are disabled completely
        self.disabled_views = [
            'PasswordChangeDoneView',
            'PasswordResetDoneView',
            'PasswordResetConfirmView',
            'PasswordResetCompleteView',
            'delete_user',
            'delete',
        ]
        # define views which reply to GET, but not to POST (typically changing something)
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
            'change_otree_room',
            'edit_privacy',
            'edit_imprint',
        ]

    def __call__(self, request):
        response = self.get_response(request)
        return response


    def process_view(self, request, view_func, view_args, view_kwargs):
        """Process calls to views according to demo restrictions"""
        
        print('disabled view: %s, method: %s' % (view_func.__name__, request.method))
        
        # disable some views completely (i.e. for all request methods)
        # return the Feature Disabled view instead
        if view_func.__name__ in self.disabled_views:
            return FeatureDisabled.as_view()(request)

        # for some views we only disable POST methods:
        if view_func.__name__ in self.disabled_post_views:
            if request.method == "POST":
                return FeatureDisabled.as_view()(request)


    def process_template_response(self, request, response):
        return response
