"""
Django settings for config project - with HTTPS/SSL
"""

from pathlib import Path
import os
import dj_database_url


# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Security
SECRET_KEY = os.environ.get('SECRET_KEY', 'fallback-secret-key')
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

# Database Configuration
if DEBUG:
    # تشغيل محلي بـ SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }
else:
    # تشغيل على Railway بـ PostgreSQL
    DATABASES = {
        'default': dj_database_url.config(
            default=os.environ.get('DATABASE_URL'),
            conn_max_age=600,
            ssl_require=True
        )
    }

# Allowed Hosts
ALLOWED_HOSTS = [
    'tutoringplatform-production-b8c8.up.railway.app',
    'alagme.com',
    'www.alagme.com',
    'localhost',
    '127.0.0.1',
]

# CSRF Trusted Origins - مهم جداً للـ HTTPS
CSRF_TRUSTED_ORIGINS = [
    'https://alagme.com',
    'https://www.alagme.com',
    'https://tutoringplatform-production-b8c8.up.railway.app',
]

# إذا كان في environment variable
if os.environ.get("CSRF_TRUSTED_ORIGINS"):
    CSRF_TRUSTED_ORIGINS.extend([
        origin.strip()
        for origin in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",")
        if origin.strip()
    ])

# ============================================
# 🔒 إعدادات HTTPS/SSL (مهمة جداً!)
# ============================================
if not DEBUG:
    # Force HTTPS
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    
    # HSTS Settings
    SECURE_HSTS_SECONDS = 31536000  # سنة واحدة
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Security Headers
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    
    # Proxy Settings (مهم لـ Railway)
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    USE_X_FORWARDED_HOST = True
    USE_X_FORWARDED_PORT = True

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'admin_interface',
    'colorfield',
    'django.contrib.sites', 
    'django.contrib.sitemaps',

    # Apps الخاصة بنا
    'accounts',
    'core',
    'payments',
    'blog',
    'qna',
    'cloudinary',
    'cloudinary_storage',

    # مكتبات إضافية
    'corsheaders',
]

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

X_FRAME_OPTIONS = 'SAMEORIGIN'
SILENCED_SYSTEM_CHECKS = ['security.W019']

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',  # ✅ أول حاجة
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

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

WSGI_APPLICATION = 'config.wsgi.application'

# Messages
from django.contrib.messages import constants as messages

MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'error',
}

# Password validation
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

# Internationalization
LANGUAGE_CODE = 'ar'  # ✅ عربي
TIME_ZONE = 'Africa/Cairo'  # ✅ توقيت مصر
USE_I18N = True
USE_TZ = True

# Default field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# WhiteNoise Configuration (لتحسين Static Files)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Cloudinary Configuration
import cloudinary
import cloudinary.uploader
import cloudinary.api

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME', 'dxunjx7wa'),
    'API_KEY': os.environ.get('CLOUDINARY_API_KEY', '183271731539698'),
    'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET', 'WjhFhczJET7-wAWu1fUs35PQW88'),
}

CLOUDINARY = {
    'cloud_name': CLOUDINARY_STORAGE['CLOUD_NAME'],
    'api_key': CLOUDINARY_STORAGE['API_KEY'],
    'api_secret': CLOUDINARY_STORAGE['API_SECRET'],
}

cloudinary.config(
    cloud_name=CLOUDINARY['cloud_name'],
    api_key=CLOUDINARY['api_key'],
    api_secret=CLOUDINARY['api_secret']
)

# Site Framework
SITE_ID = 1

# Canonical URL
CANONICAL_URL = 'https://alagme.com'  # غيّر الدومين

# Default Protocol
DEFAULT_PROTOCOL = 'https'

# Cache للـ Sitemap (لتحسين الأداء)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    },
    'sitemap': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/var/tmp/django_sitemap_cache',
        'TIMEOUT': 86400,  # يوم واحد
    }
}

# Sitemap Caching
SITEMAP_CACHE_TIMEOUT = 3600  # ساعة واحدة

# CORS Settings (إذا احتجتها)
CORS_ALLOWED_ORIGINS = [
    'https://alagme.com',
    'https://www.alagme.com',
]

# Logging (للمساعدة في Debug المشاكل)
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
        'level': 'WARNING',
    },
    'loggers': {
        'django.security': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
# ============================================
# إعدادات البريد الإلكتروني - النسخة المصححة
# ============================================


EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'



# 5. المسؤولين
ADMINS = [
    ('Admin', 'admin@example.com'),
]

# 6. مدير الموقع
MANAGERS = ADMINS

# 7. إعدادات الرسائل
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}