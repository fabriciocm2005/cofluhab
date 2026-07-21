"""
Parsers para Fichas CEF - FCVS e CADMUT

Este módulo contém parsers para ler e escrever fichas de envio para a CEF,
baseados nas especificações extraídas dos manuais oficiais.

Tipos de fichas suportados:
- FH1: Ficha para Habilitação ao FCVS (201 campos)
- FH2: Ficha complementar de Habilitação
- FH3: Ficha de alterações (25 campos)
- RCV: Receita
- RNV: Registro (5 campos)
- RCNP: Registro de contratos sem manifestação (layout legado)
- CADMUT: Cadastro de Mutuários (617 campos)
- HEADER: Cabeçalho comum a todos os tipos

Autor: CEF Integration Bot
Data: 2026-01-23
"""

import re
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from decimal import Decimal


# Fallback para layouts legados VS651 (DBFs LOTE*.DBF com 430 bytes úteis).
LEGACY_LOTE_SCHEMAS = {
    'FH2': [
        ('UFS', 2), ('MATAGE', 6), ('NOCONT', 13), ('HIP', 1), ('TR', 1), ('SEQ', 2),
        ('USO', 1), ('CODALT', 3), ('DTALT', 6), ('MESANOALT', 4), ('PZREMA', 3),
        ('TXJINDICE', 8), ('CODCATEG', 5), ('VALT', 12), ('PLANOCF', 3), ('STCF', 1),
        ('RJCF', 1), ('RRCF', 2), ('INDEXCF', 3), ('ESPACO1FH2', 254), ('ESPACO2FH2', 74),
        ('IDLUFS', 2), ('IDLMATAGE', 6), ('IDLDTPREE', 6), ('IDLLOTVOL', 3),
        ('IDLFORMAH', 1), ('IDLTPMOV', 1), ('IDLESPACO', 6),
    ],
    'RCV': [
        ('UFS', 2), ('MATAGE', 6), ('NOCONT', 13), ('HIP', 1), ('TR', 1), ('FCVSZEROS', 3),
        ('UFSFCVS', 2), ('NOFCVS', 8), ('SEQ', 2), ('USO', 1), ('CODCAMPO', 3), ('CONTEUDO', 40),
        ('ESPACO1FAC', 254), ('ESPACO2FAC', 69), ('IDLUFS', 2), ('IDLMATAGE', 6),
        ('IDLDTPREE', 6), ('IDLLOTVOL', 3), ('IDLFORMAH', 1), ('IDLTPMOV', 1), ('IDLESPACO', 6),
    ],
    'RCNP': [
        ('UFS', 2), ('MATAGE', 6), ('NOCONT', 13), ('HIP', 1), ('TR', 1), ('FCVSZEROS', 3),
        ('UFSFCVS', 2), ('NOFCVS', 8), ('SEQ', 2), ('USO', 1), ('CODCAMPO', 3), ('CONTEUDO', 40),
        ('ESPACO1FAC', 254), ('ESPACO2FAC', 69), ('IDLUFS', 2), ('IDLMATAGE', 6),
        ('IDLDTPREE', 6), ('IDLLOTVOL', 3), ('IDLFORMAH', 1), ('IDLTPMOV', 1), ('IDLESPACO', 6),
    ],
}


def _carregar_campos_legado(tipo: str) -> List['CampoSpec']:
    """Monta campos posicionais a partir dos schemas legados VS651."""
    campos = []
    inicio = 1
    for seq, (nome, tamanho) in enumerate(LEGACY_LOTE_SCHEMAS.get(tipo, []), start=1):
        fim = inicio + tamanho - 1
        campos.append(
            CampoSpec(
                seq=str(seq),
                nome=nome,
                inicio=inicio,
                fim=fim,
                tamanho=tamanho,
                tipo='ALFA',
                formato='LEGACY_VS651',
                observacoes=f'Fallback {tipo} a partir de LOTE{tipo}.DBF',
            )
        )
        inicio = fim + 1
    return campos


class CampoSpec:
    """Especificação de um campo de ficha CEF"""
    
    def __init__(self, seq: str, nome: str, inicio: int, fim: int, 
                 tamanho: int, tipo: str, formato: str = "", 
                 observacoes: str = ""):
        self.seq = seq
        self.nome = nome
        self.inicio = inicio
        self.fim = fim
        self.tamanho = tamanho
        self.tipo = tipo  # NUM, ALFA, etc
        self.formato = formato
        self.observacoes = observacoes
    
    def __repr__(self):
        return f"Campo({self.seq}, {self.nome}, {self.inicio}-{self.fim}, {self.tipo})"
    
    @classmethod
    def from_definicao(cls, definicao: str):
        """
        Extrai especificação de campo a partir de string de definição
        
        Exemplos:
        "01 . UFS  01 a 02  2 NUM"
        "08 NOME DO MUT. PRINCIPAL  27 a 66  40 ALFA"
        "16 VALOR DA GARANTIA  142 a 153  12 NUM  10 INT. e 2 DEC."
        """
        # Padrão: SEQ NOME POS_INICIO a POS_FIM TAMANHO TIPO [FORMATO]
        pattern = r'^(\d+)\s*\.?\s+([A-ZÀ-Ú\s/\.º°]+?)\s+(\d+)\s+a\s+(\d+)\s+(\d+)\s+(NUM|ALFA|-)(.*)$'
        match = re.match(pattern, definicao.strip())
        
        if match:
            seq, nome, inicio, fim, tamanho, tipo, resto = match.groups()
            return cls(
                seq=seq,
                nome=nome.strip(),
                inicio=int(inicio),
                fim=int(fim),
                tamanho=int(tamanho),
                tipo=tipo,
                formato=resto.strip(),
                observacoes=""
            )
        
        # Padrão alternativo sem posições (apenas tamanho e tipo)
        pattern2 = r'^(\d+)\s*\.?\s+([A-ZÀ-Ú\s/\.º°]+?)\s+(NUM|ALFA|-)\s+(\d+)(.*)$'
        match2 = re.match(pattern2, definicao.strip())
        
        if match2:
            seq, nome, tipo, tamanho, resto = match2.groups()
            return cls(
                seq=seq,
                nome=nome.strip(),
                inicio=0,  # Será calculado
                fim=0,
                tamanho=int(tamanho),
                tipo=tipo,
                formato=resto.strip(),
                observacoes=""
            )
        
        # Se não conseguir parsear, retorna None
        return None


class FichaParser:
    """Classe base para parsers de fichas CEF"""
    
    TAMANHO_REGISTRO = 430  # Tamanho padrão de registro FCVS
    
    def __init__(self):
        self.campos: List[CampoSpec] = []
        self.dados: Dict[str, Any] = {}
        self.layout_source: str = 'manual_atual'
        self._carregar_especificacao()

    def validar_estrutura_linha(self, linha: str) -> tuple:
        """
        Valida estrutura posicional mínima da linha para o layout carregado.

        Returns:
            (ok: bool, mensagem: str)
        """
        if linha is None:
            return (False, 'Linha ausente')

        if not self.campos:
            return (False, 'Layout sem campos carregados')

        ultimo_fim = max((c.fim for c in self.campos if c.fim > 0), default=0)
        if ultimo_fim and len(linha) < ultimo_fim:
            return (
                False,
                f'Linha menor que layout: tamanho={len(linha)} < esperado_min={ultimo_fim} ({self.layout_source})',
            )

        return (True, f'Layout {self.layout_source} validado (len={len(linha)})')
    
    def _carregar_especificacao(self):
        """Carrega especificação dos campos do arquivo JSON"""
        pass  # Implementado nas subclasses
    
    def ler_linha(self, linha: str) -> Dict[str, Any]:
        """
        Lê uma linha de arquivo texto e extrai os campos
        
        Args:
            linha: String com a linha do arquivo (formato posicional)
        
        Returns:
            Dicionário com os campos extraídos
        """
        dados = {}
        linha_padded = linha.ljust(self.TAMANHO_REGISTRO)
        
        for campo in self.campos:
            if campo.inicio > 0 and campo.fim > 0:
                valor = linha_padded[campo.inicio-1:campo.fim].strip()
                dados[campo.nome] = self._converter_valor(valor, campo)
        
        return dados
    
    def escrever_linha(self, dados: Dict[str, Any]) -> str:
        """
        Converte dicionário de dados em linha de texto posicional
        
        Args:
            dados: Dicionário com valores dos campos
        
        Returns:
            String formatada no formato posicional CEF
        """
        linha = [' '] * self.TAMANHO_REGISTRO
        
        for campo in self.campos:
            if campo.inicio > 0 and campo.fim > 0:
                valor = dados.get(campo.nome, '')
                valor_formatado = self._formatar_valor(valor, campo)
                
                # Preenche na posição correta
                for i, char in enumerate(valor_formatado):
                    pos = campo.inicio - 1 + i
                    if pos < len(linha):
                        linha[pos] = char
        
        return ''.join(linha)
    
    def _converter_valor(self, valor: str, campo: CampoSpec) -> Any:
        """Converte string do arquivo para tipo Python apropriado"""
        if not valor:
            return None
        
        if campo.tipo == 'NUM':
            # Verifica se é decimal (INT. e DEC.)
            if 'INT. e' in campo.formato or 'DEC.' in campo.formato:
                try:
                    # Remove zeros à esquerda e converte
                    return Decimal(valor) / 100  # Assume 2 decimais por padrão
                except:
                    return None
            else:
                try:
                    return int(valor)
                except:
                    return None
        
        return valor  # ALFA ou outros
    
    def _formatar_valor(self, valor: Any, campo: CampoSpec) -> str:
        """Formata valor Python para string posicional"""
        if valor is None:
            valor = ''
        
        if campo.tipo == 'NUM':
            # Verifica se é decimal
            if 'INT. e' in campo.formato or 'DEC.' in campo.formato:
                if isinstance(valor, (int, float, Decimal)):
                    # Converte para centavos e preenche com zeros
                    valor_centavos = int(valor * 100)
                    return str(valor_centavos).zfill(campo.tamanho)
                else:
                    return '0' * campo.tamanho
            else:
                # Numérico inteiro
                if isinstance(valor, (int, float)):
                    return str(int(valor)).zfill(campo.tamanho)
                else:
                    return '0' * campo.tamanho
        
        # ALFA - preenche com espaços à direita
        valor_str = str(valor) if valor else ''
        return valor_str.ljust(campo.tamanho)[:campo.tamanho]
    
    def validar(self) -> List[str]:
        """
        Valida os dados carregados
        
        Returns:
            Lista de erros encontrados (vazia se válido)
        """
        erros = []
        
        for campo in self.campos:
            valor = self.dados.get(campo.nome)
            
            # Verifica obrigatoriedade (pode ser expandido)
            if campo.nome in ['UFS', 'MAT. AG. FINANC. /DV', 'CPF/CI']:
                if not valor:
                    erros.append(f"Campo obrigatório vazio: {campo.nome}")
            
            # Valida tamanho
            if valor and isinstance(valor, str):
                if len(valor) > campo.tamanho:
                    erros.append(f"Campo {campo.nome} excede tamanho máximo: {len(valor)} > {campo.tamanho}")
        
        return erros


class FH1Parser(FichaParser):
    """Parser para Ficha FH1 - Habilitação ao FCVS (201 campos)"""
    
    def _carregar_especificacao(self):
        """Carrega os 201 campos da FH1"""
        json_path = Path(__file__).parent.parent / 'cef_conhecimento_completo.json'
        
        if json_path.exists():
            with open(json_path, 'r', encoding='utf-8') as f:
                conhecimento = json.load(f)
                
            fh1_spec = conhecimento.get('fichas_envio', {}).get('FH1', {})
            campos_def = fh1_spec.get('campos', [])
            
            for campo_def in campos_def:
                definicao = campo_def.get('definicao', '')
                campo = CampoSpec.from_definicao(definicao)
                if campo:
                    self.campos.append(campo)
    
    def criar_ficha_habilitacao(self, contrato_data: Dict[str, Any]) -> str:
        """
        Cria uma ficha FH1 a partir dos dados de um contrato
        
        Args:
            contrato_data: Dicionário com dados do contrato
        
        Returns:
            String formatada da ficha FH1
        """
        dados_ficha = {
            'UFS': contrato_data.get('uf', ''),
            'MAT. AG. FINANC. /DV': contrato_data.get('matricula_agente', ''),
            'N.º CONTRATO DO MUT. NO AGENTE': contrato_data.get('numero_contrato', ''),
            'NOME DO MUT. PRINCIPAL': contrato_data.get('nome_mutuario', ''),
            'CPF/CI': contrato_data.get('cpf', ''),
            'DATA DE NASCIMENTO': contrato_data.get('data_nascimento', ''),
            'CODIGO DO MUNICÍPIO': contrato_data.get('codigo_municipio', ''),
            'UF': contrato_data.get('uf_imovel', ''),
            'ENDEREÇO DO IMÓVEL': contrato_data.get('endereco_imovel', ''),
            'DATA DO CONTRATO': contrato_data.get('data_contrato', ''),
            'VALOR FINANCIAMENTO CONTRATADO': contrato_data.get('valor_financiamento', 0),
            'PRAZO CONTRATADO': contrato_data.get('prazo_meses', 0),
            # ... outros campos
        }
        
        self.dados = dados_ficha
        return self.escrever_linha(dados_ficha)


class FH2Parser(FichaParser):
    """Parser para Ficha FH2 - Alteração de contrato (fallback legado VS651)."""

    def _carregar_especificacao(self):
        json_path = Path(__file__).parent.parent / 'cef_conhecimento_completo.json'

        if json_path.exists():
            with open(json_path, 'r', encoding='utf-8') as f:
                conhecimento = json.load(f)

            fh2_spec = conhecimento.get('fichas_envio', {}).get('FH2', {})
            campos_def = fh2_spec.get('campos', [])

            for campo_def in campos_def:
                definicao = campo_def.get('definicao', '') if isinstance(campo_def, dict) else str(campo_def)
                campo = CampoSpec.from_definicao(definicao)
                if campo:
                    self.campos.append(campo)

        if not self.campos:
            self.campos = _carregar_campos_legado('FH2')
            self.layout_source = 'legado_vs651'


class FH3Parser(FichaParser):
    """Parser para Ficha FH3 - Alterações (25 campos)"""
    
    def _carregar_especificacao(self):
        """Carrega os 25 campos da FH3"""
        json_path = Path(__file__).parent.parent / 'cef_conhecimento_completo.json'
        
        if json_path.exists():
            with open(json_path, 'r', encoding='utf-8') as f:
                conhecimento = json.load(f)
                
            fh3_spec = conhecimento.get('fichas_envio', {}).get('FH3', {})
            campos_def = fh3_spec.get('campos', [])
            
            for campo_def in campos_def:
                definicao = campo_def.get('definicao', '')
                campo = CampoSpec.from_definicao(definicao)
                if campo:
                    self.campos.append(campo)


class RNVParser(FichaParser):
    """Parser para Ficha RNV - Registro (5 campos)"""
    
    def _carregar_especificacao(self):
        """Carrega os 5 campos da RNV"""
        json_path = Path(__file__).parent.parent / 'cef_conhecimento_completo.json'
        
        if json_path.exists():
            with open(json_path, 'r', encoding='utf-8') as f:
                conhecimento = json.load(f)
                
            rnv_spec = conhecimento.get('fichas_envio', {}).get('RNV', {})
            campos_def = rnv_spec.get('campos', [])
            
            for campo_def in campos_def:
                definicao = campo_def.get('definicao', '')
                campo = CampoSpec.from_definicao(definicao)
                if campo:
                    self.campos.append(campo)


class RCVParser(FichaParser):
    """Parser para Ficha RCV - fallback legado VS651 quando spec JSON estiver vazia."""

    def _carregar_especificacao(self):
        json_path = Path(__file__).parent.parent / 'cef_conhecimento_completo.json'

        if json_path.exists():
            with open(json_path, 'r', encoding='utf-8') as f:
                conhecimento = json.load(f)

            rcv_spec = conhecimento.get('fichas_envio', {}).get('RCV', {})
            campos_def = rcv_spec.get('campos', [])

            for campo_def in campos_def:
                definicao = campo_def.get('definicao', '') if isinstance(campo_def, dict) else str(campo_def)
                campo = CampoSpec.from_definicao(definicao)
                if campo:
                    self.campos.append(campo)

        if not self.campos:
            self.campos = _carregar_campos_legado('RCV')
            self.layout_source = 'legado_vs651'


class RCNPParser(FichaParser):
    """Parser para Ficha RCNP - schema legado VS651 (LOTERCNP)."""

    def _carregar_especificacao(self):
        # Ainda não há spec oficial consolidada no JSON; usa layout legado.
        self.campos = _carregar_campos_legado('RCNP')
        self.layout_source = 'legado_vs651'


class CADMUTParser(FichaParser):
    """Parser para Ficha CADMUT - Cadastro de Mutuários (617 campos)"""
    
    TAMANHO_REGISTRO = 650  # CADMUT tem tamanho diferente
    
    def _carregar_especificacao(self):
        """Carrega os 617 campos do CADMUT"""
        json_path = Path(__file__).parent.parent / 'cef_conhecimento_completo.json'
        
        if json_path.exists():
            with open(json_path, 'r', encoding='utf-8') as f:
                conhecimento = json.load(f)
                
            cadmut_spec = conhecimento.get('fichas_envio', {}).get('CADMUT', {})
            campos_def = cadmut_spec.get('campos', [])
            
            for campo_def in campos_def:
                # Campos CADMUT estão como strings diretas, não dicionários
                if isinstance(campo_def, str):
                    definicao = campo_def
                else:
                    definicao = campo_def.get('definicao', '')
                
                campo = CampoSpec.from_definicao(definicao)
                if campo:
                    self.campos.append(campo)
    
    def criar_cadastro_mutuario(self, mutuario_data: Dict[str, Any]) -> str:
        """
        Cria uma ficha CADMUT a partir dos dados de um mutuário
        
        Args:
            mutuario_data: Dicionário com dados do mutuário
        
        Returns:
            String formatada da ficha CADMUT
        """
        dados_ficha = {
            'CPF': mutuario_data.get('cpf', ''),
            'NOME': mutuario_data.get('nome', ''),
            'DATA_NASCIMENTO': mutuario_data.get('data_nascimento', ''),
            'ENDERECO': mutuario_data.get('endereco', ''),
            'MUNICIPIO': mutuario_data.get('municipio', ''),
            'UF': mutuario_data.get('uf', ''),
            # ... outros campos
        }
        
        self.dados = dados_ficha
        return self.escrever_linha(dados_ficha)


class ArquivoFichasCEF:
    """
    Gerenciador de arquivos de fichas CEF
    
    Lê e escreve arquivos .txt contendo múltiplas fichas
    """
    
    def __init__(self, tipo_ficha: str = 'FH1'):
        self.tipo_ficha = tipo_ficha
        self.parser = self._obter_parser(tipo_ficha)
        self.fichas: List[Dict[str, Any]] = []
    
    def _obter_parser(self, tipo: str) -> FichaParser:
        """Retorna o parser apropriado para o tipo de ficha"""
        parsers = {
            'FH1': FH1Parser,
            'FH2': FH2Parser,
            'FH3': FH3Parser,
            'RNV': RNVParser,
            'RCV': RCVParser,
            'RCNP': RCNPParser,
            'CADMUT': CADMUTParser,
        }
        
        parser_class = parsers.get(tipo, FH1Parser)
        return parser_class()
    
    def ler_arquivo(self, caminho: str) -> List[Dict[str, Any]]:
        """
        Lê arquivo de fichas e retorna lista de dicionários
        
        Args:
            caminho: Caminho para o arquivo .txt
        
        Returns:
            Lista de dicionários com dados das fichas
        """
        self.fichas = []
        
        with open(caminho, 'r', encoding='latin-1') as f:
            for linha in f:
                if linha.strip():
                    dados = self.parser.ler_linha(linha)
                    self.fichas.append(dados)
        
        return self.fichas
    
    def escrever_arquivo(self, caminho: str, fichas: List[Dict[str, Any]]):
        """
        Escreve lista de fichas em arquivo .txt
        
        Args:
            caminho: Caminho para o arquivo de saída
            fichas: Lista de dicionários com dados das fichas
        """
        with open(caminho, 'w', encoding='latin-1') as f:
            for ficha_dados in fichas:
                linha = self.parser.escrever_linha(ficha_dados)
                f.write(linha + '\n')
    
    def validar_todas(self) -> Dict[int, List[str]]:
        """
        Valida todas as fichas carregadas
        
        Returns:
            Dicionário {numero_linha: [erros]}
        """
        erros_por_linha = {}
        
        for i, ficha in enumerate(self.fichas):
            self.parser.dados = ficha
            erros = self.parser.validar()
            if erros:
                erros_por_linha[i+1] = erros
        
        return erros_por_linha


# Funções auxiliares de alto nível

def criar_fh1_de_contrato(contrato) -> str:
    """
    Cria ficha FH1 a partir de um objeto Contrato do Django
    
    Args:
        contrato: Instância do model Contrato
    
    Returns:
        String da ficha FH1 formatada
    """
    parser = FH1Parser()
    
    dados = {
        'numero_contrato': contrato.numero_contrato,
        'nome_mutuario': contrato.mutuario.nome if hasattr(contrato, 'mutuario') else '',
        'cpf': contrato.mutuario.cpf if hasattr(contrato, 'mutuario') else '',
        'valor_financiamento': contrato.valor_financiado,
        'data_contrato': contrato.data_contrato.strftime('%d%m%y') if contrato.data_contrato else '',
        # ... mais campos
    }
    
    return parser.criar_ficha_habilitacao(dados)


def criar_cadmut_de_mutuario(mutuario) -> str:
    """
    Cria ficha CADMUT a partir de um objeto Mutuario do Django
    
    Args:
        mutuario: Instância do model Mutuario
    
    Returns:
        String da ficha CADMUT formatada
    """
    parser = CADMUTParser()
    
    dados = {
        'cpf': mutuario.cpf,
        'nome': mutuario.nome,
        'data_nascimento': mutuario.data_nascimento.strftime('%d%m%y') if mutuario.data_nascimento else '',
        # ... mais campos
    }
    
    return parser.criar_cadastro_mutuario(dados)


def validar_arquivo_cef(caminho: str, tipo_ficha: str = 'FH1') -> tuple:
    """
    Valida um arquivo de fichas CEF
    
    Args:
        caminho: Caminho para o arquivo
        tipo_ficha: Tipo da ficha (FH1, FH2, FH3, RNV, RCV, RCNP, CADMUT)
    
    Returns:
        Tupla (válido: bool, erros: Dict)
    """
    arquivo = ArquivoFichasCEF(tipo_ficha)
    arquivo.ler_arquivo(caminho)
    erros = arquivo.validar_todas()
    
    return (len(erros) == 0, erros)


# Exemplo de uso
if __name__ == '__main__':
    print("🔧 Parsers de Fichas CEF")
    print("=" * 60)
    
    # Teste FH1
    print("\n📄 Testando parser FH1...")
    parser_fh1 = FH1Parser()
    print(f"   ✅ FH1: {len(parser_fh1.campos)} campos carregados")
    
    # Teste FH3
    print("\n📄 Testando parser FH3...")
    parser_fh3 = FH3Parser()
    print(f"   ✅ FH3: {len(parser_fh3.campos)} campos carregados")

    # Teste FH2
    print("\n📄 Testando parser FH2...")
    parser_fh2 = FH2Parser()
    print(f"   ✅ FH2: {len(parser_fh2.campos)} campos carregados")
    
    # Teste RNV
    print("\n📄 Testando parser RNV...")
    parser_rnv = RNVParser()
    print(f"   ✅ RNV: {len(parser_rnv.campos)} campos carregados")

    # Teste RCV
    print("\n📄 Testando parser RCV...")
    parser_rcv = RCVParser()
    print(f"   ✅ RCV: {len(parser_rcv.campos)} campos carregados")

    # Teste RCNP
    print("\n📄 Testando parser RCNP...")
    parser_rcnp = RCNPParser()
    print(f"   ✅ RCNP: {len(parser_rcnp.campos)} campos carregados")
    
    # Teste CADMUT
    print("\n📄 Testando parser CADMUT...")
    parser_cadmut = CADMUTParser()
    print(f"   ✅ CADMUT: {len(parser_cadmut.campos)} campos carregados")
    
    print(f"\n✅ Total de parsers: 7 tipos de fichas")
    print(
        "✅ Total de campos mapeados: "
        f"{len(parser_fh1.campos) + len(parser_fh2.campos) + len(parser_fh3.campos) + len(parser_rnv.campos) + len(parser_rcv.campos) + len(parser_rcnp.campos) + len(parser_cadmut.campos)}"
    )
