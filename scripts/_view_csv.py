import csv
import os

csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "exports", "confronto_divida_seguro_012019_20260515_213542.csv"))

with open(csv_path, encoding="utf-8-sig") as f:
    r = csv.DictReader(f, delimiter=";")
    print("Contrato | Nome                       | Prêmio PDF    | Devido       | Excesso      | %Exc")
    print("-" * 95)
    for i, row in enumerate(r):
        if i >= 10:
            break
        print(
            f"{row['contrato_db']:8s} | {row['nome_mutuario'][:25]:25s} | "
            f"{row['valor_prêmio_pdf']:>12s} | {row['valor_seguro_devido']:>12s} | "
            f"{row['valor_em_excesso']:>12s} | {row['percentual_excesso']:>6s}"
        )
