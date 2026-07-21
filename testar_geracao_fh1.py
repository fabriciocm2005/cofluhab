"""
Script de teste para verificar geração de FH1
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato
from principal.ficha_generators import gerar_lote_fh1_separado

# Pega primeiro contrato
contrato = Contrato.objects.first()

if contrato:
    print(f"Testando com contrato: {contrato.codigo}")
    print("=" * 80)
    
    resultado = gerar_lote_fh1_separado(
        contratos=[contrato],
        matricula='000044',
        numero_lote='001'
    )
    
    print("\n📋 HEADER:")
    print("-" * 80)
    header = resultado['header_conteudo']
    print(f"Tamanho: {len(header)} caracteres")
    print(f"Posição 1-2 (UFS): '{header[0:2]}'")
    print(f"Posição 3-9 (MAT+DV): '{header[2:9]}'")
    print(f"Posição 23 (TIPO REG): '{header[22]}' (deve ser '0')")
    print(f"Posição 33-37 (QTD): '{header[32:37]}'")
    print(f"Posição 406-430 (ID LOTE):")
    id_lote_header = header[405:430]
    print(f"  - UFS (406-407): '{id_lote_header[0:2]}'")
    print(f"  - MAT (408-413): '{id_lote_header[2:8]}'")
    print(f"  - DV (414): '{id_lote_header[8]}'")
    print(f"  - DATA (415-420): '{id_lote_header[9:15]}'")
    print(f"  - LOTE (421-423): '{id_lote_header[15:18]}'")
    print(f"  - FORMA (424): '{id_lote_header[18]}' (deve ser 'S')")
    print(f"  - TIPO MOV (425): '{id_lote_header[19]}' (deve ser 'I')")
    print(f"  - FILLER (426-430): '{id_lote_header[20:25]}'")
    
    print("\n📄 DADOS (primeira linha):")
    print("-" * 80)
    if resultado['dados_conteudo']:
        linhas = resultado['dados_conteudo'].split('\n')
        primeira_linha = linhas[0]
        print(f"Tamanho: {len(primeira_linha)} caracteres")
        print(f"Posição 1-2 (UFS): '{primeira_linha[0:2]}'")
        print(f"Posição 3-9 (MAT+DV): '{primeira_linha[2:9]}'")
        print(f"Posição 23 (TIPO REG): '{primeira_linha[22]}' (deve ser '1')")
        print(f"Posição 406-430 (ID LOTE):")
        id_lote_dados = primeira_linha[405:430]
        print(f"  - UFS (406-407): '{id_lote_dados[0:2]}'")
        print(f"  - MAT (408-413): '{id_lote_dados[2:8]}'")
        print(f"  - DV (414): '{id_lote_dados[8]}'")
        print(f"  - DATA (415-420): '{id_lote_dados[9:15]}'")
        print(f"  - LOTE (421-423): '{id_lote_dados[15:18]}'")
        print(f"  - FORMA (424): '{id_lote_dados[18]}' (deve ser 'S')")
        print(f"  - TIPO MOV (425): '{id_lote_dados[19]}' (deve ser 'I')")
        print(f"  - FILLER (426-430): '{id_lote_dados[20:25]}'")
        
        # Verifica se são idênticos
        print(f"\n🔍 ID LOTE HEADER == ID LOTE DADOS? {id_lote_header == id_lote_dados}")
        if id_lote_header != id_lote_dados:
            print("❌ ERRO: Identificações do lote são diferentes!")
            print(f"   HEADER: '{id_lote_header}'")
            print(f"   DADOS:  '{id_lote_dados}'")
    
    print("\n" + "=" * 80)
    print(f"Total de fichas: {resultado['total_fichas']}")
    print(f"Sucesso: {resultado['total_fichas_sucesso']}")
    print(f"Erros: {resultado['total_fichas_erro']}")
    
else:
    print("❌ Nenhum contrato encontrado no banco")
