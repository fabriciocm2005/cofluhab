#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SCRIPT DE APLICAÇÃO DE CORREÇÕES AUTOMÁTICAS
Assim que a CEF confirmar que UFS = 35 e DV = 9

Execute este script APÓS a resposta da CEF
"""

import os
import sys

# Configuração de valores fornecidos pela CEF
CEF_UFS_CORRETO = "35"  # ← Confirmar com CEF
CEF_DV_CORRETO = "9"    # ← Confirmar com CEF (provavelmente 9)

print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║        SCRIPT DE APLICAÇÃO DE CORREÇÕES - FH1 FICHA HABILITAÇÃO         ║
╚═══════════════════════════════════════════════════════════════════════════╝

ATENÇÃO: Execute este script APENAS APÓS CEF RESPONDER!

Valores aguardados:
- UFS Correto: 35 (São Paulo) ou outro confirmado
- DV Correto: 9 (calculado) ou outro confirmado

═══════════════════════════════════════════════════════════════════════════
""")

print(f"\n✓ UFS a ser aplicado: {CEF_UFS_CORRETO}")
print(f"✓ DV a ser aplicado: {CEF_DV_CORRETO}")

# Caminhos dos arquivos
arquivo_principal = r"C:\Users\fabri\cofluhab\cofluhab\principal\ficha_generators.py"

print(f"\n📁 Arquivo a modificar: {arquivo_principal}")

if not os.path.exists(arquivo_principal):
    print(f"❌ ERRO: Arquivo não encontrado: {arquivo_principal}")
    sys.exit(1)

print("✓ Arquivo encontrado")

# Mudanças a fazer
mudancas = [
    {
        'linha': 410,
        'antes': "header[0:2] = '19'",
        'depois': f"header[0:2] = '{CEF_UFS_CORRETO}'",
        'descricao': 'UFS no início do HEADER'
    },
    {
        'linha': 432,
        'antes': "header[405:407] = '19'",
        'depois': f"header[405:407] = '{CEF_UFS_CORRETO}'",
        'descricao': 'UFS na IDENTIFICAÇÃO DO LOTE (HEADER)'
    },
    {
        'linha': 726,
        'antes': "linha += '19'  # 01-02: UFS (RJ)",
        'depois': f"linha += '{CEF_UFS_CORRETO}'  # 01-02: UFS (SP)",
        'descricao': 'UFS no início das LINHAS DE DADOS'
    }
]

print("\n" + "═" * 73)
print("RESUMO DAS MUDANÇAS A FAZER:")
print("═" * 73)

for i, mudanca in enumerate(mudancas, 1):
    print(f"\n{i}. {mudanca['descricao']} (Linha {mudanca['linha']})")
    print(f"   ANTES: {mudanca['antes']}")
    print(f"   DEPOIS: {mudanca['depois']}")

print("\n" + "═" * 73)
print("\nPRÉ-REQUISITOS ANTES DE EXECUTAR:")
print("═" * 73)

checklist = [
    ("CEF confirmou que UFS = 35 (ou valor correto)?", False),
    ("CEF confirmou que DV = 9 (ou valor correto)?", False),
    ("Fez backup do arquivo ficha_generators.py?", False),
    ("Servidor Django está DESLIGADO?", False),
]

print("\n⚠️  CHECKLIST DE SEGURANÇA:\n")
for item, done in checklist:
    status = "✓" if done else "❌"
    print(f"  {status} {item}")

print("\n" + "═" * 73)
print("INSTRUÇÕES DE EXECUÇÃO:")
print("═" * 73)

print("""
1. BACKUP (CRÍTICO):
   ├─ Abra Windows Explorer
   ├─ Navegue até: C:/Users/fabri/cofluhab/cofluhab/principal/
   ├─ Clique direito em: ficha_generators.py
   ├─ Crie cópia: ficha_generators.py.BACKUP-29-01-2025
   └─ CONFIRME que o backup foi criado

2. APLICAR MUDANÇAS:
   ├─ Abra arquivo: principal/ficha_generators.py
   ├─ Vá para cada linha indicada abaixo
   ├─ Troque '19' por '35' conforme especificado
   └─ Salve o arquivo (Ctrl+S)

3. VALIDAÇÃO:
   ├─ Abra servidor Django
   ├─ Acesse: http://127.0.0.1:8000/cef/download-lote/
   ├─ Gere um lote de teste
   ├─ Verifique se arquivo tem '35' nas posições corretas
   └─ Upload para CEF

4. TESTE:
   ├─ Se erro 100820 desaparecer → ✅ SUCESSO!
   ├─ Se erro persiste → 🔄 Revise as mudanças
   └─ Se outro erro → 📧 Contate CEF

═══════════════════════════════════════════════════════════════════════════

MUDANÇAS DETALHADAS:

MUDANÇA 1 - Linha 410:
───────────────────────────────────────────────────────────────────────────

PROCURE POR:
    header[0:2] = '19'  # 01-02: UFS (1-2): Código da UFS - Padrão "19" (RJ)

TROQUE POR:
    header[0:2] = '{CEF_UFS_CORRETO}'  # 01-02: UFS (1-2): Código da UFS - SP

───────────────────────────────────────────────────────────────────────────

MUDANÇA 2 - Linha 432:
───────────────────────────────────────────────────────────────────────────

PROCURE POR:
    header[405:407] = '19'

TROQUE POR:
    header[405:407] = '{CEF_UFS_CORRETO}'

───────────────────────────────────────────────────────────────────────────

MUDANÇA 3 - Linha 726:
───────────────────────────────────────────────────────────────────────────

PROCURE POR:
    linha += '19'  # 01-02: UFS (RJ)

TROQUE POR:
    linha += '{CEF_UFS_CORRETO}'  # 01-02: UFS (SP)

═══════════════════════════════════════════════════════════════════════════

ROLLBACK RÁPIDO (Se algo der errado):

Opção 1 - Manual:
  ├─ Troque '35' de volta para '19' nas 3 linhas
  └─ Salve o arquivo

Opção 2 - Git (Se estiver usando):
  ├─ git checkout principal/ficha_generators.py
  └─ Volta ao estado anterior

Opção 3 - Restaurar Backup:
  ├─ Copie: ficha_generators.py.BACKUP-29-01-2025
  ├─ Cole sobre: ficha_generators.py
  └─ Arquivo restaurado

═══════════════════════════════════════════════════════════════════════════

TESTE DE VALIDAÇÃO (após mudanças):

Abra terminal e execute:

    python manage.py shell

Depois, no shell Python:

    from principal.ficha_generators import GeradorLoteFH1
    gerador = GeradorLoteFH1(tipo='FH1', matricula_agente='000049')
    header = gerador.gerar_header_fh1(1)
    print(f"UFS início: {header[0:2]}")    # Deve mostrar: 35
    print(f"UFS LOTE: {header[405:407]}")  # Deve mostrar: 35

═══════════════════════════════════════════════════════════════════════════

CONTATO DE SUPORTE:

Se as mudanças falharem ou der erro após aplicá-las:
1. Verifique se as 3 linhas foram todas atualizadas
2. Verifique se não há espaços ou caracteres extras
3. Reinicie o servidor Django
4. Se continuar com erro 100820, contate CEF novamente

═══════════════════════════════════════════════════════════════════════════

PRÓXIMOS PASSOS APÓS SUCESSO:

1. ✅ Sistema aceita lotes em CEF
2. ✅ Testes com dados reais (contratos, mutuários)
3. ✅ Configuração de retornos automáticos
4. ✅ Integração de processamento de respostas
5. ✅ Deploy em produção

═══════════════════════════════════════════════════════════════════════════
""".format(CEF_UFS_CORRETO=CEF_UFS_CORRETO, CEF_DV_CORRETO=CEF_DV_CORRETO))

print("\n✅ Script de instrução preparado")
print("📧 Aguardando confirmação da CEF com valores corretos")
print("🚀 Assim que receber, execute as mudanças acima")
