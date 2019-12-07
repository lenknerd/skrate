#!/bin/bash
# Set up appropriate user for just the skrate schema

set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE USER skrate_user WITH PASSWORD 'skrate_password';
    CREATE SCHEMA skrate;
    GRANT ALL PRIVILEGES ON SCHEMA skrate TO skrate_user;
EOSQL
