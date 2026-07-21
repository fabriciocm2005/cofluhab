"""
Script para criar arquivos de teste M460xxx e validar os parsers
"""
import sys
from pathlib import Path

# Adiciona o diretório principal ao path
sys.path.insert(0, str(Path(__file__).parent / 'principal'))

from principal.ficha_m460_parsers import (
    ParserM460,
    RegistroM460301,
    RegistroM460401,
    RegistroM460801,
    agrupar_por_gifus,
    agrupar_por_situacao,
    calcular_totais_vaf
)

def criar_arquivo_teste_m460301():
    """Cria arquivo de teste M460301 com dados mock"""
    dados = [
        # GIFUS|AgOrig|AgCess|AgCed|Contrato|Hip|DataCont|Munic|DataEvento|DataPosVA1|ValVenc|ValVinc|DataPosVA3|ValVAF3|DataPosVA4|ValVAF4|PercCob|Situacao|DataApres|DataPrazo
        "21|12345|12346|12347|1234567890123|1|15-06-2020|3550|10-01-2025|15-01-2025|00000500000|00001000000|20-01-2025|00000300000|25-01-2025|00000200000|08500|01|05-01-2025|20-02-2025",
        "19|54321|54322|54323|9876543210987|1|20-08-2019|3304|15-01-2025|18-01-2025|00001200000|00002500000|22-01-2025|00000800000|28-01-2025|00000500000|09200|03|  -  -    |  -  -    ",
        "11|11111|11112|11113|5555555555555|2|10-03-2021|3106|12-01-2025|16-01-2025|00000300000|00000750000|21-01-2025|00000200000|26-01-2025|00000150000|07800|02|08-01-2025|25-02-2025",
        "03|22222|22223|22224|7777777777777|1|05-11-2018|2927|08-01-2025|14-01-2025|00002000000|00004000000|19-01-2025|00001500000|24-01-2025|00001000000|09500|04|  -  -    |  -  -    ",
        "21|33333|33334|33335|9999999999999|1|30-12-2022|3550|20-01-2025|23-01-2025|00000800000|00001600000|25-01-2025|00000600000|30-01-2025|00000400000|08800|06|15-01-2025|05-03-2025",
    ]
    
    caminho = 'teste_m460301.txt'
    with open(caminho, 'w', encoding='latin-1') as f:
        f.write('\n'.join(dados))
    
    print(f"✅ Arquivo criado: {caminho}")
    return caminho

def criar_arquivo_teste_m460401():
    """Cria arquivo de teste M460401 (mesma estrutura, novos do mês)"""
    dados = [
        # Apenas 2 contratos novos do mês
        "21|99999|99990|99991|1111111111111|1|22-01-2025|3550|22-01-2025|23-01-2025|00000100000|00000200000|23-01-2025|00000050000|23-01-2025|00000030000|08000|01|  -  -    |  -  -    ",
        "19|88888|88889|88880|2222222222222|2|23-01-2025|3304|23-01-2025|23-01-2025|00000150000|00000300000|23-01-2025|00000080000|23-01-2025|00000050000|08500|02|23-01-2025|10-03-2025",
    ]
    
    caminho = 'teste_m460401.txt'
    with open(caminho, 'w', encoding='latin-1') as f:
        f.write('\n'.join(dados))
    
    print(f"✅ Arquivo criado: {caminho}")
    return caminho

def criar_arquivo_teste_m460801():
    """Cria arquivo de teste M460801 (apenas 9 campos)"""
    dados = [
        # GIFUS|AgOrig|AgCess|AgCed|Contrato|Hip|DataCont|Munic|DataEvento
        "21|12345|12346|12347|8888888888888|1|10-05-2020|3550|18-01-2025",
        "19|54321|54322|54323|7777777777777|1|15-08-2019|3304|19-01-2025",
        "11|11111|11112|11113|6666666666666|2|20-02-2021|3106|20-01-2025",
        "03|22222|22223|22224|5555555555555|1|25-10-2018|2927|21-01-2025",
    ]
    
    caminho = 'teste_m460801.txt'
    with open(caminho, 'w', encoding='latin-1') as f:
        f.write('\n'.join(dados))
    
    print(f"✅ Arquivo criado: {caminho}")
    return caminho

def testar_parser_m460301(caminho):
    """Testa o parser M460301"""
    print("\n" + "=" * 80)
    print("TESTE: PARSER M460301 - Irregularidades Acumulativo")
    print("=" * 80)
    
    registros, erros = ParserM460.parse_file_m460301(caminho)
    
    print(f"\n📊 Resultados:")
    print(f"   Registros processados: {len(registros)}")
    print(f"   Erros encontrados: {len(erros)}")
    
    if erros:
        print(f"\n❌ Erros:")
        for erro in erros:
            print(f"   - {erro}")
    
    if registros:
        print(f"\n✅ Primeiros 3 registros:")
        for i, reg in enumerate(registros[:3], 1):
            print(f"\n   [{i}] Contrato: {reg.contrato}")
            print(f"       GIFUS: {reg.gifus_analise}")
            print(f"       Agentes: {reg.agente_origem}/{reg.agente_cessionario}/{reg.agente_cedente}")
            print(f"       Data Contrato: {reg.data_contrato.strftime('%d/%m/%Y') if reg.data_contrato else 'N/A'}")
            print(f"       Município: {reg.municipio_cadmut}")
            print(f"       Situação: {reg.situacao_mult_sinistro}")
            print(f"       Total VAFs: R$ {reg.total_todos_vafs:,.2f}")
            print(f"       Contestação: {'Sim' if reg.tem_contestacao else 'Não'}")
        
        # Análises
        print(f"\n📈 Análises:")
        
        # Por GIFUS
        por_gifus = agrupar_por_gifus(registros)
        print(f"\n   Contratos por GIFUS:")
        for gifus, regs in sorted(por_gifus.items()):
            print(f"      GIFUS {gifus}: {len(regs)} contratos")
        
        # Por situação
        por_situacao = agrupar_por_situacao(registros)
        print(f"\n   Contratos por Situação:")
        for sit, regs in sorted(por_situacao.items()):
            print(f"      Situação {sit}: {len(regs)} contratos")
        
        # Totais
        totais = calcular_totais_vaf(registros)
        print(f"\n   Totais Financeiros:")
        print(f"      Vencido: R$ {totais['total_vencido']:,.2f}")
        print(f"      Vincendo: R$ {totais['total_vincendo']:,.2f}")
        print(f"      VAF3: R$ {totais['total_vaf3']:,.2f}")
        print(f"      VAF4: R$ {totais['total_vaf4']:,.2f}")
        print(f"      TOTAL GERAL: R$ {totais['total_geral']:,.2f}")
    
    return len(registros), len(erros)

def testar_parser_m460401(caminho):
    """Testa o parser M460401"""
    print("\n" + "=" * 80)
    print("TESTE: PARSER M460401 - Irregularidades Inclusões Mês")
    print("=" * 80)
    
    registros, erros = ParserM460.parse_file_m460401(caminho)
    
    print(f"\n📊 Resultados:")
    print(f"   Registros processados: {len(registros)}")
    print(f"   Erros encontrados: {len(erros)}")
    
    if erros:
        print(f"\n❌ Erros:")
        for erro in erros:
            print(f"   - {erro}")
    
    if registros:
        print(f"\n✅ Registros (novos do mês):")
        for i, reg in enumerate(registros, 1):
            print(f"\n   [{i}] Contrato: {reg.contrato}")
            print(f"       GIFUS: {reg.gifus_analise}")
            print(f"       Data Contrato: {reg.data_contrato.strftime('%d/%m/%Y') if reg.data_contrato else 'N/A'}")
            print(f"       Situação: {reg.situacao_mult_sinistro}")
            print(f"       Total VAFs: R$ {reg.total_todos_vafs:,.2f}")
    
    return len(registros), len(erros)

def testar_parser_m460801(caminho):
    """Testa o parser M460801"""
    print("\n" + "=" * 80)
    print("TESTE: PARSER M460801 - Contratos Regularizados")
    print("=" * 80)
    
    registros, erros = ParserM460.parse_file_m460801(caminho)
    
    print(f"\n📊 Resultados:")
    print(f"   Registros processados: {len(registros)}")
    print(f"   Erros encontrados: {len(erros)}")
    
    if erros:
        print(f"\n❌ Erros:")
        for erro in erros:
            print(f"   - {erro}")
    
    if registros:
        print(f"\n✅ Registros (regularizados):")
        for i, reg in enumerate(registros, 1):
            print(f"\n   [{i}] Contrato: {reg.contrato}")
            print(f"       GIFUS: {reg.gifus_analise}")
            print(f"       Agentes: {reg.agente_origem}/{reg.agente_cessionario}/{reg.agente_cedente}")
            print(f"       Data Contrato: {reg.data_contrato.strftime('%d/%m/%Y') if reg.data_contrato else 'N/A'}")
            print(f"       Data Evento: {reg.data_evento_cadmut.strftime('%d/%m/%Y') if reg.data_evento_cadmut else 'N/A'}")
            print(f"       Município: {reg.municipio_cadmut}")
        
        # Por GIFUS
        por_gifus = agrupar_por_gifus(registros)
        print(f"\n   Contratos por GIFUS:")
        for gifus, regs in sorted(por_gifus.items()):
            print(f"      GIFUS {gifus}: {len(regs)} contratos")
    
    return len(registros), len(erros)

def main():
    """Executa todos os testes"""
    print("=" * 80)
    print("TESTE DE PARSERS M460xxx")
    print("=" * 80)
    print("\n🔧 Criando arquivos de teste...")
    
    # Cria arquivos de teste
    arquivo_301 = criar_arquivo_teste_m460301()
    arquivo_401 = criar_arquivo_teste_m460401()
    arquivo_801 = criar_arquivo_teste_m460801()
    
    print("\n✅ Arquivos de teste criados!")
    
    # Testa cada parser
    resultados = {}
    
    try:
        regs_301, errs_301 = testar_parser_m460301(arquivo_301)
        resultados['M460301'] = {'registros': regs_301, 'erros': errs_301}
    except Exception as e:
        print(f"\n❌ ERRO no teste M460301: {e}")
        import traceback
        traceback.print_exc()
        resultados['M460301'] = {'registros': 0, 'erros': 1}
    
    try:
        regs_401, errs_401 = testar_parser_m460401(arquivo_401)
        resultados['M460401'] = {'registros': regs_401, 'erros': errs_401}
    except Exception as e:
        print(f"\n❌ ERRO no teste M460401: {e}")
        import traceback
        traceback.print_exc()
        resultados['M460401'] = {'registros': 0, 'erros': 1}
    
    try:
        regs_801, errs_801 = testar_parser_m460801(arquivo_801)
        resultados['M460801'] = {'registros': regs_801, 'erros': errs_801}
    except Exception as e:
        print(f"\n❌ ERRO no teste M460801: {e}")
        import traceback
        traceback.print_exc()
        resultados['M460801'] = {'registros': 0, 'erros': 1}
    
    # Resumo final
    print("\n" + "=" * 80)
    print("RESUMO DOS TESTES")
    print("=" * 80)
    
    total_registros = sum(r['registros'] for r in resultados.values())
    total_erros = sum(r['erros'] for r in resultados.values())
    
    print(f"\n📊 Estatísticas:")
    for tipo, dados in resultados.items():
        status = "✅" if dados['erros'] == 0 else "⚠️"
        print(f"   {status} {tipo}: {dados['registros']} registros, {dados['erros']} erros")
    
    print(f"\n   Total de registros processados: {total_registros}")
    print(f"   Total de erros: {total_erros}")
    
    if total_erros == 0:
        print("\n✅ TODOS OS TESTES PASSARAM COM SUCESSO!")
    else:
        print("\n⚠️ ALGUNS TESTES APRESENTARAM ERROS")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    main()
