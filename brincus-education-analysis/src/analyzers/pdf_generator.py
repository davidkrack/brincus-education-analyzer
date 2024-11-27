import os
import json
import traceback
import subprocess
from datetime import datetime

class PDFGenerator:
    def __init__(self):
        self.logo_path = os.path.join('templates', 'logo_home.svg')
        
    def _clean_json_field(self, field):
        """Extrae el contenido de un campo JSON con formato específico."""
        try:
            if isinstance(field, str):
                # Si tiene formato JSON con ops
                if '"ops"' in field:
                    data = json.loads(field)
                    if isinstance(data, dict) and 'ops' in data:
                        content = ''
                        for op in data['ops']:
                            if isinstance(op.get('insert'), dict) and 'formula' in op['insert']:
                                content += op['insert']['formula']
                            elif isinstance(op.get('insert'), str):
                                content += op['insert']
                        return content.strip()
                # Si tiene $$ los reemplaza por un solo $
                if '$$' in field:
                    return field.replace('$$', '$')
                return field
        except:
            return field if isinstance(field, str) else str(field)

    def _format_latex_text(self, text):
        """Formatea el texto para LaTeX, manteniendo las expresiones matemáticas."""
        if not text:
            return text
            
        # Limpia el texto
        text = self._clean_json_field(text)
        
        # Reemplaza las expresiones matemáticas comunes
        replacements = {
            r'\dfrac': r'\frac',
            '&': '',
            '||': '',
            '```': '',
            '$$': '$'  # Asegura que no haya doble $
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text

    def _clean_json_string(self, json_str):
        """Limpia el string JSON de caracteres no deseados y maneja errores de escape."""
        if isinstance(json_str, str):
            try:
                # Limpia caracteres de código
                json_str = json_str.replace('```json\n', '')
                json_str.replace('\n```', '')
                json_str = json_str.strip()
                
                # Corrige problemas comunes de escape
                json_str = json_str.replace('\\\\', '\\')  # Doble escape
                json_str = json_str.replace('\\"', '"')    # Comillas escapadas
                
                # Maneja casos específicos de LaTeX
                json_str = json_str.replace('\\frac', '\\\\frac')
                json_str = json_str.replace('\\text', '\\\\text')
                json_str = json_str.replace('\\cdot', '\\\\cdot')
                json_str = json_str.replace('\\times', '\\\\times')
                
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError as e:
                    print(f"Error inicial decodificando JSON: {str(e)}")
                    print("Intentando limpiar caracteres problemáticos...")
                    
                    # Segunda pasada: limpieza más agresiva
                    json_str = json_str.encode('utf-8').decode('unicode-escape')
                    json_str = json_str.replace('\\n', ' ')
                    
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError as e:
                        print(f"Error final decodificando JSON: {str(e)}")
                        print("Contenido problemático:", json_str)
                        return None
                    
            except Exception as e:
                print(f"Error procesando JSON string: {str(e)}")
                return None
                
        return json_str

    def _format_alternative(self, alt_text: str) -> str:
        """Formatea una alternativa correctamente, manejando texto y fórmulas."""
        # Limpia el texto primero
        alt_text = self._clean_json_field(alt_text)
        
        # Remover cualquier $ o $$ existente
        alt_text = alt_text.replace('$$', '').replace('$', '').strip()
        
        # Si la alternativa es puramente texto (sin símbolos matemáticos)
        if not any(char in alt_text for char in "+-*/^_{}\\"):
            return alt_text
        
        # Normaliza fracciones
        alt_text = alt_text.replace('\\dfrac', '\\frac')
        
        # Envolver en un solo par de $
        return f"${alt_text}$"

    def generate_latex_content(self, results_df):
        """Genera el contenido LaTeX para el documento."""
        latex_content = []
        
        # Preámbulo LaTeX mejorado
        latex_content.extend([
            r'\documentclass[12pt]{article}',
            r'\usepackage[utf8]{inputenc}',
            r'\usepackage{amsmath}',
            r'\usepackage{amssymb}',
            r'\usepackage[spanish]{babel}',
            r'\usepackage{graphicx}',
            r'\usepackage[margin=1in]{geometry}',
            r'\usepackage{enumitem}',
            r'\usepackage{fancyhdr}',
            r'\usepackage{xcolor}',
            r'\usepackage{mdframed}',
            r'\usepackage{atbegshi}  % Para posicionar elementos',
            r'\pagestyle{fancy}',
            r'\fancyhead{}',
            r'\fancyhead[C]{\includegraphics[width=3cm]{templates/logo_home.svg}}',
            r'\renewcommand{\headrulewidth}{0pt}',
            r'',
            r'\AtBeginShipoutLowerLeft{%',
            r'    \raisebox{1cm}{\includegraphics[width=2.5cm]{templates/logo_home.svg}}',
            r'}',
            r'',
            r'\begin{document}',
            r'',
            r'\begin{center}',
            r'    \Large\textbf{Análisis de Contenido Educativo}',
            r'\end{center}',
            r'\vspace{0.8cm}'
        ])

        # Procesar cada pregunta
        for _, row in results_df.iterrows():
            try:
                # Título del curso
                latex_content.append(r'\section*{' + f"Curso: {row['curso']}" + r'}')
                
                # Pregunta Original
                latex_content.extend([
                    r'\subsection*{Pregunta Original}',
                    r'\begin{tabular}{p{0.9\textwidth}}',
                    r'\textbf{' + self._clean_json_field(row['pregunta_original']) + r'} \\',
                    r'\end{tabular}',
                    r'',
                    r'\begin{enumerate}[label=\alph*)]'
                ])
                
                # Alternativas originales
                for letra in ['A', 'B', 'C', 'D', 'E']:
                    if letra in row['alternativas_original']:
                        alt_text = self._format_alternative(row['alternativas_original'][letra])
                        latex_content.append(f"    \\item {alt_text}")
                
                # Respuesta y justificación original
                latex_content.extend([
                    r'\end{enumerate}',
                    r'\textbf{Respuesta:} ' + row['correcta'] + r' \\',
                    r'\textbf{Justificación:} ' + self._clean_json_field(row['justificacion_original']),
                    r'',
                    r'\vspace{0.5cm}',
                    r''
                ])
                
                # Pregunta Mejorada
                analisis = self._clean_json_string(row['analisis_gpt'])
                if analisis:
                    latex_content.extend([
                        r'\subsection*{Pregunta Mejorada}',
                        r'\begin{tabular}{p{0.9\textwidth}}',
                        r'\textbf{' + self._format_latex_text(analisis['pregunta_mejorada']) + r'} \\',
                        r'\end{tabular}',
                        r'',
                        r'\begin{enumerate}[label=\alph*)]'
                    ])
                    
                    # Alternativas mejoradas
                    for letra, alt in analisis['alternativas'].items():
                        alt_text = self._format_alternative(alt)
                        latex_content.append(f"    \\item {alt_text}")
                    
                    # Respuesta y justificación mejorada
                    latex_content.extend([
                        r'\end{enumerate}',
                        r'\textbf{Respuesta:} ' + analisis['respuesta_correcta'] + r' \\',
                        r'\textbf{Justificación:} ' + self._format_latex_text(analisis['justificacion_mejorada'])
                    ])
                    
                    # Ejemplos relevantes
                    if 'ejemplos' in analisis and analisis['ejemplos']:
                        latex_content.extend([
                            r'',
                            r'\textbf{Ejemplos Relevantes:}',
                            r'\begin{itemize}'
                        ])
                        for ejemplo in analisis['ejemplos']:
                            latex_content.append(f"    \\item {self._format_latex_text(ejemplo)}")
                        latex_content.append(r'\end{itemize}')
                
                # Nueva página después de cada pregunta
                latex_content.append(r'\newpage')
                
            except Exception as e:
                print(f"Error procesando pregunta para LaTeX: {str(e)}")
                traceback.print_exc()
        
        latex_content.append(r'\end{document}')
        return '\n'.join(latex_content)



    def generate_report(self, results_df, output_path: str):
        """Genera el PDF usando pdflatex con mejor manejo de errores y compilación."""
        try:
            # 1. Preparar directorios y rutas
            temp_dir = os.path.abspath(os.path.dirname(output_path))
            os.makedirs(temp_dir, exist_ok=True)
            
            base_name = 'temp_report'
            tex_path = os.path.join(temp_dir, f'{base_name}.tex')
            
            print(f"\n=== Iniciando generación de PDF ===")
            print(f"Directorio de trabajo: {temp_dir}")
            print(f"Archivo LaTeX: {tex_path}")
            
            # 2. Generar y guardar contenido LaTeX
            latex_content = self.generate_latex_content(results_df)
            with open(tex_path, 'w', encoding='utf-8') as f:
                f.write(latex_content)
            
            print("\n=== Archivo LaTeX generado correctamente ===")
            
            # 3. Cambiar al directorio de trabajo
            original_dir = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                # 4. Primera compilación
                print("\n=== Primera pasada de compilación ===")
                process = subprocess.run(
                    ['pdflatex', '-interaction=nonstopmode', base_name],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                # 5. Segunda compilación para referencias
                print("\n=== Segunda pasada de compilación ===")
                process = subprocess.run(
                    ['pdflatex', '-interaction=nonstopmode', base_name],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                # 6. Verificar que el PDF se generó
                pdf_path = os.path.join(temp_dir, f'{base_name}.pdf')
                if os.path.exists(pdf_path):
                    print(f"\n=== PDF generado exitosamente ===")
                    
                    # 7. Mover el PDF a la ubicación final
                    os.replace(pdf_path, output_path)
                    print(f"PDF movido a: {output_path}")
                    
                    # 8. Limpiar archivos temporales
                    extensions = ['.aux', '.log', '.out', '.toc']
                    for ext in extensions:
                        temp_file = os.path.join(temp_dir, f'{base_name}{ext}')
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                            print(f"Archivo temporal eliminado: {temp_file}")
                    
                    return True
                else:
                    raise Exception("No se encontró el archivo PDF generado")
                
            except subprocess.CalledProcessError as e:
                print("\n=== Error en la compilación de LaTeX ===")
                print("Salida de error:")
                print(e.stdout)
                print("\nError específico:")
                print(e.stderr)
                
                # Buscar errores específicos en el archivo .log
                log_path = os.path.join(temp_dir, f'{base_name}.log')
                if os.path.exists(log_path):
                    print("\nContenido relevante del archivo .log:")
                    with open(log_path, 'r', encoding='utf-8') as f:
                        log_content = f.read()
                        error_lines = [line for line in log_content.split('\n') 
                                    if '!' in line or 'Error' in line]
                        print('\n'.join(error_lines))
                
                raise Exception("Error en la compilación de LaTeX")
                
            except Exception as e:
                print(f"\n=== Error inesperado: {str(e)} ===")
                raise e
                
            finally:
                # Volver al directorio original
                os.chdir(original_dir)
                
        except Exception as e:
            print(f"\nError generando PDF: {str(e)}")
            traceback.print_exc()
            return False

        finally:
            # Guardar el archivo .tex incluso si hay error
            if os.path.exists(tex_path):
                backup_path = os.path.join(temp_dir, f'backup_{base_name}.tex')
                try:
                    os.replace(tex_path, backup_path)
                    print(f"\nArchivo LaTeX guardado como backup: {backup_path}")
                except:
                    pass