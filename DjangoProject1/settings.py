"""
Django settings for DjangoProject1 project.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

# ========== ІНІЦІАЛІЗАЦІЯ CLOUDINARY ==========
import cloudinary
import cloudinary.uploader
import cloudinary.api

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME', 'djvycubir'),
    api_key=os.getenv('CLOUDINARY_API_KEY', '649993464552661'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET', 'kwwtOaPRA4fv4-_QpL-0sxyRVZ0'),
    secure=True
)

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-y6_u!mqip_&yv!q5-!on4!4!f4_*%q3z72nr(3n7l)@j_c-sj8')
DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = [
    'my-travel-site.onrender.com',
    'localhost',
    '127.0.0.1',
    '.onrender.com',
    'clubdatour.com.ua',
    'www.clubdatour.com.ua',
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
    'cloudinary',
    'cloudinary_storage',
]

SITE_URL = os.getenv('SITE_URL', 'https://my-travel-site.onrender.com')

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
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
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
                'DjangoProject1.context_processors.add_user_to_context',
            ],
            'debug': True,
        },
    },
]

WSGI_APPLICATION = 'DjangoProject1.wsgi.application'

# ========== БАЗА ДАНИХ – ЛОКАЛЬНО SQLite, НА СЕРВЕРІ PostgreSQL ==========
IS_LOCAL_COMMAND = any(x in sys.argv for x in ['runserver', 'migrate', 'makemigrations', 'shell'])

if IS_LOCAL_COMMAND:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
    print("⚠️ Локальна розробка: використовується SQLite")
else:
    DATABASE_URL = os.getenv('DATABASE_URL')
    if DATABASE_URL:
        DATABASES = {
            'default': dj_database_url.config(
                default=DATABASE_URL,
                conn_max_age=600,
                ssl_require=False
            )
        }
        print(f"✅ Сервер: використовується PostgreSQL")
    else:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }
        print("⚠️ Сервер: DATABASE_URL не знайдено, використовується SQLite")

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTH_USER_MODEL = 'users.User'

# Internationalization
LOGIN_REDIRECT_URL = '/home/'
LOGIN_URL = '/admin/login/'
LOGOUT_REDIRECT_URL = '/'
LANGUAGE_CODE = 'uk-ua'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ========== СТАТИЧНІ ФАЙЛИ ==========
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ========== МЕДІА ФАЙЛИ (CLOUDINARY) ==========
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.getenv('CLOUDINARY_CLOUD_NAME', 'djvycubir'),
    'API_KEY': os.getenv('CLOUDINARY_API_KEY', '649993464552661'),
    'API_SECRET': os.getenv('CLOUDINARY_API_SECRET', 'kwwtOaPRA4fv4-_QpL-0sxyRVZ0'),
}

STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_URL = '/media/'
APPEND_SLASH = True

# ========== EMAIL НАЛАШТУВАННЯ ==========
USE_AWS_SES = os.getenv('USE_AWS_SES', 'False') == 'True'

if USE_AWS_SES:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.getenv('AWS_SES_HOST', 'email-smtp.eu-north-1.amazonaws.com')
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = os.getenv('AWS_SES_USERNAME', '')
    EMAIL_HOST_PASSWORD = os.getenv('AWS_SES_PASSWORD', '')
    DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@clubdatour.com.ua')
    print("✅ AWS SES для відправки email")
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = os.getenv('GMAIL_USER', 'soniasadness627@gmail.com')
    EMAIL_HOST_PASSWORD = os.getenv('GMAIL_PASSWORD', '')
    DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
    print("✅ Gmail для відправки email")

# ========== НАЛАШТУВАННЯ ДЛЯ RENDER ==========
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_REFERRER_POLICY = 'unsafe-url'

if not DEBUG:
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

# API ключі
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyAlyvwC7SmSESF7YpCOUJRuYgTLIP7b7L4')
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY', '')

PORT = os.getenv('PORT', '10000')

# Діагностика для Gunicorn
if 'gunicorn' in sys.argv[0]:
    print("=== ДІАГНОСТИКА GUNICORN ===")
    print(f"GMAIL_USER: {os.getenv('GMAIL_USER', 'Не знайдено!')}")
    print(f"GMAIL_PASSWORD: {'Знайдено' if os.getenv('GMAIL_PASSWORD') else 'Не знайдено!'}")
    print(f"DATABASE_URL: {'Знайдено' if os.getenv('DATABASE_URL') else 'Не знайдено!'}")
    print(f"PORT: {os.getenv('PORT', 'Не знайдено!')}")
    print("===========================")

# Логування
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
    'loggers': {
        'django': {'handlers': ['console'], 'level': 'INFO'},
        'django.request': {'handlers': ['console'], 'level': 'DEBUG', 'propagate': False},
    },
}

print("✅ Cloudinary ініціалізовано")