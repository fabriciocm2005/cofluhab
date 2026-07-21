# -*- coding: utf-8 -*-
"""Script para verificar estatísticas dos saldos"""
import django
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato, ParcelaContrato
from decimal import Decimal

print("\n" + "="*80)
print("VERIFICANDO SALDOS DEVEDORES")
print("="*80 + "\n")

# Coletar todos os saldos
saldos = []
for contrato in Contrato.objects.all():
    ultima_parcela = ParcelaContrato.objects.filter(contrato=contrato).order_by('-nmens').first()
    if ultima_parcela and ultima_parcela.sddev:
        saldos.append({
            'codigo': contrato.codigo,
            'saldo': ultima_parcela.sddev
        })

saldos.sort(key=lambda x: x['saldo'])

print(f"Total de contratos com saldo: {len(saldos)}\n")

# Estatísticas
saldo_min = saldos[0]['saldo']
saldo_max = saldos[-1]['saldo']
saldo_total = sum([s['saldo'] for s in saldos])
saldo_medio = saldo_total / len(saldos)

print(f"Saldo MINIMO: R$ {saldo_min:,.2f}")
print(f"Saldo MAXIMO: R$ {saldo_max:,.2f}")
print(f"Saldo MEDIO: R$ {saldo_medio:,.2f}")
print(f"Saldo TOTAL: R$ {saldo_total:,.2f}")

print(f"\n10 MENORES saldos:")
for item in saldos[:10]:
    print(f"  Contrato {item['codigo']}: R$ {item['saldo']:,.2f}")

print(f"\n10 MAIORES saldos:")
for item in saldos[-10:]:
    print(f"  Contrato {item['codigo']}: R$ {item['saldo']:,.2f}")

print("\n" + "="*80 + "\n")
