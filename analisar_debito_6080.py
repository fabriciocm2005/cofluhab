#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Analisar débitos do contrato 6080 e aplicar conversões monetárias
"""

from dbfread import DBF
from datetime import datetime

print("="*80)
print("ANÁLISE DÉBITOS CONTRATO 6080")
print("="*80)

# Tabela de conversões monetárias do Brasil
# Fonte: Banco Central do Brasil
from datetime import date

DATA_CRUZEIRO_PARA_CR = date(1993, 8, 1)
DATA_CR_PARA_REAL = date(1994, 7, 1)
FATOR_CR_PARA_CR = 1000.0  # Cr$ -> CR$ (dividir por 1000)
FATOR_CR_PARA_REAL = 2750.0  # CR$ -> R$ (dividir por 2750)

def converter_para_real(valor, data_vencimento):
    """
    Converte valor de moeda antiga para Real baseado na data de vencimento
    """
    if not data_vencimento or not valor:
        return valor
    
    valor_convertido = float(valor)
    
    # Antes de 01/08/1993: Cruzeiro (Cr$)
    if data_vencimento < DATA_CRUZEIRO_PARA_CR:
        # Cr$ -> CR$ (dividir por 1000)
        valor_convertido = valor_convertido / FATOR_CR_PARA_CR
        
    # Entre 01/08/1993 e 30/06/1994: Cruzeiro Real (CR$)
    if data_vencimento < DATA_CR_PARA_REAL:
        # CR$ -> R$ (dividir por 2750)
        valor_convertido = valor_convertido / FATOR_CR_PARA_REAL
    
    # Depois de 01/07/1994: já é Real (R$)
    
    return valor_convertido

try:
    db = DBF('dados_antigos/DEBPREST.DBF', encoding='latin1')
    
    print("\nBuscando débitos do contrato 6080...")
    debitos_6080 = []
    
    for rec in db:
        contrato = str(rec.get('CONTRATO', '')).strip()
        if contrato in ['006080', '6080']:
            debitos_6080.append(rec)
    
    if not debitos_6080:
        print("❌ Contrato 6080 não encontrado!")
    else:
        print(f"\n✓ Encontrados {len(debitos_6080)} débitos para o contrato 6080\n")
        
        total_original = 0.0
        total_convertido = 0.0
        
        print(f"{'Prestação':<10} {'Vencimento':<12} {'Valor Original':<15} {'Moeda':<15} {'Valor em R$':<15}")
        print("-" * 80)
        
        for deb in debitos_6080[:10]:  # Mostrar primeiros 10
            prestacao = deb.get('PRESTACAO', 0)
            vencimento = deb.get('VENCIMENTO')
            total = deb.get('TOTAL', 0.0)
            
            # Determinar moeda baseado na data
            if vencimento:
                if vencimento < DATA_CRUZEIRO_PARA_CR:
                    moeda = "Cruzeiro (Cr$)"
                elif vencimento < DATA_CR_PARA_REAL:
                    moeda = "Cruzeiro Real"
                else:
                    moeda = "Real (R$)"
            else:
                moeda = "Desconhecida"
            
            valor_convertido = converter_para_real(total, vencimento)
            
            total_original += float(total) if total else 0
            total_convertido += valor_convertido
            
            print(f"{prestacao:<10} {str(vencimento):<12} R$ {total:>12.2f} {moeda:<15} R$ {valor_convertido:>12.2f}")
        
        if len(debitos_6080) > 10:
            # Calcular totais de todos
            for deb in debitos_6080[10:]:
                total = deb.get('TOTAL', 0.0)
                vencimento = deb.get('VENCIMENTO')
                valor_convertido = converter_para_real(total, vencimento)
                total_original += float(total) if total else 0
                total_convertido += valor_convertido
        
        print("-" * 80)
        print(f"{'TOTAL':<10} {'':<12} R$ {total_original:>12.2f} {'':<15} R$ {total_convertido:>12.2f}")
        print("\n" + "="*80)
        print(f"🔴 PROBLEMA: Sem conversão = R$ {total_original:,.2f}")
        print(f"✅ CORRETO: Com conversão = R$ {total_convertido:,.2f}")
        print(f"💰 Diferença: R$ {total_original - total_convertido:,.2f}")
        print("="*80)
        
except Exception as e:
    print(f"❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
