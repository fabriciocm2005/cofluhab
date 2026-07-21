# principal/validators.py
# Opção 3: Validação Preventiva
# Valida dados ANTES de gerar arquivo CEF

from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date, datetime, timedelta


class ValidacaoPreventiva:
    """
    Valida dados do contrato ANTES de gerar arquivo CEF.
    Retorna lista de erros e warnings para exibir ao usuário.
    """
    
    def __init__(self, contrato):
        self.contrato = contrato
        self.erros = []
        self.warnings = []
        self.info = []
    
    def validar_completo(self):
        """Executa todas as validações"""
        self.validar_dados_basicos()
        self.validar_mutuario()
        self.validar_datas()
        self.validar_valores()
        self.validar_endereco()
        self.validar_parcelas()
        
        return {
            'valido': len(self.erros) == 0,
            'erros': self.erros,
            'warnings': self.warnings,
            'info': self.info,
            'total_problemas': len(self.erros) + len(self.warnings)
        }
    
    def validar_dados_basicos(self):
        """Valida campos obrigatórios do contrato"""
        if not self.contrato.codigo:
            self.erros.append({
                'campo': 'codigo',
                'mensagem': 'Contrato sem código definido',
                'criticidade': 'CRÍTICO',
                'sugestao': 'Defina um código para o contrato'
            })
        
        if not self.contrato.conjunto:
            self.warnings.append({
                'campo': 'conjunto',
                'mensagem': 'Contrato sem conjunto definido',
                'criticidade': 'ALERTA',
                'sugestao': 'Defina o conjunto habitacional'
            })
        
        if not self.contrato.data_contrato:
            self.warnings.append({
                'campo': 'data_contrato',
                'mensagem': 'Data de contrato não informada',
                'criticidade': 'ALERTA',
                'sugestao': 'Informe a data do contrato'
            })
    
    def validar_mutuario(self):
        """Valida dados do mutuário"""
        try:
            # Buscar mutuário via tabela de relacionamento
            from principal.models import Mutuario
            import sqlite3
            import os
            
            mutuario = None
            try:
                db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db.sqlite3')
                conn = sqlite3.connect(db_path)
                cur = conn.cursor()
                cur.execute("SELECT mutuario_id FROM contrato_mutuario_map WHERE contrato_id = ?", (self.contrato.id,))
                result = cur.fetchone()
                if result:
                    mutuario = Mutuario.objects.get(id=result[0])
                conn.close()
            except:
                pass
            
            if not mutuario:
                self.erros.append({
                    'campo': 'mutuario',
                    'mensagem': 'Contrato sem mutuário vinculado',
                    'criticidade': 'CRÍTICO',
                    'sugestao': 'Cadastre ou vincule um mutuário ao contrato'
                })
                return
            
            # Validar CPF
            if not mutuario.cpf:
                self.warnings.append({
                    'campo': 'mutuario.cpf',
                    'mensagem': f'Mutuário {mutuario.nome} sem CPF cadastrado',
                    'criticidade': 'ALERTA',
                    'sugestao': 'Cadastre o CPF do mutuário'
                })
            elif len(mutuario.cpf.replace('.', '').replace('-', '')) != 11:
                self.erros.append({
                    'campo': 'mutuario.cpf',
                    'mensagem': f'CPF inválido: {mutuario.cpf}',
                    'criticidade': 'CRÍTICO',
                    'sugestao': 'Corrija o CPF (deve ter 11 dígitos)'
                })
            
            # Validar nome
            if not mutuario.nome or len(mutuario.nome.strip()) < 3:
                self.warnings.append({
                    'campo': 'mutuario.nome',
                    'mensagem': 'Nome do mutuário muito curto ou vazio',
                    'criticidade': 'ALERTA',
                    'sugestao': 'Informe o nome completo do mutuário'
                })
        
        except Exception as e:
            self.erros.append({
                'campo': 'mutuario',
                'mensagem': f'Erro ao validar mutuário: {str(e)}',
                'criticidade': 'CRÍTICO',
                'sugestao': 'Verifique os dados do mutuário'
            })
    
    def validar_datas(self):
        """Valida datas do contrato"""
        hoje = date.today()
        
        # Data de contrato
        if self.contrato.data_contrato:
            if self.contrato.data_contrato > hoje:
                self.warnings.append({
                    'campo': 'data_contrato',
                    'mensagem': f'Data de contrato no futuro: {self.contrato.data_contrato}',
                    'criticidade': 'ALERTA',
                    'sugestao': 'Verifique se a data está correta'
                })
            
            # Muito antiga (mais de 50 anos)
            if (hoje - self.contrato.data_contrato).days > 365 * 50:
                self.warnings.append({
                    'campo': 'data_contrato',
                    'mensagem': f'Contrato muito antigo: {self.contrato.data_contrato}',
                    'criticidade': 'INFO',
                    'sugestao': 'Verifique se a data está correta'
                })
        
        # Data primeiro vencimento
        if self.contrato.data_primeiro_venc:
            if self.contrato.data_primeiro_venc > hoje + timedelta(days=365):
                self.warnings.append({
                    'campo': 'data_primeiro_venc',
                    'mensagem': 'Primeiro vencimento muito distante no futuro',
                    'criticidade': 'ALERTA',
                    'sugestao': 'Verifique a data do primeiro vencimento'
                })
    
    def validar_valores(self):
        """Valida valores monetários"""
        # Taxa de juros
        if self.contrato.tx_juros:
            if self.contrato.tx_juros < 0:
                self.erros.append({
                    'campo': 'tx_juros',
                    'mensagem': f'Taxa de juros negativa: {self.contrato.tx_juros}',
                    'criticidade': 'CRÍTICO',
                    'sugestao': 'Corrija a taxa de juros'
                })
            elif self.contrato.tx_juros > 50:
                self.warnings.append({
                    'campo': 'tx_juros',
                    'mensagem': f'Taxa de juros muito alta: {self.contrato.tx_juros}%',
                    'criticidade': 'ALERTA',
                    'sugestao': 'Verifique se a taxa está correta'
                })
        
        # Prazo
        if self.contrato.prazo:
            if self.contrato.prazo <= 0:
                self.erros.append({
                    'campo': 'prazo',
                    'mensagem': f'Prazo inválido: {self.contrato.prazo} meses',
                    'criticidade': 'CRÍTICO',
                    'sugestao': 'Corrija o prazo do contrato'
                })
            elif self.contrato.prazo > 600:  # 50 anos
                self.warnings.append({
                    'campo': 'prazo',
                    'mensagem': f'Prazo muito longo: {self.contrato.prazo} meses',
                    'criticidade': 'ALERTA',
                    'sugestao': 'Verifique o prazo do contrato'
                })
    
    def validar_endereco(self):
        """Valida dados de endereço"""
        # Por enquanto só info
        self.info.append({
            'campo': 'endereco',
            'mensagem': 'Validação de endereço não implementada nesta versão',
            'criticidade': 'INFO',
            'sugestao': ''
        })
    
    def validar_parcelas(self):
        """Valida parcelas do contrato"""
        try:
            parcelas = self.contrato.parcelas.all()
            
            if not parcelas.exists():
                self.info.append({
                    'campo': 'parcelas',
                    'mensagem': 'Contrato sem parcelas cadastradas',
                    'criticidade': 'INFO',
                    'sugestao': 'Recomendado: cadastre as parcelas para melhor controle'
                })
            else:
                # Info sobre total de parcelas
                self.info.append({
                    'campo': 'parcelas',
                    'mensagem': f'{parcelas.count()} parcelas cadastradas',
                    'criticidade': 'INFO',
                    'sugestao': ''
                })
        
        except Exception as e:
            self.info.append({
                'campo': 'parcelas',
                'mensagem': f'Erro ao validar parcelas: {str(e)}',
                'criticidade': 'INFO',
                'sugestao': ''
            })


def validar_antes_exportar(contrato):
    """
    Atalho para validar contrato antes de exportar.
    Retorna dicionário com resultado da validação.
    """
    validador = ValidacaoPreventiva(contrato)
    return validador.validar_completo()


def pode_exportar(contrato):
    """
    Verifica se contrato pode ser exportado (não tem erros críticos).
    Retorna: (pode_exportar: bool, motivo: str)
    """
    resultado = validar_antes_exportar(contrato)
    
    if resultado['valido']:
        return (True, '')
    else:
        erros_criticos = [e for e in resultado['erros'] if e['criticidade'] == 'CRÍTICO']
        return (False, f"{len(erros_criticos)} erro(s) crítico(s) impedem a exportação")
