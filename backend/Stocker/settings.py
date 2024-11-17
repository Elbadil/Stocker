"""
Django settings for Stocker project.

Generated by 'django-admin startproject' using Django 4.2.13.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path
import os
from django.contrib import messages
from datetime import timedelta

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-fv#p*xv9dss50tjl!pr#$(vh10o16u4@rzpx9+gl3plpig!_md'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'apps.base',
    'apps.inventory',
    'apps.client_orders',
    'apps.supplier_orders',
    'django_extensions',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders'
]

# Emailing Settings
# This line specifies the backend to use for sending emails. In this case
# it's using SMTP (django.core.mail.backends.smtp.EmailBackend),
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# specifies whether to use TLS (Transport Layer Security) 
# for secure communication with the SMTP server
EMAIL_USE_TLS = True
# specifies the SMTP server host to use for sending emails.
# Here, it's set to Gmail's SMTP server.
EMAIL_HOST = 'smtp.gmail.com'
# The username (typically your email address) used to authenticate
# with the SMTP server specified in EMAIL_HOST
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
# The password or app-specific password used to authenticate
# with the SMTP server specified in EMAIL_HOST
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_APP_PWD')
# specifies the port to use for the SMTP server specified in EMAIL_HOST.
# Port 587 is the standard port for SMTP over TLS
EMAIL_PORT = 587

# Defining our custom User Model that will be used for auth and all user features
AUTH_USER_MODEL = 'base.User'

# Flash Messages Tags
MESSAGE_TAGS = {
    messages.DEBUG: 'alert-info',
    messages.INFO: 'alert-info',
    messages.SUCCESS: 'alert-success',
    messages.WARNING: 'alert-warning',
    messages.ERROR: 'alert-danger',
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware'
]

# Cors and Csrf Congig
CSRF_TRUSTED_ORIGINS = [
  "http://localhost:5173",
]
CORS_ALLOWED_ORIGINS = [
   "http://localhost:5173",
]
CORS_ALLOW_CREDENTIALS = True

ROOT_URLCONF = 'Stocker.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates'
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'Stocker.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        #'ENGINE': 'django.db.backends.sqlite3',
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DATABASE'),
        'USER': os.getenv('USER'),
        'PASSWORD': os.getenv('PASSWORD'),
        'HOST': os.getenv('HOST'),
        'PORT': os.getenv('PORT')
    }
}

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# DRF Auth
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

# JWT Token Config
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=15),
}


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

# Defining the base URL for serving static files.
STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Where we can display our images
# The base URL that will be used to serve media files.
MEDIA_URL = '/media/'

# Specifying the path for our static content
# Specify additional directories where static files are stored.
STATICFILES_DIRS = [
    BASE_DIR / 'static'
]

# User uploaded content | Where we'll be saving the user's images ..
# The filesystem path where media files are stored.
MEDIA_ROOT = BASE_DIR / 'static'