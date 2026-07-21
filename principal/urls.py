# principal/urls.py

from django.urls import path
from . import views
from . import views_validators
from . import views_cef
from . import views_ocr
from . import views_qualidade

urlpatterns = [
    # Quando a URL for a raiz do App, chama a função 'index'
    path('', views.index, name='index'),
    path('cadmut/', views.cadmut, name='cadmut'),
    path('clientes/', views.clientes, name='clientes'),
    path('conjuntos/', views.conjuntos, name='conjuntos'),
    path('mutuarios/', views.mutuarios, name='mutuarios'),
    path('mutuario/<str:codigo>/', views.mutuario_detail, name='mutuario_detail'),
    path('mutuario/<str:codigo>/editar/', views.mutuario_editar, name='mutuario_editar'),
    path('enderecos/', views.enderecos, name='enderecos'),
    path('movimentacoes/', views.movimentacoes, name='movimentacoes'),
    path('contratos/', views.contratos, name='contratos'),
    path('contrato/<int:pk>/', views.contrato_detail, name='contrato_detail'),
    path('contrato/<int:pk>/crm/adicionar/', views.adicionar_atendimento_crm, name='adicionar_atendimento_crm'),
    path('contrato/<int:pk>/crm/importar/', views.importar_atendimentos_crm, name='importar_atendimentos_crm'),
    path('contrato/<int:pk>/crm/<int:atendimento_id>/editar/', views.editar_atendimento_crm, name='editar_atendimento_crm'),
    path('contrato/<int:pk>/crm/<int:atendimento_id>/excluir/', views.excluir_atendimento_crm, name='excluir_atendimento_crm'),
    path('contrato/<int:pk>/validar/', views_validators.validar_contrato_ajax, name='validar_contrato'),
    path('contrato/<int:pk>/editar/', views.contrato_editar, name='contrato_editar'),
    path('contrato/<str:codigo>/debito/', views.debito_prestacoes, name='debito_prestacoes'),
    path('contrato/<str:codigo>/parcelas-pagas/', views.parcelas_pagas, name='parcelas_pagas'),
    path('contrato/<int:pk>/exportar-evolucao-txt/', views.exportar_evolucao_txt, name='exportar_evolucao_txt'),
    path('contrato/<int:pk>/cadastrar-mutuario/', views.cadastrar_mutuario, name='cadastrar_mutuario'),
    path('contratos-sem-mutuario/', views.contratos_sem_mutuario, name='contratos_sem_mutuario'),
    path('atualizacao-monetaria/', views.atualizacao_monetaria, name='atualizacao_monetaria'),
    path('amortizacao-negativa/', views.amortizacao_negativa, name='amortizacao_negativa'),
    path('relatorio-debitos/', views.relatorio_debitos, name='relatorio_debitos'),
    path('seguro/relatorio-dividas/', views.relatorio_divida_seguro, name='relatorio_divida_seguro'),
    path('seguro/relatorio-dividas/visualizar/<str:filename>/', views.visualizar_relatorio_divida_seguro, name='visualizar_relatorio_divida_seguro'),
    path('seguro/relatorio-dividas/download/<str:filename>/', views.download_relatorio_divida_seguro, name='download_relatorio_divida_seguro'),
    path('seguro/relatorio-dividas/exportar-excel/', views.relatorio_divida_seguro, name='exportar_excel_resumo_seguro'),
    path('fcvs/', views.fcvs, name='fcvs'),
    path('fcvs/contribuicao/', views.fcvs_contribuicao, name='fcvs_contribuicao'),
    path('relatorio-caixa/', views.relatorio_caixa, name='relatorio_caixa'),
    path('contrato/<int:pk>/relatorio-fh1/', views.relatorio_fh1, name='relatorio_fh1'),
    path('contrato/<int:pk>/fh1-completo/', views.fh1_completo, name='fh1_completo'),
    path('carteira-fcvs/', views.carteira_fcvs, name='carteira_fcvs'),
    path('integracao-cef/', views.integracao_cef, name='integracao_cef'),
    path('rcv/gerar/', views.gerar_arquivo_rcv, name='gerar_arquivo_rcv'),
    path('ai-agents/test/', views.testar_ai_agents, name='testar_ai_agents'),
    path('validacoes-ai/', views.validacoes_ai, name='validacoes_ai'),
    path('validacoes-ai/<int:validacao_id>/', views.validacao_ai_detail, name='validacao_ai_detail'),
    path('aprendizados-ai/', views.aprendizados_ai, name='aprendizados_ai'),
    path('aprendizados-ai/<int:aprendizado_id>/implementar/', views.implementar_aprendizado, name='implementar_aprendizado'),
    path('aprendizados-ai/<int:aprendizado_id>/detalhes/', views.detalhes_aprendizado, name='detalhes_aprendizado'),
    path('analisar-padroes/', views.analisar_padroes_ai, name='analisar_padroes_ai'),
    
    # CEF Integration URLs
    path('cef/', views_cef.integracao_cef, name='integracao_cef'),
    path('cef/envios/', views_cef.listar_envios_cef, name='listar_envios_cef'),
    path('cef/envios/<int:contrato_id>/criar/', views_cef.criar_envio_fh1, name='criar_envio_fh1'),
    path('cef/envio/<int:envio_id>/processar/', views_cef.processar_envio_automatico, name='processar_envio_automatico'),
    path('cef/retornos/', views_cef.listar_retornos_cef, name='listar_retornos_cef'),
    path('cef/retorno/<int:retorno_id>/marcar-lido/', views_cef.marcar_retorno_lido, name='marcar_retorno_lido'),
    path('cef/retornos/verificar/', views_cef.verificar_retornos, name='verificar_retornos'),
    path('cef/agendamentos/', views_cef.listar_agendamentos, name='listar_agendamentos'),
    path('cef/agendamento/criar/', views_cef.criar_agendamento, name='criar_agendamento'),
    path('cef/agendamento/<int:agendamento_id>/executar/', views_cef.executar_agendamento, name='executar_agendamento'),
    path('cef/credenciais/', views_cef.configurar_credenciais_cef, name='configurar_credenciais_cef'),
    path('cef/credentials/', views_cef.configurar_credenciais_cef, name='configurar_credenciais_cef_en'),  # Alias em inglês
    path('cef/logs/', views_cef.logs_automacao_original, name='logs_automacao'),
    
    # Novas URLs - Geração e Validação de Fichas
    path('cef/gerar/<int:contrato_id>/', views_cef.gerar_ficha_view, name='gerar_ficha_cef'),
    path('cef/validar/', views_cef.validar_ficha_view, name='validar_ficha_cef'),
    path('cef/interpretar/', views_cef.interpretar_retorno_view, name='interpretar_retorno_cef'),
    path('cef/relatorios/upload/', views_cef.processar_relatorios_cef_upload, name='processar_relatorios_cef_upload'),
    path('cef/relatorios/upload/exportar-csv/', views_cef.exportar_relatorios_cef_csv, name='exportar_relatorios_cef_csv'),
    path('cef/retornos/lote/', views_cef.processar_retornos_cef_lote_view, name='processar_retornos_cef_lote'),
    path('cef/api/selecao/<int:contrato_id>/', views_cef.selecao_automatica_api, name='selecao_automatica_api'),
    path('cef/download/lote/', views_cef.download_arquivo_lote, name='download_arquivo_lote'),
    path('cef/download/lote/arquivo/', views_cef.download_ultimo_lote_manual, name='download_ultimo_lote_manual'),
    path('cef/p3026/', views_cef.processar_p3026_view, name='processar_p3026'),
    path('cef/p3026/visualizar/', views_cef.visualizar_p3026, name='visualizar_p3026'),
    
    # Envio de Movimentos FCVS/CADMUT
    path('cef/enviar-movimentos/', views_cef.enviar_movimento_fcvs_view, name='enviar_movimentos'),
    path('cef/defesa-reversibilidade/', views_cef.gerar_remessa_defesa_reversibilidade, name='gerar_remessa_defesa_reversibilidade'),
    path('cef/enviar-lote-automatico/', views_cef.enviar_lote_automatico, name='enviar_lote_automatico'),
    path('cef/remessa/<int:remessa_id>/status/', views_cef.status_remessa_cef, name='status_remessa_cef'),
    path('cef/remessa/<int:remessa_id>/arquivo/<str:tipo>/', views_cef.download_remessa_arquivo, name='download_remessa_arquivo'),
    
    # M460xxx - Irregularidades CEF
    path('cef/m460/', views_cef.processar_m460_view, name='processar_m460'),
    path('cef/m460/exportar/<str:tipo_arquivo>/', views_cef.exportar_m460_excel, name='exportar_m460_excel'),
    path('cef/m460/comparar/', views_cef.comparar_m460_view, name='comparar_m460'),
    
    # Qualidade de Contratos
    path('qualidade/', views_qualidade.painel_qualidade, name='painel_qualidade'),
    path('contrato/<int:pk>/qualidade/', views_qualidade.inspecionar_contrato, name='inspecionar_contrato'),
    path('api/contrato/<int:pk>/qualidade/', views_qualidade.api_inspecionar_contrato, name='api_inspecionar_contrato'),

    # OCR - Cadastro Automático de Contratos
    path('ocr/upload/', views_ocr.upload_contrato_pdf, name='upload_contrato_pdf'),
    path('ocr/listar/', views_ocr.listar_contratos_ocr, name='listar_contratos_ocr'),
    path('ocr/relatorio/', views_ocr.relatorio_processamento_ocr, name='relatorio_processamento_ocr'),
    path('ocr/review-dashboard/', views_ocr.ocr_review_dashboard, name='ocr_review_dashboard'),
    path('api/ocr/processar-lote/', views_ocr.api_processar_lote_contratos, name='api_processar_lote_contratos'),
    
    # OCR Review Queue API
    path('api/ocr-review/pending/', views_ocr.api_ocr_review_queue_list_pending, name='api_ocr_review_queue_list_pending'),
    path('api/ocr-review/<int:queue_id>/', views_ocr.api_ocr_review_queue_detail, name='api_ocr_review_queue_detail'),
    path('api/ocr-review/<int:queue_id>/approve-field/<str:field_name>/', views_ocr.api_ocr_review_queue_approve_field, name='api_ocr_review_queue_approve_field'),
    path('api/ocr-review/<int:queue_id>/reject-field/<str:field_name>/', views_ocr.api_ocr_review_queue_reject_field, name='api_ocr_review_queue_reject_field'),
    path('api/ocr-review/<int:queue_id>/bulk-approve/', views_ocr.api_ocr_review_queue_bulk_approve, name='api_ocr_review_queue_bulk_approve'),
]
