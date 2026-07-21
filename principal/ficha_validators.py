"""
Validadores para Fichas CEF - FCVS e CADMUT

Este módulo contém validadores especializados para campos de fichas CEF,
implementando regras de negócio e validações técnicas conforme os manuais oficiais.

Funcionalidades:
- Validação de CPF/CNPJ
- Validação de datas e formatos
- Validação de valores monetários
- Validação de códigos específicos (UF, município, etc.)
- Validação de campos obrigatórios
- Validação de tamanhos e tipos
- Validação de consistência entre campos

Autor: CEF Integration Bot
Data: 2026-01-23
"""

import re
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Any, Optional, Tuple


class ValidationError:
    """Representa um erro de validação"""
    
    def __init__(self, campo: str, mensagem: str, codigo: str = None, severidade: str = 'error'):
        self.campo = campo
        self.mensagem = mensagem
        self.codigo = codigo
        self.severidade = severidade  # 'error', 'warning', 'info'
    
    def __repr__(self):
        return f"ValidationError({self.campo}: {self.mensagem})"
    
    def to_dict(self):
        return {
            'campo': self.campo,
            'mensagem': self.mensagem,
            'codigo': self.codigo,
            'severidade': self.severidade
        }


class CampoValidator:
    """Classe base para validação de campos"""
    
    # UFs válidas do Brasil
    UFS_VALIDAS = [
        'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
        'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
        'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
    ]
    
    @staticmethod
    def validar_cpf(cpf: str) -> bool:
        """
        Valida CPF brasileiro
        
        Args:
            cpf: String com CPF (pode conter pontos e traços)
        
        Returns:
            True se válido, False caso contrário
        """
        # Remove caracteres não numéricos
        cpf = re.sub(r'\D', '', str(cpf))
        
        # Verifica se tem 11 dígitos
        if len(cpf) != 11:
            return False
        
        # Verifica se todos os dígitos são iguais
        if cpf == cpf[0] * 11:
            return False
        
        # Valida primeiro dígito verificador
        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        digito1 = (soma * 10 % 11) % 10
        
        if int(cpf[9]) != digito1:
            return False
        
        # Valida segundo dígito verificador
        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        digito2 = (soma * 10 % 11) % 10
        
        if int(cpf[10]) != digito2:
            return False
        
        return True
    
    @staticmethod
    def validar_cnpj(cnpj: str) -> bool:
        """
        Valida CNPJ brasileiro
        
        Args:
            cnpj: String com CNPJ (pode conter pontos, traços e barras)
        
        Returns:
            True se válido, False caso contrário
        """
        # Remove caracteres não numéricos
        cnpj = re.sub(r'\D', '', str(cnpj))
        
        # Verifica se tem 14 dígitos
        if len(cnpj) != 14:
            return False
        
        # Verifica se todos os dígitos são iguais
        if cnpj == cnpj[0] * 14:
            return False
        
        # Valida primeiro dígito verificador
        pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma1 = sum(int(cnpj[i]) * pesos1[i] for i in range(12))
        digito1 = 0 if soma1 % 11 < 2 else 11 - (soma1 % 11)
        
        if int(cnpj[12]) != digito1:
            return False
        
        # Valida segundo dígito verificador
        pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma2 = sum(int(cnpj[i]) * pesos2[i] for i in range(13))
        digito2 = 0 if soma2 % 11 < 2 else 11 - (soma2 % 11)
        
        if int(cnpj[13]) != digito2:
            return False
        
        return True
    
    @staticmethod
    def validar_data(data_str: str, formato: str = '%d%m%y') -> Tuple[bool, Optional[date]]:
        """
        Valida string de data e converte para objeto date
        
        Args:
            data_str: String com a data
            formato: Formato esperado (padrão: DDMMAA)
        
        Returns:
            Tupla (válida, objeto_date ou None)
        """
        if not data_str:
            return False, None
        
        try:
            # Remove espaços
            data_str = data_str.strip()
            
            # Tenta converter
            if formato == '%d%m%y':
                # DDMMAA - precisa ajustar o século
                if len(data_str) == 6:
                    dia = int(data_str[0:2])
                    mes = int(data_str[2:4])
                    ano = int(data_str[4:6])
                    
                    # Define século (assumindo 1900-2099)
                    ano_completo = 2000 + ano if ano < 50 else 1900 + ano
                    
                    data_obj = date(ano_completo, mes, dia)
                    return True, data_obj
            else:
                data_obj = datetime.strptime(data_str, formato).date()
                return True, data_obj
        
        except (ValueError, IndexError):
            return False, None
        
        return False, None
    
    @staticmethod
    def validar_valor_monetario(valor: Any, max_decimais: int = 2) -> Tuple[bool, Optional[Decimal]]:
        """
        Valida valor monetário
        
        Args:
            valor: Valor a validar (pode ser string, int, float, Decimal)
            max_decimais: Número máximo de casas decimais
        
        Returns:
            Tupla (válido, Decimal ou None)
        """
        if valor is None or valor == '':
            return False, None
        
        try:
            # Converte para Decimal
            if isinstance(valor, str):
                # Remove espaços e substitui vírgula por ponto
                valor = valor.strip().replace(',', '.')
            
            decimal_valor = Decimal(str(valor))
            
            # Verifica se não é negativo
            if decimal_valor < 0:
                return False, None
            
            # Verifica casas decimais
            if decimal_valor.as_tuple().exponent < -max_decimais:
                return False, None
            
            return True, decimal_valor
        
        except (InvalidOperation, ValueError):
            return False, None
    
    @staticmethod
    def validar_uf(uf: str) -> bool:
        """Valida sigla de UF"""
        if not uf:
            return False
        
        uf = uf.strip().upper()
        return uf in CampoValidator.UFS_VALIDAS
    
    @staticmethod
    def validar_tamanho(valor: str, tamanho_esperado: int, exato: bool = False) -> bool:
        """
        Valida tamanho de campo
        
        Args:
            valor: Valor a validar
            tamanho_esperado: Tamanho esperado
            exato: Se True, deve ter exatamente o tamanho. Se False, até o tamanho.
        
        Returns:
            True se válido
        """
        if valor is None:
            return False
        
        tamanho_atual = len(str(valor))
        
        if exato:
            return tamanho_atual == tamanho_esperado
        else:
            return tamanho_atual <= tamanho_esperado
    
    @staticmethod
    def validar_numerico(valor: str, permitir_vazio: bool = False) -> bool:
        """Valida se valor contém apenas dígitos"""
        if not valor and permitir_vazio:
            return True
        
        if not valor:
            return False
        
        return valor.strip().isdigit()
    
    @staticmethod
    def validar_alfanumerico(valor: str, permitir_especiais: bool = True) -> bool:
        """Valida se valor é alfanumérico"""
        if not valor:
            return False
        
        if permitir_especiais:
            # Permite letras, números, espaços e alguns caracteres especiais comuns
            return bool(re.match(r'^[A-Za-zÀ-ÿ0-9\s\.\-/,º°]+$', valor))
        else:
            # Apenas letras e números
            return valor.replace(' ', '').isalnum()


class FH1Validator:
    """Validador especializado para ficha FH1"""
    
    CAMPOS_OBRIGATORIOS = [
        'UFS',
        'MAT. AG. FINANC. /DV',
        'N.º CONTRATO DO MUT. NO AGENTE',
        'NOME DO MUT. PRINCIPAL',
        'CPF/CI',
        'DATA DE NASCIMENTO',
        'CODIGO DO MUNICÍPIO',
        'UF',
        'ENDEREÇO DO IMÓVEL',
        'DATA DO CONTRATO',
        'VALOR FINANCIAMENTO CONTRATADO',
        'PRAZO CONTRATADO',
    ]
    
    def __init__(self):
        self.erros: List[ValidationError] = []
        self.avisos: List[ValidationError] = []
    
    def validar(self, dados: Dict[str, Any]) -> Tuple[bool, List[ValidationError]]:
        """
        Valida dados de ficha FH1
        
        Args:
            dados: Dicionário com dados da ficha
        
        Returns:
            Tupla (válido, lista_de_erros)
        """
        self.erros = []
        self.avisos = []
        
        # Valida campos obrigatórios
        self._validar_obrigatorios(dados)
        
        # Valida campos específicos
        self._validar_cpf(dados)
        self._validar_datas(dados)
        self._validar_valores_monetarios(dados)
        self._validar_uf(dados)
        self._validar_prazos(dados)
        self._validar_taxas(dados)
        self._validar_consistencia(dados)
        
        # Retorna resultado
        return (len(self.erros) == 0, self.erros + self.avisos)
    
    def _validar_obrigatorios(self, dados: Dict[str, Any]):
        """Valida se campos obrigatórios estão preenchidos"""
        for campo in self.CAMPOS_OBRIGATORIOS:
            valor = dados.get(campo)
            
            if not valor or (isinstance(valor, str) and not valor.strip()):
                self.erros.append(ValidationError(
                    campo=campo,
                    mensagem=f"Campo obrigatório não preenchido",
                    codigo='CAMPO_OBRIGATORIO',
                    severidade='error'
                ))
    
    def _validar_cpf(self, dados: Dict[str, Any]):
        """Valida CPF do mutuário"""
        cpf = dados.get('CPF/CI')
        
        if cpf:
            if not CampoValidator.validar_cpf(cpf):
                self.erros.append(ValidationError(
                    campo='CPF/CI',
                    mensagem=f"CPF inválido: {cpf}",
                    codigo='CPF_INVALIDO',
                    severidade='error'
                ))
    
    def _validar_datas(self, dados: Dict[str, Any]):
        """Valida campos de data"""
        # Data de nascimento
        data_nasc = dados.get('DATA DE NASCIMENTO')
        if data_nasc:
            valida, data_obj = CampoValidator.validar_data(data_nasc)
            if not valida:
                self.erros.append(ValidationError(
                    campo='DATA DE NASCIMENTO',
                    mensagem=f"Data de nascimento inválida: {data_nasc}",
                    codigo='DATA_INVALIDA',
                    severidade='error'
                ))
            elif data_obj:
                # Verifica se não é futura
                if data_obj > date.today():
                    self.erros.append(ValidationError(
                        campo='DATA DE NASCIMENTO',
                        mensagem=f"Data de nascimento não pode ser futura",
                        codigo='DATA_FUTURA',
                        severidade='error'
                    ))
                
                # Verifica idade mínima (18 anos)
                idade = (date.today() - data_obj).days / 365.25
                if idade < 18:
                    self.avisos.append(ValidationError(
                        campo='DATA DE NASCIMENTO',
                        mensagem=f"Mutuário menor de 18 anos",
                        codigo='IDADE_MINIMA',
                        severidade='warning'
                    ))
        
        # Data do contrato
        data_contrato = dados.get('DATA DO CONTRATO')
        if data_contrato:
            valida, data_obj = CampoValidator.validar_data(data_contrato)
            if not valida:
                self.erros.append(ValidationError(
                    campo='DATA DO CONTRATO',
                    mensagem=f"Data do contrato inválida: {data_contrato}",
                    codigo='DATA_INVALIDA',
                    severidade='error'
                ))
    
    def _validar_valores_monetarios(self, dados: Dict[str, Any]):
        """Valida campos de valor monetário"""
        campos_valores = [
            'VALOR FINANCIAMENTO CONTRATADO',
            'VALOR FINANC. PADRÃO FCVS',
            'VALOR DA GARANTIA',
            'VALOR DA PRESTAÇÃO',
        ]
        
        for campo in campos_valores:
            valor = dados.get(campo)
            if valor:
                valido, decimal_valor = CampoValidator.validar_valor_monetario(valor)
                if not valido:
                    self.erros.append(ValidationError(
                        campo=campo,
                        mensagem=f"Valor monetário inválido: {valor}",
                        codigo='VALOR_INVALIDO',
                        severidade='error'
                    ))
                elif decimal_valor and decimal_valor == 0:
                    self.avisos.append(ValidationError(
                        campo=campo,
                        mensagem=f"Valor zero pode não ser aceito",
                        codigo='VALOR_ZERO',
                        severidade='warning'
                    ))
    
    def _validar_uf(self, dados: Dict[str, Any]):
        """Valida UF"""
        uf = dados.get('UF')
        if uf:
            if not CampoValidator.validar_uf(uf):
                self.erros.append(ValidationError(
                    campo='UF',
                    mensagem=f"UF inválida: {uf}",
                    codigo='UF_INVALIDA',
                    severidade='error'
                ))
    
    def _validar_prazos(self, dados: Dict[str, Any]):
        """Valida campos de prazo"""
        prazo = dados.get('PRAZO CONTRATADO')
        
        if prazo:
            try:
                prazo_meses = int(prazo)
                
                # Verifica limite máximo (geralmente 360 meses = 30 anos)
                if prazo_meses > 360:
                    self.avisos.append(ValidationError(
                        campo='PRAZO CONTRATADO',
                        mensagem=f"Prazo superior a 30 anos: {prazo_meses} meses",
                        codigo='PRAZO_EXCEDIDO',
                        severidade='warning'
                    ))
                
                # Verifica mínimo
                if prazo_meses < 12:
                    self.avisos.append(ValidationError(
                        campo='PRAZO CONTRATADO',
                        mensagem=f"Prazo inferior a 12 meses: {prazo_meses}",
                        codigo='PRAZO_MINIMO',
                        severidade='warning'
                    ))
            
            except (ValueError, TypeError):
                self.erros.append(ValidationError(
                    campo='PRAZO CONTRATADO',
                    mensagem=f"Prazo inválido: {prazo}",
                    codigo='PRAZO_INVALIDO',
                    severidade='error'
                ))
    
    def _validar_taxas(self, dados: Dict[str, Any]):
        """Valida campos de taxa de juros"""
        taxa = dados.get('TAXA JUROS CONTRATADO')
        
        if taxa:
            try:
                taxa_decimal = Decimal(str(taxa))
                
                # Verifica se está em formato percentual razoável
                if taxa_decimal > 100:
                    self.avisos.append(ValidationError(
                        campo='TAXA JUROS CONTRATADO',
                        mensagem=f"Taxa de juros muito alta: {taxa}%",
                        codigo='TAXA_ALTA',
                        severidade='warning'
                    ))
                
                if taxa_decimal < 0:
                    self.erros.append(ValidationError(
                        campo='TAXA JUROS CONTRATADO',
                        mensagem=f"Taxa de juros negativa: {taxa}",
                        codigo='TAXA_NEGATIVA',
                        severidade='error'
                    ))
            
            except (InvalidOperation, ValueError):
                self.erros.append(ValidationError(
                    campo='TAXA JUROS CONTRATADO',
                    mensagem=f"Taxa de juros inválida: {taxa}",
                    codigo='TAXA_INVALIDA',
                    severidade='error'
                ))
    
    def _validar_consistencia(self, dados: Dict[str, Any]):
        """Valida consistência entre campos"""
        # Exemplo: Valor FCVS deve ser <= Valor Financiamento
        valor_financ = dados.get('VALOR FINANCIAMENTO CONTRATADO')
        valor_fcvs = dados.get('VALOR FINANC. PADRÃO FCVS')
        
        if valor_financ and valor_fcvs:
            try:
                val_financ = Decimal(str(valor_financ))
                val_fcvs = Decimal(str(valor_fcvs))
                
                if val_fcvs > val_financ:
                    self.avisos.append(ValidationError(
                        campo='VALOR FINANC. PADRÃO FCVS',
                        mensagem=f"Valor FCVS superior ao financiamento",
                        codigo='INCONSISTENCIA_VALORES',
                        severidade='warning'
                    ))
            except:
                pass


class CADMUTValidator:
    """Validador especializado para ficha CADMUT"""
    
    CAMPOS_OBRIGATORIOS = [
        'CPF',
        'NOME',
        'ENDERECO',
        'MUNICIPIO',
        'UF',
    ]
    
    def __init__(self):
        self.erros: List[ValidationError] = []
        self.avisos: List[ValidationError] = []
    
    def validar(self, dados: Dict[str, Any]) -> Tuple[bool, List[ValidationError]]:
        """Valida dados de ficha CADMUT"""
        self.erros = []
        self.avisos = []
        
        # Valida campos obrigatórios
        for campo in self.CAMPOS_OBRIGATORIOS:
            valor = dados.get(campo)
            if not valor or (isinstance(valor, str) and not valor.strip()):
                self.erros.append(ValidationError(
                    campo=campo,
                    mensagem=f"Campo obrigatório não preenchido",
                    codigo='CAMPO_OBRIGATORIO',
                    severidade='error'
                ))
        
        # Valida CPF
        cpf = dados.get('CPF')
        if cpf and not CampoValidator.validar_cpf(cpf):
            self.erros.append(ValidationError(
                campo='CPF',
                mensagem=f"CPF inválido: {cpf}",
                codigo='CPF_INVALIDO',
                severidade='error'
            ))
        
        # Valida UF
        uf = dados.get('UF')
        if uf and not CampoValidator.validar_uf(uf):
            self.erros.append(ValidationError(
                campo='UF',
                mensagem=f"UF inválida: {uf}",
                codigo='UF_INVALIDA',
                severidade='error'
            ))
        
        return (len(self.erros) == 0, self.erros + self.avisos)


class ArquivoValidator:
    """Validador de arquivo completo de fichas"""
    
    def __init__(self, tipo_ficha: str = 'FH1'):
        self.tipo_ficha = tipo_ficha
        self.validator = self._obter_validator(tipo_ficha)
    
    def _obter_validator(self, tipo: str):
        """Retorna o validador apropriado"""
        validators = {
            'FH1': FH1Validator,
            'CADMUT': CADMUTValidator,
        }
        
        validator_class = validators.get(tipo, FH1Validator)
        return validator_class()
    
    def validar_lote(self, fichas: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Valida um lote de fichas
        
        Args:
            fichas: Lista de dicionários com dados das fichas
        
        Returns:
            Dicionário com resultado da validação
        """
        resultado = {
            'total_fichas': len(fichas),
            'fichas_validas': 0,
            'fichas_com_erro': 0,
            'fichas_com_aviso': 0,
            'erros_por_ficha': {},
            'resumo_erros': {},
        }
        
        for i, ficha_dados in enumerate(fichas):
            valido, erros = self.validator.validar(ficha_dados)
            
            if valido and not erros:
                resultado['fichas_validas'] += 1
            else:
                # Separa erros de avisos
                erros_reais = [e for e in erros if e.severidade == 'error']
                avisos = [e for e in erros if e.severidade == 'warning']
                
                if erros_reais:
                    resultado['fichas_com_erro'] += 1
                    resultado['erros_por_ficha'][i+1] = [e.to_dict() for e in erros_reais]
                
                if avisos:
                    resultado['fichas_com_aviso'] += 1
                    if i+1 not in resultado['erros_por_ficha']:
                        resultado['erros_por_ficha'][i+1] = []
                    resultado['erros_por_ficha'][i+1].extend([e.to_dict() for e in avisos])
                
                # Conta tipos de erro
                for erro in erros:
                    codigo = erro.codigo or 'DESCONHECIDO'
                    resultado['resumo_erros'][codigo] = resultado['resumo_erros'].get(codigo, 0) + 1
        
        return resultado


# Funções auxiliares de alto nível

def validar_fh1(dados: Dict[str, Any]) -> Tuple[bool, List[Dict]]:
    """
    Valida dados de ficha FH1
    
    Args:
        dados: Dicionário com dados da ficha
    
    Returns:
        Tupla (válido, lista_de_erros_dict)
    """
    validator = FH1Validator()
    valido, erros = validator.validar(dados)
    return (valido, [e.to_dict() for e in erros])


def validar_cadmut(dados: Dict[str, Any]) -> Tuple[bool, List[Dict]]:
    """
    Valida dados de ficha CADMUT
    
    Args:
        dados: Dicionário com dados da ficha
    
    Returns:
        Tupla (válido, lista_de_erros_dict)
    """
    validator = CADMUTValidator()
    valido, erros = validator.validar(dados)
    return (valido, [e.to_dict() for e in erros])


def validar_lote_fichas(fichas: List[Dict[str, Any]], tipo: str = 'FH1') -> Dict:
    """
    Valida lote de fichas
    
    Args:
        fichas: Lista de dicionários com dados das fichas
        tipo: Tipo de ficha (FH1, CADMUT, etc)
    
    Returns:
        Dicionário com resultado da validação
    """
    validator = ArquivoValidator(tipo)
    return validator.validar_lote(fichas)


# Exemplo de uso
if __name__ == '__main__':
    print("🔍 Validadores de Fichas CEF")
    print("=" * 60)
    
    # Teste FH1 - dados válidos
    print("\n✅ Testando FH1 com dados válidos...")
    dados_validos = {
        'UFS': '35',
        'MAT. AG. FINANC. /DV': '123456',
        'N.º CONTRATO DO MUT. NO AGENTE': '0001234567890',
        'NOME DO MUT. PRINCIPAL': 'JOÃO DA SILVA',
        'CPF/CI': '12345678909',
        'DATA DE NASCIMENTO': '010180',
        'CODIGO DO MUNICÍPIO': '12345',
        'UF': 'SP',
        'ENDEREÇO DO IMÓVEL': 'RUA EXEMPLO, 123',
        'DATA DO CONTRATO': '150120',
        'VALOR FINANCIAMENTO CONTRATADO': 150000.00,
        'PRAZO CONTRATADO': 240,
        'TAXA JUROS CONTRATADO': 8.5,
    }
    
    valido, erros = validar_fh1(dados_validos)
    print(f"   Resultado: {'✅ VÁLIDO' if valido else '❌ INVÁLIDO'}")
    if erros:
        print(f"   Problemas encontrados: {len(erros)}")
        for erro in erros[:3]:
            print(f"      - {erro['campo']}: {erro['mensagem']}")
    
    # Teste FH1 - dados inválidos
    print("\n❌ Testando FH1 com dados inválidos...")
    dados_invalidos = {
        'UFS': '35',
        'MAT. AG. FINANC. /DV': '123456',
        'N.º CONTRATO DO MUT. NO AGENTE': '',  # Vazio
        'NOME DO MUT. PRINCIPAL': 'MARIA',
        'CPF/CI': '12345678900',  # CPF inválido
        'DATA DE NASCIMENTO': '320180',  # Data inválida
        'CODIGO DO MUNICÍPIO': '12345',
        'UF': 'XX',  # UF inválida
        'ENDEREÇO DO IMÓVEL': 'RUA TESTE',
        'DATA DO CONTRATO': '150120',
        'VALOR FINANCIAMENTO CONTRATADO': -1000,  # Valor negativo
        'PRAZO CONTRATADO': 500,  # Prazo muito longo
        'TAXA JUROS CONTRATADO': -5,  # Taxa negativa
    }
    
    valido, erros = validar_fh1(dados_invalidos)
    print(f"   Resultado: {'✅ VÁLIDO' if valido else '❌ INVÁLIDO'}")
    print(f"   Problemas encontrados: {len(erros)}")
    for erro in erros[:5]:
        severidade = '⚠️' if erro['severidade'] == 'warning' else '❌'
        print(f"      {severidade} {erro['campo']}: {erro['mensagem']}")
    
    # Teste CADMUT
    print("\n📋 Testando CADMUT...")
    dados_cadmut = {
        'CPF': '12345678909',
        'NOME': 'JOSE SANTOS',
        'ENDERECO': 'AV PAULISTA 1000',
        'MUNICIPIO': 'SAO PAULO',
        'UF': 'SP',
    }
    
    valido, erros = validar_cadmut(dados_cadmut)
    print(f"   Resultado: {'✅ VÁLIDO' if valido else '❌ INVÁLIDO'}")
    if erros:
        print(f"   Problemas: {len(erros)}")
    
    # Teste lote
    print("\n📦 Testando validação de lote...")
    lote = [dados_validos, dados_invalidos, dados_validos]
    resultado = validar_lote_fichas(lote, 'FH1')
    
    print(f"   Total de fichas: {resultado['total_fichas']}")
    print(f"   ✅ Fichas válidas: {resultado['fichas_validas']}")
    print(f"   ❌ Fichas com erro: {resultado['fichas_com_erro']}")
    print(f"   ⚠️  Fichas com aviso: {resultado['fichas_com_aviso']}")
    
    if resultado['resumo_erros']:
        print("\n   📊 Resumo de erros:")
        for codigo, qtd in sorted(resultado['resumo_erros'].items(), key=lambda x: x[1], reverse=True):
            print(f"      {codigo}: {qtd} ocorrência(s)")
    
    print("\n✅ Testes de validação concluídos!")
