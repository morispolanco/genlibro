import streamlit as st
import requests
import json

# Obtener las claves de API de los secretos de Streamlit
together_api_key = st.secrets["TOGETHER_API_KEY"]
serper_api_key = st.secrets["SERPER_API_KEY"]

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

# Función para hacer búsquedas con Serper
def serper_search(query):
    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": serper_api_key,
        "Content-Type": "application/json"
    }
    data = {
        "q": query
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return json.dumps(response.json(), indent=2)
    else:
        return f"Error: {response.status_code}, {response.text}"

st.title("Asistente para Escritores de No Ficción")

# Sección de Investigación y Síntesis
st.header("Investigación y Síntesis")
topic = st.text_input("Ingresa el tema principal de tu libro:")
subtopic = st.text_input("Ingresa un subtema específico (opcional):")

if st.button("Investigar"):
    search_query = f"{topic} {subtopic}".strip()
    search_results = serper_search(search_query)
    
    prompt = f"Analiza y sintetiza la siguiente información sobre '{search_query}' para un libro de no ficción: {search_results}. Proporciona un resumen conciso y bien estructurado, destacando los puntos clave, datos relevantes y cualquier controversia o debate actual sobre el tema."
    research_summary = together_complete(prompt)
    
    st.subheader("Resumen de Investigación")
    st.write(research_summary)

# Sección de Estructura del Libro
st.header("Estructura del Libro")
book_concept = st.text_area("Describe brevemente el concepto principal de tu libro:")

if st.button("Generar Estructura"):
    prompt = f"Basándote en el siguiente concepto de libro de no ficción: '{book_concept}', sugiere una estructura detallada para el libro. Incluye una propuesta de tabla de contenidos con capítulos y subcapítulos, así como una breve descripción del enfoque de cada sección principal."
    book_structure = together_complete(prompt)
    st.write(book_structure)

# Sección de Generación de Ideas para Capítulos
st.header("Ideas para Capítulos")
chapter_topic = st.text_input("Ingresa el tema del capítulo:")

if st.button("Generar Ideas"):
    prompt = f"Proporciona 5 ideas interesantes y únicas para desarrollar el capítulo sobre '{chapter_topic}' en un libro de no ficción. Incluye posibles ángulos, ejemplos o casos de estudio que podrían explorarse, y preguntas provocativas que el capítulo podría abordar."
    chapter_ideas = together_complete(prompt)
    st.write(chapter_ideas)

# Sección de Verificación de Hechos
st.header("Verificación de Hechos")
fact_to_check = st.text_area("Ingresa el hecho o afirmación a verificar:")

if st.button("Verificar"):
    search_results = serper_search(fact_to_check)
    
    prompt = f"Verifica la siguiente afirmación: '{fact_to_check}'. Basándote en la información encontrada: {search_results}, proporciona un análisis de la veracidad de la afirmación, citando fuentes confiables cuando sea posible. Si hay discrepancias o debates, menciónalos."
    fact_check_result = together_complete(prompt)
    st.write(fact_check_result)

# Sección de Estilo y Tono
st.header("Análisis de Estilo y Tono")
sample_text = st.text_area("Pega un fragmento de tu escritura para análisis:")

if st.button("Analizar Estilo"):
    prompt = f"Analiza el siguiente fragmento de un libro de no ficción en términos de estilo y tono:\n\n{sample_text}\n\nProporciona retroalimentación sobre la claridad, el compromiso del lector, el nivel de tecnicidad y la adecuación para el público objetivo. Sugiere formas de mejorar la accesibilidad y el impacto del texto."
    style_analysis = together_complete(prompt)
    st.write(style_analysis)

# Sección de Bibliografía y Citas
st.header("Asistente de Bibliografía")
source_info = st.text_area("Ingresa la información de la fuente (título, autor, año, URL, etc.):")
citation_style = st.selectbox("Estilo de citación:", ["APA", "MLA", "Chicago"])

if st.button("Generar Cita"):
    prompt = f"Genera una cita bibliográfica en estilo {citation_style} para la siguiente fuente:\n\n{source_info}"
    citation = together_complete(prompt)
    st.write(citation)
