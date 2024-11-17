import os
import pandas as pd
import numpy as np
from src.analyzers.grok_analyzer import GrokEducationAnalyzer
from src.analyzers.pdf_generator import PDFReportGenerator
from src.utils.data_cleaner import DataCleaner
from src.config.settings import OUTPUT_DIR, DATA_DIR
from dotenv import load_dotenv

def select_diverse_sample(df: pd.DataFrame, total_samples: int = 10, math_samples: int = 3) -> pd.DataFrame:
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
        # Cargar datos originales
        data_path = os.path.join(DATA_DIR, 'Preguntas_ruta_aprendizaje.csv')
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Archivo de datos no encontrado en: {data_path}")
            
        # Cargar y limpiar datos
        df = pd.read_csv(data_path, sep=';')
        cleaner = DataCleaner()
        df_clean = cleaner.clean_dataframe(df)
        
        # Seleccionar muestra diversa (10 preguntas, al menos 3 de matemáticas)
        sample_df = select_diverse_sample(df_clean, total_samples=10, math_samples=3)
        
        # Crear instancias
        analyzer = GrokEducationAnalyzer()
        pdf_generator = PDFReportGenerator()
        
        # Procesar batch de preguntas
        results = analyzer.process_batch(sample_df)
        
        # Guardar resultados CSV
        csv_path = os.path.join(OUTPUT_DIR, 'grok_education_analysis.csv')
        results.to_csv(csv_path, index=False)
        
        # Generar PDF
        pdf_path = os.path.join(OUTPUT_DIR, 'analisis_educativo.pdf')
        pdf_generator.generate_report(results, pdf_path)
        
        print(f"\nAnálisis completado. Resultados guardados en:")
        print(f"- CSV análisis: {csv_path}")
        print(f"- PDF reporte: {pdf_path}")
        
    except Exception as e:
        print(f"Error en el proceso: {str(e)}")
        raise

if __name__ == "__main__":
    main()