# -*- coding: utf-8 -*-
"""Investigar saldos por período"""
import django
import os
import sys
from datetime import date
from decimal import Decimal

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato, ParcelaContrato

print("\n" + "="*80)
print("INVESTIGACAO: SALDOS POR PERIODO")
print("="*80 + "\n")

# Analisar distribuição de datas das últimas parcelas
periodos = {
    'antes_1990': [],
    '1990_1994': [],
    '1995_2000': [],
    '2001_2010': [],
    '2011_2019': [],
    'apos_2019': []
}

for contrato in Contrato.objects.all():
    ultima = ParcelaContrato.objects.filter(contrato=contrato).order_by('-nmens').first()
    
    if not ultima or not ultima.sddev or not ultima.dtvenc:
        continue
    
    data = ultima.dtvenc
    saldo = ultima.sddev
    
    if data < date(1990, 1, 1):
        periodos['antes_1990'].append({'contrato': contrato.codigo, 'data': data, 'saldo': saldo})
    elif data < date(1994, 7, 1):
        periodos['1990_1994'].append({'contrato': contrato.codigo, 'data': data, 'saldo': saldo})
    elif data < date(2000, 1, 1):
        periodos['1995_2000'].append({'contrato': contrato.codigo, 'data': data, 'saldo': saldo})
    elif data < date(2010, 1, 1):
        periodos['2001_2010'].append({'contrato': contrato.codigo, 'data': data, 'saldo': saldo})
    elif data < date(2019, 1, 1):
        periodos['2011_2019'].append({'contrato': contrato.codigo, 'data': data, 'saldo': saldo})
    else:
        periodos['apos_2019'].append({'contrato': contrato.codigo, 'data': data, 'saldo': saldo})

for periodo, dados in periodos.items():
    if dados:
        total = sum([d['saldo'] for d in dados])
        print(f"\n{periodo}:")
        print(f"  Quantidade: {len(dados)} contratos")
        print(f"  Saldo Total: R$ {total:,.2f}")
        print(f"  Media: R$ {total/len(dados):,.2f}")
        print(f"  Exemplo: Contrato {dados[0]['contrato']} - {dados[0]['data']} - R$ {dados[0]['saldo']:,.2f}")

# Verificar se existe alguma parcela com data próxima de maio/2019
print("\n" + "="*80)
print("PROCURANDO PARCELAS DE MAIO/2019")
print("="*80 + "\n")

parcelas_maio_2019 = []
for contrato in Contrato.objects.all()[:100]:  # Amostra de 100
    parcelas = ParcelaContrato.objects.filter(
        contrato=contrato,
        dtvenc__year=2019,
        dtvenc__month=5
    )
    if parcelas.exists():
        for p in parcelas:
            parcelas_maio_2019.append({
                'contrato': contrato.codigo,
                'mes': p.nmens,
                'data': p.dtvenc,
                'saldo': p.sddev
            })

if parcelas_maio_2019:
    print(f"Encontradas {len(parcelas_maio_2019)} parcelas de maio/2019:")
    for p in parcelas_maio_2019[:5]:
        print(f"  Contrato {p['contrato']} - Mes {p['mes']} - {p['data']} - R$ {p['saldo']:,.2f}")
else:
    print("NENHUMA parcela de maio/2019 encontrada!")
    print("\nVerificando parcelas de 2019:")
    parcelas_2019 = ParcelaContrato.objects.filter(dtvenc__year=2019)[:10]
    for p in parcelas_2019:
        print(f"  Contrato {p.contrato.codigo} - {p.dtvenc} - R$ {p.sddev:,.2f}")

print("\n" + "="*80 + "\n")
