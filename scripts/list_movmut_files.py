import os, glob
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
pattern = os.path.join(ROOT, 'dados_antigos', 'MOVMUT*.DBF')
print('pattern:', pattern)
files = sorted(glob.glob(pattern))
print('found', len(files), 'files')
for f in files:
    print('-', f)
# print directory listing for dados_antigos
print('\nfirst 50 files in dados_antigos:')
allfiles = sorted(glob.glob(os.path.join(ROOT,'dados_antigos','*')))
for f in allfiles[:50]:
    print('-', os.path.basename(f))
