#!/usr/bin/env bash
# exit on error
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

# This command just collects your static files
python manage.py collectstatic --noinput

# DO NOT run makemigrations or migrate here
