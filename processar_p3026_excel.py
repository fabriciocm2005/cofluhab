"""
Processa o arquivo Excel do P3026 e extrai layouts estruturados
"""
import json
import pandas as pd

def processar_p3026():
    """Extrai os layouts do arquivo P3026 Excel"""
    
    caminho = r"C:\Users\fabri\cofluhab\dados_antigos\manuais\Leiaute_FCVS3026_TR1_a_TR9_270417.xls"
    
    print("=" * 80)
    print("PROCESSAMENTO DO ARQUIVO P3026")
    print("=" * 80)
    print(f"\nArquivo: {caminho}")
    
    try:
        xls = pd.ExcelFile(caminho)
        print(f"\n✅ Arquivo carregado com sucesso!")
        print(f"Abas encontradas: {xls.sheet_names}")
        
        layouts = {}
        
        for sheet_name in xls.sheet_names:
            print(f"\n📋 Processando aba: {sheet_name}")
            df = pd.read_excel(xls, sheet_name)
            
            # Identifica a coluna de sequência (pode ter espaços diferentes)
            col_seq = [c for c in df.columns if c.startswith('FCVS3026')][0]
            
            # Filtra apenas linhas com número de sequência válido
            campos_validos = []
            for idx, row in df.iterrows():
                seq_value = row.get(col_seq)
                
                # Verifica se é um número de sequência válido
                is_valid = False
                if isinstance(seq_value, (int, float)):
                    is_valid = True
                elif isinstance(seq_value, str) and seq_value.strip().isdigit():
                    is_valid = True
                
                if is_valid:
                    campos_validos.append({
                        'seq': str(seq_value).strip(),
                        'colunas': str(row.get('Unnamed: 1', '')).strip(),
                        'descricao': str(row.get('Unnamed: 2', '')).strip(),
                        'tamanho': str(row.get('Unnamed: 3', '')).strip(),
                        'formato': str(row.get('Unnamed: 4', '')).strip(),
                        'tipo': str(row.get('Unnamed: 5', '')).strip()
                    })
            
            layouts[sheet_name] = {
                'nome': sheet_name,
                'descricao': f'Tipo de Registro {sheet_name}',
                'total_campos': len(campos_validos),
                'campos': campos_validos
            }
            
            print(f"   ✅ {len(campos_validos)} campos extraídos")
        
        # Salva resultado
        output_file = 'p3026_layouts_estruturado.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(layouts, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'=' * 80}")
        print(f"✅ PROCESSAMENTO CONCLUÍDO!")
        print(f"{'=' * 80}")
        print(f"\nArquivo salvo: {output_file}")
        print(f"\nResumo:")
        for sheet, dados in layouts.items():
            print(f"  • {sheet}: {dados['total_campos']} campos")
        
        # Exibe exemplo do primeiro TR
        print(f"\n{'=' * 80}")
        print(f"EXEMPLO: TR1 - Primeiros 10 campos")
        print(f"{'=' * 80}")
        for campo in layouts['TR1']['campos'][:10]:
            seq_num = campo['seq']
            desc = campo['descricao'][:50] if len(campo['descricao']) > 50 else campo['descricao']
            print(f"  {seq_num}. {desc:50s} - Pos {campo['colunas']}")
        
        return layouts
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    layouts = processar_p3026()
    
    if layouts:
        print(f"\n✅ Sucesso! {len(layouts)} tipos de registro processados.")
