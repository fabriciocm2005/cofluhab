import json

with open('p3026_layouts_estruturado.json', encoding='utf-8') as f:
    data = json.load(f)

print("TR1 - Campos Completos (37 campos)")
print("=" * 80)

campos = [c for c in data['TR1']['campos'] if isinstance(c.get('seq'), str) and c['seq'].isdigit()]

for c in campos:
    pos_ini, pos_fim = c['colunas'].split('A')
    pos_ini = pos_ini.strip()
    pos_fim = pos_fim.strip()
    print(f"{c['seq']:>2}. [{pos_ini:>3}-{pos_fim:>3}] {c['tamanho']:>3} {c['tipo']:12} | {c['descricao']}")

print(f"\nTotal: {len(campos)} campos")
