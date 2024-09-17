from django.urls import path
from django.contrib.auth import views as auth_views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)
from . import views


urlpatterns = [
     path('auth/login/', views.LoginView.as_view(), name='login'),
     path('auth/signup/', views.SignUpView.as_view(), name='register'),
     path('auth/logout/', views.LogoutView.as_view(), name='logout'),
     path('users/<str:id>/', views.GetUpdateUserView.as_view(), name="get_update_user"),
     path('user/change-password/', views.ChangePasswordView.as_view(), name="change_password"),
     path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
     path('auth/token/refresh/', views.CustomTokenRefreshView.as_view(), name='token_refresh'),
     path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
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
         name='password_reset_complete')
]