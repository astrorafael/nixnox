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

from datetime import datetime, timezone
from typing import Optional, Iterable

# -------------------
# Third party imports
# -------------------

import numpy as np

from sqlalchemy import select
from lica.sqlalchemy.dbase import Session

from astropy.table import Table
from astropy import units as u

# --------------
# local imports
# -------------

from .. import (
    ObserverType,
    PhotometerModel,
    Temperature,
    Humidity,
    Timestamp,
    Coordinates,
    ValidState,
)
from ..location import geolocate
from ..dbase.model import (
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


class TASLoader:
    def __init__(self, session: Session, table: Table):
        self.session = session
        self.table = table
        self.tstamp_fmt = "%Y-%m-%d %H:%M:%S"

    def observation(self, digest: str) -> Optional[Observation]:
        filename = self.table.meta["keywords"]["measurements_file"]
        filename, _ = os.path.splitext(filename)
        temperature = np.median(self.table["T_sens"])
        temperature_meas = Temperature.MEDIAN
        humidity_meas = Humidity.UNKNOWN
        timestamp_meas = Timestamp.UNIQUE
        q = select(Observation).where(Observation.digest == digest)
        previous = self.session.scalars(q).one_or_none()
        if previous:
            result = None
        else:
            result = Observation(
                identifier=filename,
                digest=digest,
                temperature_1=temperature,
                temperature_meas=temperature_meas,
                humidity_meas=humidity_meas,
                timestamp_meas=timestamp_meas,
            )
        return result

    def photometer(self) -> Photometer:
        name = self.table.meta["keywords"]["photometer"]
        model = PhotometerModel.TAS
        comments = self.table.meta["keywords"]["comments"].split()
        zero_point = float(comments[2].split(":")[-1])
        q = select(Photometer).where(Photometer.name == name, Photometer.model == model)
        return self.session.scalars(q).one_or_none() or Photometer(
            model=model,
            name=name,
            zero_point=zero_point,
            fov=17.0,
        )

    def location(self) -> Location:
        longitude = np.median(self.table["Long"])
        latitude = np.median(self.table["Lat"])
        masl = np.median(self.table["SL"])
        coords_meas = Coordinates.MEDIAN
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
                masl=masl,
                coords_meas=coords_meas,
                town=result["town"],
                sub_region=result["sub_region"],
                region=result["region"],
                country=result["country"],
                timezone=result["timezone"],
            )
        return location

    def observer(self) -> Observer:
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

    def measurements(
        self,
        photometer: Photometer,
        observation: Observation,
        location: Location,
        observer: Observer,
    ) -> Iterable[Measurement]:
        measurements = list()
        for row in self.table:
            tstamp = datetime.strptime(row["UT_Datetime"], self.tstamp_fmt)
            measurement = Measurement(
                date_id=int(tstamp.strftime("%Y%m%d")),
                time_id=int(tstamp.strftime("%H%M%S")),
                photometer=photometer,
                observer=observer,
                location=location,
                observation=observation,
                sequence=int(row["ind"]),
                azimuth=row["Azi"],
                altitude=row["Alt"],
                zenital=90.0 - row["Alt"],
                magnitude=row["Mag"],
                frequency=row.get("Hz"),
                sky_temp=row.get("Temp_IR"),
                sensor_temp=row.get("T_sens"),
                longitude=row.get("Long"),
                latitude=row.get("Lat"),
                masl=row.get("SL"),
                bat_volt=row.get("VBat"),
            )
            measurements.append(measurement)
        return measurements



class DatabaseLoaderV2:
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

    def _photometer(self) -> Optional[Photometer]:
        phot_dict = self.table.meta["Photometer"]
        name = phot_dict["name"]
        model = PhotometerModel(phot_dict["model"])
        q = select(Photometer).where(Photometer.name == name, Photometer.model == model)
        return self.session.scalars(q).one_or_none() or Photometer(
            model=model,
            name=name,
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


class TASExporter:
    """Export a TAS Observation to AstroPy Table"""

    def to_table(
        self,
        photometer: Photometer,
        observation: Observation,
        location: Location,
        observer: Observer,
        measurements: Measurement,
    ) -> Table:
        data_rows = [
            (
                m.sequence,
                m.local_time(location.timezone).isoformat(),
                m.utc_time().isoformat(),
                m.sky_temp * u.deg_C,
                m.sensor_temp * u.deg_C,
                m.magnitude,
                m.frequency * u.Hz,
                m.altitude * u.deg,
                m.azimuth * u.deg,
                m.latitude * u.deg,
                m.longitude * u.deg,
                m.masl * u.m,
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
        return table


