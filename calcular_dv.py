"""
Calcula o DV (Dígito Verificador) da matrícula 44 usando módulo 11
"""

def calcular_dv_modulo11(matricula_str):
    """Calcula dígito verificador módulo 11 para matrícula CEF"""
    mat = matricula_str.zfill(5)  # 5 dígitos de matrícula
    print(f"Matrícula padronizada: {mat}")
    
    multiplicadores = [2, 3, 4, 5, 6, 7, 8, 9]
    soma = 0
    
    for i, digito in enumerate(mat):
        mult = multiplicadores[i % 8]
        valor = int(digito) * mult
        soma += valor
        print(f"Posição {i}: dígito={digito}, multiplicador={mult}, valor={valor}, soma acumulada={soma}")
    
    resto = soma % 11
    print(f"\nSoma total: {soma}")
    print(f"Resto (soma % 11): {resto}")
    
    if resto == 0 or resto == 1:
        dv = '0'
    else:
        dv = str(11 - resto)
    
    print(f"DV calculado: {dv}")
    print(f"\nMatrícula completa (5 dig + DV): {mat}{dv}")
    print(f"Para enviar no arquivo (6 posições): {mat}{dv}")
    
    return dv

print("="*60)
print("CALCULANDO DV PARA MATRÍCULA 44 (COFLUHAB)")
print("="*60)

dv = calcular_dv_modulo11('44')

print("\n" + "="*60)
print("VERIFICANDO OUTRAS POSSIBILIDADES:")
print("="*60)

# Testa se a matrícula poderia ser outra
for mat in ['44', '444', '4400', '0044']:
    print(f"\nMatrícula: {mat}")
    calcular_dv_modulo11(mat)
