import django
import os
import sys

sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from django.db import connection

# Calcular total atual
cursor = connection.cursor()

# Total de saldos positivos
cursor.execute("""
    SELECT 
        COUNT(DISTINCT c.id) as total_contratos,
        SUM(CASE WHEN p.sddev > 0 THEN p.sddev ELSE 0 END) as total_positivo,
        SUM(CASE WHEN p.sddev <= 0 THEN p.sddev ELSE 0 END) as total_negativo,
        SUM(p.sddev) as total_geral
    FROM principal_contrato c
    INNER JOIN principal_parcelacontrato p ON p.contrato_id = c.id
    WHERE p.id IN (
        SELECT p2.id 
        FROM principal_parcelacontrato p2 
        WHERE p2.contrato_id = c.id 
        ORDER BY p2.nmens DESC 
        LIMIT 1
    )
""")

resultado = cursor.fetchone()
total_contratos, total_positivo, total_negativo, total_geral = resultado

print("=" * 80)
print("SALDO DEVEDOR ATUAL (NOVEMBRO/2025)")
print("=" * 80)
print()
print(f"Total de contratos: {total_contratos:,}")
print()
print(f"Saldos positivos: R$ {float(total_positivo):,.2f}")
print(f"Saldos negativos: R$ {float(total_negativo):,.2f}")
print(f"Total geral: R$ {float(total_geral):,.2f}")
print()

# Verificar quantos têm sddev_original (foram convertidos)
cursor.execute("""
    SELECT COUNT(*) 
    FROM principal_parcelacontrato 
    WHERE sddev_original IS NOT NULL
""")

convertidos = cursor.fetchone()[0]
print(f"Contratos convertidos de moeda antiga: {convertidos}")
print()
print("=" * 80)
