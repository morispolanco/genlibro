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
        "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
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

st.title("Asistente para Generación de Tesis Jurídicas")

# Sección de Investigación y Generación de Tesis
st.header("Generación de Tesis")
thesis_topic = st.text_input("Ingresa el tema de tu tesis de derecho:")

if st.button("Generar Tesis"):
    # Generar la tesis
    prompt = f"Proporciona una tesis circunscrita al ámbito legal guatemalteco sobre el siguiente tema: '{thesis_topic}'. La tesis debe ser una proposición que se debe probar, con un enfoque en el derecho guatemalteco."
    thesis_statement = together_complete(prompt)
    
    st.subheader("Tesis Propuesta")
    st.write(thesis_statement)
    
    # Generar la estructura automáticamente basada en la tesis
    st.subheader("Estructura Propuesta")
    prompt_structure = f"Con base en la siguiente tesis: '{thesis_statement}', propone una tabla de contenidos detallada para una tesis jurídica circunscrita al ámbito legal guatemalteco. Incluye una introducción y un número adecuado de capítulos (no fijo), con títulos claros y relacionados con el desarrollo de la tesis. Ajusta el número de capítulos según la complejidad de los temas tratados."
    thesis_structure = together_complete(prompt_structure)
    st.write(thesis_structure)

# Sección de Verificación de Fuentes Jurídicas
st.header("Verificación de Fuentes Jurídicas")
legal_fact_to_check = st.text_area("Ingresa el hecho o norma jurídica a verificar:")

if st.button("Verificar"):
    search_results = serper_search(legal_fact_to_check)
    
    prompt = f"Verifica la siguiente afirmación o norma jurídica: '{legal_fact_to_check}'. Basándote en la información encontrada: {search_results}, proporciona un análisis de su veracidad y relevancia en el derecho guatemalteco, citando fuentes legales cuando sea posible."
    legal_fact_check_result = together_complete(prompt)
    st.write(legal_fact_check_result)

# Sección de Bibliografía y Citas
st.header("Asistente de Bibliografía")
source_info = st.text_area("Ingresa la información de la fuente (título, autor, año, URL, etc.):")
citation_style = st.selectbox("Estilo de citación:", ["APA", "MLA", "Chicago"])

if st.button("Generar Cita"):
    prompt = f"Genera una cita bibliográfica en estilo {citation_style} para la siguiente fuente jurídica:\n\n{source_info}"
    citation = together_complete(prompt)
    st.write(citation)
