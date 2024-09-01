import streamlit as st
import requests
import json
from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.shared import Pt
from io import BytesIO

# Set page configuration
st.set_page_config(page_title="Generador de Libros de No Ficción", page_icon="📚")

# Titles and Main Column
st.title("Generador de Libros de No Ficción")

st.write("Ingrese los detalles del libro:")
titulo_libro = st.text_input("Título del libro:")
num_capitulos = st.number_input("Número de capítulos:", min_value=1, max_value=15, value=10)
audiencia = st.selectbox("Audiencia:", ["Principiantes", "Conocedores", "Expertos"])
instrucciones_adicionales = st.text_area("Instrucciones adicionales", placeholder="Ingrese cualquier instrucción adicional para la generación del contenido")

# Secret key for API
TOGETHER_API_KEY = st.secrets["TOGETHER_API_KEY"]

def generar_tabla_contenido(titulo, num_capitulos, audiencia, instrucciones_adicionales):
    url = "https://api.together.xyz/inference"
    prompt = f"""
    Genera una tabla de contenido limpia para un libro de no ficción titulado "{titulo}".
    El libro está dirigido a una audiencia {audiencia}.
    La tabla de contenido debe tener {num_capitulos} capítulos.
    Los títulos de los capítulos deben ser coherentes, atractivos y relevantes para el tema del libro, sin repeticiones.
    {instrucciones_adicionales}
    Formato de salida:
    Capítulo 1: [Título del capítulo 1]
    Capítulo 2: [Título del capítulo 2]
    ...
    Capítulo {num_capitulos}: [Título del capítulo {num_capitulos}]
    """

    payload = json.dumps({
        "model": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
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

def generar_contenido_capitulo(titulo_libro, titulo_capitulo, numero_capitulo, audiencia, instrucciones_adicionales):
    url = "https://api.together.xyz/inference"
    prompt = f"""
    Escribe el contenido detallado para el capítulo {numero_capitulo} titulado "{titulo_capitulo}" 
    del libro de no ficción "{titulo_libro}".
    El contenido debe ser adecuado para una audiencia {audiencia}.
    {instrucciones_adicionales}
    No repitas el título del capítulo al inicio del contenido.
    Comienza directamente con el contenido del capítulo.
    """

    payload = json.dumps({
        "model": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
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

if st.button("Generar tabla de contenido"):
    if titulo_libro:
        with st.spinner("Generando tabla de contenido..."):
            tabla_contenido = generar_tabla_contenido(titulo_libro, num_capitulos, audiencia, instrucciones_adicionales)
            st.session_state.tabla_contenido = tabla_contenido
            st.success("Tabla de contenido generada con éxito.")
    else:
        st.warning("Por favor, ingrese el título del libro.")

if 'tabla_contenido' in st.session_state:
    st.subheader("Tabla de contenido generada:")
    tabla_contenido_editada = st.text_area("Edite los títulos de los capítulos si es necesario:", value="\n".join(st.session_state.tabla_contenido), height=400)
    st.session_state.tabla_contenido_editada = tabla_contenido_editada.strip().split('\n')

if 'tabla_contenido_editada' in st.session_state:
    if st.button("Generar contenido de capítulos"):
        with st.spinner("Generando contenido de capítulos..."):
            contenido_capitulos = []
            for i, titulo_capitulo in enumerate(st.session_state.tabla_contenido_editada):
                contenido = generar_contenido_capitulo(titulo_libro, titulo_capitulo.split(": ", 1)[1], i+1, audiencia, instrucciones_adicionales)
                contenido_capitulos.append(contenido)
            st.session_state.contenido_capitulos = contenido_capitulos
            st.success("Contenido de capítulos generado con éxito.")

    if 'contenido_capitulos' in st.session_state:
        def create_docx(titulo, tabla_contenido, contenido):
            doc = Document()

            # Check if the style already exists, and add it if not
            try:
                style = doc.styles.add_style('Sin Sangría', WD_STYLE_TYPE.PARAGRAPH)
                style.font.name = 'Calibri'
                style.font.size = Pt(11)
                style.paragraph_format.space_after = Pt(10)
                style.paragraph_format.first_line_indent = Pt(0)
            except KeyError:
                # Style might already exist
                style = doc.styles['Sin Sangría']

            doc.add_heading(titulo, 0)

            # Add table of contents
            doc.add_heading("Tabla de Contenido", level=1)
            for capitulo in tabla_contenido:
                doc.add_paragraph(capitulo, style='Sin Sangría')

            # Add chapter contents
            for i, capitulo in enumerate(contenido):
                try:
                    chapter_title = tabla_contenido[i].split(": ", 1)[1]
                except IndexError:
                    chapter_title = f"Capítulo {i+1}"
                doc.add_page_break()
                doc.add_heading(f"Capítulo {i+1}: {chapter_title}", level=2)
                doc.add_paragraph(capitulo, style='Sin Sangría')

            doc.add_paragraph('\nNota: Este libro fue generado por un asistente de IA. Se recomienda revisar y editar el contenido para garantizar precisión y calidad.', style='Sin Sangría')

            return doc

        doc = create_docx(titulo_libro, st.session_state.tabla_contenido_editada, st.session_state.contenido_capitulos)

        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)

        st.download_button(
            label="Descargar libro en DOCX",
            data=buffer,
            file_name=f"{titulo_libro}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
