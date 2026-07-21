#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Extract text from PDF 1234 to see original contract data"""

import pdfplumber

pdf_path = r'C:\Users\fabri\cofluhab\cofluhab\manual\1234.pdf'

try:
    with pdfplumber.open(pdf_path) as pdf:
        print(f"Total de páginas: {len(pdf.pages)}")
        print("=" * 80)
        
        # Extrai texto da primeira página apenas
        page = pdf.pages[0]
        text = page.extract_text(layout=False)
        
        # Limpa caracteres problemáticos
        text = text.encode('utf-8', errors='replace').decode('utf-8')
        
        print("\nPÁGINA 1:")
        print(text[:5000])  # Primeiros 5000 caracteres
            
except Exception as e:
    import traceback
    print(f"Erro ao ler PDF: {e}")
    traceback.print_exc()
