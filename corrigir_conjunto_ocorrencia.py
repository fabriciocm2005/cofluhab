"""
Script para corrigir campos conjunto e ocorrencia.
- Move siglas (TPZ, SET, SIT, LA2, LA3, etc.) de conjunto para ocorrencia
- Deixa conjunto vazio para ser preenchido posteriormente

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

# Lista de siglas conhecidas que são ocorrências, não números de conjunto
SIGLAS_OCORRENCIA = [
    'TPZ', 'SET', 'SIT', 'LA2', 'LA3', 'PXN', 'LIQ', 
    'LA1', 'LA4', 'LA5', 'LA6', 'LA7', 'LA8', 'LA9'
]

def main():
    print("=" * 80)
    print("CORRECAO DE CAMPOS CONJUNTO E OCORRENCIA")
    print("=" * 80)
    print()
    
    # Conectar ao banco
    db_path = os.path.join(os.path.dirname(__file__), 'db.sqlite3')
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Buscar todos os contratos que têm conjunto preenchido
    cur.execute("SELECT id, codigo, conjunto FROM principal_contrato WHERE conjunto != ''")
    contratos = cur.fetchall()
    
    print(f"Total de contratos com conjunto preenchido: {len(contratos)}")
    print()
    
    corrigidos = 0
    
    for contrato_id, codigo, conjunto in contratos:
        conjunto_upper = conjunto.upper().strip()
        
        # Se o conjunto é uma sigla de ocorrência
        if conjunto_upper in SIGLAS_OCORRENCIA:
            # Mover para ocorrencia e limpar conjunto
            cur.execute("""
                UPDATE principal_contrato 
                SET ocorrencia = ?, conjunto = '' 
                WHERE id = ?
            """, (conjunto_upper, contrato_id))
            
            if corrigidos < 10:  # Mostrar apenas os primeiros 10
                print(f"  Contrato {codigo}: conjunto '{conjunto}' -> ocorrencia '{conjunto_upper}'")
            elif corrigidos == 10:
                print("  ...")
            
            corrigidos += 1
        else:
            # É um número de conjunto válido, manter como está
            # Mas limpar ocorrencia se estiver vazia
            if corrigidos < 5:
                print(f"  Contrato {codigo}: mantendo conjunto '{conjunto}'")
    
    conn.commit()
    conn.close()
    
    print()
    print("=" * 80)
    print(f"Total de contratos corrigidos: {corrigidos}")
    print("=" * 80)

if __name__ == '__main__':
    main()
