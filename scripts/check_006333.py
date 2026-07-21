import os, sys
sys.path.insert(0, '.')
os.environ['DJANGO_SETTINGS_MODULE'] = 'cofluhab.settings'
import django
django.setup()

from principal.models import Contrato, ParcelaContrato, Mutuario

# Buscar contrato 006333
c = Contrato.objects.filter(codigo='006333').first()
if c:
    print(f"✓ Contrato encontrado: ID={c.id}, Codigo={c.codigo}")
    print(f"  Conjunto: {c.conjunto}, Lote: {c.lote}, Sinal: {c.sinal}, Chave: {c.chave}")
    
    # Buscar mutuário vinculado
    import sqlite3
    conn = sqlite3.connect('db.sqlite3')
    cur = conn.cursor()
    cur.execute("SELECT mutuario_id FROM contrato_mutuario_map WHERE contrato_id=?", (c.id,))
    row = cur.fetchone()
    if row:
        mut = Mutuario.objects.get(id=row[0])
        print(f"  Mutuário: {mut.nome}")
        print(f"  Endereço: {mut.endereco}")
    conn.close()
    
    # Verificar parcelas
    parcelas = ParcelaContrato.objects.filter(contrato=c).order_by('nmens')
    print(f"\n✓ Total parcelas: {parcelas.count()}")
    
    if parcelas.exists():
        p1 = parcelas.first()
        print(f"\nPrimeira parcela (mens {p1.nmens}):")
        print(f"  Vencimento: {p1.dtvenc}")
        print(f"  Pagamento: {p1.dtpgto}")
        print(f"  Juros: {p1.juros}")
        print(f"  Amortização: {p1.amort}")
        print(f"  Seguro: {p1.seguro}")
        print(f"  TCA: {p1.tca}")
        print(f"  FCVS: {p1.fcvs}")
        print(f"  EM: {p1.em}")
        print(f"  RP: {p1.rp}")
        print(f"  CM: {p1.cm}")
        print(f"  Saldo Devedor: {p1.sddev}")
        print(f"  Valor Autenticado: {p1.vlautent}")
        
        print(f"\nÚltima parcela (mens {parcelas.last().nmens}):")
        pLast = parcelas.last()
        print(f"  Saldo Devedor: {pLast.sddev}")
else:
    print("✗ Contrato 006333 não encontrado")
