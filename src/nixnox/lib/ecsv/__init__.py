# ----------------------------------------------------------------------
# Copyright (c) 2022
#
# See the LICENSE file for details
# see the AUTHORS file for authors
# ----------------------------------------------------------------------

# ----------------
# standard imports
# ----------------

import logging
import hashlib

from typing import BinaryIO, Optional

# -------------------
# Third party imports
# -------------------

from sqlalchemy import select

from lica.sqlalchemy.dbase import Session

import astropy.io.ascii
from astropy.table import Table

# --------------
# local imports
# -------------

from .. import PhotometerModel
from ..dbase.model import Observation

from .tas import TASLoader, TASExporter
from .sqm import SQMLoader


# get the root logger
log = logging.getLogger(__name__.split(".")[-1])


def loader(session: Session, file_obj: BinaryIO) -> None:
    digest = hashlib.md5(file_obj.read()).hexdigest()
    file_obj.seek(0)  # Rewind to conver it to AstroPy Table
    table = astropy.io.ascii.read(file_obj, format="ecsv")
    name = table.meta["keywords"]["photometer"]
    with session.begin():
        subloader = (
            TASLoader(session, table) if name.startswith("TAS") else SQMLoader(session, table)
        )
        observation = subloader.observation(digest)
        if observation is None:
            raise RuntimeError("Observation already exists. Abort loading")
        photometer = subloader.photometer()
        location = subloader.location()
        observer = subloader.observer()
        for item in (
            photometer,
            location,
            observer,
            observation,
        ):
            session.add(item)
        measurements = subloader.measurements(photometer, observation, location, observer)
        for measurement in measurements:
            session.add(measurement)
        try:
            session.commit()
        except Exception as e:
            log.error(e)
            log.error("Trying to reload the same observation file?")


def database_import(session: Session, file_obj: BinaryIO) -> None:
    # THIS MUST BE REVIEWED
    raise NotImplementedError


def database_export(session: Session, identifier: str) -> Optional[Table]:
    table = None
    q = select(Observation).where(Observation.identifier == identifier)
    observation = session.scalars(q).one_or_none()
    if observation:
        # This will trigger several SQL queries
        measurements = observation.measurements
        location = measurements[0].location
        observer = measurements[0].observer
        photometer = measurements[0].photometer
        if photometer.model == PhotometerModel.TAS:
            table = TASExporter().to_table(
                photometer, observation, location, observer, measurements
            )
        else:
            raise NotImplementedError
    else:
        log.warn("No observation found with identifier %s", identifier)
    return table
