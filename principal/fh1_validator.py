# principal/fh1_validator.py
from dataclasses import dataclass
from datetime import datetime
import re

NUMERIC_RE = re.compile(r"^\d+$")

@dataclass
class FH1ValidationResult:
    ok: bool
    errors: list

class FH1ValidationError(Exception):
    pass

def _is_ascii_printable_or_space(s: str) -> bool:
    """CEF geralmente aceita A-Z, 0-9, espaço e pontuação mínima.
    Check conservador: ASCII 32..126."""
    return all(32 <= ord(ch) <= 126 for ch in s)

def validate_fixed_length(line: str, expected_len: int, label: str, errors: list):
    if len(line) != expected_len:
        errors.append(f"{label}: tamanho inválido (len={len(line)}; esperado={expected_len})")

def validate_numeric_slice(line: str, start: int, end: int, label: str, errors: list):
    """start/end: 0-based, end exclusive"""
    if start >= len(line) or end > len(line):
        errors.append(f"{label}: índices fora dos limites [{start}:{end}] para linha de {len(line)} bytes")
        return
    piece = line[start:end]
    if not NUMERIC_RE.match(piece):
        errors.append(f"{label}: esperado apenas dígitos em [{start}:{end}], veio [{piece}]")

def validate_nonzero_numeric_slice(line: str, start: int, end: int, label: str, errors: list):
    """Valida campo numérico que não pode vir zerado."""
    if start >= len(line) or end > len(line):
        errors.append(f"{label}: índices fora dos limites [{start}:{end}] para linha de {len(line)} bytes")
        return
    piece = line[start:end]
    if not NUMERIC_RE.match(piece):
        errors.append(f"{label}: esperado apenas dígitos em [{start}:{end}], veio [{piece}]")
        return
    if int(piece) == 0:
        errors.append(f"{label}: campo obrigatório zerado em [{start}:{end}] [{piece}].")

def validate_exact_slice(line: str, start: int, end: int, expected: str, label: str, errors: list):
    if start >= len(line) or end > len(line):
        errors.append(f"{label}: índices fora dos limites [{start}:{end}] para linha de {len(line)} bytes")
        return
    piece = line[start:end]
    if piece != expected:
        errors.append(f"{label}: valor divergente em [{start}:{end}] (veio [{piece}] esperado [{expected}])")

def validate_charset(line: str, label: str, errors: list):
    if not _is_ascii_printable_or_space(line):
        errors.append(f"{label}: contém caracteres fora de ASCII 32..126 (risco de rejeição/encoding)")

def validate_fh1_record_I(
    linha_i: str,
    expected_vaf3: str | None = None,
    expected_len: int = 430,
    vaf3_start_0based: int = 374,
    vaf3_end_0based: int = 388,
):
    """Validações mínimas e críticas do Registro I (Habilitação)."""
    errors = []
    validate_fixed_length(linha_i, expected_len, "REGISTRO I", errors)
    validate_charset(linha_i, "REGISTRO I", errors)

    # Validações extras recomendadas
    # UFS (posições 1-2) = '33'
    validate_exact_slice(linha_i, 0, 2, "33", "UFS (1-2)", errors)
    
    # Matrícula (posições 3-8) = '000044'
    validate_exact_slice(linha_i, 2, 8, "000044", "MATRÍCULA (3-8)", errors)
    
    # Tipo de registro (posição 23) = '1'
    validate_exact_slice(linha_i, 22, 23, "1", "TIPO REGISTRO (23)", errors)

    # VAF3 (Campo 60) - posições 375-388 (1-based) => [374:388] (0-based)
    validate_numeric_slice(linha_i, vaf3_start_0based, vaf3_end_0based, "VAF3 (Campo 60 / Pos 375-388)", errors)
    if expected_vaf3 is not None:
        validate_exact_slice(linha_i, vaf3_start_0based, vaf3_end_0based, expected_vaf3, "VAF3 (Campo 60 / Pos 375-388)", errors)

    return FH1ValidationResult(ok=(len(errors) == 0), errors=errors)

def validate_header_trailer(
    header: str,
    trailer: str,
    expected_len: int = 430
):
    errors = []
    validate_fixed_length(header, expected_len, "HEADER (Tipo 0)", errors)
    validate_fixed_length(trailer, expected_len, "TRAILER (Tipo 9)", errors)
    validate_charset(header, "HEADER (Tipo 0)", errors)
    validate_charset(trailer, "TRAILER (Tipo 9)", errors)
    
    # Validar tipo de registro do header
    if len(header) >= 9:
        validate_exact_slice(header, 8, 9, "0", "HEADER TIPO (9)", errors)
    
    # Validar tipo de registro do trailer
    if len(trailer) >= 9:
        validate_exact_slice(trailer, 8, 9, "9", "TRAILER TIPO (9)", errors)
    
    return FH1ValidationResult(ok=(len(errors) == 0), errors=errors)

def write_audit_log(path: str, contrato_id: int, header: str, linha_i: str, trailer: str, validation_errors: list):
    """Log de auditoria: grava o essencial + erros + slices críticos."""
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n" + "="*90 + "\n")
            f.write(f"TS: {datetime.now().isoformat()}\n")
            f.write(f"CONTRATO_ID: {contrato_id}\n")
            f.write(f"LEN_HEADER: {len(header)} | LEN_I: {len(linha_i)} | LEN_TRAILER: {len(trailer)}\n")
            if len(linha_i) >= 388:
                f.write(f"VAF3_375_388: [{linha_i[374:388]}]\n")
            else:
                f.write(f"VAF3_375_388: [LINHA MUITO CURTA]\n")
            if validation_errors:
                f.write("STATUS: FAIL\n")
                for e in validation_errors:
                    f.write(f"- {e}\n")
            else:
                f.write("STATUS: OK\n")
    except Exception as e:
        print(f"Erro ao escrever log de auditoria: {e}")


def run_fh1_precheck_agent(header_conteudo: str, dados_conteudo: str, expected_ufs: str | None = None, expected_matricula: str | None = None):
    """
    Agente de pré-check para lote FH1 (header + múltiplos registros I).
    Retorna dicionário com status e lista de problemas críticos.
    """
    errors = []
    warnings = []

    header = (header_conteudo or '').splitlines()[0] if (header_conteudo or '').splitlines() else ''
    linhas_dados = [ln for ln in (dados_conteudo or '').splitlines() if ln]

    if not header:
        errors.append('HEADER ausente.')
        return {'ok': False, 'errors': errors, 'warnings': warnings, 'total_registros': 0}

    if not linhas_dados:
        errors.append('Arquivo de DADOS vazio.')
        return {'ok': False, 'errors': errors, 'warnings': warnings, 'total_registros': 0}

    # Regras básicas de tamanho e tipo do HEADER.
    validate_fixed_length(header, 430, 'HEADER', errors)
    validate_charset(header, 'HEADER', errors)
    if len(header) >= 23 and header[22:23] != '0':
        errors.append(f"HEADER tipo inválido na posição 23: [{header[22:23]}] (esperado '0').")

    id_lote_header = header[405:430] if len(header) >= 430 else ''
    ufs_header = header[0:2] if len(header) >= 8 else ''
    mat_header = header[2:8] if len(header) >= 8 else ''

    if expected_ufs and ufs_header != expected_ufs:
        warnings.append(f'UFS no HEADER difere do esperado ({ufs_header} != {expected_ufs}).')
    if expected_matricula and mat_header != expected_matricula:
        warnings.append(f'Matrícula no HEADER difere da esperada ({mat_header} != {expected_matricula}).')

    contratos_vistos = set()
    contratos_duplicados = set()

    for i, linha in enumerate(linhas_dados, start=1):
        validate_fixed_length(linha, 430, f'DADOS linha {i}', errors)
        validate_charset(linha, f'DADOS linha {i}', errors)

        if len(linha) < 430:
            continue

        # Tipo registro I (posição 23)
        if linha[22:23] != '1':
            errors.append(f"DADOS linha {i}: tipo de registro inválido [{linha[22:23]}] (esperado '1').")

        # ID de lote (campos * header/dados devem ser iguais)
        if linha[405:430] != id_lote_header:
            errors.append(f'DADOS linha {i}: identificação do lote divergente do HEADER (pos. 406-430).')

        # Forma e tipo do movimento no final
        if linha[422:423] != 'S':
            errors.append(f"DADOS linha {i}: FORMA DE ENVIO inválida [{linha[422:423]}] (esperado 'S').")
        if linha[423:424] != 'I':
            errors.append(f"DADOS linha {i}: TIPO MOVIMENTO inválido [{linha[423:424]}] (esperado 'I').")

        # UFS/matrícula no corpo também devem bater com o HEADER
        if linha[0:2] != ufs_header:
            errors.append(f'DADOS linha {i}: UFS diferente do HEADER.')
        if linha[2:8] != mat_header:
            errors.append(f'DADOS linha {i}: matrícula diferente do HEADER.')

        # Contrato no agente (posições 9-21) deve ter 13 dígitos (com zeros à esquerda quando aplicável)
        contrato_bruto = linha[8:21]
        if not NUMERIC_RE.match(contrato_bruto):
            errors.append(f"DADOS linha {i}: contrato inválido em 9-21 [{contrato_bruto}] (esperado 13 dígitos).")

        # Taxa Juros Evento (posições 341-346) é obrigatória e não pode ser zero
        taxa_evento = linha[340:346]
        if not NUMERIC_RE.match(taxa_evento):
            errors.append(f"DADOS linha {i}: TAXA JUROS EVENTO inválida em 341-346 [{taxa_evento}] (esperado numérico).")
        elif int(taxa_evento) == 0:
            errors.append(f"DADOS linha {i}: TAXA JUROS EVENTO zerada em 341-346; campo obrigatório.")

        # Demais campos obrigatórios reportados pela CEF como preenchidos com zero.
        validate_nonzero_numeric_slice(linha, 90, 95, f'DADOS linha {i}: CODIGO MUNICIPIO 91-95', errors)
        validate_nonzero_numeric_slice(linha, 141, 153, f'DADOS linha {i}: VALOR GARANTIA 142-153', errors)
        validate_nonzero_numeric_slice(linha, 195, 198, f'DADOS linha {i}: PRAZO 196-198', errors)
        validate_nonzero_numeric_slice(linha, 198, 204, f'DADOS linha {i}: TAXA JUROS 199-204', errors)
        validate_nonzero_numeric_slice(linha, 213, 215, f'DADOS linha {i}: RR 214-215', errors)
        validate_nonzero_numeric_slice(linha, 218, 221, f'DADOS linha {i}: PRAZO FCVS 219-221', errors)
        validate_nonzero_numeric_slice(linha, 221, 227, f'DADOS linha {i}: TAXA FCVS 222-227', errors)
        validate_nonzero_numeric_slice(linha, 316, 318, f'DADOS linha {i}: OR/CO 317-318', errors)

        st = linha[211:212]
        if st == '0':
            errors.append(f"DADOS linha {i}: ST 212 preenchido com zero; campo obrigatório.")

        contrato = linha[8:21].strip()
        if contrato:
            if contrato in contratos_vistos:
                contratos_duplicados.add(contrato)
            contratos_vistos.add(contrato)

    if contratos_duplicados:
        preview = ', '.join(sorted(list(contratos_duplicados))[:10])
        errors.append(f'Contratos duplicados no DADOS: {preview}')

    return {
        'ok': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'total_registros': len(linhas_dados),
    }
