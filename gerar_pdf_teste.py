#!/usr/bin/env python
"""
Script para gerar PDF de exemplo para teste do OCR
Cria um contrato com todos os campos que o sistema OCR consegue extrair
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from datetime import datetime
from pathlib import Path

def gerar_pdf_contrato_teste(numero_contrato="0000001", output_filename="contrato_teste.pdf"):
    """
    Gera um PDF de exemplo de contrato para teste do OCR
    """
    
    # Caminho para salvar
    output_path = Path(__file__).parent / output_filename
    
    # Criar documento
    doc = SimpleDocTemplate(str(output_path), pagesize=A4)
    story = []
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1e3c72'),
        spaceAfter=20,
        alignment=1,  # Center
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#2a5298'),
        spaceAfter=10,
        spaceBefore=10,
    )
    
    normal_style = styles['Normal']
    
    # Título
    story.append(Paragraph("CONTRATO DE FINANCIAMENTO IMOBILIÁRIO", title_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Dados do contrato
    data_hoje = datetime.now().strftime("%d/%m/%Y")
    
    dados_contrato = [
        ["Número do Contrato:", f"{numero_contrato}"],
        ["Data de Assinatura:", "21/04/2026"],
        ["Data de Processamento:", data_hoje],
        ["", ""],
        ["Conjunto Habitacional:", "BLOCO A - CONDOMÍNIO FLORES"],
        ["Localização:", "Brasília - DF"],
        ["", ""],
        ["Prazo Total:", "120 meses"],
        ["Sistema de Amortização:", "SAC (Sistema de Amortização Constante)"],
        ["Taxa de Juros:", "0,50% ao mês"],
        ["", ""],
        ["Valor do Imóvel:", "R$ 150.000,00"],
        ["Entrada/Sinal:", "R$ 30.000,00"],
        ["Valor Financiado:", "R$ 120.000,00"],
    ]
    
    # Criar tabela com dados
    table = Table(dados_contrato, colWidths=[2.5*inch, 3.5*inch])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
    ]))
    
    story.append(table)
    story.append(Spacer(1, 0.3*inch))
    
    # Dados do mutuário
    story.append(Paragraph("DADOS DO MUTUÁRIO", heading_style))
    
    mutuario_data = [
        ["Nome Completo:", "João Silva Santos"],
        ["CPF:", "123.456.789-00"],
        ["Estado Civil:", "Casado"],
        ["Data de Nascimento:", "15/05/1980"],
        ["", ""],
        ["Endereço:", "Rua das Flores, nº 100"],
        ["Complemento:", "Apto 501"],
        ["Bairro:", "Asa Sul"],
        ["Cidade:", "Brasília"],
        ["Estado:", "DF"],
        ["CEP:", "70000-000"],
        ["", ""],
        ["Email:", "joao.silva@email.com"],
        ["Telefone:", "(61) 99999-9999"],
    ]
    
    table2 = Table(mutuario_data, colWidths=[2.5*inch, 3.5*inch])
    table2.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
    ]))
    
    story.append(table2)
    story.append(Spacer(1, 0.3*inch))
    
    # Condições gerais
    story.append(Paragraph("CONDIÇÕES GERAIS DO FINANCIAMENTO", heading_style))
    
    texto_condicoes = """
    Este contrato vincula as partes às seguintes condições:
    <br/><br/>
    1. O prazo de amortização é de 120 (cento e vinte) meses, contados a partir da data da primeira parcela.
    <br/><br/>
    2. A taxa de juros aplicada é de 0,50% (zero vírgula cinquenta por cento) ao mês, sobre o saldo devedor.
    <br/><br/>
    3. O sistema de amortização utilizado é o SAC (Sistema de Amortização Constante), onde as parcelas 
    são decrescentes ao longo do período.
    <br/><br/>
    4. O mutuário se obriga ao pagamento das parcelas mensais nos prazos estipulados.
    <br/><br/>
    5. Em caso de atraso, incidirão multa de 2% e juros de mora de 1% ao mês.
    """
    
    story.append(Paragraph(texto_condicoes, normal_style))
    story.append(Spacer(1, 0.4*inch))
    
    # Assinaturas
    story.append(Paragraph("ASSINATURAS", heading_style))
    story.append(Spacer(1, 0.5*inch))
    
    assinatura_data = [
        ["___________________________", "___________________________"],
        ["Mutuário", "Instituição Financeira"],
        ["João Silva Santos", ""],
        ["", ""],
    ]
    
    table3 = Table(assinatura_data, colWidths=[3*inch, 3*inch])
    table3.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    
    story.append(table3)
    
    # Rodapé
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph(
        f"Documento gerado em {data_hoje} | Sistema de Gestão de Financiamentos",
        ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=1,
        )
    ))
    
    # Gerar PDF
    try:
        doc.build(story)
        print(f"✅ PDF gerado com sucesso: {output_path}")
        print(f"   Contrato número: {numero_contrato}")
        return str(output_path)
    except Exception as e:
        print(f"❌ Erro ao gerar PDF: {str(e)}")
        return None

if __name__ == '__main__':
    import sys
    
    numero = sys.argv[1] if len(sys.argv) > 1 else "0000001"
    gerar_pdf_contrato_teste(numero_contrato=numero)
