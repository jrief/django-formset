import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'secret_key')

DEBUG = os.getenv('DJANGO_DEBUG', '').lower() in ['true', '1', 'yes']

DEPLOYED = os.getenv('DJANGO_DEPLOYED', '').lower() in ['true', '1', 'yes']

ALLOWED_HOSTS = ['*'] if DEBUG else ['localhost', 'django-formset.fly.dev']
CSRF_TRUSTED_ORIGINS = ['https://django-formset.fly.dev']

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.admin',
    'django.contrib.staticfiles',
    'django.contrib.messages',
    'formset',
    'testapp',
]
try:
    import sphinx_view
except ImportError:
    pass
else:
    INSTALLED_APPS.append('sphinx_view')

if os.getenv('DATABASE_ENGINE') == 'postgres':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('POSTGRES_DB'),
            'USER': os.getenv('POSTGRES_USER'),
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD'),
            'HOST': os.getenv('POSTGRES_HOST'),
            'PORT': os.getenv('POSTGRES_PORT', 5432),
            # 'CONN_MAX_AGE': 900,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': Path(os.getenv('DJANGO_WORKDIR', BASE_DIR / 'workdir')) / 'testapp.sqlite3',
            'TEST': {
                'NAME': Path(__file__).parent / 'test.sqlite3',  # live_server requires a file rather than :memory:
                'OPTIONS': {
                    'timeout': 20,
                },
            },
        }
    }

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

USE_TZ = True

TIME_ZONE = 'UTC'

MIDDLEWARE = [
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
]

USE_I18N = True

ROOT_URLCONF = 'testapp.urls'

STATICFILES_DIRS = [
    ('node_modules', BASE_DIR / 'node_modules'),
    ('sphinx-view', BASE_DIR / 'docs/build/json'),
]

STATIC_URL = '/static/'

STATIC_ROOT = os.getenv('DJANGO_STATIC_ROOT', BASE_DIR / 'workdir/static')

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'testapp.storage.NoSourceMapsManifestStaticStorage' if DEPLOYED else \
                   'django.contrib.staticfiles.storage.StaticFilesStorage',
    },
}

MEDIA_ROOT = Path(os.getenv('DJANGO_MEDIA_ROOT', BASE_DIR / 'workdir/media'))

MEDIA_URL = '/media/'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'docs/source/_templates'],
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.debug',
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
        ],
    },
}]

WSGI_APPLICATION = 'wsgi.application'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'filters': {'require_debug_false': {'()': 'django.utils.log.RequireDebugFalse'}},
    'formatters': {
        'simple': {
            'format': '[%(asctime)s %(module)s] %(levelname)s: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

FORMSET_IGNORE_MARKED_FOR_REMOVAL = False

if DEBUG:
    import mimetypes
    mimetypes.add_type("application/javascript", ".js", True)
