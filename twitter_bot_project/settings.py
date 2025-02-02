"""
Django settings for twitter_bot_project project.

Generated by 'django-admin startproject' using Django 4.2.7.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""
import environ
import os
from pathlib import Path
from celery.schedules import crontab
from .slack_logging import SlackHandler

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(env_file=BASE_DIR / ".env")

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG")

ALLOWED_HOSTS = env("ALLOWED_HOSTS").split(",")


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "reply_bot",
    # "trends.apps.TrendsConfig",
    "trends",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "twitter_bot_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "twitter_bot_project.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
    
CELERY_BROKER_URL = env("REDIS_URL")
schedule_minutes = env.int("CELERY_BEAT_SCHEDULE_MINUTES", default=15)

CELERY_BEAT_SCHEDULE = {
    "run_my_task_every_15_minutes": {
        "task": "trends.tasks.process",
        "schedule": crontab(minute=f'*/{schedule_minutes}'),
    },
}

# CELERYD_HIJACK_ROOT_LOGGER = False
# CELERY_WORKER_HIJACK_ROOT_LOGGER = False
# CELERY_WORKER_LOG_FORMAT = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
# CELERY_WORKER_TASK_LOG_FORMAT = '[%(asctime)s: %(levelname)s/%(processName)s] [%(task_name)s(%(task_id)s)] %(message)s'


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "file": {
            "level": "ERROR",
            "class": "logging.FileHandler",
            "filename": "django_error.log",
            "formatter": "verbose",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file", "console"],
            "level": "ERROR",
            "propagate": True,
        },
        "django.request": {
            "handlers": ["file", "console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}

ENABLE_SLACK_LOGGING = env('ENABLE_SLACK_LOGGING')
if ENABLE_SLACK_LOGGING:
    LOGGING["handlers"]["slack"] = {
        "class": "twitter_bot_project.slack_logging.SlackHandler",
        "webhook_url": env("SLACK_ERROR_LOGGER_WEBHOOK"),
        "level": "ERROR",
    }
    LOGGING["loggers"]["django"]["handlers"].append("slack")
    LOGGING["loggers"]["django.request"]["handlers"].append("slack")


DOPESHI_TWITTER_API_KEY = env("DOPESHI_TWITTER_API_KEY")
DOPESHI_TWITTER_API_SECRET = env("DOPESHI_TWITTER_API_SECRET")
DOPESHI_TWITTER_ACCESS_TOKEN = env("DOPESHI_TWITTER_ACCESS_TOKEN")
DOPESHI_TWITTER_ACCESS_SECRET = env("DOPESHI_TWITTER_ACCESS_SECRET")
DOPESHI_TWITTER_BEARER_TOKEN = env("DOPESHI_TWITTER_BEARER_TOKEN")
DOPESHI_TWITTER_CLIENT_ID = env("DOPESHI_TWITTER_CLIENT_ID")
DOPESHI_TWITTER_CLIENT_SECRET = env("DOPESHI_TWITTER_CLIENT_SECRET")

WHY_TRENDING_TWITTER_API_KEY = env("WHY_TRENDING_TWITTER_API_KEY")
WHY_TRENDING_TWITTER_API_SECRET = env("WHY_TRENDING_TWITTER_API_SECRET")
WHY_TRENDING_TWITTER_ACCESS_TOKEN = env("WHY_TRENDING_TWITTER_ACCESS_TOKEN")
WHY_TRENDING_TWITTER_ACCESS_SECRET = env("WHY_TRENDING_TWITTER_ACCESS_SECRET")
WHY_TRENDING_TWITTER_BEARER_TOKEN = env("WHY_TRENDING_TWITTER_BEARER_TOKEN")
# TRENDING_TWITTER_CLIENT_ID = env('TRENDING_TWITTER_CLIENT_ID')
# TRENDING_TWITTER_CLIENT_SECRET = env('TRENDING_TWITTER_CLIENT_SECRET')

REDDIT_CLIENT_ID = env("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = env("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = env("REDDIT_USER_AGENT")

PAUSE_ACCOUNT = env("PAUSE_ACCOUNT", default="").split(",")

GOOGLE_CUSTOM_SEARCH_API_KEY = env("GOOGLE_CUSTOM_SEARCH_API_KEY")
GOOGLE_CUSTOM_SEARCH_ENGINE_ID = env("GOOGLE_CUSTOM_SEARCH_ENGINE_ID")
