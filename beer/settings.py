import os
import sys

from environs import Env

env = Env()


VERSION = '0.3'

PATCH_VERSION = '0'


BASE_PATH = os.path.dirname(os.path.abspath(__file__))

BASE_DIR = os.path.dirname(BASE_PATH)

BASE_NAME = os.path.basename(BASE_PATH)


CONTAINED = env.bool('CONTAINED', False)

TESTING = 'test' in sys.argv

COLLECTING = 'collectstatic' in sys.argv


if CONTAINED:
    SECRET_KEY = env.str('SECRET_KEY')

    DEBUG = env.bool('DEBUG', False)

    TEMPLATE_DEBUG = env.bool('TEMPLATE_DEBUG', False)

    HEADLESS = True
else:
    SECRET_KEY = 'dev'

    DEBUG = True

    TEMPLATE_DEBUG = True

    HEADLESS = env.bool('HEADLESS', False)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', ['localhost', '127.0.0.1', '[::1]'])


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'channels',
    'malt',
    'lager',
    'ale',
]

MIDDLEWARE = [
    BASE_NAME + '.middleware.HealthMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = BASE_NAME + '.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_PATH, 'templates')],
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

ASGI_APPLICATION = BASE_NAME + '.routing.application'


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
}


CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.PyLibMCCache',
        'LOCATION': '{}:{}'.format(env.str('CACHE_HOST', 'localhost'), env.int('CACHE_PORT', 11210)),
        'KEY_PREFIX': 'test' if TESTING else '',
    },
}


CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [
                {
                    'address': (
                        env.str('BROKER_HOST', 'localhost'),
                        env.int('BROKER_PORT', 6378),
                    ),
                },
            ],
        },
    },
}


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': env.str('DATABASE_HOST', 'localhost'),
        'PORT': env.int('DATABASE_PORT', 5431),
        'NAME': env.str('DATABASE_NAME', 'dev'),
        'USER': env.str('DATABASE_USER', 'dev'),
        'PASSWORD': env.str('DATABASE_PASSWORD', 'dev'),
    },
}


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


LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


FILE_UPLOAD_MAX_TEMP_SIZE = 26214400

FILE_UPLOAD_HANDLERS = [
    BASE_NAME + '.uphandler.ChannelMemoryFileUploadHandler',
    BASE_NAME + '.uphandler.ChannelTemporaryFileUploadHandler',
]


STATIC_BUCKET = env.str('STATIC_BUCKET', 'static')

if TESTING:
    MEDIA_BUCKET = 'media-test'
else:
    MEDIA_BUCKET = env.str('MEDIA_BUCKET', 'media')


PUBLIC_LOCATION = 'public'

PRIVATE_LOCATION = 'private'


if CONTAINED or COLLECTING:
    AWS_S3_ENDPOINT_URL = env.str('AWS_S3_ENDPOINT_URL', 'http://localhost:9000')

    AWS_S3_REGION_NAME = env.str('AWS_S3_REGION_NAME', 'us-east-1')

    AWS_ACCESS_KEY_ID = env.str('AWS_ACCESS_KEY_ID', 'filestore')

    AWS_SECRET_ACCESS_KEY = env.str('AWS_SECRET_ACCESS_KEY', 'filestore')

    AWS_DEFAULT_ACL = None

    STATICFILES_STORAGE = BASE_NAME + '.filestore.StaticRemoteStorage'


if CONTAINED and not TESTING:
    AWS_S3_OVERRIDE_URL = env.str('AWS_S3_OVERRIDE_URL', '')
else:
    AWS_S3_OVERRIDE_URL = ''

    STATIC_URL = '/{}/{}/'.format(STATIC_BUCKET, VERSION)


if CONTAINED:
    PUBLICFILES_STORAGE = BASE_NAME + '.filestore.PublicRemoteStorage'

    PRIVATEFILES_STORAGE = BASE_NAME + '.filestore.PrivateRemoteStorage'
else:
    STATICFILES_DIRS = [
        os.path.join(BASE_PATH, 'static'),
    ]

    MEDIA_ROOT = os.path.join(BASE_DIR, '..', 'dev', 'filestore')

    PUBLICFILES_STORAGE = BASE_NAME + '.filestore.PublicLocalStorage'

    PRIVATEFILES_STORAGE = BASE_NAME + '.filestore.PrivateLocalStorage'


if CONTAINED:
    SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', 15552000)

    SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', True)

    SESSION_COOKIE_SECURE = env.bool('SESSION_COOKIE_SECURE', True)

    CSRF_COOKIE_SECURE = env.bool('CSRF_COOKIE_SECURE', True)

SECURE_HSTS_INCLUDE_SUBDOMAINS = True

SECURE_HSTS_PRELOAD = True

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

SECURE_REFERRER_POLICY = 'same-origin'


EMAIL_HOST = env.str('EMAIL_HOST', 'localhost')

EMAIL_PORT = env.int('EMAIL_PORT', 1025)

EMAIL_HOST_USER = env.str('EMAIL_HOST_USER', '')

EMAIL_HOST_PASSWORD = env.str('EMAIL_HOST_PASSWORD', '')

EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', False)

EMAIL_USE_SSL = env.bool('EMAIL_USE_SSL', False)

DEFAULT_FROM_EMAIL = env.str('DEFAULT_FROM_EMAIL', 'webmaster@localhost')


LOGIN_URL = '/login'

LOGIN_REDIRECT_URL = '/'
