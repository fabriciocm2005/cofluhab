"""
Análise Detalhada do Arquivo Real FH1

Faz uma análise byte a byte do arquivo real para entender
exatamente como a CEF formata cada campo.

Autor: Cofluhab
Data: 2026-01-29
"""

from pathlib import Path


def analisar_arquivo_real():
    """Analisa arquivo real em detalhes"""
    
    print("=" * 80)
    print("ANÁLISE DETALHADA DO ARQUIVO REAL CEF")
    print("=" * 80)
    
    # Lê arquivo real
    arquivo = Path('principal/templates/DADOS_FH1_20260212_122417.txt')
    with open(arquivo, 'r', encoding='latin-1') as f:
        linha = f.read().strip()
    
    print(f"\n📏 TAMANHO: {len(linha)} caracteres")
    
    # Mostra em blocos de 80
    print(f"\n📄 CONTEÚDO (em blocos de 80 caracteres):")
    print("="*80)
    for i in range(0, len(linha), 80):
        bloco = linha[i:i+80]
        print(f"[{i+1:3d}-{i+len(bloco):3d}] {bloco}")
    
    # Análise campo a campo com layout manual
    print(f"\n{'='*80}")
    print(f"\n🔍 ANÁLISE CAMPO A CAMPO:")
    print(f"{'='*80}")
    
    # Campos documentados com posições exatas
    campos = [
        (1, 2, 'UFS', linha[0:2]),
        (3, 8, 'MAT', linha[2:8]),
        (9, 21, 'CONTRATO', linha[8:21]),
        (22, 22, 'HIPOTECA', linha[21:22]),
        (23, 24, 'SEQ', linha[22:24]),
        (25, 25, 'CONST', linha[24:25]),
        (26, 65, 'NOME', linha[25:65]),
        (66, 76, 'CPF', linha[65:76]),
        (77, 82, 'DTNASC', linha[76:82]),
        (83, 87, 'CODMUN', linha[82:87]),
        (88, 89, 'UF', linha[87:89]),
        (90, 127, 'ENDERECO', linha[89:127]),
        (128, 133, 'DTCONTRATO', linha[127:133]),
        (134, 145, 'VLRFINCONTRAT', linha[133:145]),
        (146, 148, 'PRAZOCONTRAT', linha[145:148]),
        (149, 152, 'TXJUROS', linha[148:152]),
        (153, 164, 'VLRFINFCVS', linha[152:164]),
        (165, 167, 'PRAZOFCVS', linha[164:167]),
        (168, 171, 'TXJUROSFCVS', linha[167:171]),
        (172, 174, 'PLANO', linha[171:174]),
        (175, 176, 'RR', linha[174:176]),
        (177, 179, 'INDEX', linha[176:179]),
        (180, 184, 'CATPROF', linha[179:184]),
        (185, 186, 'PR', linha[184:186]),
        (187, 192, '1VENC', linha[186:192]),
    ]
    
    for inicio, fim, nome, valor in campos:
        tam = fim - inicio + 1
        valor_repr = repr(valor)
        print(f"[{inicio:3d}-{fim:3d}] {nome:20s} ({tam:2d}): {valor_repr}")
    
    # Campos extras (193-424)
    print(f"\n{'='*80}")
    print(f"\n📦 CAMPOS EXTRAS (193-424):")
    print(f"{'='*80}")
    
    extras = linha[192:424]
    print(f"Total de {len(extras)} caracteres extras")
    print(f"\nConteúdo:")
    for i in range(0, len(extras), 80):
        bloco = extras[i:i+80]
        posicao_inicial = 193 + i
        print(f"[{posicao_inicial:3d}-{posicao_inicial+len(bloco)-1:3d}] {repr(bloco)}")
    
    # Análise de padrões nos extras
    print(f"\n{'='*80}")
    print(f"\n🔎 PADRÕES IDENTIFICADOS NOS EXTRAS:")
    print(f"{'='*80}")
    
    # Procura por sequências repetidas
    print("\n1. Primeiros 50 caracteres dos extras:")
    print(f"   {repr(extras[:50])}")
    
    print("\n2. Últimos 50 caracteres dos extras:")
    print(f"   {repr(extras[-50:])}")
    
    # Conta caracteres especiais
    zeros = extras.count('0')
    espacos = extras.count(' ')
    
    print(f"\n3. Estatísticas:")
    print(f"   - Zeros ('0'): {zeros} ({zeros/len(extras)*100:.1f}%)")
    print(f"   - Espaços (' '): {espacos} ({espacos/len(extras)*100:.1f}%)")
    print(f"   - Outros: {len(extras) - zeros - espacos}")
    
    # Tenta identificar blocos de zeros
    print(f"\n4. Blocos contínuos de zeros:")
    i = 0
    while i < len(extras):
        if extras[i] == '0':
            inicio_bloco = i
            while i < len(extras) and extras[i] == '0':
                i += 1
            tamanho_bloco = i - inicio_bloco
            if tamanho_bloco >= 10:  # Apenas blocos grandes
                pos_real = 193 + inicio_bloco
                print(f"   - Posição {pos_real}: {tamanho_bloco} zeros")
        else:
            i += 1
    
    # Salva análise
    print(f"\n{'='*80}")
    print(f"\n💾 SALVANDO ANÁLISE...")
    
    resultado = {
        'tamanho': len(linha),
        'linha_completa': linha,
        'campos_documentados': {
            campo[2]: {
                'inicio': campo[0],
                'fim': campo[1],
                'valor': campo[3]
            }
            for campo in campos
        },
        'campos_extras': extras,
        'estatisticas': {
            'zeros': zeros,
            'espacos': espacos,
            'outros': len(extras) - zeros - espacos
        }
    }
    
    import json
    with open('fh1_arquivo_real_analise.json', 'w', encoding='utf-8') as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    
    print(f"   ✅ Análise salva em: fh1_arquivo_real_analise.json")
    
    # Mostra valores específicos importantes
    print(f"\n{'='*80}")
    print(f"\n🎯 VALORES IMPORTANTES IDENTIFICADOS:")
    print(f"{'='*80}")
    
    print(f"\n📍 Campo NOME:")
    print(f"   - Valor: {repr(linha[25:65])}")
    print(f"   - Observação: Começa com '0' - pode ser flag especial")
    
    print(f"\n📍 Campo CPF:")
    print(f"   - Valor: {repr(linha[65:76])}")
    print(f"   - Observação: Tem espaço antes - alinhamento à direita")
    
    print(f"\n📍 Campo DATA_NASCIMENTO:")
    print(f"   - Valor: {repr(linha[76:82])}")
    print(f"   - Observação: Apenas ano '72' com espaços - formato especial")
    
    print(f"\n📍 Campo ENDERECO:")
    print(f"   - Valor: {repr(linha[89:127])}")
    print(f"   - Observação: Formato especial com números no início")
    
    print(f"\n📍 Campo PRIMEIRO_VENCIMENTO:")
    print(f"   - Valor: {repr(linha[186:192])}")
    print(f"   - Observação: '000301' - pode ser MMAAAA ou AAMMDD")


if __name__ == '__main__':
    analisar_arquivo_real()
