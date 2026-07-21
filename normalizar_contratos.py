"""
Script para normalizar códigos de contratos duplicados.
Mescla dados cadastrais completos (contratos com zeros à esquerda) 
com dados financeiros/parcelas (contratos sem zeros).

Autor: Sistema
Data: 27/11/2024
"""

import os
import sys
import django
from collections import defaultdict
from decimal import Decimal

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato, ParcelaContrato
import sqlite3

def calcular_score_completude(contrato):
    """
    Calcula score de completude dos dados cadastrais do contrato.
    Máximo: 12 pontos
    """
    score = 0
    
    # Dados cadastrais básicos (mais importantes)
    if contrato.conjunto and contrato.conjunto.strip(): score += 3
    if contrato.cod_imovel and contrato.cod_imovel.strip(): score += 2
    if contrato.data_contrato: score += 2
    if contrato.lote and contrato.lote.strip(): score += 1
    if contrato.chave and contrato.chave.strip(): score += 1
    if contrato.sinal and contrato.sinal.strip(): score += 1
    if contrato.sa and contrato.sa.strip(): score += 1
    if contrato.cat_prof and contrato.cat_prof.strip(): score += 1
    
    return score

def calcular_score_financeiro(contrato):
    """
    Calcula score de completude dos dados financeiros.
    Máximo: 10 pontos
    """
    score = 0
    
    # Dados financeiros
    if contrato.data_primeiro_venc: score += 2
    if contrato.tx_juros and contrato.tx_juros > 0: score += 2
    if contrato.prazo and contrato.prazo > 0: score += 2
    if contrato.conversor and contrato.conversor > 0: score += 2
    if contrato.pr and contrato.pr.strip(): score += 2
    
    return score

def normalizar_codigo(codigo):
    """Remove zeros à esquerda do código."""
    if not codigo:
        return codigo
    try:
        # Tenta converter para int e volta para string (remove zeros)
        return str(int(codigo))
    except (ValueError, TypeError):
        return codigo

def mesclar_contratos(contrato_destino, contrato_origem):
    """
    Mescla dados do contrato_origem no contrato_destino.
    Prioriza dados não vazios da origem.
    """
    campos_cadastrais = [
        'conjunto', 'cod_imovel', 'data_contrato', 'data_primeiro_venc',
        'lote', 'chave', 'sinal', 'sa', 'tx_juros', 'prazo',
        'cat_prof', 'pr', 'conversor'
    ]
    
    alteracoes = []
    
    for campo in campos_cadastrais:
        valor_destino = getattr(contrato_destino, campo)
        valor_origem = getattr(contrato_origem, campo)
        
        # Se destino está vazio e origem tem valor, copia
        if not valor_destino and valor_origem:
            setattr(contrato_destino, campo, valor_origem)
            alteracoes.append(f"{campo}: '{valor_origem}'")
        # Se origem tem valor diferente e não vazio, também copia (origem é mais completo)
        elif valor_origem and valor_origem != valor_destino:
            setattr(contrato_destino, campo, valor_origem)
            alteracoes.append(f"{campo}: '{valor_destino}' → '{valor_origem}'")
    
    return alteracoes

def main():
    print("=" * 80)
    print("NORMALIZAÇÃO DE CÓDIGOS DE CONTRATOS DUPLICADOS")
    print("=" * 80)
    print()
    
    # Buscar todos os contratos
    contratos = list(Contrato.objects.all())
    print(f"Total de contratos: {len(contratos)}")
    print()
    
    # Agrupar por código normalizado
    grupos = defaultdict(list)
    for contrato in contratos:
        codigo_original = contrato.codigo
        codigo_normalizado = normalizar_codigo(codigo_original)
        grupos[codigo_normalizado].append(contrato)
    
    # Filtrar apenas grupos com duplicatas
    grupos_duplicados = {k: v for k, v in grupos.items() if len(v) > 1}
    
    if not grupos_duplicados:
        print("OK - Nenhuma duplicata encontrada!")
        return
    
    print(f"AVISO: Encontrados {len(grupos_duplicados)} codigos com duplicatas")
    print()
    
    # Conectar diretamente ao banco para operações SQL
    db_path = os.path.join(os.path.dirname(__file__), 'db.sqlite3')
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    grupos_mesclados = 0
    contratos_removidos = 0
    
    for codigo_norm, duplicatas in grupos_duplicados.items():
        print(f"AVISO: Duplicata encontrada para codigo '{codigo_norm}': {len(duplicatas)} registros")
        
        # Calcular scores
        scores = []
        for c in duplicatas:
            score_cadastral = calcular_score_completude(c)
            score_financeiro = calcular_score_financeiro(c)
            
            # Verificar se tem parcelas (muito importante!)
            num_parcelas = ParcelaContrato.objects.filter(contrato=c).count()
            
            scores.append({
                'contrato': c,
                'score_cadastral': score_cadastral,
                'score_financeiro': score_financeiro,
                'num_parcelas': num_parcelas,
                'score_total': score_cadastral + score_financeiro + (num_parcelas * 0.1)  # Parcelas pesam mais
            })
            
            print(f"  - id={c.id}, codigo='{c.codigo}', score_cadastral={score_cadastral}, "
                  f"score_financeiro={score_financeiro}, parcelas={num_parcelas}")
        
        # Ordenar por score total (maior primeiro)
        scores.sort(key=lambda x: x['score_total'], reverse=True)
        
        # O melhor será o destino (geralmente o que tem parcelas)
        melhor = scores[0]['contrato']
        outros = [s['contrato'] for s in scores[1:]]
        
        print(f"  OK: Mantendo id={melhor.id} (score_total={scores[0]['score_total']:.1f})")
        
        # Mesclar dados cadastrais dos outros no melhor
        for outro in outros:
            alteracoes = mesclar_contratos(melhor, outro)
            if alteracoes:
                print(f"  MESCLANDO dados de id={outro.id}:")
                for alt in alteracoes[:3]:  # Mostra apenas 3 primeiras alterações
                    print(f"     {alt}")
                if len(alteracoes) > 3:
                    print(f"     ... e mais {len(alteracoes) - 3} campos")
        
        # Salvar alterações no contrato destino
        melhor.save()
        
        # Normalizar o código do melhor (remover zeros)
        if melhor.codigo != codigo_norm:
            print(f"  NORMALIZANDO codigo: '{melhor.codigo}' -> '{codigo_norm}'")
            melhor.codigo = codigo_norm
            melhor.save()
        
        # Transferir relacionamentos de contrato_mutuario_map
        for outro in outros:
            # Verificar se tem relacionamentos
            cur.execute("SELECT COUNT(*) FROM contrato_mutuario_map WHERE contrato_id = ?", (outro.id,))
            count = cur.fetchone()[0]
            
            if count > 0:
                # Transferir relacionamentos (se não existir duplicata)
                cur.execute("""
                    UPDATE OR IGNORE contrato_mutuario_map 
                    SET contrato_id = ? 
                    WHERE contrato_id = ?
                """, (melhor.id, outro.id))
                
                # Remover relacionamentos que não puderam ser transferidos (duplicatas)
                cur.execute("DELETE FROM contrato_mutuario_map WHERE contrato_id = ?", (outro.id,))
                
                print(f"  TRANSFERINDO {count} relacionamentos de id={outro.id} -> id={melhor.id}")
        
        # Transferir parcelas (se algum outro tiver)
        for outro in outros:
            parcelas = ParcelaContrato.objects.filter(contrato=outro)
            num_parcelas = parcelas.count()
            
            if num_parcelas > 0:
                print(f"  ATENCAO: id={outro.id} tem {num_parcelas} parcelas!")
                # Verificar se melhor já tem parcelas
                parcelas_melhor = ParcelaContrato.objects.filter(contrato=melhor).count()
                
                if parcelas_melhor == 0:
                    # Transferir parcelas para o melhor
                    parcelas.update(contrato=melhor)
                    print(f"  OK: Parcelas transferidas de id={outro.id} -> id={melhor.id}")
                else:
                    print(f"  AVISO: Mantendo parcelas em ambos (id={melhor.id} ja tem {parcelas_melhor} parcelas)")
        
        # Remover contratos duplicados (usar SQL direto)
        for outro in outros:
            # Verificar novamente se não tem mais parcelas
            parcelas_restantes = ParcelaContrato.objects.filter(contrato=outro).count()
            
            if parcelas_restantes == 0:
                print(f"  REMOVENDO id={outro.id}")
                cur.execute("DELETE FROM principal_contrato WHERE id = ?", (outro.id,))
                contratos_removidos += 1
            else:
                print(f"  AVISO: NAO removendo id={outro.id} (ainda tem {parcelas_restantes} parcelas)")
        
        conn.commit()
        grupos_mesclados += 1
        print()
    
    conn.close()
    
    # Contar contratos finais
    total_final = Contrato.objects.count()
    
    print("=" * 80)
    print(f"OK: Grupos mesclados: {grupos_mesclados}")
    print(f"REMOVIDOS: Contratos duplicados: {contratos_removidos}")
    print(f"TOTAL final de contratos: {total_final}")
    print("=" * 80)

if __name__ == '__main__':
    main()
