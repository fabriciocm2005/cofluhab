"""
Validar se o campo FCVS está correto no nosso sistema
Comparando com o padrão do sistema antigo (≈ 3% da prestação)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Contrato, ParcelaContrato
from decimal import Decimal

print("=" * 80)
print("VALIDAÇÃO DO CAMPO FCVS")
print("=" * 80)

# Verificar parcelas que têm FCVS
parcelas_com_fcvs = ParcelaContrato.objects.filter(fcvs__isnull=False, fcvs__gt=0).count()
total_parcelas = ParcelaContrato.objects.count()

print(f"\n📊 Estatísticas:")
print(f"   Total de parcelas: {total_parcelas}")
print(f"   Parcelas com FCVS: {parcelas_com_fcvs}")
print(f"   Percentual: {(parcelas_com_fcvs/total_parcelas)*100:.2f}%")

print("\n" + "=" * 80)
print("ANÁLISE DO CAMPO FCVS (Amostra de 20 parcelas):")
print("=" * 80)

# Buscar parcelas com FCVS e vlautent
parcelas_amostra = ParcelaContrato.objects.filter(
    fcvs__isnull=False, 
    fcvs__gt=0
).select_related('contrato')[:20]

if parcelas_amostra:
    print(f"\n{'Contrato':<10} {'Parcela':<8} {'Prestação':<15} {'FCVS':<15} {'% FCVS':<10}")
    print("-" * 80)
    
    soma_percentuais = Decimal('0')
    count_validos = 0
    
    for p in parcelas_amostra:
        # Calcular valor da prestação
        prestacao = Decimal('0')
        if p.vlautent and p.vlautent > 0:
            prestacao = p.vlautent
        else:
            if p.juros: prestacao += p.juros
            if p.amort: prestacao += p.amort
            if p.seguro: prestacao += p.seguro
            if p.tca: prestacao += p.tca
            if p.em: prestacao += p.em
            if p.rp: prestacao += p.rp
        
        if prestacao > 0:
            percentual = (p.fcvs / prestacao) * 100
            soma_percentuais += percentual
            count_validos += 1
            
            print(f"{p.contrato.codigo:<10} {p.nmens:<8} R$ {prestacao:>10,.2f}   R$ {p.fcvs:>10,.2f}   {percentual:>6.2f}%")
    
    if count_validos > 0:
        media_percentual = soma_percentuais / count_validos
        
        print("\n" + "=" * 80)
        print(f"📊 RESULTADO DA ANÁLISE:")
        print("=" * 80)
        print(f"\n   Média do percentual FCVS: {media_percentual:.3f}%")
        
        if 2.5 < media_percentual < 3.5:
            print(f"   ✅ CORRETO! O FCVS está próximo de 3% (padrão do sistema antigo)")
        elif media_percentual < 0.1:
            print(f"   ⚠️  VALORES MUITO BAIXOS - Possível problema de conversão monetária")
        else:
            print(f"   ⚠️  VALORES FORA DO PADRÃO - Esperado ≈ 3%")

else:
    print("\n❌ Nenhuma parcela com FCVS encontrada!")

print("\n" + "=" * 80)
print("VERIFICANDO CONTRATOS DO FCVS.DBF ANTIGO:")
print("=" * 80)

# Verificar se os contratos do sistema antigo existem
codigos_antigos = ['005014', '005019', '005054', '005063', '005064', '005065', 
                   '005066', '005068', '005075', '005076']

print(f"\nVerificando {len(codigos_antigos)} contratos do sistema antigo...")

for codigo in codigos_antigos:
    # Remover zeros à esquerda para buscar
    codigo_busca = codigo.lstrip('0')
    
    contrato = Contrato.objects.filter(codigo=codigo_busca).first()
    
    if contrato:
        ultima_parcela = ParcelaContrato.objects.filter(
            contrato=contrato
        ).order_by('-nmens').first()
        
        if ultima_parcela and ultima_parcela.fcvs:
            print(f"   ✓ {codigo}: Encontrado - Última parcela FCVS = R$ {ultima_parcela.fcvs:,.2f}")
        else:
            print(f"   ⚠️  {codigo}: Encontrado mas sem FCVS na última parcela")
    else:
        print(f"   ❌ {codigo}: Não encontrado no sistema")

print("\n" + "=" * 80)
print("RECOMENDAÇÕES:")
print("=" * 80)
print("""
1. Se o percentual médio está próximo de 3%:
   ✅ Campo FCVS está CORRETO!
   
2. Se o percentual está muito baixo (< 0,1%):
   ⚠️  Valores precisam de conversão monetária
   
3. Para usar o FCVS na página de saldo residual:
   - Somar todos os FCVS das parcelas não pagas
   - Esse é o valor de FCVS a recolher
   
4. Para criar relatório mensal de FCVS (como sistema antigo):
   - Listar contratos por conjunto
   - Mostrar VL_PREST e VL_FCVS da última parcela
   - Totalizar por conjunto
""")
print("=" * 80)
