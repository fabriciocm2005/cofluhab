import csv, collections, statistics, os
p = os.path.join(os.path.dirname(__file__), '..', 'exports', 'contrato_mutuario_map.csv')
if not os.path.exists(p):
    print('MISSING', p)
    raise SystemExit(1)
with open(p, encoding='utf-8') as f:
    r = csv.DictReader(f)
    total = 0
    matched = 0
    unmatched = 0
    errors = 0
    methods = collections.Counter()
    scores = []
    for row in r:
        total += 1
        mut_id = (row.get('mutuario_id') or '').strip()
        method = (row.get('method') or '').strip()
        methods[method] += 1
        try:
            s = float(row.get('score') or 0.0)
        except Exception:
            s = 0.0
        scores.append(s)
        if mut_id:
            matched += 1
        elif method == 'error':
            errors += 1
        else:
            unmatched += 1

print('total_rows', total)
print('matched_rows', matched)
print('unmatched_rows', unmatched)
print('error_rows', errors)
print('\nmethod_breakdown:')
for k, v in methods.most_common():
    print(f"  {k}: {v}")

if scores:
    print('\nscore_stats:')
    print('  mean', round(statistics.mean(scores), 4))
    print('  median', round(statistics.median(scores), 4))
    for thr in (0.9, 0.8, 0.5, 0.3, 0.0):
        cnt = sum(1 for s in scores if s >= thr)
        print(f'  >={thr}: {cnt}')
else:
    print('no scores')
