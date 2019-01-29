from django.urls import path, re_path
from django.contrib.auth import views as auth_views
from django.contrib.flatpages import views as fp_views
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('legal/imprint/', fp_views.flatpage, {'url': '/legal/imprint/'}, name='imprint'),
    path('legal/imprint/edit/', views.imprint_edit, name='edit_imprint'),
    path('legal/privacy/', fp_views.flatpage, {'url': '/legal/privacy/'}, name='privacy'),
    path('legal/privacy/edit/', views.privacy_edit, name='edit_privacy'),
    path('about/', views.about, name='about'),
    path('lobby/<str:instance_name>/', views.lobby_overview, name="lobby_overview"),
    path('lobby/<str:instance_name>/<str:participant_label>/', views.lobby, name="lobby"),
    path('lobby/download/<str:instance_name>/<str:os>/', views.download_shortcuts, name="download_shortcuts"),

    path('user/login/', auth_views.LoginView.as_view(template_name='om/user/login.html'), name='login'),
    path('user/logout/', auth_views.LogoutView.as_view(template_name='om/user/logout.html'), name="logout"),

    path('user/new/', views.new_user, name='new_user'),
    path('user/list/', views.list_users, name="list_users"),
    path('user/delete/<int:user_id>', views.delete_user, name="delete_user"),
    path('user/edit/<int:user_id>', views.edit_user, name="edit_user"),
    path('user/edit/keyfile/', views.change_key_file, name='change_key_file'),
    path('user/password/reset/', auth_views.PasswordResetView.as_view(template_name='om/user/password_reset.html', email_template_name='om/emails/password_reset_mail.html'),
         name='password_reset'),
    path('user/password/reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='om/user/password_reset_done.html'),
         name='password_reset_done'),

    re_path(r'^user/password/reset/token/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
            auth_views.PasswordResetConfirmView.as_view(template_name='om/user/password_reset_confirm.html'),
            name='password_reset_confirm'),
    path('user/password/reset/complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name='om/user/password_reset_complete.html'),
         name='password_reset_complete'),

    path('user/password/change/', auth_views.PasswordChangeView.as_view(template_name='om/user/password_change.html'),
         name='password_change'),
    path('user/password/change/done/',
         auth_views.PasswordChangeDoneView.as_view(template_name='om/user/password_change_done.html'),
         name='password_change_done'),

    path('app/new/', views.new_app, name='new_app'),
    path('app/delete/<int:instance_id>', views.delete, name='delete'),
    path('app/detail/<int:instance_id>', views.detail, name='detail'),
    path('app/restart/<int:instance_id>', views.restart_app, name="restart"),
    path('app/scale/<int:instance_id>', views.scale_app, name="scale_app"),

    path('app/otree/reset_password/<int:instance_id>', views.reset_otree_password, name="reset_otree_password"),
    path('app/otree/change_password/<int:instance_id>', views.change_otree_password, name="change_otree_password"),
    path('app/otree/reset_database/<int:instance_id>', views.reset_database, name="reset_database"),
    path('app/otree/change_room/<int:instance_id>', views.change_otree_room, name="change_otree_room"),
]
