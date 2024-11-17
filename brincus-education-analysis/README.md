# Brincus Education Analysis System

## Descripción
Sistema de análisis y mejora de contenido educativo utilizando IA (Grok) para optimizar preguntas y justificaciones en rutas de aprendizaje.

## Características
- Análisis automático de preguntas educativas
- Mejora de justificaciones con enfoque pedagógico
- Generación de reportes en múltiples formatos
- Adaptación del contenido según nivel educativo
- Exportación a PDF con formato institucional

## Requisitos
- Python 3.8+
- Docker y Docker Compose
- Grok API Key
- Dependencias listadas en requirements.txt

## Estructura del Proyecto
```
brincus-education-analysis/
├── src/
│   ├── analyzers/
│   │   ├── __init__.py
│   │   ├── grok_analyzer.py
│   │   └── pdf_generator.py
│   ├── utils/
│   │   ├── __init__.py
│   │   └── helpers.py
│   └── config/
│       └── settings.py
├── tests/
│   └── test_analyzer.py
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── templates/
│   └── report_template.html
├── .env.example
├── requirements.txt
└── README.md
```

## Configuración
1. Clonar el repositorio
```bash
git clone https://github.com/brincus/education-analysis.git
```

2. Copiar .env.example a .env y configurar variables
```bash
cp .env.example .env
```

3. Construir y levantar con Docker
```bash
docker-compose up --build
```

## Uso
```python
from src.analyzers.grok_analyzer import GrokEducationAnalyzer

analyzer = GrokEducationAnalyzer()
results = analyzer.analyze_batch('input.csv')
analyzer.generate_report(results)
```

## Variables de Entorno (.env)
- GROK_API_KEY: API key de Grok
- OUTPUT_DIR: Directorio para reportes
- BATCH_SIZE: Tamaño del lote de procesamiento
- LOG_LEVEL: Nivel de logging

## Documentación
Para más detalles, consultar la [documentación completa](docs/index.md)

## Contribuir
1. Fork del repositorio
2. Crear rama feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## Licencia
Uso interno Brincus Education