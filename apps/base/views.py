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
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
import os
from .models import User
from .serializers import (UserSerializer,
                          UserLoginSerializer,
                          UserRegisterSerializer,
                          ChangePasswordSerializer)
from utils.tokens import Token


class CustomTokenRefreshView(APIView):
    """Handles Token Refresh"""
    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return Response({'errors': 'No refresh_token found in cookies.'},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            refresh = RefreshToken(refresh_token)
            new_access_token = str(refresh.access_token)
            user_id = refresh.payload['user_id']
            user = User.objects.get(id=user_id)
            user_data = UserSerializer(user, context={'request': request}).data
            return Response({'user': user_data,
                             'access_token': new_access_token},
                            status=status.HTTP_200_OK)
        except TokenError as e:
            return Response({'errors': str(e)},
                            status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """Handles User Login"""
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            user_data = UserSerializer(user, context={'request': request}).data
            refresh = RefreshToken.for_user(user)
            response = Response({'access_token': str(refresh.access_token),
                                 'user': user_data},
                                status=status.HTTP_200_OK)
            response.set_cookie(
                key="refresh_token",
                value=str(refresh),
                httponly=True,
                secure=True,
                samesite='Lax'
            )
            return response
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
            refresh_token = request.COOKIES.get('refresh_token')
            if not refresh_token:
                return Response({'errors': 'No refresh token found.'},
                                status=status.HTTP_400_BAD_REQUEST)
            token = RefreshToken(refresh_token)
            token.blacklist()
            response = Response({'message': 'User has successfully logged out.'},
                                status=status.HTTP_205_RESET_CONTENT)
            response.delete_cookie('refresh_token')
            return response

        except (InvalidToken, TokenError) as e:
            response = Response({'errors': str(e)},
                            status=status.HTTP_400_BAD_REQUEST)
            response.delete_cookie('refresh_token', None)
            return response

        except Exception as e:
            response = Response({'errors': 'An unexpected error occurred.'},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            response.delete_cookie('refresh_token', None)
            return response


class GetUpdateUserView(RetrieveUpdateAPIView):
    """Handles User Info Update"""
    permission_classes = (IsAuthenticated,)
    parser_classes = (FormParser, MultiPartParser,)
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'id'

    def put(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data)
        if serializer.is_valid():
            user = serializer.save();
            if 'avatar_deleted' in request.data:
                user.avatar = None
            elif 'avatar' in request.FILES:
                user.avatar = request.FILES.get('avatar');
            user.save()
            user_data = UserSerializer(user, context={'request': request}).data
            return Response({'user': user_data},
                            status=status.HTTP_200_OK)
        return Response({'errors': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """Handles User Password Update"""
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = ChangePasswordSerializer(user=request.user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Password has been updated successfully'},
                            status=status.HTTP_200_OK)
        else:
            return Response({'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


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
