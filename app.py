import streamlit as st
import requests
import json

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
        "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
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
    
    prompt_content = f"Escribe un contenido extenso para el capítulo titulado '{chapter_title}' en una tesis de derecho guatemalteco. El contenido debe tener al menos {min_word_count} palabras, incluir análisis, casos prácticos y referencias legales."
    
    # Dividir la generación de contenido en varias llamadas si es necesario
    content = ""
    while len(content.split()) < min_word_count:
        new_content = together_complete(prompt_content, max_tokens=1000)  # Generar bloques grandes de texto
        content += " " + new_content
    
    return content.strip()

# Función para convertir el contenido a formato HTML
def format_to_html(thesis_title, thesis_structure, thesis_content):
    html_content = f"<h1>{thesis_title}</h1>\n"
    
    for section in thesis_structure:
        html_content += f"<h2>{section['title']}</h2>\n"
        html_content += f"<p>{thesis_content[section['title']]}</p>\n"
    
    return html_content

st.title("Generación de Tesis Jurídica con Contenido Extenso y Formato HTML")

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
    thesis_structure = [{"title": chapter.strip()} for chapter in structure_response.split("\n") if chapter.strip()]
    
    # Generar contenido extenso para cada capítulo
    st.subheader("Generando contenido extenso para cada capítulo...")
    thesis_content = {}
    for section in thesis_structure:
        st.write(f"Generando contenido para el capítulo: {section['title']}")
        thesis_content[section['title']] = generate_chapter_content(section['title'], min_pages=7)
    
    # Formatear el contenido en HTML
    doc_title = f"Tesis sobre {thesis_topic}"
    html_content = format_to_html(doc_title, thesis_structure, thesis_content)
    
    # Mostrar el contenido generado en HTML
    st.subheader("Contenido Formateado en HTML")
    st.markdown(html_content, unsafe_allow_html=True)
    
    # Descargar el archivo HTML
    st.download_button(
        label="Descargar Tesis en HTML",
        data=html_content,
        file_name=f"{doc_title}.html",
        mime="text/html"
    )
