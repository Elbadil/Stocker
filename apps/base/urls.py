from django.urls import path
from django.contrib.auth import views as auth_views
from . import views


urlpatterns = [
     path('', views.index, name='index'),
     path('login/', views.userLogin, name='login'),
     path('logout/', views.userLogout, name='logout'),
     path('signup/', views.userSignUp, name='register'),
     path('confirm-account/', views.confirmAccount, name='confirm-account'),
     path('resend-confirm-code/', views.resendConfirmCode, name='resend-confirm-code'),
     # Built-in Password Reset Views
     path('password_reset/',
               auth_views.PasswordResetView.as_view(template_name='password_reset_form.html'),
          name='password_reset'),
     path('password_reset/done/',
          auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'),
          name='password_reset_done'),
     path('reset/<uidb64>/<token>/',
          auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'),
          name='password_reset_confirm'),
     path('reset/done/',
          auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'),
         name='password_reset_complete'),
     # User Profile
     path('profile/<str:user_id>/', views.userProfile, name='profile'),
]