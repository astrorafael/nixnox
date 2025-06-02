import streamlit as st

from nixnox.web.page.admin.location import loc_init, loc_view

conn = st.connection("env:NX_ENV", type="sql")

loc_init(conn)
loc_view(conn)
