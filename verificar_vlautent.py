import sqlite3

# Conectar ao banco de dados
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

print("="*80)
print("INVESTIGANDO CONTRATO 004062 - PARCELA 84")
print("="*80)

# Buscar a parcela específica
query = """
SELECT 
    c.codigo as contrato,
    pc.nmens,
    pc.dtvenc,
    pc.dtpgto,
    pc.vlautent,
    pc.sddev,
    pc.sddev_original,
    pc.juros,
    pc.amort,
    pc.seguro,
    pc.tca,
    pc.fcvs,
    pc.em,
    pc.rp,
    pc.cm
FROM principal_parcelacontrato pc
JOIN principal_contrato c ON pc.contrato_id = c.id
WHERE c.codigo = '004062' AND pc.nmens = 84
"""

cursor.execute(query)
row = cursor.fetchone()

if row:
    print("\nDados da Parcela 84:")
    print(f"  Contrato: {row[0]}")
    print(f"  Número: {row[1]}")
    print(f"  Vencimento: {row[2]}")
    print(f"  Pagamento: {row[3]}")
    print(f"\nVALORES PRINCIPAIS:")
    print(f"  vlautent: {row[4]}")
    print(f"  sddev: {row[5]}")
    print(f"  sddev_original: {row[6]}")
    print(f"\nCOMPONENTES:")
    print(f"  juros: {row[7]}")
    print(f"  amort: {row[8]}")
    print(f"  seguro: {row[9]}")
    print(f"  tca: {row[10]}")
    print(f"  fcvs: {row[11]}")
    print(f"  em: {row[12]}")
    print(f"  rp: {row[13]}")
    print(f"  cm: {row[14]}")
    
    # Calcular soma dos componentes
    soma = 0
    for val in row[7:14]:  # juros até rp
        if val:
            soma += val
    print(f"\nSOMA DOS COMPONENTES: {soma}")
    print(f"VALOR ESPERADO: R$ 85,71")
else:
    print("Parcela não encontrada!")

print("\n" + "="*80)
print("PRIMEIRAS 5 PARCELAS EM ABERTO DO CONTRATO 004062:")
print("="*80)

query2 = """
SELECT 
    pc.nmens,
    pc.dtvenc,
    pc.dtpgto,
    pc.vlautent,
    pc.sddev,
    pc.juros,
    pc.amort,
    pc.seguro
FROM principal_parcelacontrato pc
JOIN principal_contrato c ON pc.contrato_id = c.id
WHERE c.codigo = '004062' AND pc.dtpgto IS NULL
ORDER BY pc.nmens
LIMIT 5
"""

cursor.execute(query2)
rows = cursor.fetchall()

for row in rows:
    soma_comp = (row[5] or 0) + (row[6] or 0) + (row[7] or 0)
    print(f"\nParcela {row[0]} - Venc: {row[1]}")
    print(f"  vlautent: {row[3]}")
    print(f"  sddev: {row[4]}")
    print(f"  Soma (j+a+s): {soma_comp}")

conn.close()
