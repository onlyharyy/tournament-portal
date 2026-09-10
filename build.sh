#!/usr/bin/env bash

pip install -r requirements.txt

python manage.py migrate

python manage.py shell -c "
from django.contrib.auth import get_user_model
import os
User = get_user_model()
username = os.getenv('ADMIN')
password = os.getenv('123456')
if username and password and not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, password=password)
"

python manage.py collectstatic --noinput