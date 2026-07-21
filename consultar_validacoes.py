import os
import sys
import django

os.chdir(r'C:\Users\fabri\cofluhab\cofluhab')
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import ValidacaoAI, AprendizadoAI

print("="*80)
print("ÚLTIMAS VALIDAÇÕES")
print("="*80)

validacoes = ValidacaoAI.objects.all().order_by('-data_validacao')[:3]
for v in validacoes:
    print(f"\n📋 ID: {v.id} | {v.tipo_arquivo} | {v.status}")
    print(f"🤖 Agentes: {v.agentes_utilizados}")
    print(f"🔧 Auto-correção: {v.correcao_automatica}")
    print(f"📦 Tamanho: {v.tamanho_arquivo} bytes")
    print(f"⏱️ Tempo: {v.tempo_execucao:.2f}s")
    
    if v.erros_encontrados:
        print(f"\n❌ Erros:\n{v.erros_encontrados[:300]}...")
    
    if v.correcoes_aplicadas:
        print(f"\n✅ Correções aplicadas:\n{v.correcoes_aplicadas[:300]}...")
    
    if v.relatorio_completo:
        print(f"\n📊 Relatório (preview):\n{v.relatorio_completo[:400]}...")

print("\n" + "="*80)
print("APRENDIZADOS AI")
print("="*80)

aprendizados = AprendizadoAI.objects.all()
print(f"Total de aprendizados: {aprendizados.count()}")

if aprendizados.exists():
    for apr in aprendizados[:5]:
        print(f"\n🧠 {apr.tipo_erro} ({apr.ocorrencias}x)")
        print(f"   Prioridade: {apr.prioridade}")
        print(f"   Implementado: {'✅' if apr.implementado else '⏳'}")
        print(f"   Causa: {apr.causa_raiz[:100]}...")
