# -*- coding: utf-8 -*-
"""
Varredura de saldos da carteira FCVS
Identifica contratos com valores em moeda antiga que inflam o total
"""
import django
import os
import sys
from datetime import date
from decimal import Decimal

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato, ParcelaContrato

DATA_CZ   = date(1986, 2, 28)
DATA_NCZ  = date(1989, 1, 16)
DATA_CRR  = date(1993, 8, 1)
DATA_REAL = date(1994, 7, 1)

def identificar_moeda(dt):
    if dt is None:           return 'DESCONHECIDA'
    if dt >= DATA_REAL:      return 'REAL'
    if dt >= DATA_CRR:       return 'CRUZEIRO REAL'
    if dt >= DATA_CRR:       return 'CRUZEIRO'
    if dt >= date(1990,3,16):return 'CRUZEIRO (novo)'
    if dt >= DATA_NCZ:       return 'CRUZADO NOVO'
    if dt >= DATA_CZ:        return 'CRUZADO'
    return 'CRUZEIRO (antigo)'

def conv(valor, dt):
    v = Decimal(str(valor))
    fator = Decimal('1')
    if dt is None or dt >= DATA_REAL:
        return v, fator
    if dt < DATA_CZ:
        v /= 1000; fator *= 1000
    if dt < DATA_NCZ:
        v /= 1000; fator *= 1000
    if dt < DATA_CRR:
        v /= 1000; fator *= 1000
    v /= 2750; fator *= 2750
    return v, fator

contratos = Contrato.objects.all()
total_bruto = Decimal('0')
total_real  = Decimal('0')
ant = []
pos_count = 0
sem_parcela = 0
sem_saldo = 0

for c in contratos:
    ult = ParcelaContrato.objects.filter(contrato=c).order_by('-nmens').first()
    if not ult:
        sem_parcela += 1
        continue
    saldo_raw = ult.sddev_original if ult.sddev_original else ult.sddev
    if not saldo_raw or saldo_raw == 0:
        sem_saldo += 1
        continue
    dt = ult.dtvenc
    total_bruto += Decimal(str(saldo_raw))
    saldo_r, fator = conv(saldo_raw, dt)
    total_real += saldo_r
    if dt and dt < DATA_REAL:
        ant.append({
            'codigo': c.codigo,
            'dt': dt,
            'moeda': identificar_moeda(dt),
            'saldo_raw': float(saldo_raw),
            'saldo_real': float(saldo_r),
            'fator': float(fator),
        })
    else:
        pos_count += 1

ant.sort(key=lambda x: x['saldo_raw'], reverse=True)

print("=" * 90)
print("VARREDURA SALDO CARTEIRA FCVS - Identificacao de Valores Exorbitantes")
print("=" * 90)
print()
print(f"  Total BRUTO no card (moeda original somada):  R$ {float(total_bruto):>20,.2f}")
print(f"  Total CORRETO convertido para Real:           R$ {float(total_real):>20,.2f}")
print(f"  Diferenca (inflacao por moeda antiga):        R$ {float(total_bruto - total_real):>20,.2f}")
print()
print(f"  Contratos com ultima parcela PRE-1994 (moeda antiga): {len(ant)}")
print(f"  Contratos com ultima parcela POS-1994 (Real):         {pos_count}")
print(f"  Contratos sem parcela:                                {sem_parcela}")
print(f"  Contratos sem saldo:                                  {sem_saldo}")
print()

# TOP 30 maiores valores brutos (os que mais inflam o total)
print("-" * 90)
print(f"{'Contrato':<12} {'Dt Ultima':<12} {'Moeda':<20} {'Saldo Bruto':>18} {'Fator':>10} {'Saldo Real R$':>18}")
print("-" * 90)
for r in ant[:30]:
    print(f"{str(r['codigo']):<12} {str(r['dt']):<12} {r['moeda']:<20} {r['saldo_raw']:>18,.2f} {r['fator']:>10,.0f} {r['saldo_real']:>18,.2f}")

print("-" * 90)
soma_top = sum(r['saldo_raw'] for r in ant)
soma_top_real = sum(r['saldo_real'] for r in ant)
print(f"  SOMA total moeda antiga (bruto):   R$ {soma_top:>20,.2f}")
print(f"  SOMA total moeda antiga (em R$):   R$ {soma_top_real:>20,.2f}")
print()

# Gravar CSV
import csv
csv_path = os.path.join(os.path.dirname(__file__), 'varredura_saldo_carteira.csv')
with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.DictWriter(f, fieldnames=['codigo','dt','moeda','saldo_raw','saldo_real','fator'])
    writer.writeheader()
    writer.writerows(ant)
print(f"CSV gerado: {csv_path}")
