# -*- coding: utf-8 -*-
"""
Atualização Monetária desde Maio/2019
Considera que todos os saldos no banco são de maio/2019
e aplica correção até novembro/2025
"""

import django
import os
import sys
from datetime import date
from decimal import Decimal
import requests

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato, ParcelaContrato


def coletar_indices_ipca():
    """Coleta IPCA de maio/2019 até novembro/2025"""
    print("Coletando índices IPCA do Banco Central...")
    
    url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados"
    params = {
        'formato': 'json',
        'dataInicial': '01/05/2019',
        'dataFinal': '30/11/2025'
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        dados = response.json()
        
        indices = {}
        for item in dados:
            data_str = item['data']  # "01/06/2019"
            valor = Decimal(item['valor'])
            dia, mes, ano = data_str.split('/')
            mes_ref = f"{ano}-{mes}"
            indices[mes_ref] = valor
        
        print(f"[OK] {len(indices)} índices coletados\n")
        return indices
        
    except Exception as e:
        print(f"[ERRO] Falha ao coletar índices: {e}")
        return {}


def calcular_fator_acumulado(indices):
    """Calcula fator de correção acumulado"""
    fator = Decimal('1.0')
    
    for mes, percentual in sorted(indices.items()):
        fator_mes = Decimal('1.0') + (percentual / Decimal('100'))
        fator = fator * fator_mes
    
    return fator


def atualizar_desde_maio_2019(modo='simulacao'):
    """
    Atualiza todos os saldos desde maio/2019
    Considera que os valores no banco são de maio/2019
    """
    print("\n" + "="*80)
    print(f"{'SIMULACAO' if modo == 'simulacao' else 'APLICANDO'} - ATUALIZACAO DESDE MAIO/2019")
    print("="*80 + "\n")
    
    # 1. Coletar índices
    indices = coletar_indices_ipca()
    
    if not indices:
        print("[ERRO] Não foi possível coletar índices. Abortando.")
        return
    
    # 2. Calcular fator acumulado
    fator = calcular_fator_acumulado(indices)
    percentual_total = (fator - Decimal('1.0')) * Decimal('100')
    
    print("="*80)
    print("FATOR DE CORRECAO (MAIO/2019 a NOVEMBRO/2025)")
    print("="*80)
    print(f"  Meses: {len(indices)}")
    print(f"  Fator acumulado: {fator:.6f}")
    print(f"  Percentual total: {percentual_total:.2f}%")
    print("="*80 + "\n")
    
    # 3. Aplicar nos contratos
    total_contratos = 0
    total_com_saldo = 0
    saldo_total_maio_2019 = Decimal('0')
    saldo_total_nov_2025 = Decimal('0')
    
    exemplos = []
    
    for contrato in Contrato.objects.all():
        total_contratos += 1
        
        # Pegar última parcela (assume que é saldo de maio/2019)
        ultima_parcela = ParcelaContrato.objects.filter(
            contrato=contrato
        ).order_by('-nmens').first()
        
        if not ultima_parcela or not ultima_parcela.sddev:
            continue
        
        saldo_maio_2019 = ultima_parcela.sddev
        saldo_nov_2025 = saldo_maio_2019 * fator
        correcao = saldo_nov_2025 - saldo_maio_2019
        
        saldo_total_maio_2019 += saldo_maio_2019
        saldo_total_nov_2025 += saldo_nov_2025
        total_com_saldo += 1
        
        if len(exemplos) < 10:
            exemplos.append({
                'contrato': contrato.codigo,
                'saldo_maio_2019': saldo_maio_2019,
                'correcao': correcao,
                'saldo_nov_2025': saldo_nov_2025
            })
        
        if modo == 'aplicar':
            # Atualizar saldo
            ultima_parcela.sddev = saldo_nov_2025
            ultima_parcela.save()
    
    # 4. Mostrar resultados
    print("EXEMPLOS DE ATUALIZACAO:")
    print("-" * 80)
    for ex in exemplos:
        print(f"\nContrato {ex['contrato']}:")
        print(f"  Saldo em MAI/2019: R$ {ex['saldo_maio_2019']:,.2f}")
        print(f"  Correção aplicada: R$ {ex['correcao']:,.2f}")
        print(f"  Saldo em NOV/2025: R$ {ex['saldo_nov_2025']:,.2f}")
    
    print("\n" + "="*80)
    print("RESUMO FINAL")
    print("="*80)
    print(f"Total de Contratos: {total_contratos}")
    print(f"Contratos com saldo: {total_com_saldo}")
    print(f"\nSaldo Total em MAI/2019: R$ {saldo_total_maio_2019:,.2f}")
    print(f"Correção Total Aplicada: R$ {saldo_total_nov_2025 - saldo_total_maio_2019:,.2f}")
    print(f"Saldo Total em NOV/2025: R$ {saldo_total_nov_2025:,.2f}")
    print(f"\nPercentual de correção: {percentual_total:.2f}%")
    print("="*80 + "\n")
    
    if modo == 'aplicar':
        print("[OK] ATUALIZACAO APLICADA COM SUCESSO!")
    else:
        print("[AVISO] MODO SIMULACAO - Nenhuma alteracao foi salva")
        print("        Para aplicar, execute com --aplicar")
    
    print("\n" + "="*80 + "\n")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Atualizar saldos desde maio/2019'
    )
    parser.add_argument(
        '--aplicar',
        action='store_true',
        help='Aplicar atualizacao (padrao: simulacao)'
    )
    
    args = parser.parse_args()
    
    modo = 'aplicar' if args.aplicar else 'simulacao'
    
    if modo == 'aplicar':
        print("\n" + "="*80)
        print("ATENCAO: ATUALIZACAO MONETARIA!")
        print("="*80)
        print("   Esta operacao ira atualizar TODOS os saldos devedores")
        print("   considerando:")
        print("   - Saldos atuais = Maio/2019")
        print("   - Correcao: Maio/2019 ate Novembro/2025")
        print("   - Indice: IPCA acumulado")
        print("   ")
        print("   [!] RECOMENDACAO: Faca backup do banco antes!")
        print("   ")
        print("   Comando de backup:")
        print("   copy db.sqlite3 db.sqlite3.backup-antes-atualizacao-2019")
        print("="*80 + "\n")
        
        resposta = input("Deseja continuar? (digite 'SIM' para confirmar): ")
        
        if resposta.upper() != 'SIM':
            print("\n[CANCELADO] Operacao cancelada pelo usuario.")
            return
    
    try:
        atualizar_desde_maio_2019(modo)
    except Exception as e:
        print(f"\n[ERRO] Falha na execucao: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
