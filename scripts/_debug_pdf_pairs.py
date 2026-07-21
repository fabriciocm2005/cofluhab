import pdfplumber
import re
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PDF_PATH = os.path.join(PROJECT_ROOT, "manual", "divida seguro 01_2019.pdf")

PDF_FIF_LINE = re.compile(r"^\s*(\d{15})\s+(.+?)\s+\d{1,3},\d{2}\s+\d")
PDF_CONTRATO_LINE = re.compile(r"^\s*(\d{6})\s+\d{2}/\d{4}\s+")

fif_count = 0
paired = 0
unmatched = []

with pdfplumber.open(PDF_PATH) as pdf:
    for page in pdf.pages:
        lines = (page.extract_text() or "").splitlines()
        i = 0
        while i < len(lines):
            if PDF_FIF_LINE.match(lines[i]):
                fif_count += 1
                found = False
                for j in range(i + 1, min(i + 4, len(lines))):
                    if PDF_CONTRATO_LINE.match(lines[j]):
                        paired += 1
                        found = True
                        break
                if not found:
                    block = [f"PAG {page.page_number} linha {i}: {lines[i][:100]}"]
                    for k in range(i + 1, min(i + 5, len(lines))):
                        block.append(f"  >> {lines[k][:100]}")
                    unmatched.extend(block)
            i += 1

print(f"FIF encontrados: {fif_count}")
print(f"Pareados com CONTRATO: {paired}")
print(f"FIF sem contrato correspondente: {len([x for x in unmatched if not x.startswith('  ')])}")
print()
for line in unmatched:
    print(line)
