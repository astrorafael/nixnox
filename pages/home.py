import streamlit as st
from nixnox.web.page.home import obs_init, obs_view_header, obs_view_table, obs_view_form

conn = st.connection("env:NX_ENV", type="sql")
obs_init(conn)
obs_view_header(conn)
obs_view_table(conn)
obs_view_form()
