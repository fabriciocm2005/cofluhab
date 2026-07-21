"""
Sistema de Atualização Monetária Automática dos Saldos Devedores
Aplica correção mensal baseada em índices oficiais (INPC, IPCA, TR, etc.)
"""
import os
import sys
import django
from datetime import datetime, date
from decimal import Decimal

# Setup Django
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato, ParcelaContrato
import sqlite3


# Índices de correção monetária (valores de exemplo - atualizar com dados reais)
INDICES_MENSAIS = {
    # Formato: 'AAAA-MM': percentual (ex: 0.0150 = 1.50%)
    '2023-11': Decimal('0.0028'),  # 0.28%
    '2023-12': Decimal('0.0056'),  # 0.56%
    '2024-01': Decimal('0.0042'),  # 0.42%
    '2024-02': Decimal('0.0083'),  # 0.83%
    '2024-03': Decimal('0.0016'),  # 0.16%
    '2024-04': Decimal('0.0038'),  # 0.38%
    '2024-05': Decimal('0.0046'),  # 0.46%
    '2024-06': Decimal('0.0021'),  # 0.21%
    '2024-07': Decimal('0.0038'),  # 0.38%
    '2024-08': Decimal('0.0002'),  # 0.02%
    '2024-09': Decimal('0.0044'),  # 0.44%
    '2024-10': Decimal('0.0056'),  # 0.56%
    '2024-11': Decimal('0.0039'),  # 0.39%
    '2025-01': Decimal('0.0042'),  # Projeção
}


def criar_tabela_historico():
    """Cria tabela para registrar histórico de atualizações monetárias"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db.sqlite3')
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS atualizacao_monetaria_historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_atualizacao DATETIME,
            mes_referencia TEXT,
            indice_aplicado REAL,
            total_contratos INTEGER,
            total_parcelas_atualizadas INTEGER,
            valor_total_corrigido REAL,
            observacoes TEXT
        )
    """)
    
    conn.commit()
    conn.close()
    print("[OK] Tabela de historico criada/verificada")


def obter_ultimo_mes_atualizado():
    """Verifica qual foi o último mês com atualização aplicada"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db.sqlite3')
    
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("""
            SELECT mes_referencia 
            FROM atualizacao_monetaria_historico 
            ORDER BY data_atualizacao DESC 
            LIMIT 1
        """)
        resultado = cur.fetchone()
        conn.close()
        
        if resultado:
            return resultado[0]
    except:
        pass
    
    return None


def aplicar_correcao_mensal(mes_referencia, indice, modo='simulacao'):
    """
    Aplica correção monetária em todos os saldos devedores
    
    Args:
        mes_referencia: String no formato 'AAAA-MM'
        indice: Decimal com o percentual (ex: 0.0150 para 1.50%)
        modo: 'simulacao' ou 'aplicar'
    """
    print(f"\n{'='*80}")
    print(f"{'SIMULACAO DE' if modo == 'simulacao' else 'APLICANDO'} ATUALIZACAO MONETARIA")
    print(f"   Mes de Referencia: {mes_referencia}")
    print(f"   Índice de Correção: {float(indice * 100):.4f}%")
    print(f"{'='*80}\n")
    
    contratos = Contrato.objects.all()
    total_contratos = 0
    total_parcelas = 0
    valor_total_corrigido = Decimal('0')
    
    for contrato in contratos:
        # Pegar última parcela (saldo mais recente)
        ultima_parcela = ParcelaContrato.objects.filter(
            contrato=contrato
        ).order_by('-nmens').first()
        
        if not ultima_parcela or not ultima_parcela.sddev:
            continue
        
        saldo_atual = ultima_parcela.sddev
        
        # Calcular correção
        correcao = saldo_atual * indice
        novo_saldo = saldo_atual + correcao
        
        if modo == 'aplicar':
            # Atualizar saldo na última parcela
            ultima_parcela.sddev = novo_saldo
            ultima_parcela.save()
            
            # Se houver campo CM (correção monetária), atualizar também
            if hasattr(ultima_parcela, 'cm'):
                ultima_parcela.cm = (ultima_parcela.cm or Decimal('0')) + correcao
                ultima_parcela.save()
        
        total_contratos += 1
        total_parcelas += 1
        valor_total_corrigido += correcao
        
        if total_contratos <= 5:  # Mostrar primeiros 5 exemplos
            print(f"  Contrato {contrato.codigo}:")
            print(f"    Saldo Anterior: R$ {saldo_atual:,.2f}")
            print(f"    Correção: R$ {correcao:,.2f}")
            print(f"    Novo Saldo: R$ {novo_saldo:,.2f}")
            print()
    
    print(f"\nRESUMO DA ATUALIZACAO:")
    print(f"   Total de Contratos Atualizados: {total_contratos}")
    print(f"   Total de Parcelas Modificadas: {total_parcelas}")
    print(f"   Valor Total Corrigido: R$ {valor_total_corrigido:,.2f}")
    
    if modo == 'aplicar':
        # Registrar no histórico
        registrar_historico(
            mes_referencia, 
            float(indice), 
            total_contratos, 
            total_parcelas, 
            float(valor_total_corrigido)
        )
        print(f"\n[OK] ATUALIZACAO APLICADA COM SUCESSO!")
    else:
        print(f"\n[AVISO] MODO SIMULACAO - Nenhuma alteracao foi salva no banco")
        print(f"    Para aplicar, execute com modo='aplicar'")
    
    print(f"\n{'='*80}\n")
    
    return {
        'contratos': total_contratos,
        'parcelas': total_parcelas,
        'valor_corrigido': float(valor_total_corrigido)
    }


def registrar_historico(mes_ref, indice, contratos, parcelas, valor_corrigido):
    """Registra a atualização no histórico"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db.sqlite3')
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO atualizacao_monetaria_historico 
        (data_atualizacao, mes_referencia, indice_aplicado, 
         total_contratos, total_parcelas_atualizadas, valor_total_corrigido, observacoes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        mes_ref,
        indice,
        contratos,
        parcelas,
        valor_corrigido,
        f"Atualização automática mensal - Índice {indice*100:.4f}%"
    ))
    
    conn.commit()
    conn.close()


def listar_historico():
    """Lista todas as atualizações já aplicadas"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db.sqlite3')
    
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("""
            SELECT data_atualizacao, mes_referencia, indice_aplicado, 
                   total_contratos, valor_total_corrigido
            FROM atualizacao_monetaria_historico
            ORDER BY data_atualizacao DESC
            LIMIT 10
        """)
        
        print(f"\n{'='*80}")
        print(f"📜 HISTÓRICO DE ATUALIZAÇÕES MONETÁRIAS (Últimas 10)")
        print(f"{'='*80}\n")
        
        resultados = cur.fetchall()
        if not resultados:
            print("  Nenhuma atualização registrada ainda.\n")
        else:
            for row in resultados:
                data, mes, indice, contratos, valor = row
                print(f"  📅 {data[:16]} | Mês: {mes} | Índice: {indice*100:.4f}%")
                print(f"     Contratos: {contratos} | Valor Corrigido: R$ {valor:,.2f}\n")
        
        conn.close()
        print(f"{'='*80}\n")
    except Exception as e:
        print(f"[ERRO] Erro ao listar historico: {e}")


def atualizar_mes_atual():
    """Atualiza o mês atual baseado nos índices cadastrados"""
    hoje = date.today()
    mes_atual = hoje.strftime('%Y-%m')
    
    # Verificar se já foi atualizado
    ultimo_mes = obter_ultimo_mes_atualizado()
    if ultimo_mes == mes_atual:
        print(f"⚠️  Mês {mes_atual} já foi atualizado anteriormente.")
        print(f"   Última atualização: {ultimo_mes}")
        return
    
    # Verificar se existe índice para o mês
    if mes_atual not in INDICES_MENSAIS:
        print(f"[ERRO] Indice nao disponivel para {mes_atual}")
        print(f"   Adicione o índice em INDICES_MENSAIS no script")
        return
    
    indice = INDICES_MENSAIS[mes_atual]
    
    # Primeiro simular
    print("\n🔍 Executando SIMULAÇÃO primeiro...")
    aplicar_correcao_mensal(mes_atual, indice, modo='simulacao')
    
    # Perguntar confirmação
    resposta = input("\n❓ Deseja APLICAR esta atualização? (S/N): ").strip().upper()
    
    if resposta == 'S':
        aplicar_correcao_mensal(mes_atual, indice, modo='aplicar')
    else:
        print("\n[CANCELADO] Atualizacao CANCELADA pelo usuario.")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Atualização Monetária de Saldos Devedores')
    parser.add_argument('--acao', choices=['criar-tabela', 'simular', 'aplicar', 'historico', 'mes-atual'], 
                       default='mes-atual',
                       help='Ação a executar')
    parser.add_argument('--mes', help='Mês de referência (AAAA-MM)')
    parser.add_argument('--indice', type=float, help='Índice percentual (ex: 1.5 para 1.5%%)')
    
    args = parser.parse_args()
    
    if args.acao == 'criar-tabela':
        criar_tabela_historico()
    
    elif args.acao == 'historico':
        listar_historico()
    
    elif args.acao == 'mes-atual':
        criar_tabela_historico()
        atualizar_mes_atual()
    
    elif args.acao in ['simular', 'aplicar']:
        if not args.mes or args.indice is None:
            print("[ERRO] Para simular/aplicar, forneca --mes e --indice")
        else:
            criar_tabela_historico()
            indice = Decimal(str(args.indice / 100))  # Converter para decimal
            aplicar_correcao_mensal(args.mes, indice, modo=args.acao.replace('simular', 'simulacao'))
