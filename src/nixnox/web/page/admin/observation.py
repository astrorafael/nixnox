# ------------------
# Standard libraries
# ------------------

from collections import defaultdict
from typing import Optional, Any, Tuple, Annotated
from datetime import datetime, date

# ---------------------
# Thirs party libraries
# ---------------------

import streamlit as st
from streamlit.connections import SQLConnection
from streamlit import logger

from pydantic import BaseModel, ValidationError, constr, EmailStr, HttpUrl
from pydantic.types import StringConstraints

# -----------
# own library
# -----------

import nixnox.web.dbase as db
from nixnox.lib import ValidState

# ---------------
# Pydantic Models
# ---------------

LongNameStr = Annotated[str, StringConstraints(pattern=r"^[a-zA-Z 0-9_-]{8,255}$")]
ShortNameStr = Annotated[str, StringConstraints(pattern=r"^[a-zA-Z 0-9_-]{3,22}$")]

DEF_ORG_TEXT = "Enter organization name here"
DEF_PERSON_TEXT = "Enter your full name here"

class NameField(BaseModel):
    name: LongNameStr


class AcronymField(BaseModel):
    org_acronym: Optional[ShortNameStr] = None


class WebField(BaseModel):
    org_website_url: Optional[HttpUrl] = None


class EmailField(BaseModel):
    org_email: Optional[EmailStr] = None


class NickField(BaseModel):
    nickname: Optional[ShortNameStr] = None


class AffilField(BaseModel):
    affiliation: Optional[LongNameStr] = None


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


def obs_init(conn: SQLConnection) -> None:
    pass



# ---------------
# Views rendering
# ----------------



def obs_view(conn: SQLConnection) -> None:
    st.title("✨ 🔭 Observation Data Entry")
    