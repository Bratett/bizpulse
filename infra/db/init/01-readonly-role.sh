#!/bin/bash
set -e

# Create read-only role for Analytics Service using env var from docker-compose
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '${POSTGRES_READONLY_USER:-bizpulse_readonly}') THEN
            CREATE ROLE ${POSTGRES_READONLY_USER:-bizpulse_readonly} WITH LOGIN PASSWORD '${POSTGRES_READONLY_PASSWORD:-changeme_in_production}';
        END IF;
    END
    \$\$;

    GRANT CONNECT ON DATABASE ${POSTGRES_DB} TO ${POSTGRES_READONLY_USER:-bizpulse_readonly};
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO ${POSTGRES_READONLY_USER:-bizpulse_readonly};
EOSQL
