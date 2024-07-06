from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.forms import ModelForm
from django.core.exceptions import ValidationError
from .models import User


class AddFormControlClassMixin:
    """Mixin to add 'form-control' class to form fields"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs) # Calls the next class in the MRO, which is PasswordChangeForm
        # This statement calls the next class in the MRO that has
        # an __init__ method that accepts *args and **kwargs.
        # If PasswordChangeForm.__init__ also includes
        # super().__init__(*args, **kwargs), Python will continue up
        # the MRO to the next class, typically forms.Form or
        # another base class that eventually
        # initializes all necessary attributes and methods for the form.
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class SignUpForm(AddFormControlClassMixin, UserCreationForm):
    """User Sign up Form"""
    class Meta:
        model = User
        fields = ('username',
                  'first_name',
                  'last_name',
                  'email',
                  'password1',
                  'password2')


class UpdateUserForm(AddFormControlClassMixin, ModelForm):
    """Update User Form"""
    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'bio',
            'avatar'
        ]

    def __init__(self, *args, **kwargs):
        # Extract the 'user' parameter from kwargs
        self.user = kwargs.pop('user', None)
        # Call the superclass's initializer with the remaining args and kwargs
        super().__init__(*args, **kwargs)

    # The clean_* methods are called during the form.is_valid() check
    # so by the time you call save(), you can be confident that
    # all form-level validations have passed.
    def clean_username(self):
        username = self.cleaned_data['username']
        # Check if a user with the same username (case-insensitive) already exists
        if User.objects.filter(username__iexact=username).exclude(pk=self.user.id).exists():
            raise ValidationError('This username is already taken.')
        return username.lower()


class UpdatePasswordForm(AddFormControlClassMixin, PasswordChangeForm):
    """Update User Password Form"""
    pass
