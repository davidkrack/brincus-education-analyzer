import os
import pandas as pd
import numpy as np
import csv
from src.analyzers.grok_analyzer import GrokEducationAnalyzer
from src.analyzers.pdf_generator import PDFGenerator
from src.utils.data_cleaner import DataCleaner
from src.config.settings import OUTPUT_DIR, DATA_DIR
from dotenv import load_dotenv

def select_diverse_sample(df: pd.DataFrame, total_samples: int = 3, math_samples: int = 2) -> pd.DataFrame:
    """
    Selecciona una muestra diversa de preguntas asegurando un mínimo de preguntas de matemáticas
    """
    # Filtrar preguntas de matemáticas
    math_questions = df[df['asignatura'].str.lower().isin(['matemática', 'matematicas', 'matemáticas'])]
    
    # Filtrar preguntas de otras asignaturas
    other_questions = df[~df['asignatura'].str.lower().isin(['matemática', 'matematicas', 'matemáticas'])]
    
    # Seleccionar muestras
    selected_math = math_questions.sample(n=min(math_samples, len(math_questions)), random_state=42)
    selected_others = other_questions.sample(n=min(total_samples - math_samples, len(other_questions)), random_state=42)
    
    # Combinar las muestras
    combined_sample = pd.concat([selected_math, selected_others])
    
    print("\nDistribución de la muestra:")
    print(combined_sample['asignatura'].value_counts())
    
    return combined_sample

def main():
    # Cargar variables de entorno
    load_dotenv()
    
    # Crear directorios si no existen
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    
    try:
        # Cargar datos
        data_path = os.path.join(DATA_DIR, 'Preguntas_ruta_aprendizaje.csv')
        df = pd.read_csv(data_path, sep=';', encoding='utf-8')
        
        # Procesar preguntas
        analyzer = GrokEducationAnalyzer()
        analysis_results, excel_results = analyzer.process_batch(df)
        
        # Guardar resultados de análisis
        if not analysis_results.empty:
            analysis_results.to_csv(os.path.join(OUTPUT_DIR, 'grok_education_analysis.csv'), 
                                 index=False)
            
            # Generar PDF
            pdf_generator = PDFGenerator()
            pdf_generator.generate_report(analysis_results, 
                                       os.path.join(OUTPUT_DIR, 'analisis_educativo.pdf'))
        
        # Guardar resultados en formato Excel
        if not excel_results.empty:
            # Guardar en CSV con la codificación correcta
            output_path = os.path.join(OUTPUT_DIR, 'preguntas_mejoradas.csv')
            excel_results.to_csv(output_path, 
                               index=False, 
                               sep=';',
                               encoding='utf-8',
                               quoting=csv.QUOTE_ALL)  # Esto asegura que los JSON se guarden correctamente
            
            # También guardar en Excel para verificar
            excel_path = os.path.join(OUTPUT_DIR, 'preguntas_mejoradas.xlsx')
            excel_results.to_excel(excel_path, 
                                 index=False, 
                                 engine='openpyxl')
        
        print("\nAnálisis completado. Archivos generados:")
        print(f"- CSV análisis: {os.path.join(OUTPUT_DIR, 'grok_education_analysis.csv')}")
        print(f"- Excel formato original: {os.path.join(OUTPUT_DIR, 'preguntas_mejoradas.csv')}")
        print(f"- PDF reporte: {os.path.join(OUTPUT_DIR, 'analisis_educativo.pdf')}")
        
    except Exception as e:
        print(f"Error en el proceso: {str(e)}")
        raise e  # Para ver el traceback completo

if __name__ == "__main__":
    main()