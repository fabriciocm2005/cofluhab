"""
Interpretador de Arquivos de Retorno CEF

Este módulo interpreta arquivos .txt de retorno da CEF (FCVS e CADMUT),
extraindo informações de processamento, códigos de erro, validações e status.

Funcionalidades:
- Leitura de arquivos de retorno (.txt)
- Interpretação de códigos de erro/validação
- Parsing de registros de retorno (HEADER, MOVIMENTO, TRAILER, CRÍTICA)
- Mapeamento de códigos para descrições
- Geração de relatórios de processamento
- Identificação de registros aceitos/rejeitados
- Análise de críticas e mensagens
- Suporte a múltiplos tipos de retorno (FCVS, CADMUT, DOSSIE)

Autor: CEF Integration Bot
Data: 2026-01-23
"""

import re
import json
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict


class CodigoInterpretacao:
    """Representa um código de interpretação do manual"""
    
    def __init__(self, codigo: str, descricao: str, categoria: str = 'validacao', detalhes: List[str] = None):
        self.codigo = codigo
        self.descricao = descricao
        self.categoria = categoria
        self.detalhes = detalhes or []
    
    def __repr__(self):
        return f"Codigo({self.codigo}: {self.descricao[:50]}...)"
    
    def to_dict(self):
        return {
            'codigo': self.codigo,
            'descricao': self.descricao,
            'categoria': self.categoria,
            'detalhes': self.detalhes
        }


class RegistroRetorno:
    """Representa um registro de retorno da CEF"""
    
    def __init__(self, linha: str, tipo_registro: str = None):
        self.linha_original = linha
        self.tipo_registro = tipo_registro or self._identificar_tipo(linha)
        self.campos = {}
        self.codigos_critica = []
        self.status = 'PROCESSADO'  # PROCESSADO, ACEITO, REJEITADO, CRITICA
    
    def _identificar_tipo(self, linha: str) -> str:
        """Identifica o tipo de registro pela posição inicial"""
        if not linha or len(linha) < 2:
            return 'DESCONHECIDO'
        
        # Tipo de registro geralmente está nas primeiras posições
        tipo_char = linha[0:1]
        
        tipos = {
            '0': 'HEADER',
            '1': 'MOVIMENTO',
            '2': 'MOVIMENTO',
            '3': 'HEADER',
            '4': 'MOVIMENTO',
            '5': 'CRITICA',
            '9': 'TRAILER',
        }
        
        return tipos.get(tipo_char, 'MOVIMENTO')
    
    def adicionar_campo(self, nome: str, valor: Any):
        """Adiciona um campo extraído"""
        self.campos[nome] = valor
    
    def adicionar_critica(self, codigo: str, descricao: str = None):
        """Adiciona código de crítica encontrado"""
        self.codigos_critica.append({
            'codigo': codigo,
            'descricao': descricao
        })
    
    def to_dict(self):
        return {
            'tipo_registro': self.tipo_registro,
            'status': self.status,
            'campos': self.campos,
            'codigos_critica': self.codigos_critica,
            'linha_original': self.linha_original[:100] + '...' if len(self.linha_original) > 100 else self.linha_original
        }


class ReturnFileParser:
    """Parser base para arquivos de retorno"""
    
    def __init__(self):
        self.registros: List[RegistroRetorno] = []
        self.header = None
        self.trailer = None
        self.movimentos = []
        self.criticas = []
    
    def parse_arquivo(self, caminho: str) -> Dict[str, Any]:
        """
        Lê e parseia arquivo de retorno completo
        
        Args:
            caminho: Caminho do arquivo .txt
        
        Returns:
            Dicionário com dados parseados
        """
        self.registros = []
        self.movimentos = []
        self.criticas = []
        
        # Lê arquivo
        with open(caminho, 'r', encoding='latin-1') as f:
            linhas = f.readlines()
        
        # Processa cada linha
        for i, linha in enumerate(linhas):
            linha_limpa = linha.rstrip('\n\r')
            
            if not linha_limpa:
                continue
            
            registro = RegistroRetorno(linha_limpa)
            self._parsear_registro(registro)
            
            self.registros.append(registro)
            
            # Organiza por tipo
            if registro.tipo_registro == 'HEADER':
                self.header = registro
            elif registro.tipo_registro == 'TRAILER':
                self.trailer = registro
            elif registro.tipo_registro == 'CRITICA':
                self.criticas.append(registro)
            else:
                self.movimentos.append(registro)
        
        return self._gerar_resumo()
    
    def _parsear_registro(self, registro: RegistroRetorno):
        """Parseia campos de um registro (implementar nas subclasses)"""
        # Extração básica
        linha = registro.linha_original
        
        if len(linha) >= 430:  # Tamanho padrão FCVS
            # Campos comuns
            registro.adicionar_campo('tipo_movimento', linha[0:2].strip())
            registro.adicionar_campo('tipo_registro', linha[2:3].strip())
            
            # Busca códigos de crítica (geralmente campo M1, M2, M3, etc)
            self._extrair_criticas(registro, linha)
    
    def _extrair_criticas(self, registro: RegistroRetorno, linha: str):
        """Extrai códigos de crítica da linha"""
        # Padrão: campos M1-M99 com valores numéricos indicando erro
        # Posições variam por tipo, mas geralmente estão após os dados principais
        
        # Procura por marcadores M seguidos de número
        if len(linha) > 200:
            # Área de críticas geralmente está no final do registro
            area_criticas = linha[200:]
            
            # Extrai valores não zero (indicam erro)
            for i in range(0, min(len(area_criticas), 100)):
                if area_criticas[i:i+1].isdigit() and area_criticas[i:i+1] != '0':
                    codigo_critica = f"M{i+1}"
                    registro.adicionar_critica(codigo_critica)
                    registro.status = 'CRITICA'
    
    def _gerar_resumo(self) -> Dict[str, Any]:
        """Gera resumo do processamento"""
        return {
            'total_registros': len(self.registros),
            'header': self.header.to_dict() if self.header else None,
            'trailer': self.trailer.to_dict() if self.trailer else None,
            'movimentos': len(self.movimentos),
            'criticas': len(self.criticas),
            'registros_aceitos': len([m for m in self.movimentos if m.status == 'ACEITO']),
            'registros_rejeitados': len([m for m in self.movimentos if m.status in ['REJEITADO', 'CRITICA']]),
            'codigos_critica_unicos': self._listar_codigos_unicos(),
        }
    
    def _listar_codigos_unicos(self) -> List[str]:
        """Lista códigos de crítica únicos encontrados"""
        codigos = set()
        for reg in self.registros:
            for critica in reg.codigos_critica:
                codigos.add(critica['codigo'])
        return sorted(list(codigos))


class FCVSReturnParser(ReturnFileParser):
    """Parser especializado para retornos FCVS (FH1, FH2, FH3)"""
    
    def _parsear_registro(self, registro: RegistroRetorno):
        """Parseia registro FCVS"""
        super()._parsear_registro(registro)
        
        linha = registro.linha_original
        
        if registro.tipo_registro == 'HEADER':
            # Extrai campos do header
            if len(linha) >= 20:
                registro.adicionar_campo('matricula_agente', linha[2:8].strip())
                registro.adicionar_campo('data_processamento', linha[8:14].strip())
                registro.adicionar_campo('qtd_registros', linha[14:20].strip())
        
        elif registro.tipo_registro == 'MOVIMENTO':
            # Extrai campos principais do movimento
            if len(linha) >= 50:
                registro.adicionar_campo('numero_contrato', linha[8:21].strip())
                registro.adicionar_campo('cpf_mutuario', linha[67:84].strip())
                registro.adicionar_campo('nome_mutuario', linha[26:66].strip())
                
                # Verifica se há críticas (códigos M)
                self._extrair_criticas_fcvs(registro, linha)
        
        elif registro.tipo_registro == 'TRAILER':
            # Extrai totalizadores
            if len(linha) >= 13:
                registro.adicionar_campo('qtd_processados', linha[7:13].strip())


    def _extrair_criticas_fcvs(self, registro: RegistroRetorno, linha: str):
        """Extrai críticas específicas de FCVS"""
        # Códigos M1-M99 conforme manual
        # M1: AGENTE inválido
        # M2: CONTRATO com caractere especial/não informado
        # M3: HIPOTECA fora do intervalo
        # M4: TIPO Mutuário < 0 ou = brancos
        # M5: Nome inválido
        # M6: SEGURADORA ou REGIÃO inválida
        # M7: CPF não criticado
        # etc...
        
        # Posições típicas das marcas M (variam por tipo de ficha)
        if len(linha) >= 430:
            # Área de marcas geralmente entre posições 300-400
            area_marcas = linha[300:400]
            
            for i, char in enumerate(area_marcas):
                if char != '0' and char != ' ':
                    codigo = f"M{i+1}"
                    descricao = self._obter_descricao_codigo_m(codigo)
                    registro.adicionar_critica(codigo, descricao)
                    registro.status = 'REJEITADO'


    def _obter_descricao_codigo_m(self, codigo: str) -> str:
        """Retorna descrição de código M"""
        descricoes = {
            'M1': 'AGENTE inválido',
            'M2': 'CONTRATO com caractere especial ou não informado',
            'M3': 'HIPOTECA fora do intervalo',
            'M4': 'TIPO Mutuário < 0 ou = brancos',
            'M5': 'Nome inválido (caracteres especiais, apenas um nome, etc)',
            'M6': 'SEGURADORA ou REGIÃO inválida',
            'M7': 'CPF não criticado',
            'M8': 'Identidade inválida',
            'M9': 'Data de nascimento inválida',
            'M10': 'Data do contrato inválida',
            'M11': 'Valor do financiamento inválido',
            'M12': 'Prazo inválido',
            'M13': 'Taxa de juros inválida',
            'M14': 'UF inválida',
            'M15': 'Código do município inválido',
            'M16': 'CEP inválido',
            'M17': 'Endereço inválido',
            'M18': 'Saldo devedor inválido',
            'M19': 'Data de vencimento inválida',
            'M20': 'Sistema de amortização inválido',
        }
        
        return descricoes.get(codigo, f'Código {codigo} não documentado')


class CADMUTReturnParser(ReturnFileParser):
    """Parser especializado para retornos CADMUT"""
    
    def _parsear_registro(self, registro: RegistroRetorno):
        """Parseia registro CADMUT"""
        super()._parsear_registro(registro)
        
        linha = registro.linha_original
        
        if registro.tipo_registro == 'MOVIMENTO' and len(linha) >= 50:
            # Extrai CPF e nome
            registro.adicionar_campo('cpf', linha[30:41].strip())
            registro.adicionar_campo('nome', linha[50:90].strip())


class ReturnInterpreter:
    """
    Interpretador completo de arquivos de retorno
    
    Combina parsing com interpretação de códigos usando base de conhecimento
    """
    
    def __init__(self, conhecimento_path: str = None):
        """
        Args:
            conhecimento_path: Caminho para cef_conhecimento_completo.json
        """
        self.codigos_interpretacao = {}
        
        # Carrega base de conhecimento
        if not conhecimento_path:
            conhecimento_path = Path(__file__).parent.parent / 'cef_conhecimento_completo.json'
        
        if Path(conhecimento_path).exists():
            self._carregar_conhecimento(conhecimento_path)
    
    def _carregar_conhecimento(self, path: str):
        """Carrega códigos de interpretação do JSON"""
        with open(path, 'r', encoding='utf-8') as f:
            conhecimento = json.load(f)
        
        codigos = conhecimento.get('codigos_interpretacao', {})
        
        for codigo, info in codigos.items():
            self.codigos_interpretacao[codigo] = CodigoInterpretacao(
                codigo=codigo,
                descricao=info.get('descricao', ''),
                categoria=info.get('categoria', 'validacao'),
                detalhes=info.get('detalhes', [])
            )
    
    def interpretar_arquivo(self, caminho: str, tipo: str = 'FCVS') -> Dict[str, Any]:
        """
        Interpreta arquivo de retorno completo
        
        Args:
            caminho: Caminho do arquivo .txt
            tipo: Tipo de arquivo (FCVS, CADMUT)
        
        Returns:
            Dicionário com interpretação completa
        """
        # Seleciona parser
        if tipo == 'FCVS':
            parser = FCVSReturnParser()
        elif tipo == 'CADMUT':
            parser = CADMUTReturnParser()
        else:
            parser = ReturnFileParser()
        
        # Parseia arquivo
        resumo = parser.parse_arquivo(caminho)
        
        # Interpreta códigos encontrados
        interpretacoes = self._interpretar_codigos(parser.registros)
        
        # Gera relatório
        relatorio = self._gerar_relatorio(parser, resumo, interpretacoes)
        
        return relatorio
    
    def _interpretar_codigos(self, registros: List[RegistroRetorno]) -> Dict[str, Any]:
        """Interpreta códigos de crítica encontrados"""
        interpretacoes = {
            'codigos_encontrados': [],
            'categorias': defaultdict(int),
            'descricoes': {}
        }
        
        codigos_unicos = set()
        
        for registro in registros:
            for critica in registro.codigos_critica:
                codigo = critica['codigo']
                codigos_unicos.add(codigo)
                
                # Busca interpretação na base
                if codigo in self.codigos_interpretacao:
                    info = self.codigos_interpretacao[codigo]
                    interpretacoes['descricoes'][codigo] = info.to_dict()
                    interpretacoes['categorias'][info.categoria] += 1
                else:
                    # Usa descrição do próprio registro
                    interpretacoes['descricoes'][codigo] = {
                        'codigo': codigo,
                        'descricao': critica.get('descricao', 'Código não documentado'),
                        'categoria': 'desconhecido'
                    }
        
        interpretacoes['codigos_encontrados'] = sorted(list(codigos_unicos))
        
        return interpretacoes
    
    def _gerar_relatorio(self, parser: ReturnFileParser, resumo: Dict, 
                        interpretacoes: Dict) -> Dict[str, Any]:
        """Gera relatório completo de interpretação"""
        
        # Separa registros por status
        por_status = defaultdict(list)
        for reg in parser.registros:
            por_status[reg.status].append(reg.to_dict())
        
        # Monta relatório
        relatorio = {
            'arquivo': {
                'data_processamento': datetime.now().isoformat(),
                'total_linhas': len(parser.registros),
            },
            'resumo': resumo,
            'interpretacoes': interpretacoes,
            'registros_por_status': {
                status: len(regs) for status, regs in por_status.items()
            },
            'registros_rejeitados': por_status.get('REJEITADO', []),
            'registros_critica': por_status.get('CRITICA', []),
            'mensagens': self._gerar_mensagens(interpretacoes),
            'acao_requerida': self._determinar_acao(resumo, interpretacoes)
        }
        
        return relatorio
    
    def _gerar_mensagens(self, interpretacoes: Dict) -> List[str]:
        """Gera mensagens amigáveis sobre o processamento"""
        mensagens = []
        
        if not interpretacoes['codigos_encontrados']:
            mensagens.append("✅ Nenhum código de crítica encontrado. Todos os registros foram aceitos.")
        else:
            mensagens.append(f"⚠️ {len(interpretacoes['codigos_encontrados'])} tipo(s) de crítica encontrado(s).")
            
            # Lista códigos mais comuns
            for codigo in interpretacoes['codigos_encontrados'][:5]:
                desc = interpretacoes['descricoes'].get(codigo, {}).get('descricao', 'Sem descrição')
                mensagens.append(f"   • {codigo}: {desc}")
        
        return mensagens
    
    def _determinar_acao(self, resumo: Dict, interpretacoes: Dict) -> str:
        """Determina ação recomendada baseada nos resultados"""
        
        if resumo.get('registros_rejeitados', 0) > 0:
            return "CORRIGIR_E_REENVIAR: Há registros rejeitados que precisam ser corrigidos e reenviados."
        
        elif resumo.get('criticas', 0) > 0:
            return "REVISAR: Há críticas que devem ser revisadas antes de prosseguir."
        
        elif resumo.get('registros_aceitos', 0) == resumo.get('movimentos', 0):
            return "SUCESSO: Todos os registros foram aceitos. Nenhuma ação necessária."
        
        else:
            return "VERIFICAR: Status dos registros precisa ser verificado."


class LoteReturnProcessor:
    """Processa múltiplos arquivos de retorno em lote"""
    
    def __init__(self):
        self.interpreter = ReturnInterpreter()
        self.resultados = []
    
    def processar_diretorio(self, diretorio: str, padrao: str = '*.txt') -> Dict[str, Any]:
        """
        Processa todos os arquivos de retorno em um diretório
        
        Args:
            diretorio: Caminho do diretório
            padrao: Padrão de arquivos (ex: '*.txt', 'RETORNO_*.txt')
        
        Returns:
            Relatório consolidado
        """
        path = Path(diretorio)
        arquivos = list(path.glob(padrao))
        
        self.resultados = []
        
        for arquivo in arquivos:
            try:
                # Detecta tipo pelo nome do arquivo
                tipo = self._detectar_tipo_arquivo(arquivo.name)
                
                # Interpreta
                resultado = self.interpreter.interpretar_arquivo(str(arquivo), tipo)
                resultado['arquivo_nome'] = arquivo.name
                
                self.resultados.append(resultado)
            
            except Exception as e:
                self.resultados.append({
                    'arquivo_nome': arquivo.name,
                    'erro': str(e),
                    'status': 'ERRO'
                })
        
        return self._consolidar_resultados()
    
    def _detectar_tipo_arquivo(self, nome: str) -> str:
        """Detecta tipo de arquivo pelo nome"""
        nome_upper = nome.upper()
        
        if 'CADMUT' in nome_upper or 'MCAD' in nome_upper:
            return 'CADMUT'
        elif 'FCVS' in nome_upper or 'FH' in nome_upper:
            return 'FCVS'
        else:
            return 'FCVS'  # Padrão
    
    def _consolidar_resultados(self) -> Dict[str, Any]:
        """Consolida resultados de múltiplos arquivos"""
        return {
            'total_arquivos': len(self.resultados),
            'arquivos_processados': len([r for r in self.resultados if 'erro' not in r]),
            'arquivos_com_erro': len([r for r in self.resultados if 'erro' in r]),
            'total_registros': sum(r.get('resumo', {}).get('total_registros', 0) for r in self.resultados),
            'total_aceitos': sum(r.get('resumo', {}).get('registros_aceitos', 0) for r in self.resultados),
            'total_rejeitados': sum(r.get('resumo', {}).get('registros_rejeitados', 0) for r in self.resultados),
            'arquivos': self.resultados
        }


# Funções auxiliares de alto nível

def interpretar_retorno_fcvs(caminho: str) -> Dict:
    """
    Interpreta arquivo de retorno FCVS
    
    Args:
        caminho: Caminho do arquivo .txt
    
    Returns:
        Relatório de interpretação
    """
    interpreter = ReturnInterpreter()
    return interpreter.interpretar_arquivo(caminho, 'FCVS')


def interpretar_retorno_cadmut(caminho: str) -> Dict:
    """
    Interpreta arquivo de retorno CADMUT
    
    Args:
        caminho: Caminho do arquivo .txt
    
    Returns:
        Relatório de interpretação
    """
    interpreter = ReturnInterpreter()
    return interpreter.interpretar_arquivo(caminho, 'CADMUT')


def processar_lote_retornos(diretorio: str) -> Dict:
    """
    Processa lote de arquivos de retorno
    
    Args:
        diretorio: Diretório com arquivos .txt
    
    Returns:
        Relatório consolidado
    """
    processor = LoteReturnProcessor()
    return processor.processar_diretorio(diretorio)


# Exemplo de uso
if __name__ == '__main__':
    print("🔍 Interpretador de Arquivos de Retorno CEF")
    print("=" * 60)
    
    # Teste com arquivo mock
    print("\n📄 Testando interpretação de retorno FCVS...")
    
    # Cria arquivo de exemplo
    exemplo_retorno = """0I12345620260123000010
1I12345600012345678901JOAO DA SILVA                        12345678909      010180
9123456000010"""
    
    arquivo_teste = Path('exemplo_retorno_fcvs.txt')
    with open(arquivo_teste, 'w', encoding='latin-1') as f:
        f.write(exemplo_retorno)
    
    try:
        # Interpreta
        interpreter = ReturnInterpreter()
        resultado = interpreter.interpretar_arquivo(str(arquivo_teste), 'FCVS')
        
        print(f"   ✅ Arquivo interpretado com sucesso!")
        print(f"\n   📊 Resumo:")
        print(f"      Total de registros: {resultado['resumo']['total_registros']}")
        print(f"      Movimentos: {resultado['resumo']['movimentos']}")
        print(f"      Aceitos: {resultado['resumo']['registros_aceitos']}")
        print(f"      Rejeitados: {resultado['resumo']['registros_rejeitados']}")
        
        if resultado['mensagens']:
            print(f"\n   💬 Mensagens:")
            for msg in resultado['mensagens']:
                print(f"      {msg}")
        
        print(f"\n   🎯 Ação recomendada: {resultado['acao_requerida']}")
    
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    finally:
        # Limpa arquivo de teste
        if arquivo_teste.exists():
            arquivo_teste.unlink()
    
    # Teste de códigos de interpretação
    print("\n📚 Testando base de conhecimento...")
    interpreter = ReturnInterpreter()
    print(f"   ✅ {len(interpreter.codigos_interpretacao)} códigos carregados")
    
    if interpreter.codigos_interpretacao:
        print(f"   📖 Exemplo de código:")
        codigo_exemplo = list(interpreter.codigos_interpretacao.values())[0]
        print(f"      Código {codigo_exemplo.codigo}:")
        print(f"      {codigo_exemplo.descricao[:100]}...")
    
    print("\n✅ Testes de interpretação concluídos!")
    print("\n💡 Próximos passos:")
    print("   1. Testar com arquivos reais de retorno da CEF")
    print("   2. Integrar com models Django (RetornoCEF)")
    print("   3. Criar view para upload e interpretação")
    print("   4. Adicionar notificações por e-mail")
    print("   5. Dashboard de acompanhamento de retornos")
