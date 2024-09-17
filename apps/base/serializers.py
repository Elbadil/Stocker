from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """User Model Serializer"""
    avatar = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "avatar",
            "bio",
            "is_confirmed"
        ]

    def get_avatar(self, user):
        request = self.context.get('request')
        if user.avatar and request:
            # returns the full URL for the avatar image
            return request.build_absolute_uri(user.avatar.url)
        return None

    def validate_username(self, value):
        if User.objects.filter(username=value.lower()).exists():
            raise serializers.ValidationError('user with this username already exists.')
        return value.lower()
    

class UserRegisterSerializer(serializers.ModelSerializer):
    """User Sign Up Serializer"""
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'password1',
            'password2'
        ]

    def validate_username(self, value):
        if User.objects.filter(username=value.lower()).exists():
            raise serializers.ValidationError('user with this username already exists.')
        return value.lower()

    def validate_email(self, value):
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError('user with this email already exists.')
        return value.lower()

    def validate_passwords(self, validated_data):
        password1 = validated_data.get('password1')
        password2 = validated_data.get('password2')
        if password1 != password2:
            raise serializers.ValidationError(
                {'password2': "The two password fields do not match."})
        try:
           validate_password(
               password1,
               user=User(
                   username=validated_data.get('username'),
                   first_name=validated_data.get('first_name'),
                   last_name=validated_data.get('last_name'),
                   email=validated_data.get('email')
                )
            )
        except ValidationError as err:
            raise serializers.ValidationError({'password2': err.messages})

    def validate(self, validated_data):
        self.validate_passwords(validated_data)
        return validated_data

    def create(self, validated_data):
        validated_data.pop('password2', None)
        user = User.objects.create_user(
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            email=validated_data['email'],
            password=validated_data['password1'],
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    """User Login Serializer"""
    email = serializers.EmailField(error_messages={'blank': 'Please enter your email address.'})
    password = serializers.CharField(error_messages={'blank': 'Please enter your email password.'})

    def validate(self, validated_data):
        user = authenticate(email=validated_data['email'],
                            password=validated_data['password'])
        if not user:
            raise serializers.ValidationError(
                {"login": "Login Unsuccessful. Please check your email and password"})
        validated_data['user'] = user
        return validated_data


class ChangePasswordSerializer(serializers.Serializer):
    """User Password Change Serializer"""
    old_password = serializers.CharField(write_only=True)
    new_password1 = serializers.CharField(write_only=True)
    new_password2 = serializers.CharField(write_only=True)

    def __init__(self, *args, **kwargs):
        self.user : User = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def validate_old_password(self, value):
        if not self.user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

    def validate(self, validated_data):
        old_password = validated_data['old_password']
        new_password1 = validated_data['new_password1']
        new_password2 = validated_data['new_password2']
        if new_password1 != new_password2:
            raise serializers.ValidationError(
                {'new_password2': 'The two new password fields do not match.'})

        if new_password1 == old_password:
            raise serializers.ValidationError(
                {'new_password2': 'New password cannot be the same as the old password.'})

        try:
            validate_password(new_password1, user=self.user)
        except ValidationError as err:
            raise serializers.ValidationError({'new_password2': err.messages})

        return validated_data

    def save(self, **kwargs):
        new_password1 = self.validated_data['new_password1']
        self.user.set_password(new_password1)
        self.user.save()
        return self.user
