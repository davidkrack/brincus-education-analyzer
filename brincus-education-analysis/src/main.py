import os
import pandas as pd
import numpy as np
import csv
from src.analyzers.grok_analyzer import GrokEducationAnalyzer
from src.analyzers.pdf_generator import PDFGenerator
from src.utils.data_cleaner import DataCleaner
from src.config.settings import OUTPUT_DIR, DATA_DIR
from dotenv import load_dotenv

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
        
        # Guardar resultados de análisis y generar PDF (solo últimas 20 preguntas)
        if not analysis_results.empty:
            analysis_results.to_csv(os.path.join(OUTPUT_DIR, 'grok_education_analysis.csv'), 
                                 index=False)
            
            pdf_generator = PDFGenerator()
            pdf_generator.generate_report(analysis_results, 
                                       os.path.join(OUTPUT_DIR, 'analisis_educativo.pdf'))
        
        # Guardar resultados acumulados
        if not excel_results.empty:
            # Guardar en CSV acumulativo
            output_path = os.path.join(OUTPUT_DIR, 'preguntas_mejoradas_7mo_acumulado.csv')
            excel_results.to_csv(output_path, 
                               index=False, 
                               sep=';',
                               encoding='utf-8',
                               quoting=csv.QUOTE_ALL)
            
            # También guardar en Excel para verificación
            excel_path = os.path.join(OUTPUT_DIR, 'preguntas_mejoradas_7mo_acumulado.xlsx')
            excel_results.to_excel(excel_path, 
                                 index=False, 
                                 engine='openpyxl')
        
        print("\nAnálisis completado. Archivos generados:")
        print(f"- CSV análisis (últimas 20 preguntas): {os.path.join(OUTPUT_DIR, 'grok_education_analysis.csv')}")
        print(f"- CSV acumulado 7° Básico: {os.path.join(OUTPUT_DIR, 'preguntas_mejoradas_7mo_acumulado.csv')}")
        print(f"- Excel acumulado 7° Básico: {os.path.join(OUTPUT_DIR, 'preguntas_mejoradas_7mo_acumulado.xlsx')}")
        print(f"- PDF reporte (muestra): {os.path.join(OUTPUT_DIR, 'analisis_educativo.pdf')}")
        print(f"\nTotal de preguntas procesadas: {len(excel_results)}")
        
    except Exception as e:
        print(f"Error en el proceso: {str(e)}")
        raise e

if __name__ == "__main__":
    main()