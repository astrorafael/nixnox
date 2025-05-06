# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

# --------------------
# System wide imports
# -------------------

import os
import logging
import hashlib

from datetime import datetime, timezone
from typing import Optional, BinaryIO

# -------------------
# Third party imports
# -------------------

import pytz

from sqlalchemy import select
from lica.sqlalchemy.dbase import Session

import astropy.io.ascii
from astropy.table import Table
from astropy import units as u

# --------------
# local imports
# -------------

from . import ObserverType, PhotometerModel, Temperature, Humidity, Timestamp, ValidState
from .location import geolocate
from .dbase.model import (
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


# -----------------------
# Module global variables
# -----------------------


# get the root logger
log = logging.getLogger(__name__.split(".")[-1])

# -------------------
# Auxiliary functions
# -------------------


class DatabaseLoader:
    def __init__(self, session: Session):
        self.session = session
        self.table = None
        self.tstamp_fmt = "%Y-%m-%d %H:%M:%S"

    def _observation(self, digest: str) -> Optional[Observation]:
        filename = self.table.meta["keywords"]["measurements_file"]
        filename, _ = os.path.splitext(filename)
        q = select(Observation).where(Observation.digest == digest)
        return self.session.scalars(q).one_or_none() or Observation(
            identifier=filename,
            digest=digest,
        )

    def _flags(self) -> Flags:
        name = self.table.meta["keywords"]["photometer"]
        temperature = Temperature.UNIQUE if name.startswith("TAS") else Temperature.UNKNOWN
        timestamp = Timestamp.UNIQUE if name.startswith("TAS") else Timestamp.INITIAL
        q = select(Flags).where(
            Flags.temperature_meas == temperature,  # unique Sensor temperature in TAS
            Flags.humidity_meas == Humidity.UNKNOWN,
            Flags.timestamp_meas == timestamp,
        )
        return self.session.scalars(q).one()

    def _photometer(self) -> Optional[Photometer]:
        name = self.table.meta["keywords"]["photometer"]
        model = PhotometerModel.TAS if name.startswith("TAS") else PhotometerModel.SQM
        comments = self.table.meta["keywords"]["comments"].split()
        zero_point = float(comments[2].split(":")[-1])
        q = select(Photometer).where(Photometer.name == name, Photometer.model == model)
        return self.session.scalars(q).one_or_none() or Photometer(
            model=model,
            name=name,
            identifier=name,  # THIS SHOULD BE A MAC ADDRESS BUT WE DON'T HAVE IT !!
            zero_point=zero_point,
            fov=17.0,
        )

    def _location(self) -> Optional[Location]:
        longitude = float(self.table.meta["keywords"]["longitude"])
        latitude = float(self.table.meta["keywords"]["latitude"])
        q = select(Location).where(Location.longitude == longitude, Location.latitude == latitude)
        location = self.session.scalars(q).one_or_none()
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
                place=self.table.meta["keywords"]["place"],
                longitude=result["longitude"],
                latitude=result["latitude"],
                masl=float(self.table.meta["keywords"]["height"]),
                town=result["town"],
                sub_region=result["sub_region"],
                region=result["region"],
                country=result["country"],
                timezone=result["timezone"],
            )
        return location

    def _observer(self) -> Optional[Observer]:
        name = self.table.meta["keywords"]["author"]
        affiliation = self.table.meta["keywords"].get("association")
        obs_type = ObserverType.PERSON
        q = select(Observer).where(Observer.type == obs_type, Observer.name == name)
        return self.session.scalars(q).one_or_none() or Observer(
            type=ObserverType.PERSON,
            name=self.table.meta["keywords"]["author"],
            affiliation=affiliation,
            valid_since=datetime.now(timezone.utc).replace(microsecond=0),
            valid_until=datetime(year=2999, month=12, day=31, tzinfo=timezone.utc),
            valid_state=ValidState.CURRENT,
        )

    def load(self, file_obj: BinaryIO) -> None:
        digest = hashlib.md5(file_obj.read()).hexdigest()
        file_obj.seek(0)  # Rewind to conver it to AstroPy Table
        self.table = astropy.io.ascii.read(file_obj, format="ecsv")
        with self.session.begin():
            observation = self._observation(digest)
            flags = self._flags()
            photometer = self._photometer()
            location = self._location()
            observer = self._observer()
            for item in (photometer, location, observer, observation, flags):
                self.session.add(item)
            for row in self.table:
                tstamp = datetime.strptime(row["UT_Datetime"], self.tstamp_fmt)
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
                    bat_volt=row.get("VBat")
                )
                self.session.add(measurement)
            try:
                self.session.commit()
            except Exception as e:
                log.error(e)
                log.error("Trying to reload the same observation file?")


class DatabaseLoaderV2(DatabaseLoader):

    def __init__(self, session: Session):
        self.session = session
        self.table = None
        self.tstamp_fmt = "%Y-%m-%dT%H:%M:%S%z"

    def _observation(self, digest: str) -> Optional[Observation]:
        obs_dict = self.table.meta["Observation"]
        q = select(Observation).where(Observation.digest == obs_dict["digest"])
        return self.session.scalars(q).one_or_none() or Observation(
            identifier=obs_dict["identifier"],
            digest=obs_dict["digest"],
        )

    def _flags(self) -> Flags:
        flags_dict = self.table.meta["Flags"]
        temperature = Temperature(flags_dict["temperature_meas"])
        timestamp = Timestamp(flags_dict["timestamp_meas"])
        humidity = Humidity(flags_dict["humidity_meas"])
        q = select(Flags).where(
            Flags.temperature_meas == temperature,  # unique Sensor temperature in TAS
            Flags.humidity_meas == humidity,
            Flags.timestamp_meas == timestamp,
        )
        return self.session.scalars(q).one()

    def _photometer(self) -> Optional[Photometer]:
        phot_dict = self.table.meta["Photometer"]
        name = phot_dict["name"]
        model = PhotometerModel(phot_dict["model"])
        q = select(Photometer).where(Photometer.name == name, Photometer.model == model)
        return self.session.scalars(q).one_or_none() or Photometer(
            model=model,
            name=name,
            identifier=phot_dict["identifier"],
            zero_point=float(phot_dict["zero_point"]),
            fov=float(phot_dict["fov"]),
            comment=phot_dict["comment"],
        )

    def _location(self) -> Optional[Location]:
        phot_dict = self.table.meta["Location"]
        longitude = float(phot_dict["longitude"])
        latitude = float(phot_dict["latitude"])
        q = select(Location).where(Location.longitude == longitude, Location.latitude == latitude)
        location = self.session.scalars(q).one_or_none()
        if location is None:
            location = Location(
                place=phot_dict["place"],
                longitude=longitude,
                latitude=latitude,
                masl=float(phot_dict["masl"]),
                town=phot_dict["town"],
                sub_region=phot_dict["sub_region"],
                region=phot_dict["region"],
                country=phot_dict["country"],
                timezone=phot_dict["timezone"],
            )
        return location

    def _observer(self) -> Optional[Observer]:
        over_dict = self.table.meta["Observer"]
        name = over_dict["name"]
        obs_type = ObserverType(over_dict["type"])
        q = select(Observer).where(Observer.type == obs_type, Observer.name == name)
        return self.session.scalars(q).one_or_none() or Observer(
            type=obs_type,
            name=name,
            nickname=over_dict["nickname"],
            affiliation=over_dict["affiliation"],
            acronym=over_dict["acronym"],
            email=over_dict["acronym"],
            website_url=over_dict["website_url"],
            valid_since=datetime.strptime(over_dict["valid_since"], "%Y-%m-%dT%H:%M:%S"),
            valid_until=datetime.strptime(over_dict["valid_until"], "%Y-%m-%dT%H:%M:%S"),
            valid_state=ValidState(over_dict["valid_state"]),
        )


class TableBuilder:
    def __init__(self, session: Session):
        self.session = session

    def build(self, identifier: str) -> Optional[Table]:
        table = None
        q = select(Observation).where(Observation.identifier == identifier)
        observation = self.session.scalars(q).one_or_none()
        if observation:
            measurements = observation.measurements  # This will trigger SQL query
            location = measurements[0].location
            observer = measurements[0].observer
            photometer = measurements[0].photometer
            flags = measurements[0].flags
            data_rows = [
                (
                    m.sequence,
                    m.local_time(location.timezone).isoformat(),
                    m.utc_time().isoformat(),
                    m.sky_temp * u.deg_C if m.sky_temp else None,
                    m.sensor_temp * u.deg_C if m.sensor_temp else None,
                    m.magnitude,
                    m.frequency * u.Hz if m.frequency else None,
                    m.altitude * u.deg,
                    m.azimuth * u.deg,
                    location.latitude * u.deg if location.latitude else None,
                    location.longitude * u.deg if location.longitude else None,
                    location.masl * u.m if location.masl else None,
                    m.bat_volt * u.V if m.bat_volt else None,
                )
                for m in measurements
            ]
            header = (
                "ind",
                "Datetime",
                "UT_Datetime",
                "Temp_IR",
                "T_sens",
                "Mag",
                "Hz",
                "Alt",
                "Azi",
                "Lat",
                "Long",
                "SL",
                "VBat",
            )
            table = Table(rows=data_rows, names=header)
            table.meta["Observer"] = observer.to_table()
            table.meta["Location"] = location.to_table()
            table.meta["Photometer"] = photometer.to_table()
            table.meta["Observation"] = observation.to_table()
            table.meta["Flags"] = flags.to_table()
            return table
        else:
            log.warn("No observation found with identifier %s", identifier)
        return table
