import streamlit as st
import requests
import json
from docx import Document
from io import BytesIO

# Configuración de la página
st.set_page_config(page_title="Generador de Contenido de Libro", page_icon="📚", layout="wide")

# Función para crear la columna de información
def crear_columna_info():
    st.markdown("""
    ## Sobre esta aplicación

    Esta aplicación genera descripciones detalladas y citas para capítulos de un libro basado en el título proporcionado.

    ### Cómo usar la aplicación:

    1. Ingrese el título del libro.
    2. Seleccione la audiencia (principiantes, conocedores, expertos).
    3. Especifique el número de capítulos (hasta 15).
    4. Genere los títulos de los capítulos.
    5. Edite los títulos de los capítulos si lo desea.
    6. Genere descripciones y citas para los capítulos.
    7. Genere contenido para un capítulo específico.
    8. Descargue el documento DOCX con el contenido del libro y las referencias.

    ### Autor:
    **Moris Polanco**, [Fecha actual]

    ---
    **Nota:** Esta es una herramienta de asistencia. Revise y ajuste el contenido según sea necesario.
    """)

# Columnas principales
st.title("Generador de Contenido de Libro")

col1, col2 = st.columns([1, 2])

with col1:
    crear_columna_info()

with col2:
    TOGETHER_API_KEY = st.secrets["TOGETHER_API_KEY"]
    SERPLY_API_KEY = st.secrets["SERPLY_API_KEY"]

    def generar_capitulos(titulo_libro, num_capitulos, audiencia):
        url = "https://api.together.xyz/inference"
        prompt = (f"Genera {num_capitulos} títulos de capítulos para un libro titulado '{titulo_libro}' "
                  f"dirigido a {audiencia}. Cada título debe estar en una línea nueva y ser relevante al tema del libro.")
        payload = json.dumps({
            "model": "meta-llama/Meta-Llama-3-70B-Instruct-Turbo",
            "prompt": prompt,
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
        url = f"https://api.serply.io/v1/scholar?q={query}"
        headers = {
            'X-Api-Key': SERPLY_API_KEY,
            'Content-Type': 'application/json',
            'X-Proxy-Location': 'US',
            'X-User-Agent': 'Mozilla/5.0'
        }
        response = requests.get(url, headers=headers)
        return response.json()

    def generar_descripcion_y_citas(titulo_libro, capitulo, audiencia):
        # Generar descripción
        url = "https://api.together.xyz/inference"
        prompt_desc = (f"Escribe una descripción general para el capítulo '{capitulo}' en un libro titulado '{titulo_libro}', "
                       f"dirigido a {audiencia}. La descripción debe ser concisa y adecuada para este público.")
        payload_desc = json.dumps({
            "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "prompt": prompt_desc,
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
        response_desc = requests.post(url, headers=headers, data=payload_desc)
        descripcion = response_desc.json()['output']['choices'][0]['text'].strip()

        # Buscar información para citas reales
        resultados_busqueda = buscar_informacion(f"{capitulo} {titulo_libro}")
        citas = []
        citas_formateadas = []
        
        for item in resultados_busqueda.get("results", [])[:10]:
            cita = item["snippet"]
            referencia = formatear_referencia_apa(item)
            citas.append(f'"{cita}" - {referencia}')
            citas_formateadas.append(referencia)

        return descripcion, citas, citas_formateadas

    def generar_contenido_capitulo(titulo_libro, capitulo, audiencia, descripcion, citas):
        url = "https://api.together.xyz/inference"
        prompt = (f"Escribe el contenido completo del capítulo '{capitulo}' para el libro titulado '{titulo_libro}', "
                  f"dirigido a {audiencia}, basado en la siguiente descripción y citas. El contenido debe tener al menos 15 páginas.\n\n"
                  f"Descripción: {descripcion}\n\nCitas: {', '.join(citas)}\n\nContenido del capítulo:")
        payload = json.dumps({
            "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "prompt": prompt,
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
        contenido = response.json()['output']['choices'][0]['text'].strip()
        return contenido

    def create_docx(titulo_libro, capitulos_contenido, referencias):
        doc = Document()
        doc.add_heading(f'{titulo_libro}', 0)

        # Capítulos y contenido
        for i, (capitulo, (descripcion, citas, contenido)) in enumerate(capitulos_contenido.items(), 1):
            doc.add_heading(f'Capítulo {i}: {capitulo}', level=1)
            doc.add_paragraph(descripcion)
            doc.add_heading('Citas', level=2)
            for cita in citas:
                doc.add_paragraph(cita, style='List Bullet')
            doc.add_paragraph(contenido)

        # Referencias
        doc.add_page_break()
        doc.add_heading('Referencias', level=1)
        for referencia in referencias:
            doc.add_paragraph(referencia, style='List Bullet')

        return doc

    def formatear_referencia_apa(item):
        authors = item.get('author', 'Autor desconocido')
        year = item.get('year', 's.f.')
        title = item.get('title', 'Título desconocido')
        journal = item.get('journal', '')
        volume = item.get('volume', '')
        issue = item.get('issue', '')
        pages = item.get('pages', '')
        url = item.get('url', '')

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
    audiencia = st.selectbox("Selecciona la audiencia del libro:", ["principiantes", "conocedores", "expertos"])
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
        if st.button("Generar descripciones y citas de capítulos"):
            with st.spinner("Generando descripciones y citas..."):
                capitulos_contenido = {}
                todas_referencias = []

                for capitulo in st.session_state.capitulos_editados:
                    descripcion, citas, referencias = generar_descripcion_y_citas(titulo_libro, capitulo, audiencia)
                    capitulos_contenido[capitulo] = (descripcion, citas, None)
                    todas_referencias.extend(referencias)

                st.session_state.capitulos_contenido = capitulos_contenido
                st.session_state.todas_referencias = todas_referencias

        if 'capitulos_contenido' in st.session_state:
            st.subheader("Contenido de los capítulos generados:")

            for capitulo, (descripcion, citas, _) in st.session_state.capitulos_contenido.items():
                st.write(f"**Capítulo: {capitulo}**")
                st.write(f"**Descripción:** {descripcion}")
                st.write(f"**Citas:**")
                for cita in citas:
                    st.write(f"- {cita}")
                st.write("---")

            capitulo_especifico = st.selectbox("Selecciona un capítulo para generar contenido:", st.session_state.capitulos_editados)

            if st.button("Generar contenido para el capítulo seleccionado"):
                with st.spinner("Generando contenido del capítulo..."):
                    descripcion, citas, _ = st.session_state.capitulos_contenido[capitulo_especifico]
                    contenido = generar_contenido_capitulo(titulo_libro, capitulo_especifico, audiencia, descripcion, citas)
                    st.session_state.capitulos_contenido[capitulo_especifico] = (descripcion, citas, contenido)
                    st.success(f"Contenido generado para el capítulo '{capitulo_especifico}'")

            if st.button("Generar y descargar DOCX"):
                with st.spinner("Generando archivo DOCX..."):
                    doc = create_docx(titulo_libro, st.session_state.capitulos_contenido, st.session_state.todas_referencias)
                    buffer = BytesIO()
                    doc.save(buffer)
                    buffer.seek(0)

                    st.download_button(
                        label="Descargar documento",
                        data=buffer,
                        file_name=f"{titulo_libro}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
