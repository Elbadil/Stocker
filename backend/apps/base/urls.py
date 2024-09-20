from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)
from . import views


urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('signup/', views.SignUpView.as_view(), name='register'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', views.CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('password-reset/request/', views.RequestPasswordReset.as_view(), name='password_reset'),
    path('password-reset/<uidb64>/<token>/', views.ResetPassword.as_view(), name='password_reset_confirm'),
    path('logout/', views.LogoutView.as_view(), name='logout'), 
    path('user/', views.GetUpdateUserView.as_view(), name="get_update_user"),
    path('user/change-password/', views.ChangePasswordView.as_view(), name="change_password")
]