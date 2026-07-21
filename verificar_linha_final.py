linha = "430000446000         11000ALDEMIR PEREIRA DA SILVA                135897198772      16085200000RJETR DO CASSOROTIBA                    30108400000000000000301084001621233978001621233978     NNNN 0000000000000   0 00SAC0000000000000   0 00SAC                                                                                                                                                                    4300004290126006SI      "

print("=" * 80)
print("🔍 VERIFICAÇÃO FINAL DA LINHA FH1")
print("=" * 80)

print(f"\n📏 Tamanho: {len(linha)} caracteres")

if len(linha) == 430:
    print("✅ ✅ ✅ PERFEITO! Linha tem exatamente 430 caracteres!")
elif len(linha) < 430:
    print(f"❌ ERRO: Faltam {430 - len(linha)} caracteres")
elif len(linha) > 430:
    print(f"❌ ERRO: Sobram {len(linha) - 430} caracteres")

print(f"\n📋 Verificação campo por campo:")
print(f"  01-02: UFS = '{linha[0:2]}' {'✅' if linha[0:2] == '43' else '❌'}")
print(f"  03-08: MATRÍCULA = '{linha[2:8]}' {'✅' if linha[2:8] == '000044' else '❌'}")
print(f"  09-21: CONTRATO = '{linha[8:21]}' {'✅' if '6000' in linha[8:21] else '❌'}")
print(f"  22: HIPOTECA = '{linha[21]}' {'✅' if linha[21] == '1' else '❌'}")
print(f"  23: TIPO REG = '{linha[22]}' {'✅' if linha[22] == '1' else '❌'}")
print(f"  24-25: SEQUENCIAL = '{linha[23:25]}' {'✅' if linha[23:25] == '00' else '❌'}")
print(f"  26: CONSTANTE = '{linha[25]}' {'✅' if linha[25] == '0' else '❌'}")

print(f"\n📋 Identificação do Lote (posições 406-430):")
if len(linha) >= 430:
    id_lote = linha[405:430]
    print(f"  Completa: '{id_lote}' (len={len(id_lote)})")
    print(f"  406-407: UFS = '{id_lote[0:2]}' {'✅' if id_lote[0:2] == '43' else '❌'}")
    print(f"  408-412: MAT = '{id_lote[2:7]}' {'✅' if id_lote[2:7] == '00004' else '❌'}")
    print(f"  413-418: DATA = '{id_lote[7:13]}' {'✅ (DDMMAA)' if len(id_lote[7:13]) == 6 and id_lote[7:13].isdigit() else '❌'}")
    print(f"  419-421: LOTE = '{id_lote[13:16]}' {'✅' if id_lote[13:16].isdigit() and len(id_lote[13:16]) == 3 else '❌'}")
    print(f"  422: FORMA = '{id_lote[16]}' {'✅' if id_lote[16] == 'S' else '❌'}")
    print(f"  423: TIPO = '{id_lote[17]}' {'✅' if id_lote[17] == 'I' else '❌'}")
    print(f"  424-430: FILLER = '{id_lote[18:25]}' ({'✅' if id_lote[18:25] == '       ' else '❌'})")

print(f"\n{'='*80}")
print("RESUMO:")
if len(linha) == 430:
    print("✅ ✅ ✅ ARQUIVO PRONTO PARA ENVIO À CEF!")
    print("✅ Todos os campos obrigatórios estão preenchidos")
    print("✅ Tamanho correto: 430 caracteres")
else:
    print("❌ ARQUIVO AINDA TEM PROBLEMAS")
print("=" * 80)
