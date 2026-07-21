"""
Views do Agente de Qualidade de Contratos
"""
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from principal.models import Contrato
from principal.agente_qualidade_contrato import AgenteQualidadeContrato


@require_http_methods(["GET"])
def inspecionar_contrato(request, pk):
    """Exibe o relatório de qualidade de um contrato específico."""
    contrato = get_object_or_404(Contrato, pk=pk)
    agente = AgenteQualidadeContrato(contrato=contrato)
    relatorio = agente.inspecionar()
    return render(request, 'principal/qualidade_contrato.html', {
        'contrato': contrato,
        'relatorio': relatorio,
    })


@require_http_methods(["GET"])
def api_inspecionar_contrato(request, pk):
    """Retorna relatório de qualidade como JSON (para chamadas AJAX)."""
    contrato = get_object_or_404(Contrato, pk=pk)
    agente = AgenteQualidadeContrato(contrato=contrato)
    relatorio = agente.inspecionar()

    return JsonResponse({
        'contrato_codigo': relatorio.contrato_codigo,
        'score': relatorio.score,
        'status': relatorio.status_label,
        'prontidao_cadmut': relatorio.prontidao_cadmut,
        'prontidao_fh1': relatorio.prontidao_fh1,
        'erros': [{'categoria': i.categoria, 'campo': i.campo, 'mensagem': i.mensagem, 'sugestao': i.sugestao}
                  for i in relatorio.erros],
        'avisos': [{'categoria': i.categoria, 'campo': i.campo, 'mensagem': i.mensagem, 'sugestao': i.sugestao}
                   for i in relatorio.avisos],
        'infos': [{'categoria': i.categoria, 'campo': i.campo, 'mensagem': i.mensagem}
                  for i in relatorio.infos],
        'resumo_financeiro': relatorio.resumo_financeiro,
    })


@require_http_methods(["GET"])
def painel_qualidade(request):
    """Painel geral — lista contratos com score de qualidade."""
    # Pega todos os contratos e calcula score para cada um
    contratos = Contrato.objects.order_by('codigo').all()

    resultados = []
    for c in contratos:
        try:
            agente = AgenteQualidadeContrato(contrato=c)
            rel = agente.inspecionar()
            resultados.append({
                'contrato': c,
                'score': rel.score,
                'status_label': rel.status_label,
                'status_css': rel.status_css,
                'n_erros': len(rel.erros),
                'n_avisos': len(rel.avisos),
                'prontidao_cadmut': rel.prontidao_cadmut,
                'prontidao_fh1': rel.prontidao_fh1,
            })
        except Exception as e:
            resultados.append({
                'contrato': c,
                'score': 0,
                'status_label': 'ERRO',
                'status_css': 'danger',
                'n_erros': 1,
                'n_avisos': 0,
                'prontidao_cadmut': False,
                'prontidao_fh1': False,
                'erro_interno': str(e),
            })

    # Ordena por score crescente (piores primeiro)
    resultados.sort(key=lambda r: r['score'])

    stats = {
        'total': len(resultados),
        'otimos': sum(1 for r in resultados if r['score'] >= 90),
        'bons': sum(1 for r in resultados if 75 <= r['score'] < 90),
        'atencao': sum(1 for r in resultados if 50 <= r['score'] < 75),
        'criticos': sum(1 for r in resultados if r['score'] < 50),
        'prontos_cadmut': sum(1 for r in resultados if r['prontidao_cadmut']),
        'prontos_fh1': sum(1 for r in resultados if r['prontidao_fh1']),
    }

    return render(request, 'principal/painel_qualidade.html', {
        'resultados': resultados,
        'stats': stats,
    })
