"""
simulador_sfh.py — Motor de simulação de contratos SFH/BNH

Simula a evolução mês a mês de um contrato habitacional do SFH a partir
dos parâmetros básicos extraídos do PDF, sem necessidade de parcelas reais.

Legislação de referência:
- Lei 4.380/64 (BNH, SFH, FCVS)
- Decreto-lei 2.065/83 (PES/CP — Plano de Equivalência Salarial por
  Capacidade de Pagamento)
- Lei 8.004/90 (transferência de financiamento)
- Sistemas de amortização: SAC (constante), PRICE, SACRE, MISTO
- Correção Monetária: ORTN (1964-86), OTN (1986-89), BTNF/TR (1989+)
- PES: prestação reajustada anualmente pelo índice salarial (= UPC/SM)
"""

from __future__ import annotations

import os
import csv
from datetime import date
from dateutil.relativedelta import relativedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Constantes e moedas
# ---------------------------------------------------------------------------

MOEDA_POR_PERIODO = [
    (date(1994, 7, 1),  'R$'),
    (date(1993, 8, 1),  'CR$'),    # Cruzeiro Real
    (date(1990, 3, 16), 'Cr$90'),  # Cruzeiro (pós Cruzado Novo, moeda interna)
    (date(1989, 1, 16), 'NCz$'),   # Cruzado Novo
    (date(1986, 2, 28), 'Cz$'),    # Cruzado
    (date(1900, 1,  1), 'Cr$'),    # Cruzeiro (pré-Cruzado)
]
MOEDA_DISPLAY = {
    'R$': 'R$', 'CR$': 'CR$', 'Cr$90': 'CR$',
    'NCz$': 'NCz$', 'Cz$': 'Cz$', 'Cr$': 'Cr$',
}

# Redenominações em ordem CRONOLÓGICA (da mais antiga para a mais nova)
# fator = 1 moeda_nova equivale a X moeda_antiga (divide o valor por fator)
REDENOMINACOES = [
    (date(1986, 2, 28), Decimal('1000')),   # Cz$ = 1/1000 Cr$
    (date(1989, 1, 16), Decimal('1000')),   # NCz$ = 1/1000 Cz$
    (date(1990, 3, 16), Decimal('1')),      # Cr$90 = NCz$ (1:1)
    (date(1993, 8,  1), Decimal('1000')),   # CR$ = 1/1000 Cr$90
    (date(1994, 7,  1), Decimal('2750')),   # R$ = 1/2750 CR$
]

D0 = Decimal('0')
D1 = Decimal('1')
TWO = Decimal('2')
CENTS = Decimal('0.01')
SIX_DEC = Decimal('0.000001')


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _moeda(d: date) -> str:
    for limite, simbolo in MOEDA_POR_PERIODO:
        if d >= limite:
            return simbolo
    return 'Cr$'


def _carregar_indices_csv(path: str) -> Dict[str, Decimal]:
    """Carrega CSV com colunas AAAA-MM,indice (fracional, ex: 0.203 = 20.3%)."""
    indices: Dict[str, Decimal] = {}
    if not os.path.exists(path):
        return indices
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            mes = row.get('AAAA-MM', '').strip()
            val = row.get('indice', '').strip()
            if mes and val:
                try:
                    indices[mes] = Decimal(val)
                except Exception:
                    pass
    return indices


def carregar_indices_pes(csv_path: Optional[str] = None) -> Dict[str, Decimal]:
    """
    Carrega o salário mínimo nominal mensal para cálculo do fator PES.
    Retorna {'AAAA-MM': Decimal(sm_normalizado)}.
    O fator de reajuste PES entre mês A e mês B = sm[B] / sm[A].
    CSV esperado: indices_pes.csv com colunas AAAA-MM, sm_nominal, fator_reajuste.
    """
    if not csv_path or not os.path.exists(csv_path):
        return {}
    indices: Dict[str, Decimal] = {}
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            mes = row.get('AAAA-MM', '').strip()
            val = row.get('sm_nominal', '').strip()
            if mes and val:
                try:
                    indices[mes] = Decimal(val)
                except Exception:
                    pass
    return indices


def carregar_indices_sfh(csv_path: Optional[str] = None) -> Dict[str, Decimal]:
    """
    Retorna dicionário {'AAAA-MM': Decimal(indice_mensal)}.
    Prioridade: CSV → valores embutidos.
    """
    # Índices mínimos embutidos (ORTN/OTN estimados — use o CSV completo para precisão)
    embutidos: Dict[str, Decimal] = {
        # ORTN ~ INPC mensal estimado (valores históricos aproximados)
        '1983-03': Decimal('0.110'), '1983-04': Decimal('0.118'),
        '1983-05': Decimal('0.120'), '1983-06': Decimal('0.130'),
        '1983-07': Decimal('0.145'), '1983-08': Decimal('0.140'),
        '1983-09': Decimal('0.148'), '1983-10': Decimal('0.140'),
        '1983-11': Decimal('0.145'), '1983-12': Decimal('0.155'),
        '1984-01': Decimal('0.203'), '1984-02': Decimal('0.250'),
        '1984-03': Decimal('0.300'), '1984-04': Decimal('0.280'),
        '1984-05': Decimal('0.320'), '1984-06': Decimal('0.290'),
        '1984-07': Decimal('0.310'), '1984-08': Decimal('0.270'),
        '1984-09': Decimal('0.340'), '1984-10': Decimal('0.260'),
        '1984-11': Decimal('0.330'), '1984-12': Decimal('0.350'),
    }

    if csv_path and os.path.exists(csv_path):
        embutidos.update(_carregar_indices_csv(csv_path))

    return embutidos


# ---------------------------------------------------------------------------
# Cálculo de coeficiente PRICE
# ---------------------------------------------------------------------------

def _coef_price(tx_mensal: Decimal, n: int) -> Decimal:
    """Coeficiente Price: tx*(1+tx)^n / ((1+tx)^n - 1)"""
    if tx_mensal == D0 or n == 0:
        return D0
    fator = (D1 + tx_mensal) ** n
    return (tx_mensal * fator / (fator - D1)).quantize(SIX_DEC, ROUND_HALF_UP)


# ---------------------------------------------------------------------------
# Motor principal
# ---------------------------------------------------------------------------

def simular_evolucao_sfh(
    vlfinanc: Decimal,
    sa: str,
    tx_juros_aa: Decimal,
    prazo: int,
    data_contrato: date,
    prestacao_inicial: Optional[Decimal] = None,
    indices_cm: Optional[Dict[str, Decimal]] = None,
    indices_pes: Optional[Dict[str, Decimal]] = None,
    csv_path: Optional[str] = None,
) -> Tuple[List[Dict], Decimal]:
    """
    Simula a evolução mensal de um contrato SFH/BNH.

    Parâmetros
    ----------
    vlfinanc        : Saldo inicial financiado
    sa              : 'SAC', 'PRICE', 'SACRE', 'MISTO'
    tx_juros_aa     : Taxa de juros anual em % (ex: 10.0 → 10%)
    prazo           : Prazo em meses
    data_contrato   : Data de início do contrato
    prestacao_inicial: Prestação mensal inicial (usada como base PES)
    indices_cm      : Dict {'AAAA-MM': Decimal(indice_mensal)} — Correção Monetária
    indices_pes     : Dict {'AAAA-MM': Decimal(sm_nivel)} — nível do SM mensal
                      (retornado por carregar_indices_pes()). Fator PES =
                      sm[mes_aniversario_atual] / sm[mes_aniversario_anterior].
                      Se None ou SM indisponível, usa CM acumulado como fallback.
    csv_path        : Caminho do CSV de índices (opcional, carrega se fornecido)

    Retorna
    -------
    (evolucao: List[Dict], fcvs_final: Decimal)
    """
    if indices_cm is None:
        indices_cm = carregar_indices_sfh(csv_path)

    # Taxa mensal equivalente (capitalização composta)
    tx_aa  = Decimal(str(tx_juros_aa)) / Decimal('100')
    tx_mes = ((D1 + tx_aa) ** (Decimal('1') / Decimal('12')) - D1).quantize(SIX_DEC, ROUND_HALF_UP)

    sa_upper = (sa or 'SAC').upper().strip()

    # Prestação base PRICE (se necessário)
    coef = _coef_price(tx_mes, prazo) if sa_upper == 'PRICE' else D0
    prestacao_price = (vlfinanc * coef).quantize(CENTS, ROUND_HALF_UP) if coef else D0

    # Prestação base PES (o que o mutuário paga)
    if prestacao_inicial and prestacao_inicial > D0:
        prest_pes = Decimal(str(prestacao_inicial))
    elif sa_upper == 'PRICE':
        prest_pes = prestacao_price
    else:
        # SAC: prestação inicial = amort + juros do 1º mês
        amort_base = (vlfinanc / Decimal(str(prazo))).quantize(CENTS, ROUND_HALF_UP)
        prest_pes = (amort_base + vlfinanc * tx_mes).quantize(CENTS, ROUND_HALF_UP)

    saldo = vlfinanc
    fcvs_acum = D0
    evolucao: List[Dict] = []

    # Acumuladores para PES
    cm_acum_ano = D0        # CM acumulada desde último reajuste PES
    mes_aniversario = data_contrato.month
    data_ultimo_pes = data_contrato  # data do último reajuste PES (início = data contrato)

    data_atual = data_contrato

    # Índice da próxima redenominação a aplicar
    prox_redenom_idx = 0
    # Adianta o índice para a primeira redenominação que ainda não passou
    while (prox_redenom_idx < len(REDENOMINACOES) and
           data_contrato >= REDENOMINACOES[prox_redenom_idx][0]):
        prox_redenom_idx += 1

    for mes_num in range(1, prazo + 1):
        chave = data_atual.strftime('%Y-%m')
        moeda = MOEDA_DISPLAY.get(_moeda(data_atual), _moeda(data_atual))

        # --- Redenominação monetária ---
        # Se cruzamos a data de uma redenominação, divide saldo/prestação/FCVS pelo fator
        while (prox_redenom_idx < len(REDENOMINACOES) and
               data_atual >= REDENOMINACOES[prox_redenom_idx][0]):
            _, fator = REDENOMINACOES[prox_redenom_idx]
            if fator != D1:
                saldo     = (saldo     / fator).quantize(CENTS, ROUND_HALF_UP)
                prest_pes = (prest_pes / fator).quantize(CENTS, ROUND_HALF_UP)
                fcvs_acum = (fcvs_acum / fator).quantize(CENTS, ROUND_HALF_UP)
            prox_redenom_idx += 1

        # --- Correção Monetária do mês ---
        cm_mes = indices_cm.get(chave, D0)
        saldo_corrigido = (saldo * (D1 + cm_mes)).quantize(CENTS, ROUND_HALF_UP)
        cm_valor = saldo_corrigido - saldo  # valor monetário da CM

        # --- Amortização e juros ---
        prazo_restante = prazo - mes_num + 1

        if sa_upper == 'PRICE':
            juros = (saldo_corrigido * tx_mes).quantize(CENTS, ROUND_HALF_UP)
            amort = (prestacao_price - juros).quantize(CENTS, ROUND_HALF_UP)
            if amort < D0:
                amort = D0
            encargo = prestacao_price

        elif sa_upper == 'SACRE':
            # SACRE: amort = saldo_corrigido / prazo_restante (decrescente)
            amort  = (saldo_corrigido / Decimal(str(prazo_restante))).quantize(CENTS, ROUND_HALF_UP)
            juros  = (saldo_corrigido * tx_mes).quantize(CENTS, ROUND_HALF_UP)
            encargo = amort + juros

        else:
            # SAC e MISTO: amortização = saldo_corrigido / prazo_restante
            amort  = (saldo_corrigido / Decimal(str(prazo_restante))).quantize(CENTS, ROUND_HALF_UP)
            juros  = (saldo_corrigido * tx_mes).quantize(CENTS, ROUND_HALF_UP)
            encargo = amort + juros

        saldo_novo = (saldo_corrigido - amort).quantize(CENTS, ROUND_HALF_UP)
        if saldo_novo < D0:
            saldo_novo = D0

        # --- PES: reajuste anual da prestação ---
        # No mês de aniversário, a prestação é reajustada pelo SM acumulado.
        # Fator = SM[aniversário_atual] / SM[aniversário_anterior].
        # Fallback: CM acumulada se SM não disponível.
        if (data_atual.month == mes_aniversario and
                data_atual > data_ultimo_pes):
            fator_pes = None
            if indices_pes:
                chave_ant = data_ultimo_pes.strftime('%Y-%m')
                chave_cur = data_atual.strftime('%Y-%m')
                sm_ant = indices_pes.get(chave_ant)
                sm_cur = indices_pes.get(chave_cur)
                if sm_ant and sm_cur and sm_ant > D0:
                    fator_pes = (sm_cur / sm_ant).quantize(SIX_DEC, ROUND_HALF_UP)
            if fator_pes is None:
                fator_pes = D1 + cm_acum_ano  # fallback CM
            prest_pes = (prest_pes * fator_pes).quantize(CENTS, ROUND_HALF_UP)
            data_ultimo_pes = data_atual
            cm_acum_ano = D0  # zera acumulador

        # Acumula CM para fallback do próximo reajuste PES
        cm_acum_ano = (D1 + cm_acum_ano) * (D1 + cm_mes) - D1

        # --- FCVS do mês: excedente não coberto pela prestação PES ---
        # O saldo FCVS é corrigido mensalmente pela CM (créditos anteriores
        # também crescem com a correção monetária, como um saldo devedor).
        fcvs_mes = max(D0, encargo - prest_pes).quantize(CENTS, ROUND_HALF_UP)
        fcvs_acum = ((fcvs_acum * (D1 + cm_mes)) + fcvs_mes).quantize(CENTS, ROUND_HALF_UP)

        evolucao.append({
            'mes':         mes_num,
            'data':        chave,
            'saldo_ant':   float(saldo),
            'cm_pct':      float(cm_mes * 100),
            'cm_valor':    float(cm_valor),
            'saldo_corr':  float(saldo_corrigido),
            'amort':       float(amort),
            'juros':       float(juros),
            'encargo':     float(encargo),
            'prest_pes':   float(prest_pes),
            'fcvs_mes':    float(fcvs_mes),
            'fcvs_acum':   float(fcvs_acum),
            'saldo_novo':  float(saldo_novo),
            'moeda':       moeda,
        })

        saldo = saldo_novo

        # Avança um mês
        data_atual = data_atual + relativedelta(months=1)

        # Se quitou antes do prazo, preenche meses restantes com zeros
        if saldo == D0 and mes_num < prazo:
            for m2 in range(mes_num + 1, prazo + 1):
                chave2 = data_atual.strftime('%Y-%m')
                evolucao.append({
                    'mes': m2, 'data': chave2,
                    'saldo_ant': 0.0, 'cm_pct': 0.0, 'cm_valor': 0.0,
                    'saldo_corr': 0.0, 'amort': 0.0, 'juros': 0.0,
                    'encargo': 0.0, 'prest_pes': float(prest_pes),
                    'fcvs_mes': 0.0, 'fcvs_acum': float(fcvs_acum),
                    'saldo_novo': 0.0, 'moeda': _moeda(data_atual),
                })
                data_atual = data_atual + relativedelta(months=1)
            break

    # FCVS final = saldo residual + FCVS acumulado (diferença prestação × encargo)
    fcvs_final = (fcvs_acum + saldo).quantize(CENTS, ROUND_HALF_UP)

    # Converte FCVS final para R$ aplicando as redenominações que ainda não foram aplicadas
    # (o valor ficou na moeda do fim do contrato, não necessariamente R$)
    for i in range(prox_redenom_idx, len(REDENOMINACOES)):
        _, fator = REDENOMINACOES[i]
        if fator != D1:
            fcvs_final = (fcvs_final / fator).quantize(CENTS, ROUND_HALF_UP)

    return evolucao, fcvs_final


# ---------------------------------------------------------------------------
# Resumo estatístico
# ---------------------------------------------------------------------------

def resumo_simulacao(evolucao: List[Dict]) -> Dict:
    """Retorna estatísticas resumidas da simulação."""
    if not evolucao:
        return {}

    total_encargo  = sum(e['encargo']   for e in evolucao)
    total_amort    = sum(e['amort']     for e in evolucao)
    total_juros    = sum(e['juros']     for e in evolucao)
    total_cm       = sum(e['cm_valor']  for e in evolucao)
    total_fcvs     = evolucao[-1]['fcvs_acum']
    saldo_final    = evolucao[-1]['saldo_novo']

    return {
        'meses_simulados': len(evolucao),
        'total_encargo':   round(total_encargo,  2),
        'total_amort':     round(total_amort,    2),
        'total_juros':     round(total_juros,    2),
        'total_cm':        round(total_cm,       2),
        'fcvs_acumulado':  round(total_fcvs,     2),
        'saldo_final':     round(saldo_final,    2),
    }
