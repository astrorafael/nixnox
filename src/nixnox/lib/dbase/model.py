# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------


# --------------------
# System wide imports
# -------------------

from collections import OrderedDict
from typing import Optional, List
from datetime import datetime, timezone

# =====================
# Third party libraries
# =====================

import pytz

from sqlalchemy import (
    Enum,
    String,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, declarative_base

from lica.sqlalchemy.model import metadata

from lica.asyncio.photometer import Sensor

from .. import (
    ObserverType,
    ValidState,
    PhotometerModel,
    Temperature,
    Humidity,
    Coordinates,
    Timestamp,
    PopulationCentre,
)

# ================
# Module constants
# ================

# =======================
# Module global variables
# =======================


# =================================
# Data Model, declarative ORM style
# =================================

Model = declarative_base(metadata=metadata)

# ---------------------------------------------
# Additional conveniente types for enumerations
# ---------------------------------------------

# These are really Column declarations
# They are needed on the RHS of the ORM model, in mapped_column()

ObserverCol: Enum = Enum(
    ObserverType,
    name="observer_type",
    create_constraint=False,
    metadata=Model.metadata,
    validate_strings=True,
    values_callable=lambda x: [e.value.title() for e in x],
)

PhotometerModelCol: Enum = Enum(
    PhotometerModel,
    name="model_type",
    create_constraint=False,
    metadata=Model.metadata,
    validate_strings=True,
    values_callable=lambda x: [e.value.upper() for e in x],
)


SensorType: Enum = Enum(
    Sensor,
    name="sensor_type",
    create_constraint=False,
    metadata=Model.metadata,
    validate_strings=True,
    values_callable=lambda x: [e.value.upper() for e in x],
)

ValidStateType: Enum = Enum(
    ValidState,
    name="valid_state_type",
    create_constraint=False,
    metadata=Model.metadata,
    validate_strings=True,
    values_callable=lambda x: [e.value.title() for e in x],
)

TemperatureType: Enum = Enum(
    Temperature,
    name="temperature_type",
    create_constraint=False,
    metadata=Model.metadata,
    validate_strings=True,
    values_callable=lambda x: [e.value.title() for e in x],
)

HumidityType: Enum = Enum(
    Humidity,
    name="humidity_type",
    create_constraint=False,
    metadata=Model.metadata,
    validate_strings=True,
    values_callable=lambda x: [e.value.title() for e in x],
)

TimestampType: Enum = Enum(
    Timestamp,
    name="timestamp_type",
    create_constraint=False,
    metadata=Model.metadata,
    validate_strings=True,
    values_callable=lambda x: [e.value.title() for e in x],
)

CoordinatesType: Enum = Enum(
    Coordinates,
    name="coordinates_type",
    create_constraint=False,
    metadata=Model.metadata,
    validate_strings=True,
    values_callable=lambda x: [e.value.title() for e in x],
)

PopulationCentreType: Enum = Enum(
    PopulationCentre,
    name="population_type",
    create_constraint=False,
    metadata=Model.metadata,
    validate_strings=True,
    values_callable=lambda x: [e.value.title() for e in x],
)
# ------------------
# Auxiliar functions
# ------------------


def observer_name(observer: dict) -> str:
    """Handy formatting tool to get a good observer name"""
    name = observer["name"]
    if ObserverType(observer["type"]) == ObserverType.PERSON:
        if observer["affiliation"] is not None:
            long_affil = observer["affiliation"]["name"]
            short_affil = (
                observer["affiliation"]["org_acronym"]
                if observer["affiliation"]["org_acronym"] is not None
                else ""
            )
            affiliation = short_affil or long_affil
            result = f"{name} ({affiliation})"
        else:
            result = name
    else:
        result = f"{name} ({observer['org_acronym']})" if observer["org_acronym"] else name
    return result


# --------
# Entities
# --------


class Date(Model):
    __tablename__ = "date_t"

    # Date as YYYYMMDD integer
    date_id: Mapped[int] = mapped_column(primary_key=True)
    # Date as YYYY-MM-DD string
    sql_date: Mapped[str] = mapped_column(String(10))
    # Date as DD/MM/YYYY
    date: Mapped[str] = mapped_column(String(10))
    # Day of monty 1..31
    day: Mapped[int]
    # day of year 1..365
    day_year: Mapped[int]
    # Julian date at midnight
    julian_day: Mapped[float]
    # Sunday, Monday, Tuesday, ...
    weekday: Mapped[str] = mapped_column(String(9))
    # Sun, Mon, Tue, ...
    weekday_abbr: Mapped[str] = mapped_column(String(3))
    # 0=Sunday, 1=Monday
    weekday_num: Mapped[int]
    month_num: Mapped[int]
    # January, February, March, ...
    month: Mapped[str] = mapped_column(String(8))
    # Jan, Feb, Mar, ...
    month_abbr: Mapped[str] = mapped_column(String(3))
    year: Mapped[int]

    __table_args__ = {"extend_existing": True}  # This is for streamlit only :-(


class Time(Model):
    __tablename__ = "time_t"

    # HHMMSS as integer
    time_id: Mapped[int] = mapped_column(primary_key=True)
    # HH:MM:SS string
    time: Mapped[str] = mapped_column(String(8))
    hour: Mapped[int]
    minute: Mapped[int]
    second: Mapped[int]
    day_fraction: Mapped[float]

    __table_args__ = {"extend_existing": True}  # This is for streamlit only :-(


class Observer(Model):
    __tablename__ = "observer_t"

    observer_id: Mapped[int] = mapped_column(primary_key=True)
    # Either Indiviudal or Organization
    type: Mapped[ObserverType] = mapped_column(ObserverCol, nullable=False)
    # Person/Organization full name
    name: Mapped[str] = mapped_column(String(255))

    # We can't set an UniqueConstraint on name, valid_since because this applies
    # only to Persons
    __table_args__ = (
        {"extend_existing": True},  # needed for streamlit only :-(
    )

    __mapper_args__ = {
        "polymorphic_on": "type",
    }

    def __repr__(self) -> str:
        return str(self.to_dict())

    def to_dict(self) -> OrderedDict:
        """To be written as Astropy's table metadata"""
        r = OrderedDict(
            (key, self.__dict__.get(key))
            for key in (
                "type",
                "name",
            )
        )
        # Patch enum & date values
        r["type"] = self.type.value
        return r


class Organization(Observer):
    # Since this has no proper table, we can't declare an "org_id" primary key column on its own
    # We have to reuse "observer_id"
    observer_id: Mapped[int] = mapped_column(
        ForeignKey("observer_t.observer_id"), primary_key=True, use_existing_column=True
    )
    # Organization name
    name: Mapped[str] = mapped_column(String(255), use_existing_column=True)
    # Organization org_acronym
    org_acronym: Mapped[str] = mapped_column(String(16), nullable=True, use_existing_column=True)
    # Person/Organization website URL
    org_website_url: Mapped[str] = mapped_column(String(255), nullable=True, use_existing_column=True)
    # Person/Organization contact org_email
    org_email: Mapped[str] = mapped_column(String(64), nullable=True, use_existing_column=True)
    # Version control attributes for Persons that change affiliations

    __mapper_args__ = {
        "polymorphic_identity": ObserverType.ORG,
    }

    def to_dict(self) -> OrderedDict:
        """To be written as Astropy's table metadata"""
        r = super().to_dict()
        r["org_acronym"] = self.org_acronym
        r["org_website_url"] = self.org_website_url
        r["org_email"] = self.org_email
        return r


class Person(Observer):
    observer_id: Mapped[int] = mapped_column(
        ForeignKey("observer_t.observer_id"), primary_key=True, use_existing_column=True
    )
    # Person full name
    name: Mapped[str] = mapped_column(String(255), use_existing_column=True)
    # Observer nickname for individuals, optional as it shares data with Organozation
    nickname: Mapped[str] = mapped_column(String(12), nullable=True, use_existing_column=True)
    # Observer (individual) affiliation to an organization name
    affiliation_id: Mapped[int] = mapped_column(
        ForeignKey("observer_t.observer_id"), nullable=True, use_existing_column=True
    )

    # They are optional because they share table with Organization
    valid_since: Mapped[datetime] = mapped_column(DateTime, nullable=True, use_existing_column=True)
    valid_until: Mapped[datetime] = mapped_column(DateTime, nullable=True, use_existing_column=True)
    valid_state: Mapped[ValidStateType] = mapped_column(
        ValidStateType, nullable=True, use_existing_column=True
    )

    __mapper_args__ = {
        "polymorphic_identity": ObserverType.PERSON,
    }

    # Apparently, this can't be resolved in the ORM mapper ...
    affiliation = relationship(
        "Organization",
        foreign_keys=affiliation_id,
        remote_side=observer_id,
    )
    # affiliation: Mapped[Optional["Organization"]] = relationship()

    def to_dict(self) -> OrderedDict:
        r = super().to_dict()
        r["nickname"] = self.nickname
        r["valid_since"] = self.valid_since.isoformat()
        r["valid_until"] = self.valid_until.isoformat()
        r["valid_state"] = self.valid_state.value
        if self.affiliation:
            r["affiliation"] = self.affiliation.to_dict()
        else:
            r["affiliation"] = None
        return r


class Location(Model):
    __tablename__ = "location_t"

    location_id: Mapped[int] = mapped_column(primary_key=True)
    # Geographical longitude in decimal degrees
    longitude: Mapped[Optional[float]]
    # Geographical in decimal degrees
    latitude: Mapped[Optional[float]]
    # Meters above sea level
    masl: Mapped[Optional[float]]
    # Coordinates type
    coords_meas: Mapped[Optional[CoordinatesType]] = mapped_column(CoordinatesType, nullable=True)
    # Descriptive name of this unitque location
    place: Mapped[str] = mapped_column(String(255), nullable=False)
    # village, town, city, etc name
    population_centre: Mapped[str] = mapped_column(String(255), nullable=False)
    population_centre_type: Mapped[Optional[PopulationCentreType]] = mapped_column(
        PopulationCentreType, nullable=True
    )
    # province, county, etc..
    sub_region: Mapped[str] = mapped_column(String(255), nullable=False)
    # federal state, comunidad autonomica, etc..
    region: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str] = mapped_column(String(64), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)

    __table_args__ = (
        UniqueConstraint("longitude", "latitude"),
        {"extend_existing": True},  # extend_existing is for streamlit only :-(
    )

    def __repr__(self) -> str:
        return str(self.to_dict())

    def to_dict(self) -> OrderedDict:
        """To be written as Astropy's table metadata"""
        r = OrderedDict(
            (key, self.__dict__[key])
            for key in (
                "longitude",
                "latitude",
                "masl",
                "coords_meas",
                "place",
                "population_centre",
                "population_centre_type",
                "sub_region",
                "region",
                "country",
                "timezone",
            )
        )
        # Patch enum & date values
        r["coords_meas"] = self.coords_meas.value
        r["population_centre_type"] = (
            self.population_centre_type.value if self.population_centre_type else None
        )
        return r


class Photometer(Model):
    __tablename__ = "photometer_t"

    phot_id: Mapped[int] = mapped_column(primary_key=True)
    # Either TAS or SQM
    model: Mapped[PhotometerModel] = mapped_column(PhotometerModelCol)
    # Photometer name
    name: Mapped[str] = mapped_column(String(10))
    # Photometer sensor model
    sensor: Mapped[SensorType] = mapped_column(SensorType, default=Sensor.TSL237)
    # Field of view in degrees
    fov: Mapped[Optional[float]]
    # Photometer Zero Point (TAS only)
    zero_point: Mapped[Optional[float]]  # Zero Point id known (i.e. TAS)
    # Photometer level comment
    comment: Mapped[Optional[str]] = mapped_column(String(255))

    __table_args__ = (
        UniqueConstraint(model, name),
        {"extend_existing": True},  # This is for streamlit only :-(
    )

    def __repr__(self) -> str:
        return str(self.to_dict())

    def to_dict(self) -> OrderedDict:
        r = OrderedDict(
            (key, self.__dict__[key])
            for key in (
                "model",
                "name",
                "sensor",
                "zero_point",
                "fov",
                "comment",
            )
        )
        # Patch enum & date values
        r["model"] = self.model.value
        r["sensor"] = self.sensor.value
        return r


class Observation(Model):
    __tablename__ = "observation_t"

    obs_id: Mapped[int] = mapped_column(primary_key=True)
    # Identifier is the original filename, without path or extension
    identifier: Mapped[str] = mapped_column(String(128), unique=True)
    # MD5 File digest to avoid duplicates
    digest: Mapped[str] = mapped_column(String(64), unique=True)
    # Temperature in Celsius, see temperature_meas for meaning
    temperature_1: Mapped[Optional[float]]
    # Temperature in Celsius, see temperature_meas for meaning
    temperature_2: Mapped[Optional[float]]
    # Temperature measurement type
    temperature_meas: Mapped[TemperatureType] = mapped_column(TemperatureType, nullable=False)
    # Humidity, see humidity_meas for meaning
    humidity_1: Mapped[Optional[float]]
    # Humidity, see humidity_meas for meaning
    humidity_2: Mapped[Optional[float]]
    # Huminity measurement type
    humidity_meas: Mapped[HumidityType] = mapped_column(HumidityType, nullable=False)
    # Timestamp 1, see timestamp_meas for meaning
    timestamp_1: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    #  Timestamp 2, see timestamp_meas for meaning
    timestamp_2: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    # Timestamp measurement type
    timestamp_meas: Mapped[TimestampType] = mapped_column(TimestampType, nullable=False)
    # Weather conditions in free text form
    weather_conditions: Mapped[Optional[str]] = mapped_column(String(255))
    # Additional comments
    comment: Mapped[Optional[str]] = mapped_column(String(255))
    # Other observers list (comma separated)
    other_observers: Mapped[Optional[str]] = mapped_column(String(255))
    # Site image URL
    image_url: Mapped[Optional[str]] = mapped_column(String(255))

    # These are relationship attributes
    # These are not real columns, part of the ORM magic
    measurements: Mapped[List["Measurement"]] = relationship(back_populates="observation")

    __table_args__ = {"extend_existing": True}  # This is for streamlit only :-(

    def __repr__(self) -> str:
        return str(self.to_dict())

    def to_dict(self) -> OrderedDict:
        r = OrderedDict(
            (key, self.__dict__[key])
            for key in (
                "identifier",
                "digest",
                "timestamp_1",
                "timestamp_2",
                "timestamp_meas",
                "temperature_1",
                "temperature_2",
                "temperature_meas",
                "humidity_1",
                "humidity_2",
                "humidity_meas",
                "weather_conditions",
                "image_url",
                "other_observers",
                "comment",
            )
        )
        # Patch enum & date values
        r["timestamp_meas"] = self.timestamp_meas.value
        r["temperature_meas"] = self.temperature_meas.value
        r["humidity_meas"] = self.humidity_meas.value
        return r


class Measurement(Model):
    __tablename__ = "measurement_t"

    meas_id: Mapped[int] = mapped_column(primary_key=True)
    date_id: Mapped[int] = mapped_column(ForeignKey("date_t.date_id"))
    time_id: Mapped[int] = mapped_column(ForeignKey("time_t.time_id"))
    observer_id: Mapped[int] = mapped_column(ForeignKey("observer_t.observer_id"))
    location_id: Mapped[int] = mapped_column(ForeignKey("location_t.location_id"))
    phot_id: Mapped[int] = mapped_column(ForeignKey("photometer_t.phot_id"))
    obs_id: Mapped[int] = mapped_column(ForeignKey("observation_t.obs_id"), index=True)
    # Sequence number within the batch, TAS only
    sequence: Mapped[Optional[int]]
    # Azimuth in decimal degrees
    azimuth: Mapped[float]
    # Altitude in decimal degrees
    altitude: Mapped[float]
    # Zenital distance in decimal degrees
    zenital: Mapped[float]
    # Magnitudein mag/arcsec^2
    magnitude: Mapped[float]
    # Photometer frequeincy in Hz, TAS only
    frequency: Mapped[Optional[float]]
    # Sensor temnperature in Celsius, TAS only
    sensor_temp: Mapped[Optional[float]]
    # Infrarred temnperature in Celsius, TAS only
    sky_temp: Mapped[Optional[float]]
    # individual GPŜ longitude in decimal degrees, TAS only
    longitude: Mapped[Optional[float]]
    # individual GPS latitude in decimal degrees, TAS only
    latitude: Mapped[Optional[float]]
    # individual GPS Meters above sea level, TAS only
    masl: Mapped[Optional[float]]
    # Battery voltage, TAS only
    bat_volt: Mapped[Optional[float]]

    # These are relationship attributes
    # These are not real columns, part of the ORM magic
    # Used in insertions of new measurements
    location: Mapped["Location"] = relationship()
    observer: Mapped["Observer"] = relationship()
    photometer: Mapped["Photometer"] = relationship()
    observation: Mapped["Observation"] = relationship(back_populates="measurements")
    date: Mapped["Date"] = relationship()
    time: Mapped["Time"] = relationship()

    __table_args__ = {"extend_existing": True}  # This is for streamlit only :-(

    # We can't establish uniqueness of measurements because manual measurements
    # don't have a unique timestamps, only an initial, final or mid-term timestamp

    def utc_time(self) -> datetime:
        utc = str(self.date_id) + " " + self.time.time
        return datetime.strptime(utc, "%Y%m%d %H:%M:%S").replace(tzinfo=timezone.utc)

    def local_time(self, timezone: str) -> datetime:
        return self.utc_time().astimezone(pytz.timezone(timezone))

    def to_dict(self) -> OrderedDict:
        return OrderedDict(
            (key, self.__dict__[key])
            for key in (
                "sequence",
                "azimuth",
                "altitude",
                "zenital",
                "magnitude",
                "frequency",
                "sensor_temp",
                "sky_temp",
                "longitude",
                "latitude",
                "masl",
                "bat_volt",
            )
        )
