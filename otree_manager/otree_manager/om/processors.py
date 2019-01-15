from django.conf import settings as django_conf

def settings(request):
    """Provides easy access to settings stored in django conf"""
    return {
        'DEMO': django_conf.DEMO,
        'MIN_WORKERS': django_conf.MIN_WORKERS,
        'MAX_WORKERS': django_conf.MAX_WORKERS,
        'MAX_WEB': django_conf.MAX_WEB,
    }