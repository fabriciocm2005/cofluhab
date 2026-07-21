# -*- coding: utf-8 -*-
import sqlite3
import sys

# Mapeamento de palavras mal-formadas para corretas
PALAVRAS_CORRECAO = {
    'CONCEIAO': 'CONCEICAO',
    'CONCEIÇAO': 'CONCEICAO',
    'VALENA': 'VALENÇA',
    'SAO': 'SAO',
    'ESPERANA': 'ESPERANCA',
}

def corrigir_palavras(texto):
    """Corrige palavras conhecidas que ficaram mal-formadas."""
    if not texto:
        return texto
    
    resultado = texto
    for palavra_errada, palavra_certa in PALAVRAS_CORRECAO.items():
        resultado = resultado.replace(palavra_errada, palavra_certa)
    
    return resultado

def corrigir_tabela(conn, tabela, campos):
    """Corrige palavras em uma tabela."""
    cursor = conn.cursor()
    
    print(f"\nCorrigindo tabela: {tabela}")
    print(f"Campos: {', '.join(campos)}")
    
    cursor.execute(f"SELECT id, {', '.join(campos)} FROM {tabela}")
    registros = cursor.fetchall()
    
    print(f"Total de registros: {len(registros)}")
    
    count = 0
    for registro in registros:
        id_registro = registro[0]
        valores_antigos = registro[1:]
        
        valores_novos = []
        for valor in valores_antigos:
            if valor:
                valores_novos.append(corrigir_palavras(str(valor)))
            else:
                valores_novos.append(valor)
        
        if valores_novos != list(valores_antigos):
            count += 1
            if count <= 5:
                print(f"\n  Registro ID {id_registro}:")
                for i, campo in enumerate(campos):
                    if valores_novos[i] != valores_antigos[i]:
                        print(f"    {campo}: '{valores_antigos[i]}' → '{valores_novos[i]}'")
            
            sets = []
            params = []
            for i, campo in enumerate(campos):
                sets.append(f"{campo} = ?")
                params.append(valores_novos[i])
            params.append(id_registro)
            
            sql = f"UPDATE {tabela} SET {', '.join(sets)} WHERE id = ?"
            cursor.execute(sql, params)
    
    conn.commit()
    print(f"\n✅ Registros alterados: {count} de {len(registros)}")
    return count

def main():
    print("\n" + "="*80)
    print("CORREÇÃO DE PALAVRAS MAL-FORMADAS NO BANCO DE DADOS")
    print("="*80 + "\n")
    
    confirmacao = input("⚠️  Esta operação vai alterar o banco de dados. Deseja continuar? (S/N): ")
    if confirmacao.upper() != 'S':
        print("Operação cancelada.")
        sys.exit(0)
    
    print("\n" + "="*80)
    
    conn = sqlite3.connect('db.sqlite3')
    
    total = 0
    total += corrigir_tabela(conn, 'principal_mutuario', 
                             ['nome', 'endereco', 'bairro', 'cidade', 'compl'])
    total += corrigir_tabela(conn, 'principal_endereco',
                             ['endereco', 'compl', 'bairro', 'cidade'])
    total += corrigir_tabela(conn, 'principal_contrato',
                             ['cod_imovel'])
    
    conn.close()
    
    print("\n" + "="*80)
    print(f"✅ CORREÇÃO CONCLUÍDA!")
    print(f"Total de registros alterados: {total}")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
