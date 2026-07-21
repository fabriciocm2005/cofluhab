"""
Script para popular o campo conjunto com o número correto do arquivo Contrato.txt.
O conjunto correto está no campo 0 do arquivo (000442 = conjunto 442 = 010 em formato com zeros).

Autor: Sistema  
Data: 27/11/2025
"""

import os
import sys
import django
import sqlite3

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato

def normalizar_codigo(codigo):
    """Remove zeros à esquerda."""
    if not codigo:
        return codigo
    try:
        return str(int(codigo))
    except (ValueError, TypeError):
        return codigo

def main():
    print("=" * 80)
    print("POPULANDO CAMPO CONJUNTO COM NUMEROS CORRETOS")
    print("=" * 80)
    print()
    
    # Ler arquivo Contrato.txt
    arquivo = 'dados_antigos/acerto_cadmut/Contrato.txt'
    
    if not os.path.exists(arquivo):
        print(f"ERRO: Arquivo {arquivo} não encontrado!")
        return
    
    # Dicionário: codigo_contrato -> numero_conjunto
    mapa_conjunto = {}
    
    print("Lendo arquivo Contrato.txt...")
    with open(arquivo, 'r', encoding='latin1') as f:
        for linha_num, linha in enumerate(f, 1):
            try:
                campos = linha.strip().split('\t')
                
                if len(campos) < 2:
                    continue
                
                # Campo 0: número do conjunto (000442)
                conjunto_raw = campos[0].strip()
                conjunto = normalizar_codigo(conjunto_raw)
                
                # Campo 1: código do contrato (0000000000102)
                codigo_raw = campos[1].strip()
                codigo = normalizar_codigo(codigo_raw)
                
                if codigo and conjunto:
                    mapa_conjunto[codigo] = conjunto
                
            except Exception as e:
                print(f"Erro na linha {linha_num}: {e}")
                continue
    
    print(f"Total de contratos lidos: {len(mapa_conjunto)}")
    print()
    
    # Conectar ao banco
    db_path = os.path.join(os.path.dirname(__file__), 'db.sqlite3')
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Buscar todos os contratos do banco
    cur.execute("SELECT id, codigo, conjunto FROM principal_contrato")
    contratos_db = cur.fetchall()
    
    atualizados = 0
    nao_encontrados = 0
    ja_tinham = 0
    
    for contrato_id, codigo, conjunto_atual in contratos_db:
        # Se já tem conjunto (número), pular
        if conjunto_atual and conjunto_atual.strip() and not conjunto_atual.isalpha():
            ja_tinham += 1
            continue
        
        # Buscar no mapa
        if codigo in mapa_conjunto:
            novo_conjunto = mapa_conjunto[codigo]
            
            cur.execute("""
                UPDATE principal_contrato 
                SET conjunto = ? 
                WHERE id = ?
            """, (novo_conjunto, contrato_id))
            
            if atualizados < 10:
                print(f"  Contrato {codigo}: conjunto atualizado para '{novo_conjunto}'")
            elif atualizados == 10:
                print("  ...")
            
            atualizados += 1
        else:
            nao_encontrados += 1
            if nao_encontrados <= 5:
                print(f"  AVISO: Contrato {codigo} não encontrado no arquivo Contrato.txt")
    
    conn.commit()
    conn.close()
    
    print()
    print("=" * 80)
    print(f"Contratos atualizados: {atualizados}")
    print(f"Contratos que já tinham conjunto: {ja_tinham}")
    print(f"Contratos não encontrados no arquivo: {nao_encontrados}")
    print("=" * 80)

if __name__ == '__main__':
    main()
