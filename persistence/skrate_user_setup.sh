#!/bin/bash
# Set up appropriate user for skrate database, also a testing version of database

set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE USER skrate_user WITH PASSWORD 'skrate_password';
    GRANT ALL PRIVILEGES ON SCHEMA public TO skrate_user;
    CREATE USER skrate_test_user WITH PASSWORD 'skrate_test_password';
	CREATE DATABASE skrate_test_db;
    GRANT ALL PRIVILEGES ON DATABASE skrate_test_db TO skrate_test_user;
	GRANT ALL PRIVILEGES ON DATABASE skrate_test_db TO postgres;
EOSQL
