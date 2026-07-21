"""
Reconstrói o log de contratos com amortização negativa
Usa backup do banco antes da conversão
"""
import os
import sys
import sqlite3

print("=" * 80)
print("RECONSTRUINDO LOG DE AMORTIZAÇÃO NEGATIVA")
print("=" * 80)

# Verificar se existe backup
backup_path = 'db.sqlite3.backup-antes-conversao-20251126-005453'
if not os.path.exists(backup_path):
    print(f"\n❌ Backup não encontrado: {backup_path}")
    print("Não é possível reconstruir o log sem o backup.")
    sys.exit(1)

print(f"\n✅ Backup encontrado: {backup_path}")

# Conectar ao backup
conn_backup = sqlite3.connect(backup_path)
cur_backup = conn_backup.cursor()

# Buscar contratos com saldo negativo no backup
cur_backup.execute("""
    SELECT c.id, c.codigo, c.conjunto, p.sddev
    FROM principal_contrato c
    INNER JOIN principal_parcelacontrato p ON p.contrato_id = c.id
    WHERE p.id IN (SELECT MAX(id) FROM principal_parcelacontrato GROUP BY contrato_id)
    AND p.sddev < 0
    ORDER BY p.sddev ASC
""")

contratos_negativos = cur_backup.fetchall()
conn_backup.close()

print(f"\n📊 Encontrados {len(contratos_negativos)} contratos com saldo negativo no backup")

if len(contratos_negativos) == 0:
    print("\n⚠️  Nenhum contrato negativo encontrado no backup.")
    sys.exit(0)

# Criar tabela de log no banco atual
conn_atual = sqlite3.connect('db.sqlite3')
cursor = conn_atual.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS amort_negativa_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        contrato_id INTEGER NOT NULL,
        codigo_contrato TEXT NOT NULL,
        conjunto TEXT,
        saldo_negativo_original DECIMAL(15,2),
        saldo_convertido DECIMAL(15,2),
        data_conversao TEXT DEFAULT '2025-11-26',
        UNIQUE(contrato_id)
    )
""")

# Limpar dados antigos se existir
cursor.execute("DELETE FROM amort_negativa_log")

# Inserir dados do backup
inseridos = 0
for contrato_id, codigo, conjunto, saldo_negativo in contratos_negativos:
    saldo_positivo = abs(saldo_negativo)
    cursor.execute("""
        INSERT INTO amort_negativa_log 
        (contrato_id, codigo_contrato, conjunto, saldo_negativo_original, saldo_convertido)
        VALUES (?, ?, ?, ?, ?)
    """, (contrato_id, codigo, conjunto, saldo_negativo, saldo_positivo))
    inseridos += 1

conn_atual.commit()
print(f"\n✅ {inseridos} registros inseridos no log")

# Mostrar top 10
cursor.execute("""
    SELECT codigo_contrato, conjunto, saldo_negativo_original, saldo_convertido
    FROM amort_negativa_log
    ORDER BY saldo_negativo_original ASC
    LIMIT 10
""")

print("\nTop 10 contratos com maior saldo negativo convertido:")
print("-" * 80)
for row in cursor.fetchall():
    print(f"Contrato {row[0]} (Conjunto {row[1]}): R$ {float(row[2]):,.2f} → R$ {float(row[3]):,.2f}")

conn_atual.close()

print("\n" + "=" * 80)
print("✅ LOG RECONSTRUÍDO COM SUCESSO!")
print("=" * 80)
