#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Aplica mapeamentos de alta confiança (score >= 0.9) à tabela de mapeamento
"""
import os
import sys
import csv
import sqlite3

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(project_root, 'db.sqlite3')
csv_path = os.path.join(project_root, 'exports', 'contrato_mutuario_map_v2.csv')

def main():
    print("=== Aplicando Mapeamentos V2 (High Confidence) ===")
    
    # Ler CSV
    print(f"Lendo {csv_path}...")
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # Filtrar high confidence (score >= 0.9)
    high_conf = [r for r in rows if r['mutuario_id'] and float(r['score']) >= 0.9]
    print(f"  Total rows: {len(rows)}")
    print(f"  High confidence (≥0.9): {len(high_conf)}")
    
    # Conectar DB
    print("Conectando ao banco de dados...")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Verificar se tabela existe
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='contrato_mutuario_map'")
    if not cur.fetchone():
        print("Criando tabela contrato_mutuario_map...")
        cur.execute("""
            CREATE TABLE contrato_mutuario_map (
                contrato_id INTEGER PRIMARY KEY,
                mutuario_id INTEGER NOT NULL,
                score REAL NOT NULL,
                method TEXT NOT NULL
            )
        """)
    else:
        # Limpar tabela existente
        print("Limpando dados antigos...")
        cur.execute("DELETE FROM contrato_mutuario_map")
    
    # Inserir high confidence mappings
    print(f"Inserindo {len(high_conf)} mapeamentos de alta confiança...")
    for row in high_conf:
        cur.execute("""
            INSERT INTO contrato_mutuario_map (contrato_id, mutuario_id, score, method)
            VALUES (?, ?, ?, ?)
        """, (
            int(row['contrato_id']),
            int(row['mutuario_id']),
            float(row['score']),
            row['method']
        ))
    
    conn.commit()
    
    # Verificar
    cur.execute("SELECT COUNT(*) FROM contrato_mutuario_map")
    count = cur.fetchone()[0]
    print(f"\n✓ {count} mapeamentos inseridos com sucesso!")
    
    # Estatísticas
    cur.execute("""
        SELECT method, COUNT(*), AVG(score)
        FROM contrato_mutuario_map
        GROUP BY method
    """)
    print("\nDistribuição por método:")
    for method, count, avg_score in cur.fetchall():
        print(f"  {method}: {count} ({avg_score:.3f} avg score)")
    
    # Sample
    print("\nAmostra (5 primeiros):")
    cur.execute("SELECT * FROM contrato_mutuario_map LIMIT 5")
    for row in cur.fetchall():
        print(f"  contrato={row[0]} → mutuario={row[1]} (score={row[2]}, {row[3]})")
    
    conn.close()
    print("\n✓ Concluído!")

if __name__ == '__main__':
    main()
