# ------------------
# Standard libraries
# ------------------

from typing import Any
from datetime import date
from collections import defaultdict

# ---------------------
# Third party libraries
# ---------------------

import pandas as pd
import streamlit as st
from streamlit.connections import SQLConnection
from streamlit import logger

# -------------
# Own libraries
# --------------

import nixnox.web.dbase as db
from nixnox.web.streamlit import ttl

# ============
# PAGE OBJECTS
# ============

log = logger.get_logger(__name__)
conn = st.connection("env:NX_ENV", type="sql")


def get_observation_details(_session, obs_tag: str):
    return db.obs_details(_session, obs_tag)


@st.cache_data(ttl=ttl())
def get_measurements(_session, obs_tag: str):
        return db.obs_measurements(_session, obs_tag)


def obs_init(conn: SQLConnection) -> str | None:
    selected = st.session_state["obs_summ"]["selected"]
    if not selected:
        st.warning("### Please, select an observation in the home page", icon="⚠️")
    result = st.session_state["obs_summ"]["selected"][1] if selected else None
    return result

def obs_view_details(conn: SQLConnection, obs_tag: str) -> None:
    with conn.session as session:
        measurements = get_measurements(session, obs_tag)
        observation, observer, location, photometer = get_observation_details(session, obs_tag)
        c1, c2 = st.columns(2)
        with c1:
            st.write("### Observer")
            st.dataframe(
                pd.DataFrame(
                    observer.to_dict().items(),
                    columns=("Name", "Value"),
                ),
                hide_index=True,
            )
            st.write("### Location")
            st.dataframe(
                pd.DataFrame(
                    location.to_dict().items(),
                    columns=("Name", "Value"),
                ),
                hide_index=True,
            )
        with c2:
            st.write("### Observation")
            st.dataframe(
                pd.DataFrame(
                    observation.to_dict().items(),
                    columns=("Name", "Value"),
                ),
                hide_index=True,
            )
            st.write("### Photometer")
            st.dataframe(
                pd.DataFrame(
                    photometer.to_dict().items(),
                    columns=("Name", "Value"),
                ),
                hide_index=True,
            )
        st.write("## Measurements")
        st.dataframe([m.to_dict() for m in measurements])

obs_tag = obs_init(conn)
if obs_tag:
    obs_view_details(conn, obs_tag)