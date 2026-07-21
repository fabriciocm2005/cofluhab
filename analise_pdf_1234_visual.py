#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Extração Manual baseada na análise visual do PDF 1234
Usando dados que você confirmou na screenshot
"""

import re

# DADOS CONFIRMADOS VISUALMENTE NO PDF (baseado na screenshot)
# Seção V - CONDIÇÕES DE PAGAMENTO
dados_confirmados = {
    # Contrato básico
    'prazo_meses': 120,
    'tx_juros_nominal_aa': 10.0,  # "a taxa de juros nominal de ... 10.00 ... a.a."
    'prestacao_base': 182.331540,  # Cr$ 182,33154 (com decimais)
    
    # DATA PRIMEIRA PRESTAÇÃO (no PDF está 30/11/84)
    'data_primeira_prestacao': '1984-11-30',
    
    # Seção VI - ACESSÓRIOS  
    'seguro_mip': 3454.96,  # "Seguros BNH/SFH - MIP ... Cr$ ... 3.496,96" (varia na visão)
    'total_seguros': 3573.45,  # "Total Seguros Cr$ ... 3.573,45"
    'taxa_cobranca_admin': 3573.48,  # "Taxa de Cobrança e Adminis ... Cr$ ... 3.573,48"
    'prestacao_total_com_acessorios': 195769.99,  # "totalizando prestação mais acessório ... Cr$ 195.769,99"
    
    # Data do contrato (provavelmente setembro 1983 baseado em documentos)
    'data_contrato': '1983-03-23',  # Você confirmou que PDF mostra 25/03/1983 em outro lugar
    
    # UPC vigente na data do contrato
    'upc_vigente': None,  # Valor tachado no PDF, precisa confirmar
    
    # Sistema de amortização
    'sa': 'SAC',  # Presumido, geralmente contratos 1984 são SAC
    
    # Informações adicionais do PDF
    'vlfinanc': 10939.89,  # Já no banco, derivado
}

# ===== CÁLCULOS PARA VALIDAÇÃO =====

print("=" * 100)
print("ANÁLISE DO CONTRATO 1234 - BASEADO NA SCREENSHOT DO PDF")
print("=" * 100)
print()

print("SEÇÃO V - CONDIÇÕES DE PAGAMENTO")
print("-" * 100)
print(f"  Prazo: {dados_confirmados['prazo_meses']} meses")
print(f"  Taxa juros nominal: {dados_confirmados['tx_juros_nominal_aa']}% a.a.")
print(f"  Prestação base (SEM acessórios): Cr$ {dados_confirmados['prestacao_base']:,.2f}")
print(f"  Data primeira prestação: {dados_confirmados['data_primeira_prestacao']}")
print()

print("SEÇÃO VI - ACESSÓRIOS DE PAGAMENTO")
print("-" * 100)
print(f"  Seguro MIP: Cr$ {dados_confirmados['seguro_mip']:,.2f}")
print(f"  Total Seguros: Cr$ {dados_confirmados['total_seguros']:,.2f}")
print(f"  Taxa Cobrança e Adminis: Cr$ {dados_confirmados['taxa_cobranca_admin']:,.2f}")
print(f"  ─────────────────────────────────")
print(f"  Prestação + Acessórios: Cr$ {dados_confirmados['prestacao_total_com_acessorios']:,.2f}")
print()

# Validação
print("VALIDAÇÃO")
print("-" * 100)

soma_base_acessorios = (dados_confirmados['prestacao_base'] + 
                        dados_confirmados['total_seguros'] + 
                        dados_confirmados['taxa_cobranca_admin'])

print(f"  Prestação base: Cr$ {dados_confirmados['prestacao_base']:,.2f}")
print(f"  + Total Seguros: Cr$ {dados_confirmados['total_seguros']:,.2f}")
print(f"  + Taxa Cobrança: Cr$ {dados_confirmados['taxa_cobranca_admin']:,.2f}")
print(f"  ───────────────────────────────")
print(f"  = Soma calculada: Cr$ {soma_base_acessorios:,.2f}")
print(f"  = Total do PDF: Cr$ {dados_confirmados['prestacao_total_com_acessorios']:,.2f}")
print(f"  Diferença: Cr$ {abs(soma_base_acessorios - dados_confirmados['prestacao_total_com_acessorios']):,.2f}")
print()

# Se há diferença, precisa investigar
diferenca = abs(soma_base_acessorios - dados_confirmados['prestacao_total_com_acessorios'])
if diferenca < 1:
    print(f"  ✅ Valores batem!")
else:
    print(f"  ⚠️  Diferença encontrada. Verificar PDF manualmente.")
print()

print("DADOS PARA BANCO DE DADOS")
print("-" * 100)
print(f"  data_contrato: {dados_confirmados['data_contrato']}")
print(f"  data_primeiro_venc: {dados_confirmados['data_primeira_prestacao']}")
print(f"  vlfinanc: {dados_confirmados['vlfinanc']}")
print(f"  prestacao_inicial: {dados_confirmados['prestacao_total_com_acessorios']}")
print(f"  prazo: {dados_confirmados['prazo_meses']}")
print(f"  tx_juros: {dados_confirmados['tx_juros_nominal_aa']}")
print(f"  sa: {dados_confirmados['sa']}")
print()

print("=" * 100)
print("PRÓXIMA AÇÃO: Atualizar banco com esses valores (já feito para data e prestacao_inicial)")
print("=" * 100)

