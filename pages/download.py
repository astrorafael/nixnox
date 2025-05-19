# ----------------
# Standard library
# ----------------


# ---------
# STREAMLIT
# ---------
import streamlit as st

# -------------------
# Third party library
# -------------------

import nixnox.web.dbase as db

# ============
# PAGE OBJECTS
# ============

@st.cache_data(ttl=60)
def get_observation_as_ecsv(_conn, obs_tag: str):
    with _conn.session as session:
        return db.obs_export(session, obs_tag).getvalue()


conn = st.connection("nixnox_db", type="sql")
obs_tag = st.session_state.obs_tag
ecsv =  get_observation_as_ecsv(conn, obs_tag)


#st.write(ecsv)
st.download_button(
     label="Download CSV",
     data=ecsv,
     file_name=f"{obs_tag}.ecsv",
     mime="text/csv",
     icon=":material/download:",
 )