"""Local Django settings; the database password stays in the ignored .env."""

import os
from pathlib import Path

from dotenv import dotenv_values

# Development only. We will configure a private key before adding logins.
SECRET_KEY = "django-local-development-no-accounts-yet"
DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

ROOT_URLCONF = "backend.urls"
INSTALLED_APPS = []
MIDDLEWARE = []

BASE_DIR = Path(__file__).resolve().parent.parent
DB_VALUES = {
    "DB_HOST": "127.0.0.1",
    "DB_PORT": "5432",
    "DB_NAME": "pothole_db",
    "DB_USER": "pothole_app",
    **dotenv_values(BASE_DIR / ".env", interpolate=False),
    **os.environ,
}

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": DB_VALUES["DB_NAME"],
        "USER": DB_VALUES["DB_USER"],
        "PASSWORD": DB_VALUES.get("DB_PASSWORD") or "",
        "HOST": DB_VALUES["DB_HOST"],
        "PORT": DB_VALUES["DB_PORT"],
        "OPTIONS": {"connect_timeout": 3},
    }
}
