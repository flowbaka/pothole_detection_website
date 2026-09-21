# Database setup: login and project database

The user has confirmed a local PostgreSQL administrator login and creation of `pothole_db`, owned by `postgres`. The current small milestone is preparing the `pothole_app` login; its actual login test and the backend connection remain later steps.

## Verified locally

- Windows service `postgresql-x64-18` is running.
- `pg_isready` reports that `127.0.0.1:5432` accepts connections.
- Installed `psql` client version: 18.6, under `C:\Program Files\PostgreSQL\18\bin`.
- The initial connection attempt without a password returned `no password supplied`. The user then ran the password-prompted command and supplied successful connection information: database/user `postgres`, host `127.0.0.1`, port `5432`.
- The user's output confirmed `CREATE DATABASE` and a row showing `pothole_db` owned by `postgres`. Application account creation is not yet confirmed. FastAPI is not connected to PostgreSQL yet.

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

## Current user step: create the application login

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

The script was reviewed against PostgreSQL 18 documentation; it has not been run in an authenticated session here. Account creation remains pending the user's result. Next, test the new login separately before connecting FastAPI.

References: [psql file execution and password prompts](https://www.postgresql.org/docs/18/app-psql.html), [CREATE DATABASE](https://www.postgresql.org/docs/18/sql-createdatabase.html), [CREATE ROLE](https://www.postgresql.org/docs/18/sql-createrole.html), [schema permissions](https://www.postgresql.org/docs/18/ddl-schemas.html).
