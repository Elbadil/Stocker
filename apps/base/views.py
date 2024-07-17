from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import logout, authenticate, login
from django.core.mail import send_mail
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from datetime import datetime, timezone
import os
from .models import User
from .forms import SignUpForm, UpdateUserForm, UpdatePasswordForm
from utils.tokens import Token


@login_required(login_url="login")
def index(request):
    """Home"""
    return render(request, 'index.html')


def userLogin(request):
    """Login"""
    if request.user.is_authenticated:
        return redirect('index')
    errors = {}
    context = {'title': 'Login'}
    if request.method == 'POST':
        user_email = request.POST['email']
        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            errors['login'] = ['Login Unsuccessful. Please check your email and password']
            return JsonResponse({'success': False, 'errors': errors})
        user_password = request.POST['password']
        user = authenticate(request, email=user_email, password=user_password)
        if user:
            login(request, user)
            next_page = request.POST.get('next', '/')
            print(next_page)
            return JsonResponse({'success': True, 'message': 'Successful Login', 'redirect_url': next_page})
        else:
            errors['login'] = ['Login Unsuccessful. Please check your email and password']
            return JsonResponse({'success': False, 'errors': errors})

    return render(request, 'login.html', context)


@login_required(login_url="login")
def userLogout(request):
    """Logs out the request user"""
    logout(request)
    return redirect('login')


def userSignUp(request):
    """User Registration"""
    if request.user.is_authenticated:
        return redirect('index')
    form = SignUpForm()
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            confirm_code = Token.generate_token_with_length(6)
            user = form.save(commit=False)
            user.confirm_code = confirm_code
            user.username = user.username.lower()
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
            return JsonResponse({'success': True, 'message': 'User has been registered'})
        else:
            form_fields = [name for name in form.fields.keys()]
            return JsonResponse({'success': False, 'errors': form.errors, 'fields': form_fields})
    context = {
        'title': 'Sign Up',
        'form': form
    }
    return render(request, 'register.html', context)


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
