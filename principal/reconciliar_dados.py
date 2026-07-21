#!/usr/bin/env python
"""Script para reconciliar dados de contratos"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato, ParcelaContrato
from principal.views import calcular_fcvs_residual_global

# Get contract 1234
contrato = Contrato.objects.filter(id_pdf='1234').first()
if not contrato:
    print("❌ Contrato 1234 não encontrado")
    sys.exit(1)

print("=" * 80)
print("RECONCILIAÇÃO DE DADOS - CONTRATO 1234")
print("=" * 80)
print()

print("DADOS DO BANCO DE DADOS:")
print(f"  id                = {contrato.id}")
print(f"  id_pdf            = {contrato.id_pdf}")
print(f"  data_contrato     = {contrato.data_contrato}")
print(f"  vlfinanc          = {contrato.vlfinanc}")
print(f"  prestacao_inicial = {contrato.prestacao_inicial}")
print(f"  prazo             = {contrato.prazo} meses")
print(f"  tx_juros          = {contrato.tx_juros}% a.a.")
print(f"  sa                = {contrato.sa}")
print()

# Check parcelas no banco
parcelas_banco = ParcelaContrato.objects.filter(contrato=contrato).count()
print(f"PARCELAS NO BANCO: {parcelas_banco} registros")
print()

# Simular
print("EXECUTANDO SIMULAÇÃO...")
evolucao_fmt, anomalias, fcvs_final = calcular_fcvs_residual_global(contrato.id)

print(f"  Total meses simulados: {len(evolucao_fmt)}")
print(f"  Anomalias detectadas: {anomalias}")
print(f"  FCVS residual: R$ {fcvs_final:.2f}")
print()

# Analisar mês 1
m1 = evolucao_fmt[0]
print("MÊS 1 - CHAVES E VALORES:")
for chave in sorted(m1.keys()):
    valor = m1[chave]
    print(f"  {chave:20s} = {valor}")
print()

# Reconciliação
print("=" * 80)
print("RECONCILIAÇÃO:")
print("=" * 80)

expected_saldo_ant = float(contrato.vlfinanc or 0)
actual_saldo_ant = m1.get('saldo_ant')

print(f"Saldo anterior (esperado = vlfinanc): {expected_saldo_ant}")
print(f"Saldo anterior (retornado):           {actual_saldo_ant}")

if expected_saldo_ant == actual_saldo_ant:
    print("✅ OK!")
else:
    print(f"⚠️  DISCREPÂNCIA: {abs(expected_saldo_ant - actual_saldo_ant)}")
print()

# Verificar prestacao_inicial vs encargo
expected_encargo = (float(contrato.vlfinanc) / contrato.prazo) + \
                   (float(contrato.vlfinanc) * float(contrato.tx_juros or 10) / 100 / 12)
actual_encargo = m1.get('encargo')

print(f"Encargo esperado (SAC): {expected_encargo:.4f}")
print(f"Encargo retornado:      {actual_encargo:.4f}")

if abs(expected_encargo - actual_encargo) < 0.01:
    print("✅ OK!")
else:
    print(f"⚠️  DIFERENÇA: {abs(expected_encargo - actual_encargo):.4f}")
print()
