import pdfplumber
import sys
import os

def extract_pdf(pdf_path, output_path, name):
    """Extrai texto de um PDF e salva em arquivo"""
    print(f"\n{'='*80}")
    print(f"Extraindo {name}...")
    print(f"Origem: {pdf_path}")
    print(f"Destino: {output_path}")
    print('='*80)
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            print(f"Total de páginas: {total_pages}")
            
            full_text = []
            for i, page in enumerate(pdf.pages):
                print(f"Processando página {i+1}/{total_pages}...", end='\r')
                text = page.extract_text()
                if text:
                    full_text.append(f"\n{'='*80}\n--- PÁGINA {i+1} de {total_pages} ---\n{'='*80}\n")
                    full_text.append(text)
            
            content = '\n'.join(full_text)
            
            # Salvar em arquivo
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"\n✓ {name} extraído com sucesso!")
            print(f"  - {total_pages} páginas processadas")
            print(f"  - {len(content):,} caracteres extraídos")
            return True
            
    except Exception as e:
        print(f"\n✗ Erro ao extrair {name}: {str(e)}")
        return False

def main():
    base_path = r'C:\Users\fabri\cofluhab\cofluhab\manual'
    output_path = r'C:\Users\fabri\cofluhab\cofluhab'
    
    pdfs = [
        ('CADMUT', 'Leiautes_Movim_CADMUT - 2025 (1).pdf', 'cadmut_extracted.txt'),
        ('FCVS', 'Leiautes_Movim_FCVS - 2025 - V2 (1).pdf', 'fcvs_extracted.txt'),
        ('SIWFC', 'Manual_SIWFC_MAR_2025 (1).pdf', 'siwfc_extracted.txt')
    ]
    
    print("EXTRAÇÃO DE PDFs DA CEF - 2025")
    print("="*80)
    
    results = []
    for name, pdf_file, output_file in pdfs:
        pdf_path = os.path.join(base_path, pdf_file)
        output_full_path = os.path.join(output_path, output_file)
        success = extract_pdf(pdf_path, output_full_path, name)
        results.append((name, success))
    
    print(f"\n{'='*80}")
    print("RESUMO DA EXTRAÇÃO")
    print('='*80)
    for name, success in results:
        status = "✓ Sucesso" if success else "✗ Falha"
        print(f"{name}: {status}")
    
    all_success = all(success for _, success in results)
    if all_success:
        print("\n✓ Todos os arquivos foram extraídos com sucesso!")
        return 0
    else:
        print("\n✗ Alguns arquivos falharam na extração.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
