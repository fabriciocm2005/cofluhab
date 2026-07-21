"""
Baixa salario minimo nominal mensal do IPEADATA (serie MTE12_SALMIN12)
e gera o arquivo principal/indices_pes.csv com os fatores mensais.

Formato CSV: AAAA-MM,fator
  fator = SM[mes] / SM[mes-1]  (para meses com reajuste)
        = 1.0                   (para meses sem reajuste)

O simulador usara esse fator para reajustar o PES no mes do aniversario
do contrato (aplicando acumulado desde ultimo reajuste).
"""
import urllib.request
import json
from datetime import datetime
import os

IPEA_URL = "http://ipeadata.gov.br/api/odata4/ValoresSerie(SERCODIGO='MTE12_SALMIN12')?$format=json"


def buscar():
    req = urllib.request.Request(IPEA_URL, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read()).get("value", [])


print("Buscando salario minimo IPEADATA...")
vals = buscar()
print(f"Total registros: {len(vals)}")

# Extrair 1983-01 a 2004-12 e ordenar
registros = []
for v in vals:
    dt_str = v["VALDATA"][:10]  # 1983-01-01
    try:
        dt = datetime.strptime(dt_str, "%Y-%m-%d")
        aaaamm = dt.strftime("%Y-%m")
        valor = float(v["VALVALOR"])
        registros.append((aaaamm, valor))
    except:
        continue

registros.sort()
registros_filtrados = [(k, v) for k, v in registros if "1983-01" <= k <= "2004-12"]
print(f"Registros 1983-2004: {len(registros_filtrados)}")

# Calcular fator de variacao mensal
linhas = ["AAAA-MM,sm_nominal,fator_reajuste"]
for i, (k, v) in enumerate(registros_filtrados):
    if i == 0:
        fator = 1.0
    else:
        v_ant = registros_filtrados[i-1][1]
        fator = v / v_ant if v_ant > 0 else 1.0
    linhas.append(f"{k},{v:.12e},{fator:.6f}")

out_path = os.path.join(os.path.dirname(__file__), "principal", "indices_pes.csv")
with open(out_path, "w", encoding="utf-8") as f:
    f.write("\n".join(linhas) + "\n")

print(f"\nArquivo salvo: {out_path}")
print(f"Total linhas (+ header): {len(linhas)}")

# Preview: mostrar apenas meses com reajuste (fator != 1.0)
print("\nMeses com reajuste do salario minimo:")
for l in linhas[1:]:
    parts = l.split(",")
    fator = float(parts[2])
    if abs(fator - 1.0) > 0.0001:
        print(f"  {parts[0]}: fator={fator:.4f} (+{(fator-1)*100:.1f}%)")
