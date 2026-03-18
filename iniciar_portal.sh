#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py seed_demo
python -m webbrowser "http://127.0.0.1:8000/login/" >/dev/null 2>&1 || true
python manage.py runserver
