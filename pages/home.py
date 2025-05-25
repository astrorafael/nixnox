# ------------------
# Standard libraries
# ------------------
from typing import Callable
from datetime import date

# ---------------------
# Third party libraries
# ---------------------

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


# ---------------------
# Convenience functions
# ---------------------


@st.cache_data(ttl=ttl())
def obs_summary(_conn, conditions):
    with _conn.session as session:
        return db.obs_summary_search(session, conditions)


@st.cache_data(ttl=ttl())
def obs_nsummaries(_conn):
    with _conn.session as session:
        return db.obs_nsummaries(session)


@st.cache_data(ttl=ttl())
def get_observation_as_ecsv(_conn, obs_tag: str) -> str:
    with _conn.session as session:
        return db.obs_export(session, obs_tag)


def on_selected_obs() -> None:
    if st.session_state.ObservationDF.selection.rows:
        log.debug(
            "st.session_state.ObservationDF.selection.rows = %s",
            st.session_state.ObservationDF.selection.rows,
        )
        row = st.session_state.ObservationDF.selection.rows[0]
        log.debug("st.session_state.result_table[row] = %s", st.session_state.result_table[row])
        # obs_tag is the seccnd item in the row
        st.session_state.obs_tag = st.session_state.result_table[row][1]


def on_form_submit() -> None:
    search_conditions = {
        k: st.session_state[k] for k in st.session_state.keys() if k.startswith("search_")
    }
    if search_conditions:
        search_conditions["search_by_phot_model"] = PhotometerModel(
            search_conditions["search_by_phot_model"]
        )
        search_conditions["search_by_observer_type"] = ObserverType(
            search_conditions["search_by_observer_type"]
        )
        result_set = obs_summary(conn, search_conditions)
        #st.write(result_set)
        st.session_state.result_table = result_set


def view_form(on_submit: Callable) -> None:
    with st.form("Search", clear_on_submit=True):
        st.write("## Observations finder")
        st.slider("Max. number of results", value=10, min_value=1, max_value=100, key="search_limit")
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
            st.text_input("Name", value=None, max_chars=16, key="search_by_phot_name")
        st.form_submit_button(
            "**Search**",
            help="Search by any/all filter criteria",
            icon=":material/search:",
            type="primary",
            use_container_width=False,
            on_click=on_submit,
        )


def view_header(conn) -> None:
    st.title("**Available observations**")
    st.write(f"There are {obs_nsummaries(conn)} stored observations available.")
    if "result_table" not in st.session_state:
        st.write("Displaying a default view of what is available.")
        st.session_state.result_table = obs_summary(conn, None)
    else:
        table = st.session_state.result_table
        N = st.session_state.get("search_limit",10)
        st.write(f"Search displaying {len(table)}/{N}.")

def view_results(resultset):
    #st.write(f"Up to {limit} observations are displayed:")
    st.dataframe(
        st.session_state.result_table,
        key="ObservationDF",
        hide_index=True,
        on_select=on_selected_obs,
        selection_mode="single-row",
    )
    if "obs_tag" in st.session_state:
        obs_tag = st.session_state.obs_tag
        ecsv = get_observation_as_ecsv(conn, obs_tag)
        st.download_button(
            label=f"Download ECSV file: *{obs_tag}*",
            data=ecsv,
            file_name=f"{obs_tag}.ecsv",
            mime="text/csv",
            icon=":material/download:",
        )


# ----------------------
# Start the ball rolling
# ----------------------

conn = st.connection("env:NX_ENV", type="sql")
view_header(conn)
view_results(resultset=st.session_state.result_table)
view_form(on_submit=on_form_submit)
