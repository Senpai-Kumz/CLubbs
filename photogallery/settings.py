"""Django settings for the Clubb application.

Local development uses SQLite by default when DJANGO_DEBUG=True. Production
requires an explicit secret, host list, and DATABASE_URL; it never silently
falls back to ephemeral SQLite storage when DEBUG is disabled.
"""

import os
from pathlib import Path
from urllib.parse import parse_qsl, unquote, urlparse

from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

# Local values live in .env (which must never be committed). Environment
# variables configured by a hosting provider take precedence over .env.
load_dotenv(BASE_DIR / ".env", override=False)


def env_bool(name: str, default: bool = False) -> bool:
    """Read a conventional true/false environment variable."""
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: tuple[str, ...] = ()) -> list[str]:
    """Read a comma-separated environment variable into a clean list."""
    value = os.environ.get(name, "").strip()
    if not value:
        return list(default)
    return [item.strip() for item in value.split(",") if item.strip()]


# Production-safe defaults: DEBUG remains off unless explicitly enabled.
DEBUG = env_bool("DJANGO_DEBUG", default=False)

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "").strip()
if not SECRET_KEY:
    if DEBUG:
        # Convenience fallback for local development only; never use in production.
        SECRET_KEY = "django-insecure-local-development-only-not-for-production"
    else:
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY is required when DJANGO_DEBUG is False. "
            "Set a new secret in your hosting provider's environment settings."
        )

_default_local_hosts = ("localhost", "127.0.0.1", "[::1]") if DEBUG else ()
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", default=_default_local_hosts)
if not ALLOWED_HOSTS or "*" in ALLOWED_HOSTS:
    raise ImproperlyConfigured(
        "DJANGO_ALLOWED_HOSTS must contain the allowed hostnames, for example "
        "'clubbs.onrender.com'. Do not use a wildcard in production."
    )

CSRF_TRUSTED_ORIGINS = env_list(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    default=("https://clubbs.onrender.com",),
)

# Render terminates HTTPS at its proxy and forwards this header to the app.
# If the hosting topology changes, verify this setting before enabling redirects.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", default=not DEBUG)
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"


# Application definition
INSTALLED_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "cloudinary_storage",
    "cloudinary",
    "gallery",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "photogallery.urls"

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

WSGI_APPLICATION = "photogallery.wsgi.application"
ASGI_APPLICATION = "photogallery.asgi.application"


# Database configuration.
# DATABASE_URL takes precedence and is intended for managed PostgreSQL.
# SQLite remains available for local development only.
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
if DATABASE_URL:
    parsed_database_url = urlparse(DATABASE_URL)
    if parsed_database_url.scheme not in {"postgres", "postgresql"}:
        raise ImproperlyConfigured(
            "DATABASE_URL must be a PostgreSQL URL beginning with postgres:// "
            "or postgresql://."
        )

    database_name = unquote(parsed_database_url.path.lstrip("/"))
    database_user = unquote(parsed_database_url.username or "")
    database_password = unquote(parsed_database_url.password or "")
    try:
        database_port = parsed_database_url.port
    except ValueError as exc:
        raise ImproperlyConfigured("DATABASE_URL contains an invalid port.") from exc

    if not parsed_database_url.hostname or not database_name or not database_user:
        raise ImproperlyConfigured(
            "DATABASE_URL must include a hostname, database name, and username."
        )

    database_options = dict(parse_qsl(parsed_database_url.query, keep_blank_values=True))
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": database_name,
            "USER": database_user,
            "PASSWORD": database_password,
            "HOST": parsed_database_url.hostname,
            "PORT": database_port or "",
            "OPTIONS": database_options,
            # Django recommends disabling persistent connections in ASGI mode.
            "CONN_MAX_AGE": 0,
            "CONN_HEALTH_CHECKS": True,
        }
    }
else:
    if not DEBUG:
        raise ImproperlyConfigured(
            "DATABASE_URL is required when DJANGO_DEBUG is False. Configure a "
            "managed PostgreSQL database before deploying these settings."
        )
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# Static files remain on Django's normal static-file backend.
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Uploaded media uses Cloudinary when credentials are configured.
# Otherwise, local development continues using the filesystem.
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

CLOUDINARY_CLOUD_NAME = os.environ.get(
    "CLOUDINARY_CLOUD_NAME", ""
).strip()
CLOUDINARY_API_KEY = os.environ.get(
    "CLOUDINARY_API_KEY", ""
).strip()
CLOUDINARY_API_SECRET = os.environ.get(
    "CLOUDINARY_API_SECRET", ""
).strip()

CLOUDINARY_CONFIGURED = all([
    CLOUDINARY_CLOUD_NAME,
    CLOUDINARY_API_KEY,
    CLOUDINARY_API_SECRET,
])

if CLOUDINARY_CONFIGURED:
    CLOUDINARY_STORAGE = {
        "CLOUD_NAME": CLOUDINARY_CLOUD_NAME,
        "API_KEY": CLOUDINARY_API_KEY,
        "API_SECRET": CLOUDINARY_API_SECRET,
        "SECURE": True,
    }

    STORAGES = {
        "default": {
            "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
else:
    if not DEBUG:
        raise ImproperlyConfigured(
            "Cloudinary credentials are required in production."
        )

    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }

LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"


# Real-time messaging. Configure REDIS_URL in production for a shared channel
# layer when using multiple processes or instances. The in-memory layer is a
# development fallback and is not shared between separate processes.
REDIS_URL = os.environ.get("REDIS_URL", "").strip()
if REDIS_URL:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {"hosts": [REDIS_URL]},
        },
    }
else:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        },
    }
