# ---------------
# Standard library
# ---------------

# ---------
# STREAMLIT
# ---------

import streamlit as st

# ---------------
# Other libraries
# ---------------

import nixnox.lib.ecsv as nx


# Database connection
conn = st.connection("nixnox_db", type="sql")

st.title("Subir ficheros TAS a la base de datos")

# === FORMULARIO DEL USUARIO ===
st.sidebar.header("Datos del usuario")
data = st.sidebar.file_uploader("Sube tu archivo .ecsv", type=["ecsv", "csv"])
if data:
    with conn.session as session:
        try:
            observation = nx.loader(session, data)
        except nx.AlreadyExistsError as e:
        	observation = e.args[0]
        	st.error(f"Error: {observation.identifier} already exists in the database", icon="🚨")
        else:
            st.info(f"Observation upload to database: {observation.identifier}", icon="ℹ️")
