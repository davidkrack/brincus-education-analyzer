import os
from datetime import datetime
from typing import Dict, List
import json
import re
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER

class PDFReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
        self.logo_path = os.path.join('templates', 'logo_home.png')
        
    def _create_custom_styles(self):
        """Crea estilos personalizados para el documento"""
        # Estilo para títulos
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        # Estilo para subtítulos
        self.styles.add(ParagraphStyle(
            name='SubTitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2c3e50'),
            spaceBefore=20,
            spaceAfter=10
        ))
        
        # Estilo para texto normal mejorado
        self.styles.add(ParagraphStyle(
            name='CustomNormal',
            parent=self.styles['Normal'],
            fontSize=12,
            leading=16,
            spaceBefore=6,
            spaceAfter=6
        ))
        
        # Estilo para texto en negrita
        self.styles.add(ParagraphStyle(
            name='Bold',
            parent=self.styles['Normal'],
            fontSize=12,
            leading=16,
            bold=True
        ))

    def _format_text(self, text: str) -> str:
        """Formatea el texto para manejar negritas y símbolos especiales"""
        # Reemplazar ** con etiquetas de negrita
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        
        # Reemplazar símbolos matemáticos
        text = text.replace('×', 'x')  # Multiplicación
        text = text.replace('²', '<sup>2</sup>')  # Exponente 2
        
        return text

    def generate_report(self, results_df, output_path: str):
        """Genera el reporte PDF con los análisis"""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        elements = []
        
        # Agregar logo
        if os.path.exists(self.logo_path):
            img = Image(self.logo_path, width=2*inch, height=1*inch)
            elements.append(img)
            elements.append(Spacer(1, 20))

        # Título
        elements.append(Paragraph(
            "Reporte de Análisis Educativo",
            self.styles['CustomTitle']
        ))
        
        # Fecha
        elements.append(Paragraph(
            f"Generado el: {datetime.now().strftime('%d-%m-%Y %H:%M')}",
            self.styles['CustomNormal']
        ))
        elements.append(Spacer(1, 20))

        for _, row in results_df.iterrows():
            elements.extend(self._create_question_section(row))
            elements.append(Spacer(1, 30))

        # Construir PDF
        doc.build(elements)

    def _create_question_section(self, row) -> List:
        elements = []
        
        try:
            analysis = json.loads(row['analisis_grok'])
            
            # Pregunta Original
            elements.append(Paragraph(
                "Pregunta Original:",
                self.styles['SubTitle']
            ))
            elements.append(Paragraph(
                self._format_text(row['pregunta_original']),
                self.styles['CustomNormal']
            ))

            # Justificación Original
            elements.append(Paragraph(
                "Justificación Original:",
                self.styles['SubTitle']
            ))
            elements.append(Paragraph(
                self._format_text(row['justificacion_original']),
                self.styles['CustomNormal']
            ))

            # Evaluación
            elements.append(Paragraph(
                "Evaluación:",
                self.styles['SubTitle']
            ))
            
            eval_data = [[k.capitalize(), f"{v}/10"] for k, v in analysis['evaluacion'].items()]
            eval_table = Table(eval_data, colWidths=[200, 100])
            eval_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(eval_table)
            elements.append(Spacer(1, 10))

            # Justificación Mejorada
            elements.append(Paragraph(
                "Justificación Mejorada:",
                self.styles['SubTitle']
            ))
            elements.append(Paragraph(
                self._format_text(analysis['justificacion_mejorada']),
                self.styles['CustomNormal']
            ))

            # Ejemplos Relevantes
            if analysis['ejemplos_relevantes']:
                elements.append(Paragraph(
                    "Ejemplos Relevantes:",
                    self.styles['SubTitle']
                ))
                for i, ejemplo in enumerate(analysis['ejemplos_relevantes'], 1):
                    elements.append(Paragraph(
                        f"{i}. {self._format_text(ejemplo)}",
                        self.styles['CustomNormal']
                    ))

        except Exception as e:
            elements.append(Paragraph(
                f"Error al procesar análisis: {str(e)}",
                self.styles['CustomNormal']
            ))

        return elements