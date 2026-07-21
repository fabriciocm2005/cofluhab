"""
Corrige caracteres especiais mal codificados no banco de dados
Substitui caracteres problemáticos por versões ASCII
"""
import sqlite3
import os
import sys

# Mapeamento de caracteres problemáticos
REPLACEMENTS = {
    # Ç, ç
    'Ç': 'C',
    'ç': 'c',
    # Acentos
    'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a', 'ä': 'a',
    'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
    'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
    'ó': 'o', 'ò': 'o', 'õ': 'o', 'ô': 'o', 'ö': 'o',
    'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
    'Á': 'A', 'À': 'A', 'Ã': 'A', 'Â': 'A', 'Ä': 'A',
    'É': 'E', 'È': 'E', 'Ê': 'E', 'Ë': 'E',
    'Í': 'I', 'Ì': 'I', 'Î': 'I', 'Ï': 'I',
    'Ó': 'O', 'Ò': 'O', 'Õ': 'O', 'Ô': 'O', 'Ö': 'O',
    'Ú': 'U', 'Ù': 'U', 'Û': 'U', 'Ü': 'U',
}

def limpar_texto(texto):
    """Remove caracteres especiais e acentos."""
    if not texto:
        return texto
    
    # Primeiro, limpar caracteres inválidos/mal-formados
    # Tentar decodificar como latin-1 e recodificar como ASCII
    try:
        # Remove bytes inválidos
        texto_limpo = texto.encode('utf-8', errors='ignore').decode('utf-8')
        # Remove caracteres de controle e inválidos
        texto_limpo = ''.join(char if ord(char) < 127 or ord(char) > 159 else '' for char in texto_limpo)
    except:
        texto_limpo = texto
    
    resultado = texto_limpo
    for char_old, char_new in REPLACEMENTS.items():
        resultado = resultado.replace(char_old, char_new)
    
    return resultado

def corrigir_tabela(conn, tabela, campos):
    """Corrige caracteres especiais em uma tabela"""
    print(f"\n{'='*80}")
    print(f"Corrigindo tabela: {tabela}")
    print(f"Campos: {', '.join(campos)}")
    print(f"{'='*80}")
    
    cursor = conn.cursor()
    
    # Buscar todos os registros
    cursor.execute(f"SELECT id, {', '.join(campos)} FROM {tabela}")
    registros = cursor.fetchall()
    
    total = len(registros)
    alterados = 0
    
    print(f"\nTotal de registros: {total}")
    
    for registro in registros:
        id_registro = registro[0]
        valores_antigos = registro[1:]
        
        # Limpar cada campo
        valores_novos = [limpar_texto(str(v)) if v else v for v in valores_antigos]
        
        # Verificar se houve alteração
        if valores_novos != list(valores_antigos):
            alterados += 1
            
            # Montar UPDATE
            sets = []
            params = []
            for i, campo in enumerate(campos):
                sets.append(f"{campo} = ?")
                params.append(valores_novos[i])
            params.append(id_registro)
            
            sql = f"UPDATE {tabela} SET {', '.join(sets)} WHERE id = ?"
            cursor.execute(sql, params)
            
            # Mostrar exemplo (primeiros 5)
            if alterados <= 5:
                print(f"\n  Registro ID {id_registro}:")
                for i, campo in enumerate(campos):
                    if valores_antigos[i] != valores_novos[i]:
                        print(f"    {campo}: '{valores_antigos[i]}' → '{valores_novos[i]}'")
    
    conn.commit()
    
    print(f"\n✅ Registros alterados: {alterados} de {total}")
    return alterados

def main():
    print("="*80)
    print("CORREÇÃO DE CARACTERES ESPECIAIS NO BANCO DE DADOS")
    print("="*80)
    
    # Conectar ao banco
    conn = sqlite3.connect('db.sqlite3')
    
    total_alterados = 0
    
    # Mutuários
    total_alterados += corrigir_tabela(conn, 'principal_mutuario', [
        'nome', 'endereco', 'bairro', 'cidade', 'compl'
    ])
    
    # Endereços
    total_alterados += corrigir_tabela(conn, 'principal_endereco', [
        'endereco', 'compl', 'bairro', 'cidade'
    ])
    
    # Contratos (se tiver campos de texto)
    total_alterados += corrigir_tabela(conn, 'principal_contrato', [
        'cod_imovel'
    ])
    
    conn.close()
    
    print("\n" + "="*80)
    print(f"✅ CORREÇÃO CONCLUÍDA!")
    print(f"Total de registros alterados: {total_alterados}")
    print("="*80)

if __name__ == '__main__':
    resposta = input("\n⚠️  Esta operação vai alterar o banco de dados. Deseja continuar? (S/N): ")
    if resposta.upper() == 'S':
        main()
    else:
        print("\n❌ Operação cancelada.")
