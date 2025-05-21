import datetime

import streamlit as st
from streamlit.logger import get_logger

import nixnox.web.dbase as db
from nixnox.web.streamlit import ttl
from nixnox.lib import ObserverType, PhotometerModel


# ----------------
# Global variables
# ----------------

log = get_logger(__name__)

OBSERVATION_LIMIT = 10

# ---------------------
# Convenience functions
# ---------------------


@st.cache_data(ttl=ttl())
def obs_summary(_conn, limit):
    with _conn.session as session:
        return db.obs_summary(session, limit)


@st.cache_data(ttl=ttl())
def obs_nsummaries(_conn):
    with _conn.session as session:
        return db.obs_nsummaries(session)


@st.cache_data(ttl=ttl())
def get_observation_as_ecsv(_conn, obs_tag: str) -> str:
    with _conn.session as session:
        return db.obs_export(session, obs_tag)


def selected_obs() -> None:
    if st.session_state.Observation.selection.rows:
        log.debug(
            "st.session_state.Observation.selection.rows = %s",
            st.session_state.Observation.selection.rows,
        )
        row = st.session_state.Observation.selection.rows[0]
        log.debug("st.session_state.obs_list[row] = %s", st.session_state.obs_list[row])
        st.session_state.obs_tag = st.session_state.obs_list[row][
            1
        ]  # obst tag is the seccond item in the row


# ----------------------
# Start the ball rolling
# ----------------------

conn = st.connection("env:NX_ENV", type="sql")
# Photometer, Observer, Observation, Location, Date, Time, Measurement = database_models()
N = obs_nsummaries(conn)

if "obs_list" not in st.session_state:
    st.session_state.obs_list = obs_summary(conn, OBSERVATION_LIMIT)

st.title("**Available observations**")
st.write(f"""
    There are {obs_nsummaries(conn)} observations available.

    The most recent {min(N, OBSERVATION_LIMIT)} observations are displayed:
    """)
event = st.dataframe(
    st.session_state.obs_list,
    key="Observation",
    hide_index=True,
    on_select=selected_obs,
    selection_mode="single-row",
)

if "obs_tag" in st.session_state:
    obs_tag = st.session_state.obs_tag
    ecsv = get_observation_as_ecsv(conn, obs_tag)
    st.download_button(
        label=f"Download ECSV: *{obs_tag}*",
        data=ecsv,
        file_name=f"{obs_tag}.ecsv",
        mime="text/csv",
        icon=":material/download:",
    )

with st.expander("Search by Date"):
    from_date = st.date_input(
        "From", min_value=datetime.date(2000, 1, 1), max_value=datetime.date.today()
    )
    to_date = st.date_input(
        "To", min_value=datetime.date(2000, 1, 1), max_value=datetime.date.today()
    )
    st.button("Search", type="secondary", key="SearchByDateButton")

with st.expander("Search by Location"):
    c1, c2 = st.columns(2)
    with c1:
        longitude1 = st.text_input("Longitude 1", "0.0")
        longitude2 = st.text_input("Longitude 2", "0.0")
    with c2:
        latitude1 = st.text_input("Latitude 1", "0.0")
        latitude2 = st.text_input("Latitude 2", "0.0")
    st.button("Search", type="secondary", key="SearchByCoordsButton")

with st.expander("Search by Observer"):
    option = st.selectbox(
        "Observer type",
        [x.value for x in ObserverType],
    )
    st.text_input("Name", None, key="ObserverNameButton")
    st.button("Search", type="secondary", key="SearchByObserverButton")

with st.expander("Search by Photometer"):
    option = st.selectbox(
        "Model",
        [x.value for x in PhotometerModel],
    )
    st.text_input("Name", None, key="PhotNameButton")
    st.button("Search", type="secondary", key="SearchByPhotometerButton")
