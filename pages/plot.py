import streamlit as st
from nixnox.web.page.plot import plot_init, plot_view

conn = st.connection("env:NX_ENV", type="sql")


obs_tag = plot_init(conn)
if obs_tag:
    plot_view(conn, obs_tag)