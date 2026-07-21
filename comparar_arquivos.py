"""
Compara arquivos ANTIGOS (aceitos) vs NOVOS (rejeitados)
"""

# ANTIGOS (aceitos)
with open(r'c:\Users\fabri\Downloads\HEADER_FH1_20260128_115401.txt', 'rb') as f:
    header_antigo = f.read()

with open(r'c:\Users\fabri\Downloads\DADOS_FH1_20260128_115401.txt', 'rb') as f:
    dados_antigo = f.read()

# NOVOS (rejeitados)
with open(r'c:\Users\fabri\Downloads\HEADER_FH1_20260128_122540.txt', 'rb') as f:
    header_novo = f.read()

with open(r'c:\Users\fabri\Downloads\DADOS_FH1_20260128_122540.txt', 'rb') as f:
    dados_novo = f.read()

print("=" * 80)
print("📋 COMPARAÇÃO DE HEADER")
print("=" * 80)
print(f"ANTIGO (aceito): {len(header_antigo)} bytes")
print(f"NOVO (rejeitado): {len(header_novo)} bytes")
print(f"\nDiferença de tamanho: {len(header_novo) - len(header_antigo)} bytes")

# Decodifica
h_ant = header_antigo.decode('latin-1')
h_nov = header_novo.decode('latin-1')

print(f"\nANTIGO (aceito): {len(h_ant)} caracteres")
print(f"NOVO (rejeitado): {len(h_nov)} caracteres")

# Identifica diferenças
print("\n🔍 DIFERENÇAS NO HEADER:")
for i in range(min(len(h_ant), len(h_nov))):
    if h_ant[i] != h_nov[i]:
        print(f"  Posição {i+1}: ANTIGO='{h_ant[i]}' (ord={ord(h_ant[i])}) | NOVO='{h_nov[i]}' (ord={ord(h_nov[i])})")

# Posição 406-430 (identificação do lote)
print(f"\n📍 IDENTIFICAÇÃO DO LOTE (posições 406-430):")
print(f"  ANTIGO: '{h_ant[405:430] if len(h_ant) >= 430 else 'ARQUIVO MENOR QUE 430'}'")
print(f"  NOVO:   '{h_nov[405:430]}'")

print("\n" + "=" * 80)
print("📄 COMPARAÇÃO DE DADOS")
print("=" * 80)
print(f"ANTIGO (aceito): {len(dados_antigo)} bytes")
print(f"NOVO (rejeitado): {len(dados_novo)} bytes")
print(f"\nDiferença de tamanho: {len(dados_novo) - len(dados_antigo)} bytes")

d_ant = dados_antigo.decode('latin-1')
d_nov = dados_novo.decode('latin-1')

print(f"\nANTIGO (aceito): {len(d_ant)} caracteres")
print(f"NOVO (rejeitado): {len(d_nov)} caracteres")

print("\n🔍 PRIMEIRAS DIFERENÇAS NO DADOS (primeiras 50):")
difs = 0
for i in range(min(len(d_ant), len(d_nov))):
    if d_ant[i] != d_nov[i]:
        print(f"  Posição {i+1}: ANTIGO='{d_ant[i]}' | NOVO='{d_nov[i]}'")
        difs += 1
        if difs >= 50:
            print("  ... (mais diferenças)")
            break

print(f"\n📍 Posições críticas:")
print(f"  Pos 1-2 (UFS):")
print(f"    ANTIGO: '{d_ant[0:2]}'")
print(f"    NOVO:   '{d_nov[0:2]}'")
print(f"  Pos 3-9 (MAT+DV):")
print(f"    ANTIGO: '{d_ant[2:9]}'")
print(f"    NOVO:   '{d_nov[2:9]}'")
print(f"  Pos 23 (TIPO REG):")
print(f"    ANTIGO: '{d_ant[22]}'")
print(f"    NOVO:   '{d_nov[22]}'")
print(f"  Pos 406-430 (ID LOTE):")
print(f"    ANTIGO: '{d_ant[405:430] if len(d_ant) >= 430 else 'ARQUIVO MENOR'}'")
print(f"    NOVO:   '{d_nov[405:430]}'")

print("\n" + "=" * 80)
print("💡 CONCLUSÃO:")
print("=" * 80)
print("O arquivo ANTIGO tem formato INCOMPLETO mas é aceito pela CEF (com críticas).")
print("O arquivo NOVO tem formato COMPLETO mas é REJEITADO imediatamente.")
print("\nA CEF pode estar esperando o formato ANTIGO (incompleto) no envio manual!")
