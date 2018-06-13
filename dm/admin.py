from django.contrib import admin

from django.contrib.auth.admin import UserAdmin
from .models import oTreeInstance, User
# Register your models here.

admin.site.register(oTreeInstance)
admin.site.register(User, UserAdmin)