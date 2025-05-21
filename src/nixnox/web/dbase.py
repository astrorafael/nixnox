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
