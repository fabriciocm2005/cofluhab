"""
Comparação Campo a Campo - Gerador vs Arquivo Real CEF

Compara nossa ficha FH1 gerada com a ficha real da CEF
para garantir que está 100% perfeita.

Autor: Cofluhab
Data: 2026-01-29
"""

import json
from pathlib import Path


def comparar_fh1():
    """Compara FH1 gerado com FH1 real da CEF"""
    
    print("=" * 80)
    print("COMPARAÇÃO CAMPO A CAMPO - GERADOR vs ARQUIVO REAL CEF")
    print("=" * 80)
    
    # Lê arquivo real da CEF
    arquivo_real = Path('principal/templates/DADOS_FH1_20260212_122417.txt')
    with open(arquivo_real, 'r', encoding='latin-1') as f:
        linha_real = f.read().strip()
    
    # Lê layout completo
    layout_file = Path('fh1_layout_completo_real.json')
    with open(layout_file, 'r', encoding='utf-8') as f:
        layout = json.load(f)
    
    # Gera nossa ficha usando gerador novo
    from principal.fh1_generator_novo import FH1GeneratorNovo
    from datetime import date
    from decimal import Decimal
    
    class ContratoFake:
        def __init__(self):
            self.codigo = '6000'
            self.conjunto = 'TESTE'
            self.data_contrato = date(2020, 1, 15)
            self.prazo = 240
            self.tx_juros = Decimal('0.06')
            self.sa = 'SAC'
            self.cat_prof = '00000'
            self.pr = 'NN'
    
    class MutuarioFake:
        def __init__(self):
            self.nome = 'ALDEMIR PEREIRA DA SILVA'
            self.cpf = '01358971987'
            self.dtnasc = date(1972, 1, 1)
            self.cidade = 'RIO DE JANEIRO'
            self.uf = 'RJ'
            self.endereco = 'RUA TESTE 123'
    
    class ParcelaFake:
        def __init__(self):
            self.nmens = 1
            self.dtvenc = date(2020, 2, 15)
            self.amort = Decimal('30108.40')
    
    # Simula parcelas
    contrato_fake = ContratoFake()
    contrato_fake.parcelas = type('obj', (object,), {
        'all': lambda: [ParcelaFake()],
        'order_by': lambda x: type('obj', (object,), {'first': lambda: ParcelaFake()})()
    })()
    
    gerador = FH1GeneratorNovo()
    linha_gerada, avisos = gerador.gerar_de_contrato(contrato_fake, MutuarioFake())
    
    print(f"\n📏 TAMANHOS:")
    print(f"   Real CEF: {len(linha_real)} caracteres")
    print(f"   Gerado:   {len(linha_gerada)} caracteres")
    print(f"   Status:   {'✅ IGUAL' if len(linha_real) == len(linha_gerada) else '❌ DIFERENTE'}")
    
    print(f"\n📊 COMPARAÇÃO CAMPO A CAMPO:")
    print(f"{'='*80}")
    
    # Compara campos documentados
    campos_ok = 0
    campos_diff = 0
    
    for campo in layout['campos_documentados']:
        inicio = campo['inicio'] - 1
        fim = campo['fim']
        nome = campo['nome']
        
        valor_real = linha_real[inicio:fim] if fim <= len(linha_real) else ''
        valor_gerado = linha_gerada[inicio:fim] if fim <= len(linha_gerada) else ''
        
        if valor_real == valor_gerado:
            print(f"✅ {nome:30s} | Real: '{valor_real}' | Gerado: '{valor_gerado}'")
            campos_ok += 1
        else:
            print(f"❌ {nome:30s} | Real: '{valor_real}' | Gerado: '{valor_gerado}'")
            campos_diff += 1
    
    print(f"\n{'='*80}")
    print(f"\n📊 RESUMO CAMPOS DOCUMENTADOS:")
    print(f"   ✅ Campos OK: {campos_ok}")
    print(f"   ❌ Diferenças: {campos_diff}")
    print(f"   📈 Taxa de sucesso: {campos_ok/(campos_ok+campos_diff)*100:.1f}%")
    
    # Compara campos extras
    print(f"\n{'='*80}")
    print(f"\n📊 CAMPOS EXTRAS (193-424):")
    
    campos_extras_ok = 0
    campos_extras_diff = 0
    
    for campo in layout['campos_extras']:
        inicio = campo['inicio'] - 1
        fim = campo['fim']
        nome = campo['nome']
        
        valor_real = linha_real[inicio:fim] if fim <= len(linha_real) else ''
        valor_gerado = linha_gerada[inicio:fim] if fim <= len(linha_gerada) else ''
        
        if valor_real == valor_gerado:
            print(f"✅ {nome:30s} | Real: '{valor_real[:20]}...' | OK")
            campos_extras_ok += 1
        else:
            print(f"❌ {nome:30s} | Real: '{valor_real[:20]}...' | Gerado: '{valor_gerado[:20]}...'")
            campos_extras_diff += 1
    
    print(f"\n{'='*80}")
    print(f"\n📊 RESUMO CAMPOS EXTRAS:")
    print(f"   ✅ Campos OK: {campos_extras_ok}")
    print(f"   ❌ Diferenças: {campos_extras_diff}")
    print(f"   📈 Taxa de sucesso: {campos_extras_ok/(campos_extras_ok+campos_extras_diff)*100:.1f}%")
    
    # Análise byte a byte das diferenças
    print(f"\n{'='*80}")
    print(f"\n🔍 ANÁLISE BYTE A BYTE DAS DIFERENÇAS:")
    
    diffs = []
    for i in range(min(len(linha_real), len(linha_gerada))):
        if linha_real[i] != linha_gerada[i]:
            diffs.append({
                'pos': i+1,
                'real': linha_real[i],
                'gerado': linha_gerada[i]
            })
    
    if diffs:
        print(f"\n   Total de diferenças: {len(diffs)}")
        print(f"\n   Primeiras 20 diferenças:")
        for diff in diffs[:20]:
            print(f"      Posição {diff['pos']:3d}: Real='{diff['real']}' | Gerado='{diff['gerado']}'")
    else:
        print(f"\n   🎉 NENHUMA DIFERENÇA! FH1 PERFEITO!")
    
    # Resumo final
    print(f"\n{'='*80}")
    print(f"\n🏆 RESULTADO FINAL:")
    total_campos = campos_ok + campos_diff + campos_extras_ok + campos_extras_diff
    total_ok = campos_ok + campos_extras_ok
    taxa_final = (total_ok / total_campos * 100) if total_campos > 0 else 0
    
    print(f"   Total de campos: {total_campos}")
    print(f"   Campos corretos: {total_ok}")
    print(f"   Taxa de acerto: {taxa_final:.1f}%")
    
    if len(diffs) == 0 and taxa_final == 100:
        print(f"\n   🎉🎉🎉 FH1 GERADOR ESTÁ PERFEITO! 🎉🎉🎉")
    elif taxa_final >= 90:
        print(f"\n   ✅ FH1 está muito bom! Algumas pequenas diferenças a corrigir.")
    else:
        print(f"\n   ⚠️  FH1 precisa de ajustes. Revise os campos diferentes.")
    
    # Salva relatório
    relatorio = {
        'tamanho_real': len(linha_real),
        'tamanho_gerado': len(linha_gerada),
        'campos_documentados_ok': campos_ok,
        'campos_documentados_diff': campos_diff,
        'campos_extras_ok': campos_extras_ok,
        'campos_extras_diff': campos_extras_diff,
        'total_diferencas_byte': len(diffs),
        'taxa_acerto': taxa_final,
        'perfeito': len(diffs) == 0 and taxa_final == 100
    }
    
    with open('fh1_comparacao_resultado.json', 'w', encoding='utf-8') as f:
        json.dump(relatorio, f, indent=2, ensure_ascii=False)
    
    print(f"\n   📄 Relatório salvo em: fh1_comparacao_resultado.json")
    
    return relatorio


if __name__ == '__main__':
    resultado = comparar_fh1()
