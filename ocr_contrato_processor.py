"""
OCR Processor para Contratos em PDF
Extrai dados de contratos e cadastra automaticamente no sistema
"""

import os
import re
import json
import shutil
import logging
from difflib import get_close_matches
from pathlib import Path
from decimal import Decimal
from datetime import datetime, date
from typing import Dict, List, Tuple, Optional
from dateutil import parser as date_parser
from django.db import transaction
from django.core.exceptions import ValidationError
# pytesseract e pdf2image são importados lazily dentro de _extrair_com_ocr()
# para não falhar na inicialização quando não estiverem instalados.

# Configura logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler('ocr_processamento.log')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Importa modelos Django
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from django.db import connection as _db_connection
from principal.models import Contrato, ConjuntoHabitacional, Mutuario, ParcelaContrato


class ContratoOCRExtractor:
    """
    Extrai dados estruturados de contratos PDF usando OCR
    """
    
    # Padrões de regex para encontrar campos
    PATTERNS = {
        'numero_contrato': [
            # "Contrato nº 1234", "Contrato Nº: ABC-001", "Contrato #XYZ-99"
            r'contrato\s*(?:n[\u00ba°º]?|#)\s*[:=]?\s*([a-z0-9][a-z0-9\-/\.]{1,})',
            # "Nº do contrato: 5555" / "Número contrato 5555"
            r'n[\u00ba°º°]?\s*(?:do\s+)?contrato\s*[:=]?\s*([a-z0-9][a-z0-9\-/\.]{1,})',
            # "Número: 1234" (somente se vier de campo rotulado)
            r'(?:n[\u00ba°º]\.?|n[\u00fameroúm]+)\s*[:=]\s*(\d[\d\-/\.]{1,})',
        ],
        'data_contrato': [
            r'(?:data|date)\s+(?:d[ae]\s+)?assinatura\s*[:=]?\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
            r'assinado?\s+(?:em|on)\s*[:=]?\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
            r'(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})\s+(?:\(|do mês)',
        ],
        'conjunto': [
            r'(?:conjunto|condomínio|empreendimento)\s*[:=]?\s*([a-z0-9\s\-,]+?)(?:\n|contrato)',
            r'(?:local|endereco|address)\s*[:=]?\s*([a-z0-9,\s\-]+?)(?:\n|Mutuário)',
        ],
        'mutuario_nome': [
            r'(?:mutuár?io|beneficiário|contratante|borrower)\s*[:=]?\s*([a-z\s]+?)(?:\n|CPF|RG)',
            r'(?:nome|name)\s*[:=]?\s*([a-z\s]+?)(?:\n)',
        ],
        'cpf': [
            r'(?:CPF|RFC|CIC)\s*[:=]?\s*(\d{3}\.?\d{3}\.?\d{3}-?\d{2})',
            r'(\d{3}\.?\d{3}\.?\d{3}-?\d{2})',
        ],
        'prazo': [
            r'(?:prazo|periodo|período|term)\s*(?:de\s+)?(?:amortização|amortization)\s*[:=]?\s*(\d+)\s*(?:meses|months|anos|years|anos)',
            r'(?:n[\s°º])\s*(?:de\s+)?(?:parcelas|installments)\s*[:=]?\s*(\d+)',
        ],
        'sa': [
            r'(?:SA|Sistema\s+Amortização|amortization\s+system)\s*[:=]?\s*([a-z\s\-]+?)(?:\n|valor)',
            r'(?:tabela|table)\s+(SAC|PRICE|SACRE)',
        ],
        'taxa_juros': [
            r'(?:taxa|rate|juros|interest)\s+(?:de\s+)?(?:juros|interests?)\s*[:=]?\s*([\d,\.]+)\s*%',
            r'([\d,\.]+)\s*%\s*(?:a\.?m|ao\s+mês|ao\s+ano|per\s+annum)',
        ],
        'valor_imovel': [
            r'(?:valor|preço|price|amount)\s+(?:do\s+)?(?:imóvel|imovel|property)\s*[:=]?\s*(?:R\$|$)?\s*([\d\.,]+)',
            r'(?:R\$|$)\s*([\d\.,]+)(?:\s+\(Imóvel|imovel)',
        ],
        'valor_financiado': [
            # Rótulos explícitos — ordem do mais específico para o mais genérico
            r'valor\s+(?:d[oa]\s+)?financiamento\s*[:=]?\s*(?:cr\$\s*)?([\d\.,]+)',
            r'valor\s+financiado\s*[:=]?\s*(?:cr\$|r\$)?\s*([\d\.,]+)',
            r'(?:valor|amount)\s+(?:a\s+)?(?:financiar|financed)\s*[:=]?\s*(?:cr\$|r\$)?\s*([\d\.,]+)',
            r'(?:cr\$|r\$)\s*([\d\.,]+)(?:\s*\(financiado)',
            # BNH antigo: "Cr$ 16.500,00 (Valor do Financiamento)"
            r'(?:cr\$|crs)\s*([\d\.,]+)\s*\(\s*valor\s+d[oa]\s+financiamento',
            # "importância de Cr$ 16.500,00"
            r'import[âa]ncia\s+de\s+(?:cr\$|crs)\s*([\d\.,]+)',
            # "financia a importância de ..."
            r'financia\w*\s+(?:a\s+)?import[âa]ncia\s+de\s+(?:cr\$|crs)?\s*([\d\.,]+)',
            # Quadro BNH: linha "Valor do Financiamento" seguida do valor
            r'valor\s+do\s+financiamento[\s\S]{0,60}?(?:cr\$|crs)\s*([\d\.,]+)',
            # "saldo devedor inicial" / "saldo inicial"
            r'saldo\s+(?:devedor\s+)?inicial\s*[:=]?\s*(?:cr\$|crs|r\$)?\s*([\d\.,]+)',
        ],
        'rg': [
            r'(?:RG|identidade)\s*[:=]?\s*([a-z0-9]+?)(?:\n|estado)',
            r'RG\s+([0-9]+)',
        ],
        'orgao_emissor': [
            r'(?:órgão|orgao)\s+(?:emissor|expedidor)\s*[:=]?\s*([a-z]+)',
            r'(SSP|DETRAN|PM|PC|IFP)',
        ],
        'data_nascimento': [
            r'(?:data\s+de\s+)?nascimento\s*[:=]?\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
            r'(?:nasc|dt nasc|born)\s*[:=]?\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
        ],
        'endereco': [
            r'(?:endereço|endereco|address)\s*[:=]?\s*([a-z0-9\s,\.]+?)(?:\n|número|número)',
            r'(?:rua|avenida|av|alameda)\s+([a-z\s0-9,\.]+)',
        ],
        'numero_imovel': [
            r'(?:número|número|nº|n°)\s*[:=]?\s*(\d+)',
        ],
        'complemento': [
            r'(?:complemento|compl|comp|apt|apto|bloco|lote)\s*[:=]?\s*([a-z0-9\s\-,]+?)(?:\n)',
        ],
        'bairro': [
            r'(?:bairro)\s*[:=]?\s*([a-z\s]+?)(?:\n|cidade|city)',
        ],
        'cidade': [
            r'(?:cidade|city)\s*[:=]?\s*([a-z\s]+?)(?:\n|estado|uf|state)',
        ],
        'uf': [
            r'(?:UF|estado\s+federativo|uf\s+do\s+im[oó]vel)\s*[:=]\s*([a-z]{2})(?!\w)',
            r'\b(AC|AL|AP|AM|BA|CE|DF|ES|GO|MA|MT|MS|MG|PA|PB|PR|PE|PI|RJ|RN|RS|RO|RR|SC|SP|SE|TO)\b',
        ],
        'cep': [
            r'(?:CEP|zip|postal)\s*[:=]?\s*(\d{5}-?\d{3})',
            r'(\d{5}-\d{3})',
        ],
        'telefone': [
            r'(?:telefone|phone|celular|móvel)\s*[:=]?\s*\(?(\d{2})\)?[\s\-]?(\d{4,5})[\s\-]?(\d{4})',
            r'(\(\d{2}\)\s*\d{4,5}-\d{4})',
        ],
        'email': [
            r'(?:email|e-mail|correo)\s*[:=]?\s*([\w\.\-]+@[\w\.\-]+)',
            r'([\w\.\-]+@[\w\.\-]+\.\w+)',
        ],
        # ---- Campos CADMUT / FH1 ----
        'cat_prof': [
            r'(?:categoria\s+profissional|cat\.?\s*prof|categ\.?\s*prof)\s*[:=]\s*([a-z0-9]{1,8})',
            r'(?:código\s+categ|cod\.?\s*cat|categ\s+prof)\s*[:=]\s*([a-z0-9]{1,8})',
        ],
        'pr': [
            r'(?:UF|estado\s+federativo|uf\s+do\s+im[oó]vel)\s*[:=]\s*([a-z]{2})(?!\w)',
            r'\b(AC|AL|AP|AM|BA|CE|DF|ES|GO|MA|MT|MS|MG|PA|PB|PR|PE|PI|RJ|RN|RS|RO|RR|SC|SP|SE|TO)\b',
        ],
        'cep': [
            r'(?:CEP|zip|postal)\s*[:=]?\s*(\d{5}-?\d{3})',
            r'(\d{5}-\d{3})',
        ],
        'data_primeiro_venc': [
            r'(?:data\s+do\s+primeiro\s+pagamento|data\s+do\s+primeiro\s+vencimento|1[ºo]\s+vencimento)\s*[:=]?\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
        ],
        'prazo_fcvs': [
            r'(?:prazo\s+fcvs|prazo\s+para\s+o?\s*fcvs)\s*[:=]?\s*(\d+)\s*(?:meses|months)?',
        ],
        'tipo_operacao': [
            r'(?:tipo\s+(?:de\s+)?opera[çc][aã]o|modalidade\s+operacional)\s*[:=]?\s*([0-9])',
            r'(fds[\-\s]mcmv|com\s+cobertura\s+(?:d[oa]\s+)?fcvs|sem\s+cobertura\s+(?:d[oa]\s+)?fcvs|psh\s+s/\s*desc|psh\s+c/\s*desc|com\s+desc\.?\s*fgts|pro[\-\s]moradia|rec\.?\s*fds|aq\.?\s*dir)',
        ],
        'renda': [
            # Simples: "Renda: 670.000,00" (contratos antigos BNH em Cruzeiros ou reais)
            r'\brenda\s*[:=]\s*(?:cr\$\s*)?(\d{1,3}(?:\.\d{3})*,\d{2})',
            r'(?:renda\s+bruta|renda\s+familiar|renda\s+mensal|renda\s+(?:do\s+)?mutu[aá]rio)\s*[:=]\s*(?:R\$\s*)?(\d[\d\.]*,\d{2})',
            r'(?:renda\s+declarada|comprovante\s+de\s+renda)\s*[:=]\s*(?:R\$\s*)?(\d[\d\.]*,\d{2})',
        ],
        'encargo_mensal': [
            # Valor ANTES do label — aceita formato ruidoso OCR ex: "460,960,00CrSEncargo mensal:"
            r'([\d][\d,\.]{3,12}[\d])\s*(?:cr\$|crs|r\$)?\s*encargo\s+mensal',
            # Valor DEPOIS do label
            r'encargo\s+mensal\s*[:=]\s*(?:cr\$|crs|r\$)?\s*([\d][\d,\.]{2,12}[\d])',
        ],
        'prestacao_reajustada': [
            # "5.3 - Valor da prestação: Amortização e juros: 4.962,00"
            r'5\.3[^\n]{0,80}amortiza[çcpq][aã]o\s+e\s+juros\s*[:=]?\s*(?:cr\$\s*)?([\d]{1,3}(?:\.[\d]{3})*,[\d]{2})',
            # Versão OCR ruidosa: "5.3^4.962,00" ou similar
            r'5\.3\s*[\^~]?\s*(\d{1,3}(?:\.\d{3})*,\d{2})',
        ],
        'crenda': [
            r'(?:renda\s+(?:d[oa]\s+)?cônjuge|renda\s+(?:d[oa]\s+)?conjuge|crenda|renda\s+c[o/])\s*[:=]?\s*(?:R\$\s*)?([\d\.,]+)',
        ],
        'codimovel': [
            r'(?:código\s+(?:d[oa]\s+)?imóvel|cod\.?\s*im[oó]vel|co[ód]\.?\s+imóvel)\s*[:=]?\s*([a-z0-9\-/\.]+)',
            r'(?:n[º°\.]\s*imóvel|num\.?\s*imóvel)\s*[:=]?\s*([a-z0-9\-/\.]+)',
        ],
        'tipoimovel': [
            r'(?:tipo\s+(?:d[oa]\s+)?im[oó]vel|tipo\s+imovel)\s*[:=]?\s*([a-z\s]+?)(?:\n)',
            r'\b(apartamento|apto|casa|sobrado|kitnet|quitinete|flat)\b',
        ],
        'ocorrencia': [
            r'(?:ocorrência|ocorrencia|tipo\s+evento|evento)\s*[:=]?\s*(tpz|set|sit|la2|la3|pxn|liq)',
            r'\b(TPZ|SET|SIT|LA2|LA3|PXN|LIQ)\b',
        ],
        'data_evento': [
            r'(?:data\s+(?:d[oa]\s+)?evento|dt\.?\s*evento)\s*[:=]?\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
            r'(?:data\s+(?:d[ao]\s+)?ocorrência|dt\.?\s*ocorrência)\s*[:=]?\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
        ],
        'situacao_contrato': [
            r'(?:situação|situacao|status)\s+(?:d[oa]\s+)?contrato\s*[:=]?\s*(ativo|inativo|encerrado|cancelado)',
        ],
    }

    def __init__(self, pdf_path: str):
        """Inicializa o extrator com caminho do PDF"""
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF não encontrado: {self.pdf_path}")
        self.text = ""
        self.text_norm = ""
        self.lines_norm = []
        self.data = {}

    def _prepare_text_views(self) -> None:
        """Normaliza o texto extraído para buscas mais estáveis em OCR real."""
        base = (self.text or '').replace('\r', '\n')
        base = re.sub(r'\u00a0', ' ', base)
        base = re.sub(r'[ \t]+', ' ', base)
        base = re.sub(r'\n\s+', '\n', base)
        base = re.sub(r'\s*:\s*', ': ', base)
        base = re.sub(r'\n{2,}', '\n', base)
        self.text_norm = base.strip()
        self.lines_norm = [ln.strip() for ln in self.text_norm.splitlines() if ln.strip()]

    def _score_text_candidate(self, text: str) -> int:
        """Pontua qualidade útil de texto OCR para contratos escaneados."""
        txt = (text or '').lower()
        if len(txt.strip()) < 100:
            return 0

        score = 0
        markers = [
            'taxa de juros',
            'valor do financiamento',
            'vencendo-se a primeira',
            'sendo a inicial',
            'contrato de compra e venda',
            'conjunto residencial',
            'cpf',
            'cic',
            'prazo',
            'meses',
        ]
        for m in markers:
            if m in txt:
                score += 2

        score += min(10, len(re.findall(r'\d{1,2}[\./\-]\d{1,2}[\./\-]\d{2,4}', txt)) * 2)
        score += min(10, len(re.findall(r'(?:cr\$|crs|r\$)\s*[\d\.,]{4,}', txt)) * 2)

        garbage = sum(1 for ch in txt if ch in '^*~<>|\\')
        if garbage > 40:
            score -= 4
        return max(score, 0)

    def _clean_candidate(self, value: str, max_len: int = 120) -> str:
        """Remove caudas de outros rótulos e limpa ruído básico."""
        value = str(value or '').strip(' -:;,')
        value = re.split(
            r'\b(cpf|rg|identidade|data\s+nasc|nasc|bairro|cidade|uf|cep|telefone|email|estado\s+civil|nacionalidade|profiss[aã]o|cl[aá]usula|assinatura)\b',
            value,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0]
        value = re.sub(r'\s{2,}', ' ', value).strip(' -:;,')
        return value[:max_len].strip()

    def _looks_like_bad_name(self, value: str) -> bool:
        value_norm = (value or '').strip().lower()
        if not value_norm:
            return True
        palavras = value_norm.split()
        termos_ruins = {
            'mede', 'segmentos', 'segmento', 'linha', 'linhas', 'reta', 'curva',
            'curvas', 'marco', 'area', 'área', 'divide', 'divisa', 'confronta',
            'comecando', 'comepando', 'partindo', 'rumo', 'distancia', 'distância',
            'perimetro', 'perímetro', 'quadrados', 'metros', 'lote', 'quadra',
        }
        if ',' in value_norm:
            return True
        if len(palavras) < 2 or len(palavras) > 8:
            return True
        if any(p in termos_ruins for p in palavras):
            return True
        if sum(1 for p in palavras if len(p) <= 2) > max(2, len(palavras) // 2):
            return True
        return False

    def _looks_like_bad_conjunto(self, value: str) -> bool:
        value_norm = re.sub(r'[^a-z0-9 ]', ' ', (value or '').lower())
        value_norm = re.sub(r'\s+', ' ', value_norm).strip()
        if not value_norm:
            return True
        palavras = value_norm.split()
        if len(value_norm) < 3:
            return True
        if len(palavras) >= 3 and sum(1 for p in palavras if len(p) == 1) >= 2:
            return True
        return False

    def _normalize_rg(self, value: str) -> str:
        value = (value or '').upper().strip()
        value = value.replace(' ', '')
        value = value.replace('..', '.')
        value = re.sub(r'[^A-Z0-9\.\-\/]', '', value)
        return value[:20]

    def _clean_address(self, value: str) -> str:
        value = (value or '').replace('\n', ' ')
        value = re.sub(r'\s+', ' ', value).strip(' -:;,')
        value = re.sub(r'^(im[oó]vel|endere[cç]o\s+im[oó]vel)\s*:\s*', '', value, flags=re.IGNORECASE)
        value = re.split(
            r'\b(posi[cç][aã]o|efeitos|indenit[aá]rios|por\s+onde\s+mede|segmentos\s+de\s+linha)\b',
            value,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0]
        if ' - ' in value:
            esquerda, direita = value.split(' - ', 1)
            direita_lower = direita.lower()
            if any(token in direita_lower for token in ['efeitos', 'indenit', 'osiqao', 'posi', 'ren da', 'segmentos', 'linha reta', 'curva']):
                value = esquerda
        value = re.sub(r'\s+-\s*$', '', value).strip(' -:;,')
        return value[:150]

    def _match_known_conjunto(self, value: str) -> Optional[str]:
        value_norm = re.sub(r'[^a-z0-9 ]', ' ', (value or '').lower())
        value_norm = re.sub(r'\s+', ' ', value_norm).strip()
        if not value_norm:
            return None
        try:
            nomes = list(ConjuntoHabitacional.objects.values_list('nome', flat=True))
            codigos = list(ConjuntoHabitacional.objects.values_list('conjunto', flat=True))
        except Exception:
            return None
        nomes_norm = {re.sub(r'[^a-z0-9 ]', ' ', n.lower()).strip(): n for n in nomes if n}
        if value_norm in nomes_norm:
            return nomes_norm[value_norm][:10]
        aproximados = get_close_matches(value_norm, list(nomes_norm.keys()), n=1, cutoff=0.8)
        if aproximados:
            return nomes_norm[aproximados[0]][:10]
        if value_norm.upper() in {str(c).upper() for c in codigos if c}:
            return value_norm.upper()[:10]
        return None

    def _extract_from_labels(
        self,
        labels: List[str],
        *,
        max_len: int = 120,
        allow_next_line: bool = True,
        prefer_digits: bool = False,
    ) -> Optional[str]:
        """Extrai valor após rótulos como 'Nome:', 'CPF:', 'Contrato nº:' em texto OCR."""
        if not self.lines_norm:
            self._prepare_text_views()

        candidates = []
        labels_sorted = sorted(labels, key=len, reverse=True)
        for idx, line in enumerate(self.lines_norm):
            line_lower = line.lower()
            for label in labels_sorted:
                label_lower = label.lower()
                if label_lower not in line_lower:
                    continue

                pos = line_lower.find(label_lower)
                tail = line[pos + len(label_lower):].strip(' -:;,.')
                if not tail and allow_next_line and idx + 1 < len(self.lines_norm):
                    tail = self.lines_norm[idx + 1].strip()

                tail = self._clean_candidate(tail, max_len=max_len)
                if tail:
                    candidates.append(tail)

        if not candidates:
            return None

        if prefer_digits:
            candidates.sort(key=lambda txt: sum(ch.isdigit() for ch in txt), reverse=True)
        else:
            candidates.sort(key=lambda txt: (len(txt.split()) >= 2, len(txt)), reverse=True)
        return candidates[0]

    def extract_text_from_pdf(self) -> str:
        """
        Extrai texto do PDF comparando múltiplas fontes:
          1. pypdf (texto nativo)
                    2. Tesseract OCR (imagem)
        Escolhe a fonte com melhor score para contratos escaneados/ruidosos.
        """
        logger.info(f"Extraindo texto: {self.pdf_path.name}")

        candidates = []

        texto_pypdf = self._extrair_com_pypdf()
        if len(texto_pypdf.strip()) > 100:
            score_pypdf = self._score_text_candidate(texto_pypdf)
            candidates.append(('pypdf', texto_pypdf, score_pypdf))
            logger.info(f"pypdf: {len(texto_pypdf)} chars extraídos (score={score_pypdf})")

        # Sempre tenta OCR para comparar qualidade real em PDFs escaneados.
        try:
            texto_ocr = self._extrair_com_ocr()
            if len(texto_ocr.strip()) > 100:
                score_ocr = self._score_text_candidate(texto_ocr)
                candidates.append(('tesseract_ocr', texto_ocr, score_ocr))
                logger.info(f"tesseract_ocr: {len(texto_ocr)} chars extraídos (score={score_ocr})")
        except Exception as e:
            logger.debug(f"OCR indisponível para comparação: {e}")

        if not candidates:
            raise ValueError('Não foi possível extrair texto do PDF com nenhuma estratégia')

        best_score = max(c[2] for c in candidates)
        ocr_candidate = next((c for c in candidates if c[0] == 'tesseract_ocr'), None)
        if ocr_candidate and ocr_candidate[2] >= (best_score - 1):
            metodo, texto, score = ocr_candidate
        else:
            metodo, texto, score = max(candidates, key=lambda c: c[2])
        logger.info(f"Método escolhido: {metodo} (score={score})")
        self.text = texto
        self._metodo_extracao = metodo
        self._prepare_text_views()
        return self.text

    def _extrair_com_pypdf(self) -> str:
        """Extrai texto utilizando pypdf (sem dependências externas)."""
        try:
            import pypdf
            textos = []
            with open(self.pdf_path, 'rb') as f:
                reader = pypdf.PdfReader(f)
                for pg in reader.pages:
                    t = pg.extract_text() or ''
                    textos.append(t)
            return "\n".join(textos)
        except Exception as e:
            logger.debug(f"pypdf falhou: {e}")
            return ''

    def _extrair_com_pdfplumber(self) -> str:
        """Extrai texto usando pdfplumber (melhor para PDFs com tabelas)."""
        try:
            import pdfplumber
            textos = []
            with pdfplumber.open(str(self.pdf_path)) as pdf:
                for pg in pdf.pages:
                    t = pg.extract_text() or ''
                    textos.append(t)
            return "\n".join(textos)
        except Exception as e:
            logger.debug(f"pdfplumber falhou ou não instalado: {e}")
            return ''

    def _extrair_com_ocr(self) -> str:
        """Converte PDF em imagens e aplica OCR com Tesseract (requer poppler)."""
        try:
            from pdf2image import convert_from_path
            import pytesseract

            # Resolve executáveis em PATH, variáveis de ambiente e locais comuns do Windows.
            tesseract_cmd = self._resolve_tesseract_cmd()
            if tesseract_cmd:
                pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

            poppler_path = self._resolve_poppler_path()
            kwargs = {'dpi': 300}
            if poppler_path:
                kwargs['poppler_path'] = poppler_path

            images = convert_from_path(str(self.pdf_path), **kwargs)
            logger.info(f"PDF convertido em {len(images)} página(s) para OCR")

            ocr_config = '--oem 1 --psm 6'
            ocr_lang = 'por'
            if images:
                try:
                    pytesseract.image_to_string(images[0], lang='por', config=ocr_config)
                except Exception as lang_err:
                    if 'Failed loading language' in str(lang_err) or 'Could not initialize tesseract' in str(lang_err):
                        logger.warning('Idioma OCR por indisponível; usando fallback para eng')
                        ocr_lang = 'eng'
                    else:
                        raise

            textos = []
            for i, image in enumerate(images):
                logger.debug(f"OCR página {i+1}/{len(images)}")
                t = pytesseract.image_to_string(image, lang=ocr_lang, config=ocr_config)
                textos.append(t)
            return "\n".join(textos)
        except Exception as e:
            msg = str(e)
            if 'poppler' in msg.lower():
                raise RuntimeError(
                    "Este PDF parece ser uma imagem escaneada e requer o Poppler para OCR. "
                    "Instale em: https://github.com/oschwartz10612/poppler-windows/releases — "
                    "descompacte e adicione a pasta 'bin' ao PATH do sistema. "
                    "PDFs digitais (gerados por computador) funcionam sem Poppler."
                ) from e
            raise

    def _resolve_tesseract_cmd(self) -> Optional[str]:
        """Resolve caminho do executável do Tesseract no Windows."""
        exe = shutil.which('tesseract')
        if exe:
            return exe

        candidates = [
            os.getenv('TESSERACT_CMD'),
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        ]
        for c in candidates:
            if c and os.path.exists(c):
                return c
        return None

    def _resolve_poppler_path(self) -> Optional[str]:
        """Resolve pasta bin do Poppler para pdf2image (pdftoppm)."""
        pdftoppm = shutil.which('pdftoppm')
        if pdftoppm:
            return str(Path(pdftoppm).parent)

        env = os.getenv('POPPLER_PATH')
        if env and os.path.exists(env):
            return env

        local = Path(os.getenv('LOCALAPPDATA', '')) / 'Microsoft' / 'WinGet' / 'Packages'
        if local.exists():
            for p in local.glob('oschwartz10612.Poppler_*'):
                candidate = p / 'poppler-25.07.0' / 'Library' / 'bin'
                if (candidate / 'pdftoppm.exe').exists():
                    return str(candidate)
                for b in p.glob('poppler-*'):
                    alt = b / 'Library' / 'bin'
                    if (alt / 'pdftoppm.exe').exists():
                        return str(alt)

        common = [
            r'C:\Program Files\poppler\Library\bin',
            r'C:\Program Files\poppler\bin',
        ]
        for c in common:
            if os.path.exists(os.path.join(c, 'pdftoppm.exe')):
                return c
        return None

    def detect_document_type(self) -> str:
        """
        Detecta o tipo de documento a partir do texto extraído.
        Retorna:
          - 'contrato': PDF contratual/origem de cadastro
          - 'printevo_relatorio': relatório gerado pela tela de detalhe do contrato
          - 'desconhecido': não foi possível classificar
        """
        text = (self.text or '').lower()
        if not text:
            return 'desconhecido'

        marcadores_printevo = [
            'evolução teórica do saldo do financiamento',
            'saldo devedor vincendo',
            'relatório gerado em',
            'baixar txt',
            'resumo estatístico',
            'enc mensal',
            'rz progr',
        ]
        hits_printevo = sum(1 for marcador in marcadores_printevo if marcador in text)
        if hits_printevo >= 3:
            return 'printevo_relatorio'

        marcadores_contrato = [
            'cláusula',
            'contratante',
            'mutuário',
            'financiamento',
            'sistema de amortização',
            'valor financiado',
            'assinatura',
        ]
        hits_contrato = sum(1 for marcador in marcadores_contrato if marcador in text)
        if hits_contrato >= 2:
            return 'contrato'

        return 'desconhecido'


    def _find_pattern(self, field_name: str) -> Optional[str]:
        """Busca padrão em regex com insensibilidade a maiúsculas"""
        patterns = self.PATTERNS.get(field_name, [])
        text_lower = self.text.lower()
        
        for pattern in patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE | re.MULTILINE)
            if match:
                # usa grupo 1 se existir, senão usa match completo
                try:
                    val = match.group(1)
                except IndexError:
                    val = match.group(0)
                if val:
                    return val.strip()
        
        return None

    def extract_numero_contrato(self) -> Optional[str]:
        """Extrai número do contrato"""
        numero = self._extract_from_labels(
            ['número do contrato', 'numero do contrato', 'contrato nº', 'contrato n°', 'contrato no', 'nº do contrato', 'n° do contrato'],
            max_len=40,
            prefer_digits=True,
        ) or self._find_pattern('numero_contrato')

        if numero and not any(ch.isdigit() for ch in numero):
            numero = None

        if not numero:
            m = re.search(r'n[úu]mero\s+do\s+contrato\s*:\s*\n\s*([0-9][0-9\-/\.]{1,30})', self.text, re.IGNORECASE)
            if m:
                numero = m.group(1).strip()
        if numero:
            # Limpa números especiais
            numero = re.sub(r'[^\w\-/]', '', numero)
            if len(numero) < 3 or numero.lower() in {'contrato', 'numero', 'financiamento'}:
                numero = None

        # Fallback: usa nome do arquivo (ex.: 1234.pdf)
        if not numero:
            stem = re.sub(r'[^0-9a-zA-Z\-_/]', '', self.pdf_path.stem or '')
            if stem and len(stem) <= 20 and any(ch.isdigit() for ch in stem):
                numero = stem

        if numero:
            self.data['codigo'] = numero
            logger.info(f"Contrato encontrado: {numero}")
        return numero

    def extract_data_contrato(self) -> Optional[date]:
        """Extrai data do contrato"""
        data_str = self._extract_from_labels(
            ['data de assinatura', 'data da assinatura', 'data contrato', 'data do contrato'],
            max_len=20,
            prefer_digits=True,
        ) or self._find_pattern('data_contrato')
        if data_str:
            try:
                # Tenta parsear com dateutil
                data = date_parser.parse(data_str, dayfirst=True).date()
                self.data['data_contrato'] = data
                logger.info(f"Data contrato: {data}")
                return data
            except:
                logger.warning(f"Não conseguiu parsear data: {data_str}")
        return None

    def extract_conjunto(self) -> Optional[str]:
        """Extrai nome/código do conjunto"""
        conjunto = self._extract_from_labels(
            ['conjunto habitacional', 'conjunto residencial', 'conjunto', 'empreendimento', 'residencial', 'residencia'],
            max_len=40,
        ) or self._find_pattern('conjunto')

        # Fallback para layout antigo: "CONJUNTO RESIDENCIAL: SANTA PAULA"
        if not conjunto:
            m = re.search(r'conjunto\s+residen\w*\s*:\s*([a-zà-ÿ\s]{3,40})', self.text.lower(), re.IGNORECASE)
            if m:
                conjunto = m.group(1).strip()

        # Variação OCR: "SANTA PAULA CONJUNTO RESIDENCIAL"
        if not conjunto:
            m2 = re.search(r'([a-zà-ÿ\s]{3,40})\s+conjunto\s+residen\w*', self.text.lower(), re.IGNORECASE)
            if m2:
                conjunto = m2.group(1).strip()

        # Heurística específica para variações "SANTA/STA PAULA" em OCR antigo
        if not conjunto:
            txt = self.text.lower()
            if ('santa paula' in txt) or ('sta paula' in txt):
                try:
                    cand = ConjuntoHabitacional.objects.filter(nome__icontains='PAULA').first()
                    if cand and cand.conjunto:
                        conjunto = str(cand.conjunto)
                except Exception:
                    pass

        if conjunto:
            # Remove caracteres especiais, mantém apenas alfanuméricos e hífen
            conjunto = re.sub(r'[^\w\s\-]', '', conjunto).strip()
            if conjunto.lower() in {'habitacional', 'residencial', 'conjunto'}:
                return None
            conjunto_match = self._match_known_conjunto(conjunto)
            if conjunto_match:
                conjunto = conjunto_match
            elif self._looks_like_bad_conjunto(conjunto):
                logger.warning(f"Conjunto descartado por baixa confiança: {conjunto!r}")
                return None
            self.data['conjunto'] = conjunto[:10]  # Limita a 10 chars como no modelo
            logger.info(f"Conjunto: {self.data['conjunto']}")
        return conjunto

    def _extrair_secao_condicoes_pagamento(self) -> str:
        """Recorta trecho do PDF entre CONDIÇÕES DE PAGAMENTO e próxima seção."""
        txt = self.text or ''
        m_ini = re.search(r'V\s*[-–]?\s*CONDI\w*\s*D?E?\s*PAGAMENTO', txt, re.IGNORECASE)
        if not m_ini:
            m_ini = re.search(r'CONDI\w*\s*D?E?\s*PAGAMENTO', txt, re.IGNORECASE)
        if not m_ini:
            return ''
        start = m_ini.start()
        m_fim = re.search(r'VII\s*[-–]?\s*DECLARA|ESPA[ÇC]O\s+R\s*IRMAS|CONTRATO\s+DE\s+COMPRA', txt[start:], re.IGNORECASE)
        end = start + m_fim.start() if m_fim else min(len(txt), start + 3500)
        return txt[start:end]

    def extract_quadro_financeiro(self) -> None:
        """Extrai dados financeiros dos quadros 'Preço de venda' e 'Condições de pagamento'."""
        sec = self._extrair_secao_condicoes_pagamento()
        if not sec:
            return

        # Preço de venda (valor do imóvel)
        m_preco = re.search(r'pre[çcpo]{2,4}\s+de\s+venda[^\n]{0,120}?cr\$\s*([\d\.,\*]+)', sec, re.IGNORECASE)
        if not m_preco:
            # OCR comum: valor em linha anterior ao rótulo "Prepo de Venda"
            m_lbl = re.search(r'pre[çcpo]{2,4}\s+de\s+venda', sec, re.IGNORECASE)
            if m_lbl:
                janela = sec[max(0, m_lbl.start() - 250):m_lbl.start()]
                vals = re.findall(r'\d{1,3}(?:\.\d{3})*,\d{2}', janela)
                if vals:
                    m_preco = re.match(r'.*', vals[-1])
        if m_preco:
            try:
                valor_txt = m_preco.group(1) if hasattr(m_preco, 'group') and m_preco.groups() else m_preco.group(0)
                self.data['vlprop'] = self._parse_valor(valor_txt)
                logger.info(f"[QUADRO] Preço de venda: {self.data['vlprop']}")
            except Exception:
                pass

        # Prazo (N meses)
        if not self.data.get('prazo'):
            m_prazo = re.search(r'feito\s+em\s*\.*\s*(\d{2,3})\s*\.*\s*meses', sec, re.IGNORECASE)
            if not m_prazo:
                m_prazo = re.search(r'feito\s+e\.?m[^\n]{0,50}?(\d{2,3})[^\n]{0,20}meses', sec, re.IGNORECASE)
            if not m_prazo:
                m_prazo = re.search(r'(\d{2,3})\s*\.?\s*meses', sec, re.IGNORECASE)
            if m_prazo:
                self.data['prazo'] = int(m_prazo.group(1))
                logger.info(f"[QUADRO] Prazo: {self.data['prazo']}")

        # Taxa de juros nominal/efetiva a.a.
        if not self.data.get('tx_juros'):
            m_tx = re.search(r'taxa\s+de\s+juros\s+nominal[^\n]{0,100}?([\d]{1,2}[\.,][\d]{1,5})\s*(?:%|a\.a)', sec, re.IGNORECASE)
            if not m_tx:
                m_tx = re.search(r'taxa\s+efetiva[^\n]{0,100}?([\d]{1,2}[\.,][\d]{1,5})\s*(?:%|a\.a)', sec, re.IGNORECASE)
            if m_tx:
                try:
                    self.data['tx_juros'] = Decimal(m_tx.group(1).replace(',', '.'))
                    logger.info(f"[QUADRO] Taxa juros: {self.data['tx_juros']}")
                except Exception:
                    pass

        # Data do contrato e primeiro vencimento: usa datas no contexto do quadro
        datas = re.findall(r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b', sec)
        parsed = []
        for d in datas:
            try:
                parsed.append(date_parser.parse(d, dayfirst=True).date())
            except Exception:
                pass
        parsed = sorted(set(parsed))
        if parsed:
            if not self.data.get('data_contrato'):
                self.data['data_contrato'] = parsed[0]
            if len(parsed) > 1 and not self.data.get('data_primeiro_venc'):
                self.data['data_primeiro_venc'] = parsed[1]

        # Prestação inicial
        m_prest = re.search(r'inicial\s+de\s+cr\$\s*([\d\.,\*]+)', sec, re.IGNORECASE)
        if m_prest:
            try:
                self.data['prestacao_inicial'] = float(self._parse_valor(m_prest.group(1)))
                logger.info(f"[QUADRO] Prestação inicial: {self.data['prestacao_inicial']}")
            except Exception:
                pass

        # ── Valor do Financiamento (saldo devedor inicial) ─────────────────
        if not self.data.get('vlfinanc'):
            # 1. Buscar padrões BNH na seção de condições de pagamento
            vlf_patterns = [
                r'valor\s+d[oa]\s+financiamento[\s\S]{0,80}?(?:cr\$|crs)\s*([\d\.,]+)',
                r'import[âa]ncia\s+de\s+(?:cr\$|crs)\s*([\d\.,]+)',
                r'financia\w*\s+(?:a\s+)?import[âa]ncia\s+de\s+(?:cr\$|crs)?\s*([\d\.,]+)',
                r'valor\s+financiado\s*[:=]?\s*(?:cr\$|crs|r\$)?\s*([\d\.,]+)',
                r'saldo\s+(?:devedor\s+)?inicial\s*[:=]?\s*(?:cr\$|crs|r\$)?\s*([\d\.,]+)',
                r'(?:cr\$|crs)\s*([\d\.,]+)\s*\(\s*valor\s+d[oa]\s+financiamento',
            ]
            for pat in vlf_patterns:
                m_vlf = re.search(pat, sec, re.IGNORECASE)
                if m_vlf:
                    try:
                        self.data['vlfinanc'] = self._parse_valor(m_vlf.group(1))
                        logger.info(f"[QUADRO] vlfinanc encontrado: {self.data['vlfinanc']}")
                        break
                    except Exception:
                        pass

        # 2. Back-cálculo via prestacao_inicial + SA + tx_juros + prazo
        #    Só usado se nenhum padrão encontrou e prestacao_inicial está disponível
        if not self.data.get('vlfinanc'):
            prest = self.data.get('prestacao_inicial') or self.data.get('encargo_mensal')
            prazo = self.data.get('prazo')
            tx_juros = self.data.get('tx_juros')
            sa = (self.data.get('sa') or 'SAC').upper()
            if prest and prazo and tx_juros and Decimal(str(prest)) > 0 and int(prazo) > 0:
                try:
                    prest_d = Decimal(str(prest))
                    n = int(prazo)
                    tx_mes = Decimal(str(tx_juros)) / 100 / 12
                    if sa == 'PRICE' and tx_mes > 0:
                        # PRICE: P = PV * i*(1+i)^n / ((1+i)^n - 1)
                        fator = tx_mes * (1 + tx_mes)**n / ((1 + tx_mes)**n - 1)
                        vlf_calc = prest_d / fator
                    else:
                        # SAC: P1 = PV/n + PV*i => PV = P1 / (1/n + i)
                        vlf_calc = prest_d / (Decimal(1) / n + tx_mes)
                    self.data['vlfinanc'] = vlf_calc.quantize(Decimal('0.01'))
                    self.data['vlfinanc_calculado'] = True  # marca que foi calculado
                    logger.info(f"[QUADRO] vlfinanc back-calculado ({sa}): {self.data['vlfinanc']}")
                except Exception as e:
                    logger.warning(f"[QUADRO] Back-cálculo vlfinanc falhou: {e}")

        # Encargo mensal (quadro resumo / termo de alteração contratual)
        if not self.data.get('encargo_mensal'):
            m_enc = self._find_pattern('encargo_mensal')
            if m_enc:
                try:
                    self.data['encargo_mensal'] = float(self._parse_valor(m_enc))
                    logger.info(f"[QUADRO] Encargo mensal: {self.data['encargo_mensal']}")
                except Exception:
                    pass

        # Prestação reajustada (após termo de alteração)
        if not self.data.get('prestacao_reajustada'):
            m_praj = self._find_pattern('prestacao_reajustada')
            if m_praj:
                try:
                    self.data['prestacao_reajustada'] = float(self._parse_valor(m_praj))
                    logger.info(f"[QUADRO] Prestação reajustada: {self.data['prestacao_reajustada']}")
                except Exception:
                    pass

    def extract_prazo(self) -> Optional[int]:
        """Extrai prazo/número de parcelas"""
        prazo_str = self._find_pattern('prazo')

        # Fallback para texto antigo com ruído: "... 120 ... meses"
        if not prazo_str:
            m = re.search(r'(\d{2,3})\D{0,20}meses', self.text.lower())
            if m:
                prazo_str = m.group(1)

        if prazo_str:
            try:
                prazo = int(re.sub(r'\D', '', prazo_str))
                self.data['prazo'] = prazo
                logger.info(f"Prazo: {prazo} meses")
                return prazo
            except:
                logger.warning(f"Não conseguiu parsear prazo: {prazo_str}")
        return None

    def extract_taxa_juros(self) -> Optional[Decimal]:
        """Extrai taxa de juros"""
        taxa_str = self._find_pattern('taxa_juros')
        if taxa_str:
            try:
                # Converte vírgula em ponto para Decimal
                taxa_str = taxa_str.replace(',', '.')
                taxa = Decimal(taxa_str)
                self.data['tx_juros'] = taxa
                logger.info(f"Taxa juros: {taxa}%")
                return taxa
            except:
                logger.warning(f"Não conseguiu parsear taxa: {taxa_str}")
        return None

    def extract_valor_imovel(self) -> Optional[Decimal]:
        """Extrai valor do imóvel"""
        valor_str = self._find_pattern('valor_imovel')
        if valor_str:
            try:
                valor = self._parse_valor(valor_str)
                self.data['vlprop'] = valor
                logger.info(f"Valor imóvel: R$ {valor}")
                return valor
            except:
                logger.warning(f"Não conseguiu parsear valor imóvel: {valor_str}")
        return None

    def extract_valor_financiado(self) -> Optional[Decimal]:
        """Extrai valor financiado"""
        valor_str = self._find_pattern('valor_financiado')
        if valor_str:
            try:
                valor = self._parse_valor(valor_str)
                self.data['vlfinanc'] = valor
                logger.info(f"Valor financiado: {valor}")
                return valor
            except Exception:
                logger.warning(f"Não conseguiu parsear valor financiado: {valor_str}")

        # Sem fallback para vlprop — vlprop é o preço do imóvel, não o financiamento.
        # O back-cálculo via prestacao_inicial é feito em extract_quadro_financeiro.
        return self.data.get('vlfinanc')

    def extract_numero_imovel(self) -> Optional[str]:
        """Extrai número do imóvel/logradouro"""
        numero = self._find_pattern('numero_imovel')
        if numero:
            self.data['numero'] = numero
            logger.info(f"Número: {numero}")
        return numero

    # Palavras que indicam endereço institucional — não devem ser usadas como endereço do mutuário
    _INST_KEYWORDS = re.compile(
        r'\b(cofluhab|bnh|cef|caixa\s+econ|banco\s+nacion|pronil|bndes|ins[ct]rumen[ct]o|agente\s+financeiro|outorgan[ct]e\s+vendedor)\b',
        re.IGNORECASE,
    )

    def extract_endereco(self) -> Optional[str]:
        """Extrai endereço"""
        # 1. Prioridade: "Residencia: Rua ..." — é o endereço do mutuário
        endereco = None
        for ln in self.lines_norm:
            if re.search(r'resid[eê]ncia\s*:', ln, re.I):
                tail = re.sub(r'^.*?resid[eê]ncia\s*:\s*', '', ln, flags=re.I).strip()
                # Pula linhas que são cabeçalho de tabela: múltiplos rótulos "X:"
                if len(re.findall(r'\b\w+\s*:', tail)) >= 2:
                    continue
                # Remove cidade após último " - "
                if ' - ' in tail:
                    parts = tail.rsplit(' - ', 1)
                    tail = parts[0].strip()
                # Remove cidade após traço simples sem espaços (ex: "Rua X-Rio de Janeiro")
                # Remove cidade após traço (com ou sem pontuação antes, ex: "s.-Rio" ou "s/n-Rio")
                else:
                    tail = re.sub(r'[\.\,>]?-[A-Za-z][A-Za-z\s]+$', '', tail).strip()
                tail = re.sub(r'^rua\s*:\s*', 'Rua ', tail, flags=re.I).strip()
                if len(tail) >= 6 and not self._INST_KEYWORDS.search(tail):
                    endereco = tail
                    break

        if not endereco:
            endereco = self._extract_from_labels(
                ['endereço imóvel', 'endereco imovel', 'endereço', 'endereco', 'logradouro'],
                max_len=150,
            ) or self._find_pattern('endereco')

        # Fallback extra: linha "Residencia: Rua ..."
        if not endereco:
            m = re.search(r'resid[êe]ncia\s*:\s*([^\n]{6,150})', self.text, re.IGNORECASE)
            if m:
                endereco = m.group(1).strip()

        if endereco:
            endereco = self._clean_address(endereco).title()[:150]
            if len(endereco) < 6:
                return None
            self.data['endereco'] = endereco
            logger.info(f"Endereço: {endereco}")
        return endereco

    def extract_complemento(self) -> Optional[str]:
        """Extrai complemento do endereço"""
        complemento = self._find_pattern('complemento')
        if complemento:
            complemento = complemento.strip()[:50]
            # Rejeita texto que parece corpo do contrato (muitas palavras sem tokens típicos)
            palavras = complemento.split()
            tokens_compl = {'apt', 'apto', 'ap', 'bloco', 'bl', 'lote', 'lt', 'casa', 'sala', 'unid', 'sl'}
            has_token = any(p.lower() in tokens_compl for p in palavras)
            # Rejeita se > 5 palavras sem token de complemento
            if len(palavras) > 5 and not has_token:
                logger.warning(f"Complemento rejeitado (parece corpo de texto): {complemento!r}")
                return None
            self.data['compl'] = complemento
            logger.info(f"Complemento: {complemento}")
        return complemento

    def extract_bairro(self) -> Optional[str]:
        """Extrai bairro"""
        bairro = self._find_pattern('bairro')
        if bairro:
            bairro = bairro.title()[:50]
            self.data['bairro'] = bairro
            logger.info(f"Bairro: {bairro}")
        return bairro

    # Mapa nome-do-estado → sigla UF (para inferir de endereços por extenso)
    _ESTADO_UF_MAP = {
        'acre': 'AC', 'alagoas': 'AL', 'amapá': 'AP', 'amapa': 'AP',
        'amazonas': 'AM', 'bahia': 'BA', 'ceará': 'CE', 'ceara': 'CE',
        'distrito federal': 'DF', 'espírito santo': 'ES', 'espirito santo': 'ES',
        'goiás': 'GO', 'goias': 'GO', 'maranhão': 'MA', 'maranhao': 'MA',
        'mato grosso do sul': 'MS', 'mato grosso': 'MT',
        'minas gerais': 'MG', 'pará': 'PA', 'para': 'PA',
        'paraíba': 'PB', 'paraiba': 'PB', 'paraná': 'PR', 'parana': 'PR',
        'pernambuco': 'PE', 'piauí': 'PI', 'piaui': 'PI',
        'rio de janeiro': 'RJ', 'rio grande do norte': 'RN',
        'rio grande do sul': 'RS', 'rondônia': 'RO', 'rondonia': 'RO',
        'roraima': 'RR', 'santa catarina': 'SC', 'são paulo': 'SP', 'sao paulo': 'SP',
        'sergipe': 'SE', 'tocantins': 'TO',
    }

    @staticmethod
    def _is_address_like(s: str) -> bool:
        """True se o texto parece um logradouro em vez de nome de cidade."""
        logr = re.compile(r'\b(rua|av\.?|avenida|alameda|travessa|estrada|rodovia|praça|largo)\b', re.I)
        return bool(logr.search(s))

    def extract_cidade(self) -> Optional[str]:
        """Extrai cidade"""
        candidates = []

        # 1. Procura em linhas de residência/endereço do mutuário primeiro
        for ln in self.lines_norm:
            ln_low = ln.lower()
            if re.search(r'resid[eê]ncia', ln_low):
                # Ex: "Residencia: Rua: Aymores s/n - Rio de Janeiro"
                # Pega último segmento após "-" ou a cidade após a rua
                parts = re.split(r'\s*[-–]\s*', ln)
                for part in reversed(parts):
                    p = part.strip().title()
                    if 2 <= len(p.split()) <= 4 and not self._is_address_like(p) and not p.startswith('Rua'):
                        candidates.append(p)
                        break

        # 2. Label-based mas só aceita valores curtos sem logradouro
        cand_label = self._extract_from_labels(['cidade', 'city'], max_len=50)
        if cand_label and not self._is_address_like(cand_label):
            # Rejeita prefixos "do/da/de" que indicam que é parte de frase
            cand_clean = re.sub(r'^(d[aeo]s?\s+)+', '', cand_label, flags=re.I).strip()
            if 1 <= len(cand_clean.split()) <= 4:
                candidates.append(cand_clean.title())

        # 3. Pattern-based (fallback)
        if not candidates:
            cand_pat = self._find_pattern('cidade')
            if cand_pat and not self._is_address_like(cand_pat):
                cand_pat = re.sub(r'^(d[aeo]s?\s+)+', '', cand_pat, flags=re.I).strip().title()
                if 1 <= len(cand_pat.split()) <= 4:
                    candidates.append(cand_pat)

        if candidates:
            cidade = candidates[0][:50]
            self.data['cidade'] = cidade
            logger.info(f"Cidade: {cidade}")
            return cidade
        return None

    # UFs válidas do Brasil
    _UFS_VALIDAS = {
        'AC','AL','AP','AM','BA','CE','DF','ES','GO','MA',
        'MT','MS','MG','PA','PB','PR','PE','PI','RJ','RN',
        'RS','RO','RR','SC','SP','SE','TO',
    }

    def extract_uf(self) -> Optional[str]:
        """Extrai UF"""
        # 1. Label explícito: "UF: RJ" ou "UF do Imóvel: RJ"
        uf = self._find_pattern('uf')
        # O padrão amplo \b(AC|...|TO)\b pode pegar qualquer sigla no texto
        # → filtramos: só aceita se veio do primeiro padrão (rótulo explicito) OU
        #   se aparece em contexto de endereço (linha com rua, av, cep, niteroi etc.)

        # 2. Busca UF no padrão "- RJ" / "- SP" em linhas com contexto de endereço
        uf_addr = None
        for ln in self.lines_norm:
            ln_low = ln.lower()
            if not re.search(r'resid[eê]ncia|endere[cç]o|bairro|cep|sede|centro|niter[oó]i|maric[aá]|\brua\b|\bav\.?\b', ln_low):
                continue
            m = re.search(r'[-–,]\s*([A-Z]{2})\s*[.,\)\n]', ln)
            if m and m.group(1) in self._UFS_VALIDAS:
                uf_addr = m.group(1)
                break

        # 3. Inferência por nome do estado no texto ("Estado do Rio de Janeiro" → RJ)
        uf_infer = None
        if not uf_addr:
            txt_low = (self.text or '').lower()
            for estado, sigla in sorted(self._ESTADO_UF_MAP.items(), key=lambda x: -len(x[0])):
                if re.search(r'\b' + re.escape(estado) + r'\b', txt_low):
                    uf_infer = sigla
                    break

        # Prioridade: endereço > inferência > padrão amplo
        resultado = uf_addr or uf_infer or (uf.upper()[:2] if uf else None)

        if resultado and resultado in self._UFS_VALIDAS:
            self.data['uf'] = resultado
            logger.info(f"UF: {resultado}")
            return resultado
        return None

    def extract_cep(self) -> Optional[str]:
        """Extrai CEP"""
        cep = self._find_pattern('cep')
        if cep:
            cep = re.sub(r'[^\d]', '', cep)
            if len(cep) == 8:
                cep = f"{cep[:5]}-{cep[5:]}"
            self.data['cep'] = cep
            logger.info(f"CEP: {cep}")
        return cep

    def extract_mutuario_nome(self) -> Optional[str]:
        """Extrai nome do mutuário"""
        # 1) Padrão forte para layout tabular: "Nome Completo:\n<nome>"
        nome = None
        m_nome_linha = re.search(r'nome\s+completo\s*:\s*\n\s*([^\n]{5,100})', self.text, re.IGNORECASE)
        if m_nome_linha:
            nome = m_nome_linha.group(1).strip()

        # 2) Contratos antigos: "Nome: ... CPF/CIC:"
        if not nome:
            m_nome_cic = re.search(r'nome\s*:\s*([a-zà-ÿ\s]{5,100}?)\s*(?:cic|cpf)\s*:', self.text.lower(), re.IGNORECASE)
            if m_nome_cic:
                nome = m_nome_cic.group(1).strip()

        # 3) Fallback por rótulos estruturados (evita termos genéricos do corpo)
        if not nome:
            nome = self._extract_from_labels(
                ['nome completo', 'nome do mutuário', 'nome do mutuario', 'nome do contratante', 'nome'],
                max_len=100,
            ) or self._find_pattern('mutuario_nome')

        if nome:
            nome = re.split(r'\b(cpf|cic|rg|identidade)\b', nome, maxsplit=1, flags=re.IGNORECASE)[0].strip(' -:;,')

        if nome and nome.strip().lower() in {'completo', 'nome completo'}:
            nome = None
        if nome:
            nome = nome.strip()
            if len(nome) < 3 or self._looks_like_bad_name(nome):
                logger.warning(f"Nome descartado por baixa confiança: {nome!r}")
                return None
            nome = nome.title()[:100]
            self.data['nome'] = nome
            logger.info(f"Mutuário: {nome}")
        return nome

    def extract_cpf(self) -> Optional[str]:
        """Extrai CPF"""
        cpf = self._find_pattern('cpf')
        if cpf:
            # Formata como 000.000.000-00
            cpf = re.sub(r'[^\d]', '', cpf)
            if len(cpf) == 11:
                cpf = f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
                self.data['cpf'] = cpf
                logger.info(f"CPF: {cpf}")
                return cpf
            logger.warning(f"CPF descartado por tamanho inválido: {cpf}")
        return None

    def extract_rg(self) -> Optional[str]:
        """Extrai RG"""
        rg = self._extract_from_labels(['identidade', 'rg'], max_len=20, prefer_digits=True) or self._find_pattern('rg')
        if rg:
            rg = self._normalize_rg(rg)
            self.data['ident'] = rg
            logger.info(f"RG: {rg}")
        return rg

    def extract_orgao_emissor(self) -> Optional[str]:
        """Extrai órgão emissor do RG"""
        orgao = self._extract_from_labels(['órgão emissor', 'orgao emissor', 'expedidor'], max_len=20) or self._find_pattern('orgao_emissor')
        if orgao:
            orgao = orgao.upper()[:20]
            self.data['orgao'] = orgao
            logger.info(f"Órgão: {orgao}")
        return orgao

    def extract_data_nascimento(self) -> Optional[date]:
        """Extrai data de nascimento"""
        data_str = self._extract_from_labels(['data nasc', 'data de nascimento', 'nascimento', 'dt nasc'], max_len=20, prefer_digits=True) or self._find_pattern('data_nascimento')
        if data_str:
            try:
                data = date_parser.parse(data_str, dayfirst=True).date()
                self.data['dtnasc'] = data
                logger.info(f"Data nascimento: {data}")
                return data
            except:
                logger.warning(f"Não conseguiu parsear data nascimento: {data_str}")
        return None

    def extract_telefone(self) -> Optional[str]:
        """Extrai telefone"""
        telefone_match = re.search(r'\(?(\d{2})\)?[\s\-]?(\d{4,5})[\s\-]?(\d{4})', self.text)
        if telefone_match:
            ddd = telefone_match.group(1)
            numero = telefone_match.group(2) + telefone_match.group(3)
            telefone = f"({ddd}) {numero}"
            self.data['telefone'] = telefone
            logger.info(f"Telefone: {telefone}")
            return telefone
        return None

    def extract_email(self) -> Optional[str]:
        """Extrai email"""
        email = self._find_pattern('email')
        if email:
            email = email.lower()[:100]
            self.data['email'] = email
            logger.info(f"Email: {email}")
        return email

    def extract_cat_prof(self) -> Optional[str]:
        """Extrai categoria profissional (CODIGO_CATEG_PROF no FH1)"""
        cat = self._find_pattern('cat_prof')
        if cat:
            cat = cat.strip()
            # Rejeita se parece texto corrido (contém espaço e >4 chars)
            if ' ' in cat and len(cat) > 4:
                logger.warning(f"cat_prof descartado (parece texto): {cat!r}")
                return None
            cat = cat[:10]
            self.data['cat_prof'] = cat
            logger.info(f"Categoria profissional: {cat}")
        return cat

    def extract_pr(self) -> Optional[str]:
        """Extrai código do programa (PR no FH1 e CADMUT)"""
        allowed = {'BNH', 'MCMV', 'PMCMV', 'SFH', 'SFI', 'FGTS', 'SBPE', 'FAR', 'FAT', 'PAC', 'HIS'}

        # Prioriza rótulo explícito "PR: XXX"
        pr = self._extract_from_labels(['pr', 'programa'], max_len=20)
        if pr:
            pr = pr.strip().upper().split()[0]
            if pr not in allowed:
                pr = None

        if not pr:
            pr = self._find_pattern('pr')
        if pr:
            pr = pr.strip().upper().split()[0][:10]
            if pr not in allowed:
                logger.warning(f"Programa (PR) descartado por valor inválido: {pr!r}")
                return None
            self.data['pr'] = pr
            logger.info(f"Programa (PR): {pr}")
        return pr

    def extract_data_primeiro_venc(self) -> Optional[date]:
        """Extrai data do primeiro vencimento (PRIMEIRO_VENCIMENTO no FH1)"""
        data_str = self._find_pattern('data_primeiro_venc')
        if data_str:
            try:
                data = date_parser.parse(data_str, dayfirst=True).date()
                self.data['data_primeiro_venc'] = data
                logger.info(f"Primeiro vencimento: {data}")
                return data
            except:
                logger.warning(f"Não conseguiu parsear primeiro vencimento: {data_str}")
        return None

    def extract_prazo_fcvs(self) -> Optional[int]:
        """Extrai prazo FCVS (PRAZO_FCVS no FH1 — pode diferir do prazo contratual)"""
        prazo_str = self._find_pattern('prazo_fcvs')
        if prazo_str:
            try:
                prazo = int(re.sub(r'\D', '', prazo_str))
                self.data['prazo_fcvs'] = prazo
                logger.info(f"Prazo FCVS: {prazo} meses")
                return prazo
            except:
                logger.warning(f"Não conseguiu parsear prazo FCVS: {prazo_str}")
        return None

    def extract_tipo_operacao(self) -> Optional[str]:
        """
        Extrai tipo de operação CADMUT:
        0=FDS-MCMV, 1=COM FCVS, 2=SEM FCVS, 3=PSH s/FGTS,
        4=PSH c/FGTS, 5=COM DESC FGTS, 6=PRO-MORADIA, 7=REC FDS,
        8=ARRENDAM, 9=AQ.DIR.MCMV
        """
        tipo = self._find_pattern('tipo_operacao')
        if tipo:
            # Mapeia termos descritivos para código numérico
            mapa = {
                'fds': '0', 'mcmv': '0',
                'com cobertura fcvs': '1', 'com fcvs': '1',
                'sem cobertura fcvs': '2', 'sem fcvs': '2',
                'psh s/': '3', 'psh sem': '3',
                'psh c/': '4', 'psh com': '4',
                'desc fgts': '5', 'com desc': '5',
                'pro-moradia': '6', 'pro moradia': '6',
                'rec fds': '7', 'rec. fds': '7',
                'arrendam': '8',
                'aq. dir': '9', 'aq.dir': '9',
            }
            tipo_lower = tipo.lower()
            for chave, codigo in mapa.items():
                if chave in tipo_lower:
                    self.data['tipo_operacao'] = codigo
                    logger.info(f"Tipo operação: {codigo} ({tipo})")
                    return codigo
            # Se já é numérico, usa direto
            if tipo.strip().isdigit():
                self.data['tipo_operacao'] = tipo.strip()
                return tipo.strip()
        return None

    def extract_renda(self) -> Optional[Decimal]:
        """Extrai renda bruta do mutuário"""
        renda_str = self._find_pattern('renda')
        if renda_str:
            try:
                renda = self._parse_valor(renda_str)
                self.data['renda'] = float(renda)
                logger.info(f"Renda: R$ {renda}")
                return renda
            except:
                logger.warning(f"Não conseguiu parsear renda: {renda_str}")
        return None

    def extract_crenda(self) -> Optional[Decimal]:
        """Extrai renda do cônjuge"""
        crenda_str = self._find_pattern('crenda')
        if crenda_str:
            try:
                crenda = self._parse_valor(crenda_str)
                self.data['crenda'] = float(crenda)
                logger.info(f"Renda cônjuge: R$ {crenda}")
                return crenda
            except:
                logger.warning(f"Não conseguiu parsear renda cônjuge: {crenda_str}")
        return None

    def extract_codimovel(self) -> Optional[str]:
        """Extrai código do imóvel (codimovel em Mutuario, cod_imovel em Contrato)"""
        cod = self._find_pattern('codimovel')
        if cod:
            cod = cod.strip()[:20]
            self.data['codimovel'] = cod
            self.data['cod_imovel'] = cod  # Mapeia para Contrato também
            logger.info(f"Código imóvel: {cod}")
        return cod

    def extract_tipoimovel(self) -> Optional[str]:
        """Extrai tipo do imóvel (casa, apartamento, etc.)"""
        tipo = self._find_pattern('tipoimovel')
        if tipo:
            tipo = tipo.strip().title()[:50]
            self.data['tipoimovel'] = tipo
            logger.info(f"Tipo imóvel: {tipo}")
        return tipo

    def extract_ocorrencia(self) -> Optional[str]:
        """Extrai tipo de ocorrência CADMUT (TPZ, SET, SIT, LA2, LA3, PXN, LIQ)"""
        ocorr = self._find_pattern('ocorrencia')
        if ocorr:
            ocorr = ocorr.upper().strip()[:10]
            self.data['ocorrencia'] = ocorr
            logger.info(f"Ocorrência: {ocorr}")
        return ocorr

    def extract_data_evento(self) -> Optional[date]:
        """Extrai data do evento CADMUT"""
        data_str = self._find_pattern('data_evento')
        if data_str:
            try:
                data = date_parser.parse(data_str, dayfirst=True).date()
                self.data['data_evento'] = data
                logger.info(f"Data evento: {data}")
                return data
            except:
                logger.warning(f"Não conseguiu parsear data evento: {data_str}")
        return None

    def extract_situacao_contrato(self) -> Optional[str]:
        """Extrai situação do contrato para CADMUT (1=Ativo, 2=Inativo)"""
        sit = self._find_pattern('situacao_contrato')
        if sit:
            sit_lower = sit.lower()
            codigo = '1' if 'ativo' in sit_lower and 'in' not in sit_lower else '2'
            self.data['situacao_contrato'] = codigo
            logger.info(f"Situação contrato: {codigo} ({sit})")
            return codigo
        return None

    def extract_sistema_amortizacao(self) -> Optional[str]:
        """Extrai sistema de amortização (SAC, PRICE, SACRE, MISTO)"""
        # Labels com variantes OCR (p/ç, ã→a, etc.)
        sa_str = self._extract_from_labels(
            [
                'sistema de amortização', 'sistema de amortizacao',
                'sistema amortizacao', 'sistema amortizapao',
                'sistema de amortizapao', 'sa',
            ],
            max_len=80,
        ) or self._find_pattern('sa')

        def _classify(s: str) -> Optional[str]:
            n = s.lower()
            if 'sacre' in n:
                return 'SACRE'
            if 'price' in n:
                return 'PRICE'
            if re.search(r'\bmisto\b|\bmixto\b', n):
                return 'MISTO'
            if 'sac' in n:
                return 'SAC'
            return None

        if sa_str:
            result = _classify(sa_str)
            if result:
                self.data['sa'] = result

        # Busca secundária: apenas em linhas curtas (campo, não corpo de cláusula)
        # e próximas a marcadores do quadro financeiro (5.1, sa:, sistema:)
        if not self.data.get('sa'):
            for ln in self.lines_norm:
                # Ignora linhas longas (texto de cláusula)
                if len(ln) > 120:
                    continue
                result = _classify(ln)
                if result and re.search(r'\b5[\.\s]*1\b|sistema\s*de\s*amort|\bsa\s*:', ln, re.I):
                    self.data['sa'] = result
                    break

        logger.info(f"Sistema amortização: {self.data.get('sa')}")
        return self.data.get('sa')

    @staticmethod
    def _parse_valor(valor_str: str) -> Decimal:
        """Converte string de valor em Decimal"""
        # Remove R$, espaços, etc
        valor_str = re.sub(r'[^\d,\.]', '', valor_str)
        if not valor_str:
            return Decimal('0')
        n_virgulas = valor_str.count(',')
        n_pontos   = valor_str.count('.')
        # Múltiplas vírgulas: OCR substituiu pontos de milhar por vírgulas
        # Ex: "460,960,00" → 460960.00
        if n_virgulas > 1:
            partes = valor_str.split(',')
            inteiro = ''.join(partes[:-1]).replace('.', '')
            valor_str = inteiro + '.' + partes[-1]
        elif n_virgulas == 1 and n_pontos >= 1:
            if valor_str.rfind('.') > valor_str.rfind(','):
                valor_str = valor_str.replace(',', '')
            else:
                valor_str = valor_str.replace('.', '').replace(',', '.')
        elif n_virgulas == 1:
            valor_str = valor_str.replace(',', '.')
        try:
            return Decimal(valor_str)
        except Exception:
            return Decimal('0')

    @staticmethod
    def _parse_data_br(s: str) -> Optional[date]:
        """Converte string de data brasileira (DD/MM/AAAA) em date."""
        s = s.strip()
        for fmt in ('%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y'):
            try:
                return datetime.strptime(s, fmt).date()
            except ValueError:
                pass
        return None

    # ------------------------------------------------------------------
    # EXTRAÇÃO DA TABELA DE EVOLUÇÃO FINANCEIRA (PARCELAS)
    # ------------------------------------------------------------------
    # Mapeamento de cabeçalhos comuns de planilhas financeiras → campo do modelo
    _CABECALHO_MAP = {
        'mens':     'nmens',
        'parcela':  'nmens',
        'n ':       'nmens',
        'n.':       'nmens',
        'venc':     'dtvenc',
        'dt venc':  'dtvenc',
        'data':     'dtvenc',
        'juros':    'juros',
        'amort':    'amort',
        'amortiz':  'amort',
        'corr mon': 'cm',
        'cm':       'cm',
        'reaj':     'rp',
        'rz prog':  'rp',
        'razao':    'rp',
        'sd dev':   'sddev',
        'saldo dev': 'sddev',
        'saldo':    'sddev',
        'seguro':   'seguro',
        'seguros':  'seguro',
        'tca':      'tca',
        'fcvs':     'fcvs',
        'enc men':  'vlautent',
        'encargo':  'vlautent',
        'prestac':  'vlautent',
        'total':    'vlautent',
    }

    def _mapear_cabecalho(self, colunas: List[str]) -> Dict[int, str]:
        """
        Dado uma lista de textos de cabeçalho, retorna {idx: campo_modelo}.
        Usa correspondência parcial com _CABECALHO_MAP.
        """
        mapa = {}
        for i, col in enumerate(colunas):
            col_lower = col.lower().strip()
            for chave, campo in self._CABECALHO_MAP.items():
                if chave in col_lower:
                    if campo not in mapa.values():  # prim correspência vence
                        mapa[i] = campo
                    break
        return mapa

    def _row_to_parcela(self, row: List[str], mapa: Dict[int, str]) -> Optional[Dict]:
        """
        Converte uma linha de tabela num dict de parcela, ou None se inválida.
        """
        parcela = {}
        for idx, campo in mapa.items():
            if idx >= len(row):
                continue
            val = str(row[idx]).strip()
            if not val or val == '-':
                continue
            try:
                if campo == 'nmens':
                    parcela['nmens'] = int(re.sub(r'\D', '', val))
                elif campo == 'dtvenc':
                    d = self._parse_data_br(val)
                    if d:
                        parcela['dtvenc'] = d
                else:
                    parcela[campo] = self._parse_valor(val)
            except Exception:
                pass
        # Línha válida deve ter pelo menos nmens ou dtvenc + 1 valor numérico
        numericos = [c for c in parcela if c not in ('nmens', 'dtvenc')]
        if 'nmens' not in parcela and 'dtvenc' not in parcela:
            return None
        if not numericos:
            return None
        return parcela

    def extract_parcelas(self) -> List[Dict]:
        """
        Extrai a tabela de evolução financeira do PDF.
        Estratégia 1: pdfplumber (tabelas estruturadas)
        Estratégia 2: parsing por linhas de texto
        Armazena resultado em self.data['parcelas'].
        """
        parcelas = []

        # Estratégia principal: regex sobre texto já selecionado (pypdf/ocr).
        # Evita custo alto e travamentos do parser de tabelas em PDFs antigos.
        if self.text:
            parcelas = self._parse_parcelas_texto()

        if parcelas:
            # Garante nmens seqüencial se não extraído
            for i, p in enumerate(parcelas, 1):
                if 'nmens' not in p:
                    p['nmens'] = i
            logger.info(f"Parcelas extraídas: {len(parcelas)}")
        else:
            logger.info("Nenhuma parcela encontrada no PDF")

        self.data['parcelas'] = parcelas
        return parcelas

    def _parse_parcelas_texto(self) -> List[Dict]:
        """
        Extrai tabela financeira do texto puro do PDF.
        Estratégia robusta:
          1. Localiza cabeçalho por keywords (busca substring, não palavra exata)
          2. Tenta dividir cabeçalho por: tab >> 2+ espaços >> espaço simples
          3. Extrai valores decimais por regex (não por split de colunas)
          4. Mapeia decimais positionally para campos conforme ordem do cabeçalho
        """
        parcelas = []
        linhas = self.text.splitlines()

        KWORDS = ['venc', 'juros', 'amort', 'fcvs', 'mens', 'corr', 'seguro']
        cabecalho_idx = -1
        mapa = {}

        for i, linha in enumerate(linhas):
            linha_lower = linha.lower()
            hits = sum(1 for k in KWORDS if k in linha_lower)
            if hits < 2:
                continue
            # Tenta 3 estratégias de divisão do cabeçalho
            for dividir in (
                lambda s: [c for c in s.split('\t') if c.strip()],
                lambda s: [c.strip() for c in re.split(r'\s{2,}', s) if c.strip()],
                lambda s: [c.strip() for c in re.split(r'\s+', s) if c.strip()],
            ):
                colunas = dividir(linha.strip())
                if len(colunas) >= 4:
                    mapa_tent = self._mapear_cabecalho(colunas)
                    if len(mapa_tent) >= 3:
                        mapa = mapa_tent
                        cabecalho_idx = i
                        logger.debug(f"Cabeçalho parcelas linha {i}: {colunas}")
                        logger.debug(f"Mapa colunas: {mapa}")
                        break
            if cabecalho_idx >= 0:
                break

        if cabecalho_idx < 0:
            logger.info("Cabeçalho financeiro não encontrado no texto")
            return []

        # Campos numéricos na ordem do cabeçalho (excluindo nmens e dtvenc)
        campos_numericos = [
            mapa[idx] for idx in sorted(mapa.keys())
            if mapa[idx] not in ('nmens', 'dtvenc')
        ]
        if not campos_numericos:
            # Fallback: ordem padrão COFLUHAB
            campos_numericos = ['juros', 'amort', 'cm', 'sddev', 'seguro', 'tca', 'fcvs', 'rp', 'vlautent']

        PAT_DECIMAL = re.compile(r'\d{1,3}(?:\.\d{3})*,\d{2,6}')
        PAT_DATA_MENS = re.compile(r'^(\d{2}[/\-]\d{2}[/\-]\d{4})\s+0*(\d{1,4})')
        PAT_MENS_INICIO = re.compile(r'^0*(\d{1,4})\s')

        for linha in linhas[cabecalho_idx + 1:]:
            linha_s = linha.strip()
            if not linha_s:
                continue
            if re.match(r'^(total|soma|resumo|obs|notas|assin|\*)', linha_s, re.IGNORECASE):
                break

            p = {}
            m = PAT_DATA_MENS.match(linha_s)
            if m:
                d = self._parse_data_br(m.group(1))
                if d:
                    p['dtvenc'] = d
                p['nmens'] = int(m.group(2))
            else:
                m2 = PAT_MENS_INICIO.match(linha_s)
                if m2:
                    p['nmens'] = int(m2.group(1))

            if 'nmens' not in p:
                continue

            decimais = PAT_DECIMAL.findall(linha_s)
            if len(decimais) < 2:
                continue

            for j, campo in enumerate(campos_numericos):
                if j < len(decimais):
                    try:
                        p[campo] = self._parse_valor(decimais[j])
                    except Exception:
                        pass

            if any(k not in ('nmens', 'dtvenc') for k in p):
                parcelas.append(p)

        logger.info(f"_parse_parcelas_texto: {len(parcelas)} parcelas")
        return parcelas

    def assess_quality(self) -> Dict:
        """Gera resumo simples de qualidade para operação em lote com revisão assistida."""
        # Críticos: sem eles não é possível salvar o contrato nem identificar o mutuário
        criticos = ['codigo', 'nome', 'cpf', 'data_contrato']
        # Importantes para CADMUT/FH1
        importantes = [
            'conjunto', 'endereco', 'bairro', 'cidade', 'uf', 'cep',
            'prazo', 'sa', 'tx_juros', 'dtnasc', 'renda', 'tipoimovel',
        ]

        faltando_criticos = [campo for campo in criticos if not self.data.get(campo)]
        faltando_importantes = [campo for campo in importantes if not self.data.get(campo)]

        score = 100
        score -= 20 * len(faltando_criticos)
        score -= 5 * len(faltando_importantes)
        if self.data.get('parcelas') == []:
            score -= 10
        score = max(0, score)

        if score >= 80:
            status = 'alta'
        elif score >= 50:
            status = 'media'
        else:
            status = 'baixa'

        return {
            'score': score,
            'status': status,
            'faltando_criticos': faltando_criticos,
            'faltando_importantes': faltando_importantes,
        }

    def extract_all(self) -> Dict:
        """Extrai todos os campos do contrato"""
        logger.info(f"Iniciando extração de todos os campos do PDF: {self.pdf_path.name}")
        
        # Primeiro, extrai o texto com OCR
        self.extract_text_from_pdf()
        self.data['document_type'] = self.detect_document_type()

        # Quadro financeiro (preço de venda + condições de pagamento)
        self.extract_quadro_financeiro()
        
        # Extrai dados do CONTRATO
        self.extract_numero_contrato()
        self.extract_data_contrato()
        self.extract_conjunto()
        self.extract_prazo()
        self.extract_taxa_juros()
        self.extract_valor_imovel()
        self.extract_valor_financiado()
        self.extract_sistema_amortizacao()
        
        # Extrai dados do IMÓVEL/ENDEREÇO
        self.extract_endereco()
        self.extract_numero_imovel()
        self.extract_complemento()
        self.extract_bairro()
        self.extract_cidade()
        self.extract_uf()
        self.extract_cep()
        
        # Extrai dados do MUTUÁRIO
        self.extract_mutuario_nome()
        self.extract_cpf()
        self.extract_rg()
        self.extract_orgao_emissor()
        self.extract_data_nascimento()
        self.extract_telefone()
        self.extract_email()

        # Extrai campos CADMUT / FH1
        self.extract_cat_prof()
        self.extract_pr()
        self.extract_data_primeiro_venc()
        self.extract_prazo_fcvs()
        self.extract_tipo_operacao()
        self.extract_renda()
        self.extract_crenda()
        self.extract_codimovel()
        self.extract_tipoimovel()
        self.extract_ocorrencia()
        self.extract_data_evento()
        self.extract_situacao_contrato()

        # Extrai tabela de evolução financeira (parcelas)
        self.extract_parcelas()

        self.data['ocr_quality'] = self.assess_quality()

        logger.info(f"Extração completada. Campos encontrados: {list(self.data.keys())}")
        return self.data


class ContratoProcessor:
    """
    Processa contratos extraídos e cadastra no banco de dados
    """
    
    @staticmethod
    def validate_contrato_data(data: Dict) -> Tuple[bool, List[str]]:
        """Valida dados do contrato antes de cadastro"""
        errors = []
        
        # Campos obrigatórios
        if not data.get('codigo'):
            errors.append("Código do contrato é obrigatório")
        
        # Validação de formato
        if 'data_contrato' in data and not isinstance(data['data_contrato'], date):
            errors.append("Data do contrato inválida")
        
        if 'prazo' in data:
            try:
                prazo = int(data['prazo'])
                if prazo <= 0:
                    errors.append("Prazo deve ser maior que zero")
            except:
                errors.append("Prazo inválido")
        
        # Validação de valores
        for campo in ['tx_juros', 'vlprop', 'vlfinanc']:
            if campo in data:
                try:
                    if isinstance(data[campo], str):
                        Decimal(data[campo])
                    elif not isinstance(data[campo], Decimal):
                        Decimal(str(data[campo]))
                except:
                    errors.append(f"{campo} deve ser um número válido")
        
        return len(errors) == 0, errors

    @staticmethod
    @transaction.atomic
    def save_contrato(data: Dict, dry_run: bool = False) -> Tuple[bool, str]:
        """
        Salva contrato no banco de dados
        dry_run=True apenas valida sem salvar
        """
        # Valida dados
        valid, errors = ContratoProcessor.validate_contrato_data(data)
        if not valid:
            msg = f"Validação falhou: {'; '.join(errors)}"
            logger.error(msg)
            return False, msg
        
        try:
            # Prepara dados para o modelo Contrato
            # Usa None quando o campo não foi extraído — garante que campos
            # já corretos no banco não sejam sobrescritos com vazio/None
            contrato_data = {
                'codigo': data['codigo'],
                'conjunto': data.get('conjunto') or None,
                'ocorrencia': data.get('ocorrencia') or None,
                'cod_imovel': data.get('cod_imovel') or data.get('codimovel') or None,
                'data_contrato': data.get('data_contrato') or None,
                'data_primeiro_venc': data.get('data_primeiro_venc') or None,
                'sa': data.get('sa') or None,
                'tx_juros': data.get('tx_juros') or None,
                'prazo': data.get('prazo') or None,
                'cat_prof': data.get('cat_prof') or None,
                'pr': data.get('pr') or None,
                # Campos financeiros (novos)
                'vlfinanc': data.get('vlfinanc') or None,
                'vlprop':   data.get('vlprop')   or None,
                'prestacao_inicial': data.get('prestacao_inicial') or None,
            }

            # Remove campos None — só atualiza o que o OCR efetivamente extraiu
            contrato_data = {k: v for k, v in contrato_data.items() if v is not None}
            
            if dry_run:
                logger.info(f"[DRY RUN] Contrato a ser criado: {contrato_data}")
                n_parcelas = len(data.get('parcelas') or [])
                return True, f"Validação bem-sucedida (dry run) — {n_parcelas} parcela(s) detectada(s)"
            
            # Verifica se contrato já existe
            existing = Contrato.objects.filter(codigo=data['codigo']).first()
            if existing:
                logger.warning(f"Contrato {data['codigo']} já existe. Atualizando...")
                # Atualiza apenas os campos que foram extraídos
                for key, value in contrato_data.items():
                    if value is not None:
                        setattr(existing, key, value)
                # Se OCR descartou conjunto inválido, limpa lixo antigo em vez de preservá-lo
                if not data.get('conjunto') and existing.conjunto:
                    conjunto_old = str(existing.conjunto).strip().lower()
                    palavras = conjunto_old.split()
                    if len(conjunto_old) < 3 or (len(palavras) >= 3 and sum(1 for p in palavras if len(p) == 1) >= 2):
                        existing.conjunto = ''
                existing.save()
                contrato = existing
                msg_base = f"Contrato {data['codigo']} atualizado com sucesso"
            else:
                # Cria novo contrato
                contrato = Contrato.objects.create(**contrato_data)
                logger.info(f"Contrato {contrato.codigo} criado com sucesso")
                msg_base = f"Contrato {contrato.codigo} cadastrado com sucesso"

            # Salva parcelas (se existirem)
            parcelas_salvas = 0
            for p_dict in (data.get('parcelas') or []):
                nmens = p_dict.get('nmens')
                if not nmens:
                    continue
                campos_parcela = {k: v for k, v in p_dict.items() if k != 'nmens'}
                try:
                    ParcelaContrato.objects.update_or_create(
                        contrato=contrato,
                        nmens=nmens,
                        defaults=campos_parcela,
                    )
                    parcelas_salvas += 1
                except Exception as ep:
                    logger.warning(f"Parcela {nmens} não salva: {ep}")

            # Fallback financeiro do Quadro V: sem tabela de evolução, mas com prestação inicial
            if parcelas_salvas == 0 and data.get('prestacao_inicial'):
                try:
                    ParcelaContrato.objects.update_or_create(
                        contrato=contrato,
                        nmens=1,
                        defaults={
                            'dtvenc': data.get('data_primeiro_venc') or data.get('data_contrato'),
                            'vlautent': Decimal(str(data.get('prestacao_inicial'))),
                        },
                    )
                    parcelas_salvas = 1
                    logger.info("[QUADRO] Parcela 1 criada a partir da prestação inicial")
                except Exception as ep:
                    logger.warning(f"Não foi possível criar parcela inicial do quadro: {ep}")

            if parcelas_salvas:
                msg_base += f" | {parcelas_salvas} parcela(s) importada(s)"

            # -------------------------------------------------------
            # Salva / atualiza Mutuario vinculado a este contrato
            # -------------------------------------------------------
            mutuario = ContratoProcessor._save_mutuario(data, contrato)
            if mutuario:
                msg_base += f" | Mutuário '{mutuario.nome}' (id={mutuario.pk}) salvo"

            return True, msg_base
                
        except Exception as e:
            msg = f"Erro ao salvar contrato: {str(e)}"
            logger.error(msg)
            return False, msg

    @staticmethod
    def _save_mutuario(data: Dict, contrato: 'Contrato') -> Optional['Mutuario']:
        """
        Cria ou atualiza o Mutuario associado ao contrato extraído via OCR.
        Retorna o objeto Mutuario salvo, ou None se não houver nome disponível.
        """
        nome = (data.get('nome') or '').strip()
        if not nome:
            logger.warning("Mutuario não salvo: campo 'nome' ausente")
            return None

        cpf = (data.get('cpf') or '').strip()
        conjunto = (data.get('conjunto') or contrato.conjunto or '').strip()

        # Valores padrão para campos obrigatórios do modelo
        mutuario_fields = {
            'codigo':     (data.get('codigo_mutuario') or contrato.codigo or '')[:10],
            'codimovel':  (data.get('codimovel') or data.get('cod_imovel') or contrato.cod_imovel or '')[:20],
            'conjunto':   conjunto[:10],
            'conjseg':    (data.get('conjseg') or '')[:10],
            'nome':       nome[:100],
            'ident':      (data.get('ident') or '')[:20],
            'orgao':      (data.get('orgao') or '')[:20],
            'dtnasc':     data.get('dtnasc'),
            'cpf':        cpf[:14],
            'renda':      data.get('renda'),
            'crenda':     data.get('crenda'),
            'endereco':   (data.get('endereco') or '')[:150],
            'numero':     (data.get('numero') or '')[:10],
            'compl':      (data.get('compl') or '')[:50],
            'tipoimovel': (data.get('tipoimovel') or '')[:50],
            'bairro':     (data.get('bairro') or '')[:50],
            'cidade':     (data.get('cidade') or '')[:50],
            'cep':        (data.get('cep') or '')[:10],
            'uf':         (data.get('uf') or '')[:2],
            'telefone':   (data.get('telefone') or '')[:20],
            'email':      (data.get('email') or '')[:100],
        }

        try:
            # 1ª tentativa: busca por CPF (mais confiável)
            mutuario = None
            if cpf:
                mutuario = Mutuario.objects.filter(cpf=cpf).first()

            # 2ª tentativa: busca por conjunto + nome
            if mutuario is None and conjunto:
                mutuario = Mutuario.objects.filter(conjunto=conjunto, nome__iexact=nome).first()

            # Atualiza apenas campos com valor (não sobrescreve com vazio)
            update_fields = {k: v for k, v in mutuario_fields.items()
                             if v not in (None, '', [], {})}

            if mutuario is not None:
                for k, v in update_fields.items():
                    setattr(mutuario, k, v)
                mutuario.save()
                logger.info(f"Mutuario atualizado: {mutuario.nome} (id={mutuario.pk})")
            else:
                mutuario = Mutuario.objects.create(**mutuario_fields)
                logger.info(f"Mutuario criado: {mutuario.nome} (id={mutuario.pk})")

            # Insere/atualiza mapeamento contrato → mutuario
            try:
                with _db_connection.cursor() as cur:
                    cur.execute(
                        """
                        INSERT OR REPLACE INTO contrato_mutuario_map
                            (contrato_id, mutuario_id, score, method)
                        VALUES (%s, %s, %s, %s)
                        """,
                        [contrato.pk, mutuario.pk, 1.0, 'ocr'],
                    )
            except Exception as emap:
                logger.warning(f"Não foi possível inserir contrato_mutuario_map: {emap}")

            return mutuario

        except Exception as e:
            logger.error(f"Erro ao salvar Mutuario: {e}")
            return None


class ProcessadorLoteContratos:
    """
    Processa múltiplos PDFs de uma pasta
    """
    
    def __init__(self, pasta_pdfs: str):
        """
        Inicializa com caminho da pasta contendo PDFs
        pasta_pdfs: caminho absoluto ou relativo à pasta do projeto
        """
        self.pasta_pdfs = Path(pasta_pdfs)
        if not self.pasta_pdfs.exists():
            raise FileNotFoundError(f"Pasta não encontrada: {self.pasta_pdfs}")
        
        self.resultados = {
            'sucesso': [],
            'erro': [],
            'total': 0
        }

    def processar(self, dry_run: bool = False) -> Dict:
        """
        Processa todos os PDFs da pasta
        dry_run=True apenas testa sem salvar
        """
        logger.info(f"Iniciando processamento de PDFs em: {self.pasta_pdfs}")
        
        # Lista todos os PDFs
        pdfs = list(self.pasta_pdfs.glob('**/*.pdf'))
        if not pdfs:
            logger.warning(f"Nenhum PDF encontrado em {self.pasta_pdfs}")
            return self.resultados
        
        logger.info(f"Encontrados {len(pdfs)} PDFs para processar")
        self.resultados['total'] = len(pdfs)
        
        # Processa cada PDF
        for pdf_file in pdfs:
            try:
                logger.info(f"\nProcessando: {pdf_file.name}")
                
                # Extrai dados com OCR
                extractor = ContratoOCRExtractor(str(pdf_file))
                dados = extractor.extract_all()
                
                if not dados:
                    logger.warning(f"Nenhum dado extraído de {pdf_file.name}")
                    self.resultados['erro'].append({
                        'arquivo': pdf_file.name,
                        'erro': 'Nenhum dado extraído'
                    })
                    continue
                
                # Salva no banco
                sucesso, mensagem = ContratoProcessor.save_contrato(dados, dry_run=dry_run)
                
                if sucesso:
                    self.resultados['sucesso'].append({
                        'arquivo': pdf_file.name,
                        'codigo': dados.get('codigo'),
                        'mensagem': mensagem
                    })
                    logger.info(f"✓ {mensagem}")
                else:
                    self.resultados['erro'].append({
                        'arquivo': pdf_file.name,
                        'erro': mensagem
                    })
                    logger.error(f"✗ {mensagem}")
                    
            except Exception as e:
                msg = f"Erro ao processar {pdf_file.name}: {str(e)}"
                logger.error(msg)
                self.resultados['erro'].append({
                    'arquivo': pdf_file.name,
                    'erro': str(e)
                })
        
        return self.resultados

    def gerar_relatorio(self) -> str:
        """Gera relatório de processamento"""
        relatorio = f"""
========================================
RELATÓRIO DE PROCESSAMENTO OCR
========================================

Total de PDFs: {self.resultados['total']}
Sucesso: {len(self.resultados['sucesso'])}
Erros: {len(self.resultados['erro'])}

--- CONTRATOS CADASTRADOS COM SUCESSO ---
"""
        for item in self.resultados['sucesso']:
            relatorio += f"\n  • {item['arquivo']}: {item['codigo']}"
        
        if self.resultados['erro']:
            relatorio += "\n\n--- ERROS ---\n"
            for item in self.resultados['erro']:
                relatorio += f"\n  • {item['arquivo']}: {item['erro']}"
        
        relatorio += "\n\n========================================\n"
        return relatorio


# Script para execução via CLI
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python ocr_contrato_processor.py <pasta_pdfs> [--dry-run]")
        print("Exemplo: python ocr_contrato_processor.py ./pdfs_contratos")
        sys.exit(1)
    
    pasta = sys.argv[1]
    dry_run = '--dry-run' in sys.argv
    
    processador = ProcessadorLoteContratos(pasta)
    resultados = processador.processar(dry_run=dry_run)
    
    # Salva relatório em arquivo
    relatorio = processador.gerar_relatorio()
    print(relatorio)
    
    with open('relatorio_ocr_contrato.txt', 'w', encoding='utf-8') as f:
        f.write(relatorio)
    
    logger.info("Processamento concluído. Relatório salvo em relatorio_ocr_contrato.txt")
