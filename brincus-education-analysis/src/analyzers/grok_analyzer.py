import os
import json
import time
from typing import Dict, List
import requests
import pandas as pd
from tqdm import tqdm
from src.utils.helpers import clean_json_response
from src.config.settings import SYSTEM_PROMPT

class GrokEducationAnalyzer:
    def __init__(self):
        # API Key directa para debugging
        self.api_key = "xai-CpKouLyTQxr5NvuvFANHNhBMFFSh86QD6XOQzZdp3pQopI4xHuhirmel3nGP8UxdfKAcMwuLegZip6IS"
        self.batch_size = int(os.getenv('BATCH_SIZE', '10'))
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        self.url = "https://api.x.ai/v1/chat/completions"
        
        # Verificar configuración
        print("Configuración del analizador:")
        print(f"API URL: {self.url}")
        print(f"Headers: {self.headers}")

    def analyze_justification(self, row: pd.Series) -> Dict:
        """Analiza una pregunta individual usando Grok"""
        try:
            payload = {
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": self._create_prompt(row)}
                ],
                "model": "grok-beta",
                "stream": False,
                "temperature": 0.3
            }

            # Debug de la petición
            print(f"\nEnviando petición para ID {row['id']}:")
            print(f"URL: {self.url}")
            print(f"Headers: {self.headers}")
            print(f"Payload: {json.dumps(payload, indent=2)}")

            response = requests.post(
                self.url,
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 200:
                content = response.json()['choices'][0]['message']['content']
                cleaned_content = clean_json_response(content)
                json_content = json.loads(cleaned_content)
                
                return {
                    'id': row['id'],
                    'curso': row['curso'],
                    'pregunta_original': row['pregunta'],
                    'justificacion_original': row['justificacion'],
                    'analisis_grok': json.dumps(json_content, ensure_ascii=False)
                }
            else:
                print(f"\nError API para ID {row['id']}:")
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"\nError procesando ID {row['id']}: {str(e)}")
            return None

    def process_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        """Procesa un lote de preguntas"""
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

    def _create_prompt(self, row: pd.Series) -> str:
        """Crea el prompt para la pregunta"""
        return f"""
Para un estudiante de {row['curso']}:

PREGUNTA: {row['pregunta']}
ALTERNATIVAS:
A) {row['alt_a']}
B) {row['alt_b']}
C) {row['alt_c']}
D) {row['alt_d']}
RESPUESTA CORRECTA: {row['correcta']}
JUSTIFICACIÓN ACTUAL: {row['justificacion']}"""

    def _log_error(self, message: str):
        """Registra errores en el log"""
        print(f"\nERROR: {message}")