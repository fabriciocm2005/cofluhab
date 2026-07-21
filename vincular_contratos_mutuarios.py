"""
Script para criar relacionamentos entre Contratos e Mutuários
pelo código (chave única)
"""
import os
import sys
import django
import sqlite3

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato, Mutuario


def vincular_contratos_mutuarios():
    """Cria relacionamentos na tabela contrato_mutuario_map"""
    
    print("=" * 80)
    print("VINCULANDO CONTRATOS E MUTUÁRIOS")
    print("=" * 80)
    
    db_path = os.path.join(os.path.dirname(__file__), 'db.sqlite3')
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Verificar relacionamentos existentes
    cur.execute("SELECT COUNT(*) FROM contrato_mutuario_map")
    existentes = cur.fetchone()[0]
    print(f"Relacionamentos existentes: {existentes}")
    
    # Buscar todos os contratos
    contratos = Contrato.objects.all()
    mutuarios_dict = {m.codigo: m.id for m in Mutuario.objects.all()}
    
    print(f"Total de contratos: {contratos.count()}")
    print(f"Total de mutuários: {len(mutuarios_dict)}")
    
    # Criar relacionamentos em lote
    relacionamentos = []
    vinculados = 0
    nao_encontrados = 0
    
    for contrato in contratos:
        # Verificar se já existe relacionamento
        cur.execute(
            "SELECT COUNT(*) FROM contrato_mutuario_map WHERE contrato_id = ?",
            (contrato.id,)
        )
        
        if cur.fetchone()[0] > 0:
            continue  # Já tem relacionamento
        
        # Buscar mutuário com mesmo código
        if contrato.codigo in mutuarios_dict:
            mutuario_id = mutuarios_dict[contrato.codigo]
            relacionamentos.append((contrato.id, mutuario_id, 1.0, 'codigo_match'))
            vinculados += 1
            
            # Inserir em lotes de 500
            if len(relacionamentos) >= 500:
                cur.executemany(
                    "INSERT OR IGNORE INTO contrato_mutuario_map (contrato_id, mutuario_id, score, method) VALUES (?, ?, ?, ?)",
                    relacionamentos
                )
                conn.commit()
                print(f"✅ Vinculados {vinculados} contratos...")
                relacionamentos = []
        else:
            nao_encontrados += 1
    
    # Inserir relacionamentos restantes
    if relacionamentos:
        cur.executemany(
            "INSERT OR IGNORE INTO contrato_mutuario_map (contrato_id, mutuario_id, score, method) VALUES (?, ?, ?, ?)",
            relacionamentos
        )
        conn.commit()
    
    # Verificar total após vinculação
    cur.execute("SELECT COUNT(*) FROM contrato_mutuario_map")
    total_final = cur.fetchone()[0]
    
    conn.close()
    
    print(f"\n✅ Novos vínculos criados: {vinculados}")
    print(f"⚠️  Contratos sem mutuário: {nao_encontrados}")
    print(f"📊 Total de relacionamentos: {total_final}")
    print("=" * 80)


if __name__ == '__main__':
    print("\n🚀 Iniciando vinculação...\n")
    vincular_contratos_mutuarios()
    print("\n✅ VINCULAÇÃO CONCLUÍDA!")
