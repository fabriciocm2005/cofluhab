"""
Aplica estratégia ABS: converte saldos negativos para positivos
"""
import django
import os
import sys

sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')
django.setup()

from django.db import connection, transaction

print("=" * 100)
print("APLICANDO ESTRATEGIA ABS - CONVERTER NEGATIVOS PARA POSITIVOS")
print("=" * 100)

with connection.cursor() as cursor:
    # Contar contratos antes
    cursor.execute("""
        SELECT COUNT(DISTINCT c.id)
        FROM principal_contrato c
        INNER JOIN principal_parcelacontrato p ON p.contrato_id = c.id
        WHERE p.id IN (SELECT MAX(id) FROM principal_parcelacontrato GROUP BY contrato_id)
        AND p.sddev < 0
    """)
    total_antes = cursor.fetchone()[0]
    
    # Somar total negativo antes
    cursor.execute("""
        SELECT SUM(p.sddev)
        FROM principal_contrato c
        INNER JOIN principal_parcelacontrato p ON p.contrato_id = c.id
        WHERE p.id IN (SELECT MAX(id) FROM principal_parcelacontrato GROUP BY contrato_id)
        AND p.sddev < 0
    """)
    soma_antes = cursor.fetchone()[0] or 0
    
    print(f"\nContratos com saldo negativo: {total_antes}")
    print(f"Total negativo: R$ {float(soma_antes):,.2f}")
    print("\nAplicando ABS (valor absoluto)...")
    
    with transaction.atomic():
        # Atualizar saldos negativos para positivos
        cursor.execute("""
            UPDATE principal_parcelacontrato
            SET sddev = ABS(sddev)
            WHERE sddev < 0
        """)
        
        linhas_atualizadas = cursor.rowcount
        print(f"\n✅ {linhas_atualizadas} parcelas atualizadas")
    
    # Verificar resultado
    cursor.execute("""
        SELECT COUNT(DISTINCT c.id)
        FROM principal_contrato c
        INNER JOIN principal_parcelacontrato p ON p.contrato_id = c.id
        WHERE p.id IN (SELECT MAX(id) FROM principal_parcelacontrato GROUP BY contrato_id)
        AND p.sddev < 0
    """)
    total_depois = cursor.fetchone()[0]
    
    # Somar total agora positivo
    cursor.execute("""
        SELECT SUM(p.sddev)
        FROM principal_contrato c
        INNER JOIN principal_parcelacontrato p ON p.contrato_id = c.id
        WHERE p.id IN (
            SELECT p2.id FROM principal_parcelacontrato p2
            INNER JOIN (
                SELECT contrato_id, codigo 
                FROM principal_contrato 
                WHERE codigo IN (
                    SELECT c2.codigo 
                    FROM principal_contrato c2
                    INNER JOIN principal_parcelacontrato p3 ON p3.contrato_id = c2.id
                    WHERE p3.id IN (SELECT MAX(id) FROM principal_parcelacontrato GROUP BY contrato_id)
                )
            ) c ON c.contrato_id = p2.contrato_id
            WHERE p2.id IN (SELECT MAX(id) FROM principal_parcelacontrato GROUP BY contrato_id)
        )
    """)
    total_positivo = cursor.fetchone()[0] or 0
    
    print(f"\nContratos com saldo negativo após correção: {total_depois}")
    print(f"Total geral de saldos: R$ {float(total_positivo):,.2f}")
    print("\n✅ CORREÇÃO CONCLUÍDA!")

print("\nExecute: py scripts\\ver_saldo_final.py para verificar resultado final")
