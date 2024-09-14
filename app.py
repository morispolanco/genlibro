import streamlit as st
import requests
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor

# Obtener las claves de API de los secretos de Streamlit
together_api_key = st.secrets["TOGETHER_API_KEY"]

# Función para hacer llamadas a la API de Together
def together_complete(prompt, max_tokens=500):
    url = "https://api.together.xyz/v1/completions"
    headers = {
        "Authorization": f"Bearer {together_api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": 0.7,
        "top_p": 0.7,
        "top_k": 50,
        "repetition_penalty": 1.1,  # Penalización para evitar repeticiones
        "stop": ["<|eot_id|>"]
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()['choices'][0]['text'].strip()
    else:
        return f"Error: {response.status_code}, {response.text}"

# Función para generar un cuento largo imitando el estilo de un autor latinoamericano
def generate_story(story_number, author_name):
    prompt = f"Escribe un cuento largo número {story_number} imitando el estilo del autor latinoamericano {author_name}. El cuento debe ser detallado, con un desarrollo profundo de los personajes y las emociones, en un tono similar al del autor mencionado."
    
    # Generar el cuento completo
    story = together_complete(prompt, max_tokens=1000)  # Puedes ajustar max_tokens para cuentos más largos si es necesario
    
    return story

# Función para generar el documento DOCX con los 24 cuentos
def generate_stories_docx(title, author_name, stories):
    doc = Document()
    
    # Formato del título del libro
    title_heading = doc.add_heading(title, 0)
    title_heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Formato del nombre del autor
    doc.add_paragraph(f"Imitando el estilo de {author_name}").alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Formato para los cuentos
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(12)
    
    for i, story in enumerate(stories, start=1):
        # Título de cada cuento
        story_title = f"Cuento {i}"
        doc.add_heading(story_title, level=1)
        
        # Cuerpo del cuento
        doc.add_paragraph(story)
    
    # Guardar el documento en un buffer
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# Función para generar los 24 cuentos simultáneamente utilizando multithreading
def generate_all_stories(author_name):
    stories = []
    
    # Usamos un ThreadPoolExecutor para ejecutar en paralelo
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(generate_story, i+1, author_name) for i in range(24)]
        
        # Procesar los resultados a medida que se completan
        for future in futures:
            try:
                stories.append(future.result())
            except Exception as exc:
                stories.append(f"Error al generar cuento: {exc}")
    
    return stories

st.title("Generación de 24 Cuentos Largos Imitando el Estilo de un Autor Latinoamericano")

# Sección de generación de cuentos
st.header("Generación de Cuentos")
author_name = st.text_input("Ingresa el nombre del autor latinoamericano cuyo estilo se va a imitar:")

if st.button("Generar 24 Cuentos y Exportar"):
    st.subheader("Generando los 24 cuentos largos...")
    
    # Generar los 24 cuentos imitando el estilo del autor
    stories = generate_all_stories(author_name)
    
    # Título del libro
    book_title = f"24 Cuentos Largos Imitando el Estilo de {author_name}"
    
    # Exportar a DOCX
    docx_buffer = generate_stories_docx(book_title, author_name, stories)
    
    # Descargar el archivo DOCX
    st.download_button(
        label="Descargar Libro en DOCX",
        data=docx_buffer,
        file_name=f"{book_title}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
