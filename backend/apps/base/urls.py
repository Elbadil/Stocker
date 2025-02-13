from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)
from .views import user_views, dashboard_views


urlpatterns = [
    # User 
    path('auth/login/',
         user_views.LoginView.as_view(),
         name='login'),
    path('auth/signup/',
         user_views.SignUpView.as_view(),
         name='register'),
    path('auth/token/',
         TokenObtainPairView.as_view(),
         name='token_obtain_pair'),
    path('auth/token/refresh/',
         user_views.CustomTokenRefreshView.as_view(),
         name='token_refresh'),
    path('auth/token/verify/',
         TokenVerifyView.as_view(),
         name='token_verify'),
    path('auth/password-reset/request/',
         user_views.RequestPasswordReset.as_view(),
         name='request_password_reset'),
    path('auth/password-reset/<uidb64>/<token>/',
         user_views.ResetPassword.as_view(),
         name='password_reset_confirm'),
    path('auth/logout/',
         user_views.LogoutView.as_view(),
         name='logout'), 
    path('auth/user/',
         user_views.GetUpdateUserView.as_view(),
         name="get_update_user"),
    path('auth/user/change-password/',
         user_views.ChangePasswordView.as_view(),
         name="change_password"),
    path('auth/user/activities/',
         user_views.GetUserActivities.as_view(),
         name="get_user_activities"),

    # Dashboard
    path('dashboard/',
         dashboard_views.DashboardAPIView.as_view(),
         name='dashboard_info'),
]