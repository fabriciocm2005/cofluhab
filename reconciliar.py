"""
Reconcile contract data - run with: python manage.py shell < reconciliar.py
"""

from principal.models import Contrato, ParcelaContrato
from principal.views import calcular_fcvs_residual_global

contrato = Contrato.objects.filter(id_pdf='1234').first()
if not contrato:
    print("❌ Contrato 1234 não encontrado")
else:
    print("=" * 80)
    print("RECONCILIAÇÃO - CONTRATO 1234")
    print("=" * 80)
    print()
    
    print("BANCO DE DADOS:")
    print(f"  vlfinanc = {contrato.vlfinanc}")
    print(f"  prazo = {contrato.prazo}")
    print(f"  tx_juros = {contrato.tx_juros}%")
    print(f"  sa = {contrato.sa}")
    print()
    
    evolucao_fmt, anomalias, fcvs_final = calcular_fcvs_residual_global(contrato.id)
    m1 = evolucao_fmt[0]
    
    print("MÊS 1:")
    print(f"  saldo_ant = {m1['saldo_ant']}")
    print(f"  encargo = {m1['encargo']}")
    print(f"  juros = {m1['juros']}")
    print(f"  amort = {m1['amort']}")
    print(f"  prest_pes = {m1['prest_pes']}")
    print(f"  moeda = {m1['moeda']}")
