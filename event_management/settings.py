import os
from pathlib import Path
from django.utils.translation import gettext_lazy as _
import cloudinary
import cloudinary.uploader
import cloudinary.api

# ===== CONFIGURATION DE BASE =====
BASE_DIR = Path(__file__).resolve().parent.parent

# ===== SÉCURITÉ =====
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-8x9y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q')
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

# ===== HÔTES AUTORISÉS =====
ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    '10.206.142.9',
    '192.168.1.*',
    '10.0.0.*',
    '10.206.142.*',
    '.onrender.com',
    'karamu.onrender.com',
]

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://192.168.11.107:8000',
    'http://192.168.11.*:8000',
    'https://*.onrender.com',
    'https://karamu.onrender.com',
]

# ===== APPLICATIONS =====
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'cloudinary',
    'cloudinary_storage',
    "apps.core",
    'apps.authentication',
    'apps.events',
    'apps.guests',
    'apps.payments',
    'apps.expenses',
    "apps.invitation",
]

# ===== MIDDLEWARE =====
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ===== URLS ET TEMPLATES =====
ROOT_URLCONF = 'event_management.urls'

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
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
            ],
        },
    },
]

WSGI_APPLICATION = 'event_management.wsgi.application'

# ===== BASE DE DONNÉES =====
if DEBUG:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('POSTGRES_DB'),
            'USER': os.environ.get('POSTGRES_USER'),
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD'),
            'HOST': os.environ.get('POSTGRES_HOST'),
            'PORT': os.environ.get('POSTGRES_PORT', '5432'),
        }
    }

# ===== VALIDATEURS DE MOTS DE PASSE =====
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ===== AUTHENTIFICATION =====
AUTH_USER_MODEL = 'authentication.User'
LOGIN_URL = 'authentication:login'
LOGIN_REDIRECT_URL = 'events:event_list'
LOGOUT_REDIRECT_URL = 'authentication:login'

# ===== INTERNATIONALISATION =====
LANGUAGE_CODE = 'fr'
TIME_ZONE = 'Africa/Kinshasa'
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ('fr', 'Français'),
    ('en', 'English'),
]

LOCALE_PATHS = [BASE_DIR / 'locale']

# ===== FICHIERS STATIQUES =====
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

if not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ===== FICHIERS MÉDIAS ET CLOUDINARY =====
CLOUDINARY_CLOUD_NAME = 'dtr8o0saj'

if not DEBUG:
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
    
    cloudinary.config(
        cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME', CLOUDINARY_CLOUD_NAME),
        api_key=os.environ.get('CLOUDINARY_API_KEY'),
        api_secret=os.environ.get('CLOUDINARY_API_SECRET'),
        secure=True
    )
    
    MEDIA_URL = f"https://res.cloudinary.com/{os.environ.get('CLOUDINARY_CLOUD_NAME', CLOUDINARY_CLOUD_NAME)}/image/upload/"
else:
    MEDIA_URL = 'media/'
    MEDIA_ROOT = BASE_DIR / 'media'

# ===== PARAMÈTRES GÉNÉRAUX =====
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
GUESTS_PER_PAGE = 20

# ===== SÉCURITÉ PRODUCTION =====
if not DEBUG:
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')