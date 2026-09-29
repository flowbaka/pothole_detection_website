# Django lesson 2: connect to PostgreSQL

The first lesson handled a request without using the database. This lesson gives Django the existing `pothole_db` connection and adds a read-only check at `/health/database/`. It does not create tables or save pothole reports.

## Run it

From the project folder in PowerShell:

```powershell
.\.pothholevenv\Scripts\python.exe manage.py runserver 127.0.0.1:8003
```

Open `http://127.0.0.1:8003/health/database/`. Expected response: `{"status":"ok","database":"connected"}`. If the database is unavailable, the route returns HTTP 503 and `{"status":"unavailable"}`. The separate `/health/` route still checks that Django itself responds.

The database password remains in the project's Git-ignored `.env`, created earlier with `python -m scripts.configure_database`. Never put the real password in `settings.py` or send it in chat.

## Read the code in request order

1. `backend/settings.py` builds `BASE_DIR` from the file's own path, then reads `BASE_DIR / ".env"`. `DB_VALUES` merges four local defaults, `.env` values, and process environment variables, in that order. Later values replace earlier ones. `interpolate=False` preserves literal `${...}` characters in passwords.
2. `DATABASES["default"]` is Django's required connection description. `ENGINE` selects its PostgreSQL backend. `NAME`, `USER`, `PASSWORD`, `HOST` and `PORT` tell it which database and account to use. `OPTIONS` limits connection waiting to three seconds. The dictionary describes a connection; Django opens it when a query needs it.
3. `backend/urls.py` maps `health/database/` to `views.database_health`.
4. In `backend/views.py`, `connection.cursor()` opens a cursor using Django's configured database. `cursor.execute("SELECT 1")` asks PostgreSQL to return a single number without reading or changing a table. `cursor.fetchone()` should return `(1,)`, a one-item tuple.
5. On success, `JsonResponse` returns HTTP 200 and `{"status":"ok","database":"connected"}`. If Django raises `DatabaseError`, the view returns a fixed HTTP 503 message so connection details do not appear in the response.

The key new flow is: **request → URL rule → view → Django connection → PostgreSQL → JSON response**.

`backend/tests.py` checks success and error responses with a simulated connection. `SimpleTestCase` deliberately creates no test database. Separately, a temporary real Django server returned HTTP 200 for both health routes using the existing local PostgreSQL settings, then was stopped. The check did not create any table.

## Verify

```powershell
.\.pothholevenv\Scripts\python.exe manage.py check
.\.pothholevenv\Scripts\python.exe manage.py test backend.tests
```

Both commands passed locally. The next lesson will define the first `Report` model and create its table through a Django migration. A model describes rows in Python; a migration changes the actual PostgreSQL schema.

Reference: [Django's PostgreSQL configuration](https://docs.djangoproject.com/en/5.2/ref/databases/#postgresql-notes) and [direct SQL cursor usage](https://docs.djangoproject.com/en/5.2/topics/db/sql/#executing-custom-sql-directly).
