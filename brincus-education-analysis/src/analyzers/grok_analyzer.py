import os
import json
import time
from typing import Dict
from openai import OpenAI
import pandas as pd
from tqdm import tqdm
from src.utils.helpers import clean_json_response
from src.config.settings import SYSTEM_PROMPT, OUTPUT_DIR
from unidecode import unidecode
import csv

class GPTEducationAnalyzer:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.batch_size = int(os.getenv('BATCH_SIZE', '5'))
        self.model = "gpt-4o-mini"

    def _clean_json_field(self, field: str) -> str:
        try:
            if isinstance(field, str) and 'ops' in field:
                data = json.loads(field)
                if isinstance(data, dict) and 'ops' in data:
                    return ''.join(op.get('insert', '') for op in data['ops']).strip()
            return field
        except:
            return field if isinstance(field, str) else str(field)
        
    def _clean_response(self, content: str) -> str:
        """Limpia la respuesta de Grok eliminando marcadores de código"""
         # Eliminar marcadores de código markdown
        content = content.replace('```json', '').replace('```', '')
        # Limpiar espacios extra al inicio y final
        content = content.strip()
        return content
        
    def analyze_justification(self, row: pd.Series) -> Dict:
        try:
            pregunta = self._clean_json_field(row['pregunta'])
            alt_a = self._clean_json_field(row['alt_a'])
            alt_b = self._clean_json_field(row['alt_b'])
            alt_c = self._clean_json_field(row['alt_c'])
            alt_d = self._clean_json_field(row['alt_d'])
            alt_e = self._clean_json_field(row['alt_e'])
            justificacion = self._clean_json_field(row['justificacion'])

            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"""
    Para un estudiante de {row['curso']}, mejora esta pregunta manteniendo su esencia pero haciéndola más clara y pedagógica:

    PREGUNTA ORIGINAL: {pregunta}
    ALTERNATIVAS ORIGINALES:
    A) {alt_a}
    B) {alt_b}
    C) {alt_c}
    D) {alt_d}
    E) {alt_e}
    RESPUESTA CORRECTA: {row['correcta']}
    JUSTIFICACIÓN ORIGINAL: {justificacion}

    IMPORTANTE: Responde usando exactamente el formato JSON especificado."""}
            ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3
            )
            
            # Calcular costo para GPT-4 Mini ($0.15 por 1M tokens)
            total_tokens = response.usage.total_tokens
            costo = (total_tokens * 0.15) / 1_000_000  # $0.15 por millón de tokens
            
            # Imprimir información de tokens
            print(f"\n=== Información de Tokens para pregunta ID {row['id']} ===")
            print(f"Tokens de entrada: {response.usage.prompt_tokens}")
            print(f"Tokens de salida: {response.usage.completion_tokens}")
            print(f"Total tokens: {total_tokens}")
            print(f"Costo aprox.: ${costo:.6f} USD")
            print("-" * 50)
            
            content = response.choices[0].message.content
            cleaned_content = self._clean_response(content)
            
            try:
                json_content = json.loads(cleaned_content)
                return {
                    'id': row['id'],
                    'curso': row['curso'],
                    'pregunta_original': pregunta,
                    'alternativas_original': {
                        'A': alt_a,
                        'B': alt_b,
                        'C': alt_c,
                        'D': alt_d,
                        'E': alt_e
                    },
                    'correcta': row['correcta'],
                    'justificacion_original': justificacion,
                    'analisis_gpt': cleaned_content
                }
            except json.JSONDecodeError as e:
                print(f"Error decodificando JSON para ID {row['id']}: {str(e)}")
                print("Contenido problemático:", cleaned_content)
                return None
                
        except Exception as e:
            print(f"Error procesando ID {row['id']}: {str(e)}")
            return None


    def _format_for_excel(self, original_row: pd.Series, improved_content: dict) -> dict:
        """Formatea el contenido para Excel, manteniendo el formato JSON correcto para fórmulas."""
        def format_json_text(text):
            # Separar el texto en partes: texto normal y fórmulas
            parts = []
            # Si hay una fórmula matemática (contenido entre $...$)
            if '$' in text:
                # Dividir el texto en partes
                text_parts = text.split('$')
                for i, part in enumerate(text_parts):
                    if i % 2 == 0:  # Texto normal
                        if part.strip():
                            parts.append({"insert": part})
                    else:  # Fórmula matemática
                        if part.strip():
                            parts.append({
                                "insert": {
                                    "formula": part.strip().replace('\\frac', '\\dfrac')
                                }
                            })
            else:
                # Si no hay fórmulas, solo texto normal
                parts.append({"insert": text})
            
            # Agregar el salto de línea al final
            parts.append({"insert": "\n"})
            
            return {"ops": parts}

        if 'E' not in improved_content['alternativas']:
            improved_content['alternativas']['E'] = "No hay alternativa E"

        return {
            'id': original_row['id'],
            'id_video': original_row['id_video'],
            'pregunta': json.dumps(format_json_text(improved_content['pregunta_mejorada']), ensure_ascii=False),
            'alt_a': json.dumps(format_json_text(improved_content['alternativas']['A']), ensure_ascii=False),
            'alt_b': json.dumps(format_json_text(improved_content['alternativas']['B']), ensure_ascii=False),
            'alt_c': json.dumps(format_json_text(improved_content['alternativas']['C']), ensure_ascii=False),
            'alt_d': json.dumps(format_json_text(improved_content['alternativas']['D']), ensure_ascii=False),
            'alt_e': json.dumps(format_json_text(improved_content['alternativas']['E']), ensure_ascii=False),
            'correcta': improved_content['respuesta_correcta'],
            'justificacion': json.dumps(format_json_text(improved_content['justificacion_mejorada']), ensure_ascii=False),
            'curso': original_row['curso'].encode('utf-8').decode('utf-8'),
            'asignatura': original_row['asignatura'],
            'seccion': original_row['seccion'],
            'nombrevideo': original_row['nombrevideo']
        }

    def process_batch(self, df: pd.DataFrame, batch_size: int = 50) -> tuple[pd.DataFrame, pd.DataFrame]:
        # Filtrar por 7° Básico y matemáticas, tomar las primeras 25
        df_filtered = df[
            (df['curso'] == 'III Medio') & 
            (df['asignatura'].str.lower().str.contains('matemática|matematica'))
        ].head(10).copy()
        
        total_preguntas = len(df_filtered)
        all_excel_results = []
        analysis_results = []
        
        print(f"Total de preguntas de Matemáticas 7° Básico a procesar: {total_preguntas}")
        
        output_file = os.path.join(OUTPUT_DIR, 'preguntas_mejoradas_7mo_matematicas.csv')
        processed_ids = set()

        # Solo intentamos leer resultados previos si el archivo existe y tiene contenido
        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            try:
                existing_results = pd.read_csv(output_file, sep=';', encoding='utf-8')
                processed_ids = set(existing_results['id'])
                all_excel_results = existing_results.to_dict('records')
                print(f"Cargadas {len(all_excel_results)} preguntas procesadas previamente")
            except Exception as e:
                print(f"Advertencia: No se pudieron cargar resultados previos: {str(e)}")
                all_excel_results = []
                processed_ids = set()

        # Filtrar preguntas no procesadas
        df_filtered = df_filtered[~df_filtered['id'].isin(processed_ids)]
        print(f"Preguntas nuevas a procesar: {len(df_filtered)}")
        
        for start_idx in range(0, len(df_filtered), batch_size):
            end_idx = min(start_idx + batch_size, len(df_filtered))
            batch_df = df_filtered.iloc[start_idx:end_idx]
            
            with tqdm(total=len(batch_df), desc=f"Procesando lote {start_idx//batch_size + 1}") as pbar:
                for _, row in batch_df.iterrows():
                    result = self.analyze_justification(row)
                    if result:
                        analysis_results.append(result)
                        try:
                            json_content = json.loads(result['analisis_gpt'])
                            json_content = self._preserve_correct_answer(json_content, row['correcta'])
                            excel_row = self._format_for_excel(row, json_content)
                            all_excel_results.append(excel_row)
                        except Exception as e:
                            print(f"Error formateando para Excel ID {row['id']}: {str(e)}")
                    time.sleep(2)
                    pbar.update(1)
            
            # Guardar resultados parciales después de cada lote
            if all_excel_results:
                pd.DataFrame(all_excel_results).to_csv(
                    output_file,
                    index=False, 
                    sep=';',
                    encoding='utf-8',
                    quoting=csv.QUOTE_ALL
                )
                print(f"Guardadas {len(all_excel_results)} preguntas acumuladas")
        
        return pd.DataFrame(analysis_results), pd.DataFrame(all_excel_results)
    
    def _preserve_correct_answer(self, content: dict, original_correct: str) -> dict:
        if content['respuesta_correcta'] != original_correct:
            correct_text = content['alternativas'][content['respuesta_correcta']]
            target_text = content['alternativas'][original_correct]
            content['alternativas'][content['respuesta_correcta']] = target_text
            content['alternativas'][original_correct] = correct_text
            content['respuesta_correcta'] = original_correct
        return content