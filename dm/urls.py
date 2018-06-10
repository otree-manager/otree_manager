from django.urls import path

from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('new_app/', views.new_app, name='new_app'),
    path('new_user/', views.new_user, name='new_user'),
    path('delete/<int:instance_id>', views.delete, name='delete'),
    path('login/', auth_views.login, { 'template_name': 'dm/login.html' }, name='login'),
    path('logout/', auth_views.logout, {'template_name': 'dm/logout.html' }, name="logout"),
 	# password_change
 	# password_change/done
 	# password_reset
 	# password_reset/done
 	# reset/uidb64/<token>
 	# reset/done
    path('detail/<int:instance_id>', views.detail, name='detail')
]