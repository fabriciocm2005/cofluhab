"""
Script para reverter a normalização e fazer backup antes de mexer
"""
import os
import shutil
from datetime import datetime

# Fazer backup do banco
db_file = 'db.sqlite3'
timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
backup_file = f'db.sqlite3.bak-normalização-{timestamp}'

print("=" * 80)
print("CRIANDO BACKUP DO BANCO DE DADOS")
print("=" * 80)

shutil.copy2(db_file, backup_file)
print(f"✅ Backup criado: {backup_file}")
print("=" * 80)
