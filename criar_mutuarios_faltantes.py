import os
import django
import sqlite3

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato, Mutuario

conn = sqlite3.connect(r'C:\Users\fabri\cofluhab\cofluhab\db.sqlite3')
cur = conn.cursor()

print("\n=== CRIANDO MUTUÁRIOS FALTANTES PARA CONTRATOS ===\n")

# Buscar todos os conjuntos
from principal.models import ConjuntoHabitacional

for conj in ConjuntoHabitacional.objects.all().order_by('conjunto'):
    conjunto = conj.conjunto
    
    # Buscar contratos do conjunto
    contratos = Contrato.objects.filter(conjunto=conjunto)
    qtd_contratos = contratos.count()
    
    # Buscar mutuários do conjunto
    qtd_mutuarios = Mutuario.objects.filter(conjunto=conjunto).count()
    
    if qtd_contratos > qtd_mutuarios:
        faltam = qtd_contratos - qtd_mutuarios
        print(f"Conjunto {conjunto} ({conj.nome})")
        print(f"  Contratos: {qtd_contratos}")
        print(f"  Mutuários: {qtd_mutuarios}")
        print(f"  Faltam: {faltam}")
        
        # Buscar contratos sem mutuário correspondente no mesmo conjunto
        cur.execute("""
            SELECT c.id, c.codigo
            FROM principal_contrato c
            WHERE c.conjunto = ?
            AND NOT EXISTS (
                SELECT 1 FROM principal_mutuario m
                WHERE m.codigo = c.codigo AND m.conjunto = c.conjunto
            )
        """, (conjunto,))
        
        contratos_sem_mut = cur.fetchall()
        
        if contratos_sem_mut:
            print(f"  Criando {len(contratos_sem_mut)} mutuários...")
            
            for contrato_id, codigo in contratos_sem_mut:
                # Criar mutuário genérico
                mutuario, created = Mutuario.objects.get_or_create(
                    codigo=codigo,
                    conjunto=conjunto,
                    defaults={
                        'nome': f'MUTUÁRIO CONTRATO {codigo}',
                        'cpf': '',
                        'ident': '',
                        'renda': 0,
                    }
                )
                
                if created:
                    # Vincular ao contrato
                    cur.execute("""
                        INSERT OR IGNORE INTO contrato_mutuario_map (contrato_id, mutuario_id)
                        VALUES (?, ?)
                    """, (contrato_id, mutuario.id))
            
            conn.commit()
            print(f"  ✓ Mutuários criados e vinculados!")
        print()

conn.close()
print("\n✓ Processo concluído!")
