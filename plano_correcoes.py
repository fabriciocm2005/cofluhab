#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PLANO DE AÇÃO PARA CORREÇÃO DO CÓDIGO FH1
Aguardando resposta da CEF com:
1. Código UFS correto (provavelmente 35 para SP)
2. DV correto para matrícula 44

Este arquivo documenta EXATAMENTE onde fazer as mudanças.
"""

print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║           PLANO DE AÇÃO - Correções no Código FH1                        ║
╚═══════════════════════════════════════════════════════════════════════════╝

ASSUMINDO RESPOSTA DA CEF:
- UFS Correto: 35 (São Paulo)
- DV Correto: 9 (nosso cálculo atual está certo)

═══════════════════════════════════════════════════════════════════════════

MUDANÇA 1: Atualizar Código UFS no HEADER
═══════════════════════════════════════════════════════════════════════════

ARQUIVO: principal/ficha_generators.py
FUNÇÃO: gerar_header_fh1()
LINHAS: 410 e 432

ANTES:
    # Linha 410
    header[0:2] = '19'  # ← RJ (INCORRETO)
    
    # Linha 432
    header[405:407] = '19'  # ← RJ (INCORRETO)

DEPOIS:
    # Linha 410
    header[0:2] = '35'  # ← SP (CORRETO)
    
    # Linha 432
    header[405:407] = '35'  # ← SP (CORRETO)

═══════════════════════════════════════════════════════════════════════════

MUDANÇA 2: Atualizar Código UFS nas LINHAS DE DADOS
═══════════════════════════════════════════════════════════════════════════

ARQUIVO: principal/ficha_generators.py
FUNÇÃO: gerar_lote_fh1_separado()
LINHA: 726

ANTES:
    linha += '19'  # 01-02: UFS (RJ) - INCORRETO

DEPOIS:
    linha += '35'  # 01-02: UFS (SP) - CORRETO

═══════════════════════════════════════════════════════════════════════════

MUDANÇA 3 (OPCIONAL): Se DV for diferente de 9
═══════════════════════════════════════════════════════════════════════════

Se a CEF responder que o DV correto NÃO é 9, será necessário:

ARQUIVO: principal/ficha_generators.py
FUNÇÃO: calcular_dv_modulo11()
LINHAS: ~651-662

SUBSTITUIR A FUNÇÃO INTEIRA COM ALGORITMO CORRETO FORNECIDO PELA CEF.

Exemplo (se fosse DV=2):
    def calcular_dv_modulo11(matricula_5dig):
        # ... implementação do algoritmo CEF ...
        return '2'  # ou o valor correto

═══════════════════════════════════════════════════════════════════════════

VALIDAÇÃO APÓS MUDANÇAS
═══════════════════════════════════════════════════════════════════════════

1. Executar servidor Django
2. Acessar http://127.0.0.1:8000/cef/download-lote/
3. Selecionar contratos e gerar lote
4. Verificar arquivo HEADER gerado:
   - Posição 1-2: Deve ter "35" (SP)
   - Posição 406-407: Deve ter "35" (SP)
   - Posição 408-413: Deve ter matrícula com DV correto
5. Fazer upload para CEF
6. Esperar validação sem erro 100820/100821

═══════════════════════════════════════════════════════════════════════════

TESTE RÁPIDO APÓS MUDANÇAS
═══════════════════════════════════════════════════════════════════════════

Você pode criar este teste rápido:

python manage.py shell
>>> from principal.ficha_generators import GeradoLoteFH1
>>> gerador = Gerador(tipo='FH1', matricula_agente='000049')  
>>> header = gerador.gerar_header_fh1(1)
>>> print(f"UFS no início: {header[0:2]}")  # Deve ser "35"
>>> print(f"UFS no LOTE: {header[405:407]}")  # Deve ser "35"
>>> print(f"Matrícula: {header[2:8]}")  # Deve ser "000049"

═══════════════════════════════════════════════════════════════════════════

ROLLBACK RÁPIDO
═══════════════════════════════════════════════════════════════════════════

Se algo der errado, as mudanças são triviais - basta reverter:
- '35' → '19' nas 3 linhas indicadas
- Ou usar git: git checkout principal/ficha_generators.py

═══════════════════════════════════════════════════════════════════════════

PRÓXIMAS AÇÕES ASSIM QUE CEF RESPONDER
═══════════════════════════════════════════════════════════════════════════

1. Copie este arquivo como referência
2. Execute as mudanças conforme indicado
3. Restart Django server
4. Teste no portal
5. Upload para CEF
6. Verifique se erros 100820/100821 sumiram
7. Continuar com testes de retorno e processamento

═══════════════════════════════════════════════════════════════════════════
""")

# Lista de mudanças em formato estruturado
mudancas = [
    {
        'arquivo': 'principal/ficha_generators.py',
        'funcao': 'gerar_header_fh1',
        'linha': 410,
        'antes': "header[0:2] = '19'",
        'depois': "header[0:2] = '35'",
        'motivo': 'UFS correto para São Paulo'
    },
    {
        'arquivo': 'principal/ficha_generators.py',
        'funcao': 'gerar_header_fh1',
        'linha': 432,
        'antes': "header[405:407] = '19'",
        'depois': "header[405:407] = '35'",
        'motivo': 'UFS na LOTE (repetição)'
    },
    {
        'arquivo': 'principal/ficha_generators.py',
        'funcao': 'gerar_lote_fh1_separado',
        'linha': 726,
        'antes': "linha += '19'  # UFS (RJ)",
        'depois': "linha += '35'  # UFS (SP)",
        'motivo': 'UFS nos dados da ficha'
    }
]

print("\n\nRESUMO EM FORMATO JSON:\n")
import json
print(json.dumps(mudancas, indent=2, ensure_ascii=False))

print("\n\nAGUARDANDO RESPOSTA DA CEF...")
print("Assim que souber o UFS e DV corretos, faça estas mudanças acima.")
