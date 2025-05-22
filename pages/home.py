# ------------------
# Standard libraries
# ------------------
from typing import Callable
from datetime import date

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
    if st.session_state.ObservationDF.selection.rows:
        log.debug(
            "st.session_state.ObservationDF.selection.rows = %s",
            st.session_state.ObservationDF.selection.rows,
        )
        row = st.session_state.ObservationDF.selection.rows[0]
        log.debug("st.session_state.obs_list[row] = %s", st.session_state.obs_list[row])
        # obs_tag is the seccnd item in the row
        st.session_state.obs_tag = st.session_state.obs_list[row][1]


def procesa() -> None:
    search_conditions = {
        k: st.session_state[k] for k in st.session_state.keys() if k.startswith("search_")
    }
    search_conditions["search_by_phot_model"] = PhotometerModel(
        search_conditions["search_by_phot_model"]
    )
    search_conditions["search_by_observer_type"] = ObserverType(
        search_conditions["search_by_observer_type"]
    )
    with conn.session as session:
        resultado = db.obs_summary_search(session, search_conditions)
        st.write(resultado)
        st.session_state.obs_list = resultado


def form(on_submit: Callable) -> None:
    with st.form("Search", clear_on_submit=True):
        st.write("## Observations finder")
        with st.expander("Filter by date range"):
            ancient = date(
                2000,
                1,
                1,
            )
            today = date.today()
            #month_ago = today - relativedelta(months=1)
            st.date_input(
                "Range",
                value=(ancient, today),
                min_value=ancient,
                max_value=today,
                key="search_date_range",
            )
        with st.expander("Filter by location range"):
            st.markdown("**Enter coordinates range OR location below**")
            coords_c, text_c = st.columns(2)
            with coords_c:
                with st.container(border=True):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.number_input(
                            "From Longitude (deg.)",
                            value=None,
                            min_value=-180,
                            max_value=180,
                            key="search_from_longitude",
                        )
                        st.number_input(
                            "From Latitude (deg.)",
                            value=None,
                            min_value=-90,
                            max_value=90,
                            key="search_from_latitude",
                        )

                    with c2:
                        st.number_input(
                            "To Longitude (deg.)",
                            value=None,
                            min_value=-180,
                            max_value=180,
                            key="search_to_longitude",
                        )

                        st.number_input(
                            "To Latitude (deg.)",
                            value=None,
                            min_value=-90,
                            max_value=90,
                            key="search_to_latitude",
                        )
            with text_c:
                with st.container(border=True):
                    st.selectbox(
                        "Scope", ["Population Centre", "Country"], key="search_by_location_scope"
                    )
                    st.text_input(
                        "Population centre or Country",
                        key="search_by_location_name",
                        value=None,
                        max_chars=80,
                    )
        with st.expander("Filter by observer"):
            st.selectbox(
                "Observer type", [x.value for x in ObserverType], key="search_by_observer_type"
            )
            st.text_input("Name", value=None, key="search_by_observer_name")
        with st.expander("Filter by photometer"):
            st.selectbox("Model", [x.value for x in PhotometerModel], key="search_by_phot_model")
            st.text_input("Name", value=None, key="search_by_photometer")
        st.form_submit_button(
            "**Search**",
            help="Search by any/all filter criteria",
            icon=":material/search:",
            type="primary",
            use_container_width=True,
            on_click=on_submit,
        )


def header(conn) -> None:
    st.title("**Available observations**")
    if "obs_list" not in st.session_state:
        st.session_state.obs_list = obs_summary(conn, OBSERVATION_LIMIT)
    N = obs_nsummaries(conn)
    st.write(f"There are {obs_nsummaries(conn)} observations available.")


def results(resultset, limit):
    st.write(f"Up to {limit} observations are displayed:")
    st.dataframe(
        st.session_state.obs_list,
        key="ObservationDF",
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


# ----------------------
# Start the ball rolling
# ----------------------

conn = st.connection("env:NX_ENV", type="sql")
header(conn)
results(resultset=st.session_state.obs_list, limit=OBSERVATION_LIMIT)
st.divider()
form(on_submit=procesa)
