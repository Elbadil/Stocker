from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import logout, authenticate, login
from django.core.mail import send_mail
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from datetime import datetime, timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from django.middleware.csrf import get_token
import os
from .models import User
from .forms import UpdateUserForm, UpdatePasswordForm
from .serializers import (UserSerializer,
                          UserLoginSerializer,
                          UserRegisterSerializer)
from utils.tokens import Token


@api_view(['GET'])
def get_csrf_token(request):
    """Returns the CSRF token that will be used in
    form submission from the frontend."""
    token = get_token(request)
    return Response({'csrfToken': token}, status=status.HTTP_200_OK)


class LoginView(APIView):
    """Handles User Login"""
    def post(self, request):
        print(request.data)
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)
            user_data = UserSerializer(user, context={'request': request}).data
            return Response({'user': user_data},
                             status=status.HTTP_200_OK)
        return Response({'errors': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)


class SignUpView(APIView):
    """Handles User Registration"""
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)

        if serializer.is_valid():
            confirm_code = Token.generate_token_with_length(6)
            user = serializer.save()
            user.confirm_code = confirm_code
            user.save()
            send_mail(
                "Stocker Account Confirmation",
                f"Account Confirmation Code: {confirm_code}",
                os.getenv('EMAIL_HOST_USER'),
                [user.email],
                # fail_silently: A boolean. When it’s False, send_mail()
                # will raise an smtplib.SMTPException if an error occurs.
                fail_silently=False
            )
            return Response({'message': f'User has been registered'},
                              status=status.HTTP_201_CREATED)
        return Response({'errors': serializer.errors},
                         status=status.HTTP_400_BAD_REQUEST)


@login_required(login_url="login")
def userLogout(request):
    """Logs out the request user"""
    logout(request)
    return redirect('login')


@login_required(login_url="login")
def confirmAccount(request):
    """Confirm Account"""
    user = request.user
    if user.is_confirmed:
        return redirect('index')
    context = {'title': 'Confirm Account'}
    # To handle Send Code text
    referring_url = request.META.get('HTTP_REFERER')
    if referring_url and 'signup' in referring_url:
        context['from_signup'] = True
    if request.method == 'POST':
        confirm_code = request.POST.get('confirm_code')
        confirm_code_is_valid = Token.validation(user.confirm_code_created_at, 3)
        if user.confirm_code == confirm_code and confirm_code_is_valid:
            user.is_confirmed = True
            user.save()
            messages.success(request, 'You have successfully confirmed your account!')
            next_page = request.GET.get('next')
            return redirect(next_page) if next_page else redirect('index')
        else:
            context['confirm_code'] = confirm_code
            messages.error(request, 'Invalid Confirmation Code. Please request another code!')
            return render(request, 'confirm_account.html', context)
    return render(request, 'confirm_account.html', context)


@login_required(login_url='login')
def resendConfirmCode(request):
    """Resend a new confirmation code"""
    user = request.user
    if user.is_confirmed:
        return redirect('index')
    new_confirm_code = Token.generate(6)
    user.confirm_code = new_confirm_code
    user.confirm_code_created_at = datetime.now(timezone.utc)
    user.save()
    send_mail(
        "Stocker Account Confirmation",
        f"Account Confirmation Code: {new_confirm_code}",
        os.getenv('EMAIL_HOST_USER'),
        [user.email],
        fail_silently=False
    )
    messages.success(request, 'A new confirmation code has been sent to you via email!')
    return redirect('confirm-account')


def userConfirmed(request, user):
    """Checks if the request user is confirmed"""
    if not user.is_confirmed:
        messages.info(request, 'You need to confirm your account to perform such action. \
                      Please take some few minutes to confirm your account!')
    return user.is_confirmed


@login_required(login_url='login')
def userProfile(request, user_id):
    """User Profile"""
    user = User.objects.get(id=user_id)
    # checks if the request user account is confirmed
    if not userConfirmed(request, user):
        return redirect('confirm-account')

    # check if request user is the same as the profile user
    if request.user != user:
        return HttpResponse('Unauthorized')

    profile_form = UpdateUserForm(instance=user)
    pwd_form = UpdatePasswordForm(user=user)

    if request.method == 'POST':
        if 'profile_form' in request.POST:
            profile_form = UpdateUserForm(request.POST, request.FILES, instance=user, user=user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'You have successfully updated your Profile Settings!')
        elif 'pwd_form' in request.POST:
            pwd_form = UpdatePasswordForm(user=user, data=request.POST)
            if pwd_form.is_valid():
                pwd_form.save()
                update_session_auth_hash(request, pwd_form.user)  # Important for keeping the user logged in
                messages.success(request, 'You have successfully updated your password!')
    context = {
        'title': user.username,
        'user': user,
        'profile_form': profile_form,
        'pwd_form': pwd_form
    }
    return render(request, 'profile.html', context)
