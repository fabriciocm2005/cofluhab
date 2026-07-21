import django, os, sys
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from django.db import connection

c = connection.cursor()
c.execute('''
    SELECT p.id, p.nmens, p.dtvenc, p.sddev_original, p.sddev 
    FROM principal_parcelacontrato p 
    INNER JOIN principal_contrato ct ON ct.id = p.contrato_id 
    WHERE ct.codigo = '000102' 
    ORDER BY p.nmens DESC 
    LIMIT 1
''')

r = c.fetchone()
if r:
    print(f"Contrato: 000102")
    print(f"Parcela ID: {r[0]}")
    print(f"Numero: {r[1]}")
    print(f"Vencimento: {r[2]}")
    if r[3]:
        print(f"Saldo Original (moeda antiga): R$ {float(r[3]):,.2f}")
        print(f"Saldo Atualizado (nov/2025): R$ {float(r[4]):,.2f}")
    else:
        print(f"Saldo Atual: R$ {float(r[4]):,.2f}")
        print("(Este contrato nao foi convertido - ja estava em Real)")
else:
    print("Contrato 000102 nao encontrado")
