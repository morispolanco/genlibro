import streamlit as st
import requests
import json
from docx import Document
from docx.shared import Pt
from docx.enum.style import WD_STYLE_TYPE
from io import BytesIO

# Set page configuration
st.set_page_config(page_title="Generador de Libros de No Ficción", page_icon="📚", layout="wide")

# Function to create the information column
def crear_columna_info():
    st.markdown("""
    ## Sobre esta aplicación

    Esta aplicación genera capítulos para libros de no ficción basados en el título, género y número de capítulos especificados por el usuario.

    ### Cómo usar la aplicación:

    1. Ingrese el título del libro.
    2. Seleccione el género de no ficción.
    3. Especifique el número de capítulos (máximo 24).
    4. Haga clic en "Generar capítulos" para crear la estructura del libro.
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

    def generar_capitulos(titulo, genero, num_capitulos):
        url = "https://api.together.xyz/inference"
        prompt = f"""
        Genera {num_capitulos} títulos de capítulos para un libro de no ficción titulado "{titulo}" en el género de {genero}.
        Los títulos deben ser coherentes, atractivos y relevantes para el tema del libro.
        Formato de salida:
        1. [Título del capítulo 1]
        2. [Título del capítulo 2]
        ...
        {num_capitulos}. [Título del capítulo {num_capitulos}]
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
        return response.json()['output']['choices'][0]['text'].strip().split('\n')

    def generar_contenido_capitulo(titulo_libro, genero, titulo_capitulo, numero_capitulo):
        url = "https://api.together.xyz/inference"
        prompt = f"""
        Escribe el contenido detallado para el capítulo {numero_capitulo} del libro de no ficción "{titulo_libro}" en el género de {genero}.
        El contenido debe ser informativo, bien estructurado y relevante para el tema del libro.
        Incluye subtítulos, ejemplos y explicaciones detalladas.
        No repitas el título del capítulo "{titulo_capitulo}" al inicio del contenido.
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

    if st.button("Generar capítulos"):
        if titulo_libro and genero:
            with st.spinner("Generando capítulos..."):
                capitulos = generar_capitulos(titulo_libro, genero, num_capitulos)
                st.session_state.capitulos = capitulos
                st.success("Capítulos generados con éxito.")
        else:
            st.warning("Por favor, ingrese el título del libro y seleccione un género.")

    if 'capitulos' in st.session_state:
        st.subheader("Capítulos generados:")
        capitulos_editados = []
        for i, capitulo in enumerate(st.session_state.capitulos):
            capitulo_editado = st.text_input(f"Capítulo {i+1}", value=capitulo)
            capitulos_editados.append(capitulo_editado)
        st.session_state.capitulos_editados = capitulos_editados

    if 'capitulos_editados' in st.session_state:
        if st.button("Generar contenido de capítulos"):
            with st.spinner("Generando contenido de capítulos..."):
                contenido_capitulos = []
                for i, titulo_capitulo in enumerate(st.session_state.capitulos_editados):
                    contenido = generar_contenido_capitulo(titulo_libro, genero, titulo_capitulo, i+1)
                    contenido_capitulos.append(contenido)
                st.session_state.contenido_capitulos = contenido_capitulos
                st.success("Contenido de capítulos generado con éxito.")

        if 'contenido_capitulos' in st.session_state:
            def create_docx(titulo, genero, capitulos, contenido):
                doc = Document()
                
                # Crear estilos sin sangría
                styles = doc.styles
                style = styles.add_style('Sin Sangría', WD_STYLE_TYPE.PARAGRAPH)
                style.font.name = 'Calibri'
                style.font.size = Pt(11)
                style.paragraph_format.space_after = Pt(10)
                style.paragraph_format.first_line_indent = Pt(0)
                
                doc.add_heading(titulo, 0)
                doc.add_paragraph(f"Género: {genero}")

                for i, (capitulo, contenido) in enumerate(zip(capitulos, contenido)):
                    doc.add_heading(f"Capítulo {i+1}: {capitulo}", level=1)
                    paragraphs = contenido.split('\n')
                    for para in paragraphs:
                        if para.strip():
                            doc.add_paragraph(para.strip(), style='Sin Sangría')

                doc.add_paragraph('\nNota: Este libro fue generado por un asistente de IA. Se recomienda revisar y editar el contenido para garantizar precisión y calidad.', style='Sin Sangría')

                return doc

            doc = create_docx(titulo_libro, genero, st.session_state.capitulos_editados, st.session_state.contenido_capitulos)
            buffer = BytesIO()
            doc.save(buffer)
            buffer.seek(0)
            st.download_button(
                label="Descargar libro en DOCX",
                data=buffer,
                file_name=f"{titulo_libro.replace(' ', '_')}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
