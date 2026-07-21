#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste do Parser P3026 Atualizado
=================================

Testa o parser P3026 com a nova estrutura de 31 campos TR1 e suporte TR2-TR9.

Criado: 2025
"""

from datetime import datetime
from principal.ficha_p3026_parser import (
    ParserP3026,
    RegistroContratoP3026,
    HeaderP3026,
    TrailerP3026,
    RegistroTR2, RegistroTR3, RegistroTR4, RegistroTR5,
    RegistroTR6, RegistroTR7, RegistroTR8, RegistroTR9
)


def criar_linha_tr1_teste() -> str:
    """
    Cria uma linha TR1 de teste com todos os 31 campos
    
    Posições:
    001-001: Tipo = '1'
    002-006: Matrícula agente = '12345'
    007-011: Agente cessionário = '67890'
    012-016: Agente cedente = '11111'
    017-029: Número contrato = '0000012345678'
    030-030: Grau hipoteca = '1'
    031-070: Nome mutuário = 'JOSE DA SILVA'
    071-081: CPF = '12345678901'
    082-089: Data assinatura = '01012020' (DDMMAAAA)
    090-129: Endereço = 'RUA DAS FLORES, 123'
    130-134: Código município = '35550'
    135-144: Nome município = 'SAO PAULO '
    145-146: Origem recurso = '01'
    147-148: IM = '01'
    149-154: Taxa juros contratual = '008500' (8.50%)
    155-160: Taxa juros evento = '009000' (9.00%)
    161-162: Código situação = '02' (habilitado)
    163-232: Descrição situação = 'HABILITADO PARA PAGAMENTO'
    233-235: Tipo evento = '001'
    236-243: Data evento = '15062020'
    244-257: VAF1 = '00000012345678' (123456.78)
    258-271: VAF2 = '00000000500000' (5000.00)
    272-285: VAF3 = '00000000000000' (0.00)
    286-293: Data habilitação = '20062020'
    294-294: Documentação = '1' (entregue)
    295-302: Data processamento = '25062020'
    303-310: Data entrega agente = '30062020'
    311-318: Data prazo agente = '15072020'
    319-319: Situação análise = '2' (homologado)
    320-327: Data negociação = '10072020'
    328-500: Vago (173 bytes)
    """
    linha = (
        '1'                                          # [001-001] Tipo
        + '12345'                                    # [002-006] Matrícula (5)
        + '67890'                                    # [007-011] Cessionário (5)
        + '11111'                                    # [012-016] Cedente (5)
        + '0000012345678'                            # [017-029] Número contrato (13)
        + '1'                                        # [030-030] Grau hipoteca (1)
        + 'JOSE DA SILVA' + ' ' * 27                 # [031-070] Nome (40 chars)
        + '12345678901'                              # [071-081] CPF (11 chars)
        + '01012020'                                 # [082-089] Data assinatura (8)
        + 'RUA DAS FLORES, 123' + ' ' * 21           # [090-129] Endereço (40 chars)
        + '35550'                                    # [130-134] Código município (5)
        + 'SAO PAULO '                               # [135-144] Nome município (10 chars)
        + '01'                                       # [145-146] Origem recurso (2)
        + '01'                                       # [147-148] IM (2)
        + '008500'                                   # [149-154] Taxa contratual (6)
        + '009000'                                   # [155-160] Taxa evento (6)
        + '02'                                       # [161-162] Código situação (2)
        + 'HABILITADO PARA PAGAMENTO' + ' ' * 45    # [163-232] Descrição (70 chars: 25+45)
        + '001'                                      # [233-235] Tipo evento (3)
        + '15062020'                                 # [236-243] Data evento (8)
        + '00000012345678'                           # [244-257] VAF1 (14 chars)
        + '00000000500000'                           # [258-271] VAF2 (14 chars)
        + '00000000000000'                           # [272-285] VAF3 (14 chars)
        + '20062020'                                 # [286-293] Data habilitação (8)
        + '1'                                        # [294-294] Documentação (1)
        + '25062020'                                 # [295-302] Data processamento (8)
        + '30062020'                                 # [303-310] Data entrega (8)
        + '15072020'                                 # [311-318] Data prazo (8)
        + '2'                                        # [319-319] Situação análise (1)
        + '10072020'                                 # [320-327] Data negociação (8)
        + ' ' * 173                                  # [328-500] Vago
    )
    return linha


def testar_parse_tr1():
    """Testa parsing de registro TR1 com todos os 31 campos"""
    print("=" * 80)
    print("TESTE 1: Parse TR1 - 31 Campos Completos")
    print("=" * 80)
    
    linha = criar_linha_tr1_teste()
    print(f"Tamanho da linha: {len(linha)} caracteres")
    
    try:
        registro = RegistroContratoP3026.from_linha(linha)
        
        print("\n✅ Parse bem-sucedido!")
        print("\n📋 CAMPOS PARSEADOS:")
        print(f"   01. Tipo registro: '{registro.tipo_registro}'")
        print(f"   02. Matrícula agente: '{registro.matricula_agente}'")
        print(f"   03. Agente cessionário: '{registro.agente_cessionario}'")
        print(f"   04. Agente cedente: '{registro.agente_cedente}'")
        print(f"   05. Número contrato: '{registro.numero_contrato}'")
        print(f"   06. Grau hipoteca: {registro.grau_hipoteca}")
        print(f"   07. Nome mutuário: '{registro.nome_mutuario}'")
        print(f"   08. CPF: '{registro.cpf}'")
        print(f"   09. Data assinatura: {registro.data_assinatura_contrato}")
        print(f"   10. Endereço: '{registro.endereco_imovel}'")
        print(f"   11. Código município: '{registro.codigo_municipio}'")
        print(f"   12. Nome município: '{registro.nome_municipio}'")
        print(f"   13. Origem recurso: '{registro.origem_recurso}'")
        print(f"   14. IM: '{registro.im}'")
        print(f"   15. Taxa juros contratual: '{registro.taxa_juros_contratual}'")
        print(f"   16. Taxa juros evento: '{registro.taxa_juros_evento}'")
        print(f"   17. Código situação: '{registro.codigo_situacao_contrato}'")
        print(f"   18. Descrição situação: '{registro.descricao_situacao_contrato}'")
        print(f"   19. Tipo evento: '{registro.tipo_evento}'")
        print(f"   20. Data evento: {registro.data_evento}")
        print(f"   21. VAF1 informado agente: R$ {registro.vaf1_informado_agente:,.2f}")
        print(f"   22. VAF2 informado agente: R$ {registro.vaf2_informado_agente:,.2f}")
        print(f"   23. VAF3 informado agente: R$ {registro.vaf3_informado_agente:,.2f}")
        print(f"   24. Data habilitação: {registro.data_habilitacao}")
        print(f"   25. Documentação: {registro.documentacao} (1=entregue)")
        print(f"   26. Data processamento: {registro.data_processamento_habilitacao}")
        print(f"   27. Data entrega agente: {registro.data_entrega_agente}")
        print(f"   28. Data prazo agente: {registro.data_prazo_agente}")
        print(f"   29. Situação análise: {registro.situacao_analise_atual} (2=homologado)")
        print(f"   30. Data negociação: {registro.data_negociacao_transferencia}")
        print(f"   31. Campo vago: {len(registro.campo_vago)} bytes")
        
        # Validações
        print("\n🔍 VALIDAÇÕES:")
        erros = []
        
        if registro.tipo_registro != '1':
            erros.append(f"Tipo registro inválido: {registro.tipo_registro}")
        
        if registro.numero_contrato != '0000012345678':
            erros.append(f"Número contrato incorreto: {registro.numero_contrato}")
        
        if registro.cpf != '12345678901':
            erros.append(f"CPF incorreto: {registro.cpf}")
        
        if registro.data_assinatura_contrato.strftime('%d/%m/%Y') != '01/01/2020':
            erros.append(f"Data assinatura incorreta: {registro.data_assinatura_contrato}")
        
        if registro.vaf1_informado_agente != 123456.78:
            erros.append(f"VAF1 incorreto: {registro.vaf1_informado_agente} (esperado: 123456.78)")
        
        if registro.vaf2_informado_agente != 5000.00:
            erros.append(f"VAF2 incorreto: {registro.vaf2_informado_agente} (esperado: 5000.00)")
        
        if registro.codigo_situacao_contrato != '02':
            erros.append(f"Código situação incorreto: {registro.codigo_situacao_contrato}")
        
        if registro.documentacao != 1:
            erros.append(f"Documentação incorreta: {registro.documentacao}")
        
        if registro.situacao_analise_atual != 2:
            erros.append(f"Situação análise incorreta: {registro.situacao_analise_atual}")
        
        if erros:
            print(f"   ❌ {len(erros)} erro(s) encontrado(s):")
            for erro in erros:
                print(f"      - {erro}")
            return False
        else:
            print("   ✅ Todas as validações passaram!")
            return True
            
    except Exception as e:
        print(f"\n❌ ERRO ao parsear: {e}")
        import traceback
        traceback.print_exc()
        return False


def testar_tr2_a_tr9():
    """Testa parsing básico dos registros TR2-TR9"""
    print("\n" + "=" * 80)
    print("TESTE 2: Parse TR2-TR9 - Registros Stub")
    print("=" * 80)
    
    classes_tr = [
        (RegistroTR2, '2', 76),
        (RegistroTR3, '3', 71),
        (RegistroTR4, '4', 90),
        (RegistroTR5, '5', 50),
        (RegistroTR6, '6', 46),
        (RegistroTR7, '7', 66),
        (RegistroTR8, '8', 62),
        (RegistroTR9, '9', 47)
    ]
    
    erros = 0
    for classe, tipo, total_campos in classes_tr:
        try:
            linha_teste = tipo + 'X' * 499  # Linha de teste com 500 chars
            registro = classe.from_linha(linha_teste)
            
            assert registro.tipo_registro == tipo, f"Tipo incorreto: {registro.tipo_registro}"
            assert registro.dados_brutos == linha_teste, "Dados brutos não salvos"
            
            print(f"   ✅ {classe.__name__}: tipo='{tipo}', {total_campos} campos (stub)")
            
        except Exception as e:
            print(f"   ❌ {classe.__name__}: ERRO - {e}")
            erros += 1
    
    if erros == 0:
        print(f"\n✅ Todos os 8 tipos TR2-TR9 funcionando!")
        return True
    else:
        print(f"\n❌ {erros} erro(s) encontrado(s)")
        return False


def testar_parse_datas():
    """Testa parse de datas com casos especiais"""
    print("\n" + "=" * 80)
    print("TESTE 3: Parse de Datas - Casos Especiais")
    print("=" * 80)
    
    casos = [
        ('01012020', datetime(2020, 1, 1), 'Data válida'),
        ('00000000', None, 'Data zerada'),
        ('        ', None, 'Data com espaços'),
        ('99999999', None, 'Data inválida'),
        ('31122024', datetime(2024, 12, 31), 'Data fim de ano'),
    ]
    
    erros = 0
    for data_str, esperado, descricao in casos:
        # Criar linha de teste com a data na posição 082-089
        linha = '1' + '0' * 80 + data_str + ' ' * 411
        
        try:
            registro = RegistroContratoP3026.from_linha(linha)
            resultado = registro.data_assinatura_contrato
            
            if esperado is None:
                if resultado is None:
                    print(f"   ✅ {descricao}: None (correto)")
                else:
                    print(f"   ❌ {descricao}: {resultado} (esperado: None)")
                    erros += 1
            else:
                if resultado == esperado:
                    print(f"   ✅ {descricao}: {resultado.strftime('%d/%m/%Y')}")
                else:
                    print(f"   ❌ {descricao}: {resultado} (esperado: {esperado})")
                    erros += 1
                    
        except Exception as e:
            print(f"   ❌ {descricao}: ERRO - {e}")
            erros += 1
    
    if erros == 0:
        print("\n✅ Todos os 5 casos de data validados!")
        return True
    else:
        print(f"\n❌ {erros} erro(s) encontrado(s)")
        return False


def testar_parse_decimais():
    """Testa parse de valores decimais (VAFs)"""
    print("\n" + "=" * 80)
    print("TESTE 4: Parse de Decimais - Valores VAF")
    print("=" * 80)
    
    casos = [
        ('00000012345678', 123456.78, 'VAF normal'),
        ('00000000000100', 1.00, 'VAF pequeno'),
        ('00000099999999', 999999.99, 'VAF máximo'),
        ('00000000000000', 0.00, 'VAF zerado'),
        ('              ', 0.00, 'VAF com espaços'),
    ]
    
    erros = 0
    for valor_str, esperado, descricao in casos:
        # Criar linha de teste com o valor na posição VAF1 (244-257)
        linha = '1' + '0' * 242 + valor_str + ' ' * 243
        
        try:
            registro = RegistroContratoP3026.from_linha(linha)
            resultado = registro.vaf1_informado_agente
            
            if abs(resultado - esperado) < 0.01:  # Tolerância de 1 centavo
                print(f"   ✅ {descricao}: R$ {resultado:,.2f}")
            else:
                print(f"   ❌ {descricao}: R$ {resultado:,.2f} (esperado: R$ {esperado:,.2f})")
                erros += 1
                
        except Exception as e:
            print(f"   ❌ {descricao}: ERRO - {e}")
            erros += 1
    
    if erros == 0:
        print("\n✅ Todos os 5 casos de decimal validados!")
        return True
    else:
        print(f"\n❌ {erros} erro(s) encontrado(s)")
        return False


def main():
    """Executa todos os testes"""
    print("\n" + "=" * 80)
    print("TESTE DO PARSER P3026 ATUALIZADO")
    print("Estrutura TR1: 31 campos (posições 001-500)")
    print("Estruturas TR2-TR9: Classes stub com dados_brutos")
    print("=" * 80)
    
    resultados = []
    
    # Teste 1: TR1 completo
    resultados.append(("TR1 - 31 campos", testar_parse_tr1()))
    
    # Teste 2: TR2-TR9 stubs
    resultados.append(("TR2-TR9 stubs", testar_tr2_a_tr9()))
    
    # Teste 3: Parse de datas
    resultados.append(("Parse de datas", testar_parse_datas()))
    
    # Teste 4: Parse de decimais
    resultados.append(("Parse de decimais", testar_parse_decimais()))
    
    # Resumo
    print("\n" + "=" * 80)
    print("RESUMO DOS TESTES")
    print("=" * 80)
    
    total = len(resultados)
    sucesso = sum(1 for _, passou in resultados if passou)
    falhou = total - sucesso
    
    for nome, passou in resultados:
        status = "✅ PASSOU" if passou else "❌ FALHOU"
        print(f"   {status}: {nome}")
    
    print(f"\n📊 RESULTADO FINAL: {sucesso}/{total} testes passaram ({sucesso/total*100:.0f}%)")
    
    if falhou == 0:
        print("\n🎉 TODOS OS TESTES PASSARAM! Parser P3026 está pronto para uso.")
        return 0
    else:
        print(f"\n⚠️  {falhou} teste(s) falharam. Revisar implementação.")
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
