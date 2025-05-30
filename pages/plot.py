# ----------------
# Standard library
# ----------------

from io import BytesIO
from threading import RLock

# ---------
# STREAMLIT
# ---------

import streamlit as st
import pandas as pd
import streamlit as st
from streamlit.connections import SQLConnection
from streamlit import logger


# -------------------
# Third party library
# -------------------

from astropy.table import Table

import nixnox.web.dbase as db
import nixnox.web.mpl as mpl
from nixnox.web.streamlit import ttl


def obs_init(conn: SQLConnection) -> str | None:
    selected = st.session_state["obs_summ"]["selected"]
    if not selected:
        st.warning("### Please, select an observation in the home page", icon="⚠️")
    result = st.session_state["obs_summ"]["selected"][1] if selected else None
    return result

# ============
# PAGE OBJECTS
# ============

# According to dthe streamlit documebtation:
# """Matplotlib doesn't work well with threads. 
#    So if you're using Matplotlib you should wrap your code with locks. 
#    This Matplotlib bug is more prominent when you deploy and share your apps 
#    because you're more likely to get concurrent users then.""""


log = logger.get_logger(__name__)
conn = st.connection("env:NX_ENV", type="sql")

@st.cache_data(ttl=ttl())
def get_observation_details(_session, obs_tag: str):
    return db.obs_details(_session, obs_tag)


@st.cache_data(ttl=ttl())
def get_measurements(_session, obs_tag: str):
    return db.obs_measurements(_session, obs_tag)


@st.cache_data(ttl=ttl())
def plot(
    obs_tag: str, azimuth, zenital, magnitude, _observation, _observer, _location, _photometer
):
    return mpl.plot(
        obs_tag,
        azimuth,
        zenital,
        magnitude,
        observation=_observation,
        observer=_observer,
        location=_location,
        photometer=_photometer,
    )

def plot_init(conn: SQLConnection) -> str | None:
    st.title("Night Sky Brightness Plot")
    selected = st.session_state["obs_summ"]["selected"]
    if not selected:
        st.warning("### Please, select an observation in the home page", icon="⚠️")
    result = st.session_state["obs_summ"]["selected"][1] if selected else None
    return result

def plot_view(conn: SQLConnection, obs_tag: str) -> None:
    with conn.session as session:
        observation, observer, location, photometer = db.obs_details(session, obs_tag)
        measurements = get_measurements(session, obs_tag)
        measurements = Table([m.to_dict() for m in measurements])
        st.write(measurements)
        with RLock():
            figure = plot(
                obs_tag,
                measurements["azimuth"],
                measurements["zenital"],
                measurements["magnitude"],
                observation.to_dict(),
                observer.to_dict(),
                location.to_dict(),
                photometer.to_dict(),
            )
            output = BytesIO()
            figure.savefig(output)
            st.download_button(
                label=f"Download Plot: *{obs_tag}*",
                data=output.getvalue(),
                file_name=f"{obs_tag}.png",
                mime="image/png",
                icon=":material/download:",
            )
            st.pyplot(figure)


obs_tag = plot_init(conn)
if obs_tag:
    plot_view(conn, obs_tag)