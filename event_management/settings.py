import os
from pathlib import Path

from django.utils.translation import gettext_lazy as _


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-8x9y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q'
DEBUG = True

# ============= MODIFICATION POUR LE WIFI =============
# Ajoutez l'adresse IP de votre machine et autorisez tout le réseau
ALLOWED_HOSTS = [
    '127.0.0.1',           # Localhost (ordinateur lui-même)
    'localhost',           # Localhost (ordinateur lui-même)
    '10.206.142.9',        # Votre IP fixe actuelle
    '192.168.1.*',         # Toute la plage 192.168.1.x (si vous changez de réseau)
    '10.0.0.*',            # Toute la plage 10.0.0.x
    '10.206.142.*',        # Toute la plage de votre réseau actuel
]

# Configuration CSRF pour les requêtes mobiles
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://192.168.11.107:8000',
    'http://192.168.11.*:8000',
]
# =====================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    "apps.core",
    'apps.authentication',  
    'apps.events',
    'apps.guests',
    'apps.payments', 
    'apps.expenses',
    "apps.invitation",
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

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

# Base de données – SQLite (simple, pas de configuration externe)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTH_USER_MODEL = 'authentication.User'
LOGIN_URL = 'authentication:login'
LOGIN_REDIRECT_URL = 'events:event_list'
LOGOUT_REDIRECT_URL = 'authentication:login'

LANGUAGE_CODE = 'fr'
TIME_ZONE = 'Africa/Kinshasa'
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ('fr', 'Français'),
    ('en', 'English'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
GUESTS_PER_PAGE = 20