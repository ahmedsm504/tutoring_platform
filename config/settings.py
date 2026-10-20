"""
Django settings for config project (alagme.com)

⚠️ كل الأسرار (SECRET_KEY / Cloudinary / WhatsApp / Firebase) بتتقري من متغيرات
البيئة على Railway - مفيش أي كلمة سر مكتوبة في الكود.
"""

import os
from pathlib import Path

import dj_database_url
from django.contrib.messages import constants as messages


def env_bool(name, default=False):
    return os.environ.get(name, str(default)).strip().lower() in ('1', 'true', 'yes', 'on')


def env_list(name, default=''):
    return [x.strip() for x in os.environ.get(name, default).split(',') if x.strip()]


BASE_DIR = Path(__file__).resolve().parent.parent

# =========================================================
# الأمان
# =========================================================
# على Railway (فيه DATABASE_URL) افتراضيًا False عشان الأمان.
# على جهازك (من غير DATABASE_URL) افتراضيًا True عشان runserver يشتغل على http عادي.
# وفي الحالتين تقدري تحددي DEBUG=True أو False بنفسك من متغيرات البيئة.
DEBUG = env_bool('DEBUG', not os.environ.get('DATABASE_URL'))
# ⚠️ لازم يكون فيه SECRET_KEY قوي في متغيرات Railway. القيمة الاحتياطية دي هي نفس
# القديمة بالظبط عشان جلسات الدخول الحالية متتقفلش - بس متعتمديش عليها.
SECRET_KEY = os.environ.get('SECRET_KEY', 'fallback-secret-key')

CANONICAL_HOST = os.environ.get('CANONICAL_HOST', 'alagme.com')
CANONICAL_URL = f'https://{CANONICAL_HOST}'
DEFAULT_PROTOCOL = 'https'

ALLOWED_HOSTS = [
    CANONICAL_HOST,
    f'www.{CANONICAL_HOST}',
    'tutoringplatform-production-b8c8.up.railway.app',
    '.up.railway.app',
    'healthcheck.railway.app',
    'localhost',
    '127.0.0.1',
    'testserver',
] + env_list('EXTRA_ALLOWED_HOSTS')

# الدومينات دي بتتحول 301 للدومين الأساسي (عشان جوجل ميشوفش نسخ مكررة من الموقع)
SEO_REDIRECT_HOSTS = [f'www.{CANONICAL_HOST}', 'tutoringplatform-production-b8c8.up.railway.app'] + env_list('SEO_REDIRECT_HOSTS')

CSRF_TRUSTED_ORIGINS = [
    f'https://{CANONICAL_HOST}',
    f'https://www.{CANONICAL_HOST}',
    'https://tutoringplatform-production-b8c8.up.railway.app',
] + env_list('CSRF_TRUSTED_ORIGINS')

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    USE_X_FORWARDED_HOST = True
    USE_X_FORWARDED_PORT = True

SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
X_FRAME_OPTIONS = 'SAMEORIGIN'
SILENCED_SYSTEM_CHECKS = ['security.W019']

# =========================================================
# قاعدة البيانات
# =========================================================
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL:
    DATABASES = {"default": dj_database_url.config(default=DATABASE_URL, conn_max_age=600, ssl_require=env_bool('DB_SSL', True))}
else:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}

# =========================================================
# التطبيقات
# =========================================================
INSTALLED_APPS = [
    'admin_interface',
    'colorfield',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    'accounts',
    'core',
    'payments',
    'chat.apps.ChatConfig',
    'learning.apps.LearningConfig',
    'cloudinary',
    'cloudinary_storage',
    'corsheaders',
    'blog.apps.BlogConfig',
    'qna.apps.QnaConfig',
]

MIDDLEWARE = [
    'config.middleware.BlockScannersMiddleware',
    'config.middleware.CanonicalHostMiddleware',  # الأول: http://www -> https://alagme.com في خطوة واحدة
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'config.middleware.PrivatePagesNoIndexMiddleware',
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
                'config.context_processors.seo',
                'chat.context_processors.chat_counts',
                'learning.context_processors.learning_counts',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'ar'
TIME_ZONE = 'Africa/Cairo'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'accounts.User'
SITE_ID = 1

# =========================================================
# الملفات الثابتة والمرفوعة
# ملحوظة: Django 5.1+ شال DEFAULT_FILE_STORAGE و STATICFILES_STORAGE نهائيًا
# (كانوا بيتجاهلوا من غير ما حد يحس) - الإعداد الصح بقى STORAGES.
# =========================================================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

STORAGES = {
    # افتراضيًا على السيرفر نفسه زي ما كان شغال فعليًا. لو عايزة الملفات المرفوعة
    # تتحفظ على Cloudinary (أضمن على Railway) حطي USE_CLOUDINARY_MEDIA=True
    'default': {
        'BACKEND': ('cloudinary_storage.storage.RawMediaCloudinaryStorage'
                    if env_bool('USE_CLOUDINARY_MEDIA', False)
                    else 'django.core.files.storage.FileSystemStorage'),
    },
    # ضغط gzip/brotli للـ CSS/JS (أسرع = أحسن للسيو). من غير manifest عشان
    # أي ملف ناقص ميوقعش الموقع.
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}
WHITENOISE_MAX_AGE = 60 * 60 * 24 * 7
# أسماء الملفات بقت بالـ hash (site.abc123.css)، فأي تعديل بيوصل للزوار فورًا من غير كاش قديم.
# ولو ملف ناقص منطلعش 500، نرجع للاسم العادي.
WHITENOISE_MANIFEST_STRICT = False

# ⚠️ مفاتيح Cloudinary كانت مكتوبة في الكود (ومتشافة لأي حد معاه نسخة منه).
# انقليها لمتغيرات البيئة على Railway واعملي Regenerate للـ API Secret من لوحة Cloudinary،
# وبعدها امسحي القيم الاحتياطية دي. (سايبينها مؤقتًا عشان رفع صور المدونة ميقفش)
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME', 'dxunjx7wa'),
    'API_KEY': os.environ.get('CLOUDINARY_API_KEY', '183271731539698'),
    'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET', 'WjhFhczJET7-wAWu1fUs35PQW88'),
}
if CLOUDINARY_STORAGE['CLOUD_NAME']:
    import cloudinary
    cloudinary.config(
        cloud_name=CLOUDINARY_STORAGE['CLOUD_NAME'],
        api_key=CLOUDINARY_STORAGE['API_KEY'],
        api_secret=CLOUDINARY_STORAGE['API_SECRET'],
        secure=True,
    )

# =========================================================
# كاش / جلسات / رسائل
# =========================================================
CACHES = {
    'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache', 'LOCATION': 'alagme-default'},
}
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'
MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

CORS_ALLOWED_ORIGINS = [f'https://{CANONICAL_HOST}', f'https://www.{CANONICAL_HOST}']

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'root': {'handlers': ['console'], 'level': 'WARNING'},
    'loggers': {
        'django.security': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'chat': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
    },
}

# الإيميلات (إشعار الأدمن بالأسئلة الجديدة، والمشتركين في الأسئلة) كانت بتتطبع في اللوج بس.
# لتشغيلها فعليًا ضيف في Railway: EMAIL_HOST و EMAIL_HOST_USER و EMAIL_HOST_PASSWORD
# (مثلًا Gmail: smtp.gmail.com مع App Password). من غيرهم بتفضل في اللوج زي ما هي.
EMAIL_HOST = os.environ.get('EMAIL_HOST', '')
if EMAIL_HOST:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
    EMAIL_USE_TLS = env_bool('EMAIL_USE_TLS', EMAIL_PORT == 587)
    EMAIL_USE_SSL = env_bool('EMAIL_USE_SSL', EMAIL_PORT == 465)
    EMAIL_TIMEOUT = 15
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', os.environ.get('EMAIL_HOST_USER') or 'no-reply@alagme.com')
SERVER_EMAIL = DEFAULT_FROM_EMAIL
ADMINS = [('Admin', os.environ.get('ADMIN_EMAIL', 'admin@alagme.com'))]
MANAGERS = ADMINS

# =========================================================
# SEO / IndexNow
# =========================================================
INDEXNOW_KEY = os.environ.get('INDEXNOW_KEY', '800e60e37753412893002525b148ce17')
SITE_NAME = 'مؤسسة العجمي'

# =========================================================
# الشات الداخلي بين المعلمة والطالب
# =========================================================
# رقم واتساب الإدارة اللي بيظهر للزوار في الموقع العام بس (للاستفسارات والحجز) - مالوش علاقة بالشات
WHATSAPP_PUBLIC_NUMBER = os.environ.get('WHATSAPP_PUBLIC_NUMBER', '201044568181')
# روابط مسموح للمعلمة والطالب يبعتوها في الشات (أي رابط تاني بيتمنع)
CHAT_ALLOWED_LINK_DOMAINS = env_list('CHAT_ALLOWED_LINK_DOMAINS', f'{CANONICAL_HOST},meet.google.com,zoom.us')
# مكان حفظ مرفقات الشات (صور/صوت): على السيرفر افتراضيًا. على Railway من غير Volume
# الملفات بتتمسح مع كل نشر، فيُفضل USE_CLOUDINARY_MEDIA=True أو Volume على /app/media
