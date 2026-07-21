import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
import django
django.setup()

from principal.models import Contrato, ParcelaContrato

print(f"Contratos: {Contrato.objects.count():,}")
print(f"Parcelas: {ParcelaContrato.objects.count():,}")
