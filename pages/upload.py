# ---------------
# Standard library
# ---------------
import os
import time

# ---------
# STREAMLIT
# ---------

import streamlit as st
import streamlit.logger
# ---------------
# Other libraries
# ---------------

import nixnox.lib.ecsv as nx

log = streamlit.logger.get_logger(__name__)

# Database connection
conn = st.connection("env:NX_ENV", type="sql")

st.title("Upload TAS files to database")

data = st.file_uploader("*ECSV File only!*", type=["ecsv"])
if data:
    with conn.session as session:
        try:
            observation = nx.uploader(session, data, log=log)
        except nx.excp.AlreadyExistsError as e:
            observation = e.args[0]
            st.error("Error: observation already exists in the database", icon="🚨")
        except Exception as e:
            st.write(e)
            st.error("Error: Invalid file format", icon="🚨")
        else:
            st.info(f"Observation upload to database: {observation.identifier}", icon="ℹ️")
            time.sleep(2)
            del st.session_state.result_table
            st.switch_page(os.path.join("pages", "home.py"))
