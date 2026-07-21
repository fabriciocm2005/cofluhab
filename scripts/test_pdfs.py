"""
Validador robusto de PDFs - testa quais podem ser processados.
"""

import os
import sys
from pathlib import Path

import pdfplumber

PDF_BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "manual", "divida_seguro")

def test_pdfs():
    """Testa todos os PDFs para identificar problemáticos."""
    
    for folder_name in ["CAD_APOLICE", "RIE_OFI", "RMO_OFI"]:
        folder = os.path.join(PDF_BASE_DIR, folder_name)
        if not os.path.exists(folder):
            continue
        
        print(f"\n[{folder_name}]")
        pdf_files = sorted(Path(folder).glob("*.pdf"))
        
        good = []
        bad = []
        
        for pdf_path in pdf_files:
            try:
                with pdfplumber.open(str(pdf_path)) as pdf:
                    # Try to get basic info
                    num_pages = len(pdf.pages)
                    
                    # Try to extract text from first page
                    if num_pages > 0:
                        text = pdf.pages[0].extract_text()
                        if text and len(text.strip()) > 10:
                            good.append(pdf_path.name)
                        else:
                            bad.append((pdf_path.name, "text extract failed"))
                    else:
                        bad.append((pdf_path.name, "no pages"))
                        
            except Exception as e:
                bad.append((pdf_path.name, str(e)[:80]))
        
        print(f"  OK: {len(good)}/{len(pdf_files)}")
        if bad:
            print(f"  PROBLEMATICOS: {len(bad)}")
            for name, reason in bad:
                print(f"    - {name}: {reason[:60]}...")

if __name__ == "__main__":
    test_pdfs()
