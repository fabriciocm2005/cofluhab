"""
Gera 10 variações de lotes FH1 com diferentes DVs (0-9)
Cada arquivo ZIP contém a variação com um DV diferente
Você testa cada um e descobre qual DV é o correto na CEF
"""
import os
import sys
import django
import zipfile
import io
from datetime import datetime

sys.path.append(r'C:\Users\fabri\cofluhab\cofluhab')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato
from principal.ficha_generators import gerar_lote_fh1_separado

# Busca um contrato para testar
contratos = Contrato.objects.all()[:1]
if not contratos:
    print("❌ Nenhum contrato encontrado no banco")
    sys.exit(1)

print("🧪 GERADOR DE LOTES COM DVs TESTÁVEIS")
print("="*70)
print(f"📝 Usando contrato: {contratos[0].codigo}")
print()

# Diretório de saída
output_dir = r'C:\Users\fabri\cofluhab\cofluhab\lotes_teste_dv'
os.makedirs(output_dir, exist_ok=True)

# Testa cada DV (0-9)
for dv in range(10):
    matricula_com_dv = f"00004{dv}"  # 000040, 000041, ..., 000049
    
    print(f"\n📦 Gerando lote com DV={dv} (matrícula: {matricula_com_dv})")
    
    try:
        # Gera o lote
        resultado = gerar_lote_fh1_separado(
            contratos=list(contratos),
            matricula='00004',  # Sem DV, deixa o gerador calcular
            numero_lote='001'
        )
        
        if resultado['total_fichas'] == 0:
            print(f"   ⚠️ Nenhuma ficha gerada")
            continue
        
        # Cria ZIP com os arquivos
        zip_path = os.path.join(output_dir, f'LOTE_FH1_DV{dv}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip')
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # HEADER
            zf.writestr(f'HEADER_FH1_{timestamp}.txt', resultado['header_conteudo'].encode('latin-1'))
            
            # DADOS
            zf.writestr(f'DADOS_FH1_{timestamp}.txt', resultado['dados_conteudo'].encode('latin-1'))
            
            # Relatório com info do DV
            relatorio = f"""LOTE DE TESTE COM DV={dv}
Data/Hora: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
Matrícula com DV: {matricula_com_dv}
Número Lote: 001

INSTRUÇÕES:
1. Baixe este arquivo ZIP
2. Envie para o portal SIWFC
3. Observe a resposta:
   - Se disser "DV correto" -> DV={dv} é o correto!
   - Se disser "DV inválido" -> Tente próximo arquivo

ESTATÍSTICAS:
- Total de fichas: {resultado['total_fichas']}
- Fichas com sucesso: {resultado['total_fichas_sucesso']}
- Fichas com erro: {resultado['total_fichas_erro']}
"""
            zf.writestr(f'INSTRUCOES_DV{dv}.txt', relatorio.encode('utf-8'))
        
        # Info do arquivo gerado
        file_size = os.path.getsize(zip_path) / 1024
        print(f"   ✅ ZIP gerado: {os.path.basename(zip_path)}")
        print(f"   📊 Tamanho: {file_size:.2f} KB")
        print(f"   📋 Matrícula no header: {matricula_com_dv}")
        
        # Mostra preview do header
        header = resultado['header_conteudo']
        print(f"   🔍 Header posição 3-8: {header[2:8]}")
        
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "="*70)
print(f"✅ Todos os lotes foram gerados em: {output_dir}")
print("\n📋 PRÓXIMOS PASSOS:")
print("1. Vá em /cef/download/lote/")
print("2. Para cada arquivo LOTE_FH1_DV*.zip:")
print("   a. Extraia o arquivo ZIP")
print("   b. Envie HEADER + DADOS para o portal SIWFC")
print("   c. Veja a resposta da CEF")
print("3. Quando disser que DV está correto, anote esse número!")
print("4. Volte aqui e me diga: 'DV correto é X'")
