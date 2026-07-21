import os
import django
import sqlite3

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato, Mutuario

conn = sqlite3.connect(r'C:\Users\fabri\cofluhab\cofluhab\db.sqlite3')
cur = conn.cursor()

conjunto = '010'

print(f"\n=== ANÁLISE CONJUNTO {conjunto} ===\n")

# Buscar contratos do conjunto
contratos = Contrato.objects.filter(conjunto=conjunto)
print(f"Total de contratos: {contratos.count()}")

# Verificar quantos têm mutuário vinculado
cur.execute("""
    SELECT COUNT(DISTINCT c.id)
    FROM principal_contrato c
    JOIN contrato_mutuario_map cm ON cm.contrato_id = c.id
    WHERE c.conjunto = ?
""", (conjunto,))
contratos_com_mutuario = cur.fetchone()[0]

print(f"Contratos com mutuário vinculado: {contratos_com_mutuario}")
print(f"Contratos SEM mutuário: {contratos.count() - contratos_com_mutuario}")

# Buscar contratos sem mutuário
cur.execute("""
    SELECT c.id, c.codigo
    FROM principal_contrato c
    WHERE c.conjunto = ?
    AND NOT EXISTS (
        SELECT 1 FROM contrato_mutuario_map cm
        WHERE cm.contrato_id = c.id
    )
    LIMIT 10
""", (conjunto,))

contratos_sem_mutuario = cur.fetchall()

if contratos_sem_mutuario:
    print(f"\nPrimeiros 10 contratos SEM mutuário:")
    for contrato_id, codigo in contratos_sem_mutuario:
        print(f"  ID: {contrato_id}, Código: {codigo}")
else:
    print("\n✓ Todos os contratos têm mutuário vinculado!")

# Verificar total de mutuários únicos no conjunto
qtd_mutuarios = Mutuario.objects.filter(conjunto=conjunto).count()
print(f"\nTotal de mutuários únicos no conjunto: {qtd_mutuarios}")

conn.close()
