import os
import django
import sqlite3

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato, Mutuario

conn = sqlite3.connect('db.sqlite3')
cur = conn.cursor()

conjunto = '010'

# Contar contratos
qtd_contratos = Contrato.objects.filter(conjunto=conjunto).count()

# Contar mutuários
qtd_mutuarios = Mutuario.objects.filter(conjunto=conjunto).count()

# Verificar códigos únicos de mutuários
cur.execute("""
    SELECT COUNT(DISTINCT codigo)
    FROM principal_mutuario
    WHERE conjunto = ?
""", (conjunto,))
codigos_unicos = cur.fetchone()[0]

# Ver se há contratos com código que não têm mutuário correspondente
cur.execute("""
    SELECT COUNT(*)
    FROM principal_contrato c
    WHERE c.conjunto = ?
    AND NOT EXISTS (
        SELECT 1 FROM principal_mutuario m
        WHERE m.codigo = c.codigo AND m.conjunto = c.conjunto
    )
""", (conjunto,))
contratos_sem_mutuario = cur.fetchone()[0]

print(f"\n=== CONJUNTO {conjunto} ===")
print(f"Total de contratos: {qtd_contratos}")
print(f"Total de mutuários: {qtd_mutuarios}")
print(f"Códigos únicos de mutuários: {codigos_unicos}")
print(f"Contratos sem mutuário (código não encontrado): {contratos_sem_mutuario}")

conn.close()
