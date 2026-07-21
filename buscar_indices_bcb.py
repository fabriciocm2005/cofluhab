"""
Busca índices históricos reais do BCB SGS para atualizar indices_historicos.csv

Series usadas:
  188  = TR mensal acumulada no mês (1991+)
  189  = BTNF mensal (1989-1991)
  7478 = Possível ORTN/OTN (a testar)

Para ORTN (1964-1985) e OTN (1986-1989) o BCB não tem série SGS pública direta.
Usamos valores documentados na literatura (Boletim BCB, FIPE, CEF).
"""
import urllib.request
import json
from datetime import datetime

BCB_BASE = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{serie}/dados?formato=json&dataInicial={di}&dataFinal={df}"


def buscar_serie(serie, data_ini, data_fim):
    url = BCB_BASE.format(serie=serie, di=data_ini, df=data_fim)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"  ERRO serie {serie}: {e}")
        return []


def formatar_aaaamm(data_str):
    """'01/01/1991' -> '1991-01'"""
    d = datetime.strptime(data_str, "%d/%m/%Y")
    return d.strftime("%Y-%m")


# ============================================================
# TR mensal acumulada - serie 188 (1991-01 em diante)
# ============================================================
print("=== Buscando TR mensal (serie 188) 1991-1994 ===")
tr_data = buscar_serie(188, "01/01/1991", "31/12/1994")
tr_mensal = {}
for d in tr_data:
    aaaamm = formatar_aaaamm(d["data"])
    tr_mensal[aaaamm] = float(d["valor"]) / 100.0  # converte % para decimal
for k in sorted(tr_mensal):
    print(f"  {k}: {tr_mensal[k]:.6f}")

# ============================================================
# BTNF mensal - tentar serie 7478, 7449, 189
# ============================================================
print("\n=== Buscando BTNF (tentando series) 1989-1991 ===")
for serie in [7478, 7449, 189, 190, 7392, 1619]:
    d = buscar_serie(serie, "01/01/1989", "31/12/1991")
    if d:
        print(f"  Serie {serie} - primeiros 3: {d[:3]}")
    else:
        print(f"  Serie {serie} - sem dados")

# ============================================================
# IPC mensal (substituto BTNF pos-Jan/1989 pelo Plano Verao)
# serie 733 = IPC FIPE mensal
# ============================================================
print("\n=== Buscando IPC mensal (serie 733 FIPE) 1989-1991 ===")
ipc_data = buscar_serie(733, "01/02/1989", "31/01/1991")
for d in ipc_data[:5]:
    print(f"  {d}")

# ============================================================
# IPCA mensal (serie 433) para cross-check
# ============================================================
print("\n=== Buscando IPCA mensal (serie 433) 1983-1994 ===")
ipca_data = buscar_serie(433, "01/01/1983", "31/12/1994")
ipca_mensal = {}
for d in ipca_data:
    aaaamm = formatar_aaaamm(d["data"])
    ipca_mensal[aaaamm] = float(d["valor"]) / 100.0
print(f"  Total registros IPCA: {len(ipca_mensal)}")
if ipca_mensal:
    for k in sorted(ipca_mensal)[:12]:
        print(f"  {k}: {ipca_mensal[k]:.4f}")

# ============================================================
# IGP-M mensal (serie 189) 1983-1994
# ============================================================
print("\n=== Buscando IGP-M (serie 189) 1983-1994 ===")
igpm_data = buscar_serie(189, "01/01/1983", "31/12/1994")
if igpm_data:
    print(f"  Total registros: {len(igpm_data)}")
    print(f"  Primeiros 6: {igpm_data[:6]}")
