import streamlit as st

st.title("Generador de Mapa de Brillo del Cielo en Proyección Polar")

# === FORMULARIO DEL USUARIO ===
st.sidebar.header("Datos del usuario")
nombre = st.sidebar.text_input("Nombre")
apellidos = st.sidebar.text_input("Apellidos")
institucion = st.sidebar.text_input("Institución")
latitud = st.sidebar.text_input("Latitud del sitio (opcional)")
longitud = st.sidebar.text_input("Longitud del sitio (opcional)")
alojamientos = st.sidebar.text_area("Alojamientos cercanos (opcional)")
archivo = st.sidebar.file_uploader("Sube tu archivo .ecsv", type=["ecsv", "csv"])