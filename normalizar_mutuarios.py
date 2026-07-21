"""
Script para normalizar códigos de mutuários e mesclar dados
Remove zeros à esquerda e mantém o registro mais completo
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Mutuario
import sqlite3

print("=" * 80)
print("NORMALIZANDO CÓDIGOS DE MUTUÁRIOS")
print("=" * 80)

# Buscar todos os mutuários
mutuarios = Mutuario.objects.all().order_by('codigo')
print(f"Total de mutuários: {mutuarios.count()}")

# Agrupar por código normalizado
from collections import defaultdict
grupos = defaultdict(list)

for mutuario in mutuarios:
    codigo_original = mutuario.codigo
    
    # Normalizar código (remover zeros à esquerda se for numérico)
    try:
        if codigo_original.isdigit():
            codigo_normalizado = str(int(codigo_original))
        else:
            codigo_normalizado = codigo_original
    except:
        codigo_normalizado = codigo_original
    
    grupos[codigo_normalizado].append(mutuario)

# Processar grupos com duplicatas
removidos = 0
mesclados = 0

db_path = os.path.join(os.path.dirname(__file__), 'db.sqlite3')
conn = sqlite3.connect(db_path)
cur = conn.cursor()

for codigo_norm, lista_mutuarios in grupos.items():
    if len(lista_mutuarios) > 1:
        print(f"\n⚠️  Duplicata encontrada para código '{codigo_norm}': {len(lista_mutuarios)} registros")
        
        # Escolher o registro mais completo (com mais campos preenchidos)
        melhor = None
        melhor_score = -1
        
        for mut in lista_mutuarios:
            # Calcular "score" de completude
            score = 0
            if mut.nome and mut.nome.strip(): score += 1
            if mut.cpf and mut.cpf.strip(): score += 2
            if mut.ident and mut.ident.strip(): score += 1
            if mut.dtnasc: score += 1
            if mut.endereco and mut.endereco.strip(): score += 3
            if mut.cidade and mut.cidade.strip(): score += 1
            if mut.renda and mut.renda > 0: score += 1
            if mut.telefone and mut.telefone.strip(): score += 1
            if mut.email and mut.email.strip(): score += 1
            
            print(f"  - id={mut.id}, codigo='{mut.codigo}', score={score}, nome={mut.nome[:30]}")
            
            if score > melhor_score:
                melhor_score = score
                melhor = mut
        
        print(f"  ✅ Mantendo id={melhor.id} (score={melhor_score})")
        
        # Atualizar código do melhor para normalizado
        if melhor.codigo != codigo_norm:
            melhor.codigo = codigo_norm
            melhor.save()
            print(f"  ✏️  Código normalizado: '{melhor.codigo}' → '{codigo_norm}'")
        
        # Transferir relacionamentos dos duplicados para o melhor
        for mut in lista_mutuarios:
            if mut.id != melhor.id:
                # Atualizar relacionamentos na tabela contrato_mutuario_map
                cur.execute(
                    "UPDATE contrato_mutuario_map SET mutuario_id = ? WHERE mutuario_id = ?",
                    (melhor.id, mut.id)
                )
                rels_atualizados = cur.rowcount
                
                if rels_atualizados > 0:
                    print(f"  📎 Transferidos {rels_atualizados} relacionamentos de id={mut.id} → id={melhor.id}")
                
                # Deletar duplicado via SQL direto
                print(f"  ❌ Removendo id={mut.id}")
                cur.execute("DELETE FROM principal_mutuario WHERE id = ?", (mut.id,))
                removidos += 1
        
        conn.commit()
        mesclados += 1

conn.close()

print(f"\n{'=' * 80}")
print(f"✅ Grupos mesclados: {mesclados}")
print(f"❌ Mutuários duplicados removidos: {removidos}")
print(f"📊 Total de mutuários após normalização: {Mutuario.objects.count()}")
print("=" * 80)
