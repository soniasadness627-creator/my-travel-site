"""
Django settings for DjangoProject1 project.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

# Завантажуємо змінні з .env файлу
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-y6_u!mqip_&yv!q5-!on4!4!f4_*%q3z72nr(3n7l)@j_c-sj8')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = [
    'my-travel-site.onrender.com',
    'localhost',
    '127.0.0.1',
    '.onrender.com',  # Додано для всіх піддоменів Render
    'clubdatour.com.ua',           # ← ДОДАНО ВАШ ДОМЕН
    'www.clubdatour.com.ua',       # ← ДОДАНО ВАШ ДОМЕН (з www)
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
            ],
        },
    },
]

WSGI_APPLICATION = 'DjangoProject1.wsgi.application'

# ========== БАЗА ДАНИХ ==========
# Визначаємо, чи ми на Render
IS_RENDER = os.getenv('RENDER', 'False') == 'True'

if IS_RENDER or 'gunicorn' in sys.argv[0]:
    # На Render - PostgreSQL
    DATABASE_URL = os.getenv('DATABASE_URL')
    if DATABASE_URL:
        DATABASES = {
            'default': dj_database_url.config(
                default=DATABASE_URL,
                conn_max_age=600,
                ssl_require=False
            )
        }
    else:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }
elif 'collectstatic' in sys.argv:
    # Для collectstatic - SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    # Локально - SQLite
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
# ========== НАЛАШТУВАННЯ ПЕРЕНАПРАВЛЕНЬ ==========
LOGIN_REDIRECT_URL = '/home/'  # Після входу перенаправляти на /home/
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

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
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
    DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'soniasadness627@gmail.com')
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = os.getenv('GMAIL_USER', 'soniasadness627@gmail.com')
    EMAIL_HOST_PASSWORD = os.getenv('GMAIL_PASSWORD', 'evyiikohyqedvtsq')
    DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# ========== НАЛАШТУВАННЯ ДЛЯ RENDER (уникнення циклу перенаправлень) ==========
# Render вже забезпечує SSL, тому Django не потрібно перенаправляти
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

# Тимчасово вимкнути перенаправлення на HTTPS, поки не налагодимо
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# ========== БЕЗПЕКА ДЛЯ ПРОДАКШЕНУ (оновлена) ==========
if not DEBUG:
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    # SECURE_SSL_REDIRECT = True  # ТИМЧАСОВО ВИМКНУТО
    # SESSION_COOKIE_SECURE = True  # ТИМЧАСОВО ВИМКНУТО
    # CSRF_COOKIE_SECURE = True  # ТИМЧАСОВО ВИМКНУТО
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

# Gemini API ключ для чат-бота
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyAlyvwC7SmSESF7YpCOUJRuYgTLIP7b7L4')

# ========== НАЛАШТУВАННЯ ПОРТУ ДЛЯ RENDER ==========
# Отримуємо порт зі змінних оточення Render
PORT = os.getenv('PORT', '10000')

# ========== ТИМЧАСОВА ДІАГНОСТИКА - ВИДАЛИТИ ПІСЛЯ ПЕРЕВІРКИ ==========
if 'gunicorn' in sys.argv[0]:
    print("=== ДІАГНОСТИКА GUNICORN ===")
    print(f"GMAIL_USER: {os.getenv('GMAIL_USER', 'Не знайдено!')}")
    print(f"GMAIL_PASSWORD: {'Знайдено (приховано)' if os.getenv('GMAIL_PASSWORD') else 'Не знайдено!'}")
    print(f"DATABASE_URL: {'Знайдено' if os.getenv('DATABASE_URL') else 'Не знайдено!'}")
    print(f"PORT: {os.getenv('PORT', 'Не знайдено!')}")
    print("===========================")