import logging

import streamlit as st
from sqlalchemy import select


from nixnox.lib import (
    ObserverType,
    PhotometerModel,
    Temperature,
    Humidity,
    Timestamp,
    Coordinates,
    ValidState,
)


@st.cache_resource
def database_models():
    from nixnox.lib.dbase.model import (
        Photometer,
        Observer,
        Observation,
        Location,
        Measurement,
        Date,
        Time,
      
    )
    return Photometer, Observer, Observation, Location,  Date, Time, Measurement

def sqa_logging(verbose: bool) -> None:
    if verbose:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
        # This is needed, otherwise aiosqlite msgs will jump in
        logging.getLogger("aiosqlite").setLevel(logging.INFO)
    else:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


conn = st.connection('nixnox_db', type='sql')

Photometer, Observer, Observation, Location, Date, Time, Measurement = database_models()

def available_observations(conn):
    with conn.session as session:
    	q = (select(Observation.identifier, Date.sql_date,  Observer.name, Location.place).distinct()
        .select_from(Measurement)
        .join(Date,  Measurement.date_id == Date.date_id)
        .join(Observation, Measurement.obs_id == Observation.obs_id)
        .join(Location, Measurement.observer_id == Location.location_id)
        .join(Observer, Measurement.observer_id == Observer.observer_id)
        )
    	return session.execute(q).all()

st.write("**Available observations**")
st.dataframe(available_observations(conn))
