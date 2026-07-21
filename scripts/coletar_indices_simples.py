# -*- coding: utf-8 -*-
"""
Script simplificado para coleta de índices do Banco Central
Versão sem emojis para compatibilidade com subprocess/Task Scheduler
"""

import os
import sys
import sqlite3
import requests
from datetime import datetime, timedelta
from decimal import Decimal
import argparse

def criar_tabela_indices():
    """Cria a tabela de índices econômicos se não existir"""
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS indices_economicos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mes_referencia TEXT UNIQUE NOT NULL,
        tr REAL,
        ipca REAL,
        inpc REAL,
        data_coleta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        fonte TEXT DEFAULT 'Banco Central do Brasil'
    )
    ''')
    
    conn.commit()
    conn.close()
    print("[OK] Tabela de indices criada/verificada")


def buscar_indice_bacen(codigo_serie, mes_referencia):
    """
    Busca índice específico no Banco Central
    
    Args:
        codigo_serie: Código da série temporal (226=TR, 433=IPCA, 188=INPC)
        mes_referencia: String no formato 'AAAA-MM'
    
    Returns:
        Decimal: Percentual do índice (ex: 0.56 para 0.56%)
    """
    try:
        # API do SGS (Sistema Gerenciador de Séries Temporais) do Bacen
        url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo_serie}/dados"
        
        # Converter mes_referencia para data inicial e final
        ano, mes = mes_referencia.split('-')
        data_inicial = f"01/{mes}/{ano}"
        
        # Último dia do mês
        if mes == '12':
            data_final = f"31/{mes}/{ano}"
        else:
            data_final = f"01/{int(mes)+1:02d}/{ano}"
        
        params = {
            'formato': 'json',
            'dataInicial': data_inicial,
            'dataFinal': data_final
        }
        
        print(f"   Consultando serie {codigo_serie}...")
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        dados = response.json()
        
        if not dados:
            print(f"   [AVISO] Nenhum dado encontrado para {mes_referencia}")
            return None
        
        # Pegar o primeiro valor (geralmente é o do mês)
        valor = dados[0]['valor']
        percentual = Decimal(valor)
        
        print(f"   [OK] Valor encontrado: {percentual:.4f}%")
        return percentual
        
    except requests.exceptions.RequestException as e:
        print(f"   [ERRO] Falha na requisicao: {e}")
        return None
    except (KeyError, ValueError, IndexError) as e:
        print(f"   [ERRO] Erro ao processar dados: {e}")
        return None


def coletar_indices_mes(mes_referencia=None):
    """
    Coleta TR, IPCA e INPC do Banco Central para um mês específico
    
    Args:
        mes_referencia: String no formato 'AAAA-MM' (se None, usa mês anterior)
    """
    criar_tabela_indices()
    
    # Se não especificado, usar mês anterior
    if mes_referencia is None:
        data_ref = datetime.now() - timedelta(days=30)
        mes_referencia = data_ref.strftime('%Y-%m')
    
    print("\n" + "="*80)
    print(f"COLETANDO INDICES DO BANCO CENTRAL")
    print(f"   Mes de Referencia: {mes_referencia}")
    print(f"   Data da Coleta: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("="*80 + "\n")
    
    # Buscar cada índice
    print("Buscando TR (Taxa Referencial)...")
    tr = buscar_indice_bacen('226', mes_referencia)
    
    print("\nBuscando IPCA (Inflacao)...")
    ipca = buscar_indice_bacen('433', mes_referencia)
    
    print("\nBuscando INPC (Inflacao Consumidor)...")
    inpc = buscar_indice_bacen('188', mes_referencia)
    
    # Salvar no banco
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
        INSERT INTO indices_economicos (mes_referencia, tr, ipca, inpc)
        VALUES (?, ?, ?, ?)
        ''', (mes_referencia, float(tr) if tr else None, 
              float(ipca) if ipca else None, 
              float(inpc) if inpc else None))
        
        conn.commit()
        print("\n" + "="*80)
        print("[OK] Indices salvos com sucesso!")
        print("="*80 + "\n")
        
    except sqlite3.IntegrityError:
        # Registro já existe, atualizar
        cursor.execute('''
        UPDATE indices_economicos 
        SET tr = ?, ipca = ?, inpc = ?, data_coleta = CURRENT_TIMESTAMP
        WHERE mes_referencia = ?
        ''', (float(tr) if tr else None, 
              float(ipca) if ipca else None, 
              float(inpc) if inpc else None,
              mes_referencia))
        
        conn.commit()
        print("\n" + "="*80)
        print("[OK] Indices atualizados com sucesso!")
        print("="*80 + "\n")
    
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description='Coletor de indices do Banco Central (versao simplificada)')
    parser.add_argument('--mes', type=str, help='Mes de referencia (AAAA-MM)')
    
    args = parser.parse_args()
    
    try:
        coletar_indices_mes(args.mes)
        sys.exit(0)
    except Exception as e:
        print(f"[ERRO] Falha na execucao: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
