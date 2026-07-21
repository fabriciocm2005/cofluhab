#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Debug - mostra o texto extraído do PDF para análise
"""

import pdfplumber
import re

pdf_path = r"C:\Users\fabri\cofluhab\cofluhab\manual\1234.pdf"

output = []

with pdfplumber.open(pdf_path) as pdf:
    for page_num, page in enumerate(pdf.pages, 1):
        text = page.extract_text() or ""
        
        output.append(f"\n{'='*100}")
        output.append(f"PAGINA {page_num}")
        output.append(f"{'='*100}\n")
        output.append(text)
        output.append(f"\n[...FIM PAGINA {page_num}...]\n")
        
        # Procura por padrões específicos
        output.append(f"[BUSCA] Datas encontradas na pagina {page_num}:")
        dates = re.findall(r'\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}', text)
        for d in dates[:10]:
            output.append(f"  {d}")
        
        output.append(f"\n[BUSCA] Valores com 'Cr$' encontrados:")
        valores = re.findall(r'(?:Cr\$|CR\$)?\s*[\d.]+[,.][\d]{2}', text)
        for v in valores[:15]:
            output.append(f"  {v}")
        
        output.append(f"\n[BUSCA] Numeros para prazo (XX ou XXX meses):")
        prazos = re.findall(r'(\d{2,3})\s*(?:meses?|m)\b', text, re.IGNORECASE)
        for p in prazos[:5]:
            output.append(f"  {p} meses")
        
        output.append(f"\n[BUSCA] Linhas com 'prestacao' ou 'juros':")
        for line in text.split('\n'):
            if 'prestac' in line.lower() or 'juros' in line.lower():
                output.append(f"  {line.strip()}")

# Escreve em arquivo
with open(r"C:\Users\fabri\cofluhab\cofluhab\debug_output.txt", 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print("Analise salva em: debug_output.txt")
print(f"Total de linhas: {len(output)}")
