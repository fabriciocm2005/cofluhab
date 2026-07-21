"""
Busca salario minimo NOMINAL mensal do IPEADATA para calcular reajuste PES.

IPEADATA codes:
  MTE12_SALMIN12 = Salario minimo nominal (Cr$ / Cz$ / etc)
  GAC12_SALNOMINAL = outro possivel
"""
import urllib.request
import json

IPEA_BASE = "http://ipeadata.gov.br/api/odata4/ValoresSerie(SERCODIGO='{code}')?$format=json"


def buscar_ipea(code):
    url = IPEA_BASE.format(code=code)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read())
    return data.get("value", [])


# Tentar varios codigos
for code in ["MTE12_SALMIN12", "GAC12_SALNOMINAL", "SALMINIMAL", "MTE_SALMIN"]:
    print(f"Tentando IPEADATA: {code}")
    try:
        vals = buscar_ipea(code)
        if vals:
            # Filtrar 1983+
            vals83 = [v for v in vals if v.get("VALDATA", "")[:4] >= "1983"]
            print(f"  Total: {len(vals)}, 1983+: {len(vals83)}")
            for v in vals83[:8]:
                print(f"  {v.get('VALDATA','')} = {v.get('VALVALOR','')}")
        else:
            print("  Sem dados")
    except Exception as e:
        print(f"  ERRO: {e}")
    print()
