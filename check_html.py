#!/usr/bin/env python
"""Fetch the actual HTML from the server and search for data"""

import requests
import re

url = "http://127.0.0.1:8000/contrato/6206/"

try:
    response = requests.get(url)
    html = response.text
    
    print("=" * 80)
    print("VERIFICANDO HTML RETORNADO PELO SERVIDOR")
    print("=" * 80)
    print()
    
    # Procura por padrões importantes
    patterns = {
        "Data primeiro vencimento": r'data_primeiro_venc[^<]*|(\d{1,2}/\d{1,2}/\d{4})',
        "Primeira Parcela": r'Primeira Parcela[^<]*?(\d{1,2}/\d{1,2}/\d{4}|-)',
        "Prestacao/Saldo Inicial": r'Saldo Inicial[^<]*?R\$\s*([\d.,]+)',
        "30/11/1984": r'30/11/(1984|84)',
        "195.769,99": r'195[.,]769[.,]99',
        "182": r'182[.,]33',
    }
    
    for name, pattern in patterns.items():
        matches = re.findall(pattern, html, re.IGNORECASE)
        if matches:
            print(f"[ENCONTRADO] {name}: {matches}")
        else:
            print(f"[NÃO ENCONTRADO] {name}")
    
    print()
    print("=" * 80)
    print("BUSCANDO A SEÇÃO DE DADOS DO CONTRATO (PRIMEIROS 2000 CHARS)")
    print("=" * 80)
    
    # Encontra a seção com os dados do contrato
    data_section = re.search(r'<h2[^>]*>.*?Contrato.*?</h2>(.*?)<table', html, re.DOTALL | re.IGNORECASE)
    if data_section:
        section_text = data_section.group(1)[:2000]
        print(section_text)
    else:
        print("Seção não encontrada")
        
except Exception as e:
    print(f"Erro: {e}")
