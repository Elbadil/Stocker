from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('home/', views.home, name='home'),
    path('login/', views.userLogin, name='login'),
    path('logout/', views.userLogout, name='logout'),
    path('signup/', views.userSignUp, name='register'),
    path('confirm-account/', views.confirmAccount, name='confirm-account'),
    path('resend-code/', views.resendCode, name='resend-code'),
]