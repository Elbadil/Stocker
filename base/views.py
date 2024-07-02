from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import logout, authenticate, login
from django.core.mail import send_mail
from django.contrib import messages
from datetime import datetime, timezone
import os
from .models import User
from .forms import SignUpForm
from .tokens import Token


def home(request):
    """Home"""
    context = {
        'title': 'Home'
    }
    return render(request, 'home.html', context)


def userLogin(request):
    """Login"""
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
            return render(request, 'users/login.html', context)
        user_password = request.POST['password']
        user = authenticate(request, email=user_email, password=user_password)
        if user:
            login(request, user)
            if not user.is_confirmed:
                messages.info(request, 'Your Account has not been confirmed yet. \
                              Please take some few minutes to confirm your account!')
                return redirect('confirm-account')
            else:
                next_page = request.GET.get('next')
                return redirect(next_page) if next_page else redirect('home')
        else:
            messages.error(request, 'Login Unsuccessful. Please check your email and password')
            context['user_email'] = user_email

    return render(request, 'users/login.html', context)


def userLogout(request):
    """Logs out the request user"""
    logout(request)
    return redirect('home')


def userSignUp(request):
    """User Registration"""
    form = SignUpForm()
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            confirm_code = Token.generate(6)
            user = form.save(commit=False)
            user.confirm_code = confirm_code
            user.save()
            # Sending Account Confirmation code via Email
            send_mail(
                "Stocker Account Confirmation",
                f"Account Confirmation Code: {confirm_code}",
                os.getenv('EMAIL_HOST_USER'),
                [user.email],
                # fail_silently: A boolean. When it’s False, send_mail()
                # will raise an smtplib.SMTPException if an error occurs.
                fail_silently=False
            )
            login(request, user)
            messages.success(request, 'You have successfully created an account! \
                            Please Confirm your account by entering the confirmation \
                            code that was sent to your email to complete registration.')
            return redirect('confirm-account')
    context = {
        'title': 'Sign Up',
        'form': form
    }
    return render(request, 'users/register.html', context)


def confirmAccount(request):
    """Confirm Account"""
    user = request.user
    if user.is_confirmed:
        return redirect('home')
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
            return redirect(next_page) if next_page else redirect('home')
        else:
            context['confirm_code'] = confirm_code
            messages.error(request, 'Invalid Confirmation Code. Please request another code!')
            return render(request, 'users/confirm_account.html', context)
    return render(request, 'users/confirm_account.html', context)


def resendConfirmCode(request):
    """Resend a new confirmation code"""
    user = request.user
    if user.is_confirmed:
        return redirect('home')
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
