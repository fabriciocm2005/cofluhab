"""
Camada híbrida de OCR para contratos SFH/BNH.

Objetivo:
- Aproveitar a extração existente (OCR principal)
- Tentar recuperar campos críticos com padrões contextuais
- Classificar cada campo como auto ou revisar
- Reduzir digitação manual no upload em lote
"""

from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Tuple


def _parse_decimal_br(raw: str) -> Decimal | None:
    if raw is None:
        return None
    txt = str(raw).strip()
    if not txt:
        return None
    txt = txt.replace(" ", "")
    txt = txt.replace(".", "").replace(",", ".")
    try:
        return Decimal(txt)
    except InvalidOperation:
        return None


def _parse_date(raw: Any) -> date | None:
    if raw is None:
        return None
    if isinstance(raw, date):
        return raw
    txt = str(raw).strip()
    if not txt:
        return None

    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y", "%d-%m-%Y", "%d-%m-%y"):
        try:
            d = datetime.strptime(txt, fmt).date()
            if d.year < 100:
                year = 1900 + d.year if d.year >= 50 else 2000 + d.year
                d = date(year, d.month, d.day)
            return d
        except ValueError:
            continue
    return None


def _first_group(pattern: str, text: str, flags: int = re.IGNORECASE) -> str | None:
    m = re.search(pattern, text, flags)
    if not m:
        return None
    return (m.group(1) or "").strip() or None


def _ascii_lower(text: str) -> str:
    norm = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in norm if not unicodedata.combining(c)).lower()


def _clean_ocr_numeric_token(token: str) -> str:
    """Limpa ruído típico de OCR em números monetários/taxas."""
    if token is None:
        return ""
    txt = str(token).strip().lower()

    # Correções comuns de OCR em contexto numérico
    trans = {
        "o": "0",
        "q": "0",
        "d": "0",
        "i": "1",
        "l": "1",
        "|": "1",
        "b": "8",
    }
    txt = "".join(trans.get(ch, ch) for ch in txt)

    # Mantém somente elementos de número BR
    txt = re.sub(r"[^0-9,\.-]", "", txt)

    # Remove múltiplos separadores consecutivos
    txt = re.sub(r"([,\.\-]){2,}", r"\1", txt)
    return txt


def _parse_decimal_ocr(raw: str) -> Decimal | None:
    cleaned = _clean_ocr_numeric_token(raw)
    if not cleaned:
        return None

    # Trata formatos como 16.32.9,35 -> 16329,35
    if "," in cleaned:
        int_part, frac_part = cleaned.rsplit(",", 1)
        int_digits = re.sub(r"\D", "", int_part)
        frac_digits = re.sub(r"\D", "", frac_part)[:2]
        if not int_digits:
            return None
        candidate = f"{int_digits}.{frac_digits or '00'}"
    else:
        digits = re.sub(r"\D", "", cleaned)
        if len(digits) < 3:
            return None
        candidate = f"{digits[:-2]}.{digits[-2:]}"

    try:
        return Decimal(candidate)
    except InvalidOperation:
        return None


def _parse_percent_ocr(raw: str) -> Decimal | None:
    cleaned = _clean_ocr_numeric_token(raw)
    if not cleaned:
        return None

    # Ex.: "4", "04,8", "4,90", "4.8"
    if "," in cleaned or "." in cleaned:
        num = cleaned.replace(".", "").replace(",", ".")
    else:
        digits = re.sub(r"\D", "", cleaned)
        if not digits:
            return None
        num = digits

    try:
        val = Decimal(num)
    except InvalidOperation:
        return None

    if Decimal("0") < val < Decimal("30"):
        return val
    return None


def _extract_date_from_window(window: str) -> date | None:
    # Primeiro tenta o caminho "normal"
    m = re.search(r"(\d{1,2})\s*[\./\-]\s*(\d{1,2})\s*[\./\-]\s*(\d{2,4})", window)
    if not m:
        return None

    dd, mm, yy = m.group(1), m.group(2), m.group(3)
    try:
        d = int(dd)
        mth = int(mm)
        y = int(yy)
        if y < 100:
            y = 1900 + y if y >= 50 else 2000 + y
        return date(y, mth, d)
    except Exception:
        return None


def _should_replace_existing(field: str, current_value: Any, new_value: Any) -> bool:
    if _is_blank(current_value):
        return True

    if field in {"prestacao_inicial", "vlfinanc"}:
        cur = _parse_decimal_br(str(current_value))
        new = _parse_decimal_br(str(new_value))
        if new and cur and cur <= Decimal("100") < new:
            return True

    return False


def _extract_contextual_candidates(text: str) -> Dict[str, Any]:
    """Recupera campos com padrões focados em trechos de contrato BNH."""
    recovered: Dict[str, Any] = {}
    text_norm = _ascii_lower(text)

    # Prazo típico na seção V: "Sera feito ... 120 ... meses"
    prazo = _first_group(r"sera\s+feito[\s\S]{0,80}?(\d{2,3})\s*\.*\s*meses", text_norm)
    if prazo and 12 <= int(prazo) <= 420:
        recovered["prazo"] = int(prazo)

    # CPF do comprador
    cpf_match = _first_group(r"(\d{3}[\.\s]?\d{3}[\.\s]?\d{3}[\-\s]?\d{2})", text_norm)
    if cpf_match:
        digits = re.sub(r"\D", "", cpf_match)
        if len(digits) == 11:
            recovered["cpf"] = f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"

    # Nome após "nome:" até CIC/CPF/Nacionalidade
    nome_match = _first_group(
        r"nome\s*[:\-]?\s*([a-z\s\.'/]{6,80}?)(?:\s+cic|\s+cpf|\s+nacionalidade|\s+identidade|\s+estado)"
        ,
        text_norm,
    )
    if nome_match:
        nome = re.sub(r"\s+", " ", nome_match).strip(" .,:;-")
        if len(nome) >= 6:
            recovered["nome"] = nome.title()

    # Prestação total com acessórios: "totalizando prestação mais acessório ... Cr$ 195.769,99"
    # Prestação inicial: "sendo a inicial de cr$ ..."
    prest_match = _first_group(
        r"sendo\s+a\s+inicial\s+de\s*c\s*[ri1l]?\s*\$?\s*([0-9oqdilb\|\*\?\.,\-\s]{4,40})",
        text_norm,
    )
    val_prest = _parse_decimal_ocr(prest_match) if prest_match else None
    if val_prest and Decimal("100") < val_prest < Decimal("1000000000"):
        recovered["prestacao_inicial"] = float(val_prest)

    # Fallback de prestação por "totalizando"
    if "prestacao_inicial" not in recovered:
        total = _first_group(
            r"totalizando[\s\S]{0,120}?(?:cr\$|crs)?\s*([0-9oqdilb\|\.,\-\s]{4,30})",
            text_norm,
        )
        val_total = _parse_decimal_ocr(total) if total else None
        if val_total and Decimal("100") < val_total < Decimal("1000000000"):
            recovered["prestacao_inicial"] = float(val_total)

    # Taxa nominal pode aparecer quebrada, então exige presença explícita de "juros"
    tx = _first_group(
        r"taxa\s+de\s+juros\s+nomi\w*\s+de\s*([0-9oqdilb\|\.,\-\s]{1,20})\s*a\.?\s*a\.?",
        text_norm,
    )
    if not tx:
        tx = _first_group(r"juros[\s\S]{0,60}?([0-9oqdilb\|\.,\-]{2,14})\s*(?:%|a\.a)", text_norm)
    if tx:
        tx_num = _parse_percent_ocr(tx)
        if tx_num and Decimal("0") < tx_num < Decimal("30"):
            recovered["tx_juros"] = float(tx_num)

    # Data da primeira prestação (somente quando rotulada)
    d1_match = re.search(r"vencendo\-se\s+a\s+primeira\s+prestacao([\s\S]{0,80})", text_norm)
    if d1_match:
        d1_parsed = _extract_date_from_window(d1_match.group(1))
        if d1_parsed:
            recovered["data_primeiro_venc"] = d1_parsed.isoformat()

    # Valor financiado: "valor do financiamento: cr$ ..."
    vf = _first_group(
        r"valor\s+do\s+financia\w*\s*:\s*c(?:r\$|rs|\$)?\s*([0-9oqdilb\|\.,\-\s]{4,34})",
        text_norm,
    )
    vf_num = _parse_decimal_ocr(vf) if vf else None
    if vf_num and Decimal("100") < vf_num < Decimal("100000000000"):
        recovered["vlfinanc"] = float(vf_num)

    # Data de contrato (fallback): procura data próxima ao bloco "contrato"
    if "data_contrato" not in recovered:
        m_city_date = re.search(r"rio\s+de\s+janeiro[\s\S]{0,40}?([0-9][0-9\./\-\s]{4,16}[0-9])", text_norm)
        if m_city_date:
            dc_city = _extract_date_from_window(m_city_date.group(1))
            if dc_city and 1960 <= dc_city.year <= 2000:
                recovered["data_contrato"] = dc_city.isoformat()

    if "data_contrato" not in recovered:
        m_contrato = re.search(r"contrato[\s\S]{0,220}", text_norm)
        if m_contrato:
            dc = _extract_date_from_window(m_contrato.group(0))
            if dc and 1960 <= dc.year <= 2000:
                recovered["data_contrato"] = dc.isoformat()

    return recovered


def _is_blank(v: Any) -> bool:
    if v is None:
        return True
    if isinstance(v, str) and not v.strip():
        return True
    return False


def _score_field(field: str, value: Any, dados: Dict[str, Any]) -> Tuple[str, float, str]:
    """Retorna (status, confianca, motivo)."""
    if _is_blank(value):
        return "revisar", 0.0, "campo ausente"

    if field in {"prazo"}:
        try:
            n = int(value)
        except (ValueError, TypeError):
            return "revisar", 0.2, "prazo inválido"
        if 12 <= n <= 420:
            return "auto", 0.9, "intervalo válido"
        return "revisar", 0.3, "fora do intervalo SFH"

    if field in {"tx_juros"}:
        try:
            tx = Decimal(str(value))
        except InvalidOperation:
            return "revisar", 0.2, "taxa inválida"
        if Decimal("0") < tx < Decimal("30"):
            return "auto", 0.9, "taxa plausível"
        return "revisar", 0.3, "taxa fora da faixa"

    if field in {"data_contrato", "data_primeiro_venc"}:
        d = _parse_date(value)
        if not d:
            return "revisar", 0.2, "data inválida"
        if d.year < 1960 or d > date.today():
            return "revisar", 0.3, "data fora da faixa"
        if field == "data_primeiro_venc":
            dc = _parse_date(dados.get("data_contrato"))
            if dc and d < dc:
                return "revisar", 0.2, "1º vencimento anterior ao contrato"
            if dc and (d - dc).days < 20:
                return "revisar", 0.5, "1º vencimento muito próximo da assinatura"
        return "auto", 0.85, "data plausível"

    if field in {"cpf"}:
        digits = re.sub(r"\D", "", str(value))
        if len(digits) == 11:
            return "auto", 0.9, "formato CPF ok"
        return "revisar", 0.3, "CPF incompleto"

    if field in {"sa"}:
        sa = str(value).strip().upper()
        if sa in {"SAC", "PRICE", "SACRE", "MISTO", "1", "2", "4"}:
            return "auto", 0.9, "sistema reconhecido"
        return "revisar", 0.4, "sistema não reconhecido"

    if field in {"vlfinanc", "prestacao_inicial"}:
        dec = _parse_decimal_br(value)
        if dec and dec > 0:
            return "auto", 0.85, "valor numérico plausível"
        return "revisar", 0.2, "valor inválido"

    if field in {"codigo", "nome", "endereco", "cidade", "uf"}:
        txt = str(value).strip()
        if len(txt) < 2:
            return "revisar", 0.2, "texto muito curto"
        if field == "uf" and len(txt) != 2:
            return "revisar", 0.3, "UF inválida"
        return "auto", 0.8, "texto preenchido"

    return "auto", 0.7, "campo preenchido"


def analisar_ocr_hibrido(dados: Dict[str, Any], texto_extraido: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Aplica camada híbrida de recuperação + classificação de confiança.

    Retorna:
    - dados_final: dict pronto para persistência
    - relatorio: dict para UI (auto/revisar)
    """
    dados_final = dict(dados or {})
    texto = texto_extraido or ""

    recovered = _extract_contextual_candidates(texto)
    recovered_applied: Dict[str, Any] = {}
    for key, value in recovered.items():
        if _should_replace_existing(key, dados_final.get(key), value):
            dados_final[key] = value
            recovered_applied[key] = value

    campos_criticos = [
        "codigo",
        "data_contrato",
        "data_primeiro_venc",
        "prazo",
        "tx_juros",
        "sa",
        "vlfinanc",
        "prestacao_inicial",
        "nome",
        "cpf",
        "endereco",
        "cidade",
        "uf",
    ]

    auto: List[Dict[str, Any]] = []
    revisar: List[Dict[str, Any]] = []
    soma = Decimal("0")

    for field in campos_criticos:
        val = dados_final.get(field)
        status, conf, motivo = _score_field(field, val, dados_final)
        soma += Decimal(str(conf))
        item = {
            "campo": field,
            "valor": val,
            "confianca": float(round(conf, 2)),
            "motivo": motivo,
            "origem": "recuperado" if field in recovered_applied else "ocr",
        }
        if status == "auto":
            auto.append(item)
        else:
            revisar.append(item)

    score = int((soma / Decimal(str(len(campos_criticos)))) * 100)
    status = "alta" if score >= 85 else "media" if score >= 65 else "baixa"

    relatorio = {
        "score": score,
        "status": status,
        "campos_auto": auto,
        "campos_revisar": revisar,
        "qtd_auto": len(auto),
        "qtd_revisar": len(revisar),
        "recuperados": recovered_applied,
    }

    return dados_final, relatorio
