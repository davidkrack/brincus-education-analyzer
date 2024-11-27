import json
from typing import Dict, Any

class QuillFormatHandler:
    @staticmethod
    def to_quill_format(text: str, preserve_latex: bool = True) -> Dict[str, Any]:
        """
        Convierte texto normal a formato Quill, preservando LaTeX si está presente
        """
        if preserve_latex and ('$' in text):
            # Dividir el texto en segmentos normales y LaTeX
            segments = []
            is_latex = False
            current = ""
            
            for char in text:
                if char == '$':
                    if current:
                        segments.append({"insert": current, "attributes": {"latex": is_latex}})
                        current = ""
                    is_latex = not is_latex
                else:
                    current += char
                    
            if current:
                segments.append({"insert": current, "attributes": {"latex": is_latex}})
                
            return {"ops": segments}
        else:
            return {"ops": [{"insert": text + "\n"}]}

    @staticmethod
    def from_quill_format(quill_json: str) -> str:
        """Extrae texto de formato Quill, preservando LaTeX"""
        try:
            if isinstance(quill_json, str) and 'ops' in quill_json:
                data = json.loads(quill_json)
                if isinstance(data, dict) and 'ops' in data:
                    text = ""
                    for op in data['ops']:
                        content = op.get('insert', '')
                        if op.get('attributes', {}).get('latex'):
                            text += f"${content}$"
                        else:
                            text += content
                    return text.strip()
            return quill_json
        except json.JSONDecodeError:
            return quill_json

    @staticmethod
    def preserve_format(original_format: str, new_text: str) -> str:
        """Preserva el formato Quill mientras actualiza el texto"""
        try:
            if isinstance(original_format, str) and 'ops' in original_format:
                return json.dumps(QuillFormatHandler.to_quill_format(new_text))
            return new_text
        except json.JSONDecodeError:
            return new_text