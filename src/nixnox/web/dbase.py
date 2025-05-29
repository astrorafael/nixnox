# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

# --------------------
# System wide imports
# -------------------

from datetime import datetime
from io import StringIO
from typing import Optional

# =====================
# Third party libraries
# =====================

from sqlalchemy import select, func, desc, asc, label
from streamlit.logger import get_logger

# -------------
# Local imports
# -------------

from ..lib import PhotometerModel, ValidState

from ..lib.dbase.model import (
    Photometer,
    Observer,
    Individual,
    Organization,
    Observation,
    Location,
    Measurement,
)

from ..lib.ecsv.tas import TASExporter

# ----------------
# Global variables
# ----------------

log = get_logger(__name__)


def obs_nsummaries(session) -> int:
    q = select(func.count("*")).select_from(Observation)
    return session.scalars(q).one()


def obs_summary_search(session, cond: dict = None):
    """Generic Obsewrvation summary search with several constratints"""
    q = (
        select(
            Observation.timestamp_1.label("date"),
            Observation.identifier.label("tag"),
            Location.place,
            Photometer.name.label("photometer"),
            Observer.name,
        )
        .select_from(Measurement)
        .join(Observation, Measurement.obs_id == Observation.obs_id)
        .join(Location, Measurement.observer_id == Location.location_id)
        .join(Observer, Measurement.observer_id == Observer.observer_id)
        .join(Photometer, Measurement.phot_id == Photometer.phot_id)
    )
    log.info("CONDITIONS DICT = %s", cond)
    if cond is None:
        limit = 10
    else:
        limit = cond["search_limit"]
        # Always add the date conditions
        start_date_id = int(cond["search_date_range"][0].strftime("%Y%m%d"))
        end_date_id = int(cond["search_date_range"][1].strftime("%Y%m%d"))
        q = q.where(Measurement.date_id.between(start_date_id, end_date_id))
        # Add photometer conditions if any
        if cond["search_by_phot_name"]:
            q = q.where(
                Photometer.model == cond["search_by_phot_model"],
                Photometer.name == cond["search_by_phot_name"],
            )
        # Add Observer conditions if any
        if cond["search_by_observer_name"]:
            q = q.where(
                Observer.type == cond["search_by_observer_type"],
                Observer.name.like("%" + cond["search_by_observer_name"] + "%"),
            )
        # Add Location conditions if any
        if cond["search_by_location_name"] and cond["search_by_location_scope"] == "Country":
            q = q.where(
                Location.country.like("%" + cond["search_by_location_name"] + "%"),
            )
        elif (
            cond["search_by_location_name"]
            and cond["search_by_location_scope"] == "Population Centre"
        ):
            q = q.where(
                Location.population_centre.like("%" + cond["search_by_location_name"] + "%"),
            )
        else:
            # All coords must be not None
            good_coords = list(
                map(
                    lambda x: x is not None,
                    [
                        cond["search_from_longitude"],
                        cond["search_to_longitude"],
                        cond["search_from_latitude"],
                        cond["search_to_latitude"],
                    ],
                )
            )
            if all(good_coords):
                long1 = min(cond["search_from_longitude"], cond["search_to_longitude"])
                long2 = max(cond["search_from_longitude"], cond["search_to_longitude"])
                lat1 = min(cond["search_from_latitude"], cond["search_to_latitude"])
                lat2 = max(cond["search_from_latitude"], cond["search_to_latitude"])
                q = q.where(
                    Location.longitude.between(long1, long2),
                    Location.latitude.between(lat1, lat2),
                )
    # Finalize the query
    q = (
        q.group_by(Measurement.obs_id)
        .order_by(desc(Measurement.date_id), desc(Measurement.time_id))
        .limit(limit)
    )
    return session.execute(q).all()


def obs_details(session, obs_tag: str):
    q = (
        select(Observation, Observer, Location, Photometer)
        .select_from(Measurement)
        .join(Observation, Measurement.obs_id == Observation.obs_id)
        .join(Location, Measurement.observer_id == Location.location_id)
        .join(Observer, Measurement.observer_id == Observer.observer_id)
        .join(Photometer, Measurement.phot_id == Photometer.phot_id)
        .where(Observation.identifier == obs_tag)
        .group_by(Measurement.obs_id)
    )
    return session.execute(q).one()


def obs_measurements(session, obs_tag: str):
    q = (
        select(Measurement)
        .select_from(Measurement)
        .join(Observation, Measurement.obs_id == Observation.obs_id)
        .join(Location, Measurement.observer_id == Location.location_id)
        .join(Observer, Measurement.observer_id == Observer.observer_id)
        .join(Photometer, Measurement.phot_id == Photometer.phot_id)
        .where(Observation.identifier == obs_tag)
    )
    return session.scalars(q).all()


def obs_export(session, obs_tag: str) -> str:
    """Outputs a ECSV formatted string suitable to be sent to a web browser"""
    q = select(Observation).where(Observation.identifier == obs_tag)
    observation = session.scalars(q).one_or_none()
    measurements = observation.measurements
    location = measurements[0].location
    observer = measurements[0].observer
    photometer = measurements[0].photometer
    if photometer.model == PhotometerModel.TAS:
        table = TASExporter().to_table(photometer, observation, location, observer, measurements)
    else:
        raise NotImplementedError
    output_file = StringIO()
    table.write(output_file, delimiter=",", format="ascii.ecsv", overwrite=True)
    return output_file.getvalue()


# ========================
# OBSERVER PAGE MANAGEMENT
# ========================


def persons_lookup(session):
    """Person summary search with several constratints"""
    q = select(
        Individual.name,
        Individual.nickname,
        label("affiliated", Individual.affiliation_id is not None),
        Individual.valid_state,
        Individual.valid_since,
        Individual.valid_until,
    ).order_by(asc(Individual.name))
    return session.execute(q).all()


def person_affiliation(session, name: str) -> Optional[str]:
    q = select(Individual).where(Individual.name == name)
    person = session.scalars(q).one_or_none()
    if not person or not person.affiliation:
        return None
    return person.affiliation.name


def person_delete(session, name: str) -> None:
    with session.begin():
        q = select(Individual).where(Individual.name == name)
        person = session.scalars(q).one_or_none()
        if person:
            session.delete(person)


def person_update(
    session,
    name: str,
    nickname: str,
    affiliation: str,
    valid_since: datetime,
    valid_until: datetime,
) -> None:
    with session.begin():
        qp = select(Individual).where(Individual.name == name)
        qo = select(Organization).where(Organization.name == affiliation)
        org = session.scalars(qo).one()
        persons = session.scalars(qp).all()
        log.info("PERSONS %s", persons)
        # new person ?
        if len(persons) == 0:
            person = Individual(
                name=name,
                nickname=nickname,
                valid_since=valid_since,
                valid_until=valid_until,
                valid_state=ValidState.CURRENT,
            )
            person.affiliation = org
        else:
            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!
            # ESTO ES PROVISIONAL !!!!!!!!
            # HAY QUE DARLE UNA BUENA PENSADA
            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!
            assert len(persons) == 1
            person = persons[0]
            person.nickname = nickname
            person.affiliation = org
            person.valid_since = valid_since
            person.valid_until = valid_until
        session.add(person)


def orgs_names_lookup(session):
    q = select(Organization.name).order_by(asc(Organization.name))
    return session.scalars(q).all()


def orgs_lookup(session):
    q = select(
        Organization.name, Organization.acronym, Organization.website_url, Organization.email
    ).order_by(asc(Organization.name))
    return session.execute(q).all()


def org_update(session, name: str, acronym: str, website_url: str, email: str) -> None:
    with session.begin():
        q = select(Organization).where(Organization.name == name)
        organization = session.scalars(q).one_or_none()
        log.info("ORGANIZATION %s", organization)
        if organization:
            organization.acronym = acronym
            organization.website_url = website_url
            organization.email = email
            log.info("YA EXISTE Y LA MODIFICAMOS A %s", organization)
        else:
            organization = Organization(
                name=name, acronym=acronym, website_url=website_url, email=email
            )
        session.add(organization)


def org_delete(session, name: str) -> None:
    with session.begin():
        q = select(Organization).where(Organization.name == name)
        organization = session.scalars(q).one_or_none()
        if organization:
            session.delete(organization)
