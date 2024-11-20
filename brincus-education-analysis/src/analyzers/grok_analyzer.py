import os
import json
import time
from typing import Dict
import requests
import pandas as pd
from tqdm import tqdm
from src.utils.helpers import clean_json_response
from src.config.settings import SYSTEM_PROMPT

class GrokEducationAnalyzer:
    def __init__(self):
        self.api_key = "xai-CpKouLyTQxr5NvuvFANHNhBMFFSh86QD6XOQzZdp3pQopI4xHuhirmel3nGP8UxdfKAcMwuLegZip6IS"
        self.batch_size = int(os.getenv('BATCH_SIZE', '25'))
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
                            'D': alt_d
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

    def process_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        results = []
        with tqdm(total=min(len(df), self.batch_size), desc="Procesando preguntas") as pbar:
            for i, (_, row) in enumerate(df.iterrows()):
                if i >= self.batch_size:
                    break
                result = self.analyze_justification(row)
                if result:
                    results.append(result)
                time.sleep(2)
                pbar.update(1)
        
        return pd.DataFrame(results)