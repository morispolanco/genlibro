import streamlit as st
import requests
import json
from docx import Document
from io import BytesIO

# Obtener las claves de API de los secretos de Streamlit
together_api_key = st.secrets["TOGETHER_API_KEY"]

# Función para hacer llamadas a la API de Together
def together_complete(prompt):
    url = "https://api.together.xyz/v1/completions"
    headers = {
        "Authorization": f"Bearer {together_api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
        "prompt": prompt,
        "max_tokens": 500,
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

st.title("Generación de Tesis Jurídica y Exportación a DOCX")

# Sección de Generación de Tesis
st.header("Generación de Tesis")
thesis_topic = st.text_input("Ingresa el tema de tu tesis de derecho:")

if st.button("Generar Tesis y Estructura"):
    # Generar la tesis
    prompt_thesis = f"Proporciona una tesis circunscrita al ámbito legal guatemalteco sobre el siguiente tema: '{thesis_topic}'."
    thesis_statement = together_complete(prompt_thesis)
    st.subheader("Tesis Propuesta")
    st.write(thesis_statement)
    
    # Generar la estructura automáticamente basada en la tesis
    prompt_structure = f"Con base en la siguiente tesis: '{thesis_statement}', propone una tabla de contenidos detallada para una tesis jurídica circunscrita al ámbito legal guatemalteco. Incluye una introducción y un número adecuado de capítulos."
    structure_response = together_complete(prompt_structure)
    st.subheader("Estructura Propuesta")
    st.write(structure_response)
    
    # Procesar la estructura en un formato que se pueda utilizar
    # Se asume que la API devuelve una lista de capítulos y subtítulos
    thesis_structure = [{"title": chapter.strip()} for chapter in structure_response.split("\n") if chapter.strip()]
    
    # Generar contenido dinámico para cada capítulo
    thesis_content = {}
    for section in thesis_structure:
        prompt_content = f"Escribe el contenido completo para el capítulo titulado '{section['title']}' en una tesis de derecho guatemalteco."
        thesis_content[section['title']] = together_complete(prompt_content)
    
    # Exportar a DOCX
    doc_title = f"Tesis sobre {thesis_topic}"
    docx_buffer = generate_docx(doc_title, thesis_structure, thesis_content)
    
    # Descargar el archivo DOCX
    st.download_button(
        label="Descargar Tesis en DOCX",
        data=docx_buffer,
        file_name=f"{doc_title}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
