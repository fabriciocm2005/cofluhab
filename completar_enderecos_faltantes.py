"""
Completa endereços faltantes de contratos/mutuários usando CADEND.DBF
"""
import django
import os
import sys
from dbfread import DBF

sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato, Mutuario, Endereco

print("=" * 80)
print("COMPLETANDO ENDEREÇOS FALTANTES")
print("=" * 80)

# 1. Verificar situação atual
mutuarios_sem_endereco = Mutuario.objects.filter(endereco_fk__isnull=True).count()
total_mutuarios = Mutuario.objects.count()

print(f"\n📊 Situação Atual:")
print(f"   Total de mutuários: {total_mutuarios}")
print(f"   Mutuários sem endereço: {mutuarios_sem_endereco}")

# 2. Ler CADEND.DBF
dbf_path = 'dados_antigos/CADEND.DBF'
print(f"\n📂 Lendo {dbf_path}...")

def safe_text(value):
    if value is None:
        return ''
    if isinstance(value, bytes):
        return value.decode('latin-1', errors='ignore').strip()
    return str(value).strip()

enderecos_dbf = {}
erros = 0
try:
    table = DBF(dbf_path, raw=True)  # raw=True para evitar conversões que causam erros
    for record in table:
        try:
            codigo = safe_text(record.get('CODIGO', ''))
            if not codigo:
                continue
                
            # Normalizar código
            try:
                codigo_norm = str(int(codigo))
            except:
                codigo_norm = codigo
            
            endereco_obj = {
                'logradouro': safe_text(record.get('ENDERECO', '')),
                'numero': safe_text(record.get('NUMERO', '')),
                'complemento': safe_text(record.get('COMPL', '')),
                'bairro': safe_text(record.get('BAIRRO', '')),
                'cidade': safe_text(record.get('CIDADE', '')),
                'uf': safe_text(record.get('UF', '')),
                'cep': safe_text(record.get('CEP', '')),
            }
            
            enderecos_dbf[codigo_norm] = endereco_obj
        except Exception as e:
            erros += 1
            if erros <= 3:
                print(f"  ⚠️  Erro ao processar registro: {e}")
            continue
    
    print(f"✅ {len(enderecos_dbf)} endereços carregados do DBF")
    if erros > 0:
        print(f"⚠️  {erros} registros com erro foram ignorados")
except Exception as e:
    print(f"❌ Erro ao ler DBF: {e}")
    sys.exit(1)

# 3. Processar mutuários sem endereço
print("\n🔍 Processando mutuários sem endereço...")

mutuarios_atualizados = 0
for mutuario in Mutuario.objects.filter(endereco_fk__isnull=True):
    if mutuario.codigo in enderecos_dbf:
        end_data = enderecos_dbf[mutuario.codigo]
        
        # Verificar se já existe esse endereço
        endereco, created = Endereco.objects.get_or_create(
            endereco=end_data['logradouro'] or '',
            numero=end_data['numero'] or '',
            compl=end_data['complemento'] or '',
            bairro=end_data['bairro'] or '',
            cidade=end_data['cidade'] or '',
            defaults={
                'uf': end_data['uf'] or '',
                'cep': end_data['cep'] or ''
            }
        )
        
        mutuario.endereco_fk = endereco
        mutuario.save(update_fields=['endereco_fk'])
        mutuarios_atualizados += 1
        
        if mutuarios_atualizados <= 5:
            print(f"  ✓ Mutuário {mutuario.codigo}: {end_data['logradouro']}, {end_data['cidade']}")

print(f"\n✅ {mutuarios_atualizados} mutuários atualizados")

# 4. Relatório final
print("\n" + "=" * 80)
print("RELATÓRIO FINAL")
print("=" * 80)

mutuarios_ainda_sem = Mutuario.objects.filter(endereco_fk__isnull=True).count()

print(f"\n📊 Após processamento:")
print(f"   Mutuários atualizados: {mutuarios_atualizados}")
print(f"   Mutuários ainda sem endereço: {mutuarios_ainda_sem}")
print(f"   Taxa de sucesso: {(mutuarios_atualizados / mutuarios_sem_endereco * 100):.1f}%")

print("\n✅ PROCESSAMENTO CONCLUÍDO!")
