"""
Parser para arquivo P3026 - Posição da Carteira Homologada CEF
Arquivo de retorno que detalha a situação de cada contrato na carteira FCVS

Estrutura do arquivo P3026:
- HEADER: Informações do arquivo
- REGISTROS: Detalhes de cada contrato
- TRAILER: Totalizadores

Referência: Manual SIWFC - Arquivo de Posição da Carteira
"""

from typing import List, Dict, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class TipoRegistroP3026(Enum):
    """Tipos de registro no arquivo P3026"""
    HEADER = '0'
    REGISTRO = '1'
    TRAILER = '9'


class SituacaoContrato(Enum):
    """Situações possíveis de um contrato na carteira"""
    HABILITADO = 'H'
    PENDENTE = 'P'
    REJEITADO = 'R'
    CANCELADO = 'C'
    QUITADO = 'Q'
    SUSPENSO = 'S'
    ANALISE = 'A'


@dataclass
class HeaderP3026:
    """
    HEADER do arquivo P3026 (Tipo '0')
    Contém informações gerais do arquivo
    """
    tipo_registro: str  # '0'
    codigo_agente: str  # Código do agente financeiro
    data_geracao: datetime  # Data de geração do arquivo
    hora_geracao: str  # Hora de geração (HHMMSS)
    sequencial_arquivo: str  # Número sequencial do arquivo
    nome_arquivo: str  # Nome do arquivo
    versao: str  # Versão do layout
    
    @classmethod
    def from_linha(cls, linha: str) -> 'HeaderP3026':
        """
        Parse do HEADER a partir da linha
        
        Layout (150 posições):
        001-001: Tipo registro ('0')
        002-009: Código agente
        010-017: Data geração (DDMMAAAA)
        018-023: Hora geração (HHMMSS)
        024-031: Sequencial
        032-100: Nome arquivo
        101-150: Versão/Reserva
        """
        return cls(
            tipo_registro=linha[0:1].strip(),
            codigo_agente=linha[1:9].strip(),
            data_geracao=datetime.strptime(linha[9:17].strip(), '%d%m%Y'),
            hora_geracao=linha[17:23].strip(),
            sequencial_arquivo=linha[23:31].strip(),
            nome_arquivo=linha[31:100].strip(),
            versao=linha[100:150].strip()
        )


@dataclass
class RegistroContratoP3026:
    """
    REGISTRO de contrato TR1 (Tipo '1') - P3026 Completo
    Arquivo de Posição da Carteira Homologada CEF
    
    Total: 31 campos (posições 1-500)
    Especificação: Leiaute_FCVS3026_TR1_a_TR9_270417.xls
    """
    # Campo 01: Tipo de registro
    tipo_registro: str  # '1'
    
    # Campos 02-04: Agentes
    matricula_agente: str  # Campo 02 [002-006] - Matrícula do agente
    agente_cessionario: str  # Campo 03 [007-011] - Agente cessionário
    agente_cedente: str  # Campo 04 [012-016] - Agente cedente
    
    # Campo 05-06: Identificação do contrato
    numero_contrato: str  # Campo 05 [017-029] - Número do contrato (13)
    grau_hipoteca: int  # Campo 06 [030-030] - Grau de hipoteca (1=primeira, 2=segunda)
    
    # Campos 07-08: Identificação do mutuário
    nome_mutuario: str  # Campo 07 [031-070] - Nome do mutuário (40)
    cpf: str  # Campo 08 [071-081] - CPF (11)
    
    # Campo 09: Data do contrato
    data_assinatura_contrato: datetime  # Campo 09 [082-089] - DDMMAAAA
    
    # Campos 10-12: Localização do imóvel
    endereco_imovel: str  # Campo 10 [090-129] - Endereço do imóvel (40)
    codigo_municipio: str  # Campo 11 [130-134] - Código município (5)
    nome_municipio: str  # Campo 12 [135-144] - Nome município (10)
    
    # Campos 13-14: Informações financeiras básicas
    origem_recurso: str  # Campo 13 [145-146] - Origem de recurso (2)
    im: str  # Campo 14 [147-148] - IM (2)
    
    # Campos 15-16: Taxas de juros
    taxa_juros_contratual: str  # Campo 15 [149-154] - Taxa juros contratual (6)
    taxa_juros_evento: str  # Campo 16 [155-160] - Taxa juros no evento (6)
    
    # Campos 17-18: Situação do contrato
    codigo_situacao_contrato: str  # Campo 17 [161-162] - Código situação (2)
    descricao_situacao_contrato: str  # Campo 18 [163-232] - Descrição situação (70)
    
    # Campos 19-20: Evento
    tipo_evento: str  # Campo 19 [233-235] - Tipo de evento (3)
    data_evento: datetime  # Campo 20 [236-243] - Data evento DDMMAAAA
    
    # Campos 21-23: VAF informado pelo agente
    vaf1_informado_agente: float  # Campo 21 [244-257] - VAF 1 (14)
    vaf2_informado_agente: float  # Campo 22 [258-271] - VAF 2 (14)
    vaf3_informado_agente: float  # Campo 23 [272-285] - VAF 3 (14)
    
    # Campo 24: Data habilitação
    data_habilitacao: datetime  # Campo 24 [286-293] - DDMMAAAA
    
    # Campo 25: Documentação
    documentacao: int  # Campo 25 [294-294] - 0=Não entregue, 1=Entregue
    
    # Campos 26-28: Datas de processamento
    data_processamento_habilitacao: datetime  # Campo 26 [295-302] - DDMMAAAA
    data_entrega_agente: datetime  # Campo 27 [303-310] - Data entrega ao AF
    data_prazo_agente: datetime  # Campo 28 [311-318] - Data prazo agente
    
    # Campo 29: Situação de análise
    situacao_analise_atual: int  # Campo 29 [319-319] - 0/1/2/3
    
    # Campo 30: Negociação/Transferência
    data_negociacao_transferencia: datetime  # Campo 30 [320-327] - Última marcação
    
    # Campo 31: Vago/Reserva
    campo_vago: str  # Campo 31 [328-500] - Reservado (173)
    
    @classmethod
    def from_linha(cls, linha: str) -> 'RegistroContratoP3026':
        """
        Parse do REGISTRO TR1 a partir da linha (500 posições)
        
        Especificação completa com 31 campos conforme layout oficial CEF
        """
        def parse_date(date_str: str) -> datetime:
            """Parse data DDMMAAAA, retorna None se inválida"""
            if not date_str or date_str.strip() in ('', '00000000', ' ' * 8):
                return None
            try:
                return datetime.strptime(date_str.strip(), '%d%m%Y')
            except:
                return None
        
        def parse_decimal(value_str: str, decimals: int = 2) -> float:
            """
            Parse valor decimal
            Formato CEF: valor com decimais implícitos
            Ex: "00000012345" com decimals=2 -> 123.45
            """
            try:
                value_str = value_str.strip()
                if not value_str or value_str == '0' * len(value_str):
                    return 0.0
                # Remove zeros à esquerda e converte
                value_int = int(value_str)
                return value_int / (10 ** decimals)
            except:
                return 0.0
        
        def parse_int(int_str: str) -> int:
            """Parse inteiro, retorna 0 se inválido"""
            try:
                return int(int_str.strip()) if int_str.strip() else 0
            except:
                return 0
        
        # Garante que a linha tenha 500 posições
        linha = linha.ljust(500)
        
        return cls(
            # Campo 01 [001-001]
            tipo_registro=linha[0:1].strip(),
            
            # Campos 02-04 [002-016] - Agentes
            matricula_agente=linha[1:6].strip(),
            agente_cessionario=linha[6:11].strip(),
            agente_cedente=linha[11:16].strip(),
            
            # Campos 05-06 [017-030] - Identificação contrato
            numero_contrato=linha[16:29].strip(),
            grau_hipoteca=parse_int(linha[29:30]),
            
            # Campos 07-08 [031-081] - Mutuário
            nome_mutuario=linha[30:70].strip(),
            cpf=linha[70:81].strip(),
            
            # Campo 09 [082-089] - Data contrato
            data_assinatura_contrato=parse_date(linha[81:89]),
            
            # Campos 10-12 [090-144] - Localização
            endereco_imovel=linha[89:129].strip(),
            codigo_municipio=linha[129:134].strip(),
            nome_municipio=linha[134:144].strip(),
            
            # Campos 13-14 [145-148] - Financeiras básicas
            origem_recurso=linha[144:146].strip(),
            im=linha[146:148].strip(),
            
            # Campos 15-16 [149-160] - Taxas de juros
            taxa_juros_contratual=linha[148:154].strip(),
            taxa_juros_evento=linha[154:160].strip(),
            
            # Campos 17-18 [161-232] - Situação
            codigo_situacao_contrato=linha[160:162].strip(),
            descricao_situacao_contrato=linha[162:232].strip(),
            
            # Campos 19-20 [233-243] - Evento
            tipo_evento=linha[232:235].strip(),
            data_evento=parse_date(linha[235:243]),
            
            # Campos 21-23 [244-285] - VAF informado pelo agente
            vaf1_informado_agente=parse_decimal(linha[243:257]),
            vaf2_informado_agente=parse_decimal(linha[257:271]),
            vaf3_informado_agente=parse_decimal(linha[271:285]),
            
            # Campo 24 [286-293] - Data habilitação
            data_habilitacao=parse_date(linha[285:293]),
            
            # Campo 25 [294-294] - Documentação
            documentacao=parse_int(linha[293:294]),
            
            # Campos 26-28 [295-318] - Datas processamento
            data_processamento_habilitacao=parse_date(linha[294:302]),
            data_entrega_agente=parse_date(linha[302:310]),
            data_prazo_agente=parse_date(linha[310:318]),
            
            # Campo 29 [319-319] - Situação análise
            situacao_analise_atual=parse_int(linha[318:319]),
            
            # Campo 30 [320-327] - Negociação
            data_negociacao_transferencia=parse_date(linha[319:327]),
            
            # Campo 31 [328-500] - Vago
            campo_vago=linha[327:500].strip()
        )


@dataclass
class TrailerP3026:
    """
    TRAILER do arquivo P3026 (Tipo '9')
    Totalizadores do arquivo
    """
    tipo_registro: str  # '9'
    total_registros: int  # Total de registros de contratos
    total_habilitados: int  # Total com situação HABILITADO
    total_pendentes: int  # Total PENDENTE
    total_rejeitados: int  # Total REJEITADO
    valor_total_fcvs: float  # Somatório valor FCVS
    saldo_total_devedor: float  # Somatório saldo devedor
    
    @classmethod
    def from_linha(cls, linha: str) -> 'TrailerP3026':
        """
        Parse do TRAILER a partir da linha
        
        Layout (150 posições):
        001-001: Tipo registro ('9')
        002-011: Total registros (10N)
        012-021: Total habilitados (10N)
        022-031: Total pendentes (10N)
        032-041: Total rejeitados (10N)
        042-056: Valor total FCVS (15,2)
        057-071: Saldo total devedor (15,2)
        072-150: Reserva
        """
        def parse_decimal(value_str: str, decimals: int = 2) -> float:
            try:
                return float(value_str.strip()) / (10 ** decimals)
            except:
                return 0.0
        
        return cls(
            tipo_registro=linha[0:1].strip(),
            total_registros=int(linha[1:11].strip() or '0'),
            total_habilitados=int(linha[11:21].strip() or '0'),
            total_pendentes=int(linha[21:31].strip() or '0'),
            total_rejeitados=int(linha[31:41].strip() or '0'),
            valor_total_fcvs=parse_decimal(linha[41:56]),
            saldo_total_devedor=parse_decimal(linha[56:71])
        )


@dataclass
class ArquivoP3026:
    """Arquivo P3026 completo"""
    header: HeaderP3026
    registros: List[RegistroContratoP3026]
    trailer: TrailerP3026
    
    @property
    def total_contratos(self) -> int:
        return len(self.registros)
    
    @property
    def contratos_por_situacao(self) -> Dict[str, int]:
        """Agrupa contratos por código de situação"""
        contagem = {}
        for registro in self.registros:
            # Usando codigo_situacao_contrato (str) ao invés do enum
            situacao = registro.codigo_situacao_contrato or 'SEM_CODIGO'
            contagem[situacao] = contagem.get(situacao, 0) + 1
        return contagem
    
    def filtrar_por_situacao(self, codigo_situacao: str) -> List[RegistroContratoP3026]:
        """
        Retorna apenas contratos com determinado código de situação
        
        Args:
            codigo_situacao: Código da situação (ex: '02' para habilitado)
        """
        return [r for r in self.registros if r.codigo_situacao_contrato == codigo_situacao]
    
    def buscar_por_contrato(self, numero_contrato: str) -> RegistroContratoP3026:
        """Busca um contrato específico pelo número"""
        for registro in self.registros:
            if registro.numero_contrato == numero_contrato:
                return registro
        return None
    
    def gerar_relatorio(self) -> Dict:
        """Gera relatório resumido"""
        return {
            'data_geracao': self.header.data_geracao,
            'total_contratos': self.total_contratos,
            'por_situacao': self.contratos_por_situacao,
            'totalizadores': {
                'registros': self.trailer.total_registros,
                'habilitados': self.trailer.total_habilitados,
                'pendentes': self.trailer.total_pendentes,
                'rejeitados': self.trailer.total_rejeitados,
                'valor_fcvs': self.trailer.valor_total_fcvs,
                'saldo_devedor': self.trailer.saldo_total_devedor
            }
        }


class ParserP3026:
    """Parser para arquivos P3026"""
    
    @staticmethod
    def parse_arquivo(caminho: str, encoding: str = 'latin-1') -> Tuple[ArquivoP3026, List[str]]:
        """
        Lê e faz parse de arquivo P3026
        
        Args:
            caminho: Caminho do arquivo
            encoding: Encoding (padrão latin-1 para CEF)
        
        Returns:
            Tuple (ArquivoP3026, lista de erros)
        """
        erros = []
        header = None
        registros = []
        trailer = None
        
        try:
            with open(caminho, 'r', encoding=encoding) as f:
                for num_linha, linha in enumerate(f, 1):
                    linha = linha.rstrip('\r\n')
                    
                    if not linha:
                        continue
                    
                    tipo = linha[0:1]
                    
                    try:
                        if tipo == '0':  # HEADER
                            header = HeaderP3026.from_linha(linha)
                        
                        elif tipo == '1':  # REGISTRO
                            registro = RegistroContratoP3026.from_linha(linha)
                            registros.append(registro)
                        
                        elif tipo == '9':  # TRAILER
                            trailer = TrailerP3026.from_linha(linha)
                        
                        else:
                            erros.append(f"Linha {num_linha}: Tipo de registro desconhecido '{tipo}'")
                    
                    except Exception as e:
                        erros.append(f"Linha {num_linha}: Erro ao processar - {str(e)}")
            
            # Validações
            if not header:
                erros.append("HEADER não encontrado")
            
            if not trailer:
                erros.append("TRAILER não encontrado")
            
            if header and trailer:
                if len(registros) != trailer.total_registros:
                    erros.append(
                        f"Inconsistência: {len(registros)} registros lidos, "
                        f"mas TRAILER indica {trailer.total_registros}"
                    )
            
            if header and trailer:
                arquivo = ArquivoP3026(
                    header=header,
                    registros=registros,
                    trailer=trailer
                )
                return arquivo, erros
            else:
                return None, erros
        
        except Exception as e:
            erros.append(f"Erro ao ler arquivo: {str(e)}")
            return None, erros

# ============================================================================
# CLASSES PARA OUTROS TIPOS DE REGISTRO (TR2-TR9)
# ============================================================================

@dataclass
class RegistroTR2:
    """
    TR2 - Contratos com Responsabilidade Parcial
    Total: 76 campos
    
    Estrutura mais complexa com informações adicionais de responsabilidade
    e garantias. A implementação completa requer todos os 76 campos.
    """
    tipo_registro: str = '2'
    # TODO: Implementar 76 campos conforme especificação
    dados_brutos: str = ''  # Temporário: armazena linha completa
    
    @classmethod
    def from_linha(cls, linha: str) -> 'RegistroTR2':
        """Parse básico do TR2 - implementação completa pendente"""
        return cls(
            tipo_registro=linha[0:1].strip(),
            dados_brutos=linha
        )


@dataclass
class RegistroTR3:
    """
    TR3 - Tipo de Registro 3
    Total: 71 campos
    """
    tipo_registro: str = '3'
    dados_brutos: str = ''
    
    @classmethod
    def from_linha(cls, linha: str) -> 'RegistroTR3':
        """Parse básico do TR3 - implementação completa pendente"""
        return cls(
            tipo_registro=linha[0:1].strip(),
            dados_brutos=linha
        )


@dataclass
class RegistroTR4:
    """
    TR4 - Tipo de Registro 4
    Total: 90 campos (LAYOUT MAIS COMPLEXO)
    """
    tipo_registro: str = '4'
    dados_brutos: str = ''
    
    @classmethod
    def from_linha(cls, linha: str) -> 'RegistroTR4':
        """Parse básico do TR4 - implementação completa pendente"""
        return cls(
            tipo_registro=linha[0:1].strip(),
            dados_brutos=linha
        )


@dataclass
class RegistroTR5:
    """
    TR5 - Tipo de Registro 5
    Total: 50 campos
    """
    tipo_registro: str = '5'
    dados_brutos: str = ''
    
    @classmethod
    def from_linha(cls, linha: str) -> 'RegistroTR5':
        """Parse básico do TR5 - implementação completa pendente"""
        return cls(
            tipo_registro=linha[0:1].strip(),
            dados_brutos=linha
        )


@dataclass
class RegistroTR6:
    """
    TR6 - Tipo de Registro 6
    Total: 46 campos
    """
    tipo_registro: str = '6'
    dados_brutos: str = ''
    
    @classmethod
    def from_linha(cls, linha: str) -> 'RegistroTR6':
        """Parse básico do TR6 - implementação completa pendente"""
        return cls(
            tipo_registro=linha[0:1].strip(),
            dados_brutos=linha
        )


@dataclass
class RegistroTR7:
    """
    TR7 - Tipo de Registro 7
    Total: 66 campos
    """
    tipo_registro: str = '7'
    dados_brutos: str = ''
    
    @classmethod
    def from_linha(cls, linha: str) -> 'RegistroTR7':
        """Parse básico do TR7 - implementação completa pendente"""
        return cls(
            tipo_registro=linha[0:1].strip(),
            dados_brutos=linha
        )


@dataclass
class RegistroTR8:
    """
    TR8 - Tipo de Registro 8
    Total: 62 campos
    """
    tipo_registro: str = '8'
    dados_brutos: str = ''
    
    @classmethod
    def from_linha(cls, linha: str) -> 'RegistroTR8':
        """Parse básico do TR8 - implementação completa pendente"""
        return cls(
            tipo_registro=linha[0:1].strip(),
            dados_brutos=linha
        )


@dataclass
class RegistroTR9:
    """
    TR9 - Tipo de Registro 9
    Total: 47 campos
    """
    tipo_registro: str = '9'
    dados_brutos: str = ''
    
    @classmethod
    def from_linha(cls, linha: str) -> 'RegistroTR9':
        """Parse básico do TR9 - implementação completa pendente"""
        return cls(
            tipo_registro=linha[0:1].strip(),
            dados_brutos=linha
        )


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def interpretar_p3026(caminho_arquivo: str) -> Dict:
    """
    Interpreta arquivo P3026 e retorna relatório completo
    
    Args:
        caminho_arquivo: Caminho do arquivo P3026
    
    Returns:
        Dicionário com análise completa
    """
    parser = ParserP3026()
    arquivo, erros = parser.parse_arquivo(caminho_arquivo)
    
    if not arquivo:
        return {
            'sucesso': False,
            'erros': erros,
            'mensagem': 'Erro ao processar arquivo P3026'
        }
    
    # Análise detalhada
    # Nota: SituacaoContrato enum não é mais usado - agora temos codigo_situacao_contrato (str)
    # Filtros aproximados: '02' = habilitado, outros = pendente/rejeitado
    habilitados = [r for r in arquivo.registros if r.codigo_situacao_contrato == '02']
    pendentes = [r for r in arquivo.registros if r.codigo_situacao_contrato not in ['02', '03']]
    rejeitados = [r for r in arquivo.registros if r.codigo_situacao_contrato == '03']
    
    # Valores VAF (soma dos 3 VAFs informados pelo agente)
    valor_total_habilitado = sum(
        r.vaf1_informado_agente + r.vaf2_informado_agente + r.vaf3_informado_agente
        for r in habilitados
    )
    
    return {
        'sucesso': True,
        'erros': erros,
        'arquivo': {
            'nome': arquivo.header.nome_arquivo,
            'data_geracao': arquivo.header.data_geracao,
            'hora_geracao': arquivo.header.hora_geracao,
            'codigo_agente': arquivo.header.codigo_agente
        },
        'resumo': {
            'total_contratos': arquivo.total_contratos,
            'habilitados': len(habilitados),
            'pendentes': len(pendentes),
            'rejeitados': len(rejeitados)
        },
        'valores': {
            'valor_fcvs_habilitado': valor_total_habilitado,
            # Nota: saldo_devedor e trailer fields não estão no novo spec TR1
            # Mantemos estrutura para compatibilidade mas valores podem estar zerados
            'saldo_devedor_habilitado': 0,
            'valor_fcvs_total': getattr(arquivo.trailer, 'valor_total_fcvs', 0) if arquivo.trailer else 0,
            'saldo_devedor_total': getattr(arquivo.trailer, 'saldo_total_devedor', 0) if arquivo.trailer else 0
        },
        'contratos_habilitados': [
            {
                'codigo': r.numero_contrato,  # Novo nome
                'cpf': r.cpf,  # Novo nome
                'nome': r.nome_mutuario,
                'valor_fcvs': r.vaf1_informado_agente + r.vaf2_informado_agente + r.vaf3_informado_agente,  # Soma dos VAFs
                'data_habilitacao': r.data_habilitacao,
                'data_assinatura': r.data_assinatura_contrato,  # Novo campo
                'situacao': r.descricao_situacao_contrato,  # Novo campo
                'codigo_situacao': r.codigo_situacao_contrato  # Novo campo
            }
            for r in habilitados[:10]  # Primeiros 10
        ],
        'contratos_rejeitados': [
            {
                'codigo': r.numero_contrato,  # Novo nome
                'nome': r.nome_mutuario,
                'situacao': r.descricao_situacao_contrato,  # Novo campo
                'codigo_situacao': r.codigo_situacao_contrato,  # Novo campo
                'data_evento': r.data_evento  # Novo campo
            }
            for r in rejeitados[:10]  # Primeiros 10
        ],
        'contratos_pendentes': [
            {
                'codigo': r.numero_contrato,  # Novo nome
                'nome': r.nome_mutuario,
                'situacao': r.descricao_situacao_contrato,  # Novo campo
                'codigo_situacao': r.codigo_situacao_contrato,  # Novo campo
                'data_evento': r.data_evento,  # Substituindo data_situacao
                'situacao_analise': r.situacao_analise_atual  # Novo campo: 0/1/2/3
            }
            for r in pendentes[:10]  # Primeiros 10
        ]
    }


# Teste
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python ficha_p3026_parser.py <caminho_arquivo_p3026>")
        sys.exit(1)
    
    caminho = sys.argv[1]
    resultado = interpretar_p3026(caminho)
    
    if resultado['sucesso']:
        print("✅ Arquivo P3026 processado com sucesso!")
        print(f"\n📊 RESUMO:")
        print(f"   Data geração: {resultado['arquivo']['data_geracao']}")
        print(f"   Total contratos: {resultado['resumo']['total_contratos']}")
        print(f"   Habilitados: {resultado['resumo']['habilitados']}")
        print(f"   Pendentes: {resultado['resumo']['pendentes']}")
        print(f"   Rejeitados: {resultado['resumo']['rejeitados']}")
        print(f"\n💰 VALORES:")
        print(f"   FCVS habilitado: R$ {resultado['valores']['valor_fcvs_habilitado']:,.2f}")
        print(f"   Saldo devedor: R$ {resultado['valores']['saldo_devedor_habilitado']:,.2f}")
    else:
        print("❌ Erro ao processar arquivo:")
        for erro in resultado['erros']:
            print(f"   - {erro}")
