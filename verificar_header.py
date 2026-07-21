header = "4300004400000000000000000000000000001                                                                                                                                                                                                                                                                                                                                                                                43000044290126014SI      "

print("=" * 80)
print("🔍 VERIFICAÇÃO DO HEADER FH1")
print("=" * 80)

print(f"\n📏 Tamanho: {len(header)} caracteres")

if len(header) == 430:
    print("✅ CORRETO: Header tem exatamente 430 caracteres!")
elif len(header) < 430:
    print(f"❌ ERRO: Faltam {430 - len(header)} caracteres")
else:
    print(f"❌ ERRO: Sobram {len(header) - 430} caracteres")

print(f"\n📋 Análise dos campos do HEADER:")
print(f"\nCONTROLE (posições 1-23):")
print(f"  01-02: UFS = '{header[0:2]}' {'✅ (43=RS)' if header[0:2] == '43' else '❌'}")
print(f"  03-08: MATRÍCULA = '{header[2:8]}' {'✅' if header[2:8] == '000044' else '❌'}")
print(f"  09-22: ZEROS = '{header[8:22]}' {'✅' if header[8:22] == '00000000000000' else '❌ (deve ser 14 zeros)'}")
print(f"  23: TIPO REG = '{header[22]}' {'✅ (0=header)' if header[22] == '0' else '❌'}")

print(f"\nQUANTIDADE (posições 24-37):")
print(f"  24-32: ZEROS = '{header[23:32]}' {'✅' if header[23:32] == '000000000' else '❌ (deve ser 9 zeros)'}")
print(f"  33-37: QTD DOCS = '{header[32:37]}' {'✅' if header[32:37].isdigit() else '❌'}")

print(f"\nFILLER (posições 38-405):")
filler = header[37:405]
print(f"  Tamanho: {len(filler)} caracteres (esperado: 368)")
print(f"  Apenas espaços: {'✅' if filler.strip() == '' else '❌'}")

print(f"\nIDENTIFICAÇÃO DO LOTE (posições 406-430):")
if len(header) >= 430:
    id_lote = header[405:430]
    print(f"  Completa: '{id_lote}' (len={len(id_lote)})")
    print(f"  406-407: UFS = '{id_lote[0:2]}' {'✅' if id_lote[0:2] == '43' else '❌'}")
    print(f"  408-413: MAT = '{id_lote[2:8]}' {'✅ (6 dígitos)' if len(id_lote[2:8]) == 6 and id_lote[2:8].isdigit() else '❌'}")
    print(f"  414-419: DATA = '{id_lote[8:14]}' {'✅ (DDMMAA)' if len(id_lote[8:14]) == 6 and id_lote[8:14].isdigit() else '❌'}")
    print(f"  420-422: LOTE = '{id_lote[14:17]}' {'✅' if id_lote[14:17].isdigit() and len(id_lote[14:17]) == 3 else '❌'}")
    print(f"  423: FORMA = '{id_lote[17]}' {'✅' if id_lote[17] == 'S' else '❌'}")
    print(f"  424: TIPO = '{id_lote[18]}' {'✅' if id_lote[18] == 'I' else '❌'}")
    print(f"  425-430: FILLER = '{id_lote[19:25]}' ({'✅' if len(id_lote[19:25]) == 6 else '❌'})")
else:
    print("  ❌ Header muito curto para ter identificação do lote")

print(f"\n{'='*80}")
print("RESUMO DO HEADER:")
if len(header) == 430:
    print("✅ Tamanho correto: 430 caracteres")
    print("✅ Estrutura básica OK")
    print("⚠️  ATENÇÃO: Verificar se matrícula na ID do Lote tem 6 dígitos (HEADER) ou 5 (DADOS)")
else:
    print("❌ Header com problemas de tamanho")
print("=" * 80)
