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

# Función para generar un capítulo de la novela
def generate_chapter(chapter_number, title, genre, audience):
    prompt = f"Escribe el capítulo {chapter_number} de una novela larga titulada '{title}', en el género de {genre}, para una audiencia de {audience}. El capítulo debe ser extenso, detallado y mantener la coherencia narrativa del libro."
    
    # Generar el capítulo completo
    chapter = together_complete(prompt, max_tokens=1000)  # Puedes ajustar max_tokens para capítulos más largos si es necesario
    
    return chapter

# Función para generar el documento DOCX con la novela
def generate_novel_docx(title, genre, audience, chapters):
    doc = Document()
    
    # Formato del título de la novela
    title_heading = doc.add_heading(title, 0)
    title_heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Formato del género y audiencia
    doc.add_paragraph(f"Género: {genre} | Audiencia: {audience}").alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Estilo para los capítulos
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(12)
    
    for i, chapter in enumerate(chapters, start=1):
        # Título de cada capítulo
        chapter_title = f"Capítulo {i}"
        doc.add_heading(chapter_title, level=1)
        
        # Cuerpo del capítulo
        doc.add_paragraph(chapter)
    
    # Guardar el documento en un buffer
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# Función para generar múltiples capítulos simultáneamente utilizando multithreading
def generate_all_chapters(title, genre, audience, num_chapters=20):
    chapters = []
    
    # Usamos un ThreadPoolExecutor para ejecutar en paralelo
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(generate_chapter, i+1, title, genre, audience) for i in range(num_chapters)]
        
        # Procesar los resultados a medida que se completan
        for future in futures:
            try:
                chapters.append(future.result())
            except Exception as exc:
                chapters.append(f"Error al generar capítulo: {exc}")
    
    return chapters

st.title("Generación de Novela Larga Basada en Título, Género y Audiencia")

# Sección de generación de novela
st.header("Generación de Novela")
novel_title = st.text_input("Ingresa el título de tu novela:")
novel_genre = st.text_input("Ingresa el género de tu novela:")
novel_audience = st.text_input("Ingresa la audiencia de tu novela (ej. jóvenes adultos, adultos, niños):")

if st.button("Generar Novela y Exportar"):
    st.subheader("Generando los capítulos de la novela...")
    
    # Generar los capítulos de la novela en paralelo
    chapters = generate_all_chapters(novel_title, novel_genre, novel_audience)
    
    # Exportar la novela a DOCX
    docx_buffer = generate_novel_docx(novel_title, novel_genre, novel_audience, chapters)
    
    # Descargar el archivo DOCX
    st.download_button(
        label="Descargar Novela en DOCX",
        data=docx_buffer,
        file_name=f"{novel_title}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
