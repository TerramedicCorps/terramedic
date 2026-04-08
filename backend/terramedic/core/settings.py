"""
Django settings for terramedic project.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/6.0/ref/settings/
"""

import os
import sys
from pathlib import Path

import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Detect Lambda environment
IS_LAMBDA = bool(os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

# SECURITY WARNING: keep the secret key used in production secret!
_raw_secret_key = os.getenv("SECRET_KEY", "")
if IS_LAMBDA and _raw_secret_key:
    from terramedic.core.secrets import resolve_secret

    SECRET_KEY = resolve_secret(_raw_secret_key, "key")
elif _raw_secret_key:
    SECRET_KEY = _raw_secret_key
elif IS_LAMBDA:
    # Only Lambda (the real deployed runtime) is treated as production.
    # Local dev, tests, mypy / django-stubs model introspection, and
    # ad-hoc manage commands fall through to the insecure dev key below
    # because they cannot accidentally serve production traffic.
    raise ValueError(
        "SECRET_KEY environment variable is required when running on Lambda",
    )
else:
    SECRET_KEY = "django-insecure-terramedic-dev-key-change-in-production"

# Parse ALLOWED_HOSTS from environment variable (comma-separated)
allowed_hosts_env = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1")
ALLOWED_HOSTS = [host.strip() for host in allowed_hosts_env.split(",")]

# Add testserver for Django tests (Django test runner and pytest)
if (
    "test" in sys.argv
    or "pytest" in sys.modules
    or os.getenv("PYTEST_CURRENT_TEST")
):
    ALLOWED_HOSTS.append("testserver")

# On Lambda, allow API Gateway invoke URLs
if IS_LAMBDA:
    _aws_region = (
        os.getenv("AWS_REGION")
        or os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    )
    ALLOWED_HOSTS.append(f".execute-api.{_aws_region}.amazonaws.com")
    ALLOWED_HOSTS.append(".terramedic.org")


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "corsheaders",
    "parler",
    "terramedic.organizations",
    "terramedic.nominations",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "terramedic.core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "terramedic.core.wsgi.application"


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

_database_url = os.getenv("DATABASE_URL", "")
if IS_LAMBDA and _database_url:
    from terramedic.core.secrets import resolve_secret

    _database_url = resolve_secret(_database_url, "url")

if _database_url:
    db_config = dj_database_url.parse(_database_url)
    # Use PostGIS backend for PostgreSQL
    if db_config.get("ENGINE") == "django.db.backends.postgresql":
        db_config["ENGINE"] = "django.contrib.gis.db.backends.postgis"
    if IS_LAMBDA:
        db_config["CONN_MAX_AGE"] = 0
        db_config.setdefault("OPTIONS", {})
        db_config["OPTIONS"]["connect_timeout"] = 5
    DATABASES = {"default": db_config}
else:
    # Use SpatiaLite for local development
    DATABASES = {
        "default": {
            "ENGINE": "django.contrib.gis.db.backends.spatialite",
            "NAME": str(BASE_DIR / "db" / "db.sqlite3"),
        },
    }


# GDAL/GEOS library paths (read from env so Docker build and Lambda both work)
# On Lambda, default to the geolambda image paths; elsewhere, only set if explicit.
_gdal_default = "/opt/lib64/libgdal.so" if IS_LAMBDA else ""
_geos_default = "/opt/lib64/libgeos_c.so" if IS_LAMBDA else ""
_gdal_path = os.getenv("GDAL_LIBRARY_PATH", _gdal_default)
_geos_path = os.getenv("GEOS_LIBRARY_PATH", _geos_default)
if _gdal_path:
    GDAL_LIBRARY_PATH = _gdal_path
if _geos_path:
    GEOS_LIBRARY_PATH = _geos_path

# Auto-detect SpatiaLite library path on macOS
SPATIALITE_LIBRARY_PATH = os.getenv("SPATIALITE_LIBRARY_PATH", "")
if not SPATIALITE_LIBRARY_PATH:
    _spatialite_candidates = [
        "/usr/local/lib/mod_spatialite.dylib",  # Homebrew Intel Mac
        "/opt/homebrew/lib/mod_spatialite.dylib",  # Homebrew Apple Silicon
    ]
    for candidate in _spatialite_candidates:
        if os.path.exists(candidate):
            SPATIALITE_LIBRARY_PATH = candidate
            break


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation"
            ".UserAttributeSimilarityValidator"
        ),
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization

LANGUAGE_CODE = "en"
LANGUAGES = [
    ("en", "English"),
    ("fr", "French"),
    ("es", "Spanish"),
]
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# django-parler configuration
PARLER_LANGUAGES = {
    None: (
        {"code": "en"},
        {"code": "fr"},
        {"code": "es"},
    ),
    "default": {
        "fallbacks": ["en"],
        "hide_untranslated": False,
    },
}


# Static files (CSS, JavaScript, Images)

STATIC_URL = "/static/"
STATIC_ROOT = (
    "/var/task/staticfiles" if IS_LAMBDA
    else str(BASE_DIR / "staticfiles")
)


# Default primary key field type

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# CORS configuration

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
]


# CSRF trusted origins (needed when SvelteKit POSTs to the API)

CSRF_TRUSTED_ORIGINS = []
_csrf_origins_env = os.getenv("CSRF_TRUSTED_ORIGINS", "")
if _csrf_origins_env:
    CSRF_TRUSTED_ORIGINS = [
        origin.strip() for origin in _csrf_origins_env.split(",")
    ]
if DEBUG:
    CSRF_TRUSTED_ORIGINS.extend([
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ])


# Logging

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": (
                "{levelname} {asctime} {module} {message}"
            ),
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "terramedic": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
