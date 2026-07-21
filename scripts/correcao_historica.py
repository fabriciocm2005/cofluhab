# -*- coding: utf-8 -*-
"""
Script para Correção Monetária Histórica
Atualiza saldos devedores desde maio/2019 até novembro/2025
"""

import os
import sys
import django
import sqlite3
from decimal import Decimal
from datetime import datetime
import requests

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato, ParcelaContrato


def coletar_indices_historicos(data_inicial='2019-05', data_final='2025-11'):
    """
    Coleta índices IPCA do Banco Central desde data_inicial até data_final
    
    Args:
        data_inicial: String no formato 'AAAA-MM'
        data_final: String no formato 'AAAA-MM'
    
    Returns:
        dict: {mes: percentual_ipca}
    """
    print("\n" + "="*80)
    print("COLETANDO INDICES HISTORICOS DO BANCO CENTRAL")
    print(f"   Periodo: {data_inicial} ate {data_final}")
    print("="*80 + "\n")
    
    # Converter datas
    ano_ini, mes_ini = map(int, data_inicial.split('-'))
    ano_fim, mes_fim = map(int, data_final.split('-'))
    
    # Construir data para API
    data_ini_api = f"01/{mes_ini:02d}/{ano_ini}"
    data_fim_api = f"30/{mes_fim:02d}/{ano_fim}"
    
    # API do Banco Central - Série 433 (IPCA)
    url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados"
    params = {
        'formato': 'json',
        'dataInicial': data_ini_api,
        'dataFinal': data_fim_api
    }
    
    print(f"Buscando IPCA na API do Banco Central...")
    print(f"URL: {url}")
    print(f"Periodo: {data_ini_api} a {data_fim_api}\n")
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        dados = response.json()
        
        # Organizar por mês
        indices = {}
        for item in dados:
            data_str = item['data']  # "01/06/2019"
            valor = Decimal(item['valor'])
            
            # Extrair ano-mes
            dia, mes, ano = data_str.split('/')
            mes_ref = f"{ano}-{mes}"
            
            indices[mes_ref] = valor
        
        print(f"[OK] {len(indices)} indices coletados com sucesso!\n")
        
        # Mostrar alguns exemplos
        print("Primeiros 5 indices:")
        for i, (mes, valor) in enumerate(list(indices.items())[:5]):
            print(f"   {mes}: {valor:.4f}%")
        print("   ...")
        print("Ultimos 5 indices:")
        for mes, valor in list(indices.items())[-5:]:
            print(f"   {mes}: {valor:.4f}%")
        print()
        
        return indices
        
    except Exception as e:
        print(f"[ERRO] Falha ao coletar indices: {e}")
        return {}


def calcular_correcao_acumulada(indices):
    """
    Calcula o fator de correção acumulado
    
    Args:
        indices: dict {mes: percentual}
    
    Returns:
        Decimal: Fator multiplicador acumulado (ex: 1.35 = 35% de correção total)
    """
    fator = Decimal('1.0')
    
    for mes, percentual in sorted(indices.items()):
        # Converter percentual para fator (0.39% -> 1.0039)
        fator_mes = Decimal('1.0') + (percentual / Decimal('100'))
        fator = fator * fator_mes
    
    return fator


def aplicar_correcao_historica(modo='simulacao'):
    """
    Aplica correção acumulada nos saldos devedores
    
    Args:
        modo: 'simulacao' ou 'aplicar'
    """
    print("\n" + "="*80)
    print(f"{'SIMULACAO DE' if modo == 'simulacao' else 'APLICANDO'} CORRECAO HISTORICA")
    print(f"   Periodo: MAIO/2019 ate NOVEMBRO/2025")
    print("="*80 + "\n")
    
    # 1. Coletar índices históricos
    indices = coletar_indices_historicos('2019-05', '2025-11')
    
    if not indices:
        print("[ERRO] Nao foi possivel coletar indices. Abortando.")
        return
    
    # 2. Calcular fator acumulado
    fator = calcular_correcao_acumulada(indices)
    percentual_total = (fator - Decimal('1.0')) * Decimal('100')
    
    print("="*80)
    print(f"FATOR DE CORRECAO ACUMULADA")
    print(f"   Total de meses: {len(indices)}")
    print(f"   Fator acumulado: {fator:.6f}")
    print(f"   Percentual total: {percentual_total:.2f}%")
    print("="*80 + "\n")
    
    # 3. Aplicar nos contratos
    contratos = Contrato.objects.all()
    total_contratos = 0
    total_parcelas = 0
    valor_total_antes = Decimal('0')
    valor_total_depois = Decimal('0')
    
    print(f"Processando {contratos.count()} contratos...\n")
    
    for contrato in contratos:
        # Pegar última parcela (saldo mais recente)
        ultima_parcela = ParcelaContrato.objects.filter(
            contrato=contrato
        ).order_by('-nmens').first()
        
        if not ultima_parcela or not ultima_parcela.sddev:
            continue
        
        saldo_atual = ultima_parcela.sddev
        saldo_corrigido = saldo_atual * fator
        correcao = saldo_corrigido - saldo_atual
        
        valor_total_antes += saldo_atual
        valor_total_depois += saldo_corrigido
        
        if modo == 'aplicar':
            # Atualizar saldo
            ultima_parcela.sddev = saldo_corrigido
            ultima_parcela.save()
        
        total_contratos += 1
        total_parcelas += 1
        
        # Mostrar primeiros 10 exemplos
        if total_contratos <= 10:
            print(f"  Contrato {contrato.codigo}:")
            print(f"    Saldo em MAI/2019: R$ {saldo_atual:,.2f}")
            print(f"    Correcao aplicada: R$ {correcao:,.2f}")
            print(f"    Saldo em NOV/2025: R$ {saldo_corrigido:,.2f}")
            print()
    
    # 4. Resumo
    correcao_total = valor_total_depois - valor_total_antes
    
    print("\n" + "="*80)
    print("RESUMO DA CORRECAO HISTORICA")
    print("="*80)
    print(f"   Periodo: MAIO/2019 a NOVEMBRO/2025")
    print(f"   Meses corrigidos: {len(indices)}")
    print(f"   Fator acumulado: {fator:.6f} ({percentual_total:.2f}%)")
    print(f"   Total de Contratos: {total_contratos}")
    print(f"   Total de Parcelas: {total_parcelas}")
    print(f"   Saldo Total ANTES: R$ {valor_total_antes:,.2f}")
    print(f"   Saldo Total DEPOIS: R$ {valor_total_depois:,.2f}")
    print(f"   Correcao Total: R$ {correcao_total:,.2f}")
    print("="*80 + "\n")
    
    if modo == 'aplicar':
        # Registrar no histórico
        registrar_correcao_historica(
            len(indices),
            float(fator),
            float(percentual_total),
            total_contratos,
            float(valor_total_antes),
            float(valor_total_depois),
            float(correcao_total)
        )
        print("[OK] CORRECAO APLICADA COM SUCESSO!")
        print("[OK] Historico registrado no banco de dados")
    else:
        print("[AVISO] MODO SIMULACAO - Nenhuma alteracao foi salva")
        print("        Para aplicar, execute: py scripts/correcao_historica.py --aplicar")
    
    print("\n" + "="*80 + "\n")
    
    # Retornar estatísticas
    return {
        'fator': float(fator),
        'percentual': float(percentual_total),
        'contratos': total_contratos,
        'saldo_antes': float(valor_total_antes),
        'saldo_depois': float(valor_total_depois),
        'correcao': float(correcao_total)
    }


def registrar_correcao_historica(meses, fator, percentual, contratos, 
                                  saldo_antes, saldo_depois, correcao):
    """Registra a correção histórica no banco"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db.sqlite3')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Verificar se tabela existe
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='atualizacao_monetaria_historico'
    """)
    
    if not cursor.fetchone():
        print("[AVISO] Tabela de historico nao existe. Criando...")
        cursor.execute("""
            CREATE TABLE atualizacao_monetaria_historico (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                mes_referencia TEXT NOT NULL,
                indice_aplicado REAL NOT NULL,
                total_contratos INTEGER,
                total_parcelas_atualizadas INTEGER,
                valor_total_corrigido REAL
            )
        """)
    
    # Inserir registro especial para correção histórica
    cursor.execute("""
        INSERT INTO atualizacao_monetaria_historico 
        (mes_referencia, indice_aplicado, total_contratos, 
         total_parcelas_atualizadas, valor_total_corrigido)
        VALUES (?, ?, ?, ?, ?)
    """, (
        'CORRECAO_HISTORICA_2019-05_a_2025-11',
        percentual,
        contratos,
        contratos,
        correcao
    ))
    
    conn.commit()
    conn.close()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Correcao Monetaria Historica (MAIO/2019 a NOVEMBRO/2025)'
    )
    parser.add_argument(
        '--aplicar',
        action='store_true',
        help='Aplicar correcao (padrao: simulacao)'
    )
    
    args = parser.parse_args()
    
    modo = 'aplicar' if args.aplicar else 'simulacao'
    
    if modo == 'aplicar':
        print("\n" + "="*80)
        print("ATENCAO: VOCE ESTA PRESTES A APLICAR CORRECAO HISTORICA!")
        print("="*80)
        print("   Esta operacao ira modificar TODOS os saldos devedores")
        print("   do periodo MAIO/2019 ate NOVEMBRO/2025")
        print("   ")
        print("   [!] RECOMENDACAO: Faca backup do banco antes!")
        print("   ")
        print("   Comando de backup:")
        print("   copy db.sqlite3 db.sqlite3.backup-correcao-historica")
        print("="*80 + "\n")
        
        resposta = input("Deseja continuar? (digite 'SIM' para confirmar): ")
        
        if resposta.upper() != 'SIM':
            print("\n[CANCELADO] Operacao cancelada pelo usuario.")
            return
    
    try:
        aplicar_correcao_historica(modo)
    except Exception as e:
        print(f"\n[ERRO] Falha na execucao: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
