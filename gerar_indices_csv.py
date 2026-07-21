"""
Busca IPCA e TR do BCB e gera o indices_historicos.csv com dados reais.

Indices usados:
  1983-1990: IPCA mensal (serie 433) - proxy para ORTN/OTN/BTNF
  1991-1994: TR mensal acumulada (serie 188) - indice oficial SFH pos-Plano Collor
  1995+:     TR mensal (serie 188)
"""
import urllib.request
import json
from datetime import datetime
import os

BCB = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{s}/dados?formato=json&dataInicial={di}&dataFinal={df}"


def buscar(serie, di, df):
    url = BCB.format(s=serie, di=di, df=df)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())


def aaaamm(data_str):
    return datetime.strptime(data_str, "%d/%m/%Y").strftime("%Y-%m")


# -- IPCA 1983-1990 -----------------------------------------------------------
print("Buscando IPCA 1983-1990...")
ipca = buscar(433, "01/01/1983", "31/12/1990")
ipca_dict = {}
for d in ipca:
    k = aaaamm(d["data"])
    ipca_dict[k] = round(float(d["valor"]) / 100.0, 6)
print(f"  {len(ipca_dict)} registros")

# -- TR 1991-2004 -------------------------------------------------------------
print("Buscando TR mensal 1991-2004...")
tr = buscar(188, "01/01/1991", "31/12/2004")
tr_dict = {}
for d in tr:
    k = aaaamm(d["data"])
    tr_dict[k] = round(float(d["valor"]) / 100.0, 6)
print(f"  {len(tr_dict)} registros")

# -- Montar linhas 1983-01 a 2004-12 -----------------------------------------
linhas = ["AAAA-MM,indice"]

from datetime import date

current = date(1983, 1, 1)
end = date(2004, 12, 31)
while current <= end:
    k = current.strftime("%Y-%m")
    if k in ipca_dict:
        linhas.append(f"{k},{ipca_dict[k]}")
    elif k in tr_dict:
        linhas.append(f"{k},{tr_dict[k]}")
    else:
        # lacuna - pular (o simulador usa 0 como fallback)
        print(f"  AVISO: sem dado para {k}")
    # avançar 1 mês
    if current.month == 12:
        current = date(current.year + 1, 1, 1)
    else:
        current = date(current.year, current.month + 1, 1)

# -- Salvar -------------------------------------------------------------------
out_path = os.path.join(os.path.dirname(__file__), "principal", "indices_historicos.csv")
with open(out_path, "w", encoding="utf-8") as f:
    f.write("\n".join(linhas) + "\n")

print(f"\nArquivo salvo: {out_path}")
print(f"Total linhas (+ header): {len(linhas)}")

# -- Preview ------------------------------------------------------------------
print("\nPrimeiros 15 registros (IPCA/ORTN proxy):")
for l in linhas[1:16]:
    print(" ", l)
print("...")
print("1991-01 em diante (TR real):")
for l in linhas:
    if l.startswith("1991-"):
        print(" ", l)
        break
