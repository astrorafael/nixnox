# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

# --------------------
# System wide imports
# -------------------

from io import StringIO

# =====================
# Third party libraries
# =====================

from sqlalchemy import select, func, desc
from streamlit.logger import get_logger

# -------------
# Local imports
# -------------

from ..lib import PhotometerModel

from ..lib.dbase.model import (
    Photometer,
    Observer,
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


def obs_summary(session, limit=10):
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
        .group_by(Measurement.obs_id)
        .order_by(desc(Measurement.date_id), desc(Measurement.time_id))
        .limit(limit)
    )
    return session.execute(q).all()


def obs_summary_search(session, cond: dict = None, limit=10):
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
    if cond:
        # Always add the date conditions
        start_date_id = int(cond["search_date_range"][0].strftime("%Y%m%d"))
        end_date_id = int(cond["search_date_range"][1].strftime("%Y%m%d"))
        log.info("START_DATE_ID = %s, END_DATE_ID = %s", start_date_id, end_date_id)
        q = q.where(Measurement.date_id.between(start_date_id, end_date_id))
        # Add photometer conditions if any
        if cond["search_by_photometer"]:
            q = q.where(
                Photometer.model == cond["search_by_photometer_model"],
                Photometer.name == cond["search_by_photometer"],
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
                Location.town.like("%" + cond["search_by_location_name"] + "%"),
            )
        elif not any(
            [
                cond["search_from_longitude"],
                cond["search_to_longitude"],
                cond["search_from_latitude"],
                cond["search_to_latitude"],
            ] # All four coordinates must be present to include the query condition
        ):
            long1, long2 = min(cond["search_from_longitude"]), max(cond["search_to_longitude"])
            lat1, lat2 = min(cond["search_from_latitude"]), max(cond["search_to_latitude"])
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
