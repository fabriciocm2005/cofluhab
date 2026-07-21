#!/usr/bin/env python3
# Debug script to check field positions

linha = (
    '1'                                          # [001-001] Tipo
    + '12345'                                    # [002-006] Matrícula (5)
    + '67890'                                    # [007-011] Cessionário (5)
    + '11111'                                    # [012-016] Cedente (5)
    + '0000012345678'                            # [017-029] Número contrato (13)
    + '1'                                        # [030-030] Grau hipoteca (1)
    + 'JOSE DA SILVA' + ' ' * 27                 # [031-070] Nome (40 chars)
    + '12345678901'                              # [071-081] CPF (11 chars)
    + '01012020'                                 # [082-089] Data assinatura (8)
    + 'RUA DAS FLORES, 123' + ' ' * 21           # [090-129] Endereço (40 chars)
    + '35550'                                    # [130-134] Código município (5)
    + 'SAO PAULO '                               # [135-144] Nome município (10 chars)
    + '01'                                       # [145-146] Origem recurso (2)
    + '01'                                       # [147-148] IM (2)
    + '008500'                                   # [149-154] Taxa contratual (6)
    + '009000'                                   # [155-160] Taxa evento (6)
    + '02'                                       # [161-162] Código situação (2)
    + 'HABILITADO PARA PAGAMENTO' + ' ' * 42    # [163-232] Descrição (70 chars: 28+42)
    + '001'                                      # [233-235] Tipo evento (3)
    + '15062020'                                 # [236-243] Data evento (8)
    + '00000012345678'                           # [244-257] VAF1 (14 chars)
    + '00000000500000'                           # [258-271] VAF2 (14 chars)
    + '00000000000000'                           # [272-285] VAF3 (14 chars)
    + '20062020'                                 # [286-293] Data habilitação (8)
    + '1'                                        # [294-294] Documentação (1)
    + '25062020'                                 # [295-302] Data processamento (8)
    + '30062020'                                 # [303-310] Data entrega (8)
    + '15072020'                                 # [311-318] Data prazo (8)
    + '2'                                        # [319-319] Situação análise (1)
    + '10072020'                                 # [320-327] Data negociação (8)
    + ' ' * 173                                  # [328-500] Vago
)

print(f"Tamanho total: {len(linha)}")
print()

# Check key field positions
campos_check = [
    ("Tipo [0:1]", 0, 1, '1'),
    ("Matrícula [1:6]", 1, 6, '12345'),
    ("Número contrato [16:29]", 16, 29, '0000012345678'),
    ("Nome [30:70]", 30, 70, 'JOSE DA SILVA' + ' ' * 27),
    ("CPF [70:81]", 70, 81, '12345678901'),
    ("Data evento [235:243]", 235, 243, '15062020'),
    ("VAF1 [243:257]", 243, 257, '00000012345678'),
    ("VAF2 [257:271]", 257, 271, '00000000500000'),
    ("Documentação [293:294]", 293, 294, '1'),
    ("Situação análise [318:319]", 318, 319, '2'),
]

for nome, ini, fim, esperado in campos_check:
    valor = linha[ini:fim]
    if valor == esperado:
        print(f"✅ {nome}: OK")
    else:
        print(f"❌ {nome}: GOT [{valor}] EXPECTED [{esperado}]")
        print(f"   Length: got {len(valor)}, expected {len(esperado)}")
