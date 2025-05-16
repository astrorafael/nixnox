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
def observation_details(_conn, obs_tag: str):
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

with st.container(border=True):
    observation, observer, location, photometer = observation_details(conn, st.session_state.obs_tag)
    df = pd.DataFrame(observation.to_dict().items(), columns=("Name", "Value"))
    st.dataframe(pd.DataFrame(observation.to_dict().items(), columns=("Name", "Value")))
    st.dataframe(pd.DataFrame(location.to_dict().items(), columns=("Name", "Value")))
    st.dataframe(pd.DataFrame(observer.to_dict().items(), columns=("Name", "Value")))
    st.dataframe(pd.DataFrame(photometer.to_dict().items(), columns=("Name", "Value")))

   