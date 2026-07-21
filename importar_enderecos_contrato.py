"""
Importa endereços do arquivo Contrato.txt para os mutuários
"""
import django
import os
import sys

sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Mutuario, Endereco

print("=" * 80)
print("IMPORTANDO ENDEREÇOS DO CONTRATO.TXT")
print("=" * 80)

arquivo = 'dados_antigos/acerto_cadmut/Contrato.txt'

enderecos_importados = {}
linhas_processadas = 0
erros = 0

print(f"\n📂 Lendo {arquivo}...")

with open(arquivo, 'r', encoding='latin-1') as f:
    for linha in f:
        linhas_processadas += 1
        try:
            campos = linha.strip().split('\t')
            
            if len(campos) < 11:
                continue
            
            # Extrair dados
            codigo_raw = campos[1].strip()
            endereco_completo = campos[8].strip()
            uf = campos[9].strip()
            cep = campos[10].strip()
            
            # Normalizar código
            try:
                codigo = str(int(codigo_raw))
            except:
                codigo = codigo_raw
            
            if not codigo or not endereco_completo:
                continue
            
            # Guardar no dicionário
            if codigo not in enderecos_importados:
                enderecos_importados[codigo] = {
                    'endereco': endereco_completo,
                    'uf': uf,
                    'cep': cep
                }
        
        except Exception as e:
            erros += 1
            if erros <= 3:
                print(f"  ⚠️  Erro na linha {linhas_processadas}: {e}")
            continue

print(f"\n✅ {len(enderecos_importados)} endereços únicos carregados")
print(f"📊 {linhas_processadas} linhas processadas")

# Verificar código 6000
if '6000' in enderecos_importados:
    print(f"\n✅ Código 6000 encontrado!")
    print(f"   Endereço: {enderecos_importados['6000']['endereco']}")
else:
    print(f"\n⚠️  Código 6000 NÃO encontrado no arquivo")

# Processar mutuários sem endereço
print(f"\n🔍 Processando mutuários sem endereço...")

mutuarios_sem_endereco = Mutuario.objects.filter(endereco_fk__isnull=True)
total_sem_endereco = mutuarios_sem_endereco.count()
atualizados = 0

print(f"   {total_sem_endereco} mutuários sem endereço")

for mutuario in mutuarios_sem_endereco:
    if mutuario.codigo in enderecos_importados:
        end_data = enderecos_importados[mutuario.codigo]
        
        # Tentar separar endereço em partes (rua, número, complemento)
        endereco_full = end_data['endereco']
        
        # Criar ou buscar o registro de endereço
        endereco, created = Endereco.objects.get_or_create(
            endereco=endereco_full,
            defaults={
                'numero': '',
                'compl': '',
                'bairro': '',
                'cidade': '',
                'uf': end_data['uf'],
                'cep': end_data['cep']
            }
        )
        
        # Vincular ao mutuário
        mutuario.endereco_fk = endereco
        mutuario.save(update_fields=['endereco_fk'])
        atualizados += 1
        
        if atualizados <= 5:
            print(f"  ✓ Mutuário {mutuario.codigo}: {endereco_full[:50]}...")

print(f"\n✅ {atualizados} mutuários atualizados")

# Relatório final
print("\n" + "=" * 80)
print("RELATÓRIO FINAL")
print("=" * 80)

mutuarios_ainda_sem = Mutuario.objects.filter(endereco_fk__isnull=True).count()
total_mutuarios = Mutuario.objects.count()
com_endereco = total_mutuarios - mutuarios_ainda_sem

print(f"\n📊 Status final:")
print(f"   Total de mutuários: {total_mutuarios}")
print(f"   Com endereço: {com_endereco} ({com_endereco/total_mutuarios*100:.1f}%)")
print(f"   Sem endereço: {mutuarios_ainda_sem} ({mutuarios_ainda_sem/total_mutuarios*100:.1f}%)")

print("\n✅ IMPORTAÇÃO CONCLUÍDA!")
