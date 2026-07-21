"""
Modelos para integração com CEF SIWFC
Rastreamento de envios, retornos e credenciais
"""

from django.db import models
from django.utils import timezone
from .models import Contrato


class CredencialCEF(models.Model):
    """Credenciais para acesso ao portal SIWFC"""
    
    cpf = models.CharField(max_length=11, unique=True)
    email = models.EmailField()
    senha_criptografada = models.CharField(max_length=256)  # Armazenar hash, não senha real
    matricula_agente = models.CharField(max_length=20)
    ativo = models.BooleanField(default=True)
    
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    ultimo_acesso = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Credencial CEF'
        verbose_name_plural = 'Credenciais CEF'
    
    def __str__(self):
        return f"CEF: {self.cpf} - {self.matricula_agente}"


class EnvioCEF(models.Model):
    """Registro de envios ao portal SIWFC"""
    
    TIPO_ENVIO_CHOICES = [
        ('FH1', 'FH1 - Ficha de Habilitação'),
        ('RNV', 'RNV - Relação de Não Validados'),
        ('RCV', 'RCV - Registro de Comprovação'),
        ('DOSSIE', 'Dossiê Digitalizado'),
        ('CADMUT', 'Cadastro de Mutuário'),
        ('DEFESA_REV', 'Defesa de Reversibilidade'),
        ('COMPLEMENTAR', 'Documentação Complementar'),
    ]
    
    STATUS_CHOICES = [
        ('GERADO', '📦 Gerado'),
        ('PENDENTE', '⏳ Pendente'),
        ('PROCESSANDO', '🔄 Processando'),
        ('ENVIADO', '✅ Enviado'),
        ('ERRO', '❌ Erro'),
        ('RETORNO_RECEBIDO', '📥 Retorno Recebido'),
    ]
    
    contrato = models.ForeignKey(Contrato, on_delete=models.CASCADE, related_name='envios_cef')
    remessa = models.ForeignKey('RemessaCEF', on_delete=models.SET_NULL, null=True, blank=True, related_name='envios')
    tipo_envio = models.CharField(max_length=20, choices=TIPO_ENVIO_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDENTE')
    
    # Informações do envio
    arquivo_enviado = models.CharField(max_length=500)  # Path do arquivo
    tamanho_bytes = models.IntegerField(default=0)
    hash_arquivo = models.CharField(max_length=64, blank=True)  # SHA256 para verificação
    
    # Dados do portal
    protocolo_cef = models.CharField(max_length=100, blank=True)  # Número de protocolo retornado
    codigo_contrato_cef = models.CharField(max_length=50, blank=True)
    
    # Timestamps
    data_envio = models.DateTimeField(null=True, blank=True)
    data_processamento = models.DateTimeField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    
    # Logs
    log_envio = models.TextField(blank=True)
    mensagem_erro = models.TextField(blank=True)
    
    # Automação
    enviado_automaticamente = models.BooleanField(default=False)
    tentativas = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Envio CEF'
        verbose_name_plural = 'Envios CEF'
    
    def __str__(self):
        return f"{self.tipo_envio} - {self.contrato.codigo} ({self.get_status_display()})"


class RetornoCEF(models.Model):
    """Retornos recebidos do portal SIWFC"""
    
    TIPO_RETORNO_CHOICES = [
        ('APROVADO', '✅ Aprovado'),
        ('REJEITADO', '❌ Rejeitado'),
        ('PENDENTE', '⏳ Pendente Análise'),
        ('COMPLEMENTAR', '📋 Documentação Complementar'),
        ('OFICIO', '📨 Ofício/Comunicado'),
    ]
    
    envio = models.ForeignKey(EnvioCEF, on_delete=models.CASCADE, related_name='retornos', null=True, blank=True)
    contrato = models.ForeignKey(Contrato, on_delete=models.CASCADE, related_name='retornos_cef')
    
    tipo_retorno = models.CharField(max_length=20, choices=TIPO_RETORNO_CHOICES)
    protocolo = models.CharField(max_length=100)
    
    # Arquivo de retorno
    arquivo_retorno = models.CharField(max_length=500, blank=True)
    conteudo = models.TextField(blank=True)
    
    # Informações da análise
    analise_cef = models.TextField(blank=True)
    motivo_rejeicao = models.TextField(blank=True)
    documentos_solicitados = models.TextField(blank=True)
    
    # Timestamps
    data_retorno = models.DateTimeField()
    data_processamento_local = models.DateTimeField(auto_now_add=True)
    data_leitura = models.DateTimeField(null=True, blank=True)
    
    # Flags
    lido = models.BooleanField(default=False)
    requer_acao = models.BooleanField(default=False)
    processado = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-data_retorno']
        verbose_name = 'Retorno CEF'
        verbose_name_plural = 'Retornos CEF'
    
    def __str__(self):
        return f"Retorno {self.protocolo} - {self.get_tipo_retorno_display()}"


class RemessaCEF(models.Model):
    """Controle de remessas em bloco para envio automático ao SIWFC"""

    STATUS_CHOICES = [
        ('PENDENTE', '⏳ Pendente'),
        ('PROCESSANDO', '🔄 Processando'),
        ('ENVIADO', '✅ Enviado'),
        ('ERRO', '❌ Erro'),
    ]

    tipo_envio = models.CharField(max_length=20, choices=EnvioCEF.TIPO_ENVIO_CHOICES, default='FH1')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDENTE')

    numero_lote = models.CharField(max_length=10, blank=True)
    matricula_agente = models.CharField(max_length=20, blank=True)
    protocolo_cef = models.CharField(max_length=100, blank=True)

    total_contratos = models.IntegerField(default=0)
    total_fichas = models.IntegerField(default=0)
    envios_sucesso = models.IntegerField(default=0)
    envios_erro = models.IntegerField(default=0)

    arquivo_header = models.CharField(max_length=500, blank=True)
    arquivo_dados = models.CharField(max_length=500, blank=True)

    log_processamento = models.TextField(blank=True)
    mensagem_erro = models.TextField(blank=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    iniciado_em = models.DateTimeField(null=True, blank=True)
    finalizado_em = models.DateTimeField(null=True, blank=True)

    criado_por = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Remessa CEF'
        verbose_name_plural = 'Remessas CEF'

    def __str__(self):
        return f"Remessa {self.id} - Lote {self.numero_lote} ({self.get_status_display()})"


class AgendamentoEnvio(models.Model):
    """Agendamento de envios automáticos"""
    
    FREQUENCIA_CHOICES = [
        ('UNICO', 'Envio Único'),
        ('DIARIO', 'Diário'),
        ('SEMANAL', 'Semanal'),
        ('MENSAL', 'Mensal'),
    ]
    
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    
    # Configuração
    tipo_envio = models.CharField(max_length=20, choices=EnvioCEF.TIPO_ENVIO_CHOICES)
    frequencia = models.CharField(max_length=20, choices=FREQUENCIA_CHOICES, default='UNICO')
    
    # Filtros (JSON para flexibilidade)
    filtros_contratos = models.TextField(blank=True, help_text="JSON com filtros para selecionar contratos")
    
    # Agendamento
    proxima_execucao = models.DateTimeField()
    ultima_execucao = models.DateTimeField(null=True, blank=True)
    
    # Status
    ativo = models.BooleanField(default=True)
    total_envios = models.IntegerField(default=0)
    envios_sucesso = models.IntegerField(default=0)
    envios_erro = models.IntegerField(default=0)
    
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['proxima_execucao']
        verbose_name = 'Agendamento de Envio'
        verbose_name_plural = 'Agendamentos de Envios'
    
    def __str__(self):
        return f"{self.nome} - {self.get_frequencia_display()}"


class LogAutomacao(models.Model):
    """Log de execuções da automação"""
    
    TIPO_ACAO_CHOICES = [
        ('LOGIN', '🔐 Login'),
        ('ENVIO', '📤 Envio'),
        ('DOWNLOAD', '📥 Download'),
        ('LOGOUT', '👋 Logout'),
        ('ERRO', '❌ Erro'),
    ]
    
    tipo_acao = models.CharField(max_length=20, choices=TIPO_ACAO_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Detalhes
    descricao = models.TextField()
    duracao_segundos = models.FloatField(null=True, blank=True)
    sucesso = models.BooleanField(default=True)
    
    # Contexto
    envio = models.ForeignKey(EnvioCEF, on_delete=models.CASCADE, null=True, blank=True, related_name='logs')
    agendamento = models.ForeignKey(AgendamentoEnvio, on_delete=models.CASCADE, null=True, blank=True, related_name='logs')
    
    # Dados técnicos
    screenshot = models.CharField(max_length=500, blank=True)
    traceback = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Log de Automação'
        verbose_name_plural = 'Logs de Automação'
    
    def __str__(self):
        return f"{self.get_tipo_acao_display()} - {self.timestamp.strftime('%d/%m/%Y %H:%M')}"
