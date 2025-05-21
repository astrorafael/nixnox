import os
import streamlit as st

def ttl() -> str:
	"""get the Cache Time to live as a function of the development environment"""
	env = os.environ.get("NX_ENV", "prod")
	return st.secrets["cache"][env]["ttl"]
