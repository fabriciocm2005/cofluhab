#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OCR com Tesseract - Melhor extração de dados do PDF 1234
"""

import pdf2image
import pytesseract
import re
from datetime import datetime

pdf_path = r'C:\Users\fabri\cofluhab\cofluhab\manual\1234.pdf'

def extrair_com_tesseract():
    """Extrai dados usando Tesseract OCR em imagens do PDF"""
    
    dados = {}
    
    try:
        # Converte PDF em imagens (uma por página)
        print("Convertendo PDF em imagens...")
        imagens = pdf2image.convert_from_path(pdf_path)
        
        print(f"Total de páginas: {len(imagens)}")
        print()
        
        # Processa cada página
        texto_completo = ""
        
        for i, imagem in enumerate(imagens):
            print(f"[Processando página {i+1}/{len(imagens)}...]")
            
            # Aplica Tesseract OCR
            texto_pagina = pytesseract.image_to_string(imagem, lang='por')
            texto_completo += texto_pagina + "\n"
        
        print()
        print("=" * 100)
        print("TEXTO COMPLETO EXTRAÍDO (Primeira página)")
        print("=" * 100)
        print()
        
        # Mostra primeiras 3000 caracteres
        print(texto_completo[:3000])
        print()
        
        # Busca por padrões importantes
        print("=" * 100)
        print("EXTRAÇÃO DE CAMPOS IMPORTANTES")
        print("=" * 100)
        print()
        
        # Data primeira prestação
        print("[BUSCANDO] Data primeira prestação (formato DD/MM/YY ou DD/MM/YYYY):")
        matches = re.findall(r'\d{1,2}/\d{1,2}/\d{2,4}', texto_completo)
        if matches:
            print(f"  Encontradas datas: {set(matches)}")
        
        # Valores em Cruzados
        print()
        print("[BUSCANDO] Valores em Cr$:")
        matches = re.findall(r'Cr\$\s*[\d.,]+', texto_completo)
        if matches:
            for m in matches[:10]:
                print(f"  {m}")
        
        # Prestações
        print()
        print("[BUSCANDO] Prestação inicial:")
        matches = re.findall(r'prestação.*?(\d+[.,]\d+)', texto_completo, re.IGNORECASE)
        if matches:
            for m in matches[:5]:
                print(f"  {m}")
        
        # Dados UCPs/UPC
        print()
        print("[BUSCANDO] UPC:")
        matches = re.findall(r'UPC.*?(\d+[.,]\d+)', texto_completo, re.IGNORECASE)
        if matches:
            for m in matches[:5]:
                print(f"  {m}")
        
        # Prazo
        print()
        print("[BUSCANDO] Prazo em meses:")
        matches = re.findall(r'(\d{2,3})\s+meses', texto_completo, re.IGNORECASE)
        if matches:
            print(f"  {set(matches)}")
        
        # Taxa de juros
        print()
        print("[BUSCANDO] Taxa de juros:")
        matches = re.findall(r'(\d+[.,]\d+)\s*%?\s*a\.a\.', texto_completo, re.IGNORECASE)
        if matches:
            print(f"  {set(matches[:10])}")
        
        return texto_completo
        
    except Exception as e:
        import traceback
        print(f"Erro: {e}")
        traceback.print_exc()

if __name__ == '__main__':
    extrair_com_tesseract()
