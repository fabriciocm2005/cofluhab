"""
Script para atualizar/importar dados de Contrato.txt e Mutuario.txt
Atualiza apenas campos vazios, preservando dados existentes
"""
import os
import sys
import django
from datetime import datetime

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato, Mutuario
from decimal import Decimal


def parse_data(data_str):
    """Converte data de AAAAMMDD para objeto date"""
    if not data_str or data_str.strip() == '' or data_str == '00000000':
        return None
    try:
        ano = int(data_str[0:4])
        mes = int(data_str[4:6])
        dia = int(data_str[6:8])
        return datetime(ano, mes, dia).date()
    except:
        return None


def importar_contratos():
    """Importa/atualiza dados de Contrato.txt"""
    arquivo = r'C:\Users\fabri\cofluhab\cofluhab\dados_antigos\acerto_cadmut\Contrato.txt'
    
    print("=" * 80)
    print("IMPORTANDO CONTRATOS")
    print("=" * 80)
    
    atualizados = 0
    criados = 0
    erros = 0
    
    # Primeiro, buscar todos os códigos existentes
    print("Carregando contratos existentes...")
    codigos_existentes = set(Contrato.objects.values_list('codigo', flat=True))
    print(f"Encontrados {len(codigos_existentes)} contratos no banco")
    
    # Preparar listas para bulk operations
    contratos_para_criar = []
    contratos_para_atualizar = []
    
    with open(arquivo, 'r', encoding='latin-1') as f:
        for linha_num, linha in enumerate(f, 1):
            try:
                campos = linha.strip().split('\t')
                
                if len(campos) < 11:
                    continue
                
                # Extrair código do contrato (remover zeros à esquerda)
                codigo_raw = campos[1].strip()
                try:
                    # Se for numérico, remover zeros à esquerda
                    codigo = str(int(codigo_raw))
                except:
                    # Se não for numérico, manter como está
                    codigo = codigo_raw
                
                conjunto = campos[6].strip() if len(campos) > 6 else ''
                data_contrato = parse_data(campos[3].strip()) if len(campos) > 3 else None
                cod_imovel = campos[7].strip() if len(campos) > 7 else ''
                
                if codigo not in codigos_existentes:
                    # Criar novo contrato
                    contratos_para_criar.append(Contrato(
                        codigo=codigo,
                        conjunto=conjunto,
                        data_contrato=data_contrato,
                        cod_imovel=cod_imovel,
                        chave='',
                        lote='',
                        sinal='',
                        conversor=None,
                        sa='',
                        tx_juros=None,
                        prazo=None,
                        cat_prof='',
                        pr='',
                        data_primeiro_venc=None,
                    ))
                    codigos_existentes.add(codigo)  # Adicionar para evitar duplicatas
                    
                    # Criar em lotes de 100
                    if len(contratos_para_criar) >= 100:
                        Contrato.objects.bulk_create(contratos_para_criar, ignore_conflicts=True)
                        criados += len(contratos_para_criar)
                        print(f"✅ Criados {criados} contratos...")
                        contratos_para_criar = []
                    
            except Exception as e:
                erros += 1
                if erros <= 5:  # Mostrar apenas os primeiros erros
                    print(f"Erro na linha {linha_num}: {e}")
                continue
    
    # Criar contratos restantes
    if contratos_para_criar:
        Contrato.objects.bulk_create(contratos_para_criar, ignore_conflicts=True)
        criados += len(contratos_para_criar)
    
    print(f"\n✅ Contratos criados: {criados}")
    print(f"❌ Erros: {erros}")
    
    # Agora atualizar campos vazios dos existentes
    print("\nAtualizando campos vazios...")
    contratos_db = Contrato.objects.all()
    
    # Reprocessar arquivo para atualizar
    contratos_map = {}
    with open(arquivo, 'r', encoding='latin-1') as f:
        for linha in f:
            try:
                campos = linha.strip().split('\t')
                if len(campos) < 11:
                    continue
                
                try:
                    codigo = str(int(campos[1].strip()))
                except:
                    codigo = campos[1].strip()
                    
                contratos_map[codigo] = {
                    'conjunto': campos[6].strip() if len(campos) > 6 else '',
                    'data_contrato': parse_data(campos[3].strip()) if len(campos) > 3 else None,
                    'cod_imovel': campos[7].strip() if len(campos) > 7 else '',
                }
            except:
                continue
    
    for contrato in contratos_db:
        if contrato.codigo in contratos_map:
            dados = contratos_map[contrato.codigo]
            atualizado = False
            
            if not contrato.conjunto and dados['conjunto']:
                contrato.conjunto = dados['conjunto']
                atualizado = True
            
            if not contrato.data_contrato and dados['data_contrato']:
                contrato.data_contrato = dados['data_contrato']
                atualizado = True
            
            if not contrato.cod_imovel and dados['cod_imovel']:
                contrato.cod_imovel = dados['cod_imovel']
                atualizado = True
            
            if atualizado:
                contrato.save()
                atualizados += 1
                if atualizados % 100 == 0:
                    print(f"Atualizados {atualizados} contratos...")
    
    print(f"✅ Contratos atualizados: {atualizados}")
    print()


def importar_mutuarios():
    """Importa/atualiza dados de Mutuario.txt"""
    arquivo = r'C:\Users\fabri\cofluhab\cofluhab\dados_antigos\acerto_cadmut\Mutuario.txt'
    
    print("=" * 80)
    print("IMPORTANDO MUTUÁRIOS")
    print("=" * 80)
    
    atualizados = 0
    criados = 0
    erros = 0
    pulados = 0
    
    # Carregar códigos existentes
    print("Carregando mutuários existentes...")
    codigos_existentes = set(Mutuario.objects.values_list('codigo', flat=True))
    print(f"Encontrados {len(codigos_existentes)} mutuários no banco")
    
    mutuarios_para_criar = []
    
    with open(arquivo, 'r', encoding='latin-1') as f:
        for linha_num, linha in enumerate(f, 1):
            try:
                # Pular cabeçalho
                if linha_num == 1:
                    pulados += 1
                    continue
                
                campos = linha.strip().split('\t')
                
                if len(campos) < 9:
                    continue
                
                # Extrair código do contrato
                codigo_raw = campos[1].strip()
                try:
                    codigo = str(int(codigo_raw))
                except:
                    codigo = codigo_raw
                
                # Pegar apenas mutuário principal (TIPO = 00)
                tipo_mutuario = campos[3].strip()
                if tipo_mutuario != '00':
                    pulados += 1
                    continue
                
                nome = campos[4].strip()
                cpf_raw = campos[6].strip() if len(campos) > 6 else ''
                ident = campos[7].strip() if len(campos) > 7 else ''
                dtnasc = parse_data(campos[8].strip()) if len(campos) > 8 else None
                
                # Formatar CPF
                cpf = ''
                if cpf_raw:
                    cpf_num = cpf_raw.zfill(11)
                    if len(cpf_num) == 11:
                        cpf = f"{cpf_num[0:3]}.{cpf_num[3:6]}.{cpf_num[6:9]}-{cpf_num[9:11]}"
                
                if codigo not in codigos_existentes:
                    # Criar novo mutuário
                    mutuarios_para_criar.append(Mutuario(
                        codigo=codigo,
                        codimovel='',
                        conjunto='',
                        conjseg='',
                        nome=nome,
                        ident=ident,
                        orgao='',
                        dtnasc=dtnasc,
                        cpf=cpf,
                        renda=0,
                        crenda=0,
                        endereco='',
                        numero='',
                        compl='',
                        tipoimovel='',
                        bairro='',
                        cidade='',
                        cep='',
                        uf='RJ'
                    ))
                    codigos_existentes.add(codigo)
                    
                    # Criar em lotes de 100
                    if len(mutuarios_para_criar) >= 100:
                        Mutuario.objects.bulk_create(mutuarios_para_criar, ignore_conflicts=True)
                        criados += len(mutuarios_para_criar)
                        print(f"✅ Criados {criados} mutuários...")
                        mutuarios_para_criar = []
                    
            except Exception as e:
                erros += 1
                if erros <= 5:
                    print(f"Erro na linha {linha_num}: {e}")
                continue
    
    # Criar mutuários restantes
    if mutuarios_para_criar:
        Mutuario.objects.bulk_create(mutuarios_para_criar, ignore_conflicts=True)
        criados += len(mutuarios_para_criar)
    
    print(f"\n✅ Mutuários criados: {criados}")
    print(f"❌ Erros: {erros}")
    
    # Atualizar campos vazios
    print("\nAtualizando campos vazios...")
    mutuarios_db = Mutuario.objects.all()
    
    # Reprocessar arquivo para atualizar
    mutuarios_map = {}
    with open(arquivo, 'r', encoding='latin-1') as f:
        next(f)  # Pular cabeçalho
        for linha in f:
            try:
                campos = linha.strip().split('\t')
                if len(campos) < 9:
                    continue
                
                tipo = campos[3].strip()
                if tipo != '00':
                    continue
                
                try:
                    codigo = str(int(campos[1].strip()))
                except:
                    codigo = campos[1].strip()
                    
                cpf_raw = campos[6].strip() if len(campos) > 6 else ''
                cpf = ''
                if cpf_raw:
                    cpf_num = cpf_raw.zfill(11)
                    if len(cpf_num) == 11:
                        cpf = f"{cpf_num[0:3]}.{cpf_num[3:6]}.{cpf_num[6:9]}-{cpf_num[9:11]}"
                
                mutuarios_map[codigo] = {
                    'nome': campos[4].strip(),
                    'cpf': cpf,
                    'ident': campos[7].strip() if len(campos) > 7 else '',
                    'dtnasc': parse_data(campos[8].strip()) if len(campos) > 8 else None,
                }
            except:
                continue
    
    for mutuario in mutuarios_db:
        if mutuario.codigo in mutuarios_map:
            dados = mutuarios_map[mutuario.codigo]
            atualizado = False
            
            if not mutuario.nome or mutuario.nome.strip() == '':
                mutuario.nome = dados['nome']
                atualizado = True
            
            if not mutuario.cpf or mutuario.cpf.strip() == '':
                mutuario.cpf = dados['cpf']
                atualizado = True
            
            if not mutuario.ident or mutuario.ident.strip() == '':
                mutuario.ident = dados['ident']
                atualizado = True
            
            if not mutuario.dtnasc and dados['dtnasc']:
                mutuario.dtnasc = dados['dtnasc']
                atualizado = True
            
            if atualizado:
                mutuario.save()
                atualizados += 1
                if atualizados % 100 == 0:
                    print(f"Atualizados {atualizados} mutuários...")
    
    print(f"✅ Mutuários atualizados: {atualizados}")
    print(f"⏭️  Linhas puladas: {pulados}")
    print()


if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("ATUALIZAÇÃO DE CADASTROS - Contrato.txt e Mutuario.txt")
    print("=" * 80)
    print("Este script irá:")
    print("- Criar novos registros se não existirem")
    print("- Atualizar APENAS campos vazios em registros existentes")
    print("- Preservar todos os dados já cadastrados")
    print("=" * 80)
    
    resposta = input("\nDeseja continuar? (S/N): ")
    
    if resposta.upper() != 'S':
        print("Operação cancelada.")
        sys.exit(0)
    
    print("\n🚀 Iniciando importação...\n")
    
    # Importar contratos primeiro
    importar_contratos()
    
    # Depois importar mutuários
    importar_mutuarios()
    
    print("=" * 80)
    print("✅ IMPORTAÇÃO CONCLUÍDA!")
    print("=" * 80)
