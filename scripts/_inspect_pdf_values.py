import pdfplumber
import os

pdf_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "manual", "divida seguro 01_2019.pdf"))
with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[0]
    text = page.extract_text() or ""
    lines = text.splitlines()

    print("=== PAR DE LINHAS 5695 (ARGEMIRO) ===")
    for i in range(5, 7):
        print(f"Linha {i}: {lines[i]}")

    print()
    print("=== PRÓXIMO PAR 5697 (ARY) ===")
    for i in range(7, 9):
        print(f"Linha {i}: {lines[i]}")
