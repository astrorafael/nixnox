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

from nixnox.lib.dbase.model import (
    Photometer,
    Observer,
    Observation,
    Location,
    Measurement,
    Time,
    Date,
)


def sqa_logging(verbose: bool) -> None:
    if verbose:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
        # This is needed, otherwise aiosqlite msgs will jump in
        logging.getLogger("aiosqlite").setLevel(logging.INFO)
    else:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


sqa_logging(True)
conn = st.connection('nixnox_db', type='sql')

with conn.session as session:
	q = select(Observation)
	observations = session.scalars(q).all()

st.dataframe(observations)
