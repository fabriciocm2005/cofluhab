"""
Teste de cálculo de DV para matrícula 000044
Testa diferentes algoritmos módulo 11
"""

def calcular_dv_modulo11_v1(matricula_str):
    """Algoritmo 1: Multiplicadores [2,3,4,5,6,7,8,9] ciclando"""
    mat = matricula_str.zfill(5)
    multiplicadores = [2, 3, 4, 5, 6, 7, 8, 9]
    soma = 0
    for i, digito in enumerate(mat):
        soma += int(digito) * multiplicadores[i % 8]
    resto = soma % 11
    if resto == 0 or resto == 1:
        return '0'
    return str(11 - resto)

def calcular_dv_modulo11_v2(matricula_str):
    """Algoritmo 2: Multiplicadores [9,8,7,6,5] (inverso, 5 posições)"""
    mat = matricula_str.zfill(5)
    multiplicadores = [9, 8, 7, 6, 5]
    soma = 0
    for i, digito in enumerate(mat):
        soma += int(digito) * multiplicadores[i]
    resto = soma % 11
    if resto == 0 or resto == 1:
        return '0'
    return str(11 - resto)

def calcular_dv_modulo11_v3(matricula_str):
    """Algoritmo 3: Multiplicadores [2,3,4,5,6,7,8,9,2,3] (10 posições)"""
    mat = matricula_str.zfill(5)
    multiplicadores = [2, 3, 4, 5, 6, 7, 8, 9, 2, 3]
    soma = 0
    for i, digito in enumerate(mat):
        soma += int(digito) * multiplicadores[i]
    resto = soma % 11
    if resto == 0 or resto == 1:
        return '0'
    return str(11 - resto)

def calcular_dv_modulo11_v4(matricula_str):
    """Algoritmo 4: Multiplicadores [9,8,7,6,5,4,3,2] (inverso)"""
    mat = matricula_str.zfill(5)
    multiplicadores = [9, 8, 7, 6, 5]
    soma = 0
    for i, digito in enumerate(mat):
        soma += int(digito) * multiplicadores[i]
    resto = soma % 11
    if resto == 0 or resto == 1:
        return '0'
    return str(11 - resto)

def calcular_dv_modulo11_v5(matricula_str):
    """Algoritmo 5: Com resto 10 = 0"""
    mat = matricula_str.zfill(5)
    multiplicadores = [2, 3, 4, 5, 6, 7, 8, 9]
    soma = 0
    for i, digito in enumerate(mat):
        soma += int(digito) * multiplicadores[i % 8]
    resto = soma % 11
    if resto == 0 or resto == 1 or resto == 10:
        return '0'
    return str(11 - resto)

# Testa todos os algoritmos
matricula = "000044"
print(f"Testando matrícula: {matricula}")
print(f"Algoritmo 1 (cicla [2-9]):    {matricula}+{calcular_dv_modulo11_v1(matricula)}")
print(f"Algoritmo 2 (trunca [2-6]):   {matricula}+{calcular_dv_modulo11_v2(matricula)}")
print(f"Algoritmo 3 (10 posições):    {matricula}+{calcular_dv_modulo11_v3(matricula)}")
print(f"Algoritmo 4 (inverso):        {matricula}+{calcular_dv_modulo11_v4(matricula)}")
print(f"Algoritmo 5 (resto10=0):      {matricula}+{calcular_dv_modulo11_v5(matricula)}")

# Mostra os cálculos
print("\nDetalhes do Algoritmo 1:")
mat = "00044"
mult = [2, 3, 4, 5, 6]
for i, d in enumerate(mat):
    print(f"  {d} × {mult[i]} = {int(d)*mult[i]}")
soma = sum(int(d)*mult[i] for i, d in enumerate(mat))
print(f"  Soma: {soma}")
print(f"  {soma} % 11 = {soma % 11}")
print(f"  DV: {11 - (soma % 11)}")
