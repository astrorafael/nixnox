import os
import streamlit as st

pg = st.navigation(
    [
        st.Page(os.path.join("pages", "home.py"), title="Listing"),
        st.Page(os.path.join("pages", "observation.py"), title="Observation details"),
        st.Page(
            os.path.join("pages", "data_entry.py"),
            title="Upload observation file",
            icon=":material/add_circle:",
        ),
    ]
)
st.set_page_config(page_title="NIXNOX")
pg.run()
