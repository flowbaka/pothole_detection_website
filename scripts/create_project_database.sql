-- Run with psql as the local PostgreSQL administrator.
-- This step creates only the database; the application account comes later.
\set ON_ERROR_STOP on
\pset pager off

-- Generate CREATE DATABASE only when the name is absent. Do not wrap this
-- script in a transaction: PostgreSQL creates databases outside transactions.
SELECT 'CREATE DATABASE pothole_db'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'pothole_db')
\gexec

-- Show the database and its owner without connecting a second time.
SELECT datname AS database, pg_get_userbyid(datdba) AS owner
FROM pg_database
WHERE datname = 'pothole_db';
