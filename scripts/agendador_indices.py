"""
Agendador Automático de Coleta de Índices
Executa todo dia 30 do mês às 08:00
"""
import schedule
import time
import subprocess
from datetime import datetime
import os


def coletar_indices_automatico():
    """Função executada pelo agendador"""
    print(f"\n{'='*80}")
    print(f"EXECUCAO AUTOMATICA AGENDADA")
    print(f"   Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    try:
        # Executar coleta usando script simplificado (sem emojis)
        print("Coletando indices do Banco Central...")
        resultado = subprocess.run(
            'py scripts/coletar_indices_simples.py',
            shell=True,
            capture_output=True,
            text=True
        )
        
        if resultado.returncode == 0:
            print("[OK] Coleta realizada com sucesso!")
            print(resultado.stdout)
            
            # Opcionalmente, aplicar atualização automática
            # Descomente as linhas abaixo para atualização automática
            # print("\nAplicando atualizacao monetaria automatica...")
            # subprocess.run(
            #     'py scripts/atualizar_saldo_monetario.py --acao aplicar --indice 0.5',
            #     shell=True
            # )
        else:
            print(f"[ERRO] Erro na coleta: {resultado.stderr}")
            
    except Exception as e:
        print(f"[ERRO] Erro: {str(e)}")


def iniciar_agendador():
    """Inicia o agendador em loop contínuo"""
    print(f"\n{'='*80}")
    print(f"AGENDADOR DE COLETA DE INDICES INICIADO")
    print(f"{'='*80}")
    print(f"   Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"   Próxima execução: Todo dia 30 às 08:00")
    print(f"   Pressione Ctrl+C para parar")
    print(f"{'='*80}\n")
    
    # Agendar para todo dia 30 às 08:00
    schedule.every().day.at("08:00").do(
        lambda: coletar_indices_automatico() if datetime.now().day == 30 else None
    )
    
    # Também executar imediatamente na primeira vez (opcional)
    executar_agora = input("❓ Executar coleta agora? (S/N): ").strip().upper()
    if executar_agora == 'S':
        coletar_indices_automatico()
    
    print("\n⏳ Agendador em execução... (Ctrl+C para parar)\n")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(3600)  # Verificar a cada hora
    except KeyboardInterrupt:
        print("\n\n🛑 Agendador finalizado pelo usuário")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Agendador automático de coleta de índices'
    )
    parser.add_argument('--modo', 
                       choices=['iniciar', 'executar-agora', 'task-scheduler'],
                       default='iniciar',
                       help='Modo de operação')
    
    args = parser.parse_args()
    
    if args.modo == 'executar-agora':
        coletar_indices_automatico()
    elif args.modo == 'task-scheduler':
        # Apenas executar (para ser chamado pelo Task Scheduler do Windows)
        coletar_indices_automatico()
    else:
        iniciar_agendador()
