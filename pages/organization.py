# ------------------
# Standard libraries
# ------------------

from collections import defaultdict
from typing import Optional, Any

import streamlit as st
from streamlit.connections import SQLConnection
from streamlit.logger import get_logger

from pydantic import BaseModel, ValidationError, EmailStr, HttpUrl

import nixnox.web.dbase as db


# ---------------
# Pydantic Models
# ---------------


DEF_ORG_TEXT = "<Enter organization name here>"


class NameField(BaseModel):
    name: str


class AcronymField(BaseModel):
    acronym: Optional[str] = None


class WebField(BaseModel):
    website_url: Optional[HttpUrl] = None


class EmailField(BaseModel):
    email: Optional[EmailStr] = None


# ----------------
# Global variables
# ----------------

log = get_logger(__name__)
conn: SQLConnection = st.connection("env:NX_ENV", type="sql")
default_form = {
    "name": DEF_ORG_TEXT,
    "acronym": None,
    "website_url": None,
    "email": None,
}

# ---------------------
# Convenience functions
# ---------------------


def org_init(conn: SQLConnection) -> None:
    with conn.session as session:
        if "org" not in st.session_state:
            st.session_state["org"] = defaultdict(dict)
            st.session_state["org"]["table"] = db.orgs_lookup(session)
            st.session_state["org"]["selected"] = None
            st.session_state["org"]["form"] = default_form
            st.session_state["org"]["form_validated"] = False
            st.session_state["org"]["delete_button"] = False


def on_org_selected() -> None:
    """organization dataframe callback function"""
    if st.session_state.OrganizationDF.selection.rows:
        row = st.session_state.OrganizationDF.selection.rows[0]
        # Get the whole row
        info = st.session_state["org"]["table"][row]
        new_form_data = {
            "name": info[0],
            "acronym": info[1],
            "website_url": info[2],
            "email": info[3],
        }
        st.session_state["org"]["selected"] = info
        st.session_state["org"]["delete_button"] = True
        st.session_state["org"]["form"].update(new_form_data)
    else:
        st.session_state["org"]["selected"] = None
        st.session_state["org"]["delete_button"] = False


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
        st.session_state["org"]["form"].update(default_form)


# ----------------------


def org_view_table(conn: SQLConnection, table: Any) -> None:
    with st.expander("🏢 Existing Organizations"):
        st.dataframe(
            table,
            key="OrganizationDF",
            hide_index=True,
            selection_mode="single-row",
            on_select=on_org_selected,
        )
        st.button(
            "Delete",
            icon="🗑️",
            on_click=on_org_delete,
            kwargs={"conn": conn},
            disabled=not st.session_state["org"]["delete_button"],
        )


def org_view_form(conn: SQLConnection, form_data: dict[str]) -> None:
    with st.form("organization_data_entry_form", clear_on_submit=True):
        st.header("🏢 Organization Data Entry")
        name = st.text_input("Organization Full Name", value=form_data["name"])
        try:
            name = NameField(name=name)
        except ValidationError:
            st.warning("⚠️ please, change name")
            name = None
        acronym = st.text_input("Acronym", value=form_data["acronym"])
        try:
            acronym = AcronymField(acronym=acronym)
        except ValidationError:
            st.error("❌ acronym is not valid")
            acronym = None
        website_url = st.text_input("🌎 Web Site", value=form_data["website_url"])
        try:
            website_url = WebField(website_url=website_url)
        except ValidationError:
            st.error("❌ URL format is not valid")
            website_url = None
        email = st.text_input("📧 Email", value=form_data["email"])
        try:
            email = EmailField(email=email)
        except ValidationError:
            st.error("❌ email format is not valid")
            email = None
        submitted = st.form_submit_button(
            "**Submit**",
            help="Submit Organization data to database",
            type="primary",
            # on_click=on_org_form_submitted,
            use_container_width=False,
        )
        all_valid = all(map(lambda x: x is not None, [name, acronym, website_url, email]))
        if submitted and all_valid:
            with conn.session as session:
                db.org_update(
                    session, name.name, acronym.acronym, str(website_url.website_url), email.email
                )
            st.session_state["org"]["table"] = db.orgs_lookup(session)
            st.session_state["org"]["selected"] = None
            st.session_state["org"]["delete_button"] = False
            st.rerun()
        elif not all_valid:
            st.write([name, acronym, website_url, email])
            st.error("Not Updated!")


def view_all(conn: SQLConnection) -> None:
    st.title("✨ 🔭 Observer Data Entry")  # Initialize session state
    c1, c2 = st.columns(2)
    with c1:
        st.write("Placeholder")
    with c2:
        org_view_table(conn, st.session_state["org"]["table"])
        org_view_form(conn, st.session_state["org"]["form"])


org_init(conn)
view_all(conn)
