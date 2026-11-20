#!/bin/sh
export COOKIE_SECURE=1
exec .venv/bin/gunicorn --bind 127.0.0.1:8000 --workers 1 --threads 8 app:app
