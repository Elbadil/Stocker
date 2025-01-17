from django.core.mail import send_mail, EmailMultiAlternatives
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
import os
from ..models import User, Activity
from ..serializers import (UserSerializer,
                          UserLoginSerializer,
                          UserRegisterSerializer,
                          ChangePasswordSerializer,
                          ResetPasswordSerializer,
                          ActivitySerializer)
from ..auth import TokenVersionAuthentication
from ..utils import get_tokens_for_user, set_refresh_token
from utils.pagination import CustomCursorPagination


class CustomTokenRefreshView(APIView):
    """Handles Token Refresh"""
    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return Response({'errors': 'No refresh_token found in cookies.'},
                            status=status.HTTP_401_UNAUTHORIZED)
        try:
            refresh = RefreshToken(refresh_token)
            user_id = refresh.payload['user_id']
            refresh_version = refresh.payload['token_version']
            user = User.objects.get(id=user_id)
            if user.token_version != refresh_version:
                return Response({'errors': 'Invalid or expired token.'},
                                status=status.HTTP_403_FORBIDDEN)
            new_access_token = str(refresh.access_token)
            user_data = UserSerializer(user, context={'request': request}).data
            return Response({'access_token': new_access_token,
                             'user': user_data},
                            status=status.HTTP_200_OK)
        except TokenError:
            return Response({'errors': 'Invalid refresh token.'},
                            status=status.HTTP_401_UNAUTHORIZED)
        except User.DoesNotExist:
            return Response({'errors': 'User not found.'},
                            status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'errors': str(e)},
                            status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """Handles User Login"""
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            user_data = UserSerializer(user, context={'request': request}).data
            token = get_tokens_for_user(user)
            response = Response({'access_token': token['access'],
                                 'user': user_data},
                                 status=status.HTTP_200_OK)
            set_refresh_token(response, token['refresh'], token['refresh_payload'])
            return response
        return Response(serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST)


class SignUpView(APIView):
    """Handles User Registration"""
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            send_mail(
                "Welcome to Stocker",
                f"You have Successfully Created A Stocker Account.",
                os.getenv('EMAIL_HOST_USER'),
                [user.email],
                # fail_silently: A boolean. When it’s False, send_mail()
                # will raise an smtplib.SMTPException if an error occurs.
                fail_silently=False
            )
            user_data = UserSerializer(user).data
            token = get_tokens_for_user(user)
            response = Response({'access_token': token['access'],
                                 'user': user_data},
                                 status=status.HTTP_200_OK)

            set_refresh_token(response, token['refresh'], token['refresh_payload'])
            return response
        return Response(serializer.errors,
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


class GetUpdateUserView(RetrieveUpdateAPIView):
    """Handles User Info Update"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    parser_classes = (FormParser, MultiPartParser,)
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def put(self, request, *args, **kwargs):
        print(request.data)
        user = self.get_object()
        if 'avatar_deleted' in request.data:
            user.avatar = None
            user.save()
        return super().put(request, *args, **kwargs)


class ChangePasswordView(APIView):
    """Handles User Password Update"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = ChangePasswordSerializer(user=request.user, data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.token_version += 1
            user.save()
            new_token = get_tokens_for_user(user)
            response = Response({'access_token': new_token['access']},
                            status=status.HTTP_200_OK)

            set_refresh_token(response,
                              new_token['refresh'],
                              new_token['refresh_payload'])

            return response
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)


class RequestPasswordReset(APIView):
    """Handles Requests For Password Reset"""
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'errors': 'This field is required.'},
                            status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.filter(email__iexact=email).first()
        if user:
            token_generator = PasswordResetTokenGenerator()
            token = token_generator.make_token(user)
            user_uidb64 = urlsafe_base64_encode(force_bytes(user.id))
            reset_url = f"http://localhost:5173/auth/password-reset/{user_uidb64}/{token}/"
            subject = "Stocker Password Reset"
            from_email = os.getenv('EMAIL_HOST_USER')
            to_email = [user.email]
            text_content = f"You can reset your password here: {reset_url}"
            html_content = f"You can reset your password here <a href='{reset_url}'>{reset_url}</a>."
            # Supports HTML Content
            email = EmailMultiAlternatives(subject, text_content, from_email, to_email)
            # add an HTML version of the email content if email clients accepts html
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=False)
        return Response({'message': 'If the email is associated with an account, a reset link has been sent.'},
                        status=status.HTTP_200_OK)


class ResetPassword(APIView):
    """Handles Password Reset"""
    def post(self, request, uidb64, token):
        try:
            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user and PasswordResetTokenGenerator().check_token(user, token):
            serializer = ResetPasswordSerializer(user=user, data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                user.token_version += 1
                user.save()
                return Response({'message': 'User password has been successfully reset.'},
                                status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors,
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)


class GetUserActivities(generics.ListAPIView):
    """Returns user activities"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = ActivitySerializer
    queryset = Activity.objects.all()
    pagination_class = CustomCursorPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(user=self.request.user)
