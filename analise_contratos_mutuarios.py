import os
import django
import sqlite3

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import ConjuntoHabitacional, Contrato, Mutuario

conn = sqlite3.connect(r'C:\Users\fabri\cofluhab\cofluhab\db.sqlite3')
cur = conn.cursor()

print("\n=== ANÁLISE CONTRATOS vs MUTUÁRIOS ===\n")

for conj in ConjuntoHabitacional.objects.all().order_by('conjunto'):
    qtd_contratos = Contrato.objects.filter(conjunto=conj.conjunto).count()
    qtd_mutuarios = Mutuario.objects.filter(conjunto=conj.conjunto).count()
    
    # Verificar quantos contratos têm vínculo na contrato_mutuario_map
    cur.execute("""
        SELECT COUNT(DISTINCT c.id)
        FROM principal_contrato c
        WHERE c.conjunto = ?
        AND EXISTS (
            SELECT 1 FROM contrato_mutuario_map cm
            WHERE cm.contrato_id = c.id
        )
    """, (conj.conjunto,))
    contratos_com_vinculo = cur.fetchone()[0]
    
    diferenca = qtd_contratos - qtd_mutuarios
    
    print(f"Conjunto {conj.conjunto} - {conj.nome}")
    print(f"  Contratos: {qtd_contratos}")
    print(f"  Mutuários: {qtd_mutuarios}")
    print(f"  Contratos com vínculo: {contratos_com_vinculo}")
    print(f"  Diferença: {diferenca}")
    if diferenca > 0:
        print(f"  ⚠️ Faltam {diferenca} mutuários!")
    print()

conn.close()
