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
import os

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
from ..dbase.model import Observation, Person

from .tas import TASLoader, TASExporter, TASImporter
#from .sqm import SQMLoader

# get the root logger
log = logging.getLogger(__name__.split(".")[-1])


def uploader(session: Session, file_obj: BinaryIO, log=log, **kwargs) -> Optional[Observation]:
    observation = None
    digest = hashlib.md5(file_obj.read()).hexdigest()
    file_obj.seek(0)  # Rewind to conver it to AstroPy Table
    table = astropy.io.ascii.read(file_obj, format="ecsv")
    name = table.meta["keywords"]["photometer"]
    with session.begin():
        subloader = (
            TASLoader(session, table, kwargs.get("extra_path"), log)
            if name.startswith("TAS")
            else SQMLoader(session, table)
        )
        observation = subloader.observation(digest)  # may reaise an exception if already existing
        photometer = subloader.photometer()
        location = subloader.location()
        observer = subloader.observer()
        if isinstance(observer, Person):
            affiliation = subloader.affiliation()
            observer.affiliation = affiliation
            session.add(affiliation)
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
        finally:
            return observation


def database_import(session: Session, file_obj: BinaryIO) -> Optional[Observation]:
    # THIS MUST BE REVIEWED
    observation = None
    table = astropy.io.ascii.read(file_obj, format="ecsv")
    log.info(table.meta)
    with session.begin():
        importer = TASImporter(session, table)
        observation = importer.observation()
        photometer = importer.photometer()
        location = importer.location()
        observer = importer.observer()
        if isinstance(observer, Person):
            affiliation = importer.affiliation()
            observer.affiliation = affiliation
            session.add(affiliation)
        for item in (
            photometer,
            location,
            observer,
            observation,
        ):
            session.add(item)
        measurements = importer.measurements(photometer, observation, location, observer)
        for measurement in measurements:
            session.add(measurement)
        try:
            session.commit()
        except Exception as e:
            log.error(e)
            log.error("Trying to reload the same observation file?")
        finally:
            return observation


def _recall_observation(session: Session, observation: Observation) -> Table:
    # This will trigger several SQL queries
    measurements = observation.measurements
    location = measurements[0].location
    observer = measurements[0].observer
    photometer = measurements[0].photometer
    if photometer.model == PhotometerModel.TAS:
        table = TASExporter().to_table(photometer, observation, location, observer, measurements)
    else:
        raise NotImplementedError
    return table


def database_export(session: Session, out_dir: str, identifier: str | None) -> None:
    if identifier is not None:
        q = select(Observation).where(Observation.identifier == identifier)
        observation = session.scalars(q).one_or_none()
        if observation:
            table = _recall_observation(session, observation)
        else:
            log.warn("No observation found with identifier %s", identifier)
        path = os.path.join(out_dir, identifier + ".ecsv")
        table.write(path, delimiter=",", format="ascii.ecsv", overwrite=True)
    else:
        q = select(Observation)
        observations = session.scalars(q).all()
        for observation in observations:
            identifier = observation.identifier
            table = _recall_observation(session, observation)
            path = os.path.join(out_dir, identifier + ".ecsv")
            table.write(path, delimiter=",", format="ascii.ecsv", overwrite=True)
