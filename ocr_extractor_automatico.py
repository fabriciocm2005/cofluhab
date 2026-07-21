#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OCR Extractor Automático para Contratos BNH/SFH
Extrai automaticamente campos do PDF usando EasyOCR
Valida contra dados já no banco de dados
"""

import os
import sys
import re
from pathlib import Path
from decimal import Decimal
from datetime import datetime
import easyocr
from pdf2image import convert_from_path
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato

class ContratoOCRExtractor:
    """Extrai automaticamente dados de contrato do PDF"""
    
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.reader = easyocr.Reader(['pt'], gpu=False)  # Portuguese language
        self.text_full = None
        self.fields_extracted = {}
        
    def extrair(self):
        """Extrai todos os campos do PDF"""
        print(f"🔄 Processando PDF: {self.pdf_path}")
        
        # Converte PDF para imagens
        try:
            images = convert_from_path(self.pdf_path, dpi=300)
            print(f"✅ PDF convertido: {len(images)} páginas")
        except Exception as e:
            print(f"❌ Erro ao converter PDF: {e}")
            return False
        
        # Processa cada página com OCR
        all_text = []
        for idx, image in enumerate(images):
            print(f"  Processando página {idx + 1}/{len(images)}...", end=" ", flush=True)
            
            try:
                results = self.reader.readtext(image, detail=0)
                page_text = "\n".join(results)
                all_text.append(page_text)
                print("✓")
            except Exception as e:
                print(f"✗ ({e})")
        
        self.text_full = "\n".join(all_text)
        
        print(f"\n📄 Texto extraído: {len(self.text_full)} caracteres\n")
        
        # Extrai campos específicos
        self._extrair_campos()
        
        return True
    
    def _extrair_campos(self):
        """Extrai campos estruturados do texto"""
        
        print("=" * 100)
        print("CAMPOS EXTRAÍDOS")
        print("=" * 100)
        
        # DATA PRIMEIRA PRESTAÇÃO (padrão: 30/11/1984 ou 30/11/84)
        data_prest = self._extrair_data_primeira_prestacao()
        if data_prest:
            self.fields_extracted['data_primeiro_venc'] = data_prest
            print(f"✅ Data primeira prestação: {data_prest}")
        else:
            print(f"❌ Data primeira prestação: NÃO ENCONTRADA")
        
        # PRESTAÇÃO TOTAL COM ACESSÓRIOS (padrão: 195.769,99 ou 195769,99)
        prestacao = self._extrair_prestacao_total()
        if prestacao:
            self.fields_extracted['prestacao_inicial'] = prestacao
            print(f"✅ Prestação total: {prestacao}")
        else:
            print(f"❌ Prestação total: NÃO ENCONTRADA")
        
        # PRAZO EM MESES (padrão: 120 meses)
        prazo = self._extrair_prazo()
        if prazo:
            self.fields_extracted['prazo'] = prazo
            print(f"✅ Prazo: {prazo} meses")
        else:
            print(f"❌ Prazo: NÃO ENCONTRADO")
        
        # TAXA DE JUROS (padrão: 10,00% ou 10.00%)
        tx_juros = self._extrair_taxa_juros()
        if tx_juros:
            self.fields_extracted['tx_juros'] = tx_juros
            print(f"✅ Taxa de juros: {tx_juros}% a.a.")
        else:
            print(f"❌ Taxa de juros: NÃO ENCONTRADA")
        
        # PRESTAÇÃO BASE (SEM ACESSÓRIOS)
        prestacao_base = self._extrair_prestacao_base()
        if prestacao_base:
            self.fields_extracted['prestacao_base'] = prestacao_base
            print(f"✅ Prestação base: {prestacao_base}")
        else:
            print(f"❌ Prestação base: NÃO ENCONTRADA")
        
        print()
    
    def _extrair_data_primeira_prestacao(self):
        """Extrai data primeira prestação em formato DD/MM/YYYY"""
        # Procura por padrões como "30/11/1984" ou "30/11/84"
        patterns = [
            r'(?:data\s+da\s+1[aª].*?prestação|primeira\s+prestação).*?(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})',
            r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})',  # Genérico
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, self.text_full, re.IGNORECASE)
            for match in matches:
                try:
                    dia, mes, ano = int(match[0]), int(match[1]), int(match[2])
                    
                    # Normaliza ano (84 -> 1984)
                    if ano < 100:
                        ano = 1900 + ano if ano > 50 else 2000 + ano
                    
                    # Valida
                    if 1 <= mes <= 12 and 1 <= dia <= 31:
                        # Formato esperado para banco
                        return f"{ano:04d}-{mes:02d}-{dia:02d}"
                except:
                    continue
        
        return None
    
    def _extrair_prestacao_total(self):
        """Extrai prestação total (com acessórios)"""
        # Procura por "totalizando" ou "total" seguido de valor em Cr$
        patterns = [
            r'totalizando.*?(?:Cr\$)?\s*(\d+[.,]\d{3}[.,]\d{2})',
            r'(?:prestação|total).*?(?:Cr\$)?\s*(\d+[.,]\d{3}[.,]\d{2})',
            r'(?:Cr\$)\s*(\d+[.,]\d{3}[.,]\d{2})',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, self.text_full, re.IGNORECASE)
            for valor_str in matches:
                try:
                    # Converte "195.769,99" ou "195,769.99" para Decimal
                    valor_limpo = valor_str.replace('.', '').replace(',', '.')
                    valor = Decimal(valor_limpo)
                    
                    # Validação: prestação deve estar entre 100 e 1000000
                    if 100 < valor < 1000000:
                        return float(valor)
                except:
                    continue
        
        return None
    
    def _extrair_prazo(self):
        """Extrai prazo em meses"""
        patterns = [
            r'prazo.*?(\d{2,3})\s*(?:meses?|m)',
            r'(\d{2,3})\s*(?:meses?|m)\s*(?:de|no|prazo)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, self.text_full, re.IGNORECASE)
            for valor in matches:
                try:
                    prazo = int(valor)
                    if 12 <= prazo <= 360:  # Válido: 1 a 30 anos
                        return prazo
                except:
                    continue
        
        return None
    
    def _extrair_taxa_juros(self):
        """Extrai taxa de juros nominal"""
        patterns = [
            r'taxa.*?juros.*?(\d+[.,]\d{2})\s*%',
            r'(\d+[.,]\d{2})\s*%\s*a\.a',
            r'(\d+[.,]\d{2})\s*(?:por\s+cento|%)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, self.text_full, re.IGNORECASE)
            for valor in matches:
                try:
                    tx = float(valor.replace(',', '.'))
                    if 0 < tx < 50:  # Válido: taxa entre 0 e 50% a.a.
                        return tx
                except:
                    continue
        
        return None
    
    def _extrair_prestacao_base(self):
        """Extrai prestação base (sem acessórios)"""
        patterns = [
            r'prestação\s*(?:base|mensal).*?(?:Cr\$)?\s*(\d+[.,]\d{2,6})',
            r'(?:Cr\$)\s*(\d+[.,]\d{2,6})\s*(?:prestação|base)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, self.text_full, re.IGNORECASE)
            for valor_str in matches:
                try:
                    valor_limpo = valor_str.replace('.', '').replace(',', '.')
                    valor = Decimal(valor_limpo)
                    
                    # Validação
                    if 100 < valor < 100000:
                        return float(valor)
                except:
                    continue
        
        return None
    
    def validar_contra_banco(self, codigo_contrato):
        """Valida campos extraídos contra dados no banco"""
        
        print("=" * 100)
        print("VALIDAÇÃO CONTRA BANCO DE DADOS")
        print("=" * 100)
        
        try:
            contrato = Contrato.objects.get(codigo=codigo_contrato)
        except Contrato.DoesNotExist:
            print(f"❌ Contrato {codigo_contrato} não encontrado no banco")
            return False
        
        erros = []
        
        # Valida data_primeiro_venc
        if 'data_primeiro_venc' in self.fields_extracted:
            data_ocr = self.fields_extracted['data_primeiro_venc']
            data_banco = contrato.data_primeiro_venc.isoformat() if contrato.data_primeiro_venc else None
            
            if data_banco:
                match = "✅" if data_ocr == data_banco else "❌"
                print(f"{match} Data primeira prestação:")
                print(f"    OCR:   {data_ocr}")
                print(f"    Banco: {data_banco}")
                if data_ocr != data_banco:
                    erros.append(f"Data primeira prestação diverge")
            else:
                print(f"⚠️  Data primeira prestação não está no banco")
        
        # Valida prestacao_inicial
        if 'prestacao_inicial' in self.fields_extracted:
            prestacao_ocr = self.fields_extracted['prestacao_inicial']
            prestacao_banco = float(contrato.prestacao_inicial) if contrato.prestacao_inicial else None
            
            if prestacao_banco:
                diferenca_pct = abs(prestacao_ocr - prestacao_banco) / prestacao_banco * 100
                match = "✅" if diferenca_pct < 1 else "❌"
                print(f"{match} Prestação inicial:")
                print(f"    OCR:   {prestacao_ocr:.2f}")
                print(f"    Banco: {prestacao_banco:.2f}")
                print(f"    Diferença: {diferenca_pct:.2f}%")
                if diferenca_pct >= 1:
                    erros.append(f"Prestação inicial diverge {diferenca_pct:.2f}%")
            else:
                print(f"⚠️  Prestação inicial não está no banco")
        
        # Valida prazo
        if 'prazo' in self.fields_extracted:
            prazo_ocr = self.fields_extracted['prazo']
            prazo_banco = contrato.prazo
            
            match = "✅" if prazo_ocr == prazo_banco else "❌"
            print(f"{match} Prazo:")
            print(f"    OCR:   {prazo_ocr}")
            print(f"    Banco: {prazo_banco}")
            if prazo_ocr != prazo_banco:
                erros.append(f"Prazo diverge")
        
        # Valida tx_juros
        if 'tx_juros' in self.fields_extracted:
            tx_ocr = self.fields_extracted['tx_juros']
            tx_banco = float(contrato.tx_juros)
            
            diferenca = abs(tx_ocr - tx_banco)
            match = "✅" if diferenca < 0.01 else "❌"
            print(f"{match} Taxa de juros:")
            print(f"    OCR:   {tx_ocr}%")
            print(f"    Banco: {tx_banco}%")
            if diferenca >= 0.01:
                erros.append(f"Taxa de juros diverge")
        
        print()
        
        if erros:
            print(f"❌ {len(erros)} erro(s) encontrado(s):")
            for erro in erros:
                print(f"   - {erro}")
            return False
        else:
            print(f"✅ TODOS OS CAMPOS VALIDARAM!")
            return True


def main():
    pdf_path = r"C:\Users\fabri\cofluhab\cofluhab\manual\1234.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF não encontrado: {pdf_path}")
        sys.exit(1)
    
    # Extrai dados
    extractor = ContratoOCRExtractor(pdf_path)
    if not extractor.extrair():
        sys.exit(1)
    
    # Valida contra banco
    print()
    extractor.validar_contra_banco("1234")


if __name__ == "__main__":
    main()
