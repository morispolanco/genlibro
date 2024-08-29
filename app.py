import streamlit as st
import requests
import json
from docx import Document
from io import BytesIO

# Set page configuration
st.set_page_config(page_title="Generador de Contenido de Libro", page_icon="📚", layout="wide")

# Function to create the information column
def crear_columna_info():
    st.markdown("""
    ## Sobre esta aplicación

    Esta aplicación genera contenido de libro con capítulos y citas relevantes en formato APA.

    ### Cómo usar la aplicación:

    1. Ingrese el título del libro.
    2. Selecciona el número de capítulos y la audiencia objetivo.
    3. Agrega observaciones adicionales (opcional).
    4. Genere el contenido del libro con descripciones breves de cada capítulo y citas relevantes.

    ### Autor:
    **Moris Polanco**, [Fecha actual]

    ---
    **Nota:** Verifique la información con fuentes adicionales para un análisis más profundo.
    """)

# Titles and Main Column
st.title("Generador de Contenido de Libro")

col1, col2 = st.columns([1, 2])

with col1:
    crear_columna_info()

with col2:
    TOGETHER_API_KEY = st.secrets["TOGETHER_API_KEY"]
    SERPLY_API_KEY = st.secrets["SERPLY_API_KEY"]

    def generar_capitulos(titulo_libro, num_capitulos):
        url = "https://api.together.xyz/inference"
        payload = json.dumps({
            "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "prompt": f"Genera {num_capitulos} títulos de capítulos para el libro '{titulo_libro}'. Cada título debe estar en una línea nueva.",
            "max_tokens": 2048,
            "temperature": 0.7,
            "top_p": 0.7,
            "top_k": 50,
            "repetition_penalty": 1,
        })
        headers = {
            'Authorization': f'Bearer {TOGETHER_API_KEY}',
            'Content-Type': 'application/json'
        }
        response = requests.post(url, headers=headers, data=payload)
        capitulos = response.json()['output']['choices'][0]['text'].strip().split('\n')
        return [capitulo.strip() for capitulo in capitulos if capitulo.strip()]

    def generar_descripcion_capitulo(capitulo):
        url = "https://api.together.xyz/inference"
        payload = json.dumps({
            "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "prompt": f"Proporciona una descripción breve del capítulo '{capitulo}'. No incluyas ejemplos ni detalles técnicos.",
            "max_tokens": 1024,
            "temperature": 0.7,
            "top_p": 0.7,
            "top_k": 50,
            "repetition_penalty": 1,
        })
        headers = {
            'Authorization': f'Bearer {TOGETHER_API_KEY}',
            'Content-Type': 'application/json'
        }
        response = requests.post(url, headers=headers, data=payload)
        return response.json()['output']['choices'][0]['text'].strip()

    def buscar_citas_relevantes(titulo_libro, num_citas):
        url = f"https://api.serply.io/v1/scholar/q={titulo_libro}"
        headers = {
            'X-Api-Key': SERPLY_API_KEY,
            'Content-Type': 'application/json',
            'X-Proxy-Location': 'US',
            'X-User-Agent': 'Mozilla/5.0'
        }
        response = requests.get(url, headers=headers)
        citas = response.json().get("results", [])[:num_citas]
        return [formatear_referencia_apa(cita) for cita in citas]

    def formatear_referencia_apa(ref):
        authors = ref.get('author', 'Autor desconocido')
        year = ref.get('year', 's.f.')
        title = ref.get('title', 'Título desconocido')
        journal = ref.get('journal', '')
        volume = ref.get('volume', '')
        issue = ref.get('issue', '')
        pages = ref.get('pages', '')
        url = ref.get('url', '')

        reference = f"{authors} ({year}). {title}."
        if journal:
            reference += f" {journal}"
            if volume:
                reference += f", {volume}"
                if issue:
                    reference += f"({issue})"
            if pages:
                reference += f", {pages}"
        reference += f". {url}"
        
        return reference

    # Interfaz de usuario
    titulo_libro = st.text_input("Ingresa el título del libro:")

    num_capitulos = st.selectbox("Selecciona el número de capítulos:", [5, 10, 15])

    audiencia = st.selectbox("Selecciona la audiencia objetivo:", ["Estudiantes", "Profesionales", "Investigadores"])

    observaciones = st.text_area("Agrega observaciones adicionales (opcional):")

    if st.button("Generar contenido del libro"):
        with st.spinner("Generando contenido del libro..."):
            capitulos = generar_capitulos(titulo_libro, num_capitulos)
            descripciones_capitulos = {capitulo: generar_descripcion_capitulo(capitulo) for capitulo in capitulos}
            citas_relevantes = buscar_citas_relevantes(titulo_libro, 10)

            # Mostrar resultados
            st.subheader("Capítulos generados:")
            for capitulo, descripcion in descripciones_capitulos.items():
                st.markdown(f"**{capitulo}**: {descripcion}")

            st.subheader("Citas relevantes:")
            for cita in citas_relevantes:
                st.markdown(f"- {cita}")

            # Botón para descargar el documento
            doc = Document()
            doc.add_heading(f"{titulo_libro}", 0)

            # Capítulos
            doc.add_heading("Capítulos", level=1)
            for capitulo, descripcion in descripciones_capitulos.items():
                doc.add_paragraph(f"{capitulo}: {descripcion}")

            # Citas
            doc.add_page_break()
            doc.add_heading("Citas relevantes", level=1)
            for cita in citas_relevantes:
                doc.add_paragraph(cita, style='List Bullet')

            buffer = BytesIO()
            doc.save(buffer)
            buffer.seek(0)
            st.download_button(
                label="Descargar contenido del libro en DOCX",
                data=buffer,
                file_name=f"Contenido_{titulo_libro.replace(' ', '_')}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
