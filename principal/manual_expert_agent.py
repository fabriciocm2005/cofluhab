"""Agente especialista em manuais CEF para validar leituras de arquivos."""

from __future__ import annotations

import re
from typing import Dict


class ManualExpertAgent:
    """Especialista em mapeamento de codigos de relatorios para fonte/manual e acao."""

    _DEFAULT = {
        'interpretacao': 'Codigo nao mapeado especificamente; interpretacao por parser generico FCVS/CADMUT.',
        'fonte_manual': 'Manual_SIWFC_MAR_2025.pdf / leiautes FCVS-CADMUT',
        'acao': 'Classificar manualmente e ajustar parser especializado se necessario.',
        'confianca': 'baixa',
    }

    _MAPA = {
        'CADMUT1': {
            'interpretacao': 'CADMUT1: Acerto de Contratos em Critica (Movimentacao CADMUT).',
            'fonte_manual': 'Leiautes_Movim_CADMUT - 2025.pdf / CADMUT1 (tipo movimento 12)',
            'acao': 'Tratar contratos em critica, validar cadastro e preparar reenvio quando aplicavel.',
            'confianca': 'alta',
        },
        'M302611': {
            'interpretacao': 'M302611: Retorno FCVS3026 (familia P3026) - subtipo operacional 11.',
            'fonte_manual': 'Leiaute_FCVS3026_TR1_a_TR9_270417.xls + ANALISE_P3026_COMPLETA.md',
            'acao': 'Conferir contratos/CPF/status por linha e atualizar pendencias internas.',
            'confianca': 'alta',
        },
        'M302612': {
            'interpretacao': 'M302612: Retorno FCVS3026 (familia P3026) - subtipo operacional 12.',
            'fonte_manual': 'Leiaute_FCVS3026_TR1_a_TR9_270417.xls + ANALISE_P3026_COMPLETA.md',
            'acao': 'Conferir variacoes de carteira e registrar divergencias contratuais.',
            'confianca': 'alta',
        },
        'M302615': {
            'interpretacao': 'M302615: Retorno FCVS3026 (familia P3026) - subtipo operacional 15.',
            'fonte_manual': 'Leiaute_FCVS3026_TR1_a_TR9_270417.xls + ANALISE_P3026_COMPLETA.md',
            'acao': 'Validar status/posicionamento de contratos e saldo informado pela CEF.',
            'confianca': 'alta',
        },
        'M302617': {
            'interpretacao': 'M302617: Retorno FCVS3026 (familia P3026) - subtipo operacional 17.',
            'fonte_manual': 'Leiaute_FCVS3026_TR1_a_TR9_270417.xls + ANALISE_P3026_COMPLETA.md',
            'acao': 'Mapear contratos com alteracoes e direcionar tratativa operacional.',
            'confianca': 'alta',
        },
        'S102701': {
            'interpretacao': 'S102701: Relatorio textual SIWFC/FCVS (saida operacional).',
            'fonte_manual': 'Manual_SIWFC_MAR_2025.pdf (relatorios operacionais)',
            'acao': 'Usar para acompanhamento operacional e conferencia mensal.',
            'confianca': 'alta',
        },
        'S194301': {
            'interpretacao': 'S194301: Relacao de contratos com pedido de habilitacao rejeitado.',
            'fonte_manual': 'Manual_SIWFC_MAR_2025.pdf + cabecalho do relatorio S194301',
            'acao': 'Conferir motivos de rejeicao por contrato e preparar tratativa/reenvio.',
            'confianca': 'alta',
        },
        'S343501': {
            'interpretacao': 'S343501: Relatorio textual SIWFC com total de contratos do agente.',
            'fonte_manual': 'Manual_SIWFC_MAR_2025.pdf (saida de relatorios por agente)',
            'acao': 'Conferir total de contratos do agente e consistencia com base local.',
            'confianca': 'alta',
        },
        'S343601': {
            'interpretacao': 'S343601: Relatorio textual SIWFC com total de contratos do agente.',
            'fonte_manual': 'Manual_SIWFC_MAR_2025.pdf (saida de relatorios por agente)',
            'acao': 'Conferir total de contratos do agente e diferencas da remessa anterior.',
            'confianca': 'media',
        },
        'S765101': {
            'interpretacao': 'S765101: Relatorio textual SIWFC (resumo operacional).',
            'fonte_manual': 'Manual_SIWFC_MAR_2025.pdf',
            'acao': 'Registrar resumo para auditoria e checklist de processamento.',
            'confianca': 'baixa',
        },
        'S778101': {
            'interpretacao': 'S778101: Relacao de contratos com solicitacao de RNV e RCV acatadas.',
            'fonte_manual': 'Manual_SIWFC_MAR_2025.pdf + cabecalho do relatorio S778101',
            'acao': 'Conferir contratos acatados, tipo de solicitacao e datas de termino da analise.',
            'confianca': 'alta',
        },
        'S820301': {
            'interpretacao': 'S820301: Contratos com ressarcimento ao FCVS - totalizacao por contrato.',
            'fonte_manual': 'Manual_SIWFC_MAR_2025.pdf + cabecalho do relatorio',
            'acao': 'Conferir contratos com ressarcimento e totalizadores por contrato.',
            'confianca': 'media',
        },
        'S820401': {
            'interpretacao': 'S820401: Relatorio textual SIWFC com total consolidado de contratos.',
            'fonte_manual': 'Manual_SIWFC_MAR_2025.pdf',
            'acao': 'Validar total consolidado por agente e registrar evidencias.',
            'confianca': 'alta',
        },
        'S820601': {
            'interpretacao': 'S820601: Relatorio analitico textual extenso com totalizadores por contrato/moeda.',
            'fonte_manual': 'Manual_SIWFC_MAR_2025.pdf + saida textual S820601',
            'acao': 'Extrair totalizadores e detalhar contratos com maiores valores/dividas.',
            'confianca': 'alta',
        },
    }

    def guia(self, codigo: str) -> Dict[str, str]:
        codigo = (codigo or '').upper()
        return self._MAPA.get(codigo, self._DEFAULT)

    def validar_linha(self, codigo: str, tipo_linha: str, texto: str) -> Dict[str, str]:
        """Valida rapidamente se a leitura da linha bate com o padrão esperado."""
        codigo = (codigo or '').upper()
        texto_u = (texto or '').upper()
        tipo = (tipo_linha or '').upper()

        confianca = self.guia(codigo).get('confianca', 'baixa')
        alerta = ''

        if codigo.startswith('S'):
            if tipo == 'TOTALIZADOR' and 'TOTAL' not in texto_u and 'TOTALIZ' not in texto_u:
                alerta = 'Totalizador sem marcador TOTAL/TOTALIZ.'
                confianca = 'baixa'
            elif tipo == 'CABECALHO_PAGINA' and ('PAGINA' not in texto_u and 'SEQ' not in texto_u):
                alerta = 'Cabecalho de pagina sem marcador PAGINA/SEQ.'
                confianca = 'baixa'

        if codigo.startswith('M3026'):
            if tipo in {'1', '2', '3', '4', '5', '6', '7', '8'}:
                if not re.search(r'\d{13}', texto):
                    alerta = 'Linha M3026 sem contrato (13 digitos) detectado.'
                    confianca = 'media' if confianca == 'alta' else confianca

        if codigo == 'CADMUT1':
            if tipo not in {'HEADER', 'MOVIMENTO', 'TRAILER', 'CRITICA', '3', '4', '9'}:
                alerta = 'Tipo de linha CADMUT1 fora do esperado.'
                confianca = 'baixa'

        return {
            'confianca_leitura': confianca,
            'alerta_leitura': alerta,
        }

    def enriquecer_row(self, row: Dict[str, str]) -> Dict[str, str]:
        """Anexa metadados do manual e validação de leitura na linha exportável."""
        codigo = row.get('codigo', '')
        guia = self.guia(codigo)
        leitura = self.validar_linha(codigo, row.get('tipo_linha', ''), row.get('texto', ''))

        enriched = dict(row)
        enriched.setdefault('interpretacao_manual', guia.get('interpretacao', ''))
        enriched.setdefault('fonte_manual', guia.get('fonte_manual', ''))
        enriched.setdefault('acao_recomendada', guia.get('acao', ''))
        enriched['confianca_leitura'] = leitura.get('confianca_leitura', guia.get('confianca', 'baixa'))
        enriched['alerta_leitura'] = leitura.get('alerta_leitura', '')

        if enriched['confianca_leitura'] == 'baixa' and not enriched['alerta_leitura']:
            enriched['alerta_leitura'] = (
                'Leitura textual/heuristica: validacao manual recomendada para confirmar mapeamento.'
            )

        return enriched
