import streamlit as st
import requests
import json
from io import BytesIO
from docx import Document

# Configuración de la página
st.set_page_config(page_title="Generador de Contenido de Libro", page_icon="📚", layout="wide")

# Función para crear la columna de información
def crear_columna_info():
    st.markdown("""
    ## Sobre esta aplicación

    Esta aplicación genera descripciones de capítulos y citas textuales para un libro basado en el título y audiencia proporcionados.

    ### Cómo usar la aplicación:

    1. Ingrese el título del libro.
    2. Especifique el número de capítulos (hasta 15).
    3. Seleccione la audiencia.
    4. Genere los títulos de los capítulos.
    5. Edite los títulos de los capítulos si lo desea.
    6. Genere la descripción y las citas para los capítulos.
    7. Descargue el documento DOCX con el contenido del libro y las referencias.

    ### Autor:
    **Moris Polanco**, [Fecha actual]

    ---
    **Nota:** Esta es una herramienta de asistencia. Revise y ajuste el contenido según sea necesario.
    """)

# Títulos y columna principal
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
            "prompt": f"Genera {num_capitulos} títulos de capítulos para un libro titulado '{titulo_libro}'. Cada título debe estar en una línea nueva y ser relevante al tema del libro.",
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

    def generar_descripcion(titulo_libro, capitulo, audiencia):
        url = "https://api.together.xyz/inference"
        payload = json.dumps({
            "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "prompt": f"Escribe una descripción breve del capítulo '{capitulo}' para un libro titulado '{titulo_libro}' dirigido a '{audiencia}'.",
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

    def generar_citas(capitulo, titulo_libro, num_citas=10):
        url = "https://api.together.xyz/inference"
        payload = json.dumps({
            "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "prompt": f"Proporciona {num_citas} citas textuales con referencias completas en formato APA para un capítulo titulado '{capitulo}' de un libro titulado '{titulo_libro}'.",
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
        citas = response.json()['output']['choices'][0]['text'].strip().split('\n')
        return [cita.strip() for cita in citas if cita.strip()]

    def create_docx(titulo_libro, capitulos_contenido):
        doc = Document()
        doc.add_heading(f'{titulo_libro}', 0)

        # Capítulos y contenido
        for i, (capitulo, (descripcion, citas)) in enumerate(capitulos_contenido.items(), 1):
            doc.add_heading(f'Capítulo {i}: {capitulo}', level=1)
            doc.add_paragraph(descripcion)
            doc.add_heading('Citas', level=2)
            for cita in citas:
                doc.add_paragraph(cita, style='List Bullet')

        return doc

    # Interfaz de usuario
    titulo_libro = st.text_input("Ingresa el título del libro:")
    num_capitulos = st.number_input("Número de capítulos (máximo 15):", min_value=1, max_value=15, value=5)
    audiencia = st.selectbox("Selecciona la audiencia del libro:", ["Principiantes", "Conocedores", "Expertos"])

    if st.button("Generar títulos de capítulos"):
        if titulo_libro:
            with st.spinner("Generando títulos de capítulos..."):
                capitulos = generar_capitulos(titulo_libro, num_capitulos)
                st.session_state.capitulos = capitulos

    if 'capitulos' in st.session_state:
        st.subheader("Lista de capítulos (editable):")
        capitulos_editados = st.text_area("Edita los títulos de los capítulos aquí:", "\n".join(st.session_state.capitulos), height=300)
        st.session_state.capitulos_editados = capitulos_editados.split('\n')

    if 'capitulos_editados' in st.session_state:
        if st.button("Generar descripciones y citas de capítulos"):
            with st.spinner("Generando descripciones y citas..."):
                capitulos_contenido = {}

                for capitulo in st.session_state.capitulos_editados:
                    descripcion = generar_descripcion(titulo_libro, capitulo, audiencia)
                    citas = generar_citas(capitulo, titulo_libro)
                    capitulos_contenido[capitulo] = (descripcion, citas)

                st.subheader("Contenido del libro generado:")
                for capitulo, (descripcion, citas) in capitulos_contenido.items():
                    with st.expander(f"Capítulo: {capitulo}"):
                        st.write(descripcion)
                        st.write("Citas:")
                        for cita in citas:
                            st.markdown(f"- {cita}")

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
