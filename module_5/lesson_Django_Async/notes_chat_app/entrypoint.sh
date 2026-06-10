#!/bin/sh
set -e
python manage.py migrate --noinput
python manage.py collectstatic --noinput
exec python -m uvicorn notes_project.asgi:application \
    --host 0.0.0.0 --port 8001 --reload
