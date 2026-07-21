"""
Busca salario minimo nominal (serie 1210) do BCB e calcula o indice de
reajuste anual do PES para o simulador SFH.

Na PES, o reajuste ocorre uma vez por ano no mes do contrato, aplicando
a variacao acumulada do salario minimo desde o ultimo reajuste.
"""
import urllib.request
import json
from datetime import datetime, date

BCB = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{s}/dados?formato=json&dataInicial={di}&dataFinal={df}"


def buscar(serie, di, df):
    url = BCB.format(s=serie, di=di, df=df)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())


def aaaamm(data_str):
    return datetime.strptime(data_str, "%d/%m/%Y").strftime("%Y-%m")


# -- Salario Minimo Nominal (serie 1210) 1983-1994 ----------------------------
print("Buscando salario minimo nominal (serie 1210)...")
sm = buscar(1210, "01/01/1983", "31/12/1994")
print(f"Total: {len(sm)}")
print()

# Mostrar tudo para entender escala e frequencia
print("Data         | Valor")
print("-" * 30)
for d in sm:
    print(f"{d['data']:12} | {d['valor']}")

# Calcular variacao anual (fator de reajuste)
print()
print("=== FATOR REAJUSTE ANUAL (mes-a-mes) ===")
vals = [(aaaamm(d['data']), float(d['valor'])) for d in sm]
for i in range(1, len(vals)):
    k_ant, v_ant = vals[i-1]
    k_cur, v_cur = vals[i]
    fator = v_cur / v_ant if v_ant > 0 else 1.0
    if fator > 1.0:
        print(f"{k_ant} -> {k_cur}: fator={fator:.4f} (+{(fator-1)*100:.1f}%)")
