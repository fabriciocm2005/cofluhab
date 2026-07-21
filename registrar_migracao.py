"""
Script para registrar a migração no banco de dados Django
"""
import sqlite3
import os
from datetime import datetime

# Caminho do banco de dados
db_path = os.path.join(os.path.dirname(__file__), 'db.sqlite3')

print(f"Registrando migração no Django...")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Inserir registro da migração
    cursor.execute("""
        INSERT INTO django_migrations (app, name, applied)
        VALUES ('principal', '0007_add_telefone_email_mutuario', ?)
    """, (datetime.now(),))
    
    conn.commit()
    print("✓ Migração registrada com sucesso!")

except sqlite3.IntegrityError:
    print("ℹ Migração já está registrada")

except sqlite3.Error as e:
    print(f"✗ Erro: {e}")
    conn.rollback()

finally:
    conn.close()
