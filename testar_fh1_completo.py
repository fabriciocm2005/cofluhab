#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Teste Completo do Gerador FH1
Valida conformidade com layout oficial CEF
"""
import os
import sys
import django

os.chdir(r'C:\Users\fabri\cofluhab\cofluhab')
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato, Mutuario
from principal.ficha_generators import FH1Generator
from decimal import Decimal
from datetime import date

# ============================================================================
# LAYOUT OFICIAL FH1 - TIPO DE MOVIMENTO = I (Inclusão/Habilitação)
# ============================================================================

LAYOUT_FH1_OFICIAL = {
    # SEQUÊNCIA: Nome do Campo, Posição, Tamanho, Tipo, Observações
    1: {"nome": "UFS", "pos": "001-002", "tam": 2, "tipo": "N", "obs": "Código UF"},
    2: {"nome": "MAT. AG. FINANC. /DV", "pos": "003-008", "tam": 6, "tipo": "N", "obs": "Matrícula + DV"},
    3: {"nome": "N.º CONTRATO DO MUT. NO AGENTE", "pos": "009-021", "tam": 13, "tipo": "A", "obs": "Número do contrato"},
    4: {"nome": "HIPOTECA", "pos": "022-022", "tam": 1, "tipo": "A", "obs": "Grau hipoteca (1=primeira)"},
    5: {"nome": "SEQUENCIAL", "pos": "023-024", "tam": 2, "tipo": "N", "obs": "Sequencial do mutuário"},
    6: {"nome": "CONSTANTE", "pos": "025-025", "tam": 1, "tipo": "N", "obs": "Sempre 0"},
    7: {"nome": "NOME DO MUT. PRINCIPAL", "pos": "026-065", "tam": 40, "tipo": "A", "obs": "Nome completo"},
    8: {"nome": "CPF/CI", "pos": "066-076", "tam": 11, "tipo": "N", "obs": "CPF sem pontuação"},
    9: {"nome": "DATA DE NASCIMENTO", "pos": "077-082", "tam": 6, "tipo": "N", "obs": "DDMMAA"},
    10: {"nome": "CODIGO DO MUNICÍPIO", "pos": "083-087", "tam": 5, "tipo": "N", "obs": "Código IBGE"},
    11: {"nome": "UF", "pos": "088-089", "tam": 2, "tipo": "A", "obs": "Sigla UF"},
    12: {"nome": "ENDEREÇO DO IMÓVEL", "pos": "090-127", "tam": 38, "tipo": "A", "obs": "Endereço completo"},
    13: {"nome": "DATA DO CONTRATO", "pos": "128-133", "tam": 6, "tipo": "N", "obs": "DDMMAA"},
    14: {"nome": "VALOR FINANCIAMENTO CONTRATADO", "pos": "134-145", "tam": 12, "tipo": "N", "obs": "9(10)V99"},
    15: {"nome": "PRAZO CONTRATADO", "pos": "146-148", "tam": 3, "tipo": "N", "obs": "Meses"},
    16: {"nome": "TAXA JUROS CONTRATADO", "pos": "149-152", "tam": 4, "tipo": "N", "obs": "99V99"},
    17: {"nome": "1o VENCIMENTO", "pos": "153-158", "tam": 6, "tipo": "N", "obs": "DDMMAA"},
    18: {"nome": "VALOR FINANC. PADRÃO FCVS", "pos": "159-170", "tam": 12, "tipo": "N", "obs": "9(10)V99"},
    19: {"nome": "PRAZO FCVS", "pos": "171-173", "tam": 3, "tipo": "N", "obs": "Meses"},
    20: {"nome": "TAXA JUROS PARA FCVS", "pos": "174-177", "tam": 4, "tipo": "N", "obs": "99V99"},
    21: {"nome": "PLANO", "pos": "178-180", "tam": 3, "tipo": "A", "obs": "SAC, PRICE, etc"},
    22: {"nome": "RR", "pos": "181-182", "tam": 2, "tipo": "N", "obs": "Redutor"},
    23: {"nome": "INDEX", "pos": "183-185", "tam": 3, "tipo": "A", "obs": "Índice (TR, INPC, etc)"},
    24: {"nome": "CÓDIGO DA CATEG. PROFISSIONAL", "pos": "186-190", "tam": 5, "tipo": "A", "obs": "Categoria"},
    25: {"nome": "PR", "pos": "191-192", "tam": 2, "tipo": "N", "obs": "Programa"},
}

TAMANHO_LINHA_FH1 = 192  # Tamanho total da linha FH1


def print_header(titulo):
    print("\n" + "=" * 80)
    print(titulo.center(80))
    print("=" * 80)


def print_campo(seq, nome, esperado, obtido, status):
    """Imprime resultado da validação de um campo"""
    simbolo = "✅" if status == "OK" else "❌" if status == "ERRO" else "⚠️"
    print(f"{simbolo} [{seq:2d}] {nome:35s} | Esp: {esperado:3d} | Obt: {obtido:3d} | {status}")


def validar_campo(linha, seq, spec):
    """Valida um campo específico da linha FH1"""
    # Extrai posição
    pos_str = spec['pos']
    inicio, fim = pos_str.split('-')
    inicio = int(inicio) - 1  # Converte para zero-based
    fim = int(fim)
    
    # Extrai valor
    valor = linha[inicio:fim] if len(linha) >= fim else ''
    tamanho_esperado = spec['tam']
    tamanho_obtido = len(valor)
    
    # Valida
    if tamanho_obtido != tamanho_esperado:
        status = "ERRO"
    elif not valor or valor.strip() == '':
        status = "VAZIO"
    else:
        status = "OK"
    
    return {
        'seq': seq,
        'nome': spec['nome'],
        'esperado': tamanho_esperado,
        'obtido': tamanho_obtido,
        'valor': valor,
        'status': status
    }


def testar_fh1():
    """Executa teste completo do gerador FH1"""
    
    print_header("🧪 TESTE COMPLETO DO GERADOR FH1")
    
    # ========================================================================
    # ETAPA 1: Busca contrato de teste
    # ========================================================================
    print("\n📋 ETAPA 1: Buscando contrato de teste...")
    
    try:
        # Busca um contrato real com dados completos
        contrato = Contrato.objects.filter(
            codigo__isnull=False,
            conjunto__isnull=False
        ).first()
        
        if not contrato:
            print("❌ ERRO: Nenhum contrato encontrado no banco!")
            return False
        
        print(f"✅ Contrato encontrado: {contrato.codigo}")
        print(f"   Conjunto: {contrato.conjunto}")
        print(f"   Data Contrato: {contrato.data_contrato}")
        print(f"   Prazo: {contrato.prazo} meses")
        print(f"   Taxa: {contrato.tx_juros}%")
        
        # Busca mutuário
        mutuario = None
        if contrato.conjunto:
            mutuario = Mutuario.objects.filter(conjunto=contrato.conjunto).first()
            if mutuario:
                print(f"✅ Mutuário encontrado: {mutuario.nome}")
                print(f"   CPF: {mutuario.cpf}")
            else:
                print("⚠️  AVISO: Mutuário não encontrado")
    
    except Exception as e:
        print(f"❌ ERRO ao buscar contrato: {e}")
        return False
    
    # ========================================================================
    # ETAPA 2: Gera linha FH1
    # ========================================================================
    print("\n📝 ETAPA 2: Gerando linha FH1...")
    
    try:
        generator = FH1Generator(validar=False)  # Desabilita validação estrita para análise
        linha, erros = generator.gerar_de_contrato(contrato, mutuario)
        
        print(f"✅ Linha FH1 gerada!")
        print(f"   Tamanho: {len(linha)} caracteres")
        print(f"   Esperado: {TAMANHO_LINHA_FH1} caracteres")
        
        # Testa também com validação para ver os erros
        print("\n🔍 Testando validação...")
        try:
            from principal.ficha_generators import FH1Generator as FH1Gen
            generator_com_validacao = FH1Gen(validar=True)
            _, erros_validacao = generator_com_validacao.gerar_de_contrato(contrato, mutuario)
        except Exception as e:
            print(f"   ⚠️  Validação falhou: {e}")
            # Tenta pegar erros do validador diretamente
            gen_temp = FH1Gen(validar=True)
            dados = gen_temp._extrair_dados_contrato(contrato, mutuario)
            valido, erros_validacao = gen_temp.validator.validar(dados)
            erros = erros_validacao
        
        if erros:
            print(f"\n⚠️  {len(erros)} avisos/erros de validação:")
            for i, erro in enumerate(erros[:10], 1):  # Mostra primeiros 10
                print(f"   {i}. [{erro.severidade}] {erro.campo}: {erro.mensagem}")
    
    except Exception as e:
        print(f"❌ ERRO ao gerar FH1: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # ========================================================================
    # ETAPA 3: Valida conformidade com layout oficial
    # ========================================================================
    print_header("📊 ETAPA 3: Validando conformidade com layout CEF")
    
    resultados = []
    erros_count = 0
    vazios_count = 0
    
    for seq in sorted(LAYOUT_FH1_OFICIAL.keys()):
        spec = LAYOUT_FH1_OFICIAL[seq]
        resultado = validar_campo(linha, seq, spec)
        resultados.append(resultado)
        
        if resultado['status'] == 'ERRO':
            erros_count += 1
        elif resultado['status'] == 'VAZIO':
            vazios_count += 1
    
    # Imprime resultados
    print(f"\n📋 Validação de {len(resultados)} campos:")
    print("-" * 80)
    
    for r in resultados:
        print_campo(r['seq'], r['nome'], r['esperado'], r['obtido'], r['status'])
    
    # ========================================================================
    # ETAPA 4: Resumo e diagnóstico
    # ========================================================================
    print_header("📈 ETAPA 4: Resumo e Diagnóstico")
    
    total = len(resultados)
    ok_count = total - erros_count - vazios_count
    
    print(f"\n✅ Campos OK:     {ok_count:3d} / {total} ({ok_count*100//total}%)")
    print(f"⚠️  Campos VAZIOS: {vazios_count:3d} / {total} ({vazios_count*100//total}%)")
    print(f"❌ Campos ERRO:   {erros_count:3d} / {total} ({erros_count*100//total}%)")
    
    print(f"\n📏 Tamanho da linha:")
    print(f"   Gerado:   {len(linha)} chars")
    print(f"   Esperado: {TAMANHO_LINHA_FH1} chars")
    
    if len(linha) != TAMANHO_LINHA_FH1:
        diff = len(linha) - TAMANHO_LINHA_FH1
        print(f"   ❌ DIFERENÇA: {diff:+d} caracteres")
    else:
        print(f"   ✅ TAMANHO CORRETO!")
    
    # ========================================================================
    # ETAPA 5: Amostra da linha gerada
    # ========================================================================
    print_header("🔍 ETAPA 5: Amostra da Linha Gerada")
    
    print("\nPrimeiros 100 caracteres:")
    print(linha[:100])
    print("\nÚltimos 100 caracteres:")
    print(linha[-100:])
    
    # ========================================================================
    # ETAPA 6: Campos críticos
    # ========================================================================
    print_header("🎯 ETAPA 6: Verificação de Campos Críticos")
    
    campos_criticos = [1, 2, 3, 7, 8, 13, 14, 15, 16]  # UFS, MAT, CONTRATO, NOME, CPF, etc
    
    print("\nCampos críticos para envio CEF:")
    for seq in campos_criticos:
        r = next((x for x in resultados if x['seq'] == seq), None)
        if r:
            simbolo = "✅" if r['status'] == "OK" else "❌" if r['status'] == "ERRO" else "⚠️"
            valor_trunc = r['valor'][:30] if len(r['valor']) > 30 else r['valor']
            print(f"{simbolo} {r['nome']:35s}: '{valor_trunc}'")
    
    # ========================================================================
    # CONCLUSÃO
    # ========================================================================
    print_header("🏁 CONCLUSÃO")
    
    if erros_count == 0 and len(linha) == TAMANHO_LINHA_FH1:
        print("\n✅ TESTE PASSOU! FH1 está em conformidade com o layout CEF!")
        print("   Pronto para envio.")
        sucesso = True
    elif erros_count == 0 and len(linha) != TAMANHO_LINHA_FH1:
        print("\n⚠️  TESTE PARCIAL! Campos OK mas tamanho incorreto.")
        print("   Necessário ajustar tamanho da linha.")
        sucesso = False
    else:
        print(f"\n❌ TESTE FALHOU! {erros_count} erros encontrados.")
        print("   Necessário corrigir campos antes do envio.")
        sucesso = False
    
    if vazios_count > 5:
        print(f"\n⚠️  ATENÇÃO: {vazios_count} campos vazios detectados.")
        print("   Verifique se os dados estão completos no banco.")
    
    return sucesso


if __name__ == '__main__':
    try:
        sucesso = testar_fh1()
        sys.exit(0 if sucesso else 1)
    except Exception as e:
        print(f"\n💥 ERRO FATAL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
