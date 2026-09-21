"""Run locally with: python -m scripts.configure_database"""

from getpass import getpass

from dotenv import set_key
import psycopg

from app.database import ENV_FILE, DatabaseConfigError, check_database, database_settings


def main() -> int:
    try:
        password = getpass('Enter your pothole_app password (hidden): ')
        settings = database_settings(password=password)
        check_database(settings)
        # Keep other .env settings intact. Save only after a successful query.
        for key, option in [('DB_HOST', 'host'), ('DB_PORT', 'port'),
                            ('DB_NAME', 'dbname'), ('DB_USER', 'user'),
                            ('DB_PASSWORD', 'password')]:
            set_key(ENV_FILE, key, str(settings[option]), quote_mode='always')
    except (DatabaseConfigError, psycopg.Error):
        print('Connection failed. Check PostgreSQL is running and use the pothole_app password. No new settings were saved.')
        return 1
    except OSError:
        print('Could not read or save the local .env file. Check file access and retry.')
        return 1
    except (EOFError, KeyboardInterrupt):
        print('\nSetup cancelled.')
        return 1
    print('Database connection OK. Settings saved to the Git-ignored .env file.')
    print('Next, start or restart FastAPI and open /health/database.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
