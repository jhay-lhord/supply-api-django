#!/bin/bash

echo "Creating Migrations..."
python manage.py makemigrations

echo "Starting Migrations..."
python manage.py migrate

echo "Collecting Static Files..."
python manage.py collectstatic --noinput

echo "Running Server..."
python manage.py runserver 0.0.0.0:8000
