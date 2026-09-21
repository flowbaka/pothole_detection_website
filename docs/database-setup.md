# Database setup: login and project database

The user has confirmed creation of `pothole_db`, creation and grants for `pothole_app`, and a successful password-authenticated login as `pothole_app` with superuser off. Local settings are now saved, and a real HTTP request through FastAPI successfully reached PostgreSQL. The database connection checkpoint is complete. The next small milestone will add the first report table.

## Verified locally

- Windows service `postgresql-x64-18` is running.
- `pg_isready` reports that `127.0.0.1:5432` accepts connections.
- Installed `psql` client version: 18.6, under `C:\Program Files\PostgreSQL\18\bin`.
- The initial connection attempt without a password returned `no password supplied`. The user then ran the password-prompted command and supplied successful connection information: database/user `postgres`, host `127.0.0.1`, port `5432`.
- The user's output confirmed `CREATE DATABASE` and a row showing `pothole_db` owned by `postgres`.
- The user confirmed `pothole_app` with superuser `f` and login/connection/table-creation privileges `t`. A subsequent `\conninfo` confirmed password-authenticated access as `pothole_app` to `pothole_db`, host `127.0.0.1`, port `5432`, superuser off.
- A real HTTP check through a temporary localhost-only Uvicorn server returned HTTP 200 from `/health` and `/health/database`, with the latter returning `{"status":"ok","database":"connected"}`. This used the existing local `.env` through the application's normal configuration path, with no mocked database driver. Password values were not displayed.
- The temporary server was stopped after checking. Port 8001 did not return a successful database-health response before this check; start the development server with the command below to view the result in a browser.

## User step: verify your login

Run this in PowerShell:

```powershell
& 'C:\Program Files\PostgreSQL\18\bin\psql.exe' -X -h 127.0.0.1 -p 5432 -U postgres -d postgres -W -P pager=off -c '\conninfo'
```

Enter the PostgreSQL password chosen during installation when prompted. Password input is hidden; press Enter after typing it. Do not paste the password into chat, source code or the command itself.

The command prints connection information and exits. Report whether it connects successfully, or share the error without a password. If the installation password is unknown, stop at this step and say so; do not reset an existing installation or weaken authentication.

## Completed user step: create the project database

The prepared `scripts/create_project_database.sql` checks whether `pothole_db` exists, creates it if absent, and prints its name and owner. An existing database is left unchanged. It disables the output pager so `-- More --` will not pause the result, and stops on SQL errors.

Run in PowerShell:

```powershell
Set-Location 'C:\Users\kshit\Documents\pothole_project'
& 'C:\Program Files\PostgreSQL\18\bin\psql.exe' -X -h 127.0.0.1 -p 5432 -U postgres -d postgres -W -f 'scripts/create_project_database.sql'
```

Enter the installation password locally when prompted. A newly created database should produce `CREATE DATABASE`, followed by a row showing `pothole_db` and its owner (normally `postgres` for this command). If the database already existed, only the final query result is needed; do not drop it or change its owner. Share the result before proceeding.

The user ran this script and shared successful creation output. No project tables are created in this step.

## Completed user step: create the application login

Run in PowerShell from the project folder:

```powershell
Set-Location 'C:\Users\kshit\Documents\pothole_project'
& 'C:\Program Files\PostgreSQL\18\bin\psql.exe' -X -h 127.0.0.1 -p 5432 -U postgres -d pothole_db -W -f 'scripts/create_app_user.sql'
```

There are two kinds of password prompt:

1. At the initial `Password:` prompt, enter the existing `postgres` administrator password.
2. At the new-password prompts for `pothole_app`, choose a different application password and enter it twice. Keep it locally for the upcoming connection setup; do not share it in chat or put it in source files.

The script uses psql's `\password` command so the password is entered privately instead of appearing in SQL text. It creates a login without superuser, database-creation, role-management, replication or row-security-bypass powers, grants database connection and `USAGE, CREATE` on this database's `public` schema, and prints permission booleans. These schema permissions support creating the application's own tables during development; existing tables are not automatically granted to it. This does not remove privileges inherited through PostgreSQL's `PUBLIC` role.

Expected final row: `pothole_app`, followed by `f` for superuser and `t` for login, connection and table creation. Share that row or the error, never a password. This checks configured permissions, not an actual login as `pothole_app`.

The changes run in a transaction. Connecting to the wrong database, an existing role, an empty password or a SQL error prevents completion; an uncommitted transaction rolls back when the script exits. If the role already exists, stop and report the error rather than deleting it or resetting its password. A successful run leaves `postgres` as database owner.

The user ran this step and supplied successful permission results, then confirmed a separate login as `pothole_app`. The backend can now be configured with that account.

## Completed step: configure and verify the Python connection

The project's virtual environment now includes Psycopg 3.3.6 and python-dotenv 1.2.3. On another checkout, install `requirements.txt` first. Run:

```powershell
Set-Location 'C:\Users\kshit\Documents\pothole_project'
.\.pothholevenv\Scripts\python.exe -m scripts.configure_database
```

Enter the **pothole_app** password at the hidden prompt. The helper runs `SELECT 1`, closes the connection, and saves settings to the ignored `.env` only after success. It preserves other environment-file keys and handles special password characters. Passwords must stay out of chat and Git. `.env.example` contains only defaults and an empty password.

Expected success: `Database connection OK. Settings saved to the Git-ignored .env file.` Share that message or the generic failure; no password is needed in chat. Configuration is read from this project's `.env` regardless of the launch directory, with process `DB_*` environment variables taking precedence. If those are already set, they override saved values until removed from that process.

After setup succeeds, start or restart the API in PowerShell:

```powershell
.\.pothholevenv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8001
```

Open `http://127.0.0.1:8001/health/database`. Success returns HTTP 200 and `{"status":"ok","database":"connected"}`. Missing/invalid settings or a database failure return HTTP 503 with a generic message, never the driver exception or password. `GET /health` still checks only the API process. The database check uses a three-second connection timeout and a three-second statement timeout. It creates no tables and uploads no recordings.

Seven automated tests cover missing configuration, invalid ports, literal password handling and environment precedence, connection cleanup, real driver refusal on an unused local port, setup success/failure, and API success/error responses with sanitized output. Successful database queries in these unit tests are simulated. Separately, the real HTTP check described above verified a successful query using the saved local settings. Run the unit tests with:

```powershell
.\.pothholevenv\Scripts\python.exe -m unittest discover -s tests -p test_database.py -v
```

The real API check is complete. It ran only `SELECT 1`, so it does not establish that report tables or uploads exist. The next checkpoint will add the first report table.

Driver/configuration references: [Psycopg connections](https://www.psycopg.org/psycopg3/docs/basic/usage.html), [python-dotenv](https://bbc2.github.io/python-dotenv/reference/).

References: [psql file execution and password prompts](https://www.postgresql.org/docs/18/app-psql.html), [CREATE DATABASE](https://www.postgresql.org/docs/18/sql-createdatabase.html), [CREATE ROLE](https://www.postgresql.org/docs/18/sql-createrole.html), [schema permissions](https://www.postgresql.org/docs/18/ddl-schemas.html).
