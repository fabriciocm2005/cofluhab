"""
Script para extrair estrutura completa do layout P3026 do arquivo Excel
Gera JSON com especificações de todos os tipos de registro (TR1-TR9)
"""

import pandas as pd
import json
import os

ARQUIVO_LAYOUT = r"principal\templates\Leiaute_FCVS3026_TR1_a_TR9_270417 (1).xls"
ARQUIVO_SAIDA = r"principal\ficha_p3026_layout.json"

def extrair_layout():
    """Extrai estrutura de todos os TRs do arquivo Excel"""
    
    estrutura = {}
    
    for tipo in ['TR1', 'TR2', 'TR3', 'TR4', 'TR5', 'TR6', 'TR7', 'TR8', 'TR9']:
        df = pd.read_excel(ARQUIVO_LAYOUT, sheet_name=tipo, header=None)
        
        # Extrair campos
        campos = []
        for idx in range(3, len(df)):  # Começar da linha 3
            try:
                seq = df.iloc[idx, 0]
                nome_campo = df.iloc[idx, 1]
                posicao = df.iloc[idx, 2]
                tamanho = df.iloc[idx, 3]
                formato = df.iloc[idx, 4]
                descricao = df.iloc[idx, 5] if pd.notna(df.iloc[idx, 5]) else ""
                
                # Validar que temos dados
                if pd.isna(seq):
                    break
                
                # Tentar converter seq para int
                try:
                    seq = int(seq)
                except (ValueError, TypeError):
                    continue
                
                # Converter para strings
                seq = str(seq)
                nome_campo = str(nome_campo).strip() if pd.notna(nome_campo) else ""
                posicao = str(posicao).strip() if pd.notna(posicao) else ""
                tamanho = str(tamanho).strip() if pd.notna(tamanho) else ""
                formato = str(formato).strip() if pd.notna(formato) else ""
                descricao = str(descricao).strip() if pd.notna(descricao) else ""
                
                if nome_campo and posicao:
                    campos.append({
                        "sequencia": seq,
                        "nome": nome_campo,
                        "posicao": posicao,
                        "tamanho": tamanho,
                        "formato": formato,
                        "descricao": descricao
                    })
            except Exception as e:
                continue
        
        estrutura[tipo] = {
            "descricao": f"Tipo de Registro {tipo}",
            "total_campos": len(campos),
            "campos": campos
        }
        
        print(f"✓ {tipo}: {len(campos)} campos extraídos")
    
    # Salvar JSON
    os.makedirs(os.path.dirname(ARQUIVO_SAIDA), exist_ok=True)
    with open(ARQUIVO_SAIDA, 'w', encoding='utf-8') as f:
        json.dump(estrutura, f, indent=2, ensure_ascii=False)
    
    print(f"\nLayout salvo em: {ARQUIVO_SAIDA}")
    return estrutura

if __name__ == '__main__':
    estrutura = extrair_layout()
    
    # Mostrar resumo
    print("\n" + "="*60)
    print("RESUMO DA ESTRUTURA P3026")
    print("="*60)
    for tipo, info in estrutura.items():
        print(f"{tipo}: {info['total_campos']} campos")
