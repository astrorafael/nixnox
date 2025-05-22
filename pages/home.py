# ------------------
# Standard libraries
# ------------------

from datetime import datetime

# ---------------------
# Third party libraries
# ---------------------

from dateutil.relativedelta import relativedelta

import streamlit as st
from streamlit.logger import get_logger

# -------------
# Own libraries
# -------------
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


def procesa() -> None:
    search_results = {k: st.session_state[k] for k in st.session_state.keys() if k.startswith("search_")}
    dt0 = datetime.combine(search_results["search_date_range"][0], datetime.min.time())
    dt1 = datetime.combine(search_results["search_date_range"][1], datetime.min.time())
    search_results["search_date_range"] = (dt0, dt1)
    st.write(search_results)



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
with st.form("Search", clear_on_submit=True):
    st.write("## Observations finder")
    with st.expander("Filter by date range"):
        ancient = min_value = datetime(2000, 1, 1,0,0,0)
        today = datetime.now().replace(hour=0, minute=0, second=0,microsecond=0)
        year_ago = today - relativedelta(years=1)
        month_ago = today - relativedelta(months=1)
        from_date = st.date_input(
            "Range", value=(month_ago, today), min_value=ancient, max_value=today, key="search_date_range"
        )
    with st.expander("Filter by location range"):
        c1, c2 = st.columns(2)
        with c1:
            longitude1 = st.number_input(
                "From Longitude", value=None, min_value=-180, max_value=180, key="search_from_longitude"
            )
            longitude2 = st.number_input(
                "To Longitude", value=None, min_value=-180, max_value=180, key="search_to_longitude"
            )
        with c2:
            latitude1 = st.number_input(
                "From Latitude", value=None, min_value=-90, max_value=90, key="search_from_latitude"
            )
            latitude2 = st.number_input(
                "To Latitude", value=None, min_value=-90, max_value=90, key="search_to_latitude"
            )
    with st.expander("Filter by observer"):
        option = st.selectbox(
            "Observer type",
            [x.value for x in ObserverType],  key="search_by_observer_type"
        )
        st.text_input("Name", value=None, key="search_by_observer_name")
    with st.expander("Filter by photometer"):
        option = st.selectbox(
            "Model",
            [x.value for x in PhotometerModel],  key="search_by_phot_model"
        )
        st.text_input("Name", value=None, key="search_by_photometer")
    st.form_submit_button(
        "**Search**",
        help="Search by any/all filter criteria",
        icon=":material/search:",
        on_click=procesa,
    )
