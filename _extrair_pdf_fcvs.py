import pdfplumber
import pathlib

base = pathlib.Path(r'c:\Users\fabri\cofluhab\cofluhab\manual')
roteiro = base / 'Roteiro de Analise do Fundo de Compensacao de Variacoes Salariais (CCFCVS) SEM NUMERO DE 19_10_2005 - Federal - LegisWeb.pdf'
anexos  = base / 'Anexos-do-Roteiro-de-Analise-do-FCVS.pdf'

# Tenta o nome com acentos se o sem-acento não existir
if not roteiro.exists():
    roteiro = base / 'Roteiro de An\u00e1lise do Fundo de Compensa\u00e7\u00e3o de Varia\u00e7\u00f5es Salariais (CCFCVS) SEM N\u00daMERO DE 19_10_2005 - Federal - LegisWeb.pdf'

def ler(path):
    t = []
    with pdfplumber.open(path) as pdf:
        for i, pg in enumerate(pdf.pages, 1):
            x = pg.extract_text()
            if x:
                t.append(f'--- PAGINA {i} ---\n{x}')
    return '\n\n'.join(t)

(base / '_roteiro_fcvs_texto.txt').write_text(ler(roteiro), encoding='utf-8')
(base / '_anexos_fcvs_texto.txt').write_text(ler(anexos), encoding='utf-8')
print('OK')
