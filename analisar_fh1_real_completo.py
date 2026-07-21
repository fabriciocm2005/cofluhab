#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Análise Reversa Completa do FH1 Real da CEF
Extrai layout completo dos 424 caracteres
"""
import json

# Lê o arquivo FH1 real
with open(r'principal\templates\DADOS_FH1_20260212_122417.txt', 'r', encoding='latin-1') as f:
    linha_real = f.read().strip()

print("=" * 80)
print("ENGENHARIA REVERSA - FH1 REAL DA CEF")
print("=" * 80)

print(f"\nTamanho: {len(linha_real)} caracteres")

# Layout dos primeiros 192 caracteres (documentado)
layout_documentado = [
    {"inicio": 1, "fim": 2, "nome": "UFS", "tam": 2, "valor_real": linha_real[0:2]},
    {"inicio": 3, "fim": 8, "nome": "MAT_AG_FINANC_DV", "tam": 6, "valor_real": linha_real[2:8]},
    {"inicio": 9, "fim": 21, "nome": "NUMERO_CONTRATO", "tam": 13, "valor_real": linha_real[8:21]},
    {"inicio": 22, "fim": 22, "nome": "HIPOTECA", "tam": 1, "valor_real": linha_real[21:22]},
    {"inicio": 23, "fim": 24, "nome": "SEQUENCIAL", "tam": 2, "valor_real": linha_real[22:24]},
    {"inicio": 25, "fim": 25, "nome": "CONSTANTE", "tam": 1, "valor_real": linha_real[24:25]},
    {"inicio": 26, "fim": 65, "nome": "NOME_MUTUARIO", "tam": 40, "valor_real": linha_real[25:65]},
    {"inicio": 66, "fim": 76, "nome": "CPF_CI", "tam": 11, "valor_real": linha_real[65:76]},
    {"inicio": 77, "fim": 82, "nome": "DATA_NASCIMENTO", "tam": 6, "valor_real": linha_real[76:82]},
    {"inicio": 83, "fim": 87, "nome": "CODIGO_MUNICIPIO", "tam": 5, "valor_real": linha_real[82:87]},
    {"inicio": 88, "fim": 89, "nome": "UF", "tam": 2, "valor_real": linha_real[87:89]},
    {"inicio": 90, "fim": 127, "nome": "ENDERECO_IMOVEL", "tam": 38, "valor_real": linha_real[89:127]},
    {"inicio": 128, "fim": 133, "nome": "DATA_CONTRATO", "tam": 6, "valor_real": linha_real[127:133]},
    {"inicio": 134, "fim": 145, "nome": "VALOR_FINANC_CONTRATADO", "tam": 12, "valor_real": linha_real[133:145]},
    {"inicio": 146, "fim": 148, "nome": "PRAZO_CONTRATADO", "tam": 3, "valor_real": linha_real[145:148]},
    {"inicio": 149, "fim": 152, "nome": "TAXA_JUROS_CONTRATADO", "tam": 4, "valor_real": linha_real[148:152]},
    {"inicio": 153, "fim": 158, "nome": "PRIMEIRO_VENCIMENTO", "tam": 6, "valor_real": linha_real[152:158]},
    {"inicio": 159, "fim": 170, "nome": "VALOR_FINANC_FCVS", "tam": 12, "valor_real": linha_real[158:170]},
    {"inicio": 171, "fim": 173, "nome": "PRAZO_FCVS", "tam": 3, "valor_real": linha_real[170:173]},
    {"inicio": 174, "fim": 177, "nome": "TAXA_JUROS_FCVS", "tam": 4, "valor_real": linha_real[173:177]},
    {"inicio": 178, "fim": 180, "nome": "PLANO", "tam": 3, "valor_real": linha_real[177:180]},
    {"inicio": 181, "fim": 182, "nome": "RR", "tam": 2, "valor_real": linha_real[180:182]},
    {"inicio": 183, "fim": 185, "nome": "INDEX", "tam": 3, "valor_real": linha_real[182:185]},
    {"inicio": 186, "fim": 190, "nome": "COD_CATEG_PROFISSIONAL", "tam": 5, "valor_real": linha_real[185:190]},
    {"inicio": 191, "fim": 192, "nome": "PR", "tam": 2, "valor_real": linha_real[190:192]},
]

# Analisa campos extras (193-424)
print("\n" + "=" * 80)
print("CAMPOS DOCUMENTADOS (1-192):")
print("=" * 80)

for campo in layout_documentado:
    print(f"[{campo['inicio']:3d}-{campo['fim']:3d}] {campo['nome']:25s} = '{campo['valor_real']}'")

# Campos extras - engenharia reversa
print("\n" + "=" * 80)
print("CAMPOS EXTRAS (193-424) - ENGENHARIA REVERSA:")
print("=" * 80)

resto = linha_real[192:]
print(f"\nTotal de {len(resto)} caracteres extras")
print(f"Conteúdo: '{resto}'")

# Identifica padrões
campos_extras = []

# Analisando por padrões identificados
pos = 192

# Campo 26: Parece repetir NN (2 chars)
campos_extras.append({"inicio": 193, "fim": 194, "nome": "CAMPO_EXTRA_01", "tam": 2, "valor_real": linha_real[192:194], "obs": "Repete final PR"})
pos = 194

# Campo 27: Espaço + zeros (parece valor numérico)
campos_extras.append({"inicio": 195, "fim": 206, "nome": "CAMPO_EXTRA_02", "tam": 12, "valor_real": linha_real[194:206], "obs": "Valor numérico com espaços"})
pos = 206

# Campo 28: Espaços + número
campos_extras.append({"inicio": 207, "fim": 209, "nome": "CAMPO_EXTRA_03", "tam": 3, "valor_real": linha_real[206:209], "obs": "Espaços + 0"})
pos = 209

# Campo 29: Número
campos_extras.append({"inicio": 210, "fim": 211, "nome": "CAMPO_EXTRA_04", "tam": 2, "valor_real": linha_real[209:211], "obs": "00"})
pos = 211

# Campo 30: SAC (Sistema amortização?)
campos_extras.append({"inicio": 212, "fim": 214, "nome": "CAMPO_EXTRA_05_SAC", "tam": 3, "valor_real": linha_real[211:214], "obs": "Sistema amortização"})
pos = 214

# Continua análise...
campos_extras.append({"inicio": 215, "fim": 226, "nome": "CAMPO_EXTRA_06", "tam": 12, "valor_real": linha_real[214:226], "obs": "Valor numérico"})
campos_extras.append({"inicio": 227, "fim": 229, "nome": "CAMPO_EXTRA_07", "tam": 3, "valor_real": linha_real[226:229], "obs": "Espaços + número"})
campos_extras.append({"inicio": 230, "fim": 231, "nome": "CAMPO_EXTRA_08", "tam": 2, "valor_real": linha_real[229:231], "obs": "00"})
campos_extras.append({"inicio": 232, "fim": 234, "nome": "CAMPO_EXTRA_09_SAC", "tam": 3, "valor_real": linha_real[231:234], "obs": "Sistema amortização repetido"})

# Data e valores (padrão comum nos arquivos CEF)
campos_extras.append({"inicio": 235, "fim": 240, "nome": "DATA_EXTRA_01", "tam": 6, "valor_real": linha_real[234:240], "obs": "Data formato MMAAAA"})
campos_extras.append({"inicio": 241, "fim": 252, "nome": "VALOR_EXTRA_01", "tam": 12, "valor_real": linha_real[240:252], "obs": "Valor numérico"})
campos_extras.append({"inicio": 253, "fim": 258, "nome": "DATA_EXTRA_02", "tam": 6, "valor_real": linha_real[252:258], "obs": "Data formato MMAAAA"})
campos_extras.append({"inicio": 259, "fim": 270, "nome": "VALOR_EXTRA_02", "tam": 12, "valor_real": linha_real[258:270], "obs": "Valor numérico"})
campos_extras.append({"inicio": 271, "fim": 282, "nome": "VALOR_EXTRA_03", "tam": 12, "valor_real": linha_real[270:282], "obs": "Valor numérico"})

# Sequência de zeros (campos reservados/não usados)
campos_extras.append({"inicio": 283, "fim": 312, "nome": "RESERVADO_01", "tam": 30, "valor_real": linha_real[282:312], "obs": "Zeros - reservado"})
campos_extras.append({"inicio": 313, "fim": 315, "nome": "CAMPO_EXTRA_10", "tam": 3, "valor_real": linha_real[312:315], "obs": "Espaços"})

# Mais valores
campos_extras.append({"inicio": 316, "fim": 325, "nome": "VALOR_EXTRA_04", "tam": 10, "valor_real": linha_real[315:325], "obs": "Valor numérico"})
campos_extras.append({"inicio": 326, "fim": 395, "nome": "RESERVADO_02", "tam": 70, "valor_real": linha_real[325:395], "obs": "Zeros - grande campo reservado"})

# Campos finais específicos
campos_extras.append({"inicio": 396, "fim": 405, "nome": "CAMPO_EXTRA_11", "tam": 10, "valor_real": linha_real[395:405], "obs": "Valor específico"})
campos_extras.append({"inicio": 406, "fim": 406, "nome": "FLAG_01", "tam": 1, "valor_real": linha_real[405:406], "obs": "Flag D"})
campos_extras.append({"inicio": 407, "fim": 409, "nome": "CAMPO_EXTRA_12", "tam": 3, "valor_real": linha_real[406:409], "obs": "Código"})
campos_extras.append({"inicio": 410, "fim": 415, "nome": "CAMPO_EXTRA_13", "tam": 6, "valor_real": linha_real[409:415], "obs": "Matrícula novamente?"})
campos_extras.append({"inicio": 416, "fim": 424, "nome": "CAMPO_EXTRA_14", "tam": 9, "valor_real": linha_real[415:424], "obs": "Data + código"})
# Últimos 2
campos_extras.append({"inicio": 425, "fim": 426, "nome": "FLAG_FINAL", "tam": 2, "valor_real": linha_real[424:426] if len(linha_real) > 424 else linha_real[423:425], "obs": "SI - flag final"})

print("\nCampos extras identificados:")
for campo in campos_extras:
    print(f"[{campo['inicio']:3d}-{campo['fim']:3d}] {campo['nome']:20s} = '{campo['valor_real']}' | {campo['obs']}")

# Salva layout completo em JSON
layout_completo = {
    "tamanho_total": len(linha_real),
    "campos_documentados": layout_documentado,
    "campos_extras": campos_extras,
    "exemplo_real": linha_real
}

with open('fh1_layout_completo_real.json', 'w', encoding='utf-8') as f:
    json.dump(layout_completo, f, ensure_ascii=False, indent=2)

print("\n" + "=" * 80)
print("✅ Layout completo salvo em: fh1_layout_completo_real.json")
print("=" * 80)

print(f"\nResumo:")
print(f"  • Campos documentados: {len(layout_documentado)} (1-192)")
print(f"  • Campos extras: {len(campos_extras)} (193-{len(linha_real)})")
print(f"  • Tamanho total: {len(linha_real)} caracteres")
