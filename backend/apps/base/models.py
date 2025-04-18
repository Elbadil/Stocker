from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from utils.tokens import Token
from utils.models import BaseModel


class UserManager(BaseUserManager):
    """Custom User Manager Model"""
    def create_user(self, email, password=None, **extra_fields):
        """
        Creates and returns a regular
        User with the given email and password
        """
        # This ensures that a user cannot be created without an email address.
        if not email:
            raise ValueError(_('The Email field must be set'))

        try:
            validate_email(email)
        except ValidationError as e:
            raise ValueError(_('Invalid email address.'))

        # Email normalization typically converts the email address to a consistent
        # lowercase format ensuring uniqueness and consistency in database operations.
        email = self.normalize_email(email)

        # Uses self.model (which refers to the user model managed by this manager,
        # likely a subclass of AbstractUser or a custom user model
        # inheriting from AbstractBaseUser) to create a new instance of the user model.
        user = self.model(email=email, **extra_fields)

        # Ensure password is provided, if not, raise an error
        if not password:
            raise ValueError(_('The Password field must be set'))

        # Validate password using Django's built-in password validation
        try:
            validate_password(password, user)
        except ValidationError as e:
            raise ValueError(_('Password validation failed: ') + str(e))

        # This method handles hashing the password securely before saving
        # it in the database
        user.set_password(password)

        # Saves the user instance to the database 
        user.save(using=self._db)

        # Returns the created user instance (user) once 
        # it has been successfully saved to the database.
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """ Creates and returns a SuperUser with the given email
        password and other fields"""
        # Ensures that the is_staff field and is_superuser
        # is set to True if it hasn't been provided in extra_fields.
        # This gives the superuser staff and superuser status.
        extra_fields.setdefault('is_staff', True)
        # the set_default python built-in function 
        # sets a value to a key if the key is not found.
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(email, password, **extra_fields)


def user_avatar_path(user, filename):
    """Determine upload path for user avatar."""
    return f"base/images/user/{user.id}/{filename}"

class User(AbstractUser):
    """Custom User Model"""
    id = models.UUIDField(default=Token.generate_uuid,
                          unique=True, primary_key=True, editable=False)
    username = models.CharField(max_length=200, unique=True,
                                null=False, blank=False)
    first_name = models.CharField(max_length=200, null=False, blank=False)
    last_name = models.CharField(max_length=200, null=False, blank=False)
    email = models.EmailField(unique=True, blank=False)
    # Additional Attributes
    bio = models.TextField(null=True, blank=True)
    avatar = models.ImageField(null=True, blank=True, upload_to=user_avatar_path)
    token_version = models.IntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    # In Django, the objects attribute in a model class
    # defines the default manager for that model
    objects = UserManager() # Link UserManager to User model

    def __str__(self) -> str:
        return self.username


class Activity(BaseModel):
    """Activity Model"""
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name="activities")
    action = models.CharField(max_length=50)
    model_name = models.CharField(max_length=50)
    object_ref = models.JSONField(default=list)

    def __str__(self):
        return (
            f"{self.user.username} "
            f"{self.action} {self.model_name} "
            f"{self.object_ref}"
        )
