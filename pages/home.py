import streamlit as st

import nixnox.web.dbase as db

# ---------------------
# Convenience functions
# ---------------------

@st.cache_data(ttl=60)
def obs_summary(_conn):
    with _conn.session as session:
        return db.obs_summary(session)


def selected_obs() -> None:
    row = st.session_state.Observation.selection.rows[0]
    st.session_state.obs_tag = st.session_state.obs_list[row][0]

# ----------------------
# Start the ball rolling
# ----------------------

conn = st.connection("nixnox_db", type="sql")
# Photometer, Observer, Observation, Location, Date, Time, Measurement = database_models()

if "obs_list" not in st.session_state:
    st.session_state.obs_list = obs_summary(conn)

st.title("**Available observations**")
event = st.dataframe(
    st.session_state.obs_list, 
    key="Observation",
    hide_index=True,
    on_select=selected_obs,
    selection_mode="single-row"
)
