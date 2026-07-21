#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Extract specific data from PDF 1234"""

import pdfplumber

pdf_path = r'C:\Users\fabri\cofluhab\cofluhab\manual\1234.pdf'

try:
    with pdfplumber.open(pdf_path) as pdf:
        # Procura por padrões nas páginas
        print("=" * 80)
        print("BUSCANDO DATA DA PRIMEIRA PRESTAÇÃO E OUTROS DADOS")
        print("=" * 80)
        
        for page_num in range(len(pdf.pages)):
            page = pdf.pages[page_num]
            text = page.extract_text(layout=False)
            
            # Procura por palavras-chave
            if 'primeira prestacao' in text.lower() or 'primeira prestação' in text.lower() or '30/11' in text or '1984' in text:
                print(f"\n[PÁGINA {page_num + 1}] Encontrou referência à data/primeira prestação:")
                
                # Limpa e mostra
                text_clean = text.encode('utf-8', errors='replace').decode('utf-8')
                
                # Mostra apenas as linhas relevantes
                for line in text_clean.split('\n'):
                    if any(keyword in line.lower() for keyword in ['primeira', 'prestacao', 'venc', '30/', '11/', '84', '1984']):
                        print(f"  {line.strip()}")
            
            # Também procura por "1983" ou "1984"
            if '1983' in text or '1984' in text:
                print(f"\n[PÁGINA {page_num + 1}] Encontrou ano 1983/1984")
                text_clean = text.encode('utf-8', errors='replace').decode('utf-8')
                for line in text_clean.split('\n'):
                    if '1983' in line or '1984' in line or 'venc' in line.lower():
                        print(f"  {line.strip()}")
                
except Exception as e:
    import traceback
    print(f"Erro: {e}")
    traceback.print_exc()
