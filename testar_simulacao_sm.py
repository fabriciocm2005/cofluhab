"""
Teste rápido do simulador com índices reais (IPCA/TR) e PES via SM.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
import django; django.setup()

from decimal import Decimal
from datetime import date
from principal.simulador_sfh import simular_evolucao_sfh, carregar_indices_sfh, carregar_indices_pes

BASE = os.path.dirname(__file__)
CSV_CM  = os.path.join(BASE, 'principal', 'indices_historicos.csv')
CSV_PES = os.path.join(BASE, 'principal', 'indices_pes.csv')

indices_cm  = carregar_indices_sfh(CSV_CM)
indices_pes = carregar_indices_pes(CSV_PES)
print(f"CM: {len(indices_cm)} entradas, PES-SM: {len(indices_pes)} entradas")

evolucao, fcvs_final = simular_evolucao_sfh(
    vlfinanc=Decimal('195769.99'),
    sa='SAC',
    tx_juros_aa=Decimal('10'),   # 10% a.a. (o simulador divide por 100 internamente)
    prazo=120,
    data_contrato=date(1983, 3, 1),
    prestacao_inicial=Decimal('182.3315'),
    indices_cm=indices_cm,
    indices_pes=indices_pes,
)

print()
hdr = f"{'Mes':>4}  {'Data':<10}  {'SaldoAnt':>16}  {'CM%':>7}  {'Amort':>14}  {'Encargo':>12}  {'PrestPES':>12}  {'FCVSmes':>12}  {'SaldoNovo':>16}  Moeda"
print(hdr)
for m in evolucao:
    linha = (
        f"{m['mes']:>4}  {m['data']:<10}  "
        f"{m['saldo_ant']:>16,.2f}  "
        f"{m['cm_pct']:>6.2f}%  "
        f"{m['amort']:>14,.2f}  "
        f"{m['encargo']:>12,.4f}  "
        f"{m['prest_pes']:>12,.4f}  "
        f"{m['fcvs_mes']:>12,.2f}  "
        f"{m['saldo_novo']:>16,.2f}  "
        f"{m['moeda']}"
    )
    print(linha)

print()
print(f"fcvs_acum final: {evolucao[-1]['fcvs_acum']:,.4f} {evolucao[-1]['moeda']}")
print(f"FCVS FINAL (R$): {fcvs_final:,.2f}")
