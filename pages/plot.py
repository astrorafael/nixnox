# ----------------
# Standard library
# ----------------

from io import BytesIO
from threading import RLock

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
from nixnox.web.streamlit import ttl

# ============
# PAGE OBJECTS
# ============

# According to dthe streamlit documebtation:
# """Matplotlib doesn't work well with threads. 
#    So if you're using Matplotlib you should wrap your code with locks. 
#    This Matplotlib bug is more prominent when you deploy and share your apps 
#    because you're more likely to get concurrent users then.""""

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


st.write("## Night Sky Brightness Plot")
if "obs_tag" not in st.session_state:
    st.warning("### Please, select an observation in the home page", icon="⚠️")
else:

    obs_tag = st.session_state.obs_tag
    with conn.session as session:
        observation, observer, location, photometer = get_observation_details(session, obs_tag)
        measurements = get_measurements(session, st.session_state.obs_tag)
        measurements = Table([m.to_dict() for m in measurements])
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
