#!/bin/bash
set -e

echo "Starting Application..."

DB_HOST=$(echo "$DATABASE_URL" | sed -n 's/.*@\([^:\/]*\).*/\1/p')
DB_HOST=${DB_HOST:-localhost}

echo "Waiting database $DB_HOST..."
while ! pg_isready -h "$DB_HOST" -p 5432 -U postgres; do
  echo "Database is not ready, waiting..."
  sleep 1
done

echo "Database is ready!"

# DETALHE DESSA ABORDAGEM >> Usar esse entrypoint em arquiteturas orientadas a microsserviço pode gerar problemas
if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
  echo "Running migrations..."
  python manage.py migrate --noinput
  echo "Migrations is done!"
fi

echo "Ready to start..."
exec "$@"
