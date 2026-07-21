"""
Verifica o conteúdo dos arquivos HEADER e DADOS gerados
"""
import os
from pathlib import Path

# Procura pelos arquivos mais recentes na pasta Downloads ou pasta atual
pastas = [
    Path.home() / "Downloads",
    Path(".")
]

arquivos_header = []
arquivos_dados = []

for pasta in pastas:
    if pasta.exists():
        arquivos_header.extend(pasta.glob("HEADER_FH1_*.txt"))
        arquivos_dados.extend(pasta.glob("DADOS_FH1_*.txt"))

# Ordena por data de modificação (mais recente primeiro)
arquivos_header.sort(key=lambda x: x.stat().st_mtime, reverse=True)
arquivos_dados.sort(key=lambda x: x.stat().st_mtime, reverse=True)

if arquivos_header:
    print("=" * 80)
    print(f"📋 VERIFICANDO HEADER: {arquivos_header[0].name}")
    print("=" * 80)
    
    with open(arquivos_header[0], 'r', encoding='latin-1') as f:
        header = f.read()
    
    print(f"Tamanho: {len(header)} caracteres")
    print(f"\nPosição 1-2 (UFS): '{header[0:2]}'")
    print(f"Posição 3-9 (MAT+DV): '{header[2:9]}'")
    print(f"Posição 23 (TIPO REG): '{header[22]}' (deve ser '0')")
    print(f"Posição 33-37 (QTD): '{header[32:37]}'")
    print(f"\nIDENTIFICAÇÃO DO LOTE (406-430):")
    id_lote = header[405:430]
    print(f"  Completa: '{id_lote}'")
    print(f"  - Posição 406-407 (UFS): '{id_lote[0:2]}'")
    print(f"  - Posição 408-413 (MAT): '{id_lote[2:8]}'")
    print(f"  - Posição 414 (DV): '{id_lote[8]}'")
    print(f"  - Posição 415-420 (DATA): '{id_lote[9:15]}'")
    print(f"  - Posição 421-423 (LOTE): '{id_lote[15:18]}'")
    print(f"  - Posição 424 (FORMA): '{id_lote[18]}' (deve ser 'S')")
    print(f"  - Posição 425 (TIPO MOV): '{id_lote[19]}' (deve ser 'I')")
    print(f"  - Posição 426-430 (FILLER): '{id_lote[20:25]}'")

if arquivos_dados:
    print("\n" + "=" * 80)
    print(f"📄 VERIFICANDO DADOS: {arquivos_dados[0].name}")
    print("=" * 80)
    
    with open(arquivos_dados[0], 'r', encoding='latin-1') as f:
        linhas = f.readlines()
    
    print(f"Total de linhas: {len(linhas)}")
    
    if linhas:
        primeira = linhas[0].rstrip('\n\r')
        print(f"\nPRIMEIRA LINHA:")
        print(f"Tamanho: {len(primeira)} caracteres")
        print(f"\nPosição 1-2 (UFS): '{primeira[0:2]}'")
        print(f"Posição 3-9 (MAT+DV): '{primeira[2:9]}'")
        print(f"Posição 23 (TIPO REG): '{primeira[22]}' (deve ser '1')")
        print(f"\nIDENTIFICAÇÃO DO LOTE (406-430):")
        id_lote = primeira[405:430]
        print(f"  Completa: '{id_lote}'")
        print(f"  - Posição 406-407 (UFS): '{id_lote[0:2]}'")
        print(f"  - Posição 408-413 (MAT): '{id_lote[2:8]}'")
        print(f"  - Posição 414 (DV): '{id_lote[8]}'")
        print(f"  - Posição 415-420 (DATA): '{id_lote[9:15]}'")
        print(f"  - Posição 421-423 (LOTE): '{id_lote[15:18]}'")
        print(f"  - Posição 424 (FORMA): '{id_lote[18]}' (deve ser 'S')")
        print(f"  - Posição 425 (TIPO MOV): '{id_lote[19]}' (deve ser 'I')")
        print(f"  - Posição 426-430 (FILLER): '{id_lote[20:25]}'")

if not arquivos_header and not arquivos_dados:
    print("❌ Nenhum arquivo HEADER ou DADOS encontrado!")
    print("Gere um novo lote e rode este script novamente.")
