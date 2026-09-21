# Database setup: first connection

The next small milestone is confirming a local PostgreSQL login before creating the project's database and application account.

## Verified locally

- Windows service `postgresql-x64-18` is running.
- `pg_isready` reports that `127.0.0.1:5432` accepts connections.
- Installed `psql` client version: 18.6, under `C:\Program Files\PostgreSQL\18\bin`.
- A connection attempt as `postgres` without a password reached authentication and returned `no password supplied`. An authenticated login has not yet been verified.
- No database, account, password or authentication configuration was changed. FastAPI is not connected to PostgreSQL yet.

## User step: verify your login

Run this in PowerShell:

```powershell
& 'C:\Program Files\PostgreSQL\18\bin\psql.exe' -X -h 127.0.0.1 -p 5432 -U postgres -d postgres -W -c '\conninfo'
```

Enter the PostgreSQL password chosen during installation when prompted. Password input is hidden; press Enter after typing it. Do not paste the password into chat, source code or the command itself.

The command prints connection information and exits. Report whether it connects successfully, or share the error without a password. If the installation password is unknown, stop at this step and say so; do not reset an existing installation or weaken authentication.

After a successful login, the next separate step will be creating a dedicated project database and application account. The application should not use the PostgreSQL administrator account for normal operation.
