# ----------------
# Standard library
# ----------------

import os

# ---------
# STREAMLIT
# ---------
import streamlit as st

# -------------------
# Third party library
# -------------------

import pandas as pd
import nixnox.web.dbase as db
from nixnox.web.streamlit import ttl

# ============
# PAGE OBJECTS
# ============

conn = st.connection("env:NX_ENV", type="sql")


@st.cache_data(ttl=ttl())
def get_observation_details(_session, obs_tag: str):
    return db.obs_details(_session, obs_tag)


@st.cache_data(ttl=ttl())
def get_measurements(_session, obs_tag: str):
        return db.obs_measurements(_session, obs_tag)


st.write("## Observation Details")
if "obs_tag" not in st.session_state:
    st.warning("### Please, select an observation in the home page", icon="⚠️")
else:
    obs_tag = st.session_state.obs_tag
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
