#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OCR Extractor Rápido - Usando pdfplumber + regex patterns otimizados
"""

import os
import sys
import re
from decimal import Decimal
from datetime import datetime
import pdfplumber
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato

class ContratoExtractorRapido:
    """Extrator rápido usando pdfplumber"""
    
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.text_full = ""
        self.fields_extracted = {}
        
    def extrair(self):
        """Extrai campos do PDF"""
        print(f"[PROCESSANDO] PDF: {self.pdf_path}")
        
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                print(f"[OK] PDF aberto: {len(pdf.pages)} paginas\n")
                
                # Extrai texto de todas as páginas
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        text = page.extract_text() or ""
                        self.text_full += text + "\n"
                        print(f"  Pagina {page_num}: {len(text)} caracteres")
                    except Exception as e:
                        print(f"  Pagina {page_num}: Erro ({e})")
        
        except Exception as e:
            print(f"[ERRO] ao abrir PDF: {e}")
            return False
        
        print(f"\n[INFO] Total extraido: {len(self.text_full)} caracteres\n")
        
        # Limpa alguns caracteres problemáticos
        self.text_full = self.text_full.replace('\x00', '')
        
        # Extrai campos
        self._extrair_campos()
        
        return True
    
    def _extrair_campos(self):
        """Extrai campos estruturados"""
        
        print("=" * 100)
        print("CAMPOS EXTRAIDOS")
        print("=" * 100)
        
        # DATA PRIMEIRA PRESTAÇÃO
        data = self._extrair_data_primeira_prestacao()
        if data:
            self.fields_extracted['data_primeiro_venc'] = data
            print(f"[OK] Data primeira prestacao: {data}")
        else:
            print(f"[NAO_ENCONTRADO] Data primeira prestacao")
        
        # PRESTAÇÃO TOTAL
        prestacao = self._extrair_prestacao_total()
        if prestacao:
            self.fields_extracted['prestacao_inicial'] = prestacao
            print(f"[OK] Prestacao total: {prestacao}")
        else:
            print(f"[NAO_ENCONTRADO] Prestacao total")
        
        # PRAZO
        prazo = self._extrair_prazo()
        if prazo:
            self.fields_extracted['prazo'] = prazo
            print(f"[OK] Prazo: {prazo} meses")
        else:
            print(f"[NAO_ENCONTRADO] Prazo")
        
        # TAXA DE JUROS
        tx = self._extrair_taxa_juros()
        if tx:
            self.fields_extracted['tx_juros'] = tx
            print(f"[OK] Taxa juros: {tx}% a.a.")
        else:
            print(f"[NAO_ENCONTRADO] Taxa juros")
        
        # PRESTAÇÃO BASE
        prest_base = self._extrair_prestacao_base()
        if prest_base:
            self.fields_extracted['prestacao_base'] = prest_base
            print(f"[OK] Prestacao base: {prest_base}")
        else:
            print(f"[NAO_ENCONTRADO] Prestacao base")
        
        print()
    
    def _extrair_data_primeira_prestacao(self):
        """Extrai data primeira prestação"""
        # Procura a seção de "DATA DA PRIMEIRA PRESTAÇÃO"
        patterns = [
            r'[Dd]ata\s+(?:d[oa]|da)\s+(?:1[ªa]|primeira)\s+(?:pre|prest).*?(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})',
            r'(?:primeira|1a|1ª)\s+prestação.*?(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})',
            r'(\d{1,2})/(\d{1,2})/(\d{2,4})',  # Genérico
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.text_full, re.IGNORECASE)
            if match:
                try:
                    dia, mes, ano = int(match.group(1)), int(match.group(2)), int(match.group(3))
                    
                    # Normaliza ano
                    if ano < 100:
                        ano = 1900 + ano if ano > 50 else 2000 + ano
                    
                    # Valida
                    if 1 <= mes <= 12 and 1 <= dia <= 31:
                        return f"{ano:04d}-{mes:02d}-{dia:02d}"
                except:
                    pass
        
        return None
    
    def _extrair_prestacao_total(self):
        """Extrai prestação total com acessórios"""
        # Procura valor próximo a "totalizando" ou "total"
        patterns = [
            r'(?:tota|total).*?(?:Cr\$|CR\$)?\s*(\d{1,3}[.,]\d{3}[.,]\d{2})',
            r'(?:Cr\$|CR\$)\s*(\d{1,3}[.,]\d{3}[.,]\d{2})',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, self.text_full, re.IGNORECASE)
            for valor in matches:
                try:
                    # Converte 195.769,99 para 195769.99
                    v_limpo = valor.replace('.', '').replace(',', '.')
                    v = Decimal(v_limpo)
                    
                    # Validação: deve ser > 100 e < 1M
                    if 100 < v < 1000000:
                        return float(v)
                except:
                    pass
        
        return None
    
    def _extrair_prazo(self):
        """Extrai prazo em meses"""
        patterns = [
            r'([0-9]{2,3})\s*(?:meses?|m)\s*(?:de\s+(?:prazo|amortizacao)|referentes?)',
            r'[Pp]razo.*?([0-9]{2,3})\s*(?:meses?|m)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, self.text_full)
            for valor in matches:
                try:
                    p = int(valor)
                    if 12 <= p <= 360:
                        return p
                except:
                    pass
        
        return None
    
    def _extrair_taxa_juros(self):
        """Extrai taxa de juros"""
        patterns = [
            r'(?:taxa|juros).*?([0-9]+[.,][0-9]{2})\s*%',
            r'([0-9]+[.,][0-9]{2})\s*%\s*(?:a\.a|ao\s+ano)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, self.text_full, re.IGNORECASE)
            for valor in matches:
                try:
                    tx = float(valor.replace(',', '.'))
                    if 0 < tx < 50:
                        return tx
                except:
                    pass
        
        return None
    
    def _extrair_prestacao_base(self):
        """Extrai prestação base (sem acessórios)"""
        patterns = [
            r'(?:prestacao|prest)\s+(?:base|mensal).*?(?:Cr\$)?\s*([0-9]{1,3}[.,][0-9]{2,6})',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, self.text_full, re.IGNORECASE)
            for valor in matches:
                try:
                    v_limpo = valor.replace('.', '').replace(',', '.')
                    v = Decimal(v_limpo)
                    
                    if 100 < v < 500000:
                        return float(v)
                except:
                    pass
        
        return None
    
    def validar(self, codigo):
        """Valida contra banco"""
        
        print("=" * 100)
        print("VALIDACAO CONTRA BANCO")
        print("=" * 100)
        
        try:
            c = Contrato.objects.get(codigo=codigo)
        except:
            print(f"[ERRO] Contrato {codigo} nao encontrado")
            return False
        
        print(f"Contrato: {c.codigo}")
        print(f"ID: {c.id}")
        print()
        
        sucesso = True
        
        # DATA
        if 'data_primeiro_venc' in self.fields_extracted:
            ocr_val = self.fields_extracted['data_primeiro_venc']
            db_val = str(c.data_primeiro_venc) if c.data_primeiro_venc else None
            
            match = ocr_val == db_val
            icon = "[OK]" if match else "[ERRO]"
            print(f"{icon} Data primeiro venc: OCR={ocr_val} | DB={db_val}")
            if not match:
                sucesso = False
        
        # PRESTAÇÃO
        if 'prestacao_inicial' in self.fields_extracted:
            ocr_val = self.fields_extracted['prestacao_inicial']
            db_val = float(c.prestacao_inicial) if c.prestacao_inicial else None
            
            if db_val:
                diff_pct = abs(ocr_val - db_val) / db_val * 100
                match = diff_pct < 1
                icon = "[OK]" if match else "[ERRO]"
                print(f"{icon} Prestacao: OCR={ocr_val:.2f} | DB={db_val:.2f} (diff={diff_pct:.2f}%)")
                if not match:
                    sucesso = False
        
        # PRAZO
        if 'prazo' in self.fields_extracted:
            ocr_val = self.fields_extracted['prazo']
            db_val = c.prazo
            
            match = ocr_val == db_val
            icon = "[OK]" if match else "[ERRO]"
            print(f"{icon} Prazo: OCR={ocr_val} | DB={db_val}")
            if not match:
                sucesso = False
        
        # TAXA
        if 'tx_juros' in self.fields_extracted:
            ocr_val = self.fields_extracted['tx_juros']
            db_val = float(c.tx_juros)
            
            match = abs(ocr_val - db_val) < 0.01
            icon = "[OK]" if match else "[ERRO]"
            print(f"{icon} Taxa juros: OCR={ocr_val:.2f}% | DB={db_val:.2f}%")
            if not match:
                sucesso = False
        
        print()
        return sucesso


def main():
    pdf_path = r"C:\Users\fabri\cofluhab\cofluhab\manual\1234.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"[ERRO] PDF nao encontrado: {pdf_path}")
        return
    
    extrator = ContratoExtractorRapido(pdf_path)
    
    if extrator.extrair():
        print()
        if extrator.validar("1234"):
            print("[SUCESSO] VALIDACAO OK - EXTRACAO FUNCIONANDO!")
        else:
            print("[FALHA] Ha divergencias - verificar patterns")


if __name__ == "__main__":
    main()
