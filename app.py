import streamlit as st
import requests
import json
from docx import Document
from io import BytesIO
import random

# Set page configuration
st.set_page_config(page_title="Generador de Contenido de Libro", page_icon="📚", layout="wide")

# Function to create the information column
def crear_columna_info():
    st.markdown("""
    ## Sobre esta aplicación

    Esta aplicación genera el contenido completo de los capítulos para un libro basado en el título proporcionado.

    ### Cómo usar la aplicación:

    1. Ingrese el título del libro.
    2. Especifique el número de capítulos (hasta 15).
    3. Genere los títulos de los capítulos.
    4. Edite los títulos de los capítulos si lo desea.
    5. Genere el contenido completo de los capítulos (5 a 10 páginas cada uno).
    6. Descargue el documento DOCX con el contenido del libro y las referencias.

    ### Autor:
    **Moris Polanco**, [Fecha actual]

    ---
    **Nota:** Esta es una herramienta de asistencia. Revise y ajuste el contenido según sea necesario.
    """)

# Titles and Main Column
st.title("Generador de Contenido de Libro")

col1, col2 = st.columns([1, 2])

with col1:
    crear_columna_info()

with col2:
    TOGETHER_API_KEY = st.secrets["TOGETHER_API_KEY"]
    SERPLY_API_KEY = st.secrets["SERPLY_API_KEY"]

    def generar_capitulos(titulo_libro, num_capitulos, audiencia):
        url = "https://api.together.xyz/inference"
        payload = json.dumps({
            "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "prompt": f"Genera {num_capitulos} títulos de capítulos para un libro titulado '{titulo_libro}' dirigido a {audiencia}. Cada título debe estar en una línea nueva y ser relevante al tema del libro.",
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

    def buscar_informacion(query):
        url = f"https://api.serply.io/v1/scholar/q={query}"
        headers = {
            'X-Api-Key': SERPLY_API_KEY,
            'Content-Type': 'application/json',
            'X-Proxy-Location': 'US',
            'X-User-Agent': 'Mozilla/5.0'
        }
        response = requests.get(url, headers=headers)
        return response.json()

    def generar_contenido(titulo_libro, capitulo, contexto):
        num_palabras = random.randint(1500, 3000)  # Variable length between 5 and 10 pages
        url = "https://api.together.xyz/inference"
        payload = json.dumps({
            "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "prompt": f"Escribe el contenido completo del capítulo '{capitulo}' para el libro titulado '{titulo_libro}' basado en el siguiente contexto académico. El contenido debe ser detallado, informativo y tener una extensión de aproximadamente {num_palabras} palabras. Evita repeticiones y subdivisiones:\n\nContexto: {contexto}\n\nContenido del capítulo:",
            "max_tokens": 4096,
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

    def create_docx(titulo_libro, capitulos_contenido):
        doc = Document()
        doc.add_heading(f'{titulo_libro}', 0)

        # Capítulos y contenido con referencias
        for i, (capitulo, data) in enumerate(capitulos_contenido.items(), 1):
            doc.add_heading(f'Capítulo {i}: {capitulo}', level=1)
            doc.add_paragraph(data['contenido'])
            doc.add_heading('Referencias', level=2)
            for referencia in data['referencias']:
                doc.add_paragraph(referencia, style='List Bullet')

        return doc

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
    audiencia = st.selectbox("Selecciona la audiencia:", ["Principiantes", "Conocedores", "Expertos"])
    num_capitulos = st.number_input("Número de capítulos (máximo 15):", min_value=1, max_value=15, value=5)

    if st.button("Generar títulos de capítulos"):
        if titulo_libro:
            with st.spinner("Generando títulos de capítulos..."):
                capitulos = generar_capitulos(titulo_libro, num_capitulos, audiencia)
                st.session_state.capitulos = capitulos

    if 'capitulos' in st.session_state:
        st.subheader("Lista de capítulos (editable):")
        capitulos_editados = st.text_area("Edita los títulos de los capítulos aquí:", "\n".join(st.session_state.capitulos), height=300)
        st.session_state.capitulos_editados = capitulos_editados.split('\n')

    if 'capitulos_editados' in st.session_state:
        if st.button("Generar contenido de capítulos"):
            with st.spinner("Generando contenido y referencias..."):
                capitulos_contenido = {}

                for capitulo in st.session_state.capitulos_editados:
                    resultados_busqueda = buscar_informacion(f"{capitulo} {titulo_libro}")
                    contexto = "\n".join([item["snippet"] for item in resultados_busqueda.get("results", [])])
                    contenido = generar_contenido(titulo_libro, capitulo, contexto)
                    referencias = [formatear_referencia_apa(item) for item in resultados_busqueda.get("results", [])[:10]]  # Limit to 10 references

                    capitulos_contenido[capitulo] = {
                        'contenido': contenido,
                        'referencias': referencias
                    }

                st.subheader("Contenido del libro generado:")
                for capitulo, data in capitulos_contenido.items():
                    with st.expander(f"Capítulo: {capitulo}"):
                        st.write(data['contenido'])
                        st.write("**Referencias:**")
                        for referencia in data['referencias']:
                            st.markdown(f"- {referencia}")

                # Botón para descargar el documento
                doc = create_docx(titulo_libro, capitulos_contenido)
                buffer = BytesIO()
                doc.save(buffer)
                buffer.seek(0)
                st.download_button(
                    label="Descargar libro completo en DOCX",
                    data=buffer,
                    file_name=f"{titulo_libro.replace(' ', '_')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
