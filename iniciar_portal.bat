@echo off
cd /d "%~dp0"
if not exist .venv (
  py -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py seed_demo
start http://127.0.0.1:8000/login/
python manage.py runserver
