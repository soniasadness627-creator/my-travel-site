"""
Django settings for DjangoProject1 project.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

# ========== ІМПОРТ ДЛЯ НАЛАШТУВАННЯ БАЗИ ДАНИХ ==========
from django.db.backends.signals import connection_created

# ========== ІНІЦІАЛІЗАЦІЯ CLOUDINARY ==========
import cloudinary
import cloudinary.uploader
import cloudinary.api

# Завантажуємо .env файл
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ========== ПЕРЕВІРКА НАЯВНОСТІ ОБОВ'ЯЗКОВИХ ЗМІННИХ ==========
required_env_vars = [
    'SECRET_KEY',
    'CLOUDINARY_CLOUD_NAME',
    'CLOUDINARY_API_KEY',
    'CLOUDINARY_API_SECRET',
    'DATABASE_URL',
]

missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"❌ Відсутні обов'язкові змінні в .env: {', '.join(missing_vars)}")

# ========== НАЛАШТУВАННЯ CLOUDINARY ==========
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET'),
    secure=True
)

# ========== БЕЗПЕЧНІ НАЛАШТУВАННЯ ==========
SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG', 'False') == 'True'

# Отримуємо ALLOWED_HOSTS з .env
ALLOWED_HOSTS = [host.strip() for host in os.getenv('ALLOWED_HOSTS', '').split(',') if host.strip()]
# Додаємо базові хоcти для локальної розробки
if DEBUG:
    ALLOWED_HOSTS.extend(['localhost', '127.0.0.1'])

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

SITE_URL = os.getenv('SITE_URL', 'https://clubdatour.com.ua')

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
    'constructor.middleware.SubdomainMiddleware',
    'constructor.middleware.AgentColorsMiddleware',
    'tours.middleware.TourTrackingMiddleware',
    'constructor.middleware.DatabaseConnectionMiddleware',
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
            'debug': DEBUG,
        },
    },
]

WSGI_APPLICATION = 'DjangoProject1.wsgi.application'

# ========== БАЗА ДАНИХ ==========
IS_LOCAL_COMMAND = any(x in sys.argv for x in ['runserver', 'migrate', 'makemigrations'])

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
                conn_health_checks=True,
                ssl_require=True
            )
        }
        print(f"✅ Сервер: використовується PostgreSQL")
    else:
        raise ValueError("❌ DATABASE_URL не знайдено в .env для серверного режиму!")

# ========== НАЛАШТУВАННЯ KEEPALIVE ДЛЯ БАЗИ ДАНИХ ==========
def activate_keepalive(sender, connection, **kwargs):
    """Встановлює keepalive параметри для PostgreSQL з'єднання"""
    if connection.vendor == 'postgresql':
        with connection.cursor() as cursor:
            cursor.execute("SET tcp_keepalives_idle = 60")
            cursor.execute("SET tcp_keepalives_interval = 10")
            cursor.execute("SET tcp_keepalives_count = 5")

connection_created.connect(activate_keepalive)

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
    'CLOUD_NAME': os.getenv('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': os.getenv('CLOUDINARY_API_KEY'),
    'API_SECRET': os.getenv('CLOUDINARY_API_SECRET'),
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

# ========== НАЛАШТУВАННЯ ДЛЯ RENDER ТА CLOUDFLARE ==========
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_REFERRER_POLICY = 'unsafe-url'

# Довірені origin для CSRF (важливо для Cloudflare)
CSRF_TRUSTED_ORIGINS = [
    'https://clubdatour.com.ua',
    'https://www.clubdatour.com.ua',
]
# Додаємо всі піддомени
for host in ALLOWED_HOSTS:
    if host.startswith('.'):
        CSRF_TRUSTED_ORIGINS.append(f'https://{host[1:]}')

if not DEBUG:
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

# API ключі
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY', '')

PORT = os.getenv('PORT', '10000')

# ========== ЛОГУВАННЯ ==========
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'errors.log',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO' if not DEBUG else 'DEBUG',
    },
    'loggers': {
        'django': {'handlers': ['console'], 'level': 'INFO'},
        'django.request': {'handlers': ['console', 'file'], 'level': 'ERROR', 'propagate': False},
    },
}

# Створюємо директорію для логів
LOGS_DIR = BASE_DIR / 'logs'
if not LOGS_DIR.exists():
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

# ========== КЕШУВАННЯ ==========
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# ========== TELEGRAM БОТ ==========
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_ADMIN_IDS_STR = os.getenv('TELEGRAM_ADMIN_IDS', '')
TELEGRAM_ADMIN_IDS = []
if TELEGRAM_ADMIN_IDS_STR:
    TELEGRAM_ADMIN_IDS = [int(x.strip()) for x in TELEGRAM_ADMIN_IDS_STR.split(',') if x.strip()]

# ========== EMAIL НАЛАШТУВАННЯ ==========
USE_SENDGRID = os.getenv('USE_SENDGRID', 'True') == 'True'
USE_AWS_SES = os.getenv('USE_AWS_SES', 'False') == 'True'

if USE_SENDGRID:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.sendgrid.net'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = 'apikey'
    EMAIL_HOST_PASSWORD = os.getenv('SENDGRID_API_KEY', '')
    DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'ClubDatour <info@clubdatour.com.ua>')
    SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY', '')
    print("✅ ВСІ листи надсилаються через SENDGRID")

elif USE_AWS_SES:
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
    EMAIL_HOST_USER = os.getenv('GMAIL_USER', '')
    EMAIL_HOST_PASSWORD = os.getenv('GMAIL_PASSWORD', '')
    DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
    print("✅ Gmail для відправки email")

# Mailgun для масових розсилок (опціонально)
MAILGUN_API_KEY = os.getenv('MAILGUN_API_KEY', '')
MAILGUN_DOMAIN = os.getenv('MAILGUN_DOMAIN', '')
MAILGUN_FROM_EMAIL = os.getenv('MAILGUN_FROM_EMAIL', '')

print("✅ Cloudinary ініціалізовано")
if TELEGRAM_ADMIN_IDS:
    print(f"✅ Telegram бот налаштовано. Адмінів: {len(TELEGRAM_ADMIN_IDS)}")