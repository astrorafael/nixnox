# ------------------
# Standard libraries
# ------------------

from collections import defaultdict
from typing import Optional, Any, Tuple
from datetime import datetime, date

# ---------------------
# Thirs party libraries
# ---------------------

import streamlit as st
from streamlit.connections import SQLConnection
from streamlit import logger

from pydantic import BaseModel, ValidationError, EmailStr, HttpUrl

# -----------
# own library
# -----------

import nixnox.web.dbase as db
from nixnox.lib import ValidState

# ---------------
# Pydantic Models
# ---------------

DEF_ORG_TEXT = "<Enter organization name here>"
DEF_PERSON_TEXT = "<Enter your full name here>"


class NameField(BaseModel):
    name: str


class AcronymField(BaseModel):
    org_acronym: Optional[str] = None


class WebField(BaseModel):
    org_website_url: Optional[HttpUrl] = None


class EmailField(BaseModel):
    org_email: Optional[EmailStr] = None


class NickField(BaseModel):
    nickname: Optional[str] = None


class AffilField(BaseModel):
    affiliation: Optional[str] = None


class ValidDateField(BaseModel):
    valid_date: Optional[datetime] = None


class ValidStateField(BaseModel):
    valid_state: Optional[ValidState] = None


# ----------------
# Global variables
# ----------------

log = logger.get_logger(__name__)
log.info("ENTERING PAGE")

conn: SQLConnection = st.connection("env:NX_ENV", type="sql")

org_default_form = {
    "name": DEF_ORG_TEXT,
    "org_acronym": None,
    "org_website_url": None,
    "org_email": None,
}

person_default_form = {
    "observer_id": None,
    "name": DEF_PERSON_TEXT,
    "nickname": None,
    "affiliation": None,
    "valid_since": date.today(),
    "valid_until": None,
    "valid_state": ValidState.CURRENT,
    "affiliated": False,
}


# ---------------------
# Convenience functions
# ---------------------


def person_init(conn: SQLConnection) -> None:
    with conn.session as session:
        if "person" not in st.session_state:
            st.session_state["person"] = defaultdict(dict)
            st.session_state["person"]["table"] = db.persons_lookup(session)
            st.session_state["person"]["selected"] = None
            st.session_state["person"]["form"].update(person_default_form)
            st.session_state["person"]["delete_button"] = False
            st.session_state["person"]["clone_button"] = False


def org_init(conn: SQLConnection) -> None:
    with conn.session as session:
        if "org" not in st.session_state:
            st.session_state["org"] = defaultdict(dict)
            st.session_state["org"]["table"] = db.orgs_lookup(session)
            st.session_state["org"]["selected"] = None
            st.session_state["org"]["form"].update(org_default_form)
            st.session_state["org"]["delete_button"] = False


def on_person_selected() -> None:
    """Person dataframe callback function"""
    if st.session_state.PersonDataFrame.selection.rows:
        # Clicked one row
        row = st.session_state.PersonDataFrame.selection.rows[0]
        # Get the whole row
        info = st.session_state["person"]["table"][row]
        new_form_data = {
            "observer_id": info[0],
            "name": info[1],
            "nickname": info[2],
            "affiliated": info[3],
            "valid_state": info[4],
            "valid_since": info[5],
            "valid_until": info[6],
        }
        st.session_state["person"]["selected"] = info
        st.session_state["person"]["delete_button"] = True
        st.session_state["person"]["clone_button"] = True
        st.session_state["person"]["form"].update(new_form_data)
    else:
        # No rows clicked by unclicking
        st.session_state["person"]["selected"] = None
        st.session_state["person"]["delete_button"] = False
        st.session_state["person"]["clone_button"] = False
        st.session_state["person"]["form"].update(person_default_form)


def on_org_selected() -> None:
    """organization dataframe callback function"""
    if st.session_state.OrganizationDataFrame.selection.rows:
        row = st.session_state.OrganizationDataFrame.selection.rows[0]
        # Get the whole row
        info = st.session_state["org"]["table"][row]
        new_form_data = {
            "name": info[0],
            "org_acronym": info[1],
            "org_website_url": info[2],
            "org_email": info[3],
        }
        st.session_state["org"]["selected"] = info
        st.session_state["org"]["delete_button"] = True
        st.session_state["org"]["form"].update(new_form_data)
    else:
        st.session_state["org"]["selected"] = None
        st.session_state["org"]["delete_button"] = False
        st.session_state["org"]["form"].update(org_default_form)


def on_person_delete(**kwargs):
    conn = kwargs["conn"]
    selected = st.session_state["person"]["selected"]
    if selected:
        observer_id = selected[0]
        with conn.session as session:
            db.person_delete(session, observer_id)
        st.session_state["person"]["selected"] = None
        st.session_state["person"]["delete_button"] = False
        st.session_state["person"]["table"] = db.persons_lookup(session)
        st.session_state["person"]["form"].update(person_default_form)


def on_person_clone(**kwargs):
    conn = kwargs["conn"]
    selected = st.session_state["person"]["selected"]
    if selected:
        with conn.session as session:
            db.person_clone(
                session,
                name=selected[1],
                nickname=selected[2],
                affiliation=selected[3],
                valid_state=selected[4],
                valid_since=selected[5],
                valid_until=selected[6],
            )
        st.session_state["person"]["selected"] = None
        st.session_state["person"]["clone_button"] = False
        st.session_state["person"]["table"] = db.persons_lookup(session)
        st.session_state["person"]["form"].update(person_default_form)


def on_org_delete(**kwargs):
    conn = kwargs["conn"]
    selected = st.session_state["org"]["selected"]
    if selected:
        name = selected[0]
        with conn.session as session:
            db.org_delete(session, name)
        st.session_state["org"]["selected"] = None
        st.session_state["org"]["delete_button"] = False
        st.session_state["org"]["table"] = db.orgs_lookup(session)
        st.session_state["org"]["form"].update(org_default_form)


# ---------------
# Views rendering
# ----------------


def org_view_table(conn: SQLConnection, table: Any) -> None:
    with st.expander("🏢 Existing Organizations"):
        st.dataframe(
            table,
            key="OrganizationDataFrame",
            hide_index=True,
            selection_mode="single-row",
            on_select=on_org_selected,
        )
        st.button(
            "Delete",
            icon="🗑️",
            key="OrganizationDeleteButton",
            type="primary",
            on_click=on_org_delete,
            kwargs={"conn": conn},
            disabled=not st.session_state["org"]["delete_button"],
        )


def person_view_table(conn: SQLConnection, table: Any) -> None:
    with st.expander("👤 Existing Persons"):
        st.dataframe(
            table,
            key="PersonDataFrame",
            hide_index=True,
            selection_mode="single-row",
            on_select=on_person_selected,
        )
        c1, c2 = st.columns(2)
        with c1:
            st.button(
                "Clone",
                icon="🗑️",
                type="secondary",
                key="PersonCloneButton",
                on_click=on_person_clone,
                kwargs={"conn": conn},
                disabled=not st.session_state["person"]["clone_button"],
            )

        with c2:
            st.button(
                "Delete",
                icon="🗑️",
                type="primary",
                key="PersonDeleteButton",
                on_click=on_person_delete,
                kwargs={"conn": conn},
                disabled=not st.session_state["person"]["delete_button"],
            )


def view_affiliation(
    conn: SQLConnection, form_data: dict[str, Any]
) -> Tuple[date, date, ValidState, str]:
    with conn.session as session:
        available_affiliations = db.orgs_names_lookup(session)
        affiliation = db.person_affiliation(session, form_data["observer_id"])
    try:
        index = available_affiliations.index(affiliation)
    except ValueError:
        index = None
    selected_affil = st.selectbox("Organization", options=available_affiliations, index=index)
    c1, c2, c3 = st.columns(3)
    with c1:
        ancient = date(1940, 1, 1)
        forever = date(2099, 12, 31)
        since = st.date_input(
            "Since",
            value=form_data["valid_since"],
            min_value=ancient,
            max_value=forever,
        )
    with c2:
        until = st.date_input(
            "Until",
            value=form_data["valid_until"],
            min_value=ancient,
            max_value=forever,
        )
    with c3:
        states = [s.value for s in ValidState]
        j = states.index(form_data["valid_state"])  # No need to check boundaries
        state = st.selectbox("Affiliation state", options=states, index=j)
    return since, until, state, selected_affil


def person_view_form(conn: SQLConnection, form_data: dict[str]) -> None:
    with st.form("person_data_entry_form", clear_on_submit=True):
        st.header("👤 Person Data Entry")
        c1, c2 = st.columns(2)
        with c1:
            observer_id = st.number_input("Id (read only)", value=form_data["observer_id"], disabled=True)
        with c2:
            nickname = st.text_input("Nickname", value=form_data["nickname"])
        try:
            nickname = NickField(nickname=nickname)
        except ValidationError:
            st.error("❌ nickname is not valid")
            nickname = None
        name = st.text_input("Full Name", value=form_data["name"])
        try:
            name = NameField(name=name)
        except ValidationError:
            st.warning("⚠️ please, change name")
            name = None
        st.subheader("Affiliation")
        since, until, state, selected_affil = view_affiliation(conn, form_data)
        submitted = st.form_submit_button(
            "**Submit**",
            help="Submit Observer data to database",
            type="primary",
            use_container_width=False,
        )
        all_valid = all(map(lambda x: x is not None, [name, nickname]))
        if submitted and all_valid:
            with conn.session as session:
                db.person_update(
                    session, observer_id, name.name, nickname.nickname, selected_affil, since, until, state
                )
                st.session_state["person"]["table"] = db.persons_lookup(session)
                st.session_state["person"]["selected"] = None
                st.session_state["person"]["delete_button"] = False
            st.rerun()
        elif not all_valid:
            st.error("Not Updated!")


def org_view_form(conn: SQLConnection, form_data: dict[str]) -> None:
    with st.form("organization_data_entry_form", clear_on_submit=True):
        st.header("🏢 Organization Data Entry")
        name = st.text_input("Organization Full Name", value=form_data["name"])
        try:
            name = NameField(name=name)
        except ValidationError:
            st.warning("⚠️ please, change name")
            name = None
        org_acronym = st.text_input("Acronym", value=form_data["org_acronym"])
        try:
            org_acronym = AcronymField(org_acronym=org_acronym)
        except ValidationError:
            st.error("❌ org_acronym is not valid")
            org_acronym = None
        org_website_url = st.text_input("🌎 Web Site", value=form_data["org_website_url"])
        try:
            org_website_url = WebField(org_website_url=org_website_url)
        except ValidationError:
            st.error("❌ URL format is not valid")
            org_website_url = None
        org_email = st.text_input("📧 Email", value=form_data["org_email"])
        try:
            org_email = EmailField(org_email=org_email)
        except ValidationError:
            st.error("❌ org_email format is not valid")
            org_email = None
        submitted = st.form_submit_button(
            "**Submit**",
            help="Submit Organization data to database",
            type="primary",
            # on_click=on_org_form_submitted,
            use_container_width=False,
        )
        all_valid = all(map(lambda x: x is not None, [name, org_acronym, org_website_url, org_email]))
        if submitted and all_valid:
            with conn.session as session:
                db.org_update(
                    session, name.name, org_acronym.org_acronym, str(org_website_url.org_website_url), org_email.org_email
                )
                st.session_state["org"]["table"] = db.orgs_lookup(session)
                st.session_state["org"]["selected"] = None
                st.session_state["org"]["delete_button"] = False
            st.rerun()
        elif not all_valid:
            st.error("Not Updated!")


def view_all(conn: SQLConnection) -> None:
    st.title("✨ 🔭 Observer Data Entry")
    st.write(""" 
        To add a new observer:

        1. Make sure that the organization he/she is affiliated to already exists. 
        2. If not exists, then **add the organization first**.
        3. Add the observer.
        """)
    c1, c2 = st.columns(2)
    with c1:
        person_view_table(conn, st.session_state["person"]["table"])
        person_view_form(conn, st.session_state["person"]["form"])
    with c2:
        org_view_table(conn, st.session_state["org"]["table"])
        org_view_form(conn, st.session_state["org"]["form"])


org_init(conn)
person_init(conn)
view_all(conn)
