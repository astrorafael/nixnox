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

from astropy.table import Table
import nixnox.web.dbase as db
import nixnox.web.mpl as mpl

# ============
# PAGE OBJECTS
# ============

conn = st.connection("nixnox_db", type="sql")
obs_tag = st.session_state.obs_tag


@st.cache_data(ttl=60)
def get_observation_details(_conn, obs_tag: str):
    with _conn.session as session:
        return db.obs_details(session, obs_tag)


@st.cache_data(ttl=60)
def get_measurements(_conn, obs_tag: str):
    with _conn.session as session:
        return db.obs_measurements(session, obs_tag)


observation, observer, location, photometer = get_observation_details(conn, obs_tag)
measurements = get_measurements(conn, st.session_state.obs_tag)
measurements = Table([m.to_dict() for m in measurements])

@st.cache_data(ttl=60)
def plot(tag: str, azimuth, zenital, magnitude):
    return mpl.plot(obs_tag, azimuth, zenital, magnitude)

figure = plot(obs_tag, measurements["azimuth"], measurements["zenital"], measurements["magnitude"])
st.write("## Night Sky Brightness Plot")
st.pyplot(figure)
