#!/bin/sh
set -e

echo "Running database migrations..."
flask db upgrade

echo "Starting gunicorn..."
exec gunicorn -w 1 --threads 2 -b 0.0.0.0:5000 "app:create_app()"
