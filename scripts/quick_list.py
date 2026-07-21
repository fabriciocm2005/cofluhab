import os, glob
print('cwd:', os.getcwd())
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
print('ROOT:', ROOT)
d = os.path.join(ROOT, 'dados_antigos')
print('dados_antigos exists:', os.path.exists(d))
if os.path.exists(d):
    files = sorted(glob.glob(os.path.join(d, '*')))
    print('first 30 entries:')
    for f in files[:30]:
        print('-', os.path.basename(f))
else:
    print('no dados_antigos')
print('exports exists:', os.path.exists(os.path.join(ROOT, 'exports')))
