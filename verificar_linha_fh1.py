linha = "430000446000         11000ALDEMIR PEREIRA DA SILVA                135897198772      16085200000RJETR DO CASSOROTIBA                    30108400000000000000301084001621233978001621233978     NNNN 0000000000000   0 00SAC0000000000000   0 00SAC                                                                                                                                                                    4300004290126002SI   "

print("=" * 80)
print("🔍 VERIFICAÇÃO DA LINHA FH1")
print("=" * 80)

print(f"\n📏 Tamanho: {len(linha)} caracteres")

if len(linha) == 430:
    print("✅ CORRETO: Linha tem exatamente 430 caracteres!")
elif len(linha) < 430:
    print(f"❌ ERRO: Faltam {430 - len(linha)} caracteres")
elif len(linha) > 430:
    print(f"❌ ERRO: Sobram {len(linha) - 430} caracteres")

print(f"\n📋 Análise de campos principais:")
print(f"  01-02: UFS = '{linha[0:2]}'")
print(f"  03-08: MATRÍCULA = '{linha[2:8]}'")
print(f"  09-21: CONTRATO = '{linha[8:21]}'")
print(f"  22: HIPOTECA = '{linha[21]}'")
print(f"  23: TIPO REG = '{linha[22]}'")
print(f"  24-25: SEQUENCIAL = '{linha[23:25]}'")
print(f"  26: CONSTANTE = '{linha[25]}'")
print(f"  27-66: NOME = '{linha[26:66]}'")
print(f"  67: TIPO CPF = '{linha[66]}'")
print(f"  68-84: CPF = '{linha[67:84]}'")
print(f"  85-90: DATA NASC = '{linha[84:90]}'")
print(f"  91-95: COD MUN = '{linha[90:95]}'")
print(f"  96-97: UF = '{linha[95:97]}'")
print(f"  98-135: ENDEREÇO = '{linha[97:135]}'")
print(f"  136-141: DATA CONTRATO = '{linha[135:141]}'")
print(f"  142-153: VALOR GARANTIA = '{linha[141:153]}'")
print(f"  154-155: IM = '{linha[153:155]}'")
print(f"  156-161: DATA LEGISLAÇÃO = '{linha[155:161]}'")
print(f"  162-173: VALOR FINANC = '{linha[161:173]}'")
print(f"  174-185: VALOR FCVS = '{linha[173:185]}'")
print(f"  186-190: CAT PROF = '{linha[185:190]}'")
print(f"  191-195: FLAGS = '{linha[190:195]}'")
print(f"  196-198: PRAZO = '{linha[195:198]}'")
print(f"  199-204: TAXA JUROS = '{linha[198:204]}'")

print(f"\n📋 Identificação do Lote (posições 406-430):")
id_lote = linha[405:430] if len(linha) >= 430 else linha[405:]
print(f"  Completa: '{id_lote}' (len={len(id_lote)})")
if len(id_lote) >= 25:
    print(f"  406-407: UFS = '{id_lote[0:2]}'")
    print(f"  408-412: MAT = '{id_lote[2:7]}'")
    print(f"  413-418: DATA = '{id_lote[7:13]}'")
    print(f"  419-421: LOTE = '{id_lote[13:16]}'")
    print(f"  422: FORMA = '{id_lote[16]}'")
    print(f"  423: TIPO = '{id_lote[17]}'")
    print(f"  424-430: FILLER = '{id_lote[18:25]}'")

print(f"\n📋 Últimos 30 caracteres:")
print(f"  [{linha[-30:]}]")

print("\n" + "=" * 80)
