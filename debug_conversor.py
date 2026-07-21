import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

cursor.execute("""
    SELECT 
        pc.nmens,
        pc.conversor,
        pc.vlautent,
        pc.juros,
        pc.amort,
        pc.seguro,
        pc.tca,
        pc.fcvs,
        pc.em,
        pc.rp,
        (COALESCE(pc.juros,0) + COALESCE(pc.amort,0) + COALESCE(pc.seguro,0) + 
         COALESCE(pc.tca,0) + COALESCE(pc.fcvs,0) + COALESCE(pc.em,0) + COALESCE(pc.rp,0)) as soma
    FROM principal_parcelacontrato pc
    JOIN principal_contrato c ON pc.contrato_id = c.id
    WHERE c.codigo = '004062' AND pc.nmens = 84
""")

row = cursor.fetchone()
if row:
    print(f"Parcela: {row[0]}")
    print(f"Conversor: {row[1]}")
    print(f"vlautent: {row[2]}")
    print(f"juros: {row[3]}")
    print(f"amort: {row[4]}")
    print(f"seguro: {row[5]}")
    print(f"tca: {row[6]}")
    print(f"fcvs: {row[7]}")
    print(f"em: {row[8]}")
    print(f"rp: {row[9]}")
    print(f"SOMA: {row[10]}")
    if row[1]:
        print(f"SOMA / CONVERSOR: {row[10] / row[1]}")

conn.close()
