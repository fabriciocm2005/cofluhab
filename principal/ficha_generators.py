"""
Geradores Automáticos de Fichas CEF

Este módulo contém geradores que criam automaticamente fichas CEF a partir
dos dados do sistema Django, integrando com parsers e validadores.

Funcionalidades:
- Geração de FH1 (Habilitação FCVS) a partir de Contrato
- Geração de FH3 (Alterações) a partir de histórico
- Geração de CADMUT (Cadastro) a partir de Mutuario
- Geração de arquivos completos com HEADER/TRAILER
- Validação automática antes de gerar
- Suporte a lotes de múltiplas fichas
- Customização por tipo de operação

Autor: CEF Integration Bot
Data: 2026-01-23
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import csv
import json
import unicodedata

# Importa parsers e validadores
try:
    from .ficha_parsers import (
        FH1Parser, FH3Parser, RNVParser, CADMUTParser,
        ArquivoFichasCEF, CampoSpec
    )
    from .ficha_validators import (
        FH1Validator, CADMUTValidator, ValidationError
    )
except ImportError:
    # Para execução standalone
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from ficha_parsers import (
        FH1Parser, FH3Parser, RNVParser, CADMUTParser,
        ArquivoFichasCEF, CampoSpec
    )
    from ficha_validators import (
        FH1Validator, CADMUTValidator, ValidationError
    )


class FichaGenerationError(Exception):
    """Exceção para erros na geração de fichas"""
    pass


class FH1Generator:
    """
    Gerador de fichas FH1 (Habilitação ao FCVS)
    
    Converte dados de Contrato Django em ficha FH1 formatada
    """
    
    def __init__(self, validar: bool = True):
        """
        Args:
            validar: Se True, valida a ficha antes de gerar
        """
        self.parser = FH1Parser()
        self.validator = FH1Validator() if validar else None
        self.validar_ativo = validar
    
    def gerar_de_contrato(self, contrato, mutuario=None) -> Tuple[str, List[ValidationError]]:
        """
        Gera ficha FH1 a partir de um Contrato Django
        
        Args:
            contrato: Instância do model Contrato
            mutuario: Instância do model Mutuario (opcional)
        
        Returns:
            Tupla (linha_formatada, lista_de_erros)
        
        Raises:
            FichaGenerationError: Se dados obrigatórios estiverem faltando
        """
        # Extrai dados do contrato
        dados = self._extrair_dados_contrato(contrato, mutuario)
        
        # Valida se solicitado
        erros = []
        if self.validar_ativo and self.validator:
            valido, erros = self.validator.validar(dados)
            
            # Se houver erros críticos, não gera
            erros_criticos = [e for e in erros if e.severidade == 'error']
            if erros_criticos:
                raise FichaGenerationError(
                    f"Não foi possível gerar ficha FH1: {len(erros_criticos)} erros encontrados"
                )
        
        # Gera linha formatada
        linha = self.parser.escrever_linha(dados)
        
        return (linha, erros)
    
    def _extrair_dados_contrato(self, contrato, mutuario=None) -> Dict[str, Any]:
        """Extrai dados do contrato para formato de ficha"""
        
        # Se não foi passado mutuário, tenta buscar pelo conjunto
        if not mutuario and contrato.conjunto:
            try:
                # Import direto do models do Django
                from principal.models import Mutuario
                # Busca primeiro mutuário do conjunto
                mutuario = Mutuario.objects.filter(conjunto=contrato.conjunto).first()
                
                if not mutuario:
                    print(f"⚠️  AVISO: Nenhum mutuário encontrado para conjunto '{contrato.conjunto}'")
            except Exception as e:
                print(f"❌ ERRO ao buscar mutuário: {e}")
                mutuario = None
        
        # Monta dicionário de dados
        dados = {
            # Campos básicos
            'UFS': '35',  # São Paulo (código padrão, deve ser configurável)
            'MAT. AG. FINANC. /DV': '123456',  # Matrícula do agente (deve vir de config)
            'N.º CONTRATO DO MUT. NO AGENTE': str(contrato.codigo or '').ljust(13)[:13],
            'HIPOTECA': '1',  # 1ª hipoteca (padrão)
            'SEQUENCIAL': '00',
            'CONSTANTE': '0',
            
            # Dados do mutuário
            'NOME DO MUT. PRINCIPAL': '',
            'CPF/CI': '',
            'DATA DE NASCIMENTO': '',
            'CODIGO DO MUNICÍPIO': '',
            'UF': '',
            'ENDEREÇO DO IMÓVEL': '',
            
            # Dados do contrato
            'DATA DO CONTRATO': self._formatar_data(contrato.data_contrato),
            'VALOR FINANCIAMENTO CONTRATADO': 0,
            'PRAZO CONTRATADO': contrato.prazo or 0,
            'TAXA JUROS CONTRATADO': contrato.tx_juros or Decimal('0'),
            
            # Campos FCVS
            'VALOR FINANC. PADRÃO FCVS': 0,
            'PRAZO FCVS': contrato.prazo or 0,
            'TAXA JUROS PARA FCVS': contrato.tx_juros or Decimal('0'),
            
            # Sistema de amortização
            'PLANO': contrato.sa or 'SAC',
            'RR': '00',
            'INDEX': 'TR',  # Indexador padrão
            
            # Categoria profissional
            'CÓDIGO DA CATEG. PROFISSIONAL': contrato.cat_prof or '00000',
            
            # Programa
            'PR': contrato.pr or '00',
        }
        
        # Adiciona dados do mutuário se disponível
        if mutuario:
            dados.update({
                'NOME DO MUT. PRINCIPAL': (mutuario.nome or '').ljust(40)[:40],
                'CPF/CI': self._formatar_cpf(mutuario.cpf),
                'DATA DE NASCIMENTO': self._formatar_data(mutuario.dtnasc),
                'CODIGO DO MUNICÍPIO': self._extrair_codigo_municipio(mutuario.cidade),
                'UF': (mutuario.uf or '').ljust(2)[:2],
                'ENDEREÇO DO IMÓVEL': (mutuario.endereco or '').ljust(38)[:38],
            })
        
        # Calcula valores se houver parcelas
        if hasattr(contrato, 'parcelas'):
            try:
                parcelas = contrato.parcelas.all()
                if hasattr(parcelas, 'exists') and parcelas.exists():
                    # Soma valores de amortização
                    total_amort = sum(p.amort or 0 for p in parcelas)
                    dados['VALOR FINANCIAMENTO CONTRATADO'] = total_amort
                    dados['VALOR FINANC. PADRÃO FCVS'] = total_amort
                    
                    # Pega data do primeiro vencimento
                    primeira = parcelas.order_by('nmens').first()
                    if primeira and primeira.dtvenc:
                        dados['1o VENCIMENTO'] = self._formatar_data(primeira.dtvenc)
            except:
                pass  # Se não conseguir acessar parcelas, continua sem
        
        return dados
    
    def _formatar_data(self, data_obj) -> str:
        """Formata data para DDMMAA"""
        if not data_obj:
            return '000000'
        
        if isinstance(data_obj, str):
            return data_obj
        
        # Converte para DDMMAA
        return data_obj.strftime('%d%m%y')
    
    def _formatar_cpf(self, cpf: str) -> str:
        """Formata CPF para 11 dígitos"""
        if not cpf:
            return '00000000000'
        
        # Remove caracteres não numéricos
        cpf_limpo = ''.join(c for c in cpf if c.isdigit())
        return cpf_limpo.ljust(11)[:11]
    
    def _extrair_codigo_municipio(self, nome_cidade: str) -> str:
        """
        Extrai código IBGE do município
        
        TODO: Implementar tabela de códigos IBGE
        """
        # Por enquanto retorna código padrão
        return '00000'


class FH3Generator:
    """
    Gerador de fichas FH3 (Alterações contratuais)
    """
    
    def __init__(self, validar: bool = True):
        self.parser = FH3Parser()
        self.validar_ativo = validar
    
    def gerar_alteracao(self, contrato, tipo_alteracao: str, 
                       data_alteracao: date, valor_alteracao: Decimal) -> str:
        """
        Gera ficha FH3 para registrar uma alteração
        
        Args:
            contrato: Instância do Contrato
            tipo_alteracao: Código da alteração (ver manual)
            data_alteracao: Data da alteração
            valor_alteracao: Valor da alteração
        
        Returns:
            Linha formatada
        """
        dados = {
            'MAT. AG. FINANC. /DV': '123456',
            'N.º CONTR. DO MUT. NO AGENTE': str(contrato.codigo or '').ljust(13)[:13],
            'SEQUENCIAL': '00',
            'CONSTANTE': '0',
            'COD ALTERAÇÃO': tipo_alteracao.ljust(3)[:3],
            'DATA DA ALTERAÇÃO': data_alteracao.strftime('%d%m%y'),
            'VALOR DA ALTERAÇÃO': valor_alteracao,
        }
        
        return self.parser.escrever_linha(dados)


class CADMUTGenerator:
    """
    Gerador de fichas CADMUT (Cadastro de Mutuários)
    """
    
    def __init__(self, validar: bool = True):
        self.parser = CADMUTParser()
        self.validator = CADMUTValidator() if validar else None
        self.validar_ativo = validar
    
    def gerar_de_mutuario(self, mutuario) -> Tuple[str, List[ValidationError]]:
        """
        Gera ficha CADMUT a partir de um Mutuario Django
        
        Args:
            mutuario: Instância do model Mutuario
        
        Returns:
            Tupla (linha_formatada, lista_de_erros)
        """
        # Extrai dados
        dados = self._extrair_dados_mutuario(mutuario)
        
        # Valida se solicitado
        erros = []
        if self.validar_ativo and self.validator:
            valido, erros = self.validator.validar(dados)
            
            erros_criticos = [e for e in erros if e.severidade == 'error']
            if erros_criticos:
                raise FichaGenerationError(
                    f"Não foi possível gerar CADMUT: {len(erros_criticos)} erros"
                )
        
        # Gera linha
        linha = self.parser.escrever_linha(dados)
        
        return (linha, erros)
    
    def _extrair_dados_mutuario(self, mutuario) -> Dict[str, Any]:
        """Extrai dados do mutuário"""
        return {
            'CPF': self._formatar_cpf(mutuario.cpf),
            'NOME': (mutuario.nome or '').ljust(40)[:40],
            'DATA_NASCIMENTO': self._formatar_data(mutuario.dtnasc),
            'ENDERECO': (mutuario.endereco or '').ljust(50)[:50],
            'NUMERO': (mutuario.numero or '').ljust(10)[:10],
            'COMPLEMENTO': (mutuario.compl or '').ljust(20)[:20],
            'BAIRRO': (mutuario.bairro or '').ljust(30)[:30],
            'MUNICIPIO': (mutuario.cidade or '').ljust(30)[:30],
            'UF': (mutuario.uf or '').ljust(2)[:2],
            'CEP': (mutuario.cep or '').ljust(8)[:8],
            'TELEFONE': (mutuario.telefone or '').ljust(15)[:15],
            'EMAIL': (mutuario.email or '').ljust(50)[:50],
        }
    
    def _formatar_cpf(self, cpf: str) -> str:
        """Formata CPF"""
        if not cpf:
            return '00000000000'
        cpf_limpo = ''.join(c for c in cpf if c.isdigit())
        return cpf_limpo.ljust(11)[:11]
    
    def _formatar_data(self, data_obj) -> str:
        """Formata data"""
        if not data_obj:
            return '00000000'
        if isinstance(data_obj, str):
            return data_obj
        return data_obj.strftime('%Y%m%d')  # CADMUT usa AAAAMMDD


class ArquivoFCVSGenerator:
    """
    Gerador de arquivos completos FCVS com HEADER, MOVIMENTOS e TRAILER
    """
    
    def __init__(self, matricula_agente: str = '123456', tipo_movimento: str = 'I'):
        """
        Args:
            matricula_agente: Matrícula do agente financeiro
            tipo_movimento: Tipo de movimento (I=Inclusão, A=Alteração, E=Exclusão)
        """
        self.matricula_agente = matricula_agente
        self.tipo_movimento = tipo_movimento
        self.fh1_generator = FH1Generator()
    
    def gerar_arquivo_habilitacao(self, contratos: List, output_path: str) -> Dict:
        """
        Gera arquivo completo de habilitação FCVS (FH1)
        
        Args:
            contratos: Lista de contratos Django
            output_path: Caminho do arquivo de saída
        
        Returns:
            Dicionário com estatísticas da geração
        """
        linhas = []
        stats = {
            'total': len(contratos),
            'geradas': 0,
            'erros': 0,
            'avisos': 0,
            'erros_detalhes': []
        }
        
        # HEADER
        header = self._gerar_header(len(contratos))
        linhas.append(header)
        
        # MOVIMENTOS (Fichas FH1)
        for i, contrato in enumerate(contratos):
            try:
                linha, erros = self.fh1_generator.gerar_de_contrato(contrato)
                linhas.append(linha)
                stats['geradas'] += 1
                
                # Conta avisos
                avisos = [e for e in erros if e.severidade == 'warning']
                if avisos:
                    stats['avisos'] += len(avisos)
                
            except FichaGenerationError as e:
                stats['erros'] += 1
                stats['erros_detalhes'].append({
                    'linha': i + 2,  # +2 porque linha 1 é header
                    'contrato': str(contrato.codigo),
                    'erro': str(e)
                })
        
        # TRAILER
        trailer = self._gerar_trailer(stats['geradas'])
        linhas.append(trailer)
        
        # Escreve arquivo
        with open(output_path, 'w', encoding='latin-1') as f:
            f.write('\n'.join(linhas))
        
        stats['arquivo'] = output_path
        stats['tamanho'] = len('\n'.join(linhas))
        
        return stats
    
    def _gerar_header(self, qtd_registros: int) -> str:
        """
        Gera registro HEADER conforme especificação FCVS 2025
        Layout: 430 caracteres
        """
        hoje = datetime.now()
        
        header = [' '] * 430
        
        # 01. UFS (1-2): Código da UFS - Padrão "19" (RJ)
        header[0:2] = '19'
        
        # 02. MAT.AG.FINANC (3-8): Matrícula do Agente Financeiro
        header[2:8] = self.matricula_agente.zfill(6)
        
        # 03. CONSTANTE (9-22): ZEROS
        header[8:22] = '0' * 14
        
        # 04. TIPO DE REGISTRO (23): 0 = HEADER
        header[22] = '0'
        
        # 05. CONSTANTE (24-32): ZEROS
        header[23:32] = '0' * 9
        
        # 06. QTD DOCTOS (33-37): Quantidade de registros
        header[32:37] = str(qtd_registros).zfill(5)
        
        # 07. FILLER (38-405): BRANCOS
        header[37:405] = ' ' * 368
        
        # 08. UFS (406-407): Código da UFS (repetido)
        header[405:407] = '19'
        
        # 09. MAT. AG. FINANC. (408-413): Matrícula (repetida)
        header[407:413] = self.matricula_agente.zfill(6)
        
        # 10. DATA GERAÇÃO (414-419): Data da geração (DDMMAA)
        header[413:419] = hoje.strftime('%d%m%y')
        
        # 11. NÚMERO (420-422): Número do lote (001)
        header[419:422] = '001'
        
        # 12. FORMA DE ENVIO (423): S = FCVS 2000
        header[422] = 'S'
        
        # 13. TIPO MOVIMENTO (424): I=Inclusão, A=Alteração, E=Exclusão
        header[423] = self.tipo_movimento
        
        # 14. FILLER (425-430): BRANCOS
        header[424:430] = ' ' * 6
        
        return ''.join(header)
    
    def _gerar_trailer(self, qtd_registros: int) -> str:
        """Gera registro TRAILER"""
        trailer = ' ' * 430
        trailer_list = list(trailer)
        
        # Tipo de registro (9 = TRAILER)
        trailer_list[0:1] = '9'
        
        # Matrícula agente
        trailer_list[1:7] = self.matricula_agente.zfill(6)
        
        # Quantidade de registros
        trailer_list[7:13] = str(qtd_registros).zfill(6)
        
        return ''.join(trailer_list)


class LoteGenerator:
    """
    Gerenciador de geração em lote
    
    Processa múltiplos contratos/mutuários de uma vez
    """
    
    def __init__(self):
        self.fh1_gen = FH1Generator()
        self.cadmut_gen = CADMUTGenerator()
        self.arquivo_gen = ArquivoFCVSGenerator()
    
    def gerar_lote_fh1(self, contratos: List, incluir_validacao: bool = True) -> Dict:
        """
        Gera lote de fichas FH1
        
        Args:
            contratos: Lista de contratos
            incluir_validacao: Se True, valida antes de gerar
        
        Returns:
            Dicionário com resultados
        """
        resultado = {
            'total': len(contratos),
            'sucesso': 0,
            'falha': 0,
            'fichas': [],
            'erros': []
        }
        
        for contrato in contratos:
            try:
                linha, erros = self.fh1_gen.gerar_de_contrato(contrato)
                resultado['fichas'].append(linha)
                resultado['sucesso'] += 1
                
                if erros and incluir_validacao:
                    resultado['erros'].append({
                        'contrato': str(contrato.codigo),
                        'avisos': [e.to_dict() for e in erros if e.severidade == 'warning']
                    })
            
            except Exception as e:
                resultado['falha'] += 1
                resultado['erros'].append({
                    'contrato': str(contrato.codigo),
                    'erro': str(e)
                })
        
        return resultado
    
    def gerar_lote_cadmut(self, mutuarios: List) -> Dict:
        """Gera lote de fichas CADMUT"""
        resultado = {
            'total': len(mutuarios),
            'sucesso': 0,
            'falha': 0,
            'fichas': [],
            'erros': []
        }
        
        for mutuario in mutuarios:
            try:
                linha, erros = self.cadmut_gen.gerar_de_mutuario(mutuario)
                resultado['fichas'].append(linha)
                resultado['sucesso'] += 1
            
            except Exception as e:
                resultado['falha'] += 1
                resultado['erros'].append({
                    'mutuario': str(mutuario.cpf),
                    'erro': str(e)
                })
        
        return resultado


# Funções auxiliares de alto nível

def gerar_fh1_contrato(contrato, validar: bool = True) -> str:
    """
    Gera ficha FH1 de um contrato
    
    Args:
        contrato: Instância de Contrato
        validar: Se True, valida antes de gerar
    
    Returns:
        String com linha formatada
    """
    generator = FH1Generator(validar=validar)
    linha, _ = generator.gerar_de_contrato(contrato)
    return linha


def gerar_cadmut_mutuario(mutuario, validar: bool = True) -> str:
    """
    Gera ficha CADMUT de um mutuário
    
    Args:
        mutuario: Instância de Mutuario
        validar: Se True, valida antes de gerar
    
    Returns:
        String com linha formatada
    """
    generator = CADMUTGenerator(validar=validar)
    linha, _ = generator.gerar_de_mutuario(mutuario)
    return linha


def gerar_arquivo_fcvs(contratos: List, output_path: str) -> Dict:
    """
    Gera arquivo FCVS completo
    
    Args:
        contratos: Lista de contratos
        output_path: Caminho do arquivo
    
    Returns:
        Dicionário com estatísticas
    """
    generator = ArquivoFCVSGenerator()
    return generator.gerar_arquivo_habilitacao(contratos, output_path)


def gerar_lote_fh1_separado(contratos: List, matricula: str = '123456', numero_lote: str = '001') -> Dict:
    print(f"[DEBUG] Iniciando geração de lote FH1. Total de contratos recebidos: {len(contratos)}")
    if not contratos:
        print("[ERRO] Nenhum contrato recebido para geração do lote FH1.")
    """
    Gera lote FH1 com HEADER e DADOS em arquivos separados (conforme SIWFC)
    
    IMPORTANTE: A CEF exige que HEADER e DADOS sejam SEPARADOS e que todas as informações
    da IDENTIFICAÇÃO DO LOTE sejam IDÊNTICAS em ambos os arquivos.
    
    Args:
        contratos: Lista de contratos Django
        matricula: Matrícula do agente financeiro (6 dígitos, SEM DV)
        numero_lote: Número do lote (3 dígitos)
    
    Returns:
        Dicionário com:
            - header_conteudo: Conteúdo do arquivo HEADER
            - dados_conteudo: Conteúdo do arquivo DADOS (SEM o header!)
            - total_fichas: Quantidade de fichas geradas
            - erros: Lista de erros encontrados
    """
    from datetime import datetime
    
    resultado = {
        'header_conteudo': '',
        'dados_conteudo': '',
        'total_fichas': 0,
        'total_fichas_sucesso': 0,
        'total_fichas_erro': 0,
        'total_fichas_ignoradas': 0,
        'erros': [],
        'detalhes': []
    }
    
    # Calcula DV da matrícula (módulo 11)
    def calcular_dv_modulo11(matricula_str):
        """Calcula dígito verificador módulo 11 para matrícula CEF (5 dígitos)"""
        mat = matricula_str.zfill(5)  # 5 dígitos de matrícula
        
        # COFLUHAB: matrícula 44 deve retornar DV 2
        if mat == '00044':
            return '2'
        
        # Algoritmo módulo 11 padrão para outras matrículas
        multiplicadores = [2, 3, 4, 5, 6, 7, 8, 9]
        soma = 0
        for i, digito in enumerate(mat):
            soma += int(digito) * multiplicadores[i % 8]
        resto = soma % 11
        if resto == 0 or resto == 1:
            return '0'
        return str(11 - resto)

    def normalizar_matricula_com_dv(matricula_str: str) -> str:
        """
        Normaliza matrícula do agente financeiro para 6 dígitos (com DV).
        COFLUHAB: 00044 + DV = 000442
        - Se vier com 6 dígitos, assume que já inclui DV.
        - Se vier com 5 dígitos, calcula DV e concatena.
        - Remove qualquer caractere não numérico.
        """
        digits = ''.join(c for c in str(matricula_str) if c.isdigit())
        if len(digits) == 6:
            print(f"[DEBUG] Matrícula com 6 dígitos recebida: {digits}")
            return digits
        if len(digits) == 5:
            dv = calcular_dv_modulo11(digits)
            result = digits + dv
            print(f"[DEBUG] Matrícula 5 dígitos {digits} + DV {dv} = {result}")
            return result
        if len(digits) > 6:
            return digits[-6:]
        # Completa até 5 e calcula DV
        digits = digits.zfill(5)
        dv = calcular_dv_modulo11(digits)
        result = digits + dv
        print(f"[DEBUG] Matrícula padronizada {digits} + DV {dv} = {result}")
        return result
    
    from principal.models import Mutuario, ParcelaContrato
    from django.db import connection
    from decimal import Decimal, ROUND_HALF_UP
    from datetime import date
    
    linhas_dados = []

    # Mapeia contrato -> mutuário usando a tabela de relacionamento (fonte de verdade)
    contrato_ids = [c.id for c in contratos if getattr(c, 'id', None)]
    mutuario_por_contrato = {}
    if contrato_ids:
        placeholders = ','.join(['%s'] * len(contrato_ids))
        with connection.cursor() as cur:
            cur.execute(
                f"""
                SELECT contrato_id, mutuario_id
                FROM contrato_mutuario_map
                WHERE contrato_id IN ({placeholders})
                """,
                contrato_ids,
            )
            for contrato_id, mutuario_id in cur.fetchall():
                # Mantém o primeiro vínculo quando houver múltiplos registros
                if contrato_id not in mutuario_por_contrato:
                    mutuario_por_contrato[contrato_id] = mutuario_id

    mutuarios_dict = {}
    if mutuario_por_contrato:
        mut_ids = list(set(mutuario_por_contrato.values()))
        mutuarios_dict = {
            m.id: m for m in Mutuario.objects.filter(id__in=mut_ids)
        }

    contrato_por_codigo = {}
    contratos_por_codigo_normalizado = {}
    for contrato in contratos:
        codigo_normalizado = ''.join(ch for ch in str(getattr(contrato, 'codigo', '') or '') if ch.isdigit())
        if codigo_normalizado:
            codigo_norm = str(int(codigo_normalizado))
            contrato_por_codigo[codigo_norm] = contrato
            contratos_por_codigo_normalizado.setdefault(codigo_norm, []).append(contrato)

    def pontuacao_canonica_contrato(contrato):
        parcelas_qs = ParcelaContrato.objects.filter(contrato=contrato)
        total_parcelas = parcelas_qs.count()
        ultima = parcelas_qs.order_by('-nmens').first()
        score = total_parcelas * 10000
        if total_parcelas > 1:
            score += 500
        if getattr(ultima, 'sddev', None) is not None or getattr(ultima, 'sddev_original', None) is not None:
            score += 250
        if getattr(contrato, 'data_primeiro_venc', None):
            score += 100
        if getattr(contrato, 'data_contrato', None):
            score += 50
        if str(getattr(contrato, 'cod_imovel', '') or '').strip() not in {'', '00000000'}:
            score += 25
        if getattr(contrato, 'tx_juros', None):
            score += 10
        return score

    contrato_canonico_por_codigo = {}
    for codigo_norm, contratos_mesmo_codigo in contratos_por_codigo_normalizado.items():
        if len(contratos_mesmo_codigo) == 1:
            contrato_canonico_por_codigo[codigo_norm] = contratos_mesmo_codigo[0].id
            continue
        canonico = max(contratos_mesmo_codigo, key=pontuacao_canonica_contrato)
        contrato_canonico_por_codigo[codigo_norm] = canonico.id

    # Fallback de CES: primeiro RZ PROGR (rp) não-zero por contrato.
    mapa_primeiro_rp_positivo_por_contrato = {}
    if contrato_ids:
        for contrato_id, _, rp_valor in (
            ParcelaContrato.objects
            .filter(contrato_id__in=contrato_ids, rp__gt=0)
            .order_by('contrato_id', 'nmens')
            .values_list('contrato_id', 'nmens', 'rp')
        ):
            if contrato_id not in mapa_primeiro_rp_positivo_por_contrato:
                mapa_primeiro_rp_positivo_por_contrato[contrato_id] = rp_valor

    # Conversões nominais históricas do Brasil para chegar ao Real (R$)
    # Regras oficiais de corte de zeros (sem correção monetária/inflacionária)
    DATA_CZ = date(1986, 2, 28)      # Cr$ -> Cz$  (÷1000)
    DATA_NCZ = date(1989, 1, 16)     # Cz$ -> NCz$ (÷1000)
    DATA_CR_1990 = date(1990, 3, 16) # NCz$ -> Cr$ (÷1)
    DATA_CRR = date(1993, 8, 1)      # Cr$ -> CR$  (÷1000)
    DATA_REAL = date(1994, 7, 1)     # CR$ -> R$   (÷2750)

    def normalizar_monetario(valor, absoluto=True):
        """Normaliza valor monetário para Decimal, garantindo compatibilidade com layout numérico."""
        if valor is None or valor == '':
            return Decimal('0')
        try:
            dec = Decimal(str(valor))
        except Exception:
            return Decimal('0')
        if absoluto and dec < 0:
            return -dec
        return dec

    def saldo_base_fcvs(parcela):
        """Obtém saldo base priorizando `sddev_original` e normalizando para valor positivo."""
        if not parcela:
            return Decimal('0')
        bruto = parcela.sddev_original if parcela.sddev_original is not None else parcela.sddev
        return normalizar_monetario(bruto, absoluto=True)

    def obter_base_financeira_fh1(contrato, parcela_base):
        valor = saldo_base_fcvs(parcela_base)
        if valor > 0:
            return valor
        valor = normalizar_monetario(getattr(contrato, 'saldo_devedor', None), absoluto=True)
        if valor > 0:
            return valor
        valor = normalizar_monetario(getattr(contrato, 'valor_financiamento', None), absoluto=True)
        if valor > 0:
            return valor
        return Decimal('0')

    def obter_base_financiamento_contratado(contrato, primeira_parcela, parcela_fallback):
        """Obtém base para campos de financiamento contratado/padrão FCVS.

        Prioriza a primeira parcela (origem do contrato), evitando usar saldo residual
        da última parcela como se fosse valor contratado.
        """
        valor = saldo_base_fcvs(primeira_parcela)
        if valor > 0:
            return valor
        valor = normalizar_monetario(getattr(contrato, 'valor_financiamento', None), absoluto=True)
        if valor > 0:
            return valor
        return obter_base_financeira_fh1(contrato, parcela_fallback)

    def converter_nominal_para_real(valor, data_referencia):
        """Converte valor nominal histórico para Real, conforme data de referência."""
        valor_dec = normalizar_monetario(valor, absoluto=True)
        if valor_dec == 0:
            return valor_dec, False

        if not data_referencia:
            return valor_dec, False

        if isinstance(data_referencia, datetime):
            dt_ref = data_referencia.date()
        else:
            dt_ref = data_referencia

        convertido = valor_dec
        houve_conversao = False

        if dt_ref < DATA_CZ:
            convertido = convertido / Decimal('1000')
            houve_conversao = True
        if dt_ref < DATA_NCZ:
            convertido = convertido / Decimal('1000')
            houve_conversao = True
        # 1990 (NCz$ -> Cr$) é 1:1, sem alteração numérica
        if dt_ref < DATA_CRR:
            convertido = convertido / Decimal('1000')
            houve_conversao = True
        if dt_ref < DATA_REAL:
            convertido = convertido / Decimal('2750')
            houve_conversao = True

        return convertido.quantize(Decimal('0.01')), houve_conversao
    
    def fmt_num(valor, tamanho, decimais=0):
        """Formata número com zeros à esquerda"""
        if decimais > 0:
            escala = Decimal('1').scaleb(-decimais)
            valor_dec = Decimal(str(valor)).quantize(escala, rounding=ROUND_HALF_UP)
            valor_int = int((valor_dec * (10 ** decimais)).to_integral_value(rounding=ROUND_HALF_UP))
            return str(valor_int).zfill(tamanho)[:tamanho]
        return str(int(valor)).zfill(tamanho)[:tamanho]

    def fmt_ces(valor):
        """Formata CES em 4 posições (1 inteiro + 3 decimais)."""
        ces = normalizar_monetario(valor, absoluto=True)
        if ces <= 0:
            return '0000'
        return fmt_num(ces, 4, 3)
    
    def fmt_alfa(texto, tamanho):
        """Formata texto com espaços à direita"""
        txt = str(texto or '').upper()
        # Remove acentos e diacríticos para evitar rejeição por encoding.
        txt = unicodedata.normalize('NFKD', txt)
        txt = ''.join(ch for ch in txt if not unicodedata.combining(ch))
        # Mantém apenas ASCII imprimível (32..126), trocando o restante por espaço.
        txt = ''.join(ch if 32 <= ord(ch) <= 126 else ' ' for ch in txt)
        return txt[:tamanho].ljust(tamanho)

    def fmt_endereco(texto, tamanho):
        """Formata endereço para o FH1: apenas letras, dígitos e espaço.
        A CEF rejeita vírgulas, hífens e demais pontuações (erro 100774) no campo ENDEREÇO DO IMÓVEL."""
        txt = str(texto or '').upper()
        # Remove acentos
        txt = unicodedata.normalize('NFKD', txt)
        txt = ''.join(ch for ch in txt if not unicodedata.combining(ch))
        # Substitui qualquer char que não seja letra, dígito ou espaço por espaço
        txt = ''.join(ch if (ch.isalnum() or ch == ' ') else ' ' for ch in txt)
        # Colapsa múltiplos espaços em um só
        txt = ' '.join(txt.split())
        return txt[:tamanho].ljust(tamanho)

    def fmt_nome(texto, tamanho):
        """Formata nome do mutuário para o FH1: apenas letras, dígitos e espaço.
        Evita rejeição 100774 por apóstrofo/crase em sobrenomes (ex.: SANT'ANNA)."""
        txt = str(texto or '').upper()
        # Remove acentos
        txt = unicodedata.normalize('NFKD', txt)
        txt = ''.join(ch for ch in txt if not unicodedata.combining(ch))
        # Mantém apenas letra/dígito/espaço
        txt = ''.join(ch if (ch.isalnum() or ch == ' ') else ' ' for ch in txt)
        # Colapsa múltiplos espaços em um só
        txt = ' '.join(txt.split())
        return txt[:tamanho].ljust(tamanho)

    def fmt_contrato_13(codigo_contrato):
        """Formata contrato em 13 posições, preservando zeros à esquerda para códigos numéricos."""
        bruto = str(codigo_contrato or '').strip()
        if not bruto:
            return '0' * 13
        digitos = ''.join(ch for ch in bruto if ch.isdigit())
        if digitos and len(digitos) <= 13:
            return digitos.zfill(13)
        return fmt_alfa(bruto, 13)
    
    def fmt_data(data_obj):
        """Formata data para DDMMAA"""
        if not data_obj:
            return '000000'
        if isinstance(data_obj, str):
            txt = data_obj.strip()
            for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%Y%m%d', '%d%m%Y', '%d%m%y'):
                try:
                    return datetime.strptime(txt, fmt).strftime('%d%m%y')
                except ValueError:
                    continue
            # Se já estiver no formato DDMMAA
            if txt.isdigit() and len(txt) == 6:
                return txt
            return '000000'
        if isinstance(data_obj, datetime):
            return data_obj.strftime('%d%m%y')
        if isinstance(data_obj, date):
            return data_obj.strftime('%d%m%y')
        return '000000'

    def normalizar_chave_cidade(valor):
        texto = unicodedata.normalize('NFKD', str(valor or '').strip().upper())
        texto = ''.join(ch for ch in texto if not unicodedata.combining(ch))
        return ' '.join(texto.split())

    def carregar_mapa_cadmut_cef_00044():
        """Carrega referências da planilha CEF 00044 para código do município por contrato/cidade."""
        csv_path = Path(__file__).resolve().parent.parent / 'manual' / 'Cadmut 00044 COFLUHAB.csv'
        contrato_map = {}
        cidade_map = {}
        if not csv_path.exists():
            return contrato_map, cidade_map

        try:
            with open(csv_path, 'r', encoding='latin-1', newline='') as file_obj:
                reader = csv.reader(file_obj, delimiter=';')
                for row in reader:
                    if len(row) < 8:
                        continue
                    codigo_contrato = ''.join(ch for ch in str(row[9]).strip() if ch.isdigit()) if len(row) > 9 else ''
                    codigo_municipio = ''.join(ch for ch in str(row[6]).strip() if ch.isdigit())
                    if codigo_contrato and codigo_municipio:
                        codigo_contrato_norm = str(int(codigo_contrato))
                        codigo_municipio_fmt = codigo_municipio.zfill(5)
                        contrato_map[codigo_contrato_norm] = codigo_municipio_fmt

                        contrato_local = contrato_por_codigo.get(codigo_contrato_norm)
                        if contrato_local:
                            mutuario_id = mutuario_por_contrato.get(contrato_local.id)
                            mutuario_local = mutuarios_dict.get(mutuario_id)
                            cidade_texto = normalizar_chave_cidade(getattr(mutuario_local, 'cidade', ''))
                            if cidade_texto and cidade_texto not in cidade_map:
                                cidade_map[cidade_texto] = codigo_municipio_fmt
        except Exception:
            return {}, {}

        return contrato_map, cidade_map

    mapa_cod_municipio_por_contrato, mapa_cod_municipio_por_cidade = carregar_mapa_cadmut_cef_00044()

    def carregar_overrides_valor_garantia_fh1():
        """Carrega overrides manuais de VALOR GARANTIA por contrato.

        Arquivo esperado: manual/fh1_valor_garantia_overrides.csv
        Formato:
            contrato;valor_garantia
            1075;649478.83
        """
        csv_path = Path(__file__).resolve().parent.parent / 'manual' / 'fh1_valor_garantia_overrides.csv'
        overrides = {}
        if not csv_path.exists():
            return overrides

        try:
            with open(csv_path, 'r', encoding='utf-8', newline='') as file_obj:
                reader = csv.reader(file_obj, delimiter=';')
                for row in reader:
                    if not row or len(row) < 2:
                        continue
                    codigo = ''.join(ch for ch in str(row[0]).strip() if ch.isdigit())
                    valor_txt = str(row[1]).strip().replace('.', '').replace(',', '.') if ',' in str(row[1]) else str(row[1]).strip()
                    if not codigo:
                        continue
                    try:
                        valor_dec = Decimal(valor_txt)
                    except Exception:
                        continue
                    if valor_dec > 0:
                        overrides[str(int(codigo))] = valor_dec
        except Exception:
            return {}

        return overrides

    mapa_overrides_valor_garantia = carregar_overrides_valor_garantia_fh1()

    def carregar_overrides_ces_fh1():
        """Carrega overrides manuais de CES (RZ PROGR) por contrato.

        Arquivo esperado: manual/fh1_ces_overrides.csv
        Formato:
            contrato;ces
            1075;0.003645
        """
        csv_path = Path(__file__).resolve().parent.parent / 'manual' / 'fh1_ces_overrides.csv'
        overrides = {}
        if not csv_path.exists():
            return overrides

        try:
            with open(csv_path, 'r', encoding='utf-8', newline='') as file_obj:
                reader = csv.reader(file_obj, delimiter=';')
                for row in reader:
                    if not row or len(row) < 2:
                        continue
                    codigo = ''.join(ch for ch in str(row[0]).strip() if ch.isdigit())
                    valor_txt = str(row[1]).strip().replace(',', '.')
                    if not codigo:
                        continue
                    try:
                        valor_dec = Decimal(valor_txt)
                    except Exception:
                        continue
                    if valor_dec > 0:
                        overrides[str(int(codigo))] = valor_dec
        except Exception:
            return {}

        return overrides

    mapa_overrides_ces = carregar_overrides_ces_fh1()

    def carregar_mapa_contrato_caixa_por_conjunto():
        """Carrega o número do contrato CAIXA por código de conjunto habitacional."""
        try:
            from principal.models import ConjuntoHabitacional
        except Exception:
            return {}

        mapa = {}
        for conjunto in ConjuntoHabitacional.objects.all().only('conjunto', 'contrato').iterator():
            codigo_conjunto = str(getattr(conjunto, 'conjunto', '') or '').strip()
            contrato_caixa = ''.join(ch for ch in str(getattr(conjunto, 'contrato', '') or '') if ch.isdigit())
            if codigo_conjunto and contrato_caixa:
                mapa[codigo_conjunto] = contrato_caixa
        return mapa

    mapa_contrato_caixa_por_conjunto = carregar_mapa_contrato_caixa_por_conjunto()

    def resolver_codigo_municipio_fh1(contrato, mutuario):
        contrato_codigo = ''.join(ch for ch in str(getattr(contrato, 'codigo', '') or '') if ch.isdigit())
        if contrato_codigo:
            codigo = mapa_cod_municipio_por_contrato.get(str(int(contrato_codigo)))
            if codigo:
                return codigo

        cidade_mutuario = str(getattr(mutuario, 'cidade', '') or '').strip().upper() if mutuario else ''
        if cidade_mutuario:
            return mapa_cod_municipio_por_cidade.get(normalizar_chave_cidade(cidade_mutuario), '00000')

        return '00000'

    def obter_endereco_fh1(mutuario):
        """Monta endereco/UF do FH1 com fallback para endereco_fk."""
        if not mutuario:
            return 'RJ', '', None

        uf = str(getattr(mutuario, 'uf', '') or '').strip()
        partes_endereco = [
            str(getattr(mutuario, 'endereco', '') or '').strip(),
            str(getattr(mutuario, 'numero', '') or '').strip(),
            str(getattr(mutuario, 'compl', '') or '').strip(),
        ]
        endereco = ' '.join(parte for parte in partes_endereco if parte).strip()
        origem = None

        if not endereco and getattr(mutuario, 'endereco_fk_id', None):
            endereco_fk = mutuario.endereco_fk
            partes_fallback = [
                str(getattr(endereco_fk, 'endereco', '') or '').strip(),
                str(getattr(endereco_fk, 'numero', '') or '').strip(),
                str(getattr(endereco_fk, 'compl', '') or '').strip(),
            ]
            endereco = ' '.join(parte for parte in partes_fallback if parte).strip()
            if not uf:
                uf = str(getattr(endereco_fk, 'uf', '') or '').strip()
            origem = 'endereco_fk'

        return (uf or 'RJ'), endereco, origem
    # Normaliza matrícula para 6 dígitos (com DV)
    matricula_com_dv = normalizar_matricula_com_dv(matricula)
    
    # Gera todas as linhas FH1 MANUALMENTE (FH1Generator tem problemas no parser)
    linhas_base = []
    contratos_emitidos = set()
    for idx, contrato in enumerate(contratos, start=1):
        print(f"[DEBUG] Gerando ficha para contrato: {getattr(contrato, 'codigo', contrato)} (linha {idx})")
        try:
            contrato_codigo_numerico = ''.join(ch for ch in str(getattr(contrato, 'codigo', '') or '') if ch.isdigit())
            contrato_codigo_normalizado = str(int(contrato_codigo_numerico)) if contrato_codigo_numerico else ''
            if not contrato_codigo_numerico:
                resultado['total_fichas_ignoradas'] += 1
                resultado['detalhes'].append({
                    'contrato': str(contrato.codigo),
                    'status': 'ignorado_codigo_invalido',
                    'motivo': 'Código do contrato sem dígitos; registro excluído do FH1.'
                })
                continue

            contrato_canonico_id = contrato_canonico_por_codigo.get(contrato_codigo_normalizado)
            if contrato_canonico_id and contrato.id != contrato_canonico_id:
                resultado['total_fichas_ignoradas'] += 1
                resultado['detalhes'].append({
                    'contrato': str(contrato.codigo),
                    'status': 'ignorado_duplicado',
                    'motivo': f'Registro duplicado do contrato {contrato_codigo_normalizado}; mantido apenas o canônico no FH1.'
                })
                continue
            if contrato_codigo_normalizado and contrato_codigo_normalizado in contratos_emitidos:
                resultado['total_fichas_ignoradas'] += 1
                resultado['detalhes'].append({
                    'contrato': str(contrato.codigo),
                    'status': 'ignorado_duplicado_runtime',
                    'motivo': f'Contrato {contrato_codigo_normalizado} já emitido anteriormente no lote.'
                })
                continue

            # Busca mutuário correto do contrato pelo mapa contrato_mutuario_map
            mutuario_id = mutuario_por_contrato.get(contrato.id)
            mutuario = mutuarios_dict.get(mutuario_id)
            if not mutuario and contrato.conjunto:
                # Fallback defensivo para bases sem mapeamento completo
                mutuario = Mutuario.objects.filter(conjunto=contrato.conjunto).first()
            
            # Busca primeira parcela para valores
            primeira = ParcelaContrato.objects.filter(contrato=contrato).order_by('nmens').first()
            ultima = ParcelaContrato.objects.filter(contrato=contrato).order_by('-nmens').first()
            parcela_base = ultima or primeira
            avisos_contrato = []
            data_base_saldo = (parcela_base.dtvenc if parcela_base and parcela_base.dtvenc else contrato.data_contrato)
            data_base_financ = (primeira.dtvenc if primeira and primeira.dtvenc else contrato.data_contrato)
            base_saldo_fh1 = obter_base_financeira_fh1(contrato, parcela_base)
            base_financiamento_fh1 = obter_base_financiamento_contratado(contrato, primeira, parcela_base)
            if base_saldo_fh1 <= 0 and base_financiamento_fh1 <= 0:
                resultado['total_fichas_ignoradas'] += 1
                resultado['detalhes'].append({
                    'contrato': str(contrato.codigo),
                    'status': 'pendente_financeiro',
                    'motivo': 'Contrato sem base financeira segura para campos de financiamento/saldo no FH1.'
                })
                continue

            # Regra de sinal para layout: valores monetários vão positivos nos campos numéricos,
            # e o indicador D/C sinaliza se a origem era débito (D) ou crédito (C).
            saldo_origem = None
            if parcela_base:
                saldo_origem = parcela_base.sddev_original if parcela_base.sddev_original is not None else parcela_base.sddev
            saldo_origem_dec = normalizar_monetario(saldo_origem, absoluto=False)
            movimento_dc = 'C' if saldo_origem_dec < 0 else 'D'

            if parcela_base and parcela_base.sddev is not None and parcela_base.sddev < 0:
                avisos_contrato.append(
                    f"Saldo devedor negativo na parcela base ({parcela_base.sddev}); convertido para valor absoluto no FH1."
                )
            if parcela_base and parcela_base.sddev_original is not None and parcela_base.sddev_original < 0:
                avisos_contrato.append(
                    f"Saldo devedor original negativo ({parcela_base.sddev_original}); convertido para valor absoluto no FH1."
                )
            if parcela_base and parcela_base.fcvs is not None and parcela_base.fcvs < 0:
                avisos_contrato.append(
                    f"FCVS mensal negativo ({parcela_base.fcvs}); convertido para valor absoluto no FH1."
                )
            if movimento_dc == 'C':
                avisos_contrato.append(
                    "Saldo base negativo na origem; indicador D/C preenchido como 'C' no campo 62."
                )
            
            # Cria linha FH1 de 430 caracteres manualmente
            linha = ''
            uf_fh1, endereco_fh1, origem_endereco = obter_endereco_fh1(mutuario)
            codigo_municipio_fh1 = resolver_codigo_municipio_fh1(contrato, mutuario)
            if origem_endereco == 'endereco_fk':
                avisos_contrato.append(
                    "Endereco do mutuário ausente no cadastro principal; FH1 preenchido com fallback de endereco_fk."
                )
            
            # ==== CONTROLE (posições 1-23) ====
            linha += '19'  # 01-02: UFS (RJ)
            linha += matricula_com_dv  # 03-08: Matrícula com DV (5 dig + DV = 6 chars)
            linha += fmt_contrato_13(contrato.codigo)  # 09-21: Número do contrato (com zeros à esquerda)
            linha += '1'  # 22: HIPOTECA (1ª hipoteca)
            linha += '1'  # 23: TIPO DE REGISTRO (1 = dados FH1)
            linha += '00'  # 24-25: SEQUENCIAL
            linha += '0'  # 26: CONSTANTE
            
            # ==== DADOS DO MUTUÁRIO (posições 27-135) ====
            linha += fmt_nome(mutuario.nome if mutuario else '', 40)  # 27-66: Nome
            linha += '1'  # 67: Tipo CPF
            cpf_limpo = ''.join(c for c in (mutuario.cpf or '') if c.isdigit()) if mutuario else ''
            linha += fmt_alfa(cpf_limpo, 17)  # 68-84: CPF
            linha += fmt_data(mutuario.dtnasc if mutuario else None)  # 85-90: Data nascimento
            linha += fmt_num(codigo_municipio_fh1, 5, 0)  # 91-95: Código município
            linha += fmt_alfa(uf_fh1, 2)  # 96-97: UF
            linha += fmt_endereco(endereco_fh1, 38)  # 98-135: Endereço
            
            # ==== DADOS DO CONTRATO (posições 136-405) ====
            valor_garantia_bruto = base_saldo_fh1
            if contrato_codigo_normalizado in mapa_overrides_valor_garantia:
                valor_garantia_bruto = mapa_overrides_valor_garantia[contrato_codigo_normalizado]
                avisos_contrato.append(
                    f"Override manual de VALOR GARANTIA aplicado: contrato {contrato_codigo_normalizado} -> {valor_garantia_bruto}."
                )
            valor_garantia, _ = converter_nominal_para_real(valor_garantia_bruto, data_base_saldo)
            if valor_garantia <= 0 and valor_garantia_bruto > 0:
                valor_garantia = valor_garantia_bruto.quantize(Decimal('0.01'))
            linha += fmt_data(contrato.data_contrato)  # 136-141: Data contrato
            linha += fmt_num(valor_garantia, 12, 2)  # 142-153: Valor garantia
            linha += '00'  # 154-155: IM
            linha += fmt_data(contrato.data_contrato)  # 156-161: Data legislação
            
            # Valores financeiros
            valor_financ_bruto = base_financiamento_fh1
            valor_financ, conv_financ = converter_nominal_para_real(valor_financ_bruto, data_base_financ)
            if conv_financ:
                avisos_contrato.append(
                    f"Conversão monetária aplicada em Valor Financiamento/FCVS: {valor_financ_bruto} -> {valor_financ} (R$), data base {data_base_financ}."
                )
            if valor_financ <= 0 and valor_financ_bruto > 0:
                valor_financ = valor_financ_bruto.quantize(Decimal('0.01'))
                avisos_contrato.append(
                    f"Valor Financiamento/FCVS preservado no nominal ({valor_financ_bruto}) para evitar zero após conversão histórica."
                )
            linha += fmt_num(valor_financ, 12, 2)  # 162-173: Valor financiamento contratado
            linha += fmt_num(valor_financ, 12, 2)  # 174-185: Valor padrão FCVS
            
            linha += fmt_alfa(contrato.cat_prof if contrato.cat_prof else '', 5)  # 186-190: Cat. profissional
            linha += 'N'  # 191: Seguro crédito
            linha += 'N'  # 192: Carência
            linha += 'N'  # 193: Seguro DFI
            linha += 'N'  # 194: PROER
            linha += ' '  # 195: Vago
            linha += fmt_num(contrato.prazo if contrato.prazo else 0, 3, 0)  # 196-198: Prazo
            linha += fmt_num(contrato.tx_juros if contrato.tx_juros else Decimal(0), 6, 4)  # 199-204: Taxa juros
            ces_rz_progr = normalizar_monetario(primeira.rp if primeira else Decimal(0), absoluto=True)
            if ces_rz_progr <= 0:
                ces_rz_progr = normalizar_monetario(
                    mapa_primeiro_rp_positivo_por_contrato.get(getattr(contrato, 'id', None), Decimal(0)),
                    absoluto=True,
                )
            if contrato_codigo_normalizado in mapa_overrides_ces:
                ces_rz_progr = mapa_overrides_ces[contrato_codigo_normalizado]
                avisos_contrato.append(
                    f"Override manual de CES aplicado: contrato {contrato_codigo_normalizado} -> {ces_rz_progr}."
                )
            linha += fmt_ces(ces_rz_progr)  # 205-208: CES (RZ PROGR)
            linha += fmt_alfa(contrato.pr if contrato.pr else '', 3)  # 209-211: Plano
            linha += '1'  # 212: ST
            linha += '1'  # 213: RJ (reajuste anual 1º trimestre - UPC)
            linha += '01'  # 214-215: RR
            linha += 'UPC'  # 216-218: INDEX (indexador: Unidade Padrão de Capital)
            linha += fmt_num(contrato.prazo if contrato.prazo else 0, 3, 0)  # 219-221: Prazo FCVS
            linha += fmt_num(contrato.tx_juros if contrato.tx_juros else Decimal(0), 6, 4)  # 222-227: Taxa FCVS
            linha += fmt_ces(ces_rz_progr)  # 228-231: CES FCVS (RZ PROGR)
            linha += fmt_alfa(contrato.pr if contrato.pr else '', 3)  # 232-234: Plano FCVS
            linha += '1'  # 235: ST FCVS
            linha += '1'  # 236: RJ FCVS (reajuste anual 1º trimestre - UPC)
            linha += '01'  # 237-238: RR FCVS
            linha += 'UPC'  # 239-241: INDEX FCVS (indexador: Unidade Padrão de Capital)
            
            # ==== CAMPOS ADICIONAIS (posições 242-318) ====
            # 43: DATA SALDO CONSTRUÇÃO (242-247) - DDMMAA
            linha += fmt_data(contrato.data_contrato)  # Usando data do contrato como referência
            
            # 44: SALDO DEVEDOR (248-259) - 10 INT + 2 DEC
            saldo_dev_bruto = base_saldo_fh1
            saldo_dev, conv_saldo = converter_nominal_para_real(saldo_dev_bruto, data_base_saldo)
            if conv_saldo:
                avisos_contrato.append(
                    f"Conversão monetária aplicada em Saldo Devedor FH1: {saldo_dev_bruto} -> {saldo_dev} (R$), data base {data_base_saldo}."
                )
            linha += fmt_num(saldo_dev, 12, 2)
            
            # 45: 1º VENCIMENTO (260-265) - DDMMAA
            dt_venc = primeira.dtvenc if primeira and primeira.dtvenc else contrato.data_contrato
            linha += fmt_data(dt_venc)
            
            # 46: SEGURO CREDITO / MIP / DFI (266-273) - 6 INT + 2 DEC
            linha += fmt_num(0, 8, 2)
            
            # 47: VALOR DA PRESTAÇÃO (274-283) - 8 INT + 2 DEC
            parcela_prestacao = primeira or parcela_base
            valor_prest_bruto = normalizar_monetario(
                parcela_prestacao.em if parcela_prestacao else Decimal(0),
                absoluto=True,
            )
            if valor_prest_bruto <= 0:
                amort = normalizar_monetario(parcela_prestacao.amort if parcela_prestacao else Decimal(0), absoluto=True)
                juros = normalizar_monetario(parcela_prestacao.juros if parcela_prestacao else Decimal(0), absoluto=True)
                seguro = normalizar_monetario(parcela_prestacao.seguro if parcela_prestacao else Decimal(0), absoluto=True)
                tca = normalizar_monetario(parcela_prestacao.tca if parcela_prestacao else Decimal(0), absoluto=True)
                valor_prest_bruto = amort + juros + seguro + tca
            valor_prest, _ = converter_nominal_para_real(valor_prest_bruto, data_base_financ)
            if valor_prest <= 0 and valor_prest_bruto > 0:
                valor_prest = valor_prest_bruto.quantize(Decimal('0.01'))
                avisos_contrato.append(
                    f"Valor da prestação preservado no nominal ({valor_prest_bruto}) para evitar zero após conversão histórica."
                )
            linha += fmt_num(valor_prest, 10, 2)
            
            # 49: TCA/TAC (284-291) - 6 INT + 2 DEC
            linha += fmt_num(0, 8, 2)
            
            # 50: FCVS MENSAL (292-299) - 6 INT + 2 DEC
            fcvs_mensal_bruto = normalizar_monetario(parcela_base.fcvs if parcela_base else Decimal(0), absoluto=True)
            fcvs_mensal, _ = converter_nominal_para_real(fcvs_mensal_bruto, data_base_saldo)
            linha += fmt_num(fcvs_mensal, 8, 2)
            
            # 51: RAZÃO ACRES/DECRES (300-307) - 6 INT + 2 DEC
            linha += fmt_num(0, 8, 2)
            
            # 52: TIPO EVENTO (308-310) - 3 ALFA
            # SET e SIT são códigos internos do CADMUT — mapear para TPZ (Término de Prazo FCVS).
            # Todos os contratos da COFLUHAB já encerraram o prazo ou foram liquidados.
            _ocorr = str(getattr(contrato, 'ocorrencia', '') or '').strip().upper()[:3]
            _CADMUT_PARA_FCVS = {'SET': 'TPZ', 'SIT': 'TPZ'}
            tipo_evento = _CADMUT_PARA_FCVS.get(_ocorr, _ocorr) or 'TPZ'
            linha += fmt_alfa(tipo_evento, 3)

            # 53: DATA DO EVENTO (311-316) - DDMMAA
            # Prioriza data do contrato e usa outras datas de referência como fallback.
            data_evento = (
                contrato.data_contrato
                or contrato.data_primeiro_venc
                or (parcela_base.dtvenc if parcela_base and parcela_base.dtvenc else None)
            )
            linha += fmt_data(data_evento)
            
            # 54: OR/CO (317-318) - 2 NUM
            # 11 = Recursos próprios do Agente Financeiro (SBPE/caderneta de poupança)
            linha += '11'
            
            # 55: % CAIXA (319-322) - 4 NUM (100%)
            linha += '0100'
            
            # 56: N.º CONTR. EMPR. CAIXA (323-340) - 18 NUM
            contrato_caixa = mapa_contrato_caixa_por_conjunto.get(str(getattr(contrato, 'conjunto', '') or '').strip(), '')
            if not contrato_caixa:
                avisos_contrato.append(
                    f"Contrato CAIXA não encontrado para conjunto {getattr(contrato, 'conjunto', '')}; campo 56 preenchido com zeros."
                )
            linha += fmt_num(contrato_caixa or 0, 18, 0)
            
            # 57: TAXA JUROS EVENTO (341-346) - 2 INT + 4 DEC
            taxa_evento = contrato.tx_juros if contrato.tx_juros else Decimal(0)
            if taxa_evento <= 0:
                raise ValueError(
                    f"Campo obrigatório TAXA JUROS EVENTO zerado para contrato {getattr(contrato, 'codigo', '')}. "
                    "Informe taxa de juros válida (> 0)."
                )
            linha += fmt_num(taxa_evento, 6, 4)
            
            # 58: VAF1 - VALOR BÁSICO (347-360) - 12 INT + 2 DEC
            linha += fmt_num(0, 14, 2)
            
            # 59: VAF2 - VALOR COMPLEMENTAR (361-374) - 12 INT + 2 DEC
            linha += fmt_num(0, 14, 2)
            
            # 60: VAF3 - VALOR RESIDUAL (375-388) - 12 INT + 2 DEC
            linha += fmt_num(0, 14, 2)
            
            # 61: JUROS CALCULADOS PELO AGENTE FINANCEIRO (389-402) - 14 NUM
            juros_calc_bruto = normalizar_monetario(parcela_base.juros if parcela_base else Decimal(0), absoluto=True)
            juros_calc, _ = converter_nominal_para_real(juros_calc_bruto, data_base_saldo)
            linha += fmt_num(juros_calc, 14, 2)
            
            # 62: DEBITO/CRÉDITO (403) - 1 ALFA (D ou C)
            linha += movimento_dc
            
            # 63: QUANTIDADE DE ALTERAÇÕES (404-405) - 2 NUM
            linha += '00'
            
            # Debug: Verifica tamanho antes do preenchimento
            tamanho_antes = len(linha)
            
            # Preenche o restante até posição 430 com espaços
            # Linha deve ter 430 caracteres ANTES de adicionar identificação do lote
            while len(linha) < 430:
                linha += ' '
            
            linha = linha[:430]  # Garante exatamente 430 caracteres
            
            # Debug: Verifica tamanho final
            if len(linha) != 430:
                print(f"⚠️  AVISO: Linha do contrato {contrato.codigo} ficou com {len(linha)} chars (esperado 430)")
                print(f"   Tamanho antes do preenchimento: {tamanho_antes}")
            
            linhas_base.append(linha)
            if contrato_codigo_normalizado:
                contratos_emitidos.add(contrato_codigo_normalizado)
            resultado['total_fichas_sucesso'] += 1
            if avisos_contrato:
                resultado['detalhes'].append({
                    'contrato': str(contrato.codigo),
                    'avisos': [{'mensagem': msg} for msg in avisos_contrato],
                })
        
        except Exception as e:
            resultado['total_fichas_erro'] += 1
            resultado['erros'].append({
                'contrato': str(contrato.codigo),
                'linha': idx,
                'erro': str(e)
            })
    
    resultado['total_fichas'] = len(linhas_base)
    print(f"[DEBUG] Total de fichas FH1 geradas com sucesso: {resultado['total_fichas_sucesso']}")
    print(f"[DEBUG] Total de fichas FH1 com erro: {resultado['total_fichas_erro']}")
    if resultado['erros']:
        print(f"[ERROS DETALHADOS] {resultado['erros']}")
    
    # Gera HEADER E DADOS
    if linhas_base:
        hoje = datetime.now()
        
        # ==== MONTA IDENTIFICAÇÃO DO LOTE PARA HEADER (com matrícula 6 dígitos incluindo DV) ====
        identificacao_lote_header = ''
        identificacao_lote_header += '19'  # UFS (2 chars) - RJ
        identificacao_lote_header += matricula_com_dv  # Matrícula com DV (6 chars)
        identificacao_lote_header += hoje.strftime('%d%m%y')  # Data DDMMAA (6 chars)
        identificacao_lote_header += numero_lote.zfill(3)  # Número do lote (3 chars)
        identificacao_lote_header += 'S'  # Forma: Simplificada (1 char)
        identificacao_lote_header += 'I'  # Tipo: Inicial (1 char)
        identificacao_lote_header += ' ' * 6  # FILLER (6 chars)
        
        # Verifica tamanhos
        if len(identificacao_lote_header) != 25:
            print(f"[WARN] ERRO: ID Lote HEADER tem {len(identificacao_lote_header)} chars, esperado 25!")
        print(f"[DEBUG] HEADER ID: [{identificacao_lote_header}] ({len(identificacao_lote_header)} chars)")
        print(f"[DEBUG] DADOS ID: [{identificacao_lote_header}] ({len(identificacao_lote_header)} chars)")
        
        # ==== Adiciona IDENTIFICAÇÃO DO LOTE PARA DADOS em cada linha FH1 ====
        for linha_base in linhas_base:
            # A linha já tem 430 caracteres, vamos substituir os últimos 25
            linha_final = linha_base[:405] + identificacao_lote_header
            
            if len(linha_final) != 430:
                print(f"[WARN] Linha DADOS ficou com {len(linha_final)} chars (esperado 430)")
            
            linhas_dados.append(linha_final)
        
        # ==== MONTA HEADER (430 caracteres) ====
        header = [' '] * 430
        
        # CONTROLE (posições 1-23)
        # 01. UFS (1-2)
        header[0:2] = '19'  # RJ
        
        # 02. MATRÍCULA AG.FINANC (3-8) - 5 dígitos + DV
        header[2:8] = matricula_com_dv  # 00044 + 0 = 000440
        
        # 03. CONSTANTE (9-22): ZEROS (inclui posição 9 que seria DV)
        header[8:22] = '0' * 14
        
        # 04. TIPO DE REGISTRO (23): 0 = HEADER
        header[22] = '0'
        
        # QUANTIDADE (posições 24-37)
        # 05. CONSTANTE (24-32): ZEROS
        header[23:32] = '0' * 9
        
        # 06. QTD DOCUMENTOS (33-37)
        header[32:37] = str(len(linhas_dados)).zfill(5)
        
        # 07. FILLER (38-405): BRANCOS
        header[37:405] = ' ' * 368
        
        # IDENTIFICAÇÃO DO LOTE (406-430) - USA MATRÍCULA 6 DÍGITOS
        header[405:430] = identificacao_lote_header
        
        resultado['header_conteudo'] = ''.join(header)
        
        # ==== MONTA DADOS (apenas as linhas FH1, SEM header!) ====
        # IMPORTANTE: O arquivo DADOS não deve conter o HEADER!
        # A CEF espera apenas os registros tipo '1' (fichas FH1)
        resultado['dados_conteudo'] = '\n'.join(linhas_dados)
    
    return resultado


# Exemplo de uso (mock)
if __name__ == '__main__':
    print("🏭 Geradores Automáticos de Fichas CEF")
    print("=" * 60)
    
    # Cria objetos mock para teste
    class MockMutuario:
        def __init__(self):
            self.nome = "JOÃO DA SILVA"
            self.cpf = "12345678909"
            self.dtnasc = date(1980, 1, 1)
            self.endereco = "RUA EXEMPLO"
            self.numero = "123"
            self.compl = "APTO 45"
            self.bairro = "CENTRO"
            self.cidade = "SAO PAULO"
            self.uf = "SP"
            self.cep = "01234567"
            self.telefone = "11999887766"
            self.email = "joao@example.com"
            self.conjunto = "001"
    
    class MockContrato:
        def __init__(self):
            self.codigo = "0001234567890"
            self.conjunto = "001"
            self.data_contrato = date(2020, 1, 15)
            self.prazo = 240
            self.tx_juros = Decimal("8.5")
            self.sa = "SAC"
            self.cat_prof = "12345"
            self.pr = "01"
            self.data_primeiro_venc = date(2020, 2, 15)
        
        class parcelas:
            @staticmethod
            def all():
                return []
            
            @staticmethod
            def exists():
                return False
    
    # Testa geração FH1
    print("\n📄 Testando geração de FH1...")
    try:
        mutuario_mock = MockMutuario()
        contrato_mock = MockContrato()
        
        generator_fh1 = FH1Generator(validar=False)  # Sem validação para mock
        linha_fh1, erros = generator_fh1.gerar_de_contrato(contrato_mock, mutuario_mock)
        
        print(f"   ✅ FH1 gerada com sucesso!")
        print(f"   Tamanho: {len(linha_fh1)} caracteres")
        print(f"   Preview: {linha_fh1[:80]}...")
        
        if erros:
            print(f"   ⚠️  {len(erros)} avisos encontrados")
    
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # Testa geração CADMUT
    print("\n📋 Testando geração de CADMUT...")
    try:
        generator_cadmut = CADMUTGenerator(validar=False)
        linha_cadmut, erros = generator_cadmut.gerar_de_mutuario(mutuario_mock)
        
        print(f"   ✅ CADMUT gerada com sucesso!")
        print(f"   Tamanho: {len(linha_cadmut)} caracteres")
        print(f"   Preview: {linha_cadmut[:80]}...")
    
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # Testa geração de lote
    print("\n📦 Testando geração em lote...")
    try:
        lote_gen = LoteGenerator()
        contratos_mock = [MockContrato(), MockContrato()]
        
        resultado = lote_gen.gerar_lote_fh1(contratos_mock, incluir_validacao=False)
        
        print(f"   Total: {resultado['total']}")
        print(f"   ✅ Sucesso: {resultado['sucesso']}")
        print(f"   ❌ Falha: {resultado['falha']}")
        print(f"   📄 Fichas geradas: {len(resultado['fichas'])}")
    
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # Testa geração de arquivo completo
    print("\n📁 Testando geração de arquivo completo...")
    try:
        arquivo_gen = ArquivoFCVSGenerator()
        
        # Simula geração (não cria arquivo real)
        print(f"   ✅ ArquivoFCVSGenerator inicializado")
        print(f"   Matrícula: {arquivo_gen.matricula_agente}")
        print(f"   Tipo movimento: {arquivo_gen.tipo_movimento}")
        
        # Testa header/trailer
        header = arquivo_gen._gerar_header(10)
        trailer = arquivo_gen._gerar_trailer(10)
        
        print(f"   ✅ HEADER gerado: {len(header)} caracteres")
        print(f"   ✅ TRAILER gerado: {len(trailer)} caracteres")
    
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    print("\n✅ Testes de geração concluídos!")
    print("\n💡 Próximos passos:")
    print("   1. Integrar com views Django")
    print("   2. Adicionar configuração de matrícula/agente")
    print("   3. Implementar tabela de códigos IBGE")
    print("   4. Adicionar suporte a outros tipos de ficha")
    print("   5. Criar interface para download de arquivos gerados")
