import os, csv, sys, re, difflib
# ensure project root is on sys.path so `import cofluhab` works when run from anywhere
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE','cofluhab.settings')
import django
django.setup()
from principal.models import Mutuario, ConjuntoHabitacional, Endereco, Movimentacao

EXPORT_DIR = os.path.join(os.path.dirname(__file__), '..', 'exports')
os.makedirs(EXPORT_DIR, exist_ok=True)

mut_total = Mutuario.objects.count()
mut_linked = 0
mut_unmatched = []

for m in Mutuario.objects.all():
    linked_conj = None
    # try exact match on conjunto field
    if m.conjunto:
        linked_conj = ConjuntoHabitacional.objects.filter(conjunto__iexact=m.conjunto).first()
    if not linked_conj and hasattr(m, 'conjseg') and m.conjseg:
        linked_conj = ConjuntoHabitacional.objects.filter(conj__iexact=m.conjseg).first()
    if linked_conj:
        m.conjunto_fk = linked_conj

    # endereco matching: by cep then by endereco substring
    linked_end = None
    if m.cep:
        linked_end = Endereco.objects.filter(cep__icontains=m.cep.strip()).first()
    if not linked_end and m.endereco:
        snippet = (m.endereco or '')[:40]
        linked_end = Endereco.objects.filter(endereco__icontains=snippet).first()
    if linked_end:
        m.endereco_fk = linked_end

    # if either fk set, save
    if m.conjunto_fk or m.endereco_fk:
        m.save()
        mut_linked += 1
    else:
        mut_unmatched.append({'codigo': m.codigo, 'nome': m.nome, 'codimovel': m.codimovel, 'conjunto': m.conjunto, 'cep': m.cep, 'endereco': m.endereco})

# Movimentacoes linking (improved heuristics)
mov_total = Movimentacao.objects.count()
mov_linked = 0
mov_unmatched = []
mov_ambiguous = []

def normalize_code(s):
    if not s:
        return ''
    return re.sub(r"[^A-Za-z0-9]", "", s).lower()

# Build indices
cod_map = {}
cod_conj_map = {}
name_list = []
for m in Mutuario.objects.all():
    nc = normalize_code(m.codimovel)
    cod_map.setdefault(nc, []).append(m)
    conj_key = (nc, (m.conjunto or '').strip().lower())
    cod_conj_map.setdefault(conj_key, []).append(m)
    name_list.append((m.nome or '', m))

def best_name_match(text, cutoff=0.7):
    if not text:
        return None
    names = [n for n, _ in name_list]
    matches = difflib.get_close_matches(text, names, n=3, cutoff=cutoff)
    if not matches:
        return None
    best = matches[0]
    for n, m in name_list:
        if n == best:
            return m
    return None

for mv in Movimentacao.objects.all():
    matched = None
    mv_code = normalize_code(mv.codimovel)
    mv_conj = (mv.conjunto or '').strip().lower()

    # 1) codimovel + conjunto exact unique
    if mv_code:
        key = (mv_code, mv_conj)
        candidates = cod_conj_map.get(key, [])
        if len(candidates) == 1:
            matched = candidates[0]
        elif len(candidates) > 1:
            mov_ambiguous.append({'id': mv.id, 'codimovel': mv.codimovel, 'conjunto': mv.conjunto, 'count': len(candidates)})

    # 2) codimovel exact unique
    if not matched and mv_code:
        candidates = cod_map.get(mv_code, [])
        if len(candidates) == 1:
            matched = candidates[0]
        elif len(candidates) > 1:
            mov_ambiguous.append({'id': mv.id, 'codimovel': mv.codimovel, 'conjunto': mv.conjunto, 'count': len(candidates)})

    # 3) try fuzzy match on descricao and tipo
    if not matched:
        probe = ' '.join(filter(None, [mv.descricao or '', mv.tipo or '']))
        if probe:
            toks = re.split(r'\W+', probe)
            toks = [t for t in toks if len(t) > 2]
            toks = sorted(toks, key=lambda s: -len(s))
            for t in toks[:6]:
                candidate = best_name_match(t, cutoff=0.7)
                if candidate:
                    matched = candidate
                    break

    # 4) conjunto-only unique fallback
    if not matched and mv_conj:
        possible = Mutuario.objects.filter(conjunto__iexact=mv_conj)
        if possible.count() == 1:
            matched = possible.first()
        elif possible.count() > 1:
            mov_ambiguous.append({'id': mv.id, 'codimovel': mv.codimovel, 'conjunto': mv.conjunto, 'count': possible.count()})

    if matched:
        mv.mutuario_fk = matched
        mv.save()
        mov_linked += 1
    else:
        mov_unmatched.append({'id': mv.id, 'codigo': mv.codigo, 'codimovel': mv.codimovel, 'conjunto': mv.conjunto, 'descricao': mv.descricao})

# write CSVs
mut_unmatched_path = os.path.join(EXPORT_DIR, 'mutuarios_unmatched.csv')
with open(mut_unmatched_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['codigo','nome','codimovel','conjunto','cep','endereco'])
    writer.writeheader()
    writer.writerows(mut_unmatched)

mov_unmatched_path = os.path.join(EXPORT_DIR, 'movimentacoes_unmatched.csv')
with open(mov_unmatched_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['id','codigo','codimovel','conjunto','descricao'], extrasaction='ignore')
    writer.writeheader()
    writer.writerows(mov_unmatched)

mov_ambiguous_path = os.path.join(EXPORT_DIR, 'movimentacoes_ambiguous.csv')
with open(mov_ambiguous_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['id','codimovel','conjunto','count'])
    writer.writeheader()
    writer.writerows(mov_ambiguous)

# summary
print('Mutuarios total:', mut_total)
print('Mutuarios linked:', mut_linked)
print('Mutuarios unmatched saved to', mut_unmatched_path)
print('Movimentacoes total:', mov_total)
print('Movimentacoes linked:', mov_linked)
print('Movimentacoes unmatched saved to', mov_unmatched_path)
print('Movimentacoes ambiguous saved to', mov_ambiguous_path)
