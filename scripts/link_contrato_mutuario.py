"""
Heuristic mapper: link Contrato -> Mutuario using `chave`/`codigo`/conjunto and fuzzy match on name
Produces CSV: exports/contrato_mutuario_map.csv with columns: contrato_id,codigo,chave,conjunto,mutuario_id,mutuario_nome,score,method
"""
import os, csv, sys
from difflib import SequenceMatcher

os.environ = os.environ if 'os' in globals() else os.environ
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
EXPORT_DIR = os.path.join(ROOT, 'exports')
if not os.path.isdir(EXPORT_DIR):
    os.makedirs(EXPORT_DIR, exist_ok=True)

# Django setup
sys.path.insert(0, ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
import django
django.setup()
from principal.models import Contrato, Mutuario


def norm(s):
    if s is None:
        return ''
    return ''.join(ch for ch in str(s).lower() if ch.isalnum())


def ratio(a,b):
    return SequenceMatcher(None, a, b).ratio()


def main():
    contratos = list(Contrato.objects.all())
    mutuarios = list(Mutuario.objects.all())
    # build indices
    by_codigo = {}
    by_chave = {}
    for m in mutuarios:
        keyc = norm(getattr(m, 'codimovel', '') or getattr(m, 'codigo', ''))
        keych = norm(getattr(m, 'chave', '') or '')
        if keyc:
            by_codigo.setdefault(keyc, []).append(m)
        if keych:
            by_chave.setdefault(keych, []).append(m)

    outp = os.path.join(EXPORT_DIR, 'contrato_mutuario_map.csv')
    written = 0
    print('contratos_count=', len(contratos), 'mutuarios_count=', len(mutuarios))
    try:
        with open(outp, 'w', newline='', encoding='utf-8') as fh:
            w = csv.writer(fh)
            w.writerow(['contrato_id','codigo','chave','conjunto','mutuario_id','mutuario_nome','score','method'])

            print('starting to iterate contratos')
            sys.stdout.flush()

            for idx, c in enumerate(contratos, start=1):
                try:
                    codigo = (c.codigo or '').strip()
                    chave = (c.chave or '').strip()
                    conj = (c.conjunto or '').strip()
                    best = (None, 0.0, 'none')
                    # try exact codigo
                    k = norm(codigo)
                    if k and k in by_codigo:
                        mlist = by_codigo[k]
                        if len(mlist) == 1:
                            best = (mlist[0], 1.0, 'codigo-exact')
                        else:
                            # choose by best name ratio if available
                            for m in mlist:
                                score = ratio(norm(m.nome or ''), norm(chave or codigo or ''))
                                if score > best[1]:
                                    best = (m, score, 'codigo-multi')
                    # try chave exact
                    if best[0] is None and chave:
                        kch = norm(chave)
                        if kch in by_chave:
                            mlist = by_chave[kch]
                            if len(mlist) == 1:
                                best = (mlist[0], 0.95, 'chave-exact')
                            else:
                                for m in mlist:
                                    score = ratio(norm(m.nome or ''), norm(chave or ''))
                                    if score > best[1]:
                                        best = (m, score, 'chave-multi')
                    # fuzzy name match fallback across all mutuarios (expensive but last resort)
                    if best[0] is None:
                        target = norm(chave or codigo or '')
                        if not target:
                            # try contraparte: use contrato.conjunto + codigo
                            target = norm((conj or '') + (codigo or ''))
                        if target:
                            for m in mutuarios:
                                s = norm(m.nome or '')
                                sc = ratio(s, target)
                                if sc > best[1]:
                                    best = (m, sc, 'fuzzy-name')
                    m = best[0]
                    if m:
                        w.writerow([c.id, codigo, chave, conj, m.id, (m.nome or '').strip(), round(best[1], 4), best[2]])
                    else:
                        w.writerow([c.id, codigo, chave, conj, '', '', 0.0, 'unmatched'])
                    written += 1
                    if idx % 100 == 0:
                        print('processed', idx)
                        sys.stdout.flush()
                except Exception as row_e:
                    # ensure a row is written even if one contrato fails
                    try:
                        w.writerow([getattr(c, 'id', None), getattr(c, 'codigo', ''), getattr(c, 'chave', ''), getattr(c, 'conjunto', ''), '', '', 0.0, 'error'])
                    except Exception:
                        pass
                    print('row-exception for contrato', getattr(c, 'id', None), str(row_e))
                    sys.stdout.flush()
    except Exception as e:
        print('FATAL error while writing csv', str(e))
        import traceback
        traceback.print_exc()

    print('WROTE', outp, 'rows_written=', written)


if __name__ == '__main__':
    main()
