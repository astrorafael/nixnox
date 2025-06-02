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
st.set_page_config(page_title="NIXNOX", layout="wide", page_icon=":material/moon_stars:")
pg = st.navigation(
    {
        "General": [
            st.Page(
                os.path.join("pages", "home.py"),
                title="Observations List",
                icon=":material/list:",
            ),
            st.Page(
                os.path.join("pages", "obsdetails.py"),
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
        ],
        "Administration": [
            st.Page(
                os.path.join("pages", "adm", "observer.py"),
                title="Edit observer",
                icon=":material/edit:",
            ),
            st.Page(
                os.path.join("pages", "adm", "observation.py"),
                title="Edit observation",
                icon=":material/edit:",
            ),
            st.Page(
                os.path.join("pages", "adm", "location.py"),
                title="Edit location",
                icon=":material/edit:",
            ),
            st.Page(
                os.path.join("pages", "adm", "photometer.py"),
                title="Edit photometer",
                icon=":material/edit:",
            ),
        ],
    }
)
pg.run()
