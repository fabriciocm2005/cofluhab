"""
Parser Aprimorado para arquivo P3026 - Posição da Carteira Homologada CEF
Suporta todos os tipos de registro: TR1, TR2, TR3, TR4, TR5, TR6, TR7, TR8, TR9

Baseado no layout: Leiaute_FCVS3026_TR1_a_TR9_270417
"""

import json
import os
import csv
import re
import unicodedata
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path


class TipoRegistroP3026(Enum):
    """Tipos de registro no arquivo P3026"""
    HEADER = '0'
    TR1 = '1'  # Contratos habilitados não homologados
    TR2 = '2'  # Contratos com responsabilidade de replanejamento
    TR3 = '3'  # Contratos com responsabilidade de alteração cadastral
    TR4 = '4'  # Contratos com responsabilidade de outra natureza
    TR5 = '5'  # Contratos com responsabilidade associada à cobertura
    TR6 = '6'  # Contratos com responsabilidade por incidir evento
    TR7 = '7'  # Contratos quitados
    TR8 = '8'  # Contratos cancelados
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
    """HEADER do arquivo P3026 (Tipo '0')"""
    tipo_registro: str
    codigo_agente: str
    data_geracao: datetime
    hora_geracao: str
    sequencial_arquivo: str
    nome_arquivo: str
    versao: str


@dataclass
class RegistroP3026:
    """Registro genérico com suporte a todos os tipos"""
    tipo_registro: str
    dados: Dict[str, Any]
    numero_contrato: str = ""
    cpf_mutuario: str = ""
    
    def get_campo(self, nome: str) -> Any:
        """Obter valor de um campo por nome"""
        return self.dados.get(nome)
    
    def __repr__(self):
        return f"RegistroP3026(tipo={self.tipo_registro}, contrato={self.numero_contrato}, cpf={self.cpf_mutuario})"


@dataclass
class TrailerP3026:
    """TRAILER do arquivo P3026 (Tipo '9')"""
    tipo_registro: str
    codigo_agente: str
    total_registros: int
    data_geracao: datetime
    sequencial_arquivo: str


class ParserP3026:
    """
    Parser robusto para arquivo P3026
    Carrega layout dinamicamente de ficha_p3026_layout.json
    """
    
    def __init__(self, caminho_layout: Optional[str] = None):
        """
        Inicializa parser
        
        Args:
            caminho_layout: Caminho para arquivo de layout JSON
                          Se None, busca em principal/ficha_p3026_layout.json
        """
        self.layout = self._carregar_layout(caminho_layout)
        self.erros_parse = []
        
    def _carregar_layout(self, caminho: Optional[str]) -> Dict[str, Any]:
        """Carrega especificação de layout do JSON"""
        if caminho is None:
            # Procurar no diretório principal/
            caminho = Path(__file__).parent / "ficha_p3026_layout.json"
        
        caminho = Path(caminho)
        
        if not caminho.exists():
            # Se não encontrar, retornar layout vazio
            print(f"⚠️ Layout não encontrado em {caminho}")
            return {}
        
        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Erro ao carregar layout: {e}")
            return {}
    
    def parse_arquivo(self, caminho_arquivo: str) -> Tuple[Optional['ArquivoP3026'], List[str]]:
        """
        Parse do arquivo P3026 completo
        
        Returns:
            (ArquivoP3026, lista_de_erros)
        """
        self.erros_parse = []
        
        try:
            with open(caminho_arquivo, 'r', encoding='latin-1') as f:
                linhas = f.readlines()

            # Alguns retornos P3026 chegam sem quebras de linha: um stream contínuo
            # de registros com tamanho fixo (251 chars). Nesse caso, f.readlines()
            # retorna uma única linha gigante e precisamos fatiar manualmente.
            if len(linhas) == 1:
                bruto = (linhas[0] or '').rstrip('\n\r')
                if bruto and len(bruto) > 251 and len(bruto) % 251 == 0:
                    linhas = [bruto[i:i + 251] for i in range(0, len(bruto), 251)]
                    self.erros_parse.append(
                        f"Arquivo sem quebras de linha detectado; fatiado em {len(linhas)} registros de 251 posições"
                    )
            
            if not linhas:
                self.erros_parse.append("Arquivo vazio")
                return None, self.erros_parse

            # Formato CSV/Delimitado (ex.: POSICAO;TIPO_DE_REGISTRO;...)
            primeira_linha = linhas[0].strip().upper()
            if 'TIPO_DE_REGISTRO' in primeira_linha and ';' in primeira_linha:
                return self._parse_arquivo_delimitado(caminho_arquivo)
            
            header = None
            registros = []
            trailer = None
            
            for num_linha, linha in enumerate(linhas, 1):
                linha = linha.rstrip('\n\r')
                if not linha.strip():
                    continue

                tipo_registro, linha_normalizada = self._detectar_tipo_registro(linha)
                
                try:
                    if tipo_registro == '0':
                        header = self._parse_header(linha_normalizada)
                    elif tipo_registro in ['1', '2', '3', '4', '5', '6', '7', '8']:
                        registro = self._parse_registro_tipo(linha_normalizada)
                        if registro:
                            registros.append(registro)
                    elif tipo_registro == '9':
                        trailer = self._parse_trailer(linha_normalizada)
                except Exception as e:
                    self.erros_parse.append(f"Linha {num_linha}: {str(e)}")
            
            if not header:
                if registros:
                    # Alguns arquivos de retorno podem vir sem HEADER.
                    # Nesses casos, cria um header sintético para permitir visualização.
                    self.erros_parse.append("HEADER não encontrado (processado com header sintético)")
                    header = HeaderP3026(
                        tipo_registro='0',
                        codigo_agente='',
                        data_geracao=datetime.now(),
                        hora_geracao='',
                        sequencial_arquivo='',
                        nome_arquivo=os.path.basename(caminho_arquivo),
                        versao='SINTETICO'
                    )
                else:
                    self.erros_parse.append("HEADER não encontrado")
                    return None, self.erros_parse
            
            arquivo = ArquivoP3026(
                header=header,
                registros=registros,
                trailer=trailer or TrailerP3026('9', '', len(registros), datetime.now(), '')
            )
            
            return arquivo, self.erros_parse
            
        except Exception as e:
            self.erros_parse.append(f"Erro geral: {str(e)}")
            return None, self.erros_parse

    def _parse_arquivo_delimitado(self, caminho_arquivo: str) -> Tuple[Optional['ArquivoP3026'], List[str]]:
        """Parse de arquivo P3026 delimitado por ';'."""
        self.erros_parse = []
        registros: List[RegistroP3026] = []

        try:
            with open(caminho_arquivo, 'r', encoding='latin-1', newline='') as f:
                reader = csv.DictReader(f, delimiter=';')
                for i, row in enumerate(reader, start=2):
                    if not row:
                        continue

                    tipo = (row.get('TIPO_DE_REGISTRO') or '').strip()
                    if tipo not in {'1', '2', '3', '4', '5', '6', '7', '8', '9'}:
                        # Alguns arquivos podem ter linhas inválidas no final
                        continue

                    numero_contrato = (row.get('NUMERO_DO_CONTRATO') or '').strip()
                    cpf = (row.get('CPF') or '').strip()

                    # Limpar chaves/valores e converter strings vazias em None
                    dados = {}
                    for k, v in row.items():
                        chave = (k or '').strip()
                        valor = (v or '').strip()
                        if chave:
                            # Converter strings vazias ou apenas espaços em None
                            dados[chave] = valor if valor else None

                    registros.append(
                        RegistroP3026(
                            tipo_registro=tipo,
                            dados=dados,
                            numero_contrato=numero_contrato,
                            cpf_mutuario=cpf
                        )
                    )

            if not registros:
                self.erros_parse.append('Nenhum registro válido encontrado no arquivo delimitado')
                return None, self.erros_parse

            header = HeaderP3026(
                tipo_registro='0',
                codigo_agente=(registros[0].dados.get('MATRICULA_DO_AGENTE') or '').strip(),
                data_geracao=datetime.now(),
                hora_geracao='',
                sequencial_arquivo='',
                nome_arquivo=os.path.basename(caminho_arquivo),
                versao='DELIMITADO'
            )

            trailer = TrailerP3026(
                tipo_registro='9',
                codigo_agente=header.codigo_agente,
                total_registros=len(registros),
                data_geracao=header.data_geracao,
                sequencial_arquivo=''
            )

            arquivo = ArquivoP3026(header=header, registros=registros, trailer=trailer)
            return arquivo, self.erros_parse

        except Exception as e:
            self.erros_parse.append(f'Erro ao ler arquivo delimitado: {str(e)}')
            return None, self.erros_parse

    def _detectar_tipo_registro(self, linha: str) -> Tuple[str, str]:
        """Detecta tipo de registro em formatos diferentes de arquivo."""
        if not linha:
            return '', linha

        # Formato padrão: primeiro caractere é o tipo
        if linha[0:1] in {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9'}:
            return linha[0:1], linha

        linha_stripped = linha.lstrip()
        if linha_stripped and linha_stripped[0:1] in {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9'}:
            return linha_stripped[0:1], linha_stripped

        # Formato alternativo: prefixo TR1, TR2, ..., TR9
        prefixo = linha_stripped[:3].upper()
        if prefixo in {'TR1', 'TR2', 'TR3', 'TR4', 'TR5', 'TR6', 'TR7', 'TR8', 'TR9'}:
            tipo = prefixo[-1]
            return tipo, linha_stripped[3:].lstrip()

        return '', linha
    
    def _parse_header(self, linha: str) -> HeaderP3026:
        """Parse do HEADER (tipo 0)"""
        return HeaderP3026(
            tipo_registro=linha[0:1],
            codigo_agente=linha[1:9].strip(),
            data_geracao=self._parse_data(linha[9:17]) if len(linha) > 16 else datetime.now(),
            hora_geracao=linha[17:23].strip() if len(linha) > 22 else "",
            sequencial_arquivo=linha[23:31].strip() if len(linha) > 30 else "",
            nome_arquivo=linha[31:100].strip() if len(linha) > 99 else "",
            versao=linha[100:150].strip() if len(linha) > 149 else ""
        )
    
    def _parse_registro_tipo(self, linha: str) -> Optional[RegistroP3026]:
        """Parse de registro de dados (TR1-TR8)"""
        # Ignora linhas curtas/espurias (ex.: cabeçalho textual sem layout de registro).
        if len(linha) < 100:
            return None

        tipo = linha[0:1]
        
        if tipo not in ['1', '2', '3', '4', '5', '6', '7', '8']:
            return None
        
        # Extrair campos básicos comuns
        numero_contrato = linha[16:29].strip() if len(linha) > 28 else ""
        
        # CPF/CNPJ do mutuário varia por tipo
        # Geralmente em posição próxima
        cpf_posicao = 70  # Aproximado baseado em TR1
        cpf = linha[cpf_posicao:cpf_posicao+11].strip() if len(linha) > cpf_posicao+10 else ""
        
        # Criar registro genérico com todos os dados disponíveis
        dados = {
            'linha_original': linha[:min(500, len(linha))],  # Guardar original
            'comprimento_total': len(linha)
        }
        
        # Se houver layout, extrair campos específicos
        chave_layout = f'TR{tipo}'
        if chave_layout in self.layout:
            layout_tipo = self.layout[chave_layout]
            for campo in layout_tipo.get('campos', []):
                nome = (campo.get('nome', '') or '').strip()
                posicao_str = (campo.get('posicao', '') or '').strip()
                
                # Tentar extrair posição e tamanho
                try:
                    # Alguns layouts trazem a faixa em "nome" e descrição em "posicao".
                    faixa = ''
                    nome_logico = ''

                    if re.match(r'^\d+\s*A\s*\d+$', nome.replace('  ', ' ')):
                        faixa = nome
                        nome_logico = self._normalizar_nome_campo(posicao_str)
                    elif re.match(r'^\d+\s*A\s*\d+$', posicao_str.replace('  ', ' ')):
                        faixa = posicao_str
                        nome_logico = self._normalizar_nome_campo(nome)

                    # Formato esperado: "XXX A YYY" onde XXX é início e YYY é fim
                    if faixa and 'A' in faixa:
                        inicio, fim = re.split(r'\s*A\s*', faixa)
                        inicio = int(inicio.strip()) - 1  # Converter para 0-based
                        fim = int(fim.strip())
                        
                        if fim <= len(linha):
                            valor = linha[inicio:fim].strip()
                            # Converter strings vazias ou apenas com espaços em None
                            if nome_logico:
                                dados[nome_logico] = valor if valor else None
                except (ValueError, IndexError):
                    pass
        
        return RegistroP3026(
            tipo_registro=tipo,
            dados=dados,
            numero_contrato=numero_contrato,
            cpf_mutuario=cpf
        )
    
    def _parse_trailer(self, linha: str) -> TrailerP3026:
        """Parse do TRAILER (tipo 9)"""
        try:
            total_registros = int(linha[1:9].strip()) if len(linha) > 8 else 0
        except ValueError:
            total_registros = 0
        
        return TrailerP3026(
            tipo_registro=linha[0:1],
            codigo_agente=linha[9:14].strip() if len(linha) > 13 else "",
            total_registros=total_registros,
            data_geracao=self._parse_data(linha[14:22]) if len(linha) > 21 else datetime.now(),
            sequencial_arquivo=linha[22:30].strip() if len(linha) > 29 else ""
        )
    
    def _parse_data(self, data_str: str) -> Optional[datetime]:
        """Parse de data DDMMAAAA"""
        try:
            if len(data_str) == 8 and data_str.isdigit():
                return datetime.strptime(data_str, '%d%m%Y')
        except ValueError:
            pass
        return None
    
    def _parse_numero(self, valor_str: str, casas_decimais: int = 0) -> Optional[float]:
        """Parse de número com casas decimais"""
        try:
            valor = float(valor_str.strip())
            if casas_decimais > 0:
                valor = valor / (10 ** casas_decimais)
            return valor
        except ValueError:
            return None

    def _normalizar_nome_campo(self, nome: str) -> str:
        """Normaliza nomes de campos para chaves estáveis (ASCII, upper snake case)."""
        texto = unicodedata.normalize('NFKD', nome or '')
        texto = ''.join(c for c in texto if not unicodedata.combining(c))
        texto = texto.upper()
        texto = re.sub(r'\([^)]*\)', '', texto)
        texto = re.sub(r'[^A-Z0-9]+', '_', texto)
        texto = re.sub(r'_+', '_', texto).strip('_')
        return texto


@dataclass
class ArquivoP3026:
    """Arquivo P3026 completo com header, registros e trailer"""
    header: HeaderP3026
    registros: List[RegistroP3026]
    trailer: TrailerP3026
    
    def filtrar_por_tipo(self, tipo_registro: str) -> List[RegistroP3026]:
        """Filtrar registros por tipo (TR1, TR2, etc)"""
        return [r for r in self.registros if r.tipo_registro == tipo_registro]
    
    def filtrar_por_cpf(self, cpf: str) -> List[RegistroP3026]:
        """Filtrar registros por CPF do mutuário"""
        return [r for r in self.registros if cpf in r.cpf_mutuario]
    
    def filtrar_por_contrato(self, numero_contrato: str) -> List[RegistroP3026]:
        """Filtrar registros por número de contrato"""
        return [r for r in self.registros if numero_contrato in r.numero_contrato]
    
    def resumo(self) -> Dict[str, Any]:
        """Gerar resumo do arquivo"""
        contagens_tipo = {}
        for tipo in ['1', '2', '3', '4', '5', '6', '7', '8']:
            contagens_tipo[f'TR{tipo}'] = len(self.filtrar_por_tipo(tipo))
        
        return {
            'total_registros': len(self.registros),
            'por_tipo': contagens_tipo,
            'data_geracao': self.header.data_geracao.isoformat() if self.header.data_geracao else None,
            'codigo_agente': self.header.codigo_agente
        }


# Função de conveniência para interpretação rápida
def interpretar_p3026(caminho_arquivo: str) -> Dict[str, Any]:
    """
    Função de compatibilidade com código anterior
    Interpreta arquivo P3026 e retorna dicionário
    """
    parser = ParserP3026()
    arquivo, erros = parser.parse_arquivo(caminho_arquivo)
    
    if not arquivo:
        return {
            'sucesso': False,
            'erros': erros,
            'resumo': {}
        }
    
    return {
        'sucesso': True,
        'erros': erros,
        'resumo': arquivo.resumo(),
        'total_registros': len(arquivo.registros),
        'arquivo': arquivo
    }
