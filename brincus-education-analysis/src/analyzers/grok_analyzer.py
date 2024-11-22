import os
import json
import time
from typing import Dict
import requests
import pandas as pd
from tqdm import tqdm
from src.utils.helpers import clean_json_response
from src.config.settings import SYSTEM_PROMPT, OUTPUT_DIR
from unidecode import unidecode
import csv


class GrokEducationAnalyzer:
    def __init__(self):
        self.api_key = "xai-CpKouLyTQxr5NvuvFANHNhBMFFSh86QD6XOQzZdp3pQopI4xHuhirmel3nGP8UxdfKAcMwuLegZip6IS"
        self.batch_size = int(os.getenv('BATCH_SIZE', '3'))
        self.url = "https://api.x.ai/v1/chat/completions"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    def _clean_json_field(self, field: str) -> str:
        """Limpia campos JSON en formato Quill"""
        try:
            if isinstance(field, str) and 'ops' in field:
                data = json.loads(field)
                if isinstance(data, dict) and 'ops' in data:
                    return ''.join(op.get('insert', '') for op in data['ops']).strip()
            return field
        except:
            return field

    def _clean_response(self, content: str) -> str:
        """Limpia la respuesta de Grok eliminando marcadores de código"""
         # Eliminar marcadores de código markdown
        content = content.replace('```json', '').replace('```', '')
        # Limpiar espacios extra al inicio y final
        content = content.strip()
        return content

    def analyze_justification(self, row: pd.Series) -> Dict:
        try:
            # Limpiar campos JSON
            pregunta = self._clean_json_field(row['pregunta'])
            alt_a = self._clean_json_field(row['alt_a'])
            alt_b = self._clean_json_field(row['alt_b'])
            alt_c = self._clean_json_field(row['alt_c'])
            alt_d = self._clean_json_field(row['alt_d'])
            alt_e = self._clean_json_field(row['alt_e'])
            justificacion = self._clean_json_field(row['justificacion'])

            # Construir el prompt del usuario
            user_prompt = f"""
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

IMPORTANTE: Responde usando exactamente el formato JSON especificado."""

            payload = {
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                "model": "grok-beta",
                "stream": False,
                "temperature": 0.3  # Bajamos la temperatura para respuestas más consistentes
            }

            response = requests.post(
                self.url,
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 200:
                content = response.json()['choices'][0]['message']['content']
                # Limpiar la respuesta
                cleaned_content = self._clean_response(content)
                
                print(f"\nRespuesta limpia de Grok para ID {row['id']}:")
                print(cleaned_content)
                print("-" * 50)
                
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
                        'analisis_grok': cleaned_content
                    }
                except json.JSONDecodeError as e:
                    print(f"Error decodificando JSON para ID {row['id']}: {str(e)}")
                    print("Contenido problemático:", cleaned_content)
                    return None
            else:
                print(f"Error API: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error procesando ID {row['id']}: {str(e)}")
            return None
    def _format_for_excel(self, original_row: pd.Series, improved_content: dict) -> dict:
        """Formatea el contenido mejorado al formato JSON del Excel original"""
        if 'E' not in improved_content['alternativas']:
            improved_content['alternativas']['E'] = "No hay alternativa E"

        def format_json_text(text):
            # Asegurarse de que el texto esté en la codificación correcta
            text = text.encode('utf-8').decode('utf-8')
            return {
                "ops": [{"insert": f"{text}\n"}]
            }

        return {
            'id': original_row['id'],
            'id_video': original_row['id_video'],
            'pregunta': json.dumps(format_json_text(improved_content['pregunta_mejorada']), 
                                 ensure_ascii=False),
            'alt_a': json.dumps(format_json_text(improved_content['alternativas']['A']), 
                              ensure_ascii=False),
            'alt_b': json.dumps(format_json_text(improved_content['alternativas']['B']), 
                              ensure_ascii=False),
            'alt_c': json.dumps(format_json_text(improved_content['alternativas']['C']), 
                              ensure_ascii=False),
            'alt_d': json.dumps(format_json_text(improved_content['alternativas']['D']), 
                              ensure_ascii=False),
            'alt_e': json.dumps(format_json_text(improved_content['alternativas']['E']), 
                              ensure_ascii=False),
            'correcta': improved_content['respuesta_correcta'],
            'justificacion': json.dumps(format_json_text(improved_content['justificacion_mejorada']), 
                                      ensure_ascii=False),
            'curso': original_row['curso'].encode('utf-8').decode('utf-8'),
            'asignatura': original_row['asignatura'],
            'seccion': original_row['seccion'],
            'nombrevideo': original_row['nombrevideo']
        }
    
    def process_batch(self, df: pd.DataFrame, batch_size: int = 50) -> tuple[pd.DataFrame, pd.DataFrame]:
        df_7mo = df[df['curso'] == '7° Básico'].copy()
        total_preguntas = len(df_7mo)
        all_excel_results = []
        analysis_results = []
        
        print(f"Total de preguntas de 7° Básico: {total_preguntas}")
        
        # Cargar resultados previos si existen
        output_file = os.path.join(OUTPUT_DIR, 'preguntas_mejoradas_7mo_acumulado.csv')
        if os.path.exists(output_file):
            existing_results = pd.read_csv(output_file, sep=';', encoding='utf-8')
            processed_ids = set(existing_results['id'])
            all_excel_results = existing_results.to_dict('records')
            print(f"Cargadas {len(all_excel_results)} preguntas procesadas previamente")
        else:
            processed_ids = set()

        # Filtrar preguntas no procesadas
        df_7mo = df_7mo[~df_7mo['id'].isin(processed_ids)]
        
        for start_idx in range(0, len(df_7mo), batch_size):
            end_idx = min(start_idx + batch_size, len(df_7mo))
            batch_df = df_7mo.iloc[start_idx:end_idx]
            
            with tqdm(total=len(batch_df), desc=f"Procesando lote {start_idx//batch_size + 1}") as pbar:
                for _, row in batch_df.iterrows():
                    result = self.analyze_justification(row)
                    if result:
                        analysis_results.append(result)
                        try:
                            json_content = json.loads(result['analisis_grok'])
                            json_content = self._preserve_correct_answer(json_content, row['correcta'])
                            excel_row = self._format_for_excel(row, json_content)
                            all_excel_results.append(excel_row)
                        except Exception as e:
                            print(f"Error formateando para Excel ID {row['id']}: {str(e)}")
                    time.sleep(2)
                    pbar.update(1)
            
            # Guardar progreso acumulado
            pd.DataFrame(all_excel_results).to_csv(
                output_file,
                index=False, 
                sep=';',
                encoding='utf-8',
                quoting=csv.QUOTE_ALL
            )
            print(f"Guardadas {len(all_excel_results)} preguntas acumuladas")
        
        return pd.DataFrame(analysis_results[-20:]), pd.DataFrame(all_excel_results)

    def _preserve_correct_answer(self, content: dict, original_correct: str) -> dict:
        """Asegura que la respuesta correcta mantiene la misma letra que la original"""
        if content['respuesta_correcta'] != original_correct:
            # Obtener alternativa correcta actual
            correct_text = content['alternativas'][content['respuesta_correcta']]
            # Obtener alternativa en la posición original
            target_text = content['alternativas'][original_correct]
            # Intercambiar alternativas
            content['alternativas'][content['respuesta_correcta']] = target_text
            content['alternativas'][original_correct] = correct_text
            # Actualizar letra correcta
            content['respuesta_correcta'] = original_correct
        return content