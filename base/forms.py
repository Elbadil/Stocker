from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm
from .models import User


class BaseForm(ModelForm):
    """Adding a class attribute with a value of form-control
    to Form Fields"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class SignUpForm(BaseForm, UserCreationForm):
    """User Sign up Form"""
    class Meta:
        model = User
        fields = ('username',
                  'first_name',
                  'last_name',
                  'email',
                  'password1',
                  'password2')


class UpdateUserForm(BaseForm, ModelForm):
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
