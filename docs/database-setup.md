# Database setup: login and project database

The user has confirmed a local PostgreSQL administrator login. The next small milestone is creating `pothole_db`; the application account and backend connection remain separate later steps.

## Verified locally

- Windows service `postgresql-x64-18` is running.
- `pg_isready` reports that `127.0.0.1:5432` accepts connections.
- Installed `psql` client version: 18.6, under `C:\Program Files\PostgreSQL\18\bin`.
- The initial connection attempt without a password returned `no password supplied`. The user then ran the password-prompted command and supplied successful connection information: database/user `postgres`, host `127.0.0.1`, port `5432`.
- Login is confirmed by the user's output. Project database creation is not yet confirmed. No account, password or authentication configuration was changed. FastAPI is not connected to PostgreSQL yet.

## User step: verify your login

Run this in PowerShell:

```powershell
& 'C:\Program Files\PostgreSQL\18\bin\psql.exe' -X -h 127.0.0.1 -p 5432 -U postgres -d postgres -W -P pager=off -c '\conninfo'
```

Enter the PostgreSQL password chosen during installation when prompted. Password input is hidden; press Enter after typing it. Do not paste the password into chat, source code or the command itself.

The command prints connection information and exits. Report whether it connects successfully, or share the error without a password. If the installation password is unknown, stop at this step and say so; do not reset an existing installation or weaken authentication.

## Current user step: create the project database

The prepared `scripts/create_project_database.sql` checks whether `pothole_db` exists, creates it if absent, and prints its name and owner. An existing database is left unchanged. It disables the output pager so `-- More --` will not pause the result, and stops on SQL errors.

Run in PowerShell:

```powershell
Set-Location 'C:\Users\kshit\Documents\pothole_project'
& 'C:\Program Files\PostgreSQL\18\bin\psql.exe' -X -h 127.0.0.1 -p 5432 -U postgres -d postgres -W -f 'scripts/create_project_database.sql'
```

Enter the installation password locally when prompted. A newly created database should produce `CREATE DATABASE`, followed by a row showing `pothole_db` and its owner (normally `postgres` for this command). If the database already existed, only the final query result is needed; do not drop it or change its owner. Share the result before proceeding.

This script has been reviewed against PostgreSQL 18 documentation but has not been run against the user's authenticated server. Database creation remains pending user execution. No project tables are created in this step.

The next separate step will prepare a dedicated application account. FastAPI should not use the PostgreSQL administrator account for normal operation.

References: [psql file execution and generated queries](https://www.postgresql.org/docs/18/app-psql.html), [CREATE DATABASE](https://www.postgresql.org/docs/18/sql-createdatabase.html).
