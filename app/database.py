"""Small connection check; project tables will be added in a later milestone."""

import os
from pathlib import Path

from dotenv import dotenv_values
import psycopg


ENV_FILE = Path(__file__).resolve().parents[1] / '.env'
DEFAULTS = {
    'DB_HOST': '127.0.0.1',
    'DB_PORT': '5432',
    'DB_NAME': 'pothole_db',
    'DB_USER': 'pothole_app',
}


class DatabaseConfigError(ValueError):
    """Missing or invalid configuration, without exposing its contents."""


def database_settings(password: str | None = None) -> dict:
    # Explicit path works regardless of where Uvicorn was launched. Disabling
    # interpolation preserves literal ${...} characters in passwords.
    values = {**DEFAULTS, **dotenv_values(ENV_FILE, interpolate=False), **os.environ}
    secret = password if password is not None else values.get('DB_PASSWORD')
    if not secret or any(not values.get(key) for key in DEFAULTS):
        raise DatabaseConfigError('Database configuration is incomplete.')
    try:
        port = int(values['DB_PORT'])
    except (TypeError, ValueError):
        raise DatabaseConfigError('Database port is invalid.') from None
    if not 1 <= port <= 65535:
        raise DatabaseConfigError('Database port is invalid.')
    # Pass keywords, not a URL, so special password characters need no URL escaping.
    return {
        'host': values['DB_HOST'], 'port': port, 'dbname': values['DB_NAME'],
        'user': values['DB_USER'], 'password': secret,
        'connect_timeout': 3, 'options': '-c statement_timeout=3000',
        'autocommit': True,
    }


def check_database(settings: dict | None = None) -> None:
    # A context manager closes the connection even when a query fails.
    with psycopg.connect(**(settings if settings is not None else database_settings())) as connection:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            if cursor.fetchone() != (1,):
                raise psycopg.DatabaseError('Unexpected connection-check result.')
