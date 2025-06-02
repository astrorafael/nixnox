# ------------------
# Standard libraries
# ------------------

from typing import Any
from datetime import date
from collections import defaultdict

# ---------------------
# Third party libraries
# ---------------------

import streamlit as st
from streamlit.connections import SQLConnection
from streamlit import logger

# -------------
# Own libraries
# -------------

import nixnox.web.dbase as db
from nixnox.web.streamlit import ttl
from nixnox.lib import ObserverType, PhotometerModel


# ----------------
# Global variables
# ----------------

log = logger.get_logger(__name__)

obs_default_form = {
    "date": None,
    "tag": None,
    "place": None,
    "photometer": None,
    "observer": None,
}

# ---------------------
# Convenience functions
# ---------------------


@st.cache_data(ttl=ttl())
def obs_summary(_conn: SQLConnection, conditions: dict[str, Any]):
    with _conn.session as session:
        return db.obs_summary_search(session, conditions)


@st.cache_data(ttl=ttl())
def obs_nsummaries(_conn: SQLConnection):
    with _conn.session as session:
        return db.obs_nsummaries(session)


@st.cache_data(ttl=ttl())
def get_observation_as_ecsv(_conn: SQLConnection, obs_tag: str) -> str:
    with _conn.session as session:
        return db.obs_export(session, obs_tag)


def obs_init(conn: SQLConnection) -> None:
    if "obs_summ" not in st.session_state:
        st.session_state["obs_summ"] = defaultdict(dict)
        st.session_state["obs_summ"]["table"] = obs_summary(conn, None)
        st.session_state["obs_summ"]["selected"] = None
        st.session_state["obs_summ"]["form"].update(obs_default_form)


def on_selected_obs() -> None:
    if st.session_state.ObservationDataFrame.selection.rows:
        # Clicked one row
        row = st.session_state.ObservationDataFrame.selection.rows[0]
        # Get the whole row
        info = st.session_state["obs_summ"]["table"][row]
        st.session_state["obs_summ"]["selected"] = info
    else:
        st.session_state["obs_summ"]["selected"] = None


def on_obs_form_submit() -> None:
    conditions = {
        k: st.session_state[k] for k in st.session_state.keys() if k.startswith("search_")
    }
    if conditions:
        conditions["search_by_phot_model"] = PhotometerModel(conditions["search_by_phot_model"])
        conditions["search_by_observer_type"] = ObserverType(conditions["search_by_observer_type"])
        st.session_state["obs_summ"]["table"] = obs_summary(conn, conditions)
        st.session_state["obs_summ"]["selected"] = None

def obs_view_form() -> None:
    with st.form("Search", clear_on_submit=True):
        st.write("## Observations finder")
        st.slider(
            "Max. number of results", value=10, min_value=1, max_value=100, key="search_limit"
        )
        with st.expander("Filter by date range"):
            ancient = date(
                2000,
                1,
                1,
            )
            today = date.today()
            # month_ago = today - relativedelta(months=1)
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
            on_click=on_obs_form_submit,
        )


def obs_view_header(conn: SQLConnection) -> None:
    st.title("Available observations")
    st.write(f"There are {obs_nsummaries(conn)} stored observations available.")


def obs_view_table(conn: SQLConnection) -> None:
    st.header("Search results")
    st.dataframe(
        st.session_state["obs_summ"]["table"],
        key="ObservationDataFrame",
        hide_index=True,
        on_select=on_selected_obs,
        selection_mode="single-row",
    )
    if st.session_state["obs_summ"]["selected"]:
        obs_tag = st.session_state["obs_summ"]["selected"][1]
        ecsv = get_observation_as_ecsv(conn, obs_tag)
        st.download_button(
            label=f"Download ECSV file: *{obs_tag}*",
            data=ecsv,
            file_name=f"{obs_tag}.ecsv",
            mime="text/csv",
            icon=":material/download:",
        )
