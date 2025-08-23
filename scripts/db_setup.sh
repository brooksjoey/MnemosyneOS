scripts/db_setup.sh
#!/usr/bin/env bash
set -euo pipefail

DBUSER="mnemo"
DBPASS="mnemo"
DBNAME="mnemo"

sudo -u postgres psql -v ON_ERROR_STOP=1 <<SQL
DO
\$do\$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '${DBUSER}') THEN
      CREATE ROLE ${DBUSER} LOGIN PASSWORD '${DBPASS}';
   END IF;
END
\$do\$;

CREATE DATABASE ${DBNAME} OWNER ${DBUSER};
GRANT ALL PRIVILEGES ON DATABASE ${DBNAME} TO ${DBUSER};
\c ${DBNAME}
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
SQL

echo "Postgres ready with pgvector and pg_trgm."