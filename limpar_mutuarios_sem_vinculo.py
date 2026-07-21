import os
import django
import sqlite3

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Mutuario

conn = sqlite3.connect(r'C:\Users\fabri\cofluhab\cofluhab\db.sqlite3')
cur = conn.cursor()

print("\n=== LIMPANDO MUTUÁRIOS SEM VÍNCULO COM CONTRATOS ===\n")

# Contar total antes
total_antes = Mutuario.objects.count()
print(f"Total de mutuários antes: {total_antes}")

# Buscar mutuários que NÃO estão vinculados a nenhum contrato
cur.execute("""
    SELECT id FROM principal_mutuario
    WHERE id NOT IN (
        SELECT DISTINCT mutuario_id FROM contrato_mutuario_map
    )
""")

ids_sem_vinculo = [row[0] for row in cur.fetchall()]
print(f"Mutuários SEM vínculo com contratos: {len(ids_sem_vinculo)}")

if ids_sem_vinculo:
    print("\nRemovendo mutuários sem vínculo...")
    
    # Deletar em lotes de 500
    total_removidos = 0
    for i in range(0, len(ids_sem_vinculo), 500):
        batch = ids_sem_vinculo[i:i+500]
        Mutuario.objects.filter(id__in=batch).delete()
        total_removidos += len(batch)
        print(f"  Removidos: {total_removidos}/{len(ids_sem_vinculo)}")
    
    print(f"\n✓ Total removido: {total_removidos}")
    
    # Contar total depois
    total_depois = Mutuario.objects.count()
    print(f"✓ Total de mutuários agora: {total_depois}")
    
    # Verificar conjunto 010
    qtd_010 = Mutuario.objects.filter(conjunto='010').count()
    print(f"✓ Mutuários no conjunto 010: {qtd_010}")
else:
    print("\n✓ Nenhum mutuário sem vínculo encontrado!")

conn.close()
