"""
Views para processamento OCR de contratos no Django
"""

import os
import json
import logging
import tempfile
from pathlib import Path
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
from ocr_contrato_processor import ContratoOCRExtractor, ContratoProcessor, ProcessadorLoteContratos
from principal.ocr_hibrido import analisar_ocr_hibrido
from principal.models import Contrato, Mutuario, ConjuntoHabitacional, OCRReviewQueue, ReviewQueueItem

logger = logging.getLogger(__name__)


def criar_fila_revisao_ocr(contrato, dados_ocr, relatorio_hibrido, pdf_filename=''):
    """
    Cria uma fila de revisão OCR com items para cada campo híbrido.
    
    Args:
        contrato: Objeto Contrato
        dados_ocr: Dicionário com dados extraídos
        relatorio_hibrido: Dicionário retornado por analisar_ocr_hibrido()
        pdf_filename: Nome do arquivo PDF
    
    Returns:
        Objeto OCRReviewQueue criado
    """
    try:
        import json
        
        # Cria fila
        fila = OCRReviewQueue.objects.create(
            contrato=contrato,
            score=relatorio_hibrido.get('score', 0),
            auto_count=relatorio_hibrido.get('qtd_auto', 0),
            revisar_count=relatorio_hibrido.get('qtd_revisar', 0),
            faltando_criticos=json.dumps(relatorio_hibrido.get('faltando_criticos', [])),
            faltando_importantes=json.dumps(relatorio_hibrido.get('faltando_importantes', [])),
            recuperados=json.dumps(list(relatorio_hibrido.get('recuperados', {}).keys()) if isinstance(relatorio_hibrido.get('recuperados'), dict) else relatorio_hibrido.get('recuperados', [])),
            pdf_filename=pdf_filename,
            status='PARTIALLY_REVIEWED' if relatorio_hibrido.get('qtd_revisar', 0) > 0 else 'APPROVED'
        )
        
        # Cria items para cada campo extraído
        campos_tipo = {
            'data_contrato': 'date',
            'data_primeiro_venc': 'date',
            'data_pagto': 'date',
            'dtvenc': 'date',
            'prazo': 'integer',
            'tx_juros': 'decimal',
            'vlfinanc': 'decimal',
            'vlprop': 'decimal',
            'prestacao_inicial': 'decimal',
            'juros': 'decimal',
            'amort': 'decimal',
            'sddev': 'decimal',
        }
        
        # Campos que vieram como AUTO_APPROVED
        campos_auto = relatorio_hibrido.get('campos_auto', [])
        campos_revisar = relatorio_hibrido.get('campos_revisar', [])
        
        # Cria items para campos auto-aprovados
        for field_info in campos_auto:
            field_name = field_info.get('campo', '')
            ReviewQueueItem.objects.create(
                review_queue=fila,
                field_name=field_name,
                value_extracted=str(field_info.get('valor', '')),
                value_approved=str(field_info.get('valor', '')),
                status='AUTO_APPROVED',
                confidence_score=int(field_info.get('confianca', 100) * 100),  # Converter para 0-100
                field_type=campos_tipo.get(field_name, 'string'),
                notes=f"Auto-aprovado - {field_info.get('motivo', '')} (confiança: {field_info.get('confianca', 1.0) * 100:.0f}%)"
            )
        
        # Cria items para campos que precisam revisão
        for field_info in campos_revisar:
            field_name = field_info.get('campo', '')
            ReviewQueueItem.objects.create(
                review_queue=fila,
                field_name=field_name,
                value_extracted=str(field_info.get('valor', '')),
                value_approved=None,
                status='PENDING_REVIEW',
                confidence_score=int(field_info.get('confianca', 0) * 100),  # Converter para 0-100
                field_type=campos_tipo.get(field_name, 'string'),
                notes=f"Aguarda revisão - {field_info.get('motivo', '')} (confiança: {field_info.get('confianca', 0) * 100:.0f}%)"
            )
        
        logger.info(f"Fila de revisão criada para contrato {contrato.codigo}: {fila.auto_count} auto, {fila.revisar_count} revisar")
        return fila
    
    except Exception as e:
        logger.error(f"Erro ao criar fila de revisão OCR: {str(e)}")
        return None


def criar_ou_atualizar_mutuario(dados_contrato: dict) -> Mutuario:
    """
    Cria ou atualiza mutuário do contrato.
    O mutuário é vinculado ao contrato via mutuario.codigo == contrato.codigo.
    """
    codigo_contrato = dados_contrato.get('codigo', '').strip()
    if not codigo_contrato:
        return None

    # Tenta encontrar por CPF (mais confiável) ou por código do contrato
    mutuario = None
    if dados_contrato.get('cpf'):
        mutuario = Mutuario.objects.filter(cpf=dados_contrato['cpf']).first()
    if not mutuario:
        mutuario = Mutuario.objects.filter(codigo=codigo_contrato[:10]).first()
    if not mutuario:
        mutuario = Mutuario()

    # codigo sempre aponta para o contrato (chave de ligação usada em contrato_detail)
    mutuario.codigo = codigo_contrato[:10]

    # Preenche nome: usa o extraído ou placeholder
    nome_extraido = dados_contrato.get('nome', '').strip()
    nome_atual = (getattr(mutuario, 'nome', '') or '').strip()
    nome_atual_ruim = (
        ',' in nome_atual.lower() or
        any(token in nome_atual.lower() for token in ['mede', 'segmentos', 'linha reta', 'curva', 'marco', 'divide esta area'])
    )

    if nome_extraido and len(nome_extraido) >= 3:
        mutuario.nome = nome_extraido[:100]
    elif not mutuario.pk or not mutuario.nome or nome_atual_ruim:
        mutuario.nome = f'MUTUARIO-{codigo_contrato}'[:100]

    # Todos os demais campos opcionais
    campos_map = {
        'cpf': 'cpf',
        'ident': 'ident',
        'orgao': 'orgao',
        'dtnasc': 'dtnasc',
        'endereco': 'endereco',
        'numero': 'numero',
        'compl': 'compl',
        'bairro': 'bairro',
        'cidade': 'cidade',
        'cep': 'cep',
        'uf': 'uf',
        'telefone': 'telefone',
        'email': 'email',
        'renda': 'renda',
        'crenda': 'crenda',
        'codimovel': 'codimovel',
        'conjseg': 'conjseg',
        'tipoimovel': 'tipoimovel',
    }
    for campo_pdf, campo_model in campos_map.items():
        val = dados_contrato.get(campo_pdf)
        if val:
            setattr(mutuario, campo_model, val)

    # conjunto (herdado do contrato se não vier no PDF)
    conj = dados_contrato.get('conjunto', '')
    if conj:
        mutuario.conjunto = conj[:10]
    elif not mutuario.pk:
        mutuario.conjunto = ''

    # Garante campos obrigatórios com defaults
    for campo, default in [('cpf',''), ('ident',''), ('orgao',''), ('endereco',''),
                            ('numero',''), ('compl',''), ('bairro',''), ('cidade',''),
                            ('cep',''), ('uf',''), ('conjseg',''), ('codimovel',''),
                            ('tipoimovel','')]:
        if not getattr(mutuario, campo, None):
            setattr(mutuario, campo, default)

    mutuario.save()
    return mutuario


@require_http_methods(["GET"])
def ocr_review_dashboard(request):
    """
    Dashboard para revisão de contratos com OCR híbrido.
    Mostra filas pendentes e permite aprovar/rejeitar campos.
    """
    context = {
        'title': 'OCR Review Dashboard',
    }
    return render(request, 'principal/ocr_review_dashboard.html', context)


@require_http_methods(["GET", "POST"])
def upload_contrato_pdf(request):
    """
    View para upload e processamento de um contrato PDF
    GET: Mostra formulário de upload
    POST: Processa o PDF enviado
    """
    context = {}
    
    if request.method == 'POST':
        if 'pdf_file' not in request.FILES:
            context['erro'] = 'Nenhum arquivo PDF enviado'
        else:
            pdf_file = request.FILES['pdf_file']
            
            # Valida extensão
            if not pdf_file.name.lower().endswith('.pdf'):
                context['erro'] = 'Arquivo deve ser um PDF'
            else:
                temp_path = None
                try:
                    # Salva arquivo temporário em diretório compatível com Windows e Linux
                    sufixo = Path(pdf_file.name).suffix or '.pdf'
                    fd, temp_str = tempfile.mkstemp(suffix=sufixo, prefix='ocr_contrato_')
                    os.close(fd)
                    temp_path = Path(temp_str)

                    with open(temp_path, 'wb') as f:
                        for chunk in pdf_file.chunks():
                            f.write(chunk)

                    # Processa OCR
                    extractor = ContratoOCRExtractor(str(temp_path))
                    dados = extractor.extract_all()

                    if dados.get('document_type') == 'printevo_relatorio':
                        context['erro'] = (
                            'O arquivo enviado não é um contrato fonte. Ele é um relatório PRINTEVO '
                            '(Evolução Teórica do Saldo do Financiamento) gerado pela tela do sistema. '
                            'Esse tipo de PDF não serve para cadastro via OCR. Envie o PDF original do contrato '
                            'ou o TXT/MOVMUT com a evolução financeira.'
                        )
                        context['dados_extraidos'] = dados
                        context['texto_pdf_preview'] = (extractor.text or '')[:5000]
                        context['metodo_extracao'] = getattr(extractor, '_metodo_extracao', 'desconhecido')
                        context['n_parcelas_detectadas'] = len(dados.get('parcelas') or [])
                        return render(request, 'principal/ocr_upload_contrato.html', context)

                    # codigo_manual sempre prevalece sobre OCR (usuário sabe o número correto)
                    codigo_manual = request.POST.get('codigo_manual', '').strip()
                    if codigo_manual:
                        dados['codigo'] = codigo_manual
                    elif not dados.get('codigo'):
                        # fallback seguro: usa nome do arquivo PDF (ex.: 1234.pdf)
                        stem = Path(pdf_file.name).stem.strip()
                        if stem:
                            dados['codigo'] = stem[:20]

                    if dados:
                        # Camada hibrida: recupera campos com padroes contextuais
                        # e classifica auto/revisar para reduzir digitacao manual.
                        dados, relatorio_hibrido = analisar_ocr_hibrido(dados, extractor.text or '')

                        # Valida e salva no banco
                        dry_run = request.POST.get('dry_run') == 'on'
                        sucesso, mensagem = ContratoProcessor.save_contrato(dados, dry_run=dry_run)

                        if relatorio_hibrido.get('qtd_revisar', 0) > 0:
                            mensagem = (
                                f"{mensagem} | OCR hibrido: {relatorio_hibrido['qtd_auto']} auto, "
                                f"{relatorio_hibrido['qtd_revisar']} para revisar"
                            )

                        # Se salvou com sucesso, cria mutuário também
                        if sucesso and not dry_run:
                            try:
                                # Obtém o contrato criado
                                contrato = Contrato.objects.filter(codigo=dados.get('codigo')).last()
                                
                                # Cria mutuário
                                mutuario = criar_ou_atualizar_mutuario(dados)
                                if mutuario:
                                    mensagem += f" | Mutuário: {mutuario.nome} cadastrado"
                                
                                # Cria fila de revisão OCR com itens para cada campo
                                if contrato and relatorio_hibrido:
                                    fila = criar_fila_revisao_ocr(
                                        contrato=contrato,
                                        dados_ocr=dados,
                                        relatorio_hibrido=relatorio_hibrido,
                                        pdf_filename=pdf_file.name
                                    )
                                    if fila:
                                        mensagem += f" | Fila de revisão criada (ID: {fila.id})"
                            except Exception as e:
                                logger.warning(f"Erro ao criar mutuário/fila: {str(e)}")

                        context['sucesso'] = True
                        context['mensagem'] = mensagem
                        context['dados_extraidos'] = dados
                        context['ocr_hibrido'] = relatorio_hibrido
                        context['dry_run'] = dry_run
                        # Diagnóstico: texto bruto extraído do PDF
                        context['texto_pdf_preview'] = (extractor.text or '')[:5000]
                        context['metodo_extracao'] = getattr(extractor, '_metodo_extracao', 'desconhecido')
                        context['n_parcelas_detectadas'] = len(dados.get('parcelas') or [])
                    else:
                        context['erro'] = 'Nenhum dado foi extraído do PDF'

                except Exception as e:
                    context['erro'] = f'Erro ao processar: {str(e)}'
                finally:
                    # Garante remoção do arquivo temporário em qualquer situação
                    if temp_path and temp_path.exists():
                        try:
                            temp_path.unlink()
                        except Exception:
                            pass
    
    return render(request, 'principal/ocr_upload_contrato.html', context)


@require_http_methods(["POST"])
@csrf_exempt
def api_processar_lote_contratos(request):
    """
    API para processar múltiplos contratos de uma pasta
    Espera POST com JSON: {"pasta": "caminho_relativo", "dry_run": true/false}
    """
    try:
        data = json.loads(request.body)
        pasta = data.get('pasta', 'pdfs_contratos')
        dry_run = data.get('dry_run', False)
        
        # Caminho relativo ao projeto
        caminho_absoluto = Path(__file__).parent.parent / pasta
        
        if not caminho_absoluto.exists():
            return JsonResponse({
                'sucesso': False,
                'erro': f'Pasta não encontrada: {pasta}'
            }, status=400)
        
        # Processa lote
        processador = ProcessadorLoteContratos(str(caminho_absoluto))
        resultados = processador.processar(dry_run=dry_run)
        
        return JsonResponse({
            'sucesso': True,
            'resultados': resultados,
            'relatorio': processador.gerar_relatorio()
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'sucesso': False,
            'erro': 'JSON inválido'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'sucesso': False,
            'erro': str(e)
        }, status=500)


@require_http_methods(["GET"])
def listar_contratos_ocr(request):
    """
    Lista contratos cadastrados via OCR
    """
    from principal.models import Contrato
    
    contratos = Contrato.objects.all().order_by('-data_contrato')
    
    context = {
        'contratos': contratos,
        'total': contratos.count()
    }
    
    return render(request, 'principal/listar_contratos_ocr.html', context)


# Utility views
def relatorio_processamento_ocr(request):
    """
    Mostra relatório do último processamento OCR
    """
    relatorio_path = Path('relatorio_ocr_contrato.txt')
    
    if not relatorio_path.exists():
        relatorio = "Nenhum processamento realizado ainda"
    else:
        with open(relatorio_path, 'r', encoding='utf-8') as f:
            relatorio = f.read()
    
    return HttpResponse(f'<pre>{relatorio}</pre>')


# ===== OCR REVIEW QUEUE API ENDPOINTS =====

@require_http_methods(["GET"])
def api_ocr_review_queue_list_pending(request):
    """
    Lista contratos com campos pendentes de revisão.
    GET /api/ocr-review/pending/
    
    Query params:
    - sort_by: 'score' (default) | 'auto_count' | 'revisar_count' | 'date'
    - limit: número máximo de resultados (default: 50)
    """
    from principal.models import OCRReviewQueue
    
    sort_by = request.GET.get('sort_by', 'score')
    limit = int(request.GET.get('limit', 50))
    
    # Filtra apenas filas com campos pendentes
    pending_queues = OCRReviewQueue.objects.filter(
        status__in=['PENDING', 'PARTIALLY_REVIEWED']
    ).select_related('contrato')
    
    # Ordena conforme solicitado
    if sort_by == 'auto_count':
        pending_queues = pending_queues.order_by('auto_count', '-revisar_count')
    elif sort_by == 'revisar_count':
        pending_queues = pending_queues.order_by('-revisar_count')
    elif sort_by == 'date':
        pending_queues = pending_queues.order_by('-extraction_date')
    else:  # score (default)
        pending_queues = pending_queues.order_by('score', '-revisar_count')
    
    pending_queues = pending_queues[:limit]
    
    data = {
        'total': pending_queues.count(),
        'queues': [
            {
                'id': q.id,
                'contrato_codigo': q.contrato.codigo,
                'contrato_id': q.contrato.id,
                'status': q.status,
                'score': q.score,
                'auto_count': q.auto_count,
                'revisar_count': q.revisar_count,
                'extraction_date': q.extraction_date.isoformat(),
                'pending_items_count': q.get_pending_items_count(),
            }
            for q in pending_queues
        ]
    }
    
    return JsonResponse(data)


@require_http_methods(["GET"])
def api_ocr_review_queue_detail(request, queue_id):
    """
    Obtém detalhes completos de uma fila de revisão e seus items.
    GET /api/ocr-review/{queue_id}/
    """
    from principal.models import OCRReviewQueue, ReviewQueueItem
    
    try:
        queue = OCRReviewQueue.objects.get(id=queue_id)
    except OCRReviewQueue.DoesNotExist:
        return JsonResponse({'erro': 'Fila não encontrada'}, status=404)
    
    items = queue.review_items.all()
    
    data = {
        'queue': {
            'id': queue.id,
            'contrato_codigo': queue.contrato.codigo,
            'contrato_id': queue.contrato.id,
            'status': queue.status,
            'score': queue.score,
            'auto_count': queue.auto_count,
            'revisar_count': queue.revisar_count,
            'extraction_date': queue.extraction_date.isoformat(),
            'pdf_filename': queue.pdf_filename,
        },
        'items': [
            {
                'id': item.id,
                'field_name': item.field_name,
                'value_extracted': item.value_extracted,
                'value_approved': item.value_approved,
                'status': item.status,
                'confidence_score': item.confidence_score,
                'field_type': item.field_type,
                'notes': item.notes,
                'created_at': item.created_at.isoformat(),
                'approved_at': item.approved_at.isoformat() if item.approved_at else None,
                'approved_by': item.approved_by,
            }
            for item in items
        ]
    }
    
    return JsonResponse(data)


@require_http_methods(["POST"])
@csrf_exempt
def api_ocr_review_queue_approve_field(request, queue_id, field_name):
    """
    Aprova um campo específico de uma fila de revisão.
    POST /api/ocr-review/{queue_id}/approve-field/{field_name}/
    
    Body JSON:
    {
        "approved_value": "valor aprovado",  # opcional, usa value_extracted se não fornecido
        "notes": "notas do revisor"  # opcional
    }
    """
    from principal.models import OCRReviewQueue, ReviewQueueItem
    from django.utils import timezone
    
    try:
        queue = OCRReviewQueue.objects.get(id=queue_id)
        item = queue.review_items.get(field_name=field_name)
    except (OCRReviewQueue.DoesNotExist, ReviewQueueItem.DoesNotExist):
        return JsonResponse({'erro': 'Fila ou item não encontrado'}, status=404)
    
    try:
        body_data = json.loads(request.body)
    except json.JSONDecodeError:
        body_data = {}
    
    # Aprova o item
    item.status = 'USER_CORRECTED' if body_data.get('approved_value') else 'AUTO_APPROVED'
    item.value_approved = body_data.get('approved_value') or item.value_extracted
    item.approved_at = timezone.now()
    item.approved_by = getattr(request.user, 'username', 'api_user')
    item.notes = body_data.get('notes', '')
    item.save()
    
    # Atualiza status da fila
    pending_count = queue.review_items.filter(status='PENDING_REVIEW').count()
    if pending_count == 0:
        queue.status = 'APPROVED'
    else:
        queue.status = 'PARTIALLY_REVIEWED'
    queue.reviewed_by = getattr(request.user, 'username', 'api_user')
    queue.reviewed_at = timezone.now()
    queue.save()
    
    return JsonResponse({
        'sucesso': True,
        'item': {
            'id': item.id,
            'field_name': item.field_name,
            'value_approved': item.value_approved,
            'status': item.status,
            'approved_at': item.approved_at.isoformat(),
        },
        'queue_status': queue.status,
        'remaining_pending': pending_count,
    })


@require_http_methods(["POST"])
@csrf_exempt
def api_ocr_review_queue_reject_field(request, queue_id, field_name):
    """
    Rejeita um campo específico de uma fila de revisão.
    POST /api/ocr-review/{queue_id}/reject-field/{field_name}/
    
    Body JSON:
    {
        "notes": "motivo da rejeição"  # recomendado
    }
    """
    from principal.models import OCRReviewQueue, ReviewQueueItem
    from django.utils import timezone
    
    try:
        queue = OCRReviewQueue.objects.get(id=queue_id)
        item = queue.review_items.get(field_name=field_name)
    except (OCRReviewQueue.DoesNotExist, ReviewQueueItem.DoesNotExist):
        return JsonResponse({'erro': 'Fila ou item não encontrado'}, status=404)
    
    try:
        body_data = json.loads(request.body)
    except json.JSONDecodeError:
        body_data = {}
    
    # Rejeita o item
    item.status = 'REJECTED'
    item.approved_at = timezone.now()
    item.approved_by = getattr(request.user, 'username', 'api_user')
    item.notes = body_data.get('notes', 'Rejeitado pelo revisor')
    item.save()
    
    # Atualiza status da fila
    pending_count = queue.review_items.filter(status='PENDING_REVIEW').count()
    if pending_count > 0:
        queue.status = 'PARTIALLY_REVIEWED'
    queue.reviewed_by = getattr(request.user, 'username', 'api_user')
    queue.reviewed_at = timezone.now()
    queue.save()
    
    return JsonResponse({
        'sucesso': True,
        'item': {
            'id': item.id,
            'field_name': item.field_name,
            'status': item.status,
            'notes': item.notes,
            'approved_at': item.approved_at.isoformat(),
        },
        'queue_status': queue.status,
        'remaining_pending': pending_count,
    })


@require_http_methods(["POST"])
@csrf_exempt
def api_ocr_review_queue_bulk_approve(request, queue_id):
    """
    Aprova múltiplos campos de uma vez.
    POST /api/ocr-review/{queue_id}/bulk-approve/
    
    Body JSON:
    {
        "field_names": ["prazo", "tx_juros"],  # campos a aprovar
        "approve_all": false  # se true, aprova todos os pending
    }
    """
    from principal.models import OCRReviewQueue, ReviewQueueItem
    from django.utils import timezone
    
    try:
        queue = OCRReviewQueue.objects.get(id=queue_id)
    except OCRReviewQueue.DoesNotExist:
        return JsonResponse({'erro': 'Fila não encontrada'}, status=404)
    
    try:
        body_data = json.loads(request.body)
    except json.JSONDecodeError:
        body_data = {}
    
    approve_all = body_data.get('approve_all', False)
    field_names = body_data.get('field_names', [])
    
    if approve_all:
        items = queue.review_items.filter(status='PENDING_REVIEW')
    else:
        items = queue.review_items.filter(field_name__in=field_names)
    
    approved_count = 0
    for item in items:
        if item.status == 'PENDING_REVIEW':
            item.status = 'AUTO_APPROVED'
            item.value_approved = item.value_extracted
            item.approved_at = timezone.now()
            item.approved_by = getattr(request.user, 'username', 'api_user')
            item.save()
            approved_count += 1
    
    # Atualiza status da fila
    pending_count = queue.review_items.filter(status='PENDING_REVIEW').count()
    if pending_count == 0:
        queue.status = 'APPROVED'
    else:
        queue.status = 'PARTIALLY_REVIEWED'
    queue.reviewed_by = getattr(request.user, 'username', 'api_user')
    queue.reviewed_at = timezone.now()
    queue.save()
    
    return JsonResponse({
        'sucesso': True,
        'approved_count': approved_count,
        'queue_status': queue.status,
        'remaining_pending': pending_count,
    })
