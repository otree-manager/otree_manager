from django.urls import path, re_path

from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path('', views.index, name='index'),

    path('login/', auth_views.login, { 'template_name': 'dm/login.html' }, name='login'),
    path('logout/', auth_views.logout, {'template_name': 'dm/logout.html' }, name="logout"),

    path('new_user/', views.new_user, name='new_user'),

    path('password_reset/', auth_views.password_reset, {'template_name': 'dm/password_reset.html' }, name='password_reset'),
    path('password_reset/done/', auth_views.password_reset_done, {'template_name': 'dm/password_reset_done.html' },
    	name='password_reset_done'),
    re_path(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        auth_views.password_reset_confirm, {'template_name': 'dm/password_reset_confirm.html' }, name='password_reset_confirm'),
    path('reset/done/', auth_views.password_reset_complete, {'template_name': 'dm/password_reset_complete.html' }, name='password_reset_complete'),


    path('password_change/', auth_views.password_change, { 'template_name': 'dm/password_change.html'}, name='password_change'),
    path('password_change/done/', auth_views.password_change_done, { 'template_name': 'dm/password_change_complete.html' }, name='password_change_done'),


    path('new_app/', views.new_app, name='new_app'),
    path('delete/<int:instance_id>', views.delete, name='delete'),
    path('detail/<int:instance_id>', views.detail, name='detail')
]