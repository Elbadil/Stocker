from django.urls import path
from django.contrib.auth import views as auth_views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)
from . import views


urlpatterns = [
     # Auth
     path('auth/login/', views.LoginView.as_view(), name='login'),
     path('auth/signup/', views.SignUpView.as_view(), name='register'),
     path('auth/logout/', views.LogoutView.as_view(), name='logout'), 
     path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
     path('auth/token/refresh/', views.CustomTokenRefreshView.as_view(), name='token_refresh'),
     path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
     path('auth/password-reset/request/', views.RequestPasswordReset.as_view(), name='password_reset'),
     path('auth/password-reset/<uidb64>/<token>/', views.ResetPassword.as_view(), name='password_reset_confirm'),
     # User
     path('users/<str:id>/', views.GetUpdateUserView.as_view(), name="get_update_user"),
     path('user/change-password/', views.ChangePasswordView.as_view(), name="change_password")
]