import os
import glob
from pathlib import Path

print("=" * 80)
print("🔍 ANALISANDO ÚLTIMOS ARQUIVOS GERADOS")
print("=" * 80)

# Busca arquivos mais recentes no Downloads
downloads = Path.home() / "Downloads"
header_files = sorted(downloads.glob("HEADER_FH1_*.txt"), key=os.path.getmtime, reverse=True)
dados_files = sorted(downloads.glob("DADOS_FH1_*.txt"), key=os.path.getmtime, reverse=True)

if not header_files or not dados_files:
    print("❌ Nenhum arquivo encontrado no Downloads")
    exit()

header_file = header_files[0]
dados_file = dados_files[0]

print(f"\n📄 HEADER: {header_file.name}")
print(f"📄 DADOS: {dados_file.name}")

# Lê HEADER
with open(header_file, 'r', encoding='latin-1') as f:
    header_linhas = f.readlines()

# Lê DADOS
with open(dados_file, 'r', encoding='latin-1') as f:
    dados_linhas = f.readlines()

print(f"\n{'='*80}")
print(f"HEADER - Total de linhas: {len(header_linhas)}")
print(f"{'='*80}")
for idx, linha in enumerate(header_linhas, 1):
    tipo_reg = linha[22] if len(linha) > 22 else '?'
    print(f"Linha {idx}: len={len(linha.rstrip())} | Tipo Reg (pos 23): '{tipo_reg}'")
    print(f"  Primeiros 50 chars: [{linha[:50]}]")
    print(f"  Últimos 50 chars: [{linha[-50:].rstrip()}]")
    print()

print(f"\n{'='*80}")
print(f"DADOS - Total de linhas: {len(dados_linhas)}")
print(f"{'='*80}")
for idx, linha in enumerate(dados_linhas[:5], 1):  # Mostra primeiras 5 linhas
    tipo_reg = linha[22] if len(linha) > 22 else '?'
    ufs = linha[0:2] if len(linha) >= 2 else '?'
    mat = linha[2:8] if len(linha) >= 8 else '?'
    print(f"Linha {idx}: len={len(linha.rstrip())} | Tipo Reg (pos 23): '{tipo_reg}' | UFS: '{ufs}' | MAT: '{mat}'")
    print(f"  Primeiros 50 chars: [{linha[:50]}]")
    
    # Verifica se é HEADER (tipo '0' na posição 23)
    if tipo_reg == '0':
        print(f"  ⚠️  ATENÇÃO: Esta linha parece ser HEADER no arquivo DADOS!")
    print()

# Análise detalhada da primeira linha DADOS
if dados_linhas:
    primeira = dados_linhas[0].rstrip()
    print(f"\n{'='*80}")
    print("ANÁLISE DETALHADA - PRIMEIRA LINHA DADOS")
    print(f"{'='*80}")
    print(f"Tamanho: {len(primeira)} caracteres")
    print()
    print("CONTROLE (posições 1-23):")
    print(f"  01-02: UFS = '{primeira[0:2] if len(primeira) >= 2 else 'FALTA'}'")
    print(f"  03-08: MATRÍCULA = '{primeira[2:8] if len(primeira) >= 8 else 'FALTA'}'")
    print(f"  09-22: ZEROS = '{primeira[8:22] if len(primeira) >= 22 else 'FALTA'}'")
    print(f"  23: TIPO REG = '{primeira[22] if len(primeira) >= 23 else 'FALTA'}'")
    print()
    print("IDENTIFICAÇÃO DO LOTE (posições 406-430):")
    if len(primeira) >= 430:
        id_lote = primeira[405:430]
        print(f"  406-407: UFS = '{id_lote[0:2]}'")
        print(f"  408-412: MAT = '{id_lote[2:7]}'")
        print(f"  413-418: DATA = '{id_lote[7:13]}'")
        print(f"  419-421: LOTE = '{id_lote[13:16]}'")
        print(f"  422: FORMA = '{id_lote[16]}'")
        print(f"  423: TIPO = '{id_lote[17]}'")
        print(f"  424-430: FILLER = '{id_lote[18:25]}'")
        print()
        print(f"  ID LOTE completa: [{id_lote}]")
        
        # Verifica se número do lote é numérico
        num_lote = id_lote[13:16]
        if num_lote.isdigit():
            print(f"  ✅ Número do lote é numérico: {num_lote}")
        else:
            print(f"  ❌ Número do lote NÃO é numérico: '{num_lote}'")
    else:
        print(f"  ❌ Linha muito curta: {len(primeira)} chars")

print(f"\n{'='*80}")
