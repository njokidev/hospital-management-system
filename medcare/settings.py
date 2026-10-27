import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-medcare-hospital-2026-production-key-change-in-production',
)

DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() in ('1', 'true', 'yes')

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '*').split(',')
CSRF_TRUSTED_ORIGINS = [o for o in os.environ.get('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(',') if o]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'crispy_forms',
    'crispy_bootstrap5',
    'accounts',
    'core',
    'hospitals',
    'departments',
    'employees',
    'doctors',
    'patients',
    'appointments',
    'opd',
    'ipd',
    'pharmacy',
    'laboratory',
    'radiology',
    'billing',
    'insurance',
    'nursing',
    'ambulance',
    'inventory',
    'hr',
    'reports',
    'auditlogs',
    'notifications',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.AuditLogMiddleware',
]

ROOT_URLCONF = 'medcare.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'builtins': ['core.templatetags.kenya'],
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.global_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'medcare.wsgi.application'

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

# Kenya uses British English conventions and East Africa Time (UTC+3, no DST)
LANGUAGE_CODE = 'en-gb'
TIME_ZONE = 'Africa/Nairobi'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

AUTH_USER_MODEL = 'accounts.User'

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Hospital identity (override per deployment via environment variables) ──
HOSPITAL_NAME = os.environ.get('HOSPITAL_NAME', 'MEDCARE HOSPITAL & DIAGNOSTIC CENTRE')
HOSPITAL_SHORT_NAME = os.environ.get('HOSPITAL_SHORT_NAME', 'MEDCARE')
HOSPITAL_TAGLINE = os.environ.get('HOSPITAL_TAGLINE', 'Your Health, Our Priority')
HOSPITAL_PHONE = os.environ.get('HOSPITAL_PHONE', '+254 700 000 000')
HOSPITAL_EMAIL = os.environ.get('HOSPITAL_EMAIL', 'info@medcare.co.ke')
HOSPITAL_ADDRESS = os.environ.get('HOSPITAL_ADDRESS', 'Upper Hill, P.O. Box 00000-00100, Nairobi, Kenya')
HOSPITAL_WEBSITE = os.environ.get('HOSPITAL_WEBSITE', 'www.medcare.co.ke')
HOSPITAL_KRA_PIN = os.environ.get('HOSPITAL_KRA_PIN', '')
HOSPITAL_MFL_CODE = os.environ.get('HOSPITAL_MFL_CODE', '')  # Kenya Master Facility List code

# ── Currency ──
CURRENCY_CODE = 'KES'
CURRENCY_SYMBOL = 'KSh'

# ── M-Pesa (Safaricom Daraja API) ──
# Leave MPESA_CONSUMER_KEY empty to disable STK Push; manual M-Pesa entry still works.
MPESA_ENVIRONMENT = os.environ.get('MPESA_ENVIRONMENT', 'sandbox')  # 'sandbox' or 'production'
MPESA_CONSUMER_KEY = os.environ.get('MPESA_CONSUMER_KEY', '')
MPESA_CONSUMER_SECRET = os.environ.get('MPESA_CONSUMER_SECRET', '')
MPESA_SHORTCODE = os.environ.get('MPESA_SHORTCODE', '174379')  # Daraja sandbox paybill
MPESA_PASSKEY = os.environ.get('MPESA_PASSKEY', '')
MPESA_TRANSACTION_TYPE = os.environ.get('MPESA_TRANSACTION_TYPE', 'CustomerPayBillOnline')  # or CustomerBuyGoodsOnline
# Public HTTPS base URL Safaricom can reach, e.g. https://hms.example.co.ke
MPESA_CALLBACK_BASE_URL = os.environ.get('MPESA_CALLBACK_BASE_URL', '')
# Secret path segment so only Safaricom (who knows the URL) can post results
MPESA_CALLBACK_TOKEN = os.environ.get('MPESA_CALLBACK_TOKEN', 'change-me')
