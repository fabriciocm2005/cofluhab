from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Contrato
from .validators import validar_antes_exportar, pode_exportar


def validar_contrato_ajax(request, pk):
    """
    Endpoint AJAX para validar contrato antes de exportar.
    Retorna JSON com erros, warnings e informações.
    """
    contrato = get_object_or_404(Contrato, pk=pk)
    
    # Executar validação
    resultado = validar_antes_exportar(contrato)
    pode_exp, motivo = pode_exportar(contrato)
    
    # Organizar resposta
    response_data = {
        'sucesso': True,
        'valido': resultado['valido'],
        'pode_exportar': pode_exp,
        'motivo_bloqueio': motivo,
        'total_problemas': resultado['total_problemas'],
        'resumo': {
            'erros': len(resultado['erros']),
            'warnings': len(resultado['warnings']),
            'info': len(resultado['info'])
        },
        'detalhes': {
            'erros': resultado['erros'],
            'warnings': resultado['warnings'],
            'info': resultado['info']
        },
        'contrato': {
            'id': contrato.id,
            'codigo': contrato.codigo,
            'conjunto': contrato.conjunto
        }
    }
    
    return JsonResponse(response_data)
