import os
import sys
import django

sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')

from django.core.management import execute_from_command_line

execute_from_command_line(['manage.py', 'runserver'])
