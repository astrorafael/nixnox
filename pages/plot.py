# ----------------
# Standard library
# ----------------

from io import BytesIO

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

@st.cache_data(ttl=60)
def get_observation_details(_conn, obs_tag: str):
    with _conn.session as session:
        return db.obs_details(session, obs_tag)


@st.cache_data(ttl=60)
def get_measurements(_conn, obs_tag: str):
    with _conn.session as session:
        return db.obs_measurements(session, obs_tag)



@st.cache_data(ttl=60)
def plot(obs_tag: str, azimuth, zenital, magnitude):
    return mpl.plot(obs_tag, azimuth, zenital, magnitude)

st.write("## Night Sky Brightness Plot")
if  "obs_tag" not in st.session_state:
    st.warning("### Please, select an observation in the home page")
else:
    obs_tag = st.session_state.obs_tag
    observation, observer, location, photometer = get_observation_details(conn, obs_tag)
    measurements = get_measurements(conn, st.session_state.obs_tag)
    measurements = Table([m.to_dict() for m in measurements])
    figure = plot(obs_tag, measurements["azimuth"], measurements["zenital"], measurements["magnitude"])
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
