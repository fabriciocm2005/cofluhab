"""
Aplica migration manualmente
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from django.core.management import call_command

print("Aplicando migration...")
call_command('migrate', 'principal', '0006_add_contrato_fields')
print("✅ Migration aplicada!")
