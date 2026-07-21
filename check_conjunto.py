import django
import os
import sys

sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato
from collections import Counter

print("=" * 80)
print("VERIFICANDO CAMPO CONJUNTO NOS CONTRATOS")
print("=" * 80)

# Contar por conjunto
conjuntos = Counter()
for contrato in Contrato.objects.all():
    conjuntos[contrato.conjunto or '(vazio)'] += 1

print("\nDistribuição de contratos por conjunto:")
for conjunto, qtd in sorted(conjuntos.items()):
    print(f"  {conjunto:15s}: {qtd:5d} contratos")

print(f"\nTotal: {Contrato.objects.count()} contratos")
