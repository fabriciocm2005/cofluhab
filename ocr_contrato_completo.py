#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OCR COMPLETO DO CONTRATO 1234
Extrai TODOS os campos necessários para simulação, CADMUT, FH1
"""

import pdfplumber
import re
from datetime import datetime

pdf_path = r'C:\Users\fabri\cofluhab\cofluhab\manual\1234.pdf'

def extrair_dados_contrato():
    """Extrai todos os campos do contrato"""
    
    dados = {}
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print("=" * 100)
            print("OCR COMPLETO - CONTRATO 1234")
            print("=" * 100)
            print()
            
            # Combina texto de todas as páginas
            texto_completo = ""
            for page in pdf.pages:
                texto_completo += page.extract_text() + "\n"
            
            # Limpa encoding
            texto_completo = texto_completo.encode('utf-8', errors='replace').decode('utf-8')
            
            # ===== SEÇÃO I: DADOS DO IMÓVEL =====
            print("SEÇÃO I - DADOS DO IMÓVEL")
            print("-" * 100)
            
            # Endereço
            match = re.search(r'sito à\s*([^,]+),\s*n[º°]?\s*(\d+)', texto_completo, re.IGNORECASE)
            if match:
                dados['endereco_rua'] = match.group(1).strip()
                dados['endereco_numero'] = match.group(2).strip()
                print(f"  Endereço: {dados['endereco_rua']}, {dados['endereco_numero']}")
            
            # Município
            match = re.search(r'Município:\s*([^,\n]+)', texto_completo, re.IGNORECASE)
            if match:
                dados['municipio'] = match.group(1).strip()
                print(f"  Município: {dados['municipio']}")
            
            print()
            
            # ===== SEÇÃO II: DADOS DO MUTUÁRIO =====
            print("SEÇÃO II - DADOS DO MUTUÁRIO")
            print("-" * 100)
            
            # Procura por padrão de nome (geralmente ANTES de "declara(m)")
            match = re.search(r'O\(s\)\s+COMPRADOR\(es\)\s+([^d]+?)\s+declara', texto_completo, re.IGNORECASE | re.DOTALL)
            if match:
                nome = match.group(1).strip()
                # Limpa quebras de linha
                nome = ' '.join(nome.split())
                dados['mutuario_nome'] = nome
                print(f"  Mutuário: {nome}")
            
            print()
            
            # ===== SEÇÃO IV: PREÇO DE VENDA =====
            print("SEÇÃO IV - PREÇO DE VENDA")
            print("-" * 100)
            
            # Valor de venda (Cr$)
            match = re.search(r'Preço de Venda:\s*Cr\$\s*\(([^)]+)\)', texto_completo, re.IGNORECASE)
            if match:
                valor_texto = match.group(1).strip()
                dados['preco_venda_texto'] = valor_texto
                print(f"  Preço de Venda (texto): {valor_texto}")
            
            print()
            
            # ===== SEÇÃO V: CONDIÇÕES DE PAGAMENTO =====
            print("SEÇÃO V - CONDIÇÕES DE PAGAMENTO")
            print("-" * 100)
            
            # Prazo (meses)
            match = re.search(r'Será feito em\s*\.{2,}\s*(\d+)\s*\.{2,}\s*meses', texto_completo, re.IGNORECASE)
            if match:
                dados['prazo_meses'] = int(match.group(1))
                print(f"  Prazo: {dados['prazo_meses']} meses")
            
            # Taxa de juros nominal (a.a.)
            match = re.search(r'taxa de juros nominal de\s*\.{2,}\s*(\d+[.,]\d+)\s*\.{2,}\s*a\.a\.', texto_completo, re.IGNORECASE)
            if match:
                tx_nominal = match.group(1).replace(',', '.')
                dados['tx_juros_nominal'] = float(tx_nominal)
                print(f"  Taxa juros nominal: {dados['tx_juros_nominal']}% a.a.")
            
            # Taxa efetiva (a.a.)
            match = re.search(r'taxa efetiva\s*"a\.a\.,\s*presta', texto_completo, re.IGNORECASE)
            print(f"  Taxa efetiva: [valor cortado no OCR]")
            
            # Prestação inicial (Cr$)
            match = re.search(r'sendo a inicial de Cr\$\s*(\d+[.,]\d+)', texto_completo, re.IGNORECASE)
            if match:
                prest_base = match.group(1).replace(',', '.')
                dados['prestacao_base'] = float(prest_base)
                print(f"  Prestação base: {dados['prestacao_base']} Cr$")
            
            # Data primeira prestação
            match = re.search(r'vencendo-se a primeira prestação em\s*\.{2,}\s*(\d{1,2})\s*/\s*\.{2,}\s*(\d{1,2})\s*/\s*\.{2,}\s*(\d{2})', texto_completo, re.IGNORECASE)
            if match:
                dia = match.group(1)
                mes = match.group(2)
                ano = match.group(3)
                # Converte para ano 4 dígitos
                if int(ano) < 50:
                    ano = '20' + ano
                else:
                    ano = '19' + ano
                dados['data_primeira_prestacao'] = f"{ano}-{mes.zfill(2)}-{dia.zfill(2)}"
                print(f"  Primeira prestação: {dados['data_primeira_prestacao']}")
            
            # Número UPC
            match = re.search(r'UPC\s+vigentes?\s+nesta\s+data.*?(\d+\.?\d+)', texto_completo, re.IGNORECASE | re.DOTALL)
            if match:
                dados['upc_contrato'] = match.group(1)
                print(f"  UPC contrato: {dados['upc_contrato']}")
            
            print()
            
            # ===== SEÇÃO VI: ACESSÓRIOS DE PAGAMENTO =====
            print("SEÇÃO VI - ACESSÓRIOS DE PAGAMENTO")
            print("-" * 100)
            
            # Seguros
            match = re.search(r'Seguros BNH/SFH\s*-\s*MIP\s*\.{2,}\s*Cr\$\s*\.{2,}\s*(\d+[.,]\d+)', texto_completo, re.IGNORECASE)
            if match:
                seguro_mip = match.group(1).replace(',', '.')
                dados['seguro_mip'] = float(seguro_mip)
                print(f"  Seguro MIP: {dados['seguro_mip']} Cr$")
            
            # D. Fis
            match = re.search(r'D\.\s*Fis\s+Cr\$\s*\.{2,}\s*(\d+[.,]\d+)', texto_completo, re.IGNORECASE)
            if match:
                d_fis = match.group(1).replace(',', '.')
                dados['d_fis'] = float(d_fis)
                print(f"  D. Fis: {dados['d_fis']} Cr$")
            
            # Total Seguros
            match = re.search(r'Total Seguros\s+Cr\$\s*\.{2,}\s*(\d+[.,]\d+)', texto_completo, re.IGNORECASE)
            if match:
                total_seguros = match.group(1).replace(',', '.')
                dados['total_seguros'] = float(total_seguros)
                print(f"  Total Seguros: {dados['total_seguros']} Cr$")
            
            # Taxa de Cobrança e Adminis
            match = re.search(r'Taxa de Cobrança.*?Adminis\s+Cr\$\s*\.{2,}\s*(\d+[.,]\d+)', texto_completo, re.IGNORECASE | re.DOTALL)
            if match:
                taxa_cobranca = match.group(1).replace(',', '.')
                dados['taxa_cobranca'] = float(taxa_cobranca)
                print(f"  Taxa Cobrança: {dados['taxa_cobranca']} Cr$")
            
            # Total prestação + acessórios
            match = re.search(r'totalizando prestação mais acessório nesta data em\s*\.{2,}\s*Cr\$\s*\.{2,}\s*(\d+[.,]\d+)', texto_completo, re.IGNORECASE)
            if match:
                total_prest = match.group(1).replace(',', '.')
                dados['prestacao_total_com_acessorios'] = float(total_prest)
                print(f"  Prestação + acessórios: {dados['prestacao_total_com_acessorios']} Cr$")
            
            print()
            
            # ===== SEÇÃO VIII: DATA DO CONTRATO =====
            print("DATA DO CONTRATO")
            print("-" * 100)
            
            # Data de assinatura (geralmente em ESPAÇO PARA FIRMAS)
            # Busca por padrão "de __ de _______ de 19__"
            match = re.search(r'de\s+(\d{1,2})\s+de\s+([a-záéíóú]+)\s+de\s+(19\d{2})', texto_completo, re.IGNORECASE)
            if match:
                dia = match.group(1)
                mes_nome = match.group(2).lower()
                ano = match.group(3)
                
                # Converte mês nome para número
                meses = {
                    'janeiro': '01', 'fevereiro': '02', 'março': '03', 'abril': '04',
                    'maio': '05', 'junho': '06', 'julho': '07', 'agosto': '08',
                    'setembro': '09', 'outubro': '10', 'novembro': '11', 'dezembro': '12'
                }
                mes_num = meses.get(mes_nome, '00')
                
                dados['data_assinatura'] = f"{ano}-{mes_num}-{dia.zfill(2)}"
                print(f"  Data assinatura: {dados['data_assinatura']}")
            
            print()
            print("=" * 100)
            print("RESUMO DOS DADOS EXTRAÍDOS")
            print("=" * 100)
            print()
            
            for chave, valor in sorted(dados.items()):
                print(f"  {chave:40s} = {valor}")
            
            return dados
            
    except Exception as e:
        import traceback
        print(f"Erro: {e}")
        traceback.print_exc()
        return dados

if __name__ == '__main__':
    extrair_dados_contrato()
