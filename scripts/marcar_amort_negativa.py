"""
Marca contratos que tiveram saldo negativo convertido
Cria uma tabela de log para rastreamento
"""
import django
import os
import sys

sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from django.db import connection

print("=" * 80)
print("MARCANDO CONTRATOS COM AMORTIZAÇÃO NEGATIVA CORRIGIDA")
print("=" * 80)

with connection.cursor() as cursor:
    # Criar tabela de log se não existir
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS amort_negativa_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contrato_id INTEGER NOT NULL,
            codigo_contrato TEXT NOT NULL,
            conjunto TEXT,
            saldo_negativo_original DECIMAL(15,2),
            saldo_convertido DECIMAL(15,2),
            data_conversao TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (contrato_id) REFERENCES principal_contrato(id)
        )
    """)
    
    # Verificar se já tem dados
    cursor.execute("SELECT COUNT(*) FROM amort_negativa_log")
    total_log = cursor.fetchone()[0]
    
    if total_log > 0:
        print(f"\n✅ Tabela já possui {total_log} registros")
        print("\nPrimeiros 10 registros:")
        cursor.execute("""
            SELECT codigo_contrato, conjunto, saldo_negativo_original, saldo_convertido
            FROM amort_negativa_log
            ORDER BY saldo_negativo_original ASC
            LIMIT 10
        """)
        for row in cursor.fetchall():
            print(f"Contrato {row[0]} (Conjunto {row[1]}): R$ {float(row[2]):,.2f} → R$ {float(row[3]):,.2f}")
    else:
        print("\n⚠️  Tabela vazia. Execute este script ANTES de aplicar a correção ABS.")
        print("Ou execute o script de reconstrução do log.")

print("\n" + "=" * 80)
