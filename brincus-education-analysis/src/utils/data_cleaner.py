import pandas as pd
import json
import re

class DataCleaner:
    @staticmethod
    def clean_json_field(text):
        """Limpia campos que contienen JSON"""
        try:
            if pd.isna(text):
                return ""
            if isinstance(text, str) and 'ops' in text:
                json_obj = json.loads(text)
                if isinstance(json_obj, dict) and 'ops' in json_obj:
                    insert_content = json_obj['ops'][0].get('insert', '')
                    # Limpia caracteres especiales
                    return re.sub(r'\\n"|"$', '', insert_content)
            return text
        except:
            return text

    def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpia el DataFrame completo"""
        df_clean = df.copy()
        
        # Columnas que necesitan limpieza JSON
        json_columns = ['pregunta', 'alt_a', 'alt_b', 'alt_c', 'alt_d', 'alt_e', 'justificacion']
        
        for col in json_columns:
            if col in df_clean.columns:
                df_clean[col] = df_clean[col].apply(self.clean_json_field)
        
        # Limpieza adicional
        df_clean = df_clean.fillna('')  # Rellena NaN
        
        return df_clean

    @staticmethod
    def validate_row(row: pd.Series) -> bool:
        """Valida si una fila tiene todos los campos necesarios"""
        required_fields = ['pregunta', 'alt_a', 'alt_b', 'alt_c', 'alt_d', 'correcta', 'justificacion', 'curso']
        return all(row[field] != '' for field in required_fields if field in row)