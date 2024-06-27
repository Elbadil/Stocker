from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import logout, authenticate, login
from django.contrib import messages
from .models import User
from .forms import SignUpForm


def home(request):
    """Index Page"""
    context = {
        'title': 'Home'
    }
    return render(request, 'home.html', context)


def userLogin(request):
    """Login Page"""
    context = {
        'title': 'Login'
    }
    if request.method == 'POST':
        user_email = request.POST['email']
        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            messages.error(request, 'Email does not Exist')
            context['user_email'] = user_email
            return render(request, 'login.html', context)
        user_password = request.POST['password']
        user = authenticate(email=user_email, password=user_password)
        if user:
            login(request, user)
            next_page = request.GET.get('next')
            return redirect(next_page) if next_page else redirect('home')
        else:
            messages.error(request, 'Login Unsuccessful. Please check your email and password')
            context['user_email'] = user_email

    return render(request, 'login.html', context)


def userLogout(request):
    """Logs out the request user"""
    logout(request)
    return redirect('home')


def userSignUp(request):
    """User Registration Page"""
    form = SignUpForm()
    context = {
        'title': 'Sign Up',
        'form': form
    }
    return render(request, 'register.html', context)
