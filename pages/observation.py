import streamlit as st
import pandas as pd

from sqlalchemy import select


from nixnox.lib.dbase.model import (
    Photometer,
    Observer,
    Observation,
    Location,
    Measurement,
)

conn = st.connection("nixnox_db", type="sql")

@st.cache_data(ttl=60)
def db_observation_details(_conn, obs_tag: str):
    with _conn.session as session:
        q = (
            select(
                Observation,
                Observer,
                Location,
                Photometer,
            )
            .select_from(Measurement)
            .distinct()
            .join(Observation, Measurement.obs_id == Observation.obs_id)
            .join(Location, Measurement.observer_id == Location.location_id)
            .join(Observer, Measurement.observer_id == Observer.observer_id)
            .join(Photometer, Measurement.phot_id == Photometer.phot_id)
            .where(Observation.identifier == obs_tag)
        )
        return session.execute(q).one()

@st.cache_data(ttl=60)
def db_measurements(_conn, obs_tag: str):
    with _conn.session as session:
        q = (
            select(Measurement)
            .select_from(Measurement)
            .join(Observation, Measurement.obs_id == Observation.obs_id)
            .join(Location, Measurement.observer_id == Location.location_id)
            .join(Observer, Measurement.observer_id == Observer.observer_id)
            .join(Photometer, Measurement.phot_id == Photometer.phot_id)
            .where(Observation.identifier == obs_tag)
        )
        return session.scalars(q).all()

observation, observer, location, photometer = db_observation_details(conn, st.session_state.obs_tag)
measurements = db_measurements(conn, st.session_state.obs_tag)

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