"""
Restaura campo conjunto dos contratos a partir do backup
"""
import sqlite3

print("=" * 80)
print("RESTAURANDO CAMPO CONJUNTO DO BACKUP")
print("=" * 80)

# Conectar ao backup
backup_path = 'db.sqlite3.backup-antes-conversao-20251126-005453'
conn_backup = sqlite3.connect(backup_path)
cur_backup = conn_backup.cursor()

# Buscar todos os conjuntos do backup
cur_backup.execute("""
    SELECT codigo, conjunto
    FROM principal_contrato
    WHERE conjunto IS NOT NULL AND conjunto != ''
""")

mapeamento = {}
for codigo, conjunto in cur_backup.fetchall():
    # Normalizar código removendo zeros à esquerda
    codigo_normalizado = str(int(codigo)) if codigo.isdigit() else codigo
    mapeamento[codigo_normalizado] = conjunto

conn_backup.close()

print(f"\n✅ Encontrados {len(mapeamento)} contratos com conjunto no backup")

# Mostrar amostra
print("\nAmostra dos primeiros 10:")
for i, (codigo, conjunto) in enumerate(list(mapeamento.items())[:10]):
    print(f"  {codigo} -> {conjunto}")

# Aplicar no banco atual
conn = sqlite3.connect('db.sqlite3')
cur = conn.cursor()

atualizados = 0
for codigo, conjunto in mapeamento.items():
    cur.execute("""
        UPDATE principal_contrato
        SET conjunto = ?
        WHERE codigo = ?
    """, (conjunto, codigo))
    if cur.rowcount > 0:
        atualizados += 1

conn.commit()

print(f"\n✅ {atualizados} contratos atualizados com sucesso!")

# Verificar distribuição
cur.execute("""
    SELECT conjunto, COUNT(*) as qtd
    FROM principal_contrato
    WHERE conjunto != ''
    GROUP BY conjunto
    ORDER BY conjunto
""")

print("\nDistribuição por conjunto:")
total = 0
for conjunto, qtd in cur.fetchall():
    print(f"  {conjunto}: {qtd} contratos")
    total += qtd

print(f"\nTotal com conjunto: {total}")

cur.execute("SELECT COUNT(*) FROM principal_contrato WHERE conjunto = ''")
vazios = cur.fetchone()[0]
print(f"Contratos sem conjunto: {vazios}")

conn.close()

print("\n" + "=" * 80)
print("✅ RESTAURAÇÃO CONCLUÍDA!")
print("=" * 80)
