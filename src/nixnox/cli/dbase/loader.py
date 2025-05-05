# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

# --------------------
# System wide imports
# -------------------

import logging
import hashlib
from argparse import ArgumentParser, Namespace

from datetime import datetime, timezone
from typing import Optional

# -------------------
# Third party imports
# -------------------

from sqlalchemy import select

import astropy.io.ascii

from astropy.table import Table

from lica.sqlalchemy import sqa_logging
from lica.sqlalchemy.dbase import Session
from lica.cli import execute

# --------------
# local imports
# -------------

from ... import __version__
from ..util import parser as prs
from ...lib import ObserverType, PhotometerModel, Temperature, Humidity, Timestamp, ValidState
from ...lib.location import geolocate
from ...lib.dbase.model import (
    Flags,
    Photometer,
    Observer,
    Observation,
    Location,
    Measurement,
)

# ----------------
# Module constants
# ----------------

DESCRIPTION = "NIXNOX Database load ECSV tool"

# -----------------------
# Module global variables
# -----------------------


# get the root logger
log = logging.getLogger(__name__.split(".")[-1])

# -------------------
# Auxiliary functions
# -------------------


def get_observation(session: Session, table: Table, digest: str) -> Optional[Observation]:
    filename = table.meta["keywords"]["measurements_file"]
    q = select(Observation).where(Observation.digest == digest)
    return session.scalars(q).one_or_none() or Observation(
        filename=filename,
        digest=digest,
    )


def get_observer(session: Session, table: Table) -> Optional[Observer]:
    name = table.meta["keywords"]["author"]
    affiliation = table.meta["keywords"].get("association")
    obs_type = ObserverType.PERSON
    q = select(Observer).where(Observer.type == obs_type, Observer.name == name)
    return session.scalars(q).one_or_none() or Observer(
        type=ObserverType.PERSON,
        name=table.meta["keywords"]["author"],
        affiliation=affiliation,
        valid_since=datetime.now(timezone.utc).replace(microsecond=0),
        valid_until=datetime(year=2999, month=12, day=31),
        valid_state=ValidState.CURRENT,
    )


def get_location(session: Session, table: Table) -> Optional[Location]:
    longitude = float(table.meta["keywords"]["longitude"])
    latitude = float(table.meta["keywords"]["latitude"])
    q = select(Location).where(Location.longitude == longitude, Location.latitude == latitude)
    location = session.scalars(q).one_or_none()
    if location is None:
        result = geolocate(
            longitude=longitude,
            latitude=latitude,
        )
        result["town"] = result["town"] or "Unknown"
        result["sub_region"] = result["sub_region"] or "Unknown"
        result["region"] = result["region"] or "Unknown"
        result["country"] = result["country"] or "Unknown"
        location = Location(
            place=table.meta["keywords"]["place"],
            longitude=result["longitude"],
            latitude=result["latitude"],
            masl=float(table.meta["keywords"]["height"]),
            town=result["town"],
            sub_region=result["sub_region"],
            region=result["region"],
            country=result["country"],
            timezone=result["timezone"],
        )
    return location


def get_photometer(session: Session, table: Table) -> Optional[Photometer]:
    name = table.meta["keywords"]["photometer"]
    model = PhotometerModel.TAS if name.startswith("TAS") else PhotometerModel.SQM
    comments = table.meta["keywords"]["comments"].split()
    zero_point = float(comments[2].split(":")[-1])
    q = select(Photometer).where(Photometer.name == name, Photometer.model == model)
    return session.scalars(q).one_or_none() or Photometer(
        model=model,
        name=name,
        identifier=name,  # THIS SHOULD BE A MAC ADDRESS BUT WE DON?T HAVE IT !!
        zero_point=zero_point,
        fov=17.0,
    )


def get_flags(session: Session, table: Table) -> Flags:
    name = table.meta["keywords"]["photometer"]
    temperature = Temperature.UNIQUE if name.startswith("TAS") else Temperature.UNKNOWN
    timestamp = Timestamp.UNIQUE if name.startswith("TAS") else Timestamp.INITIAL
    q = select(Flags).where(
        Flags.temperature_meas == temperature,  # unique Sensor temperature in TAS
        Flags.humidity_meas == Humidity.UNKNOWN,
        Flags.timestamp_meas == timestamp,
    )
    return session.scalars(q).one()


# -------------
# CLI Functions
# -------------


def cli_load_obs(session: Session, args: Namespace) -> None:
    path = " ".join(args.input_file)
    log.info("Loading file %s", path)
    with open(path, "rb") as fd:
        contents = fd.read()
        digest = hashlib.md5(contents).hexdigest()
        fd.seek(0)  # Rewind to conver it to AstroPy Table
        table = astropy.io.ascii.read(fd, format="ecsv")
    log.info("Digest is %s", digest)
    with session.begin():
        observation = get_observation(session, table, digest)
        flags = get_flags(session, table)
        photometer = get_photometer(session, table)
        location = get_location(session, table)
        observer = get_observer(session, table)
        for item in (photometer, location, observer, observation, flags):
            session.add(item)
        for row in table:
            tstamp = datetime.strptime(row["UT_Datetime"], "%Y-%m-%d %H:%M:%S")
            measurement = Measurement(
                date_id=int(tstamp.strftime("%Y%m%d")),
                time_id=int(tstamp.strftime("%H%M%S")),
                photometer=photometer,
                observer=observer,
                location=location,
                observation=observation,
                flags=flags,
                sequence=int(row["ind"]),
                azimuth=row["Azi"],
                altitude=row["Alt"],
                zenital=90.0 - row["Alt"],
                magnitude=row["Mag"],
                frequency=row["Hz"],
                sky_temp=row["Temp_IR"],
                sensor_temp=row["T_sens"],
            )
            session.add(measurement)
        try:
            session.commit()
        except Exception:
            log.error("(%s) Trying to reload the same observation file?", path)
    
           


def add_args(parser: ArgumentParser) -> None:
    subparser = parser.add_subparsers(dest="command", required=True)
    p = subparser.add_parser(
        "observation", parents=[prs.ifiles()], help="Load one or more ECSV observation files"
    )
    p.set_defaults(func=cli_load_obs)


def cli_main(args: Namespace) -> None:
    sqa_logging(args)
    with Session() as session:
        args.func(session, args)


def main():
    """The main entry point specified by pyproject.toml"""
    execute(
        main_func=cli_main,
        add_args_func=add_args,
        name=__name__,
        version=__version__,
        description=DESCRIPTION,
    )


if __name__ == "__main__":
    main()
