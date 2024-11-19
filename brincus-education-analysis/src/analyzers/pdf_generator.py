
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF
import json
import os

class PDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
        self.logo_path = os.path.join('templates', 'logo_home.svg')

    def _create_custom_styles(self):
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2c3e50'),
            spaceBefore=15,
            spaceAfter=10,
            bold=True
        ))
        
        self.styles.add(ParagraphStyle(
            name='Content',
            parent=self.styles['Normal'],
            fontSize=11,
            leading=14,
            spaceAfter=8
        ))
    def _clean_formula(self, text):
        """Limpia fórmulas matemáticas del formato JSON"""
        if isinstance(text, str):
            if '"ops"' in text and '"formula"' in text:
                try:
                    data = json.loads(text)
                    formula = data['ops'][0]['insert'].get('formula', '')
                    return formula or text
                except:
                    pass
        return text
    def _format_question_block(self, pregunta, alternativas, respuesta, justificacion):
        """Formatea un bloque de pregunta con formato estandarizado y alternativas verticales"""
        # Limpiar la pregunta
        pregunta = self._clean_formula(pregunta)
        
        # Construir el bloque con formato específico y alternativas verticales
        texto = pregunta.strip() + "<br/><br/>"  # Doble salto de línea después de la pregunta
        
        # Formatear alternativas con alineación vertical
        for letra, alt in [('a', 'A'), ('b', 'B'), ('c', 'C'), ('d', 'D'), ('e', 'E')]:
            if alt in alternativas:
                alt_text = self._clean_formula(alternativas[alt])
                texto += f"{letra}){alt_text.strip()}<br/>"  # Salto de línea después de cada alternativa
        
        texto += "<br/>"  # Línea en blanco antes de la respuesta
        texto += f"Respuesta: {respuesta}<br/>"
        
        # Limpiar justificación
        justificacion = justificacion.replace('&La', 'La')
        justificacion = justificacion.replace('||', '')
        justificacion = justificacion.strip()
        texto += f"Justificación: {justificacion}"
        
        return texto


    def create_comparison_section(self, content: dict) -> list:
        elements = []
        
        # Título del curso
        elements.append(Paragraph(f"Curso: {content['curso']}", self.styles['SectionTitle']))
        elements.append(Spacer(1, 12))
        
        try:
            # Pregunta Original
            elements.append(Paragraph("Pregunta Original:", self.styles['SectionTitle']))
            original_text = self._format_question_block(
                content['pregunta_original'],
                content['alternativas_original'],
                content.get('correcta', ''),
                content['justificacion_original']
            )
            elements.append(Paragraph(original_text, self.styles['Content']))
            elements.append(Spacer(1, 20))
            
            # Pregunta Mejorada
            analysis = self._clean_json_string(content['analisis_grok'])
            if analysis:
                elements.append(Paragraph("Pregunta Mejorada:", self.styles['SectionTitle']))
                improved_text = self._format_question_block(
                    analysis['pregunta_mejorada'],
                    analysis['alternativas'],
                    analysis['respuesta_correcta'],
                    analysis['justificacion_mejorada']
                )
                elements.append(Paragraph(improved_text, self.styles['Content']))
                
                if analysis.get('ejemplos'):
                    elements.append(Paragraph("Ejemplos Relevantes:", self.styles['SectionTitle']))
                    for i, ejemplo in enumerate(analysis['ejemplos'], 1):
                        elements.append(Paragraph(f"{i}. {ejemplo}", self.styles['Content']))
        
        except Exception as e:
            print(f"Error procesando pregunta: {str(e)}")
        
        elements.append(Spacer(1, 30))
        return elements

    def _clean_json_string(self, json_str):
        """Limpia el string JSON de caracteres no deseados"""
        if isinstance(json_str, str):
            json_str = json_str.replace('```json\n', '').replace('\n```', '').strip()
            try:
                return json.loads(json_str)
            except:
                return None
        return json_str

    def generate_report(self, results_df, output_path: str):
        class HeaderCanvas:
            def __init__(self, pdf_generator):
                self.pdf_generator = pdf_generator

            def on_page(self, canvas, doc):
                # Dibujar el logo en el encabezado
                if os.path.exists(self.pdf_generator.logo_path):
                    canvas.saveState()
                    # Convertir SVG a objeto ReportLab Graphics
                    drawing = svg2rlg(self.pdf_generator.logo_path)
                    
                    # Calcular escala
                    original_width = drawing.width
                    desired_width = 2*inch
                    scale_factor = desired_width / original_width
                    
                    # Escalar el dibujo SVG
                    drawing.scale(scale_factor, scale_factor)
                    
                    # Dibujar logo
                    renderPDF.draw(drawing, canvas, 
                                doc.leftMargin, 
                                doc.pagesize[1] - doc.topMargin + 1.5*inch - drawing.height)
                    canvas.restoreState()

        # Configurar documento
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72 + 0.6*inch,
            bottomMargin=72
        )

        elements = []
        elements.append(Spacer(1, 0.2*inch))
        elements.append(Paragraph("Análisis de Contenido Educativo", self.styles['CustomTitle']))
        elements.append(Spacer(1, 20))
        
        # Procesar cada pregunta
        for _, row in results_df.iterrows():
            try:
                elements.extend(self.create_comparison_section(row))
            except Exception as e:
                print(f"Error procesando pregunta: {str(e)}")
        
        # Construir PDF
        doc.build(elements, onFirstPage=HeaderCanvas(self).on_page, 
                           onLaterPages=HeaderCanvas(self).on_page)