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

from sqlalchemy import select

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
    Date,
)

from ..lib.ecsv.tas import TASExporter


def obs_summary(session):
    q = (
        select(
            Observation.identifier.label("tag"),
            Observation.timestamp_1.label("date"),
            Observer.name,
            Location.place,
            Photometer.name.label("photometer"),
        )
        .distinct()
        .select_from(Measurement)
        .join(Date, Measurement.date_id == Date.date_id)
        .join(Observation, Measurement.obs_id == Observation.obs_id)
        .join(Location, Measurement.observer_id == Location.location_id)
        .join(Observer, Measurement.observer_id == Observer.observer_id)
        .join(Photometer, Measurement.phot_id == Photometer.phot_id)
    )
    return session.execute(q).all()


def obs_details(session, obs_tag: str):
    q = (
        select(Observation, Observer, Location, Photometer)
        .select_from(Measurement)
        .distinct()
        .join(Observation, Measurement.obs_id == Observation.obs_id)
        .join(Location, Measurement.observer_id == Location.location_id)
        .join(Observer, Measurement.observer_id == Observer.observer_id)
        .join(Photometer, Measurement.phot_id == Photometer.phot_id)
        .where(Observation.identifier == obs_tag)
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
