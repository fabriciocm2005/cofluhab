"""
Sistema de Coleta Automática de Índices do Banco Central
Busca TR, IPCA e INPC diretamente da API do Bacen
"""
import os
import sys
import django
import requests
from datetime import datetime, timedelta
from decimal import Decimal

# Setup Django
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

import sqlite3


def criar_tabela_indices():
    """Cria tabela para armazenar índices econômicos"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db.sqlite3')
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS indices_economicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mes_referencia TEXT UNIQUE,
            tr REAL,
            ipca REAL,
            inpc REAL,
            data_coleta DATETIME,
            fonte TEXT
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ Tabela de índices criada/verificada")


def buscar_indice_bacen(codigo_serie, mes_referencia):
    """
    Busca índice específico na API do Banco Central
    
    Códigos das séries:
    - TR: 226 (Taxa Referencial)
    - IPCA: 433 (Índice de Preços ao Consumidor Amplo)
    - INPC: 188 (Índice Nacional de Preços ao Consumidor)
    
    Args:
        codigo_serie: Código da série temporal do Bacen
        mes_referencia: String no formato 'AAAA-MM'
    
    Returns:
        Decimal com o valor percentual ou None
    """
    try:
        # Converter formato de data para API do Bacen
        ano, mes = mes_referencia.split('-')
        
        # API do Banco Central - SGS (Sistema Gerenciador de Séries Temporais)
        url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo_serie}/dados"
        
        # Parâmetros: último mês disponível
        params = {
            'formato': 'json'
        }
        
        print(f"   Consultando série {codigo_serie}...")
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            dados = response.json()
            
            # Procurar pelo mês específico
            # Formato retornado: [{"data": "01/11/2024", "valor": "0.39"}, ...]
            for item in reversed(dados[-60:]):  # Últimos 60 registros
                data_str = item.get('data', '')
                valor_str = item.get('valor', '')
                
                # Converter data "DD/MM/AAAA" para verificar
                try:
                    dia, mes_item, ano_item = data_str.split('/')
                    if f"{ano_item}-{mes_item}" == mes_referencia:
                        valor = float(valor_str.replace(',', '.'))
                        print(f"   ✅ Encontrado: {valor}% em {data_str}")
                        return Decimal(str(valor))
                except:
                    continue
            
            # Se não encontrou o mês exato, pegar o último disponível
            if dados:
                ultimo = dados[-1]
                valor = float(ultimo['valor'].replace(',', '.'))
                print(f"   ⚠️  Usando último disponível: {valor}% ({ultimo['data']})")
                return Decimal(str(valor))
        
        print(f"   ❌ Erro ao consultar: Status {response.status_code}")
        return None
        
    except Exception as e:
        print(f"   ❌ Erro: {str(e)}")
        return None


def coletar_indices_mes(mes_referencia=None):
    """
    Coleta todos os índices para um mês específico
    
    Args:
        mes_referencia: String 'AAAA-MM' ou None para mês anterior
    """
    if not mes_referencia:
        # Usar mês anterior como padrão
        hoje = datetime.now()
        if hoje.month == 1:
            mes_anterior = datetime(hoje.year - 1, 12, 1)
        else:
            mes_anterior = datetime(hoje.year, hoje.month - 1, 1)
        mes_referencia = mes_anterior.strftime('%Y-%m')
    
    print(f"\n{'='*80}")
    print(f"📊 COLETANDO ÍNDICES DO BANCO CENTRAL")
    print(f"   Mês de Referência: {mes_referencia}")
    print(f"   Data da Coleta: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    # Buscar cada índice
    print("🔍 Buscando TR (Taxa Referencial)...")
    tr = buscar_indice_bacen('226', mes_referencia)
    
    print("\n🔍 Buscando IPCA (Índice de Preços ao Consumidor Amplo)...")
    ipca = buscar_indice_bacen('433', mes_referencia)
    
    print("\n🔍 Buscando INPC (Índice Nacional de Preços ao Consumidor)...")
    inpc = buscar_indice_bacen('188', mes_referencia)
    
    # Salvar no banco
    if tr is not None or ipca is not None or inpc is not None:
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db.sqlite3')
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        # Verificar se já existe
        cur.execute(
            "SELECT id FROM indices_economicos WHERE mes_referencia = ?",
            (mes_referencia,)
        )
        existe = cur.fetchone()
        
        if existe:
            # Atualizar
            cur.execute("""
                UPDATE indices_economicos 
                SET tr = ?, ipca = ?, inpc = ?, data_coleta = ?, fonte = ?
                WHERE mes_referencia = ?
            """, (
                float(tr) if tr else None,
                float(ipca) if ipca else None,
                float(inpc) if inpc else None,
                datetime.now().isoformat(),
                'API Banco Central do Brasil',
                mes_referencia
            ))
            print(f"\n✅ Índices ATUALIZADOS no banco de dados")
        else:
            # Inserir
            cur.execute("""
                INSERT INTO indices_economicos 
                (mes_referencia, tr, ipca, inpc, data_coleta, fonte)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                mes_referencia,
                float(tr) if tr else None,
                float(ipca) if ipca else None,
                float(inpc) if inpc else None,
                datetime.now().isoformat(),
                'API Banco Central do Brasil'
            ))
            print(f"\n✅ Índices SALVOS no banco de dados")
        
        conn.commit()
        conn.close()
        
        # Mostrar resumo
        print(f"\n{'='*80}")
        print(f"📈 RESUMO DOS ÍNDICES - {mes_referencia}")
        print(f"{'='*80}")
        print(f"   TR (Taxa Referencial):      {float(tr):>8.4f}%" if tr else "   TR: Não disponível")
        print(f"   IPCA (Inflação Ampla):      {float(ipca):>8.4f}%" if ipca else "   IPCA: Não disponível")
        print(f"   INPC (Inflação Consumidor): {float(inpc):>8.4f}%" if inpc else "   INPC: Não disponível")
        print(f"{'='*80}\n")
        
        return {
            'mes': mes_referencia,
            'tr': float(tr) if tr else None,
            'ipca': float(ipca) if ipca else None,
            'inpc': float(inpc) if inpc else None
        }
    else:
        print(f"\n❌ Nenhum índice coletado com sucesso")
        return None


def listar_indices_salvos():
    """Lista todos os índices já coletados"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db.sqlite3')
    
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT mes_referencia, tr, ipca, inpc, data_coleta
            FROM indices_economicos
            ORDER BY mes_referencia DESC
            LIMIT 24
        """)
        
        print(f"\n{'='*80}")
        print(f"📊 ÍNDICES ECONÔMICOS SALVOS (Últimos 24 meses)")
        print(f"{'='*80}\n")
        print(f"{'Mês':<12} {'TR %':>10} {'IPCA %':>10} {'INPC %':>10} {'Data Coleta':<20}")
        print(f"{'-'*80}")
        
        resultados = cur.fetchall()
        if not resultados:
            print("  Nenhum índice salvo ainda.\n")
        else:
            for row in resultados:
                mes, tr, ipca, inpc, data_coleta = row
                tr_str = f"{tr:>8.4f}" if tr else "    -"
                ipca_str = f"{ipca:>8.4f}" if ipca else "    -"
                inpc_str = f"{inpc:>8.4f}" if inpc else "    -"
                data_str = data_coleta[:16] if data_coleta else "-"
                print(f"{mes:<12} {tr_str:>10} {ipca_str:>10} {inpc_str:>10} {data_str:<20}")
        
        conn.close()
        print(f"{'='*80}\n")
        
    except Exception as e:
        print(f"❌ Erro ao listar índices: {e}")


def coletar_ultimos_meses(quantidade=6):
    """Coleta índices dos últimos N meses"""
    print(f"\n🔄 Coletando índices dos últimos {quantidade} meses...\n")
    
    hoje = datetime.now()
    for i in range(quantidade):
        meses_atras = quantidade - i - 1
        
        # Calcular o mês
        mes_calc = hoje.month - meses_atras
        ano_calc = hoje.year
        
        while mes_calc <= 0:
            mes_calc += 12
            ano_calc -= 1
        
        mes_referencia = f"{ano_calc:04d}-{mes_calc:02d}"
        
        print(f"📅 Processando {mes_referencia}...")
        coletar_indices_mes(mes_referencia)
        print()


def atualizar_saldos_com_indice_coletado(mes_referencia, tipo_indice='ipca'):
    """
    Atualiza os saldos devedores usando índice já coletado
    
    Args:
        mes_referencia: String 'AAAA-MM'
        tipo_indice: 'tr', 'ipca' ou 'inpc'
    """
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db.sqlite3')
    
    # Buscar índice salvo
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    cur.execute(
        f"SELECT {tipo_indice} FROM indices_economicos WHERE mes_referencia = ?",
        (mes_referencia,)
    )
    resultado = cur.fetchone()
    conn.close()
    
    if not resultado or resultado[0] is None:
        print(f"❌ Índice {tipo_indice.upper()} não encontrado para {mes_referencia}")
        print(f"   Execute: py scripts\\coletar_indices_bacen.py --coletar --mes {mes_referencia}")
        return False
    
    indice = Decimal(str(resultado[0]))
    
    print(f"\n✅ Índice {tipo_indice.upper()} encontrado: {float(indice):.4f}%")
    print(f"   Iniciando atualização dos saldos devedores...\n")
    
    # Chamar o sistema de atualização monetária
    import subprocess
    cmd = f'py scripts/atualizar_saldo_monetario.py --acao aplicar --mes {mes_referencia} --indice {float(indice)}'
    
    resposta = input(f"❓ Confirma aplicação da atualização com {tipo_indice.upper()} = {float(indice):.4f}%? (S/N): ").strip().upper()
    
    if resposta == 'S':
        resultado = subprocess.run(cmd, shell=True)
        return resultado.returncode == 0
    else:
        print("❌ Atualização CANCELADA pelo usuário")
        return False


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Coleta automática de índices do Banco Central do Brasil'
    )
    parser.add_argument('--acao', 
                       choices=['criar-tabela', 'coletar', 'listar', 'ultimos-meses', 'atualizar-saldos'],
                       default='coletar',
                       help='Ação a executar')
    parser.add_argument('--mes', help='Mês de referência (AAAA-MM)')
    parser.add_argument('--quantidade', type=int, default=6, help='Quantidade de meses (para ultimos-meses)')
    parser.add_argument('--indice', choices=['tr', 'ipca', 'inpc'], default='ipca',
                       help='Tipo de índice para atualizar saldos')
    
    args = parser.parse_args()
    
    if args.acao == 'criar-tabela':
        criar_tabela_indices()
    
    elif args.acao == 'listar':
        listar_indices_salvos()
    
    elif args.acao == 'coletar':
        criar_tabela_indices()
        coletar_indices_mes(args.mes)
        listar_indices_salvos()
    
    elif args.acao == 'ultimos-meses':
        criar_tabela_indices()
        coletar_ultimos_meses(args.quantidade)
        listar_indices_salvos()
    
    elif args.acao == 'atualizar-saldos':
        if not args.mes:
            print("❌ Forneça o mês com --mes AAAA-MM")
        else:
            atualizar_saldos_com_indice_coletado(args.mes, args.indice)
