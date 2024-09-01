import streamlit as st
import requests
import json
from docx import Document
from docx.shared import Pt
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH
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
    3. Especifique el número de capítulos (máximo 15).
    4. Seleccione la audiencia.
    5. Seleccione el idioma.
    6. Seleccione el número de subdivisiones por capítulo.
    7. Haga clic en "Generar tabla de contenido" para crear la estructura del libro.
    8. Edite los títulos de los capítulos si lo desea.
    9. Haga clic en "Generar contenido de capítulos" para crear el contenido.
    10. Descargue el libro completo en formato DOCX.

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

    audiencias = ["Principiantes", "Conocedores", "Expertos"]
    idiomas = ["Español", "Inglés", "Francés", "Alemán"]

    st.write("Ingrese los detalles del libro:")
    titulo_libro = st.text_input("Título del libro:")
    genero = st.selectbox("Género de no ficción:", generos_no_ficcion)
    audiencia = st.selectbox("Audiencia del libro:", audiencias)
    idioma = st.selectbox("Idioma del libro:", idiomas)
    num_capitulos = st.number_input("Número de capítulos:", min_value=1, max_value=15, value=10)
    num_subdivisiones = st.selectbox("Número de subdivisiones por capítulo:", [0, 1, 2])

    def generar_tabla_contenido(titulo, genero, audiencia, idioma, num_capitulos, num_subdivisiones):
        url = "https://api.together.xyz/inference"
        prompt = f"""
        Genera una tabla de contenido para un libro de no ficción titulado "{titulo}" en el género de {genero}, dirigido a una audiencia de {audiencia}, y en el idioma {idioma}.
        La tabla de contenido debe tener {num_capitulos} capítulos.
        Cada capítulo puede tener hasta {num_subdivisiones} subdivisiones.
        Los títulos de los capítulos y subdivisiones deben ser coherentes, atractivos y relevantes para el tema del libro.
        Formato de salida:
        Capítulo 1: [Título del capítulo 1]
        Subdivisión 1.1: [Título de la subdivisión 1.1] (si aplica)
        Subdivisión 1.2: [Título de la subdivisión 1.2] (si aplica)
        Capítulo 2: [Título del capítulo 2]
        ...
        Capítulo {num_capitulos}: [Título del capítulo {num_capitulos}]
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

    def generar_contenido_capitulo(titulo_libro, genero, audiencia, idioma, titulo_capitulo, numero_capitulo, num_subdivisiones):
        url = "https://api.together.xyz/inference"
        prompt = f"""
        Escribe el contenido detallado para el capítulo {numero_capitulo} titulado "{titulo_capitulo}" 
        del libro de no ficción "{titulo_libro}" en el género de {genero}, dirigido a una audiencia de {audiencia}, y en el idioma {idioma}.
        El contenido debe ser informativo, bien estructurado y relevante para el tema del libro.
        Incluye subtítulos, ejemplos y explicaciones detalladas.
        Cada capítulo puede tener hasta {num_subdivisiones} subdivisiones.
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

    if st.button("Generar tabla de contenido"):
        if titulo_libro and genero and audiencia and idioma:
            with st.spinner("Generando tabla de contenido..."):
                tabla_contenido = generar_tabla_contenido(titulo_libro, genero, audiencia, idioma, num_capitulos, num_subdivisiones)
                st.session_state.tabla_contenido = tabla_contenido
                st.success("Tabla de contenido generada con éxito.")
        else:
            st.warning("Por favor, ingrese el título del libro, seleccione un género, una audiencia y un idioma.")

    if 'tabla_contenido' in st.session_state:
        st.subheader("Tabla de contenido generada:")
        tabla_contenido_editada = st.text_area("Tabla de contenido (edite si es necesario):", "\n".join(st.session_state.tabla_contenido))
        st.session_state.tabla_contenido_editada = tabla_contenido_editada.split("\n")

    if 'tabla_contenido_editada' in st.session_state:
        if st.button("Generar contenido de capítulos"):
            with st.spinner("Generando contenido de capítulos..."):
                contenido_capitulos = []
                for i, titulo_capitulo in enumerate(st.session_state.tabla_contenido_editada):
                    contenido = generar_contenido_capitulo(titulo_libro, genero, audiencia, idioma, titulo_capitulo.split(": ", 1)[1], i+1, num_subdivisiones)
                    contenido_capitulos.append(contenido)
                st.session_state.contenido_capitulos = contenido_capitulos
                st.success("Contenido de capítulos generado con éxito.")

        if 'contenido_capitulos' in st.session_state:
            def create_docx(titulo, genero, tabla_contenido, contenido):
                doc = Document()
                
                # Crear estilos sin sangría y justificación completa
                styles = doc.styles
                style = styles.add_style('Sin Sangría', WD_STYLE_TYPE.PARAGRAPH)
                style.font.name = 'Calibri'
                style.font.size = Pt(11)
                style.paragraph_format.space_after = Pt(10)
                style.paragraph_format.first_line_indent = Pt(0)
                
                doc.add_heading(titulo, 0).alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                doc.add_paragraph(f"Género: {genero}", style='Sin Sangría').alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

                # Agregar tabla de contenido
                doc.add_heading("Tabla de Contenido", level=1).alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                for capitulo in tabla_contenido:
                    doc.add_paragraph(capitulo, style='Sin Sangría').alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

                # Agregar contenido de capítulos
                for i, capitulo in enumerate(contenido):
                    doc.add_heading(f"Capítulo {i+1}", level=1).alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                    doc.add_paragraph(capitulo, style='Sin Sangría').alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

                return doc

            doc = create_docx(titulo_libro, genero, st.session_state.tabla_contenido_editada, st.session_state.contenido_capitulos)
            
            buffer = BytesIO()
            doc.save(buffer)
            buffer.seek(0)
            
            st.download_button(
                label="Descargar libro en DOCX",
                data=buffer,
                file_name=f"{titulo_libro}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
