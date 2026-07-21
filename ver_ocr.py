"""
Uso: python ver_ocr.py <caminho_do_pdf>
Exemplo: python ver_ocr.py manual/1234.pdf
"""
import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
import django
django.setup()

from ocr_contrato_processor import ContratoOCRExtractor

pdf = sys.argv[1] if len(sys.argv) > 1 else 'contrato_teste.pdf'

print(f"\n{'='*55}")
print(f"PDF: {pdf}")
print('='*55)

ex = ContratoOCRExtractor(pdf)
d = ex.extract_all()

skip = {'parcelas', 'ocr_quality', 'document_type'}
# Ordem lógica de exibição
ORDEM = [
    'codigo','nome','cpf','data_contrato','conjunto','sa','prazo','tx_juros',
    'vlprop','vlfinanc','prestacao_inicial','encargo_mensal','prestacao_reajustada',
    'renda','crenda','dtnasc',
    'endereco','numero','compl','bairro','cidade','uf','cep',
    'tipoimovel','ocorrencia','cat_prof','pr',
    'ident','orgao','telefone','email',
]

print("\n--- CAMPOS EXTRAÍDOS ---")
mostrados = set()
for f in ORDEM:
    v = d.get(f)
    if v is not None:
        print(f"  {f:<30}: {v}")
        mostrados.add(f)

# Campos extras não previstos na ordem
print("\n--- OUTROS CAMPOS ---")
for k, v in d.items():
    if k not in skip and k not in mostrados and v is not None:
        print(f"  {k:<30}: {v}")

q = d.get('ocr_quality', {})
parcelas = d.get('parcelas') or []

print()
print(f"SCORE           : {q.get('score')}  [{q.get('status', '').upper()}]")
print(f"Críticos faltando   : {q.get('faltando_criticos', [])}")
print(f"Importantes faltando: {q.get('faltando_importantes', [])}")
print(f"Parcelas encontradas: {len(parcelas)}")

if parcelas:
    print("\n--- PRIMEIRAS 3 PARCELAS ---")
    for p in parcelas[:3]:
        print(f"  {p}")
