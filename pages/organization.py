# ------------------
# Standard libraries
# ------------------
from typing import Optional, Any, Iterable

import streamlit as st
from streamlit.logger import get_logger

from pydantic import BaseModel, field_validator, ValidationError, EmailStr, HttpUrl

import nixnox.web.dbase as db
from nixnox.web.streamlit import ttl


# ---------------
# Pydantic Models
# ---------------


DEF_ORG_TEXT = "<Enter organization name here>"

class NameField(BaseModel):
    name: str

    @field_validator('name')
    def not_sample_text(cls, v):
        v_stripped = v.strip()
        if v_stripped.startswith("<") and v_stripped.endswith("<"):
            raise ValueError(f"Sample text is not valid: {v_stripped}")
        return v

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
conn = st.connection("env:NX_ENV", type="sql")


org_form_data = {
    "name": DEF_ORG_TEXT,
    "acronym": None,
    "website_url": None,
    "email": None,
    "submitted": False,
}


# ---------------------
# Convenience functions
# ---------------------


@st.cache_data(ttl=ttl())
def affiliations(_conn) -> Iterable[str]:
    with _conn.session as session:
        return db.orgs_names_lookup(session)


@st.cache_data(ttl=ttl())
def person_affiliation(_conn, name) -> Optional[str]:
    with _conn.session as session:
        return db.person_affiliation(session, name)


def init_state_org(conn) -> None:
    with conn.session as session:
        if "orgs_table" not in st.session_state:
            st.session_state["orgs_table"] = db.orgs_lookup(session)
            st.session_state["selected_org"] = None
        if "org_form_data" not in st.session_state:
            # Form below
            st.session_state.org_form_data = org_form_data
        elif st.session_state["org_form_data"]["submitted"]:
            del st.session_state["orgs_table"]
            del st.session_state["selected_org"]

def update_organization(conn, name, acronym, website_url, email):
    with conn.session as session:
        db.org_update(session, name.name, acronym.acronym, str(website_url.website_url), email.email)

def delete_organization(conn, name):
    with conn.session as session:
        db.org_delete(session, name)

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

@st.fragment
def view_org_table(conn, table: Any) -> None: 
    with st.expander("🏢 Existing Organizations"):
        st.dataframe(
            table,
            key="OrganizationDF",
            hide_index=True,
            selection_mode="single-row",
            on_select=on_selected_org,
        )
        clicked = st.button("Delete", icon="🗑️")
        if clicked and st.session_state.get("selected_org"):
            try:
                name = st.session_state["selected_org"][0]
                delete_organization(conn, name)
            except Exception as e:
                st.write(e)
            else:
                del st.session_state["selected_org"]
                del st.session_state["orgs_table"]
                st.success(f"Organization {name} deleted")
                


def view_org_form(conn, form_data: dict[str]) -> None:
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
            st.error("acronym is not valid")
            acronym = None
        website_url = st.text_input("🌎 Web Site", value=form_data["website_url"])
        try:
            website_url = WebField(website_url=website_url)
        except ValidationError:
            st.error("URL format is not valid")
            website_url = None
        email = st.text_input("📧 Email", value=form_data["email"])
        try:
            email = EmailField(email=email)
        except ValidationError:
            st.error("email format is not valid")
            email = None
        submitted = st.form_submit_button(
            "**Submit**",
            help="Submit Organization data to database",
            type="primary",
            use_container_width=False,
        )
        form_data["submitted"] = submitted
        if submitted and all(map(lambda x: x is not None, [name, acronym, website_url, email])):
            update_organization(conn, name, acronym, website_url, email)
            st.success("Updated!")


def view_all(conn) -> None:
    st.title("✨ 🔭 Observer Data Entry")  # Initialize session state
    c1, c2 = st.columns(2)
    with c1:
        st.write("Placeholder")
    with c2:
        view_org_table(conn, st.session_state["orgs_table"])
        view_org_form(conn, st.session_state["org_form_data"])

init_state_org(conn)
view_all(conn)
