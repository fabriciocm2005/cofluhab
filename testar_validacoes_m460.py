"""
Testes unitários para os parsers M460xxx
Valida casos edge, erros e validações
"""
import sys
from pathlib import Path
from datetime import datetime
from decimal import Decimal

sys.path.insert(0, str(Path(__file__).parent / 'principal'))

from principal.ficha_m460_parsers import (
    ParserM460,
    TipoGIFUS,
    SituacaoMultiplicidadeSinistro
)

def testar_parse_date():
    """Testa parsing de datas"""
    print("\n📅 Teste: Parse de Datas")
    print("-" * 60)
    
    testes = [
        ("15-06-2020", datetime(2020, 6, 15), "Data válida normal"),
        ("01-01-2025", datetime(2025, 1, 1), "Primeiro dia do ano"),
        ("31-12-2024", datetime(2024, 12, 31), "Último dia do ano"),
        ("  -  -    ", None, "Data vazia (espaços)"),
        ("00-00-0000", None, "Data zerada"),
        ("", None, "String vazia"),
        ("99-99-9999", None, "Data inválida"),
    ]
    
    sucessos = 0
    falhas = 0
    
    for entrada, esperado, descricao in testes:
        resultado = ParserM460.parse_date(entrada)
        if resultado == esperado:
            print(f"   ✅ {descricao}: '{entrada}' -> {resultado}")
            sucessos += 1
        else:
            print(f"   ❌ {descricao}: '{entrada}' -> {resultado} (esperado: {esperado})")
            falhas += 1
    
    print(f"\n   Resultado: {sucessos} sucessos, {falhas} falhas")
    return falhas == 0

def testar_parse_decimal():
    """Testa parsing de valores decimais"""
    print("\n💰 Teste: Parse de Decimais")
    print("-" * 60)
    
    testes = [
        ("00000500000", 2, Decimal("5000.00"), "Valor 5000.00"),
        ("00001234567", 2, Decimal("12345.67"), "Valor com decimais"),
        ("00000000001", 2, Decimal("0.01"), "Um centavo"),
        ("99999999999", 2, Decimal("999999999.99"), "Valor máximo"),
        ("00000000000", 2, Decimal("0"), "Zero"),
        ("", 2, Decimal("0"), "String vazia"),
        ("   ", 2, Decimal("0"), "Espaços"),
        ("00012345", 3, Decimal("12.345"), "3 casas decimais"),
    ]
    
    sucessos = 0
    falhas = 0
    
    for entrada, decimais, esperado, descricao in testes:
        resultado = ParserM460.parse_decimal(entrada, decimais)
        if resultado == esperado:
            print(f"   ✅ {descricao}: '{entrada}' (dec={decimais}) -> {resultado}")
            sucessos += 1
        else:
            print(f"   ❌ {descricao}: '{entrada}' (dec={decimais}) -> {resultado} (esperado: {esperado})")
            falhas += 1
    
    print(f"\n   Resultado: {sucessos} sucessos, {falhas} falhas")
    return falhas == 0

def testar_enums():
    """Testa enumeradores"""
    print("\n🏷️  Teste: Enumeradores")
    print("-" * 60)
    
    # Testa GIFUS
    print("   GIFUS disponíveis:")
    for gifus in TipoGIFUS:
        print(f"      {gifus.value} - {gifus.name}")
    
    # Testa Situações
    print("\n   Situações de Multiplicidade/Sinistro:")
    for sit in SituacaoMultiplicidadeSinistro:
        print(f"      {sit.value} - {sit.name}")
    
    print(f"\n   ✅ {len(TipoGIFUS)} GIFUS e {len(SituacaoMultiplicidadeSinistro)} situações mapeadas")
    return True

def testar_validacoes_m460301():
    """Testa validações específicas do M460301"""
    print("\n🔍 Teste: Validações M460301")
    print("-" * 60)
    
    # Linha válida
    linha_valida = "21|12345|12346|12347|1234567890123|1|15-06-2020|3550|10-01-2025|15-01-2025|00000500000|00001000000|20-01-2025|00000300000|25-01-2025|00000200000|08500|01|05-01-2025|20-02-2025"
    
    try:
        reg = ParserM460.parse_m460301_line(linha_valida)
        print(f"   ✅ Linha válida parseada com sucesso")
        print(f"      Contrato: {reg.contrato}")
        print(f"      Total VAFs: R$ {reg.total_todos_vafs:,.2f}")
        print(f"      Tem contestação: {reg.tem_contestacao}")
        print(f"      Prazo vencido: {reg.contestacao_vencida}")
    except Exception as e:
        print(f"   ❌ Erro ao parsear linha válida: {e}")
        return False
    
    # Linha com menos campos
    linha_incompleta = "21|12345|12346|12347|1234567890123"
    try:
        reg = ParserM460.parse_m460301_line(linha_incompleta)
        print(f"   ❌ Linha incompleta deveria gerar erro mas não gerou")
        return False
    except ValueError as e:
        print(f"   ✅ Linha incompleta detectada corretamente: {e}")
    
    # Linha com datas vazias
    linha_sem_datas = "21|12345|12346|12347|1234567890123|1|15-06-2020|3550|10-01-2025|15-01-2025|00000500000|00001000000|20-01-2025|00000300000|25-01-2025|00000200000|08500|01|  -  -    |  -  -    "
    try:
        reg = ParserM460.parse_m460301_line(linha_sem_datas)
        print(f"   ✅ Linha com datas vazias parseada")
        print(f"      Data contestação: {reg.data_apresentacao_contestacao}")
        print(f"      Tem contestação: {reg.tem_contestacao}")
    except Exception as e:
        print(f"   ❌ Erro ao parsear linha com datas vazias: {e}")
        return False
    
    return True

def testar_validacoes_m460801():
    """Testa validações específicas do M460801"""
    print("\n🔍 Teste: Validações M460801")
    print("-" * 60)
    
    # Linha válida
    linha_valida = "21|12345|12346|12347|8888888888888|1|10-05-2020|3550|18-01-2025"
    
    try:
        reg = ParserM460.parse_m460801_line(linha_valida)
        print(f"   ✅ Linha válida parseada com sucesso")
        print(f"      Contrato: {reg.contrato}")
        print(f"      Data evento: {reg.data_evento_cadmut.strftime('%d/%m/%Y')}")
    except Exception as e:
        print(f"   ❌ Erro ao parsear linha válida: {e}")
        return False
    
    # Linha com menos campos
    linha_incompleta = "21|12345|12346"
    try:
        reg = ParserM460.parse_m460801_line(linha_incompleta)
        print(f"   ❌ Linha incompleta deveria gerar erro mas não gerou")
        return False
    except ValueError as e:
        print(f"   ✅ Linha incompleta detectada corretamente: {e}")
    
    return True

def testar_calculos_financeiros():
    """Testa cálculos financeiros"""
    print("\n💵 Teste: Cálculos Financeiros")
    print("-" * 60)
    
    linha = "21|12345|12346|12347|1234567890123|1|15-06-2020|3550|10-01-2025|15-01-2025|00000100000|00000200000|20-01-2025|00000050000|25-01-2025|00000030000|08500|01|05-01-2025|20-02-2025"
    
    reg = ParserM460.parse_m460301_line(linha)
    
    # Valores esperados (com 2 casas decimais implícitas)
    # 00000100000 = 1000.00
    # 00000200000 = 2000.00
    # 00000050000 = 500.00
    # 00000030000 = 300.00
    
    print(f"   Valores individuais:")
    print(f"      VAF1/VA2 Vencido: R$ {reg.valor_saldo_vaf1_va2_vencido:,.2f}")
    print(f"      VAF1/VAF2 Vincendo: R$ {reg.valor_saldo_vaf1_vaf2_vincendo:,.2f}")
    print(f"      VAF3: R$ {reg.valor_saldo_vaf3:,.2f}")
    print(f"      VAF4: R$ {reg.valor_saldo_vaf4:,.2f}")
    
    total_venc_vinc = reg.total_saldo_vencido_vincendo
    total_todos = reg.total_todos_vafs
    
    print(f"\n   Totais calculados:")
    print(f"      Vencido + Vincendo: R$ {total_venc_vinc:,.2f}")
    print(f"      Todos os VAFs: R$ {total_todos:,.2f}")
    
    # Validações
    esperado_venc_vinc = Decimal("3000.00")
    esperado_total = Decimal("3800.00")
    
    if total_venc_vinc == esperado_venc_vinc and total_todos == esperado_total:
        print(f"\n   ✅ Cálculos corretos!")
        return True
    else:
        print(f"\n   ❌ Cálculos incorretos!")
        print(f"      Esperado venc+vinc: {esperado_venc_vinc}, obtido: {total_venc_vinc}")
        print(f"      Esperado total: {esperado_total}, obtido: {total_todos}")
        return False

def testar_percentual_cobertura():
    """Testa parsing do percentual de cobertura"""
    print("\n📊 Teste: Percentual de Cobertura")
    print("-" * 60)
    
    # 08500 com 2 decimais = 85.00%
    linha = "21|12345|12346|12347|1234567890123|1|15-06-2020|3550|10-01-2025|15-01-2025|00000100000|00000200000|20-01-2025|00000050000|25-01-2025|00000030000|08500|01|05-01-2025|20-02-2025"
    
    reg = ParserM460.parse_m460301_line(linha)
    
    print(f"   Valor bruto: 08500")
    print(f"   Percentual parseado: {reg.percentual_cobertura}%")
    
    if reg.percentual_cobertura == Decimal("85.00"):
        print(f"   ✅ Percentual correto (85.00%)")
        return True
    else:
        print(f"   ❌ Percentual incorreto (esperado: 85.00%, obtido: {reg.percentual_cobertura}%)")
        return False

def main():
    """Executa todos os testes de validação"""
    print("=" * 80)
    print("TESTES DE VALIDAÇÃO - PARSERS M460xxx")
    print("=" * 80)
    
    resultados = []
    
    # Executa cada teste
    resultados.append(("Parse de Datas", testar_parse_date()))
    resultados.append(("Parse de Decimais", testar_parse_decimal()))
    resultados.append(("Enumeradores", testar_enums()))
    resultados.append(("Validações M460301", testar_validacoes_m460301()))
    resultados.append(("Validações M460801", testar_validacoes_m460801()))
    resultados.append(("Cálculos Financeiros", testar_calculos_financeiros()))
    resultados.append(("Percentual de Cobertura", testar_percentual_cobertura()))
    
    # Resumo
    print("\n" + "=" * 80)
    print("RESUMO DOS TESTES DE VALIDAÇÃO")
    print("=" * 80)
    
    sucessos = sum(1 for _, passou in resultados if passou)
    total = len(resultados)
    
    print("\n📊 Resultados:")
    for nome, passou in resultados:
        status = "✅" if passou else "❌"
        print(f"   {status} {nome}")
    
    print(f"\n   Total: {sucessos}/{total} testes passaram")
    
    if sucessos == total:
        print("\n🎉 TODOS OS TESTES DE VALIDAÇÃO PASSARAM!")
    else:
        print(f"\n⚠️  {total - sucessos} teste(s) falharam")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    main()
