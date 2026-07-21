#!/usr/bin/env python
"""
Script utilitário para processamento OCR de contratos via CLI
Uso: python manage.py shell < processar_ocr_contratos.py
Ou: python ocr_processor_cli.py <pasta_pdfs>
"""

import os
import sys
import django
from pathlib import Path
from typing import Dict, Any

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from ocr_contrato_processor import ProcessadorLoteContratos, ContratoOCRExtractor, ContratoProcessor
from principal.ocr_hibrido import analisar_ocr_hibrido


def _resumo_hibrido(relatorio: Dict[str, Any]) -> str:
    return (
        f"hibrido score={relatorio.get('score', 0)} "
        f"auto={relatorio.get('qtd_auto', 0)} "
        f"revisar={relatorio.get('qtd_revisar', 0)}"
    )

def processar_pasta(caminho_pasta, dry_run=False, verbose=True):
    """Processa todos os PDFs de uma pasta"""
    try:
        processador = ProcessadorLoteContratos(caminho_pasta)
        
        if verbose:
            print("\n" + "="*60)
            print("PROCESSADOR OCR DE CONTRATOS")
            print("="*60)
            print(f"Pasta: {caminho_pasta}")
            print(f"Modo: {'TESTE (dry-run)' if dry_run else 'PRODUÇÃO'}")
            print("="*60 + "\n")
        
        # Processa
        resultados = processador.processar(dry_run=dry_run)
        
        # Mostra relatório
        relatorio = processador.gerar_relatorio()
        print(relatorio)
        
        return resultados
        
    except Exception as e:
        print(f"\n✗ Erro: {str(e)}", file=sys.stderr)
        return None

def processar_arquivo_unico(caminho_pdf, dry_run=False, verbose=True):
    """Processa um único PDF"""
    try:
        extractor = ContratoOCRExtractor(caminho_pdf)
        dados = extractor.extract_all()
        dados, relatorio_hibrido = analisar_ocr_hibrido(dados or {}, extractor.text or '')
        
        if verbose:
            print("\n" + "="*60)
            print("PROCESSADOR OCR - ARQUIVO ÚNICO")
            print("="*60)
            print(f"Arquivo: {Path(caminho_pdf).name}")
            print("="*60 + "\n")
            
            if dados:
                print("Dados extraídos:")
                for chave, valor in dados.items():
                    print(f"  {chave}: {valor}")
                print()
                print(f"OCR Hibrido: {_resumo_hibrido(relatorio_hibrido)}")
                if relatorio_hibrido.get('recuperados'):
                    print(f"Campos recuperados: {relatorio_hibrido['recuperados']}")
                if relatorio_hibrido.get('campos_revisar'):
                    print("Campos para revisar:")
                    for item in relatorio_hibrido['campos_revisar']:
                        print(f"  - {item['campo']}: {item.get('valor')} ({item['motivo']})")
                print()
            else:
                print("✗ Nenhum dado foi extraído\n")
                return None
        
        # Salva no banco
        sucesso, mensagem = ContratoProcessor.save_contrato(dados, dry_run=dry_run)
        
        if sucesso:
            print(f"✓ {mensagem} | {_resumo_hibrido(relatorio_hibrido)}")
        else:
            print(f"✗ {mensagem}")
        
        return dados
        
    except Exception as e:
        print(f"\n✗ Erro: {str(e)}", file=sys.stderr)
        return None

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nExemplos de uso:")
        print("  python ocr_processor_cli.py ./pdfs")
        print("  python ocr_processor_cli.py ./pdfs --dry-run")
        print("  python ocr_processor_cli.py ./contrato.pdf")
        sys.exit(1)
    
    alvo = sys.argv[1]
    dry_run = '--dry-run' in sys.argv or '-t' in sys.argv
    
    alvo_path = Path(alvo)
    
    if not alvo_path.exists():
        print(f"✗ Arquivo/pasta não encontrada: {alvo}")
        sys.exit(1)
    
    if alvo_path.is_file():
        # Processa arquivo único
        processar_arquivo_unico(str(alvo_path), dry_run=dry_run)
    else:
        # Processa pasta
        processar_pasta(str(alvo_path), dry_run=dry_run)
