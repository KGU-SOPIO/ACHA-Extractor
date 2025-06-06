import os
from pathlib import Path

import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Env
env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))


# SECRET_KEY
SECRET_KEY = env("SECRET_KEY")


# SECURITY WARNING
DEBUG = env("DEBUG")

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")


# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Django Rest Framework
    "rest_framework",
    # DRF Spectacular
    "drf_spectacular",
    # Apps
    "Scrape",
]

# Django Rest Framework Settings
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "SOPIO Extractor API Swagger",
    "DESCRIPTION": "널 위해서라면 뭐든지 긁어올 수 있어",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SERVE_URLCONF": "Extractor.urls",
    "AUTHENTICATION_WHITELIST": [],
}

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "Extractor.middleware.PerformanceMiddleware",
]

ROOT_URLCONF = "Extractor.urls"

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

WSGI_APPLICATION = "Extractor.wsgi.application"


# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Password validation
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
LANGUAGE_CODE = "ko-kr"

TIME_ZONE = "Asia/Seoul"

USE_I18N = True

USE_L10N = True

USE_TZ = False


# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"

if DEBUG:
    STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]
else:
    STATIC_ROOT = os.path.join(BASE_DIR, "static")


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        }
    },
    "formatters": {
        "info": {"format": "{asctime} {message}", "style": "{"},
        "warning": {
            "format": "[{levelname}] {asctime} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "system": {
            "level": "INFO",
            "formatter": "warning",
            "filters": ["require_debug_false"],
            "class": "logging.FileHandler",
            "filename": "/app/logs/extractor.log",
        },
        "performance": {
            "level": "INFO",
            "formatter": "info",
            "filters": ["require_debug_false"],
            "class": "Extractor.handlers.PerformanceHandler",
            "discordUrl": env("INFO_DISCORDURL"),
        },
        "warning": {
            "level": "WARNING",
            "formatter": "warning",
            "filters": ["require_debug_false"],
            "class": "Extractor.handlers.ExtractorHandler",
            "discordUrl": env("WARNING_DISCORDURL"),
            "logPath": "/app/logs/extractor.log",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["system"],
            "level": "WARNING",
            "propagate": False,
        },
        "performance": {
            "handlers": ["performance"],
            "level": "INFO",
            "propagate": False,
        },
        "watchmen": {
            "handlers": ["warning"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}
