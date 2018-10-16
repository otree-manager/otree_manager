from django.contrib import admin

from django.contrib.auth.admin import UserAdmin
from .models import OTreeInstance, User
# Register your models here.

admin.site.register(OTreeInstance)
admin.site.register(User, UserAdmin)