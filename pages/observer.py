# ------------------
# Standard libraries
# ------------------
from typing import Optional, Callable
from datetime import datetime, date

import streamlit as st
from streamlit.logger import get_logger

from pydantic import BaseModel, ValidationError, validator, EmailStr, HttpUrl

import nixnox.web.dbase as db
from nixnox.web.streamlit import ttl
from nixnox.lib import ObserverType, ValidState

# ---------------
# Pydantic Models
# ---------------


class NameField(BaseModel):
    name: str


class NickField(BaseModel):
    nickname: Optional[str]


class AffilField(BaseModel):
    affiliation: Optional[str]


class ValidDateField(BaseModel):
    valid_date: Optional[datetime]


class ValidStateField(BaseModel):
    valid_state: Optional[ValidState]


class AcronymField(BaseModel):
    acronym: Optional[str]


class WebField(BaseModel):
    website_url: Optional[HttpUrl]


class EmailField(BaseModel):
    email: Optional[EmailStr]


class PersonForm(BaseModel):
    name: str
    nickname: Optional[str]
    affiliation: Optional[str]
    valid_since: Optional[datetime]
    valid_until: Optional[datetime]
    valid_state: Optional[ValidState]


class OrganizationForm(BaseModel):
    name: str
    acronym: Optional[str]
    website_url: Optional[HttpUrl]
    email: Optional[EmailStr]


# ----------------
# Global variables
# ----------------

log = get_logger(__name__)
conn = st.connection("env:NX_ENV", type="sql")

person_form_data = {
    "name": "Enter your full name here",
    "nickname": None,
    "affiliation": None,
    "valid_since": date.today(),
    "valid_until": None,
    "valid_state": ValidState.CURRENT,
    "submitted": False,
}

org_form_data = {
    "name": "Enter organization name here",
    "acronym": None,
    "website_url": None,
    "email": None,
    "submitted": False,
}

st.session_state.person_form_data = person_form_data
st.session_state.org_form_data = org_form_data
st.session_state.persons_table = None
st.session_state.orgs_table = None
st.session_state.selected_person_name = None
st.session_state.selected_org_name = None

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


def on_selected_person() -> None:
    if st.session_state.PersonDF.selection.rows:
        log.debug(
            "st.session_state.PersonDF.selection.rows = %s",
            st.session_state.PersonDF.selection.rows,
        )
        row = st.session_state.PersonDF.selection.rows[0]
        log.debug("st.session_state.result_table[row] = %s", st.session_state.persons_table[row])
        # name is the first item in the row
        st.session_state.selected_person_name = st.session_state.persons_table[row][0]
    
def on_selected_org() -> None:
    if st.session_state.OrganizationDF.selection.rows:
        log.debug(
            "st.session_state.OrganizationDF.selection.rows = %s",
            st.session_state.OrganizationDF.selection.rows,
        )
        row = st.session_state.OrganizationDF.selection.rows[0]
        log.debug("st.session_state.result_table[row] = %s", st.session_state.orgs_table[row])
        # name is the first item in the row
        st.session_state.selected_org_name = st.session_state.orgs_table[row][0]

# ----------------------


def view_person_list() -> None:
    with st.expander("👤 Existing Persons"):
        with conn.session as session:
            st.session_state.persons_table = db.persons_lookup(session)
            st.dataframe(
                st.session_state.persons_table,
                key="PersonDF",
                hide_index=True,
                on_select=on_selected_person,
                selection_mode="single-row",
            )


def view_org_list() -> None:
    with st.expander("🏢 Existing Organnizations"):
        with conn.session as session:
            st.session_state.orgs_table = db.orgs_lookup(session)
            st.dataframe(
                st.session_state.orgs_table,
                key="OrganizationDF",
                hide_index=True,
                on_select=on_selected_org,
                selection_mode="single-row",
            )


def view_person() -> None:
    with st.form("person_data_entry_form", clear_on_submit=False):
        st.header("👤 Person Data Entry")
        name = st.text_input("Full Name", value=st.session_state.person_form_data["name"])
        try:
            name = NameField(name=name)
        except ValidationError as e:
            st.error(str(e))
        nickname = st.text_input("Nickname", value=st.session_state.person_form_data["nickname"])
        try:
            nickname = NickField(nickname=nickname)
        except ValidationError as e:
            st.error(str(e))
        st.form_submit_button(
            "**Submit**",
            help="Sumbit Observer data to database",
            type="primary",
            use_container_width=False,
        )


def view_organization() -> None:
    with st.form("organization_data_entry_form", clear_on_submit=False):
        st.header("🏢 Organization Data Entry")
        name = st.text_input("Organization Full Name", value=st.session_state.org_form_data["name"])
        try:
            name = NameField(name=name)
        except ValidationError as e:
            st.error(str(e))
        acronym = st.text_input("Acronym", value=st.session_state.org_form_data["acronym"])
        try:
            acronym = AcronymField(acronym=acronym)
        except ValidationError as e:
            st.error(str(e))
        website_url = st.text_input(
            "🌎 Web Site", value=st.session_state.org_form_data["website_url"]
        )
        try:
            website_url = WebField(website_url=website_url)
        except ValidationError as e:
            st.error(str(e))
        email = st.text_input("📧 Email", value=st.session_state.org_form_data["email"])
        try:
            email = EmailField(email=email)
        except ValidationError as e:
            st.error(str(e))
        st.form_submit_button(
            "**Submit**",
            help="Sumbit Organization database",
            type="primary",
            use_container_width=False,
        )


def view_all() -> None:
    c1, c2 = st.columns(2)
    with c1:
        view_person_list()
        view_person()
    with c2:
        view_org_list()
        view_organization()


st.title("✨ 🔭 Observer Data Entry")  # Initialize session state
view_all()
