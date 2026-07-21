from django.db import models


class Cliente(models.Model):
    # Campos do CRM
    nome_completo = models.CharField(max_length=150)
    cpf = models.CharField(max_length=14, unique=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    aprovado = models.BooleanField(default=False)

    def __str__(self):
        return self.nome_completo


class ConjuntoHabitacional(models.Model):
    conj = models.CharField(max_length=10)
    conjunto = models.CharField(max_length=10)
    contrato = models.CharField(max_length=20)
    conjseg = models.CharField(max_length=10)
    nome = models.CharField(max_length=100)
    nomeseg = models.CharField(max_length=100)
    qtd_mut = models.IntegerField()

    def __str__(self):
        return f"{self.nome} ({self.conjunto})"


class Mutuario(models.Model):
    codigo = models.CharField(max_length=10)
    codimovel = models.CharField(max_length=20)
    conjunto = models.CharField(max_length=10)
    conjseg = models.CharField(max_length=10)
    nome = models.CharField(max_length=100)
    ident = models.CharField(max_length=20)
    orgao = models.CharField(max_length=20)
    dtnasc = models.DateField(null=True)
    cpf = models.CharField(max_length=14)
    renda = models.FloatField(null=True)
    crenda = models.FloatField(null=True)
    endereco = models.CharField(max_length=150)
    numero = models.CharField(max_length=10)
    compl = models.CharField(max_length=50)
    tipoimovel = models.CharField(max_length=50)
    bairro = models.CharField(max_length=50)
    cidade = models.CharField(max_length=50)
    cep = models.CharField(max_length=10)
    uf = models.CharField(max_length=2)
    telefone = models.CharField(max_length=20, blank=True, default='')
    email = models.EmailField(max_length=100, blank=True, default='')

    # Normalized relationships (nullable for safe migration)
    endereco_fk = models.ForeignKey('Endereco', null=True, blank=True, on_delete=models.SET_NULL, related_name='mutuarios_endereco')
    conjunto_fk = models.ForeignKey('ConjuntoHabitacional', null=True, blank=True, on_delete=models.SET_NULL, related_name='mutuarios_conjunto')

    def __str__(self):
        return f"{self.nome} ({self.cpf})"


class Endereco(models.Model):
    endereco = models.CharField(max_length=150)
    numero = models.CharField(max_length=10)
    compl = models.CharField(max_length=50)
    bairro = models.CharField(max_length=50)
    cidade = models.CharField(max_length=50)
    cep = models.CharField(max_length=10)
    uf = models.CharField(max_length=2)

    def __str__(self):
        return f"{self.endereco}, {self.numero} - {self.bairro}"


class Movimentacao(models.Model):
    codigo = models.CharField(max_length=10)
    codimovel = models.CharField(max_length=10)
    conjunto = models.CharField(max_length=10)
    tipo = models.CharField(max_length=30)
    data = models.DateField(null=True, blank=True)
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    descricao = models.CharField(max_length=150)
    # Link to Mutuario if matched (nullable)
    mutuario_fk = models.ForeignKey('Mutuario', null=True, blank=True, on_delete=models.SET_NULL, related_name='movimentacoes_mutuario')

    def __str__(self):
        return f"{self.tipo} - {self.data} - R$ {self.valor}"


class Contrato(models.Model):
    codigo = models.CharField(max_length=20)
    conjunto = models.CharField(max_length=10, blank=True)
    ocorrencia = models.CharField(max_length=10, blank=True)  # TPZ, SET, SIT, LA2, LA3, PXN, LIQ, etc.
    chave = models.CharField(max_length=50, blank=True)
    lote = models.CharField(max_length=50, blank=True)
    sinal = models.CharField(max_length=50, blank=True)
    conversor = models.FloatField(null=True, blank=True)
    
    # Campos adicionais do CADMUT (para formato PRINTEVO)
    cod_imovel = models.CharField(max_length=20, blank=True)
    data_contrato = models.DateField(null=True, blank=True)
    data_primeiro_venc = models.DateField(null=True, blank=True)
    sa = models.CharField(max_length=10, blank=True)  # Sistema de Amortização
    tx_juros = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    prazo = models.IntegerField(null=True, blank=True)  # Prazo em meses
    cat_prof = models.CharField(max_length=10, blank=True)  # Categoria Profissional
    pr = models.CharField(max_length=10, blank=True)  # Programa

    # Campos financeiros (extraídos do contrato PDF ou CADMUT)
    vlfinanc = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)  # Valor financiado
    vlprop   = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)  # Valor do imóvel
    prestacao_inicial = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)  # Prestação inicial

    def __str__(self):
        return f"Contrato {self.codigo} ({self.conjunto})"


class ParcelaContrato(models.Model):
    contrato = models.ForeignKey('Contrato', on_delete=models.CASCADE, related_name='parcelas')
    nmens = models.IntegerField()  # installment number
    dtvenc = models.DateField(null=True, blank=True)
    dtpgto = models.DateField(null=True, blank=True)
    juros = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    amort = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    seguro = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    tca = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    fcvs = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    em = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    rp = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    cm = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    sddev = models.DecimalField(max_digits=24, decimal_places=2, null=True, blank=True)
    sddev_original = models.DecimalField(max_digits=24, decimal_places=2, null=True, blank=True)  # Valor original antes da conversão
    vlautent = models.DecimalField(max_digits=24, decimal_places=2, null=True, blank=True)
    seq = models.IntegerField(null=True, blank=True)
    lote = models.CharField(max_length=50, blank=True)
    sinal = models.CharField(max_length=50, blank=True)
    chave = models.CharField(max_length=100, blank=True)
    conversor = models.FloatField(null=True, blank=True)

    class Meta:
        unique_together = (('contrato', 'nmens'),)
        indexes = [
            models.Index(fields=['dtvenc'], name='parc_dtvenc_idx'),
            models.Index(fields=['contrato', 'dtvenc'], name='parc_cont_dtv_idx'),
        ]

    def __str__(self):
        return f"{self.contrato.codigo} - parcela {self.nmens}"


class AtendimentoCRM(models.Model):
    """Registro de atendimentos e follow-up por contrato."""

    TIPO_CONTATO_CHOICES = [
        ('TELEFONE', 'Telefone'),
        ('WHATSAPP', 'WhatsApp'),
        ('EMAIL', 'E-mail'),
        ('PRESENCIAL', 'Presencial'),
        ('OUTRO', 'Outro'),
    ]

    STATUS_CHOICES = [
        ('ABERTO', 'Aberto'),
        ('EM_ANDAMENTO', 'Em andamento'),
        ('CONCLUIDO', 'Concluido'),
    ]

    contrato = models.ForeignKey('Contrato', on_delete=models.CASCADE, related_name='atendimentos_crm')
    data_atendimento = models.DateTimeField(auto_now_add=True)
    tipo_contato = models.CharField(max_length=20, choices=TIPO_CONTATO_CHOICES, default='OUTRO')
    assunto = models.CharField(max_length=150)
    observacoes = models.TextField()
    acordo_novo = models.TextField(blank=True, default='')
    proximo_passo = models.TextField(blank=True, default='')
    data_retorno = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ABERTO')
    responsavel = models.CharField(max_length=100, blank=True, default='')
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-data_atendimento']
        verbose_name = 'Atendimento CRM'
        verbose_name_plural = 'Atendimentos CRM'

    def __str__(self):
        return f"{self.contrato.codigo} - {self.assunto} ({self.data_atendimento:%d/%m/%Y})"


class ValidacaoAI(models.Model):
    """
    Histórico de validações realizadas pelos agentes AI
    """
    TIPO_CHOICES = [
        ('FH1', 'Arquivo FH1 - Habilitação'),
        ('RCV', 'Arquivo RCV - Comprovação'),
    ]
    
    STATUS_CHOICES = [
        ('APROVADO', 'Aprovado'),
        ('REPROVADO', 'Reprovado'),
        ('ERRO', 'Erro na validação'),
    ]
    
    # Informações básicas
    tipo_arquivo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    contrato = models.ForeignKey('Contrato', on_delete=models.SET_NULL, null=True, blank=True, related_name='validacoes_ai')
    data_validacao = models.DateTimeField(auto_now_add=True)
    
    # Resultado
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    relatorio_completo = models.TextField()  # Relatório gerado pelos agentes
    erros_encontrados = models.TextField(blank=True)  # Lista de erros
    recomendacoes = models.TextField(blank=True)  # Recomendações dos agentes
    
    # Métricas
    tempo_execucao = models.FloatField(null=True, blank=True)  # segundos
    tamanho_arquivo = models.IntegerField(null=True, blank=True)  # bytes
    
    # Metadata
    agentes_utilizados = models.CharField(max_length=200, blank=True)  # Ex: "QA Engineer, Backend Engineer"
    
    # Auto-correção
    correcao_automatica = models.BooleanField(default=False)  # Se foi auto-corrigido
    correcoes_aplicadas = models.TextField(blank=True)  # Lista de correções feitas
    
    class Meta:
        ordering = ['-data_validacao']
        verbose_name = 'Validação AI'
        verbose_name_plural = 'Validações AI'
    
    def __str__(self):
        status_icon = '✅' if self.status == 'APROVADO' else '❌' if self.status == 'REPROVADO' else '⚠️'
        return f"{status_icon} {self.tipo_arquivo} - {self.data_validacao.strftime('%d/%m/%Y %H:%M')}"


class AprendizadoAI(models.Model):
    """
    OPÇÃO 2: Aprendizados e sugestões do Auto-Fix Engineer
    """
    # Quando foi identificado
    data_analise = models.DateTimeField(auto_now_add=True)
    
    # Padrão identificado
    tipo_erro = models.CharField(max_length=100)  # Ex: "HEADER_431_BYTES"
    ocorrencias = models.IntegerField(default=1)  # Quantas vezes foi visto
    
    # Análise do agente
    causa_raiz = models.TextField()  # Por que acontece
    sugestao_codigo = models.TextField()  # Como corrigir no código
    prevencao = models.TextField()  # Como evitar
    
    # Implementação
    implementado = models.BooleanField(default=False)  # Se já foi corrigido no código
    data_implementacao = models.DateTimeField(null=True, blank=True)
    arquivo_modificado = models.CharField(max_length=200, blank=True, null=True)  # Ex: "views.py"
    linha = models.CharField(max_length=50, blank=True, null=True)  # Ex: "1420-1450"
    comentario = models.TextField(blank=True, null=True)  # Observações sobre a implementação
    
    # Metadata
    arquivo_afetado = models.CharField(max_length=200, blank=True)  # Ex: "views.py linha 1234"
    prioridade = models.IntegerField(default=5)  # 1-10, quanto maior mais urgente
    
    class Meta:
        ordering = ['-prioridade', '-ocorrencias', '-data_analise']
        verbose_name = 'Aprendizado AI'
        verbose_name_plural = 'Aprendizados AI'
    
    def __str__(self):
        status = '✅' if self.implementado else '⏳'
        return f"{status} {self.tipo_erro} ({self.ocorrencias}x)"


# ===== MODELOS DE OCR REVIEW QUEUE =====

class OCRReviewQueue(models.Model):
    """
    Fila de revisão para extrações OCR.
    Cada contrato enviado via PDF gera uma entrada nesta fila.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pendente'),
        ('PARTIALLY_REVIEWED', 'Parcialmente Revisado'),
        ('APPROVED', 'Aprovado'),
        ('REJECTED', 'Rejeitado'),
    ]
    
    contrato = models.ForeignKey('Contrato', on_delete=models.CASCADE, related_name='ocr_review_queues')
    extraction_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Scores e métricas
    score = models.IntegerField(default=0)  # 0-100, confidence score
    auto_count = models.IntegerField(default=0)  # Quantidade de campos auto-aprovados
    revisar_count = models.IntegerField(default=0)  # Quantidade de campos a revisar
    
    # Campos faltantes críticos e importantes
    faltando_criticos = models.TextField(blank=True, default='')  # JSON list
    faltando_importantes = models.TextField(blank=True, default='')  # JSON list
    recuperados = models.TextField(blank=True, default='')  # JSON list
    
    # Metadata
    pdf_filename = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reviewed_by = models.CharField(max_length=100, blank=True, null=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-extraction_date']
        verbose_name = 'OCR Review Queue'
        verbose_name_plural = 'OCR Review Queues'
    
    def __str__(self):
        return f"OCR Review - {self.contrato.codigo} ({self.status})"
    
    def get_pending_items_count(self):
        return self.review_items.filter(status='PENDING_REVIEW').count()
    
    def get_approved_items_count(self):
        return self.review_items.filter(status='AUTO_APPROVED').count()


class ReviewQueueItem(models.Model):
    """
    Item individual de revisão dentro de uma fila OCR.
    Cada campo de cada contrato tem um item de revisão.
    """
    STATUS_CHOICES = [
        ('AUTO_APPROVED', 'Auto-Aprovado'),
        ('PENDING_REVIEW', 'Aguardando Revisão'),
        ('USER_CORRECTED', 'Corrigido pelo Usuário'),
        ('REJECTED', 'Rejeitado'),
    ]
    
    review_queue = models.ForeignKey('OCRReviewQueue', on_delete=models.CASCADE, related_name='review_items')
    field_name = models.CharField(max_length=100)  # Ex: 'prazo', 'data_primeiro_venc', 'tx_juros'
    
    # Valores
    value_extracted = models.TextField(blank=True)  # Valor original extraído via OCR
    value_approved = models.TextField(blank=True, null=True)  # Valor aprovado (auto ou user-corrected)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING_REVIEW')
    confidence_score = models.IntegerField(default=0)  # 0-100, confidence para este campo específico
    
    # Auditoria
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_by = models.CharField(max_length=100, blank=True, null=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Notas
    notes = models.TextField(blank=True, default='')  # Por que foi rejeitado, notas do revisor, etc.
    
    # Campo de tipo para facilitar filtragem
    field_type = models.CharField(max_length=50, blank=True)  # 'date', 'decimal', 'integer', 'string'
    
    class Meta:
        ordering = ['status', '-confidence_score', 'field_name']
        unique_together = (('review_queue', 'field_name'),)
        verbose_name = 'Review Queue Item'
        verbose_name_plural = 'Review Queue Items'
    
    def __str__(self):
        return f"{self.review_queue.contrato.codigo} - {self.field_name} ({self.status})"


# ===== MODELOS DE INTEGRAÇÃO CEF =====
# Importar modelos de integração CEF
from .models_cef import (
    RemessaCEF,
    CredencialCEF,
    EnvioCEF,
    RetornoCEF,
    AgendamentoEnvio,
    LogAutomacao
)

__all__ = [
    'Cliente', 'ConjuntoHabitacional', 'Mutuario', 'Endereco',
    'Movimentacao', 'Contrato', 'ParcelaContrato',
    'AtendimentoCRM',
    'ValidacaoAI', 'AprendizadoAI',
    'OCRReviewQueue', 'ReviewQueueItem',
    'RemessaCEF', 'CredencialCEF', 'EnvioCEF', 'RetornoCEF', 'AgendamentoEnvio', 'LogAutomacao'
]