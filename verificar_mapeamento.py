import os
import django
import sqlite3

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato

conn = sqlite3.connect(r'C:\Users\fabri\cofluhab\cofluhab\db.sqlite3')
cur = conn.cursor()

conjunto = '010'

# Contar contratos
qtd_contratos = Contrato.objects.filter(conjunto=conjunto).count()

# Contar quantos contratos têm mapeamento na tabela contrato_mutuario_map
cur.execute("""
    SELECT COUNT(DISTINCT contrato_id)
    FROM contrato_mutuario_map cm
    JOIN principal_contrato c ON c.id = cm.contrato_id
    WHERE c.conjunto = ?
""", (conjunto,))
contratos_com_map = cur.fetchone()[0]

# Contar total de vínculos (pode ser maior que contratos se houver co-titulares)
cur.execute("""
    SELECT COUNT(*)
    FROM contrato_mutuario_map cm
    JOIN principal_contrato c ON c.id = cm.contrato_id
    WHERE c.conjunto = ?
""", (conjunto,))
total_vinculos = cur.fetchone()[0]

print(f"\n=== CONJUNTO {conjunto} ===")
print(f"Total de contratos: {qtd_contratos}")
print(f"Contratos com mapeamento: {contratos_com_map}")
print(f"Contratos sem mapeamento: {qtd_contratos - contratos_com_map}")
print(f"Total de vínculos na tabela: {total_vinculos}")
print(f"Média de mutuários por contrato: {total_vinculos / contratos_com_map if contratos_com_map > 0 else 0:.2f}")

conn.close()
