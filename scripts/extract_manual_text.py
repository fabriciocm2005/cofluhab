import re
from pathlib import Path
from PyPDF2 import PdfReader

pdf_dir = Path(r"C:\Users\fabri\cofluhab\cofluhab\manual")
pdf_files = [
    pdf_dir / "Manual_SIWFC_MAR_2025.pdf",
    pdf_dir / "Leiautes_Movim_FCVS - 2025 - V2.pdf",
    pdf_dir / "Leiautes_Movim_FCVS - 2025 - V2 (1).pdf",
    pdf_dir / "Leiautes_Movim_CADMUT - 2025.pdf",
    pdf_dir / "Leiautes_Movim_CADMUT - 2025 (1).pdf",
    pdf_dir / "Leiaute_CADMUT_Espelho.pdf",
]

terms = ["FH1", "IDENTIFICA", "LOTE", "MATRICULA", "AGENTE FINANCEIRO", "HEADER", "DADOS", "SEQUENC", "HIPOTECA"]

for pdf_path in pdf_files:
    if not pdf_path.exists():
        continue
    print("\n" + "=" * 80)
    print(f"Arquivo: {pdf_path.name}")
    reader = PdfReader(str(pdf_path))
    text = "".join((page.extract_text() or "") for page in reader.pages)
    text = re.sub(r"\s+", " ", text)

    for term in terms:
        idx = text.upper().find(term)
        print(f"{term}: {idx}")

    print("\n--- SNIPPET (IDENTIFICA/LOTE) ---")
    snippet_found = False
    for m in re.finditer(r"IDENTIFICA", text, re.IGNORECASE):
        start = max(m.start() - 200, 0)
        end = min(m.end() + 400, len(text))
        snippet = text[start:end]
        if "LOTE" in snippet.upper():
            print(snippet)
            snippet_found = True
            break
    if not snippet_found:
        print("(sem snippet com IDENTIFICA + LOTE)")

    print("\n--- SNIPPET (SEQUENC/HIPOTECA) ---")
    snippet_found = False
    for m in re.finditer(r"SEQUENC|HIPOTECA", text, re.IGNORECASE):
        start = max(m.start() - 200, 0)
        end = min(m.end() + 400, len(text))
        snippet = text[start:end]
        if "FH1" in snippet.upper() or "HIPOTECA" in snippet.upper():
            print(snippet)
            snippet_found = True
            break
    if not snippet_found:
        print("(sem snippet com SEQUENC/HIPOTECA)")
