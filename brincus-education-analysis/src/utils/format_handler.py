import json
from typing import Dict, Any

class QuillFormatHandler:
    @staticmethod
    def to_quill_format(text: str) -> Dict[str, Any]:
        """Convierte texto normal a formato Quill"""
        return {
            "ops": [
                {"insert": text + "\n"}
            ]
        }

    @staticmethod
    def from_quill_format(quill_json: str) -> str:
        """Extrae texto de formato Quill"""
        try:
            if isinstance(quill_json, str) and 'ops' in quill_json:
                data = json.loads(quill_json)
                if isinstance(data, dict) and 'ops' in data:
                    return ''.join(op.get('insert', '') for op in data['ops']).strip()
            return quill_json
        except json.JSONDecodeError:
            return quill_json

    @staticmethod
    def preserve_format(original_format: str, new_text: str) -> str:
        """Preserva el formato Quill mientras actualiza el texto"""
        try:
            if isinstance(original_format, str) and 'ops' in original_format:
                data = json.loads(original_format)
                if isinstance(data, dict) and 'ops' in data:
                    return json.dumps({"ops": [{"insert": new_text + "\n"}]})
            return new_text
        except json.JSONDecodeError:
            return new_text