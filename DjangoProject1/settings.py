"""
Django settings for DjangoProject1 project.
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-y6_u!mqip_&yv!q5-!on4!4!f4_*%q3z72nr(3n7l)@j_c-sj8'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False  # ЗМІНЕНО НА False ДЛЯ RENDER

ALLOWED_HOSTS = [
    'my-travel-site.onrender.com',
    'localhost',
    '127.0.0.1',

    # ⭐️⭐️⭐️ ДЛЯ МАЙБУТНЬОГО ДОМЕНУ ⭐️⭐️⭐️
    # -----------------------------------------------------------------
    # Після купівлі домену:
    # 1. Замініть 'your-domain.com' на свій домен
    # 2. Розкоментуйте (видаліть #) обидва рядки нижче
    # 3. Зробіть git commit та git push
    # 4. Налаштуйте домен у Render (Custom Domain)
    # -----------------------------------------------------------------
    # 'your-domain.com',
    # 'www.your-domain.com',
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'users',
    'tours',
    'smart_selects',
    'constructor',
    'landing',
]

SITE_URL = 'https://my-travel-site.onrender.com'  # Змініть на ваш URL

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'constructor.middleware.AgentSiteMiddleware',
    'constructor.middleware.AgentColorsMiddleware',
]

ROOT_URLCONF = 'DjangoProject1.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'DjangoProject1.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTH_USER_MODEL = 'users.User'

# Internationalization
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'
LANGUAGE_CODE = 'uk-ua'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images) - ВИПРАВЛЕНО ДЛЯ RENDER
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # ← ДОДАНО
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# Media files (для завантажених файлів) - ТИМЧАСОВО
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

APPEND_SLASH = True

# Email settings - через Gmail (працює)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'soniasadness627@gmail.com'
EMAIL_HOST_PASSWORD = 'evyiikohyqedvtsq'
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# Gemini API
GEMINI_API_KEY = "AIzaSyAlyvwC7SmSESF7YpCOUJRuYgTLIP7b7L4"