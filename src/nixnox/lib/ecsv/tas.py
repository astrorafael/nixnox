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

from datetime import datetime, timezone, timedelta
from typing import Optional, Iterable

# -------------------
# Third party imports
# -------------------

import numpy as np

from sqlalchemy import select
from lica.sqlalchemy.dbase import Session

import astropy.io.ascii
from astropy.table import Table
from astropy import units as u

from lica.asyncio.photometer import Sensor

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
    def __init__(self, session: Session, table: Table, extra_path: str):
        self.session = session
        self.table = table
        self.tstamp_fmt = "%Y-%m-%d %H:%M:%S"
        self.extra_path = extra_path

    def observation(self, digest: str) -> Optional[Observation]:
        filename = self.table.meta["keywords"]["measurements_file"]
        filename, _ = os.path.splitext(filename)
        temperature = np.median(self.table["T_sens"])
        temperature_meas = Temperature.MEDIAN
        humidity_meas = Humidity.UNKNOWN
        timestamp_meas = Timestamp.MIDTERM
        t_initial = datetime.strptime(min(self.table["UT_Datetime"]), self.tstamp_fmt)
        t_final = datetime.strptime(max(self.table["UT_Datetime"]), self.tstamp_fmt)
        delta_t = (t_final - t_initial).total_seconds()
        mid_time = (t_initial + timedelta(seconds=(delta_t/2)+0.5)).replace(microsecond=0)
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
                timestamp_1 = mid_time,
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
        self.fill_vbat(measurements)
        return measurements

    def fill_vbat(self, measurements: Iterable[Measurement]) -> None:
        """Take the raw TAS file to extract battery voltages"""
        if self.extra_path:
            names = (
                "ind",
                "Date",
                "Time",
                "T IR",
                "T Sens",
                "Mag",
                "Hz",
                "Alt",
                "Azi",
                "Lat",
                "Long",
                "SL",
                "Bat",
            )
            with open(self.extra_path, "rb") as fd:
                extra_table = astropy.io.ascii.read(
                    fd, format="csv", names=names, data_start=1, delimiter="\t"
                )
                for measurement, extra in zip(measurements, extra_table):
                    assert measurement.sequence == int(extra["ind"])
                    measurement.bat_volt = float(extra["Bat"])


class TASImporter:
    def __init__(self, session: Session, table: Table):
        self.session = session
        self.table = table
        self.tstamp_fmt = "%Y-%m-%dT%H:%M:%S%z"

    def observation(self) -> Optional[Observation]:
        obs_dict = self.table.meta["Observation"]
        q = select(Observation).where(Observation.digest == obs_dict["digest"])
        previous = self.session.scalars(q).one_or_none()
        if previous:
            return None
        
        return Observation(
            identifier=obs_dict["identifier"],
            digest=obs_dict["digest"],
            temperature_1=obs_dict["temperature_1"],
            temperature_2=obs_dict["temperature_1"],
            temperature_meas=Temperature(obs_dict["temperature_meas"]),
            humidity_meas=Humidity(obs_dict["humidity_meas"]),
            humidity_1=obs_dict["humidity_1"],
            humidity_2=obs_dict["humidity_2"],
            timestamp_1=obs_dict["timestamp_1"],
            timestamp_2=obs_dict["timestamp_2"],
            timestamp_meas=Timestamp(obs_dict["timestamp_meas"]),
            weather_conditions=obs_dict["weather_conditions"],
            other_observers=obs_dict["other_observers"],
            comment=obs_dict["comment"],
            image_url=obs_dict["image_url"],
        )

    def photometer(self) -> Photometer:
        phot_dict = self.table.meta["Photometer"]
        name = phot_dict["name"]
        model = PhotometerModel(phot_dict["model"])
        q = select(Photometer).where(Photometer.name == name, Photometer.model == model)
        return self.session.scalars(q).one_or_none() or Photometer(
            model=model,
            name=name,
            sensor=Sensor(phot_dict["sensor"]),
            fov=float(phot_dict["fov"]),
            zero_point=float(phot_dict["zero_point"]),
            comment=phot_dict["comment"],
        )

    def location(self) -> Location:
        loc_dict = self.table.meta["Location"]
        longitude = float(loc_dict["longitude"])
        latitude = float(loc_dict["latitude"])
        q = select(Location).where(Location.longitude == longitude, Location.latitude == latitude)
        location = self.session.scalars(q).one_or_none()
        if location is None:
            location = Location(
                place=loc_dict["place"],
                longitude=longitude,
                latitude=latitude,
                masl=float(loc_dict["masl"]),
                coords_meas=Coordinates(loc_dict["coords_meas"]),
                town=loc_dict["town"],
                sub_region=loc_dict["sub_region"],
                region=loc_dict["region"],
                country=loc_dict["country"],
                timezone=loc_dict["timezone"],
            )
        return location

    def observer(self) -> Observer:
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
