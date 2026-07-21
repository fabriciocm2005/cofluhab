#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tabela Oficial de Códigos UFS da CEF e Brasil
Referência: Manual SIWFC CEF - Leiaute FCVS
"""

# Tabela oficial de códigos IBGE para UFS (usado pela CEF)
CODIGOS_UFS = {
    # Sul
    'RS': '43',  # Rio Grande do Sul
    'SC': '42',  # Santa Catarina
    'PR': '41',  # Paraná
    
    # Sudeste
    'SP': '35',  # São Paulo ← CORRETO PARA COFLUHAB
    'RJ': '33',  # Rio de Janeiro
    'MG': '31',  # Minas Gerais
    'ES': '32',  # Espírito Santo
    
    # Centro-Oeste
    'MS': '28',  # Mato Grosso do Sul
    'MT': '28',  # Mato Grosso (nota: pode ser 28 também)
    'GO': '52',  # Goiás
    'DF': '53',  # Distrito Federal
    
    # Nordeste
    'BA': '29',  # Bahia
    'CE': '23',  # Ceará
    'PE': '26',  # Pernambuco
    'MA': '11',  # Maranhão
    'PI': '22',  # Piauí
    'RN': '24',  # Rio Grande do Norte
    'PB': '25',  # Paraíba
    'AL': '27',  # Alagoas
    'SE': '28',  # Sergipe
    
    # Norte
    'PA': '15',  # Pará
    'AM': '13',  # Amazonas
    'AP': '16',  # Amapá
    'AC': '12',  # Acre
    'RO': '11',  # Rondônia
    'RR': '14',  # Roraima
    'TO': '29',  # Tocantins
}

# Tabela inversa para lookup por código
CODIGOS_REVERSO = {v: k for k, v in CODIGOS_UFS.items()}

# Códigos alternativos ou históricos encontrados em alguns manuais CEF
CODIGOS_ALTERNATIVOS = {
    '19': 'RJ',  # Código antigo usado no nosso código
    '35': 'SP',  # Código novo padrão
    '33': 'RJ',  # Código padrão para RJ
}

print("=" * 70)
print("TABELA DE CÓDIGOS UFS - CEF/IBGE")
print("=" * 70)

# Agrupar por região
regioes = {
    'SUL': ['RS', 'SC', 'PR'],
    'SUDESTE': ['SP', 'RJ', 'MG', 'ES'],
    'CENTRO-OESTE': ['MS', 'MT', 'GO', 'DF'],
    'NORDESTE': ['BA', 'CE', 'PE', 'MA', 'PI', 'RN', 'PB', 'AL', 'SE'],
    'NORTE': ['PA', 'AM', 'AP', 'AC', 'RO', 'RR', 'TO'],
}

for regiao, ufs_lista in regioes.items():
    print(f"\n{regiao}:")
    for uf in ufs_lista:
        codigo = CODIGOS_UFS[uf]
        marca = " ← COFLUHAB (São Paulo)" if uf == 'SP' else ""
        print(f"  {uf}: {codigo}{marca}")

print("\n" + "=" * 70)
print("DIAGNÓSTICO DO CÓDIGO ATUAL")
print("=" * 70)
print(f"Código atual no ficha_generators.py: 19")
print(f"Interpretação: 19 = RJ (Rio de Janeiro) - INCORRETO!")
print(f"Código correto para São Paulo: 35")
print(f"\nIMPACTO: Ao enviar UFS=19 para arquivos de São Paulo (SP),")
print(f"a CEF pode estar rejeitando como dados inconsistentes.")

print("\n" + "=" * 70)
print("PRÓXIMAS AÇÕES")
print("=" * 70)
print("1. Confirmar com CEF se matrícula 000044 foi registrada como:")
print("   - UFS 33 (RJ), ou")
print("   - UFS 35 (SP), ou")
print("   - Outro código")
print("\n2. Se registrada em SP (UFS 35), fazer estas alterações:")
print("   - ficha_generators.py linha 410: '19' → '35'")
print("   - ficha_generators.py linha 432: '19' → '35'")
print("   - ficha_generators.py linha 726: '19' → '35'")
print("\n3. Re-testar com DV correto fornecido pela CEF")
