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
            icon=":material/list:",
        ),
        st.Page(
            os.path.join("pages", "observation.py"),
            title="Observation details",
            icon=":material/zoom_in:",
        ),
        st.Page(
            os.path.join("pages", "plot.py"),
            title="Observation plot",
            icon=":material/graph_7:",
        ),
        st.Page(
            os.path.join("pages", "upload.py"),
            title="Upload observation file",
            icon=":material/upload_file:",
        ),
        st.Page(
            os.path.join("pages", "plot_alex.py"),
            title="Plot Alex",
        ),
    ]
)
st.set_page_config(page_title="NIXNOX")
pg.run()
