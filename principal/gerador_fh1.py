#!/usr/bin/env python
"""
GERADOR AUTOMÁTICO DO FORMULÁRIO FH1
Sistema para geração do formulário de habilitação ao FCVS
"""

import os
import sys
import django
from decimal import Decimal
from datetime import date, datetime
import json

# Adicionar diretório pai ao path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato, ParcelaContrato, Mutuario

def calcular_fcvs_residual(contrato):
    """Calcula o FCVS residual do contrato"""
    parcelas = ParcelaContrato.objects.filter(contrato=contrato).order_by('nmens')
    
    if not parcelas.exists():
        return Decimal('0'), 0
    
    fcvs_acum = Decimal('0')
    anomalias = 0
    
    # Tabela de conversão de moedas
    CONVERSION_FACTORS = [
        (date(1994, 7, 1), Decimal('2750')),
        (date(1993, 8, 1), Decimal('1000')),
        (date(1990, 3, 16), Decimal('1')),
        (date(1989, 1, 16), Decimal('1000')),
        (date(1986, 2, 28), Decimal('1000')),
    ]
    
    for i, parcela in enumerate(parcelas):
        if i == 0:
            continue
        
        parcela_ant = parcelas[i-1]
        
        # Aplica conversões de moeda
        for data_limite, fator in CONVERSION_FACTORS:
            if parcela.dtvenc >= data_limite:
                fcvs_acum /= fator
                break
        
        # Detecta amortização negativa
        if parcela.sddev and parcela_ant.sddev:
            if parcela.sddev > parcela_ant.sddev:
                crescimento = parcela.sddev - parcela_ant.sddev
                fcvs_acum += crescimento
                anomalias += 1
    
    return fcvs_acum, anomalias

def gerar_fh1(codigo_contrato):
    """Gera o formulário FH1 para um contrato específico"""
    
    try:
        contrato = Contrato.objects.get(codigo=codigo_contrato)
    except Contrato.DoesNotExist:
        print(f"❌ Contrato {codigo_contrato} não encontrado!")
        return
    
    # Buscar mutuário vinculado
    mutuario = None
    try:
        # Tenta pelo código do contrato
        mutuario = Mutuario.objects.filter(codigo=contrato.codigo).first()
        
        # Se não encontrar, tenta pela tabela de mapeamento
        if not mutuario:
            import sqlite3
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db.sqlite3')
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute("SELECT mutuario_id FROM contrato_mutuario_map WHERE contrato_id = ?", (contrato.id,))
            result = cur.fetchone()
            if result:
                mutuario = Mutuario.objects.get(id=result[0])
            conn.close()
    except Exception as e:
        print(f"⚠️  Erro ao buscar mutuário: {e}")
    
    # Buscar parcelas
    parcelas = ParcelaContrato.objects.filter(contrato=contrato).order_by('nmens')
    primeira = parcelas.first() if parcelas.exists() else None
    ultima = parcelas.last() if parcelas.exists() else None
    
    # Calcular FCVS residual
    fcvs_residual, anomalias = calcular_fcvs_residual(contrato)
    
    # Dados do formulário FH1
    fh1_data = {
        # Cabeçalho
        "data_geracao": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "agente_financeiro": "COFLUHAB - CIA FLUMINENSE DE HABITAÇÃO",
        
        # Dados do Mutuário
        "nome_mutuario": mutuario.nome if mutuario else "NÃO IDENTIFICADO",
        "cpf": mutuario.cpf if mutuario else "",
        "identidade": mutuario.ident if mutuario else "",
        "data_nascimento": mutuario.dtnasc.strftime("%d/%m/%Y") if mutuario and mutuario.dtnasc else "",
        "orgao": mutuario.orgao if mutuario else "",
        
        # Dados do Contrato
        "numero_contrato": contrato.codigo,
        "conjunto": contrato.conjunto,
        "data_contrato": contrato.data_contrato.strftime("%d/%m/%Y") if contrato.data_contrato else "",
        "prazo": contrato.prazo or 360,
        "total_parcelas": parcelas.count(),
        
        # Dados Financeiros
        "saldo_inicial": primeira.sddev if primeira else Decimal('0'),
        "saldo_atual": ultima.sddev if ultima else Decimal('0'),
        "fcvs_residual": fcvs_residual,
        "anomalias_detectadas": anomalias,
        
        # Período
        "primeira_parcela": primeira.dtvenc.strftime("%m/%Y") if primeira and primeira.dtvenc else "",
        "ultima_parcela": ultima.dtvenc.strftime("%m/%Y") if ultima and ultima.dtvenc else "",
        
        # Endereço do Imóvel
        "endereco_imovel": mutuario.endereco if mutuario else "",
        "numero": mutuario.numero if mutuario else "",
        "complemento": mutuario.compl if mutuario else "",
        "bairro": mutuario.bairro if mutuario else "",
        "cidade": mutuario.cidade if mutuario else "",
        "uf": mutuario.uf if mutuario else "",
        "cep": mutuario.cep if mutuario else "",
        "codigo_imovel": mutuario.codimovel if mutuario else "",
    }
    
    return fh1_data

def formatar_fh1_txt(fh1_data):
    """Formata os dados do FH1 em texto para impressão"""
    
    txt = f"""
{'='*80}
FICHA PARA HABILITAÇÃO AO FCVS - FORMULÁRIO FH1
{'='*80}

{'='*80}
I. IDENTIFICAÇÃO DO AGENTE FINANCEIRO
{'='*80}
AGENTE FINANCEIRO: {fh1_data['agente_financeiro']}
DATA DE GERAÇÃO: {fh1_data['data_geracao']}

{'='*80}
II. IDENTIFICAÇÃO DO MUTUÁRIO
{'='*80}
NOME: {fh1_data['nome_mutuario']}
CPF: {fh1_data['cpf']}
IDENTIDADE: {fh1_data['identidade']}
DATA DE NASCIMENTO: {fh1_data['data_nascimento']}
ÓRGÃO: {fh1_data['orgao']}

{'='*80}
III. IDENTIFICAÇÃO DO CONTRATO
{'='*80}
NÚMERO DO CONTRATO: {fh1_data['numero_contrato']}
CONJUNTO HABITACIONAL: {fh1_data['conjunto']}
DATA DO CONTRATO: {fh1_data['data_contrato']}
PRAZO: {fh1_data['prazo']} meses
TOTAL DE PARCELAS: {fh1_data['total_parcelas']}

{'='*80}
IV. LOCALIZAÇÃO DO IMÓVEL
{'='*80}
ENDEREÇO: {fh1_data['endereco_imovel']}, {fh1_data['numero']}
COMPLEMENTO: {fh1_data['complemento']}
BAIRRO: {fh1_data['bairro']}
CIDADE/UF: {fh1_data['cidade']}/{fh1_data['uf']}
CEP: {fh1_data['cep']}
CÓDIGO DO IMÓVEL: {fh1_data['codigo_imovel']}

{'='*80}
V. SITUAÇÃO FINANCEIRA
{'='*80}
SALDO INICIAL: R$ {fh1_data['saldo_inicial']:,.2f}
SALDO ATUAL: R$ {fh1_data['saldo_atual']:,.2f}
FCVS RESIDUAL: R$ {fh1_data['fcvs_residual']:,.2f}
ANOMALIAS DETECTADAS: {fh1_data['anomalias_detectadas']} ocorrências de amortização negativa

PERÍODO DO CONTRATO: {fh1_data['primeira_parcela']} até {fh1_data['ultima_parcela']}

{'='*80}
VI. FUNDAMENTAÇÃO JURÍDICA
{'='*80}
1. O contrato foi celebrado durante período de hiperinflação (1984-1994)
2. Foram detectadas {fh1_data['anomalias_detectadas']} ocorrências de amortização negativa
3. O saldo residual de FCVS não foi devidamente compensado
4. Há direito à habilitação ao FCVS conforme Resolução CMN nº 2.099/94

{'='*80}
VII. RECOMENDAÇÕES
{'='*80}
1. Solicitar auditoria à Caixa Econômica Federal
2. Apresentar este formulário como anexo ao processo
3. Requerer a quitação do saldo residual de FCVS
4. Caso negado, ingressar com ação judicial

{'='*80}
VIII. ASSINATURAS
{'='*80}

_______________________________________
Responsável Técnico - COFLUHAB

_______________________________________
Mutuário

DATA: ____/____/______

{'='*80}
"""
    return txt

def exportar_fh1_json(fh1_data, filename):
    """Exporta os dados do FH1 em formato JSON"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(fh1_data, f, ensure_ascii=False, indent=2, default=str)
    print(f"✅ FH1 exportado para JSON: {filename}")

def exportar_fh1_txt(fh1_data, filename):
    """Exporta o FH1 em formato texto"""
    txt_content = formatar_fh1_txt(fh1_data)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(txt_content)
    print(f"✅ FH1 exportado para TXT: {filename}")

def main():
    """Função principal"""
    if len(sys.argv) > 1:
        codigo = sys.argv[1]
    else:
        codigo = input("Digite o código do contrato (ex: 6001): ").strip()
    
    print(f"\n{'='*80}")
    print(f"GERANDO FORMULÁRIO FH1 - CONTRATO {codigo}")
    print(f"{'='*80}")
    
    # Gerar dados do FH1
    fh1_data = gerar_fh1(codigo)
    
    if not fh1_data:
        return
    
    # Mostrar na tela
    print(formatar_fh1_txt(fh1_data))
    
    # Exportar arquivos
    base_filename = f"FH1_{codigo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    exportar_fh1_json(fh1_data, f"{base_filename}.json")
    exportar_fh1_txt(fh1_data, f"{base_filename}.txt")
    
    print(f"\n✅ FORMULÁRIO FH1 GERADO COM SUCESSO!")
    print(f"📁 Arquivos criados:")
    print(f"   • {base_filename}.json (dados estruturados)")
    print(f"   • {base_filename}.txt (formulário para impressão)")
    
    # Recomendações
    print(f"\n💡 PRÓXIMOS PASSOS:")
    print(f"   1. Imprima o arquivo TXT e assine")
    print(f"   2. Anexe ao processo de habilitação ao FCVS")
    print(f"   3. Encaminhe à Caixa Econômica Federal")
    print(f"   4. Guarde o arquivo JSON como backup digital")

if __name__ == "__main__":
    main()
