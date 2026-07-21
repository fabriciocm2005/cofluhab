"""
Agente de Qualidade de Contratos
=================================
Inspeciona contratos cadastrados (via OCR ou manual) e valida:
  1. Completude dos campos obrigatórios (CADMUT + FH1)
  2. Integridade do mutuário (CPF DV, formato, dados mínimos)
  3. Evolução financeira (parcelas, saldo devedor, juros, amortização)
  4. Prontidão CADMUT (pode gerar arquivo para a CEF?)
  5. Prontidão FH1 (pode gerar ficha de habilitação?)

Uso:
    from principal.agente_qualidade_contrato import AgenteQualidadeContrato
    relatorio = AgenteQualidadeContrato(contrato_id=42).inspecionar()
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from datetime import date, timedelta
from typing import List, Optional, Dict, Any
from django.db import connection

# ─────────────────────────────────────────────────────────────────────────────
# Estruturas de dados do relatório
# ─────────────────────────────────────────────────────────────────────────────

NIVEL_ERRO    = 'ERRO'    # Bloqueia CADMUT/FH1
NIVEL_AVISO   = 'AVISO'   # Pode causar rejeição; revisar
NIVEL_INFO    = 'INFO'    # Informação/sugestão

@dataclass
class ItemQualidade:
    nivel: str          # ERRO | AVISO | INFO
    categoria: str      # Ex: "Contrato", "Mutuário", "Evolução Financeira"
    campo: str          # Campo específico ou 'geral'
    mensagem: str
    sugestao: str = ''


@dataclass
class RelatorioQualidade:
    contrato_id: Optional[int]
    contrato_codigo: str
    score: int                       # 0-100
    prontidao_cadmut: bool
    prontidao_fh1: bool
    itens: List[ItemQualidade] = field(default_factory=list)
    resumo_financeiro: Dict[str, Any] = field(default_factory=dict)

    @property
    def erros(self) -> List[ItemQualidade]:
        return [i for i in self.itens if i.nivel == NIVEL_ERRO]

    @property
    def avisos(self) -> List[ItemQualidade]:
        return [i for i in self.itens if i.nivel == NIVEL_AVISO]

    @property
    def alertas(self) -> List[ItemQualidade]:
        """Compatibilidade com scripts antigos que ainda usam `rel.alertas`."""
        return self.avisos

    @property
    def infos(self) -> List[ItemQualidade]:
        return [i for i in self.itens if i.nivel == NIVEL_INFO]

    @property
    def status_label(self) -> str:
        if self.score >= 90:
            return 'ÓTIMO'
        if self.score >= 75:
            return 'BOM'
        if self.score >= 50:
            return 'ATENÇÃO'
        return 'CRÍTICO'

    @property
    def status_css(self) -> str:
        if self.score >= 90:
            return 'success'
        if self.score >= 75:
            return 'primary'
        if self.score >= 50:
            return 'warning'
        return 'danger'


# ─────────────────────────────────────────────────────────────────────────────
# Utilitários
# ─────────────────────────────────────────────────────────────────────────────

def _validar_cpf(cpf: str) -> bool:
    """Retorna True se CPF é válido (dígitos verificadores corretos)."""
    digitos = re.sub(r'\D', '', cpf or '')
    if len(digitos) != 11 or len(set(digitos)) == 1:
        return False
    soma = sum(int(d) * (10 - i) for i, d in enumerate(digitos[:9]))
    r1 = (soma * 10 % 11) % 10
    soma = sum(int(d) * (11 - i) for i, d in enumerate(digitos[:10]))
    r2 = (soma * 10 % 11) % 10
    return int(digitos[9]) == r1 and int(digitos[10]) == r2


def _nome_valido_cadmut(nome: str) -> tuple[bool, str]:
    """
    Valida nome segundo regras CADMUT:
    - Não pode começar com espaço ou ponto
    - Sem caracteres especiais (só A-Z, espaço, hífen, apóstrofo)
    - Deve ter ao menos 2 partes (nome + sobrenome)
    - Não pode ter 3 letras iguais consecutivas
    """
    if not nome:
        return False, "Nome vazio"
    nome = nome.strip()
    if nome[0] in (' ', '.'):
        return False, "Nome inicia com espaço ou ponto"
    if re.search(r'[^A-Za-zÀ-ÿ\s\'\-]', nome):
        return False, "Nome contém caracteres especiais"
    if len(nome.split()) < 2:
        return False, "Nome deve ter ao menos nome e sobrenome"
    if re.search(r'(.)\1\1', nome.upper()):
        return False, "Nome com 3 letras iguais consecutivas"
    return True, ""


OCORRENCIAS_VALIDAS = {'TPZ', 'SET', 'SIT', 'LA2', 'LA3', 'PXN', 'LIQ'}
SISTEMAS_AMORT_VALIDOS = {'SAC', 'PRICE', 'SACRE', 'MISTO'}
CODIGOS_SA_LEGADO_VALIDOS = {'1', '2', '4'}


# ─────────────────────────────────────────────────────────────────────────────
# Agente principal
# ─────────────────────────────────────────────────────────────────────────────

class AgenteQualidadeContrato:
    """
    Inspeciona um contrato cadastrado no banco e gera relatório de qualidade.
    Pode receber contrato_id (busca do banco) ou uma instância direta.
    """

    def __init__(self, contrato_id: int = None, contrato=None):
        if contrato is not None:
            self._contrato = contrato
        elif contrato_id is not None:
            from principal.models import Contrato
            self._contrato = Contrato.objects.get(pk=contrato_id)
        else:
            raise ValueError("Informe contrato_id ou contrato")
        self._itens: List[ItemQualidade] = []

    # ── helpers internos ─────────────────────────────────────────────────────

    def _add(self, nivel: str, categoria: str, campo: str, mensagem: str, sugestao: str = ''):
        self._itens.append(ItemQualidade(nivel, categoria, campo, mensagem, sugestao))

    def _erro(self, cat, campo, msg, sug=''):
        self._add(NIVEL_ERRO, cat, campo, msg, sug)

    def _aviso(self, cat, campo, msg, sug=''):
        self._add(NIVEL_AVISO, cat, campo, msg, sug)

    def _info(self, cat, campo, msg, sug=''):
        self._add(NIVEL_INFO, cat, campo, msg, sug)

    def _buscar_mutuario_principal(self):
        from principal.models import Mutuario

        contrato_id = getattr(self._contrato, 'id', None)
        if contrato_id:
            with connection.cursor() as cur:
                cur.execute(
                    """
                    SELECT mutuario_id
                    FROM contrato_mutuario_map
                    WHERE contrato_id = %s
                    ORDER BY rowid
                    LIMIT 1
                    """,
                    [contrato_id],
                )
                row = cur.fetchone()
            if row and row[0]:
                mutuario = Mutuario.objects.filter(id=row[0]).first()
                if mutuario:
                    return mutuario

        if self._contrato.conjunto:
            return Mutuario.objects.filter(conjunto=self._contrato.conjunto).first()

        return None

    # ── verificações de completude do CONTRATO ────────────────────────────────

    def _checar_campos_contrato(self):
        c = self._contrato
        cat = 'Contrato'

        if not c.codigo:
            self._erro(cat, 'codigo', 'Código do contrato ausente', 'Informe o número gerado pela CEF')
        if not c.conjunto:
            self._erro(cat, 'conjunto', 'Conjunto habitacional não informado', 'Campo obrigatório para CADMUT')
        if not c.data_contrato:
            self._erro(cat, 'data_contrato', 'Data de assinatura do contrato ausente', 'Obrigatório para CADMUT e FH1')
        else:
            hoje = date.today()
            if c.data_contrato > hoje:
                self._erro(cat, 'data_contrato', f'Data futura: {c.data_contrato}', 'Verifique o OCR')
            if c.data_contrato.year < 1960:
                self._aviso(cat, 'data_contrato', f'Data muito antiga: {c.data_contrato}', 'Confirme se está correta')

        if not c.data_primeiro_venc:
            self._erro(cat, 'data_primeiro_venc', '1º vencimento ausente', 'Obrigatório para campo PRIMEIRO_VENCIMENTO do FH1')
        elif c.data_contrato and c.data_primeiro_venc < c.data_contrato:
            self._erro(cat, 'data_primeiro_venc', '1º vencimento anterior à data do contrato', 'Verifique o OCR')

        if not c.sa:
            self._erro(cat, 'sa', 'Sistema de amortização não informado (SAC/PRICE/SACRE)', 'Obrigatório para FH1')
        elif str(c.sa).strip().upper() not in SISTEMAS_AMORT_VALIDOS and str(c.sa).strip() not in CODIGOS_SA_LEGADO_VALIDOS:
            self._aviso(cat, 'sa', f'Sistema de amortização desconhecido: {c.sa}', f'Esperado: {", ".join(SISTEMAS_AMORT_VALIDOS)}')

        if c.tx_juros is None:
            self._erro(cat, 'tx_juros', 'Taxa de juros ausente', 'Obrigatório para FH1')
        else:
            tx = float(c.tx_juros)
            if tx <= 0:
                self._erro(cat, 'tx_juros', f'Taxa de juros inválida: {tx}%', 'Deve ser positiva')
            elif tx > 15:
                self._aviso(cat, 'tx_juros', f'Taxa de juros elevada: {tx}%', 'Confirme se é % a.a. (não a.m.)')

        if not c.prazo:
            self._erro(cat, 'prazo', 'Prazo do contrato ausente', 'Obrigatório para FH1 (PRAZO_CONTRATADO)')
        elif c.prazo <= 0 or c.prazo > 600:
            self._aviso(cat, 'prazo', f'Prazo fora do intervalo esperado: {c.prazo} meses', 'Contratos SFH: 12 a 420 meses')

        if not c.cat_prof:
            self._aviso(cat, 'cat_prof', 'Categoria profissional ausente', 'CODIGO_CATEG_PROF é obrigatório no FH1')

        if not c.pr:
            self._aviso(cat, 'pr', 'Programa (PR) não informado', 'Campo PR obrigatório no FH1')

        if not c.ocorrencia:
            self._aviso(cat, 'ocorrencia', 'Tipo de ocorrência CADMUT não informado', f'Valores válidos: {", ".join(OCORRENCIAS_VALIDAS)}')
        elif c.ocorrencia.upper() not in OCORRENCIAS_VALIDAS:
            self._erro(cat, 'ocorrencia', f'Ocorrência inválida: {c.ocorrencia}', f'Valores: {", ".join(OCORRENCIAS_VALIDAS)}')

        if not c.cod_imovel:
            self._aviso(cat, 'cod_imovel', 'Código do imóvel não informado', 'Necessário para vincular ao Mutuário')

    # ── verificações do MUTUÁRIO ─────────────────────────────────────────────

    def _checar_mutuario(self):
        cat = 'Mutuário'
        mutuario = self._buscar_mutuario_principal()
        if not mutuario:
            self._erro(cat, 'geral', 'Mutuário não encontrado para este conjunto',
                       'Cadastre o mutuário ou verifique o campo conjunto')
            return

        endereco_fk = getattr(mutuario, 'endereco_fk', None)
        uf_resolvida = str(getattr(mutuario, 'uf', '') or '').strip() or str(getattr(endereco_fk, 'uf', '') or '').strip()
        endereco_resolvido = str(getattr(mutuario, 'endereco', '') or '').strip() or str(getattr(endereco_fk, 'endereco', '') or '').strip()
        cidade_resolvida = str(getattr(mutuario, 'cidade', '') or '').strip() or str(getattr(endereco_fk, 'cidade', '') or '').strip()
        cep_resolvido = str(getattr(mutuario, 'cep', '') or '').strip() or str(getattr(endereco_fk, 'cep', '') or '').strip()

        if not str(getattr(mutuario, 'endereco', '') or '').strip() and endereco_resolvido and endereco_fk:
            self._info(cat, 'endereco_fk', 'Endereço principal vazio; usando endereco_fk como fonte de fallback para FH1/CADMUT', 'Considere sincronizar o endereço textual do mutuário')

        if not mutuario.nome:
            self._erro(cat, 'nome', 'Nome do mutuário ausente', 'Obrigatório CADMUT/FH1')
        else:
            ok, motivo = _nome_valido_cadmut(mutuario.nome)
            if not ok:
                self._erro(cat, 'nome', f'Nome inválido para CADMUT: {motivo}',
                           'Corrija usando apenas letras, espaço e hífen; inclua sobrenome')

        if not mutuario.cpf:
            self._erro(cat, 'cpf', 'CPF ausente', 'Obrigatório CADMUT/FH1')
        else:
            if not _validar_cpf(mutuario.cpf):
                self._erro(cat, 'cpf', f'CPF com dígitos verificadores inválidos: {mutuario.cpf}',
                           'Verifique o documento original')

        if not mutuario.dtnasc:
            self._aviso(cat, 'dtnasc', 'Data de nascimento ausente', 'Obrigatório no campo DATA_NASCIMENTO do FH1')
        else:
            idade = (date.today() - mutuario.dtnasc).days // 365
            if idade < 18:
                self._erro(cat, 'dtnasc', f'Mutuário menor de idade ({idade} anos)', 'Verifique a data de nascimento')
            if idade > 100:
                self._aviso(cat, 'dtnasc', f'Idade incomum: {idade} anos', 'Confirme o ano de nascimento')

        if not uf_resolvida or len(uf_resolvida) != 2:
            self._erro(cat, 'uf', 'UF ausente ou inválida', 'Obrigatório UF-Imóvel no CADMUT/FH1 (2 letras)')

        if not endereco_resolvido:
            self._erro(cat, 'endereco', 'Endereço do imóvel ausente', 'Obrigatório Endereço-Imóvel CADMUT/FH1')

        if not cidade_resolvida:
            self._aviso(cat, 'cidade', 'Cidade ausente', 'Necessário para gerar COD_MUNICIPIO no FH1')

        if not cep_resolvido:
            self._aviso(cat, 'cep', 'CEP ausente', 'Necessário para localização do imóvel')
        else:
            cep_limpo = re.sub(r'\D', '', cep_resolvido)
            if len(cep_limpo) != 8:
                self._aviso(cat, 'cep', f'CEP com formato inválido: {cep_resolvido}', 'Formato esperado: 00000-000')

        if not mutuario.ident:
            self._aviso(cat, 'ident', 'RG (Identidade) ausente', 'Campo Identidade-Mutuário CADMUT')

        if not mutuario.renda:
            self._aviso(cat, 'renda', 'Renda do mutuário não informada', 'Necessário para análise de capacidade de pagamento')

    # ── verificações da EVOLUÇÃO FINANCEIRA ──────────────────────────────────

    def _checar_evolucao_financeira(self) -> Dict[str, Any]:
        cat = 'Evolução Financeira'
        c = self._contrato
        resumo: Dict[str, Any] = {}

        try:
            parcelas = list(c.parcelas.order_by('nmens').all())
        except Exception:
            self._erro(cat, 'parcelas', 'Não foi possível acessar as parcelas do contrato', '')
            return resumo

        n_parcelas = len(parcelas)
        resumo['total_parcelas'] = n_parcelas

        # ── sem parcelas ─────────────────────────────────────────────────────
        if n_parcelas == 0:
            self._erro(cat, 'parcelas', 'Contrato sem parcelas cadastradas',
                       'Importe o arquivo de evolução financeira (MOVMUT/TXT) ou cadastre as parcelas')
            return resumo

        # ── cobertura vs prazo ───────────────────────────────────────────────
        if c.prazo:
            cobertura = n_parcelas / c.prazo * 100
            resumo['cobertura_prazo_pct'] = round(cobertura, 1)
            if n_parcelas < c.prazo * 0.95:
                self._aviso(cat, 'parcelas',
                            f'Apenas {n_parcelas} de {c.prazo} parcelas cadastradas ({cobertura:.0f}%)',
                            'Importe o restante do histórico de evolução')
        else:
            resumo['cobertura_prazo_pct'] = None

        # ── lacunas no nmens ─────────────────────────────────────────────────
        numeros = [p.nmens for p in parcelas]
        esperado = list(range(min(numeros), max(numeros) + 1))
        faltando = sorted(set(esperado) - set(numeros))
        resumo['lacunas'] = faltando[:20]  # Máx 20 para exibição
        if faltando:
            self._aviso(cat, 'nmens',
                        f'{len(faltando)} lacuna(s) na sequência de parcelas (ex: {faltando[:5]})',
                        'Importe as parcelas faltantes para o histórico completo')

        # ── saldo devedor ────────────────────────────────────────────────────
        saldos = [p.sddev for p in parcelas if p.sddev is not None]
        resumo['saldo_inicial'] = float(saldos[0]) if saldos else None
        resumo['saldo_final'] = float(saldos[-1]) if saldos else None

        if saldos:
            # Deve ser decrescente (para SAC/PRICE normais)
            inversoes = sum(1 for i in range(1, len(saldos)) if saldos[i] > saldos[i-1] * Decimal('1.05'))
            resumo['inversoes_saldo'] = inversoes
            if inversoes > 0:
                self._aviso(cat, 'sddev',
                            f'{inversoes} parcela(s) com saldo devedor crescendo mais de 5%',
                            'Pode indicar correção monetária alta ou erro na importação')

            # Saldo final deve ser próximo de zero (de ≤ 2 prestações)
            sd_final = float(saldos[-1])
            primeiro_saldo = float(saldos[0])
            if primeiro_saldo > 0 and sd_final > primeiro_saldo * 0.10:
                self._aviso(cat, 'sddev',
                            f'Saldo final ({sd_final:,.2f}) ainda é {sd_final/primeiro_saldo*100:.0f}% do saldo inicial',
                            'Verifique se o prazo contratual está completo')
        else:
            self._aviso(cat, 'sddev', 'Saldo devedor (sddev) não preenchido nas parcelas',
                        'Importe o histórico completo de evolução')

        # ── amortização ──────────────────────────────────────────────────────
        amorts = [float(p.amort) for p in parcelas if p.amort is not None]
        resumo['amort_negativas'] = sum(1 for a in amorts if a < 0)
        resumo['amort_zero'] = sum(1 for a in amorts if a == 0)
        resumo['soma_amort'] = round(sum(amorts), 2) if amorts else None

        if resumo['amort_negativas'] > 0:
            self._erro(cat, 'amort',
                       f'{resumo["amort_negativas"]} parcela(s) com amortização negativa',
                       'Amortização negativa indica problema no cálculo ou importação')
        if amorts and resumo['amort_zero'] > n_parcelas * 0.30:
            self._aviso(cat, 'amort',
                        f'{resumo["amort_zero"]} parcelas sem amortização ({resumo["amort_zero"]/n_parcelas*100:.0f}%)',
                        'Verifique se as parcelas em carência/atraso estão corretas')

        # ── juros ────────────────────────────────────────────────────────────
        if c.tx_juros and saldos and len(parcelas) > 5:
            tx_mensal = float(c.tx_juros) / 100 / 12
            erros_juros = 0
            for i, p in enumerate(parcelas[1:], 1):
                if p.juros is None or saldos[i-1] is None:
                    continue
                juros_esperado = float(saldos[i-1]) * tx_mensal
                juros_real = float(p.juros)
                if juros_esperado > 0:
                    desvio = abs(juros_real - juros_esperado) / juros_esperado
                    if desvio > 0.10:  # tolerância 10%
                        erros_juros += 1

            resumo['erros_calculo_juros'] = erros_juros
            total_verificado = n_parcelas - 1
            if erros_juros > 0:
                pct = erros_juros / total_verificado * 100
                if pct > 20:
                    self._erro(cat, 'juros',
                               f'{erros_juros} parcelas ({pct:.0f}%) com juros divergindo >10% do esperado',
                               'Verifique a taxa de juros informada ou se há correção monetária não contabilizada')
                else:
                    self._aviso(cat, 'juros',
                                f'{erros_juros} parcelas ({pct:.0f}%) com juros divergindo >10%',
                                'Tolerância normal para correção monetária e arredondamentos')
        else:
            resumo['erros_calculo_juros'] = None

        # ── FCVS ─────────────────────────────────────────────────────────────
        fcvs_valores = [p.fcvs for p in parcelas if p.fcvs is not None and p.fcvs > 0]
        resumo['parcelas_com_fcvs'] = len(fcvs_valores)
        resumo['soma_fcvs'] = round(float(sum(fcvs_valores)), 2) if fcvs_valores else 0

        if len(fcvs_valores) == 0:
            self._aviso(cat, 'fcvs',
                        'Nenhuma parcela com contribuição FCVS',
                        'Se o contrato tem cobertura FCVS, as parcelas devem ter esse campo')
        elif len(fcvs_valores) < n_parcelas * 0.8:
            self._aviso(cat, 'fcvs',
                        f'Apenas {len(fcvs_valores)} de {n_parcelas} parcelas com FCVS',
                        'Verifique se todas as parcelas cobertas pelo FCVS estão corretas')

        # ── seguro ───────────────────────────────────────────────────────────
        seguros = [p.seguro for p in parcelas if p.seguro is not None and p.seguro > 0]
        resumo['parcelas_com_seguro'] = len(seguros)
        if len(seguros) == 0:
            self._aviso(cat, 'seguro',
                        'Nenhuma parcela com seguro habitacional (MIP/DFI)',
                        'O seguro é obrigatório em contratos SFH')

        # ── datas de vencimento ──────────────────────────────────────────────
        datas = [p.dtvenc for p in parcelas if p.dtvenc is not None]
        resumo['parcelas_com_dtvenc'] = len(datas)
        if len(datas) < n_parcelas * 0.9:
            self._aviso(cat, 'dtvenc',
                        f'Apenas {len(datas)} de {n_parcelas} parcelas têm data de vencimento',
                        'Datas de vencimento são necessárias para o cálculo de encargos de atraso')
        if len(datas) >= 2:
            # Detecta parcelas com datas fora de ordem
            datas_sort = sorted(datas)
            if datas != datas_sort:
                self._aviso(cat, 'dtvenc', 'Datas de vencimento fora de sequência cronológica',
                            'Verifique a ordenação das parcelas')

        # ── informação de resumo ─────────────────────────────────────────────
        if amorts and saldos:
            self._info(cat, 'resumo',
                       f'Total amortizado: R$ {sum(amorts):,.2f} | '
                       f'Saldo inicial: R$ {float(saldos[0]):,.2f} | '
                       f'Saldo final: R$ {float(saldos[-1]):,.2f}')

        return resumo

    # ── prontidão CADMUT ──────────────────────────────────────────────────────

    def _avaliar_prontidao_cadmut(self) -> bool:
        campos_obrigatorios_bloqueantes = {
            'Contrato': ['codigo', 'conjunto', 'data_contrato', 'ocorrencia'],
            'Mutuário': ['nome', 'cpf', 'uf', 'endereco'],
            'Evolução Financeira': ['parcelas'],
        }
        erros_bloqueantes = {
            (i.categoria, i.campo)
            for i in self._itens
            if i.nivel == NIVEL_ERRO
        }
        for cat, campos in campos_obrigatorios_bloqueantes.items():
            for campo in campos:
                if (cat, campo) in erros_bloqueantes:
                    return False
        return True

    # ── prontidão FH1 ─────────────────────────────────────────────────────────

    def _avaliar_prontidao_fh1(self) -> bool:
        campos_fh1 = {
            'Contrato': ['codigo', 'data_contrato', 'data_primeiro_venc', 'sa', 'tx_juros', 'prazo'],
            'Mutuário': ['nome', 'cpf', 'dtnasc', 'uf', 'endereco'],
            'Evolução Financeira': ['parcelas'],
        }
        erros = {(i.categoria, i.campo) for i in self._itens if i.nivel == NIVEL_ERRO}
        for cat, campos in campos_fh1.items():
            for campo in campos:
                if (cat, campo) in erros:
                    return False
        return True

    # ── cálculo do score ──────────────────────────────────────────────────────

    def _calcular_score(self) -> int:
        score = 100
        for item in self._itens:
            if item.nivel == NIVEL_ERRO:
                score -= 8
            elif item.nivel == NIVEL_AVISO:
                score -= 3
        return max(0, min(100, score))

    # ── ponto de entrada principal ────────────────────────────────────────────

    def inspecionar(self) -> RelatorioQualidade:
        """Executa todas as checagens e retorna o relatório completo."""
        c = self._contrato
        self._itens = []

        self._checar_campos_contrato()
        self._checar_mutuario()
        resumo_fin = self._checar_evolucao_financeira()

        score = self._calcular_score()
        prontidao_cadmut = self._avaliar_prontidao_cadmut()
        prontidao_fh1 = self._avaliar_prontidao_fh1()

        # Informe positivo se score alto
        if score >= 90 and prontidao_cadmut and prontidao_fh1:
            self._info('Geral', 'resumo',
                       'Contrato em excelente estado — pronto para CADMUT e FH1',
                       'Pode prosseguir com envio à CEF')

        return RelatorioQualidade(
            contrato_id=c.pk,
            contrato_codigo=c.codigo,
            score=score,
            prontidao_cadmut=prontidao_cadmut,
            prontidao_fh1=prontidao_fh1,
            itens=self._itens,
            resumo_financeiro=resumo_fin,
        )
