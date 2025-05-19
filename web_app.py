# ---------------
# Standard library
# ---------------

import os

# ---------
# STREAMLIT
# ---------

import streamlit as st

# ==========================
# WEB APPPLICATION STRUCTURE
# ==========================

pg = st.navigation(
    [
        st.Page(
            os.path.join("pages", "home.py"),
            title="Observations List",
        ),
        st.Page(
            os.path.join("pages", "observation.py"),
            title="Observation details",
        ),
        st.Page(
            os.path.join("pages", "plot.py"),
            title="Observation plot",
        ),
        st.Page(
            os.path.join("pages", "data_entry.py"),
            title="Upload observation file",
            icon=":material/add_circle:",
        ),
        
    ]
)
st.set_page_config(page_title="NIXNOX")
pg.run()
