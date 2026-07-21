import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from principal.models import Mutuario, Endereco
from datetime import datetime

TXT_PATH = r'C:\Users\fabri\cofluhab\dados_antigos\acerto_cadmut\Mutuario.txt'

# Mapeamento de conjunto antigo para novo
CONJUNTO_MAP = {
    '000442': '010',  # S STA PAULA
    '000443': '011',  # MARAMBAIA
    # Adicionar outros se necessário
}

def safe_date(value):
    """Converte string AAAAMMDD para date"""
    if not value or value.strip() == '':
        return None
    try:
        value = value.strip()
        if len(value) == 8:
            ano = int(value[0:4])
            mes = int(value[4:6])
            dia = int(value[6:8])
            return datetime(ano, mes, dia).date()
    except:
        pass
    return None

def importar_mutuarios_txt():
    print("Iniciando importação de mutuários do Mutuario.txt...")
    
    contador = 0
    erros = 0
    atualizados = 0
    criados = 0
    
    with open(TXT_PATH, 'r', encoding='latin-1') as f:
        # Pular cabeçalho
        next(f)
        
        for linha in f:
            try:
                campos = linha.strip().split('\t')
                
                if len(campos) < 9:
                    continue
                
                conjunto_antigo = campos[0].strip()
                codigo = str(int(campos[1].strip()))  # Normalizar código
                nome = campos[4].strip() if len(campos) > 4 else ''
                cpf = campos[6].strip() if len(campos) > 6 else ''
                ident = campos[7].strip() if len(campos) > 7 else ''
                dtnasc = safe_date(campos[8]) if len(campos) > 8 else None
                
                # Converter conjunto
                conjunto = CONJUNTO_MAP.get(conjunto_antigo, conjunto_antigo)
                
                # Criar ou atualizar mutuário
                mutuario, created = Mutuario.objects.update_or_create(
                    codigo=codigo,
                    conjunto=conjunto,
                    defaults={
                        'nome': nome,
                        'cpf': cpf,
                        'ident': ident,
                        'dtnasc': dtnasc,
                    }
                )
                
                contador += 1
                if created:
                    criados += 1
                else:
                    atualizados += 1
                    
                if contador % 100 == 0:
                    print(f"Processados: {contador} | Criados: {criados} | Atualizados: {atualizados}")
                    
            except Exception as e:
                erros += 1
                if erros <= 5:
                    print(f"Erro na linha: {linha[:50]}... | {str(e)}")
    
    print(f"\n✓ Importação concluída!")
    print(f"  Total processado: {contador}")
    print(f"  Criados: {criados}")
    print(f"  Atualizados: {atualizados}")
    print(f"  Erros: {erros}")

if __name__ == '__main__':
    importar_mutuarios_txt()
