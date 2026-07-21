"""
Extrai o leiaute completo da FH1 do PDF para ver posições corretas
"""
import re
from pathlib import Path
from PyPDF2 import PdfReader

pdf_path = Path(r"C:\Users\fabri\cofluhab\cofluhab\manual\Leiautes_Movim_FCVS - 2025 - V2.pdf")
reader = PdfReader(str(pdf_path))
text = "".join((page.extract_text() or "") for page in reader.pages)

# Procura por "FH1" e extrai o leiaute
fh1_idx = text.upper().find("FH1")
if fh1_idx > 0:
    # Extrai 5000 caracteres após "FH1"
    snippet = text[fh1_idx:fh1_idx+5000]
    
    # Procura pela tabela de posições
    lines = snippet.split('\n')
    
    print("LEIAUTE FH1 - POSICOES:")
    print("="*100)
    
    capture = False
    for i, line in enumerate(lines):
        # Procura pelo início da tabela
        if 'SEQ' in line and 'NOME' in line and 'TIPO' in line:
            capture = True
        
        if capture:
            # Para quando encontra "TIPO DE MOVIMENTO"
            if 'TIPO DE MOVIMENTO' in line and capture and i > 5:
                break
            print(line)

print("\n" + "="*100)
print("\nPROCURANDO ESPECIFICAMENTE MATRICULA E HEADER:")
print("="*100)

# Procura por "MAT" ou "MATRICULA" 
for m in re.finditer(r"MAT.*AG.*FINANC|MATRICULA", text, re.IGNORECASE):
    start = max(m.start() - 300, 0)
    end = min(m.end() + 500, len(text))
    snippet = text[start:end]
    print("\n---")
    print(snippet)
