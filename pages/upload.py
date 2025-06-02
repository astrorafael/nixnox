import streamlit as st
from nixnox.web.page.upload import view_upload

# Database connection
conn = st.connection("env:NX_ENV", type="sql")

view_upload(conn)