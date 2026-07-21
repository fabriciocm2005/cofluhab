"""
Parser para arquivos M460xxx da CEF
Processa arquivos de irregularidades CADMUT:
- M460301: Acumulativo
- M460401: Inclusões no Mês  
- M460801: Regularizados sem Manifestação GIFUS
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Tuple
from enum import Enum


class TipoGIFUS(Enum):
    """Códigos GIFUS de análise"""
    GIFUS_SA = '03'  # Salvador
    GIFUS_BR = '04'  # Brasília
    GIFUS_FO = '05'  # Fortaleza
    GIFUS_GO = '08'  # Goiânia
    GIFUS_BH = '11'  # Belo Horizonte
    GIFUS_BE = '12'  # Belém
    GIFUS_CT = '14'  # Curitiba
    GIFUS_RE = '15'  # Recife
    GIFUS_PO = '18'  # Porto Alegre
    GIFUS_RJ = '19'  # Rio de Janeiro
    GIFUS_FL = '20'  # Florianópolis
    GIFUS_SP = '21'  # São Paulo


class SituacaoMultiplicidadeSinistro(Enum):
    """Situações de Multiplicidade e Sinistro"""
    INDICIO_MULTIPLICIDADE = '01'
    INDICIO_SINISTRO_SIT = '02'
    MULTIPLICIDADE_CARACTERIZADA = '03'
    SINISTRO_CARACTERIZADO_SIT = '04'
    INDICIO_SINISTRO_PARCIAL = '06'
    SINISTRO_PARCIAL_CARACTERIZADO = '08'
    INDICIO_SINISTRO_DFI = '10'
    SINISTRO_DFI_CARACTERIZADO = '12'


@dataclass
class RegistroM460301:
    """
    Registro do arquivo M460301 - Contratos Novados com Irregularidade CADMUT (Acumulativo)
    
    Layout de 20 campos:
    1. GIFUS de Análise (Cha 2)
    2. Agente Origem (Num 5)
    3. Agente Cessionário (Num 5)
    4. Agente Cedente (Num 5)
    5. Contrato (Cha 13)
    6. Hipoteca (Num 1)
    7. Data do Contrato (Date DD-MM-AAAA)
    8. Município CADMUT (Num 4)
    9. Data Evento CADMUT (Date DD-MM-AAAA)
    10. Data Posicionamento Novação VA1/VAF2 (Date DD-MM-AAAA)
    11. Valor Saldo VAF1/VA2 Vencido (Num 11v2)
    12. Valor Saldo VAF1/VAF2 Vincendo (Num 11v2)
    13. Data Posicionamento Novação VA3 (Date DD-MM-AAAA)
    14. Valor Saldo VAF3 (Num 11v2)
    15. Data Posicionamento Novação VAF4 (Date DD-MM-AAAA)
    16. Valor Saldo VAF4 (Num 11v2)
    17. Percentual de Cobertura (Num 3v2)
    18. Situação de Multiplicidade e Sinistro (Cha 2)
    19. Apresentação da Contestação (Date DD-MM-AAAA)
    20. Prazo final para Contestação (Date DD-MM-AAAA)
    """
    gifus_analise: str  # Campo 1
    agente_origem: str  # Campo 2
    agente_cessionario: str  # Campo 3
    agente_cedente: str  # Campo 4
    contrato: str  # Campo 5
    hipoteca: int  # Campo 6
    data_contrato: datetime  # Campo 7
    municipio_cadmut: str  # Campo 8
    data_evento_cadmut: datetime  # Campo 9
    data_pos_novacao_va1_vaf2: datetime  # Campo 10
    valor_saldo_vaf1_va2_vencido: Decimal  # Campo 11
    valor_saldo_vaf1_vaf2_vincendo: Decimal  # Campo 12
    data_pos_novacao_va3: datetime  # Campo 13
    valor_saldo_vaf3: Decimal  # Campo 14
    data_pos_novacao_vaf4: datetime  # Campo 15
    valor_saldo_vaf4: Decimal  # Campo 16
    percentual_cobertura: Decimal  # Campo 17
    situacao_mult_sinistro: str  # Campo 18
    data_apresentacao_contestacao: Optional[datetime]  # Campo 19
    data_prazo_final_contestacao: Optional[datetime]  # Campo 20
    
    @property
    def total_saldo_vencido_vincendo(self) -> Decimal:
        """Total de saldo vencido + vincendo"""
        return self.valor_saldo_vaf1_va2_vencido + self.valor_saldo_vaf1_vaf2_vincendo
    
    @property
    def total_todos_vafs(self) -> Decimal:
        """Total de todos os VAFs"""
        return (self.valor_saldo_vaf1_va2_vencido + 
                self.valor_saldo_vaf1_vaf2_vincendo +
                self.valor_saldo_vaf3 + 
                self.valor_saldo_vaf4)
    
    @property
    def tem_contestacao(self) -> bool:
        """Verifica se tem contestação apresentada"""
        return self.data_apresentacao_contestacao is not None
    
    @property
    def contestacao_vencida(self) -> bool:
        """Verifica se o prazo de contestação já venceu"""
        if self.data_prazo_final_contestacao:
            return datetime.now() > self.data_prazo_final_contestacao
        return False


@dataclass
class RegistroM460401:
    """
    Registro do arquivo M460401 - Contratos Novados com Irregularidade CADMUT (Inclusões no Mês)
    
    MESMA ESTRUTURA DO M460301, mas contém apenas os registros adicionados no mês corrente.
    """
    gifus_analise: str
    agente_origem: str
    agente_cessionario: str
    agente_cedente: str
    contrato: str
    hipoteca: int
    data_contrato: datetime
    municipio_cadmut: str
    data_evento_cadmut: datetime
    data_pos_novacao_va1_vaf2: datetime
    valor_saldo_vaf1_va2_vencido: Decimal
    valor_saldo_vaf1_vaf2_vincendo: Decimal
    data_pos_novacao_va3: datetime
    valor_saldo_vaf3: Decimal
    data_pos_novacao_vaf4: datetime
    valor_saldo_vaf4: Decimal
    percentual_cobertura: Decimal
    situacao_mult_sinistro: str
    data_apresentacao_contestacao: Optional[datetime]
    data_prazo_final_contestacao: Optional[datetime]
    
    @property
    def total_todos_vafs(self) -> Decimal:
        """Total de todos os VAFs"""
        return (self.valor_saldo_vaf1_va2_vencido + 
                self.valor_saldo_vaf1_vaf2_vincendo +
                self.valor_saldo_vaf3 + 
                self.valor_saldo_vaf4)


@dataclass
class RegistroM460801:
    """
    Registro do arquivo M460801 - Contratos Novados Regularizados no CADMUT 
    sem Manifestação da GIFUS
    
    Layout de 9 campos (mais simples que M460301/M460401):
    1. GIFUS de Análise (Cha 2)
    2. Agente Origem (Num 5)
    3. Agente Cessionário (Num 5)
    4. Agente Cedente (Num 5)
    5. Contrato (Cha 13)
    6. Hipoteca (Num 1)
    7. Data do Contrato (Date DD-MM-AAAA)
    8. Município CADMUT (Num 4)
    9. Data Evento CADMUT (Date DD-MM-AAAA)
    """
    gifus_analise: str  # Campo 1
    agente_origem: str  # Campo 2
    agente_cessionario: str  # Campo 3
    agente_cedente: str  # Campo 4
    contrato: str  # Campo 5
    hipoteca: int  # Campo 6
    data_contrato: datetime  # Campo 7
    municipio_cadmut: str  # Campo 8
    data_evento_cadmut: datetime  # Campo 9


class ParserM460:
    """Parser genérico para arquivos M460xxx"""
    
    @staticmethod
    def parse_date(date_str: str) -> Optional[datetime]:
        """
        Converte string DD-MM-AAAA para datetime
        Retorna None se a data estiver vazia ou inválida
        """
        if not date_str or date_str.strip() in ('', '00-00-0000', '  -  -    '):
            return None
        
        try:
            # Remove espaços e valida formato
            date_str = date_str.strip()
            if len(date_str) == 10:  # DD-MM-AAAA
                day, month, year = date_str.split('-')
                return datetime(int(year), int(month), int(day))
        except (ValueError, AttributeError):
            pass
        
        return None
    
    @staticmethod
    def parse_decimal(value_str: str, decimais: int = 2) -> Decimal:
        """
        Converte string numérica para Decimal
        Assume formato com casas decimais implícitas
        Ex: "0000012345" com decimais=2 -> 123.45
        """
        if not value_str or value_str.strip() == '':
            return Decimal('0')
        
        try:
            # Remove espaços
            value_str = value_str.strip()
            
            # Converte considerando casas decimais implícitas
            value_int = int(value_str)
            divisor = Decimal(10 ** decimais)
            return Decimal(value_int) / divisor
        except (ValueError, InvalidOperation):
            return Decimal('0')
    
    @staticmethod
    def parse_m460301_line(linha: str) -> RegistroM460301:
        """
        Parse uma linha do arquivo M460301
        
        Tamanho estimado: 176 caracteres
        Formato: campos separados por delimitador (provavelmente pipe | ou tab)
        """
        # TODO: Implementar parsing baseado no delimitador real
        # Por enquanto, assumindo campos separados por pipe
        campos = linha.split('|')
        
        if len(campos) < 20:
            raise ValueError(f"Linha com menos de 20 campos: {len(campos)}")
        
        return RegistroM460301(
            gifus_analise=campos[0].strip(),
            agente_origem=campos[1].strip(),
            agente_cessionario=campos[2].strip(),
            agente_cedente=campos[3].strip(),
            contrato=campos[4].strip(),
            hipoteca=int(campos[5].strip()) if campos[5].strip() else 0,
            data_contrato=ParserM460.parse_date(campos[6]),
            municipio_cadmut=campos[7].strip(),
            data_evento_cadmut=ParserM460.parse_date(campos[8]),
            data_pos_novacao_va1_vaf2=ParserM460.parse_date(campos[9]),
            valor_saldo_vaf1_va2_vencido=ParserM460.parse_decimal(campos[10]),
            valor_saldo_vaf1_vaf2_vincendo=ParserM460.parse_decimal(campos[11]),
            data_pos_novacao_va3=ParserM460.parse_date(campos[12]),
            valor_saldo_vaf3=ParserM460.parse_decimal(campos[13]),
            data_pos_novacao_vaf4=ParserM460.parse_date(campos[14]),
            valor_saldo_vaf4=ParserM460.parse_decimal(campos[15]),
            percentual_cobertura=ParserM460.parse_decimal(campos[16]),
            situacao_mult_sinistro=campos[17].strip(),
            data_apresentacao_contestacao=ParserM460.parse_date(campos[18]),
            data_prazo_final_contestacao=ParserM460.parse_date(campos[19]),
        )
    
    @staticmethod
    def parse_m460401_line(linha: str) -> RegistroM460401:
        """Parse uma linha do arquivo M460401 (mesma estrutura do M460301)"""
        # Usa mesma lógica do M460301
        campos = linha.split('|')
        
        if len(campos) < 20:
            raise ValueError(f"Linha com menos de 20 campos: {len(campos)}")
        
        return RegistroM460401(
            gifus_analise=campos[0].strip(),
            agente_origem=campos[1].strip(),
            agente_cessionario=campos[2].strip(),
            agente_cedente=campos[3].strip(),
            contrato=campos[4].strip(),
            hipoteca=int(campos[5].strip()) if campos[5].strip() else 0,
            data_contrato=ParserM460.parse_date(campos[6]),
            municipio_cadmut=campos[7].strip(),
            data_evento_cadmut=ParserM460.parse_date(campos[8]),
            data_pos_novacao_va1_vaf2=ParserM460.parse_date(campos[9]),
            valor_saldo_vaf1_va2_vencido=ParserM460.parse_decimal(campos[10]),
            valor_saldo_vaf1_vaf2_vincendo=ParserM460.parse_decimal(campos[11]),
            data_pos_novacao_va3=ParserM460.parse_date(campos[12]),
            valor_saldo_vaf3=ParserM460.parse_decimal(campos[13]),
            data_pos_novacao_vaf4=ParserM460.parse_date(campos[14]),
            valor_saldo_vaf4=ParserM460.parse_decimal(campos[15]),
            percentual_cobertura=ParserM460.parse_decimal(campos[16]),
            situacao_mult_sinistro=campos[17].strip(),
            data_apresentacao_contestacao=ParserM460.parse_date(campos[18]),
            data_prazo_final_contestacao=ParserM460.parse_date(campos[19]),
        )
    
    @staticmethod
    def parse_m460801_line(linha: str) -> RegistroM460801:
        """
        Parse uma linha do arquivo M460801
        
        Tamanho estimado: 56 caracteres
        Formato: apenas 9 campos
        """
        campos = linha.split('|')
        
        if len(campos) < 9:
            raise ValueError(f"Linha com menos de 9 campos: {len(campos)}")
        
        return RegistroM460801(
            gifus_analise=campos[0].strip(),
            agente_origem=campos[1].strip(),
            agente_cessionario=campos[2].strip(),
            agente_cedente=campos[3].strip(),
            contrato=campos[4].strip(),
            hipoteca=int(campos[5].strip()) if campos[5].strip() else 0,
            data_contrato=ParserM460.parse_date(campos[6]),
            municipio_cadmut=campos[7].strip(),
            data_evento_cadmut=ParserM460.parse_date(campos[8]),
        )
    
    @staticmethod
    def parse_file_m460301(caminho: str, encoding: str = 'latin-1') -> Tuple[List[RegistroM460301], List[str]]:
        """
        Parse arquivo M460301 completo
        
        Returns:
            Tuple com (lista de registros, lista de erros)
        """
        registros = []
        erros = []
        
        try:
            with open(caminho, 'r', encoding=encoding) as f:
                for num_linha, linha in enumerate(f, 1):
                    linha = linha.strip()
                    if not linha:
                        continue
                    
                    try:
                        registro = ParserM460.parse_m460301_line(linha)
                        registros.append(registro)
                    except Exception as e:
                        erros.append(f"Linha {num_linha}: {str(e)}")
        
        except Exception as e:
            erros.append(f"Erro ao abrir arquivo: {str(e)}")
        
        return registros, erros
    
    @staticmethod
    def parse_file_m460401(caminho: str, encoding: str = 'latin-1') -> Tuple[List[RegistroM460401], List[str]]:
        """Parse arquivo M460401 completo"""
        registros = []
        erros = []
        
        try:
            with open(caminho, 'r', encoding=encoding) as f:
                for num_linha, linha in enumerate(f, 1):
                    linha = linha.strip()
                    if not linha:
                        continue
                    
                    try:
                        registro = ParserM460.parse_m460401_line(linha)
                        registros.append(registro)
                    except Exception as e:
                        erros.append(f"Linha {num_linha}: {str(e)}")
        
        except Exception as e:
            erros.append(f"Erro ao abrir arquivo: {str(e)}")
        
        return registros, erros
    
    @staticmethod
    def parse_file_m460801(caminho: str, encoding: str = 'latin-1') -> Tuple[List[RegistroM460801], List[str]]:
        """Parse arquivo M460801 completo"""
        registros = []
        erros = []
        
        try:
            with open(caminho, 'r', encoding=encoding) as f:
                for num_linha, linha in enumerate(f, 1):
                    linha = linha.strip()
                    if not linha:
                        continue
                    
                    try:
                        registro = ParserM460.parse_m460801_line(linha)
                        registros.append(registro)
                    except Exception as e:
                        erros.append(f"Linha {num_linha}: {str(e)}")
        
        except Exception as e:
            erros.append(f"Erro ao abrir arquivo: {str(e)}")
        
        return registros, erros


# Funções auxiliares para análise

def agrupar_por_gifus(registros: List) -> dict:
    """Agrupa registros por GIFUS"""
    grupos = {}
    for reg in registros:
        gifus = reg.gifus_analise
        if gifus not in grupos:
            grupos[gifus] = []
        grupos[gifus].append(reg)
    return grupos


def agrupar_por_situacao(registros: List[RegistroM460301]) -> dict:
    """Agrupa registros M460301/M460401 por situação de multiplicidade/sinistro"""
    grupos = {}
    for reg in registros:
        situacao = reg.situacao_mult_sinistro
        if situacao not in grupos:
            grupos[situacao] = []
        grupos[situacao].append(reg)
    return grupos


def calcular_totais_vaf(registros: List) -> dict:
    """Calcula totais de VAF para registros M460301/M460401"""
    total_vencido = Decimal('0')
    total_vincendo = Decimal('0')
    total_vaf3 = Decimal('0')
    total_vaf4 = Decimal('0')
    
    for reg in registros:
        if hasattr(reg, 'valor_saldo_vaf1_va2_vencido'):
            total_vencido += reg.valor_saldo_vaf1_va2_vencido
            total_vincendo += reg.valor_saldo_vaf1_vaf2_vincendo
            total_vaf3 += reg.valor_saldo_vaf3
            total_vaf4 += reg.valor_saldo_vaf4
    
    return {
        'total_vencido': total_vencido,
        'total_vincendo': total_vincendo,
        'total_vaf3': total_vaf3,
        'total_vaf4': total_vaf4,
        'total_geral': total_vencido + total_vincendo + total_vaf3 + total_vaf4
    }


if __name__ == '__main__':
    print("=" * 80)
    print("PARSER M460xxx - CEF")
    print("=" * 80)
    print("\nMódulo de parsing para arquivos de irregularidades CADMUT")
    print("\nArquivos suportados:")
    print("  • M460301: Contratos com Irregularidade (Acumulativo)")
    print("  • M460401: Contratos com Irregularidade (Inclusões no Mês)")
    print("  • M460801: Contratos Regularizados sem Manifestação GIFUS")
    print("\n✅ Módulo carregado com sucesso!")
