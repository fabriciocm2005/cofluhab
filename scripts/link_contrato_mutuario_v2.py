#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Heuristic mapper v2: Contrato -> Mutuario
Estratégias melhoradas:
1. Exact match: CODIGO + CONJUNTO
2. Fuzzy name com normalização avançada
3. Proximidade de datas (cadastro)
4. Scoring ponderado multi-critério
"""
import os
import sys
import django
import csv
import re
from difflib import SequenceMatcher
from datetime import datetime, timedelta
from unicodedata import normalize

# Setup Django
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato, Mutuario

def normalize_text(text):
    """Remove acentos, converte para maiúsculas, remove pontuação e espaços extras"""
    if not text:
        return ""
    # Remove acentos
    text = normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
    # Converte para maiúsculas
    text = text.upper()
    # Remove pontuação e caracteres especiais
    text = re.sub(r'[^A-Z0-9\s]', '', text)
    # Remove espaços extras
    text = ' '.join(text.split())
    return text

def extract_key_words(name):
    """Extrai palavras-chave ignorando conectores comuns"""
    if not name:
        return []
    stopwords = {'DE', 'DA', 'DO', 'DOS', 'DAS', 'E'}
    words = normalize_text(name).split()
    return [w for w in words if w not in stopwords and len(w) > 2]

def fuzzy_match_score(name1, name2):
    """Calcula similaridade fuzzy com normalização"""
    norm1 = normalize_text(name1)
    norm2 = normalize_text(name2)
    
    if not norm1 or not norm2:
        return 0.0
    
    # Similaridade básica
    basic_score = SequenceMatcher(None, norm1, norm2).ratio()
    
    # Palavras-chave
    words1 = extract_key_words(name1)
    words2 = extract_key_words(name2)
    
    if not words1 or not words2:
        return basic_score
    
    # Conta palavras em comum
    common = set(words1) & set(words2)
    word_score = len(common) / max(len(words1), len(words2)) if words1 or words2 else 0
    
    # Score ponderado
    return 0.6 * basic_score + 0.4 * word_score

def date_proximity_score(date1, date2, max_days=365):
    """Calcula score baseado em proximidade de datas (1.0 = mesma data, 0.0 = > max_days)"""
    if not date1 or not date2:
        return 0.0
    
    try:
        if isinstance(date1, str):
            date1 = datetime.strptime(date1, '%Y-%m-%d').date()
        if isinstance(date2, str):
            date2 = datetime.strptime(date2, '%Y-%m-%d').date()
        
        diff_days = abs((date1 - date2).days)
        if diff_days == 0:
            return 1.0
        if diff_days > max_days:
            return 0.0
        return 1.0 - (diff_days / max_days)
    except:
        return 0.0

def find_best_match(contrato, mutuarios_cache):
    """
    Encontra o melhor match usando múltiplas estratégias
    Returns: (mutuario_id, score, method)
    """
    codigo = contrato.codigo.strip() if contrato.codigo else ""
    conjunto = contrato.conjunto.strip() if contrato.conjunto else ""
    # Contrato não tem nome, apenas codigo e conjunto
    
    best_match = None
    best_score = 0.0
    best_method = None
    
    # Estratégia 1: Exact match CODIGO + CONJUNTO
    if codigo and conjunto:
        for mut in mutuarios_cache:
            mut_codigo = mut.codigo.strip() if mut.codigo else ""
            mut_conjunto = mut.conjunto_fk.conjunto.strip() if mut.conjunto_fk and mut.conjunto_fk.conjunto else ""
            
            if mut_codigo == codigo and mut_conjunto == conjunto:
                return (mut.id, 1.0, 'exact-codigo-conjunto')
    
    # Estratégia 2: Exact match CODIGO only (se não encontrou com conjunto)
    if codigo:
        for mut in mutuarios_cache:
            mut_codigo = mut.codigo.strip() if mut.codigo else ""
            if mut_codigo == codigo:
                return (mut.id, 0.9, 'exact-codigo')
    
    # Estratégia 3: Partial CONJUNTO match (como fallback)
    if conjunto:
        for mut in mutuarios_cache:
            mut_conjunto = mut.conjunto_fk.conjunto.strip() if mut.conjunto_fk and mut.conjunto_fk.conjunto else ""
            if mut_conjunto == conjunto:
                score = 0.5  # Score moderado para match apenas por conjunto
                if score > best_score:
                    best_score = score
                    best_match = mut.id
                    best_method = 'conjunto-only'
    
    if best_match:
        return (best_match, best_score, best_method)
    
    return (None, 0.0, 'no-match')

def main():
    print("=== Contrato → Mutuário Mapper V2 ===")
    print("Carregando Contratos...")
    contratos = list(Contrato.objects.all())
    print(f"  Total: {len(contratos)}")
    
    print("Carregando Mutuários...")
    mutuarios = list(Mutuario.objects.all().select_related('conjunto_fk'))
    print(f"  Total: {len(mutuarios)}")
    
    output_file = os.path.join(project_root, 'exports', 'contrato_mutuario_map_v2.csv')
    
    print(f"Processando mapeamento...")
    results = []
    
    for i, contrato in enumerate(contratos, 1):
        if i % 100 == 0:
            print(f"  {i}/{len(contratos)} processados...")
        
        mutuario_id, score, method = find_best_match(contrato, mutuarios)
        
        results.append({
            'contrato_id': contrato.id,
            'mutuario_id': mutuario_id,
            'score': round(score, 4),
            'method': method,
            'contrato_codigo': contrato.codigo or '',
            'contrato_conjunto': contrato.conjunto or '',
        })
    
    # Write CSV
    print(f"Salvando resultados em {output_file}...")
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['contrato_id', 'mutuario_id', 'score', 'method', 
                  'contrato_codigo', 'contrato_conjunto']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    # Estatísticas
    matched = sum(1 for r in results if r['mutuario_id'])
    unmatched = len(results) - matched
    
    methods = {}
    scores_by_method = {}
    for r in results:
        if r['mutuario_id']:
            method = r['method']
            methods[method] = methods.get(method, 0) + 1
            if method not in scores_by_method:
                scores_by_method[method] = []
            scores_by_method[method].append(r['score'])
    
    print("\n=== Estatísticas ===")
    print(f"Total contratos: {len(results)}")
    print(f"Com match: {matched} ({matched/len(results)*100:.1f}%)")
    print(f"Sem match: {unmatched} ({unmatched/len(results)*100:.1f}%)")
    print("\nMétodos utilizados:")
    for method, count in sorted(methods.items(), key=lambda x: -x[1]):
        avg_score = sum(scores_by_method[method]) / len(scores_by_method[method])
        print(f"  {method}: {count} matches (score médio: {avg_score:.3f})")
    
    # High confidence (score >= 0.9)
    high_conf = [r for r in results if r['mutuario_id'] and r['score'] >= 0.9]
    print(f"\nHigh confidence (score >= 0.9): {len(high_conf)} ({len(high_conf)/len(results)*100:.1f}%)")
    
    # Medium confidence (0.7 <= score < 0.9)
    med_conf = [r for r in results if r['mutuario_id'] and 0.7 <= r['score'] < 0.9]
    print(f"Medium confidence (0.7-0.9): {len(med_conf)} ({len(med_conf)/len(results)*100:.1f}%)")
    
    # Low confidence (score < 0.7)
    low_conf = [r for r in results if r['mutuario_id'] and r['score'] < 0.7]
    print(f"Low confidence (< 0.7): {len(low_conf)} ({len(low_conf)/len(results)*100:.1f}%)")
    
    print(f"\n✓ CSV gerado: {output_file}")

if __name__ == '__main__':
    main()
