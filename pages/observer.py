# ------------------
# Standard libraries
# ------------------
from typing import Callable
from datetime import date

import streamlit as st
from streamlit.logger import get_logger

import nixnox.web.dbase as db
from nixnox.web.streamlit import ttl
from nixnox.lib import ObserverType, PhotometerModel


# ----------------
# Global variables
# ----------------

log = get_logger(__name__)
conn = st.connection("env:NX_ENV", type="sql")


# ---------------------
# Convenience functions
# ---------------------


@st.cache_data(ttl=ttl())
def obs_summary(_conn, conditions):
    with _conn.session as session:
        return db.obs_summary_search(session, conditions)


@st.cache_data(ttl=ttl())
def obs_nsummaries(_conn):
    with _conn.session as session:
        return db.obs_nsummaries(session)


@st.cache_data(ttl=ttl())
def get_observation_as_ecsv(_conn, obs_tag: str) -> str:
    with _conn.session as session:
        return db.obs_export(session, obs_tag)

# ----------------------



