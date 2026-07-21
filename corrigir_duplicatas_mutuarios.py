import os
import django
import sqlite3

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Mutuario

conn = sqlite3.connect(r'C:\Users\fabri\cofluhab\cofluhab\db.sqlite3')
cur = conn.cursor()

print("Verificando duplicidades de mutuários...\n")

# Encontrar mutuários duplicados (mesmo código e conjunto)
cur.execute("""
    SELECT codigo, conjunto, COUNT(*) as qtd
    FROM principal_mutuario
    GROUP BY codigo, conjunto
    HAVING COUNT(*) > 1
    ORDER BY qtd DESC
    LIMIT 20
""")

duplicatas = cur.fetchall()

if duplicatas:
    print(f"Encontradas {len(duplicatas)} combinações de código+conjunto duplicadas:\n")
    for codigo, conjunto, qtd in duplicatas[:10]:
        print(f"  Código {codigo}, Conjunto {conjunto}: {qtd} registros")
    
    print("\n" + "="*70)
    print("REMOVENDO DUPLICATAS...")
    print("="*70 + "\n")
    
    # Para cada duplicata, manter apenas o primeiro registro (id menor)
    cur.execute("""
        DELETE FROM principal_mutuario
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM principal_mutuario
            GROUP BY codigo, conjunto
        )
    """)
    
    removidos = cur.rowcount
    conn.commit()
    
    print(f"✓ Removidos {removidos} registros duplicados!")
    
    # Verificar novamente
    cur.execute("""
        SELECT COUNT(*)
        FROM principal_mutuario
    """)
    total = cur.fetchone()[0]
    print(f"✓ Total de mutuários restantes: {total}")
else:
    print("✓ Nenhuma duplicidade encontrada!")

conn.close()
