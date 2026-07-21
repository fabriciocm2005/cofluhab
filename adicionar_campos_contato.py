"""
Script para adicionar campos telefone e email à tabela principal_mutuario
"""
import sqlite3
import os

# Caminho do banco de dados
db_path = os.path.join(os.path.dirname(__file__), 'db.sqlite3')

print(f"Conectando ao banco de dados: {db_path}")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Verificar se as colunas já existem
    cursor.execute("PRAGMA table_info(principal_mutuario)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'telefone' not in columns:
        print("Adicionando coluna 'telefone'...")
        cursor.execute("ALTER TABLE principal_mutuario ADD COLUMN telefone VARCHAR(20) DEFAULT ''")
        print("✓ Coluna 'telefone' adicionada com sucesso!")
    else:
        print("ℹ Coluna 'telefone' já existe")
    
    if 'email' not in columns:
        print("Adicionando coluna 'email'...")
        cursor.execute("ALTER TABLE principal_mutuario ADD COLUMN email VARCHAR(100) DEFAULT ''")
        print("✓ Coluna 'email' adicionada com sucesso!")
    else:
        print("ℹ Coluna 'email' já existe")
    
    # Confirmar alterações
    conn.commit()
    print("\n✓ Migração concluída com sucesso!")
    
    # Verificar as colunas finais
    cursor.execute("PRAGMA table_info(principal_mutuario)")
    columns = cursor.fetchall()
    print(f"\nColunas da tabela principal_mutuario ({len(columns)} total):")
    for col in columns[-5:]:  # Mostrar últimas 5 colunas
        print(f"  - {col[1]} ({col[2]})")

except sqlite3.Error as e:
    print(f"✗ Erro ao executar migração: {e}")
    conn.rollback()

finally:
    conn.close()
    print("\nConexão fechada.")
