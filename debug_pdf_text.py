#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Debug - mostra o texto extraído do PDF para análise
"""

import pdfplumber
import re

pdf_path = r"C:\Users\fabri\cofluhab\cofluhab\manual\1234.pdf"

with pdfplumber.open(pdf_path) as pdf:
    for page_num, page in enumerate(pdf.pages, 1):
        text = page.extract_text() or ""
        
        print(f"\n{'='*100}")
        print(f"PAGINA {page_num}")
        print(f"{'='*100}\n")
        print(text)
        print(f"\n[...FIM PAGINA {page_num}...]\n")
        
        # Procura por padrões específicos
        print(f"[BUSCA] Datas encontradas na pagina {page_num}:")
        dates = re.findall(r'\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}', text)
        for d in dates:
            print(f"  {d}")
        
        print(f"\n[BUSCA] Valores com 'Cr$' encontrados:")
        valores = re.findall(r'(?:Cr\$|CR\$)\s*[\d.,]+', text, re.IGNORECASE)
        for v in valores[:10]:  # Primeiros 10
            print(f"  {v}")
        
        print(f"\n[BUSCA] Números que parecem 'prazo' (XX ou XXX meses):")
        prazos = re.findall(r'(\d{2,3})\s*(?:meses?|m)\b', text, re.IGNORECASE)
        for p in prazos[:5]:
            print(f"  {p} meses")
        
        input("Pressione ENTER para continuar para a próxima página...")
