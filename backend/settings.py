"""First Django lesson: local settings for two small backend routes."""

# Development only. We will configure a private key before adding logins.
SECRET_KEY = "django-local-development-no-accounts-yet"
DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

ROOT_URLCONF = "backend.urls"
INSTALLED_APPS = []
MIDDLEWARE = []

# The next lesson will configure the existing PostgreSQL database here.
DATABASES = {}
