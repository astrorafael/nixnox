import streamlit as st
from nixnox.web.page.observation import obs_init, obs_view_details

conn = st.connection("env:NX_ENV", type="sql")

obs_tag = obs_init(conn)
if obs_tag:
    obs_view_details(conn, obs_tag)