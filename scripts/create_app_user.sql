-- Connect to pothole_db as postgres. Passwords are entered at the terminal.
\set ON_ERROR_STOP on
\pset pager off

BEGIN;
DO $$
BEGIN
    IF current_database() <> 'pothole_db' THEN
        RAISE EXCEPTION 'Connect to pothole_db before running this script.';
    END IF;
END;
$$;

-- Stop if this role already exists; never overwrite an existing login.
CREATE ROLE pothole_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE
    NOREPLICATION NOBYPASSRLS;

\echo Choose a new password for pothole_app, then enter it again to confirm.
\password pothole_app

-- An empty password disables password login. Roll back rather than reporting
-- successful setup when no password was set. Never print the password hash.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_authid
        WHERE rolname = 'pothole_app' AND rolpassword IS NOT NULL
    ) THEN
        RAISE EXCEPTION 'No application password was set. Run again with a nonempty password.';
    END IF;
END;
$$;

GRANT CONNECT ON DATABASE pothole_db TO pothole_app;
-- Allow the upcoming application tables to be created in this database.
GRANT USAGE, CREATE ON SCHEMA public TO pothole_app;
COMMIT;

SELECT rolname AS app_user, rolsuper AS superuser, rolcanlogin AS can_login,
       has_database_privilege(rolname, 'pothole_db', 'CONNECT') AS can_connect,
       (has_schema_privilege(rolname, 'public', 'USAGE') AND
        has_schema_privilege(rolname, 'public', 'CREATE')) AS can_create_tables
FROM pg_roles
WHERE rolname = 'pothole_app';
