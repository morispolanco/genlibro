import streamlit as st
import requests
import json
from docx import Document
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
        "repetition_penalty": 1,
        "stop": ["<|eot_id|>"]
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()['choices'][0]['text'].strip()
    else:
        return f"Error: {response.status_code}, {response.text}"

# Función para generar el contenido de cada capítulo con al menos siete páginas simuladas
def generate_chapter_content(chapter_title, min_pages=7):
    page_word_count = 350  # Aproximación de palabras por página
    min_word_count = page_word_count * min_pages  # Palabras mínimas por capítulo
    
    prompt_content = f"Escribe un contenido extenso para el capítulo titulado '{chapter_title}' en un libro de introducción a la filosofía. El contenido debe tener al menos {min_word_count} palabras, incluyendo referencias a filósofos relevantes, corrientes filosóficas y ejemplos para facilitar la comprensión."
    
    # Dividir la generación de contenido en varias llamadas si es necesario
    content = ""
    while len(content.split()) < min_word_count:
        new_content = together_complete(prompt_content, max_tokens=1000)  # Generar bloques grandes de texto
        content += " " + new_content
    
    return content.strip()

# Función para generar el documento DOCX basado en la estructura y contenido
def generate_docx(title, thesis_structure, thesis_content):
    doc = Document()
    doc.add_heading(title, 0)
    
    # Crear el contenido dinámicamente
    for section in thesis_structure:
        doc.add_heading(section['title'], level=1)
        doc.add_paragraph(thesis_content[section['title']])
    
    # Guardar el documento en un buffer
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# Función para generar contenido simultáneamente utilizando multithreading
def generate_all_chapters_concurrently(thesis_structure):
    thesis_content = {}
    
    # Usamos un ThreadPoolExecutor para ejecutar en paralelo
    with ThreadPoolExecutor() as executor:
        # Lanzar tareas simultáneamente
        future_to_section = {executor.submit(generate_chapter_content, section['title']): section for section in thesis_structure}
        
        # Procesar los resultados a medida que se completan
        for future in future_to_section:
            section = future_to_section[future]
            try:
                thesis_content[section['title']] = future.result()
            except Exception as exc:
                thesis_content[section['title']] = f"Error al generar contenido: {exc}"
    
    return thesis_content

st.title("Generación Simultánea de Libro de Introducción a la Filosofía con Exportación a DOCX")

# Sección de Generación de Libro
st.header("Generación de Libro")
book_topic = st.text_input("Ingresa el tema central de tu libro de filosofía:")

if st.button("Generar Libro y Estructura"):
    # Generar la introducción y estructura del libro
    prompt_thesis = f"Proporciona un libro de introducción a la filosofía circunscrito al tema: '{book_topic}'."
    book_statement = together_complete(prompt_thesis)
    st.subheader("Propuesta del Libro")
    st.write(book_statement)
    
    # Generar la estructura automáticamente basada en el tema
    prompt_structure = f"Con base en el siguiente libro: '{book_statement}', propone una tabla de contenidos detallada para un libro de introducción a la filosofía. Incluye una introducción y un número adecuado de capítulos que cubran el tema de manera exhaustiva."
    structure_response = together_complete(prompt_structure)
    st.subheader("Estructura Propuesta")
    st.write(structure_response)
    
    # Procesar la estructura en un formato que se pueda utilizar
    thesis_structure = [{"title": chapter.strip()} for chapter in structure_response.split("\n") if chapter.strip()]
    
    # Generar contenido extenso para cada capítulo de forma simultánea
    st.subheader("Generando contenido extenso para cada capítulo de forma simultánea...")
    thesis_content = generate_all_chapters_concurrently(thesis_structure)
    
    # Exportar a DOCX
    doc_title = f"Introducción a la Filosofía: {book_topic}"
    docx_buffer = generate_docx(doc_title, thesis_structure, thesis_content)
    
    # Descargar el archivo DOCX
    st.download_button(
        label="Descargar Libro en DOCX",
        data=docx_buffer,
        file_name=f"{doc_title}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
