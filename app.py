import streamlit as st
import requests
import json
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from io import BytesIO

# Set page configuration
st.set_page_config(page_title="Generador de Libros de No Ficción", page_icon="📚", layout="wide")

# Function to create the information column
def crear_columna_info():
    st.markdown("""
    ## Sobre esta aplicación

    Esta aplicación genera una tabla de contenido editable para libros de no ficción basada en el título, género y número de capítulos especificados por el usuario.

    ### Cómo usar la aplicación:

    1. Ingrese el título del libro.
    2. Seleccione el género de no ficción.
    3. Especifique el número de capítulos (máximo 24).
    4. Haga clic en "Generar tabla de contenido" para crear la estructura del libro.
    5. Edite los títulos de los capítulos si lo desea.
    6. Haga clic en "Generar contenido de capítulos" para crear el contenido.
    7. Descargue el libro completo en formato DOCX.

    ### Autor y actualización:
    **[Tu Nombre]**, [Fecha actual]

    ### Cómo citar esta aplicación (formato APA):
    [Tu Apellido], [Inicial del Nombre]. (Año). *Generador de Libros de No Ficción* [Aplicación web]. [URL de tu aplicación]

    ---
    **Nota:** Esta aplicación utiliza inteligencia artificial para generar contenido. Siempre revise y edite el contenido generado para garantizar precisión y calidad.
    """)

# Titles and Main Column
st.title("Generador de Libros de No Ficción")

# Create two columns
col1, col2 = st.columns([1, 2])

# Column 1 content
with col1:
    crear_columna_info()

# Column 2 content
with col2:
    TOGETHER_API_KEY = st.secrets["TOGETHER_API_KEY"]

    # Géneros de no ficción
    generos_no_ficcion = [
        "Autobiografía", "Biografía", "Historia", "Ciencia", "Tecnología",
        "Filosofía", "Psicología", "Autoayuda", "Negocios", "Economía",
        "Política", "Sociología", "Antropología", "Viajes", "Naturaleza",
        "Medio ambiente", "Salud y bienestar", "Cocina", "Arte", "Música"
    ]

    st.write("Ingrese los detalles del libro:")
    titulo_libro = st.text_input("Título del libro:")
    genero = st.selectbox("Género de no ficción:", generos_no_ficcion)
    num_capitulos = st.number_input("Número de capítulos:", min_value=1, max_value=24, value=10)

    def generar_tabla_contenido(titulo, genero, num_capitulos):
        url = "https://api.together.xyz/inference"
        prompt = f"""
        Genera una tabla de contenido para un libro de no ficción titulado "{titulo}" en el género de {genero}.
        La tabla de contenido debe tener {num_capitulos} capítulos.
        Los títulos de los capítulos deben ser coherentes, atractivos y relevantes para el tema del libro.
        """
        
        payload = json.dumps({
            "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "prompt": prompt,
            "max_tokens": 1024,
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 50,
            "repetition_penalty": 1.1
        })
        headers = {
            'Authorization': f'Bearer {TOGETHER_API_KEY}',
            'Content-Type': 'application/json'
        }
        response = requests.post(url, headers=headers, data=payload)
        return response.json()['output']['choices'][0]['text'].strip()

# Ajuste en el código para evitar errores al dividir títulos de capítulos
def generar_contenido_capitulo(titulo_libro, genero, titulo_capitulo, numero_capitulo):
    url = "https://api.together.xyz/inference"
    prompt = f"""
    Escribe el contenido detallado para el capítulo {numero_capitulo} titulado "{titulo_capitulo}" 
    del libro de no ficción "{titulo_libro}" en el género de {genero}.
    El contenido debe ser informativo, bien estructurado y relevante para el tema del libro.
    Incluye subtítulos, ejemplos y explicaciones detalladas.
    No repitas el título del capítulo al inicio del contenido.
    Comienza directamente con el contenido del capítulo.
    """
    
    payload = json.dumps({
        "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "prompt": prompt,
        "max_tokens": 4096,
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 50,
        "repetition_penalty": 1.1
    })
    headers = {
        'Authorization': f'Bearer {TOGETHER_API_KEY}',
        'Content-Type': 'application/json'
    }
    response = requests.post(url, headers=headers, data=payload)
    return response.json()['output']['choices'][0]['text'].strip()

if 'tabla_contenido_editada' in st.session_state:
    if st.button("Generar contenido de capítulos"):
        with st.spinner("Generando contenido de capítulos..."):
            contenido_capitulos = []
            for i, titulo_capitulo in enumerate(st.session_state.tabla_contenido_editada):
                # Asegurar que el título del capítulo tiene el formato esperado
                partes_titulo = titulo_capitulo.split(": ", 1)
                if len(partes_titulo) > 1:
                    contenido = generar_contenido_capitulo(titulo_libro, genero, partes_titulo[1], i+1)
                else:
                    contenido = generar_contenido_capitulo(titulo_libro, genero, partes_titulo[0], i+1)
                contenido_capitulos.append(contenido)
            st.session_state.contenido_capitulos = contenido_capitulos
            st.success("Contenido de capítulos generado con éxito.")
