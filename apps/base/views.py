from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from datetime import datetime, timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
import os
from .models import User
from . import serializers
from .utils import get_tokens_for_user
from utils.tokens import Token


class LoginView(APIView):
    """Handles User Login"""
    def post(self, request):
        serializer = serializers.UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            tokens = get_tokens_for_user(request, user)
            return Response({'tokens': tokens},
                             status=status.HTTP_200_OK)
        return Response({'errors': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)


class SignUpView(APIView):
    """Handles User Registration"""
    def post(self, request):
        serializer = serializers.UserRegisterSerializer(data=request.data)

        if serializer.is_valid():
            confirm_code = Token.generate_token_with_length(6)
            user = serializer.save()
            user.confirm_code = confirm_code
            user.save()
            # send_mail(
            #     "Stocker Account Confirmation",
            #     f"Account Confirmation Code: {confirm_code}",
            #     os.getenv('EMAIL_HOST_USER'),
            #     [user.email],
            #     # fail_silently: A boolean. When it’s False, send_mail()
            #     # will raise an smtplib.SMTPException if an error occurs.
            #     fail_silently=False
            # )
            return Response({'message': f'User has been registered'},
                              status=status.HTTP_201_CREATED)
        return Response({'errors': serializer.errors},
                         status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """Handles User Logout"""
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            refresh_token = request.data['refresh']
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'User has successfully logged out.'},
                            status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({'errors': e},
                            status=status.HTTP_400_BAD_REQUEST)


class UpdateUserView(RetrieveUpdateAPIView):
    """Handles User Info Update"""
    permission_classes = (IsAuthenticated,)
    queryset = User.objects.all()
    serializer_class = serializers.UserSerializer
    lookup_field = 'id'

    def patch(self, request, *args, **kwargs):
        response = super().patch(request, *args, **kwargs)
        return self.handle_token_refresh(request, response)

    def put(self, request, *args, **kwargs):
        response = super().put(request, *args, **kwargs)
        return self.handle_token_refresh(request, response)

    def handle_token_refresh(self, request, response):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response({'errors': 'Refresh token is required.'},
                                status=status.HTTP_400_BAD_REQUEST)
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            tokens = get_tokens_for_user(request, request.user)
            response.data['tokens'] = tokens
        except Exception as e:
            return Response({'errors': e},
                            status=status.HTTP_400_BAD_REQUEST)
        return response


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
