# streamlit_demo.py
import streamlit as st
import time
from pathlib import Path
import base64

# Configuración de la página
st.set_page_config(
    page_title="IA en Educación - Mejora de Preguntas",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Preguntas demo pre-procesadas con LaTeX
DEMO_QUESTIONS = [
    {
        "titulo": "Ecuación Cuadrática",
        "pregunta": "¿Cuál es la solución de la siguiente ecuación cuadrática?",
        "latex": r"2x^2 + 3x - 5 = 0",
        "tiempo": 1.2
    },
    {
        "titulo": "Función Exponencial",
        "pregunta": "Determine el valor de x que satisface la siguiente ecuación:",
        "latex": r"e^x + 2^x = 10",
        "tiempo": 1.2
    },
    {
        "titulo": "Derivada",
        "pregunta": "Calcule la derivada de la función:",
        "latex": r"f(x) = \frac{x^2 + 3x}{x - 1}",
        "tiempo": 1.2
    },
    {
        "titulo": "Integral Definida",
        "pregunta": "Evalúe la siguiente integral definida:",
        "latex": r"\int_{0}^{\pi} \sin(x) \cos(x) dx",
        "tiempo": 1.2
    },
    {
        "titulo": "Límite",
        "pregunta": "Calcule el siguiente límite:",
        "latex": r"\lim_{x \to \infty} \frac{\sqrt{x^2 + 1}}{x}",
        "tiempo": 1.2
    }
]

def load_css():
    """Carga estilos personalizados"""
    st.markdown("""
        <style>
        .main {
            padding: 2rem;
        }
        .question-card {
            padding: 1.5rem;
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
        }
        .stProgress {
            height: 20px;
        }
        .stProgress > div > div {
            background-color: #00acee;
        }
        </style>
    """, unsafe_allow_html=True)

def show_pdf_download(pdf_path: str):
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    b64_pdf = base64.b64encode(pdf_bytes).decode()
    st.download_button(
        label="Descargar Reporte PDF ⬇️",
        data=pdf_bytes,
        file_name="preguntas_mejoradas.pdf",
        mime="application/pdf"
    )

def main():
    load_css()
    
    # Header
    col1, col2 = st.columns([1, 5])
    with col1:
        st.image("assets/logo.png", width=120)
    with col2:
        st.title("Mejora Automática de Preguntas con IA")
    
    st.markdown("---")
    
    # Barra de progreso principal
    progress = st.progress(0)
    
    # Contenedor para las preguntas
    question_container = st.container()
    
    # Procesar cada pregunta
    for i, pregunta in enumerate(DEMO_QUESTIONS):
        # Actualizar progreso
        progress.progress((i + 1) * 20)
        
        with question_container:
            st.markdown(f"### {pregunta['pregunta']}")
            st.latex(pregunta['latex'])
            
            # Pequeña pausa para mostrar el "procesamiento"
            time.sleep(pregunta['tiempo'])
            
            st.markdown("---")
    
    # Finalización
    st.success("¡Proceso completado!")
    show_pdf_download("output/preguntas_mejoradas.pdf")

if __name__ == "__main__":
    main()