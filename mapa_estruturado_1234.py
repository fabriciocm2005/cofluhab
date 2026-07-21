#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MAPA ESTRUTURADO - Contrato 1234
Define EXATAMENTE quais campos extrair do PDF e como processar
"""

MAPA_CONTRATO = {
    # ===== SEÇÃO I: IMÓVEL =====
    "imvel": {
        "endereco_rua": {
            "descricao": "Rua/Avenida do imóvel",
            "secao": "I",
            "padrao_regex": r'sito à\s*([^,]+)',
            "tipo": "texto",
            "obrigatorio": True,
        },
        "endereco_numero": {
            "descricao": "Número do imóvel",
            "secao": "I",
            "padrao_regex": r'n[º°]?\s*(\d+)',
            "tipo": "numero",
            "obrigatorio": True,
        },
        "municipio": {
            "descricao": "Município",
            "secao": "I",
            "padrao_regex": r'Município:\s*([^,\n]+)',
            "tipo": "texto",
            "obrigatorio": False,
        },
    },
    
    # ===== SEÇÃO III: DATA DO CONTRATO =====
    "contrato": {
        "data_contrato": {
            "descricao": "Data de assinatura do contrato",
            "secao": "Firmas",
            "exemplo": "23/03/1983",
            "tipo": "data",
            "obrigatorio": True,
            "uso": "Data início para simulação"
        },
    },
    
    # ===== SEÇÃO IV: PREÇO DE VENDA =====
    "preco_venda": {
        "valor_venda": {
            "descricao": "Preço de venda do imóvel",
            "secao": "IV",
            "tipo": "decimal",
            "obrigatorio": False,
            "nota": "Pode estar em texto ou cortado no PDF"
        },
        "upc_vigente_contrato": {
            "descricao": "UPC vigente na data do contrato",
            "secao": "IV",
            "exemplo": "24.0",
            "tipo": "decimal",
            "obrigatorio": True,
            "uso": "Para conversão de valores e simulação"
        },
    },
    
    # ===== SEÇÃO V: CONDIÇÕES DE PAGAMENTO =====
    "financiamento": {
        "prazo_meses": {
            "descricao": "Prazo em meses",
            "secao": "V",
            "exemplo": "120",
            "tipo": "inteiro",
            "obrigatorio": True,
            "uso": "Número de períodos da amortização"
        },
        "tx_juros_nominal": {
            "descricao": "Taxa de juros nominal (% a.a.)",
            "secao": "V",
            "exemplo": "10.00",
            "tipo": "decimal",
            "obrigatorio": True,
            "uso": "Cálculo de juros na simulação"
        },
        "prestacao_base_mensal": {
            "descricao": "Prestação mensal BASE (sem acessórios)",
            "secao": "V",
            "exemplo": "182,33",
            "tipo": "decimal",
            "obrigatorio": True,
            "uso": "Para validar SAC/PRICE, calcular FCVS"
        },
        "data_primeira_prestacao": {
            "descricao": "Data do primeiro vencimento",
            "secao": "V",
            "exemplo": "30/11/1984",
            "tipo": "data",
            "obrigatorio": True,
            "uso": "Data início dos pagamentos"
        },
        "progressao_aritmetica_razao": {
            "descricao": "Razão de acréscimo em progressão aritmética",
            "secao": "V",
            "exemplo": "2.440,00",
            "tipo": "decimal",
            "obrigatorio": False,
            "nota": "Se contrato é com reajuste PA"
        },
    },
    
    # ===== SEÇÃO VI: ACESSÓRIOS =====
    "acessorios": {
        "seguro_mip": {
            "descricao": "Seguro MIP",
            "secao": "VI",
            "tipo": "decimal",
            "obrigatorio": True,
            "nota": "Prêmio de seguros"
        },
        "d_fis": {
            "descricao": "Despesa Fiscal",
            "secao": "VI",
            "tipo": "decimal",
            "obrigatorio": False,
        },
        "total_seguros": {
            "descricao": "Total de seguros",
            "secao": "VI",
            "tipo": "decimal",
            "obrigatorio": True,
        },
        "taxa_cobranca_admin": {
            "descricao": "Taxa de cobrança e administração",
            "secao": "VI",
            "tipo": "decimal",
            "obrigatorio": True,
        },
        "prestacao_total_com_acessorios": {
            "descricao": "Prestação + acessórios (O QUE O MUTUÁRIO PAGA NO 1º MÊS)",
            "secao": "VI",
            "linha": "totalizando prestação mais acessório nesta data em",
            "exemplo": "195.769,99",
            "tipo": "decimal",
            "obrigatorio": True,
            "uso": "Validar encargo total mensal vs prestação base para cálculo FCVS",
            "CRITICO": "Este é o valor REAL que o mutuário paga mensalmente no início"
        },
    },
    
    # ===== SISTEMA DE AMORTIZAÇÃO (derivado) =====
    "amortizacao": {
        "sistema_amortizacao": {
            "descricao": "Sistema de amortização (SAC, PRICE, SACRE, etc)",
            "tipo": "texto",
            "obrigatorio": True,
            "nota": "Se não constar no PDF, usar SAC (padrão BNH 1983-1985)",
            "exemplo": "SAC"
        },
    }
}

print("=" * 100)
print("MAPA ESTRUTURADO - CONTRATO 1234")
print("=" * 100)
print()

for secao, campos in MAPA_CONTRATO.items():
    print(f"\n{secao.upper()}")
    print("-" * 100)
    
    for campo, info in campos.items():
        print(f"\n  {campo}")
        for chave, valor in info.items():
            if chave == "CRITICO":
                print(f"    🔴 {chave}: {valor}")
            else:
                print(f"    {chave}: {valor}")

print()
print("=" * 100)
print("RESUMO DOS VALORES DO CONTRATO 1234 (PARA BANCO)")
print("=" * 100)
print()

valores_banco = {
    "data_contrato": "1983-03-23",
    "data_primeiro_venc": "1984-11-30",  # ✅ CONFIRMADO NO PDF
    "vlfinanc": "10939.89",  # Já no banco
    "prestacao_inicial": "195769.99",  # ✅ CONFIRMADO NO PDF (valor que mutuário paga)
    "prestacao_base": "182.33",  # Prestação pura (sem acessórios)
    "prazo": "120",
    "tx_juros": "10.0",
    "sa": "SAC",  # Presumido
}

for campo, valor in valores_banco.items():
    print(f"  {campo:30s} = {valor}")

print()
print("✅ = Confirmado visualmente no PDF")

