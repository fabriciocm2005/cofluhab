"""
Testa simulação do contrato 1234 com os índices reais (IPCA/TR do BCB).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')

import django
django.setup()

from decimal import Decimal
from principal.simulador_sfh import simular_evolucao_sfh, carregar_indices_sfh

CSV = os.path.join(os.path.dirname(__file__), 'principal', 'indices_historicos.csv')

indices = carregar_indices_sfh(CSV)
print(f"Total indices carregados: {len(indices)}")

# Contrato 1234 — dados do banco
vlfinanc = Decimal('195769.99')
sa = 'SAC'
tx_juros_aa = Decimal('0.10')
prazo = 120
from datetime import date
data_contrato = date(1983, 3, 1)
prestacao_inicial = Decimal('182.3315')

print(f"\nSimulando contrato: Cr$ {vlfinanc}, {sa}, {tx_juros_aa*100}% a.a., {prazo} meses, inicio {data_contrato}")
print(f"Prestacao inicial (PES): Cr$ {prestacao_inicial}")
print()

evolucao, fcvs_final = simular_evolucao_sfh(
    vlfinanc=vlfinanc,
    sa=sa,
    tx_juros_aa=tx_juros_aa,
    prazo=prazo,
    data_contrato=data_contrato,
    prestacao_inicial=prestacao_inicial,
    indices_cm=indices,
)

print(f"{'Mes':>4}  {'Data':<10}  {'SaldoAnt':>18}  {'CM%':>7}  {'Amort':>16}  {'Encargo':>16}  {'PrestPES':>14}  {'FCVSmes':>16}  {'SaldoNovo':>18}  Moeda")
for m in evolucao:
    saldo_ant_fmt = f"{m['saldo_anterior']:,.2f}"
    saldo_novo_fmt = f"{m['saldo_devedor']:,.2f}"
    amort_fmt = f"{m['amort']:,.2f}"
    encargo_fmt = f"{m['encargo']:,.4f}"
    ppes_fmt = f"{m['prest_pes']:,.4f}"
    fcvs_fmt = f"{m['fcvs_mes']:,.2f}"
    cm_pct = f"{float(m['cm_aplicado'])*100:.2f}%"
    print(f"{m['mes']:>4}  {m['data']:<10}  {saldo_ant_fmt:>18}  {cm_pct:>7}  {amort_fmt:>16}  {encargo_fmt:>16}  {ppes_fmt:>14}  {fcvs_fmt:>16}  {saldo_novo_fmt:>18}  {m['moeda']}")

print(f"\nFCVS FINAL (R$): R$ {fcvs_final:,.2f}")
