# ------------------
# Standard libraries
# ------------------
from typing import Optional, Any, Iterable, Callable
from datetime import datetime, date

import streamlit as st
from streamlit.logger import get_logger

from pydantic import BaseModel, ValidationError, validator, EmailStr, HttpUrl

import nixnox.web.dbase as db
from nixnox.web.streamlit import ttl
from nixnox.lib import ValidState

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
    "affiliated": False,
    "submitted": False,
}

org_form_data = {
    "name": "Enter organization name here",
    "acronym": None,
    "website_url": None,
    "email": None,
    "submitted": False,
}


@st.cache_data(ttl=ttl())
def affiliations(_conn) -> Iterable[str]:
    with _conn.session as session:
        return db.orgs_names_lookup(session)

@st.cache_data(ttl=ttl())
def person_affiliation(_conn, name) -> Optional[str]:
    with _conn.session as session:
        return db.person_affiliation(session, name)

def init_state_person() -> None:
    # Table above
    st.session_state.persons_table = None
    st.session_state.selected_person = None
    # Form below
    st.session_state.person_form_data = person_form_data


def init_state_org() -> None:
    # Table above
    st.session_state.orgs_table = None
    st.session_state.selected_org = None
    # Form below
    st.session_state.org_form_data = org_form_data


# ---------------------
# Convenience functions
# ---------------------

def on_selected_person() -> None:
    """Person dataframe callback function"""
    if st.session_state.PersonDF.selection.rows:
        # Clicked one row
        row = st.session_state.PersonDF.selection.rows[0]
        # Get the whole row
        info = st.session_state["persons_table"][row]
        st.session_state["selected_person"] = info
        new_form_data = {
            "name": info[0],
            "nickname": info[1],
            "affiliated": info[2],
            "valid_state": info[3],
            "valid_since": info[4],
            "valid_until": info[5],
        }
        st.session_state["person_form_data"].update(new_form_data)
    else:
        # No rows clicked by unclicking
        del st.session_state["selected_person"]
        del st.session_state["person_form_data"]


def on_selected_org() -> None:
    """organization dataframe callback function"""
    if st.session_state.OrganizationDF.selection.rows:
        row = st.session_state.OrganizationDF.selection.rows[0]
        # Get the whole row
        info = st.session_state["orgs_table"][row]
        st.session_state["selected_org"] = info
        new_form_data = {
            "name": info[0],
            "acronym": info[1],
            "website_url": info[2],
            "email": info[3],
        }
        st.session_state["org_form_data"].update(new_form_data)
    else:
        del st.session_state["selected_org"]
        del st.session_state["org_form_data"]


# ----------------------


def view_person_list(table: Any) -> None:
    with st.expander("👤 Existing Persons"):
        with conn.session as session:
            st.session_state.persons_table = db.persons_lookup(session)
            st.dataframe(
                table,
                key="PersonDF",
                hide_index=True,
                selection_mode="single-row",
                on_select=on_selected_person,
            )


def view_org_list(table: Any) -> None:
    with st.expander("🏢 Existing Organizations"):
        with conn.session as session:
            st.session_state.orgs_table = db.orgs_lookup(session)
            st.dataframe(
                table,
                key="OrganizationDF",
                hide_index=True,
                selection_mode="single-row",
                on_select=on_selected_org,
            )


def view_affiliation(form_data) -> None:
    available_aff = affiliations(conn)
    aff = person_affiliation(conn, form_data["name"])
    try:
        index = available_aff.index(aff)
    except ValueError:
        index=None
    c1, c2 = st.columns(2)
    with c1:
        ancient = date(2000, 1, 1)
        forever = date(2999, 12, 31)
        st.date_input(
            "Since",
            value=form_data["valid_since"],
            min_value=ancient,
            max_value="today",
        )
        st.date_input(
            "Until",
            value=form_data["valid_since"],
            min_value="today",
            max_value=forever,
        )
    with c2:
        option = st.selectbox("Organization", options=available_aff, index=index)


def view_person(form_data: dict[str]) -> None:
    with st.form("person_data_entry_form", clear_on_submit=True):
        st.header("👤 Person Data Entry")
        name = st.text_input("Full Name", value=form_data["name"])
        try:
            name = NameField(name=name)
        except ValidationError as e:
            st.error(str(e))
        nickname = st.text_input("Nickname", value=form_data["nickname"])
        try:
            nickname = NickField(nickname=nickname)
        except ValidationError as e:
            st.error(str(e))
        st.divider()
        st.subheader("Affiliation")
        view_affiliation(form_data)
        st.form_submit_button(
            "**Submit**",
            help="Sumbit Observer data to database",
            type="primary",
            use_container_width=False,
        )


def view_organization(form_data: dict[str]) -> None:
    with st.form("organization_data_entry_form", clear_on_submit=True):
        st.header("🏢 Organization Data Entry")
        name = st.text_input("Organization Full Name", value=form_data["name"])
        try:
            name = NameField(name=name)
        except ValidationError as e:
            st.error(str(e))
        acronym = st.text_input("Acronym", value=form_data["acronym"])
        try:
            acronym = AcronymField(acronym=acronym)
        except ValidationError as e:
            st.error(str(e))
        website_url = st.text_input("🌎 Web Site", value=form_data["website_url"])
        try:
            website_url = WebField(website_url=website_url)
        except ValidationError as e:
            st.error(str(e))
        email = st.text_input("📧 Email", value=form_data["email"])
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
    st.title("✨ 🔭 Observer Data Entry")  # Initialize session state
    c1, c2 = st.columns(2)
    with c1:
        view_person_list(st.session_state["persons_table"])
        view_person(st.session_state["person_form_data"])
    with c2:
        view_org_list(st.session_state["orgs_table"])
        view_organization(st.session_state["org_form_data"])


if "person_form_data" not in st.session_state:
    init_state_person()
if "org_form_data" not in st.session_state:
    init_state_org()
view_all()
