#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Corrigir débitos com conversão monetária correta
Histórico de moedas no Brasil
"""

from datetime import date

# Histórico completo de conversões monetárias do Brasil
# Fonte: Banco Central do Brasil

def converter_para_real(valor, data_vencimento):
    """
    Converte valor de moeda antiga para Real baseado na data de vencimento
    
    Histórico de moedas:
    - Até 27/02/1986: Cruzeiro (Cr$)
    - 28/02/1986 a 15/01/1989: Cruzado (Cz$) - corte 3 zeros (÷1000)
    - 16/01/1989 a 15/03/1990: Cruzado Novo (NCz$) - corte 3 zeros (÷1000) 
    - 16/03/1990 a 31/07/1993: Cruzeiro (Cr$) - mantém valor
    - 01/08/1993 a 30/06/1994: Cruzeiro Real (CR$) - corte 3 zeros (÷1000)
    - A partir de 01/07/1994: Real (R$) - fator 2750 (÷2750)
    """
    if not data_vencimento or not valor:
        return 0.0
    
    try:
        valor_convertido = float(valor)
        
        # Até 27/02/1986: Cruzeiro antigo -> precisa passar por todas conversões
        if data_vencimento < date(1986, 2, 28):
            valor_convertido = valor_convertido / 1000  # Cr$ -> Cz$ (corte 3 zeros)
            valor_convertido = valor_convertido / 1000  # Cz$ -> NCz$ (corte 3 zeros)
            valor_convertido = valor_convertido / 1000  # Cr$ (novo) -> CR$ (corte 3 zeros)
            valor_convertido = valor_convertido / 2750  # CR$ -> R$ (fator 2750)
        
        # 28/02/1986 a 15/01/1989: Cruzado
        elif data_vencimento < date(1989, 1, 16):
            valor_convertido = valor_convertido / 1000  # Cz$ -> NCz$ (corte 3 zeros)
            valor_convertido = valor_convertido / 1000  # Cr$ (novo) -> CR$ (corte 3 zeros)
            valor_convertido = valor_convertido / 2750  # CR$ -> R$ (fator 2750)
        
        # 16/01/1989 a 15/03/1990: Cruzado Novo
        elif data_vencimento < date(1990, 3, 16):
            valor_convertido = valor_convertido / 1000  # Cr$ (novo) -> CR$ (corte 3 zeros)
            valor_convertido = valor_convertido / 2750  # CR$ -> R$ (fator 2750)
        
        # 16/03/1990 a 31/07/1993: Cruzeiro (retorno)
        elif data_vencimento < date(1993, 8, 1):
            valor_convertido = valor_convertido / 1000  # Cr$ -> CR$ (corte 3 zeros)
            valor_convertido = valor_convertido / 2750  # CR$ -> R$ (fator 2750)
        
        # 01/08/1993 a 30/06/1994: Cruzeiro Real
        elif data_vencimento < date(1994, 7, 1):
            valor_convertido = valor_convertido / 2750  # CR$ -> R$ (fator 2750)
        
        # A partir de 01/07/1994: já é Real
        
        return valor_convertido
    
    except:
        return 0.0

def identificar_moeda(data_vencimento):
    """Identifica qual moeda estava em vigor na data"""
    if not data_vencimento:
        return "Desconhecida"
    
    if data_vencimento < date(1986, 2, 28):
        return "Cruzeiro (Cr$)"
    elif data_vencimento < date(1989, 1, 16):
        return "Cruzado (Cz$)"
    elif data_vencimento < date(1990, 3, 16):
        return "Cruzado Novo (NCz$)"
    elif data_vencimento < date(1993, 8, 1):
        return "Cruzeiro (Cr$)"
    elif data_vencimento < date(1994, 7, 1):
        return "Cruzeiro Real (CR$)"
    else:
        return "Real (R$)"


# Teste
if __name__ == '__main__':
    from dbfread import DBF
    
    print("="*100)
    print("ANÁLISE DE CONVERSÃO MONETÁRIA - CONTRATO 6080")
    print("="*100)
    
    db = DBF('dados_antigos/DEBPREST.DBF', encoding='latin1')
    
    debitos = []
    for rec in db:
        contrato = str(rec.get('CONTRATO', '')).strip()
        if contrato in ['006080', '6080']:
            debitos.append(rec)
    
    print(f"\n✓ Encontrados {len(debitos)} débitos\n")
    
    total_original = 0.0
    total_convertido = 0.0
    
    print(f"{'Prest':<6} {'Vencimento':<12} {'Valor Original':<18} {'Moeda':<20} {'Valor em R$':<15}")
    print("-" * 100)
    
    for i, deb in enumerate(debitos):
        if i < 15 or i >= len(debitos) - 5:  # Mostrar primeiros 15 e últimos 5
            prestacao = deb.get('PRESTACAO', 0)
            vencimento = deb.get('VENCIMENTO')
            total = float(deb.get('TOTAL', 0.0))
            
            moeda = identificar_moeda(vencimento)
            valor_convertido = converter_para_real(total, vencimento)
            
            print(f"{prestacao:<6} {str(vencimento):<12} {total:>16.2f}  {moeda:<20} R$ {valor_convertido:>12.2f}")
        elif i == 15:
            print(f"{'...':<6} {'...':<12} {'...':<18} {'...':<20} {'...':<15}")
        
        total_original += float(deb.get('TOTAL', 0.0))
        total_convertido += converter_para_real(deb.get('TOTAL', 0.0), deb.get('VENCIMENTO'))
    
    print("-" * 100)
    print(f"{'TOTAL':<6} {'':<12} {total_original:>16.2f}  {'':<20} R$ {total_convertido:>12.2f}")
    
    print("\n" + "="*100)
    print(f"🔴 PROBLEMA (sem conversão): R$ {total_original:,.2f}")
    print(f"✅ CORRETO (com conversão):  R$ {total_convertido:,.2f}")
    print(f"💰 Economia na conversão:    R$ {total_original - total_convertido:,.2f}")
    print("="*100)
