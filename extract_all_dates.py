#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Extract all dates from PDF 1234"""

import pdfplumber
import re

pdf_path = r'C:\Users\fabri\cofluhab\cofluhab\manual\1234.pdf'

# Padrão para datas em formato DD/MM/YYYY ou DD/MM/AAAA
date_pattern = r'\d{1,2}/\d{1,2}/\d{4}|\d{1,2}/\d{1,2}/\d{2}'

try:
    with pdfplumber.open(pdf_path) as pdf:
        print("=" * 80)
        print("TODAS AS DATAS ENCONTRADAS NO PDF")
        print("=" * 80)
        
        all_dates = set()
        
        for page_num in range(len(pdf.pages)):
            page = pdf.pages[page_num]
            text = page.extract_text(layout=False)
            text_clean = text.encode('utf-8', errors='replace').decode('utf-8')
            
            # Procura por todas as datas
            dates = re.findall(date_pattern, text_clean)
            if dates:
                print(f"\n[PÁGINA {page_num + 1}]:")
                for date in dates:
                    if date not in all_dates:
                        all_dates.add(date)
                        print(f"  {date}")
        
        print("\n" + "=" * 80)
        print("RESUMO DE DATAS ÚNICAS:")
        print("=" * 80)
        for date in sorted(all_dates):
            print(f"  {date}")
                
except Exception as e:
    import traceback
    print(f"Erro: {e}")
    traceback.print_exc()
