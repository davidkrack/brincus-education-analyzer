import json
from typing import Dict, Any

def clean_json_response(response: str) -> str:
    """Limpia la respuesta de Grok eliminando delimitadores de código"""
    return response.replace('```json', '').replace('```', '').strip()

def validate_json_response(content: str) -> Dict[str, Any]:
    """Valida y parsea una respuesta JSON"""
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON inválido: {str(e)}")

def format_course_name(course: str) -> str:
    """Formatea el nombre del curso"""
    return course.strip().upper()