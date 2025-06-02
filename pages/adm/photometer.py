import streamlit as st

from nixnox.web.page.admin.observation import obs_init, obs_view

conn = st.connection("env:NX_ENV", type="sql")

obs_init(conn)
obs_view(conn)
