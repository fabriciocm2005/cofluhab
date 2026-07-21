"""
Reimporta TODOS os endereços do Contrato.txt, atualizando os existentes
"""
import django
import os
import sys

sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Mutuario, Endereco

print("=" * 80)
print("REIMPORTANDO ENDEREÇOS DO CONTRATO.TXT COM CIDADE")
print("=" * 80)

# Mapeamento conjunto -> cidade
CONJUNTO_CIDADE = {
    '001': 'NOVA FRIBURGO',
    '002': 'NOVA FRIBURGO',
    '003': 'NOVA FRIBURGO',
    '004': 'NOVA FRIBURGO',
    '005': 'NOVA FRIBURGO',
    '006': 'NOVA FRIBURGO',
    '008': 'NOVA FRIBURGO',
    '009': 'NOVA FRIBURGO',
    '010': 'MARICÁ',
    '011': 'MARICÁ',
    '012': 'NOVA FRIBURGO',
}

arquivo = 'dados_antigos/acerto_cadmut/Contrato.txt'

enderecos_contrato = {}
print(f"\n📂 Lendo {arquivo}...")

with open(arquivo, 'r', encoding='latin-1') as f:
    for linha in f:
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
            
            enderecos_contrato[codigo] = {
                'endereco': endereco_completo,
                'uf': uf,
                'cep': cep
            }
        except:
            continue

print(f"✅ {len(enderecos_contrato)} endereços carregados do Contrato.txt")

# Processar TODOS os mutuários
print(f"\n🔍 Processando mutuários...")

criados = 0
atualizados = 0
erros = 0

for mutuario in Mutuario.objects.all():
    if mutuario.codigo not in enderecos_contrato:
        continue
    
    try:
        end_data = enderecos_contrato[mutuario.codigo]
        
        # Determinar cidade pelo conjunto
        cidade = CONJUNTO_CIDADE.get(mutuario.conjunto, '')
        
        # Criar ou buscar endereço
        endereco, created = Endereco.objects.get_or_create(
            endereco=end_data['endereco'],
            defaults={
                'numero': '',
                'compl': '',
                'bairro': '',
                'cidade': cidade,
                'uf': end_data['uf'],
                'cep': end_data['cep']
            }
        )
        
        # Se o endereço já existe mas não tem cidade, atualizar
        if not created and not endereco.cidade and cidade:
            endereco.cidade = cidade
            endereco.save(update_fields=['cidade'])
        
        # Vincular ao mutuário (substituir se já tiver)
        if mutuario.endereco_fk != endereco:
            mutuario.endereco_fk = endereco
            mutuario.save(update_fields=['endereco_fk'])
            if created:
                criados += 1
            else:
                atualizados += 1
            
            if (criados + atualizados) <= 10:
                print(f"  ✓ {mutuario.codigo} (Conjunto {mutuario.conjunto}): {end_data['endereco'][:40]}... - {cidade}")
    
    except Exception as e:
        erros += 1
        if erros <= 3:
            print(f"  ❌ Erro no mutuário {mutuario.codigo}: {e}")

print(f"\n✅ {criados} endereços novos criados")
print(f"✅ {atualizados} endereços atualizados/vinculados")
print(f"❌ {erros} erros")

# Relatório final por conjunto
print("\n" + "=" * 80)
print("RELATÓRIO FINAL POR CONJUNTO")
print("=" * 80)

for conjunto, cidade in sorted(CONJUNTO_CIDADE.items()):
    mutuarios_conj = Mutuario.objects.filter(conjunto=conjunto)
    total = mutuarios_conj.count()
    com_endereco = mutuarios_conj.filter(endereco_fk__isnull=False).count()
    com_cidade = mutuarios_conj.filter(endereco_fk__isnull=False, endereco_fk__cidade=cidade).count()
    
    print(f"\nConjunto {conjunto} - {cidade}:")
    print(f"   Total mutuários: {total}")
    print(f"   Com endereço: {com_endereco}")
    print(f"   Com cidade correta: {com_cidade}")
    print(f"   Cobertura: {(com_endereco/total*100) if total > 0 else 0:.1f}%")

print("\n✅ REIMPORTAÇÃO CONCLUÍDA!")
