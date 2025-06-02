import streamlit as st

from nixnox.web.page.observer import org_init, person_init, view_all

conn = st.connection("env:NX_ENV", type="sql")

org_init(conn)
person_init(conn)
view_all(conn)
