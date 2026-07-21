# -*- coding: utf-8 -*-
"""
Script para Converter Valores Históricos para Real
Corrige todos os saldos devedores considerando a moeda da época
"""

import django
import os
import sys
from datetime import datetime, date
from decimal import Decimal

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato, ParcelaContrato


def converter_para_real(valor, data_referencia):
    """Converte valor histórico para Real considerando mudanças de moeda"""
    if isinstance(data_referencia, str):
        data_referencia = datetime.strptime(data_referencia, '%d/%m/%Y').date()
    elif isinstance(data_referencia, datetime):
        data_referencia = data_referencia.date()
    
    # Fatores de conversão acumulados
    fator = Decimal('1.0')
    
    # 1994-07-01: Cruzeiro Real -> Real (divide por 2.750)
    if data_referencia < date(1994, 7, 1):
        fator = fator / Decimal('2750')
    
    # 1993-08-01: Cruzeiro -> Cruzeiro Real (divide por 1.000)
    if data_referencia < date(1993, 8, 1):
        fator = fator / Decimal('1000')
    
    # 1989-01-16: Cruzado -> Cruzado Novo (divide por 1.000)
    if data_referencia < date(1989, 1, 16):
        fator = fator / Decimal('1000')
    
    # 1986-02-28: Cruzeiro -> Cruzado (divide por 1.000)
    if data_referencia < date(1986, 2, 28):
        fator = fator / Decimal('1000')
    
    # 1967-02-13: Cruzeiro -> Cruzeiro Novo (divide por 1.000)
    if data_referencia < date(1967, 2, 13):
        fator = fator / Decimal('1000')
    
    return valor * fator


def corrigir_saldos_monetarios(modo='simulacao'):
    """
    Corrige todos os saldos das parcelas para Real
    
    Args:
        modo: 'simulacao' ou 'aplicar'
    """
    print("\n" + "="*80)
    print(f"{'SIMULACAO DE' if modo == 'simulacao' else 'APLICANDO'} CONVERSAO MONETARIA")
    print("="*80 + "\n")
    
    total_contratos = 0
    total_parcelas = 0
    total_parcelas_modificadas = 0
    
    exemplos = []
    
    for contrato in Contrato.objects.all():
        parcelas = ParcelaContrato.objects.filter(contrato=contrato)
        
        if not parcelas.exists():
            continue
        
        total_contratos += 1
        parcelas_modificadas_contrato = 0
        
        for parcela in parcelas:
            total_parcelas += 1
            
            if not parcela.sddev or not parcela.dtvenc:
                continue
            
            # Verificar se já está em Real (data >= 01/07/1994)
            if parcela.dtvenc >= date(1994, 7, 1):
                # Já está em Real, não precisa converter
                continue
            
            saldo_original = parcela.sddev
            saldo_convertido = converter_para_real(saldo_original, parcela.dtvenc)
            
            # Se a conversão mudou significativamente (mais de 10 reais de diferença)
            if abs(saldo_convertido - saldo_original) > Decimal('10'):
                if modo == 'aplicar':
                    parcela.sddev = saldo_convertido
                    parcela.conversor = float(saldo_convertido / saldo_original) if saldo_original != 0 else 1.0
                    parcela.save()
                
                total_parcelas_modificadas += 1
                parcelas_modificadas_contrato += 1
                
                # Guardar exemplos
                if len(exemplos) < 10:
                    exemplos.append({
                        'contrato': contrato.codigo,
                        'parcela': parcela.nmens,
                        'data': parcela.dtvenc,
                        'saldo_antes': saldo_original,
                        'saldo_depois': saldo_convertido
                    })
        
        if parcelas_modificadas_contrato > 0 and total_contratos <= 5:
            print(f"Contrato {contrato.codigo}: {parcelas_modificadas_contrato} parcelas convertidas")
    
    print("\n" + "="*80)
    print("EXEMPLOS DE CONVERSAO")
    print("="*80 + "\n")
    
    for ex in exemplos:
        print(f"Contrato {ex['contrato']} - Parcela {ex['parcela']} ({ex['data']}):")
        print(f"  ANTES: {ex['saldo_antes']:,.2f}")
        print(f"  DEPOIS: R$ {ex['saldo_depois']:,.2f}")
        print()
    
    print("="*80)
    print("RESUMO")
    print("="*80)
    print(f"Total de Contratos: {total_contratos}")
    print(f"Total de Parcelas: {total_parcelas}")
    print(f"Parcelas Modificadas: {total_parcelas_modificadas}")
    print("="*80 + "\n")
    
    if modo == 'aplicar':
        print("[OK] CONVERSAO APLICADA COM SUCESSO!")
    else:
        print("[AVISO] MODO SIMULACAO - Nenhuma alteracao foi salva")
        print("        Para aplicar, execute: py scripts/converter_moedas.py --aplicar")
    
    print("\n" + "="*80 + "\n")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Converter valores historicos para Real'
    )
    parser.add_argument(
        '--aplicar',
        action='store_true',
        help='Aplicar conversao (padrao: simulacao)'
    )
    
    args = parser.parse_args()
    
    modo = 'aplicar' if args.aplicar else 'simulacao'
    
    if modo == 'aplicar':
        print("\n" + "="*80)
        print("ATENCAO: CONVERSAO MONETARIA!")
        print("="*80)
        print("   Esta operacao ira converter TODOS os saldos")
        print("   de moedas antigas (Cruzeiro, Cruzado, etc) para Real")
        print("   ")
        print("   [!] RECOMENDACAO: Faca backup do banco antes!")
        print("   ")
        print("   Comando de backup:")
        print("   copy db.sqlite3 db.sqlite3.backup-antes-conversao")
        print("="*80 + "\n")
        
        resposta = input("Deseja continuar? (digite 'SIM' para confirmar): ")
        
        if resposta.upper() != 'SIM':
            print("\n[CANCELADO] Operacao cancelada pelo usuario.")
            return
    
    try:
        corrigir_saldos_monetarios(modo)
    except Exception as e:
        print(f"\n[ERRO] Falha na execucao: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
