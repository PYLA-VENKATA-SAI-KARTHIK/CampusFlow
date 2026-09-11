#!/bin/sh
set -e

# Run Alembic database migrations if RUN_MIGRATIONS is set to "true" (default for container startup)
if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
  echo "Applying database migrations..."
  alembic upgrade head
fi

exec "$@"
