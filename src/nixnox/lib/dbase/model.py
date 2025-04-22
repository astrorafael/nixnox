# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------


# --------------------
# System wide imports
# -------------------

import sys
import logging

from typing import Optional, List
from datetime import datetime

# =====================
# Third party libraries
# =====================

from sqlalchemy import (
    select,
    func,
    Enum,
    Table,
    Column,
    Integer,
    Float,
    String,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, aliased

from lica.sqlalchemy.dbase import Model

from lica.asyncio.photometer import Sensor

from .. import ObserverType, ValidState, PhotometerModel, Temperature, Humidity, Timestamp

# ================
# Module constants
# ================

# =======================
# Module global variables
# =======================

# get the module logger
log = logging.getLogger(__name__)


def datestr(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S.%f") if dt is not None else None


# =================================
# Data Model, declarative ORM style
# =================================

# ---------------------------------------------
# Additional conveniente types for enumerations
# ---------------------------------------------

ObserverEnum: Enum = Enum(
    ObserverType,
    name="observer_type",
    create_constraint=False,
    metadata=Model.metadata,
    validate_strings=True,
    values_callable=lambda x: [e.value.title() for e in x],
)

PhotModelType: Enum = Enum(
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


class Observer(Model):
    __tablename__ = "observer_t"

    observer_id: Mapped[int] = mapped_column(primary_key=True)
    # Either Indiviudal or Organization
    type: Mapped[ObserverEnum] = mapped_column(ObserverEnum, nullable=False)
    # Full name or organization name
    name: Mapped[str] = mapped_column(String(255))
    # Observer nickname for indivoiduals
    nickname: Mapped[Optional[str]] = mapped_column(String(12), nullable=True)
    # Observer (individual) affiliation (an organization name)
    affiliation: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # Organization acronym
    acronym: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    # Individual/Organization website URL
    website_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # Individual/Organization contact email
    email: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    # Version control attributes for Individuals that change affiliations
    valid_since: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    valid_until: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    valid_state: Mapped[ValidStateType] = mapped_column(ValidStateType, nullable=False)

    __table_args__ = (UniqueConstraint(name, valid_since, valid_until), {})


class Location(Model):
    __tablename__ = "location_t"

    location_id: Mapped[int] = mapped_column(primary_key=True)
    # Geographical longitude in decimal degrees
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    # Geographical in decimal degrees
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    # Meters above sea level
    msl: Mapped[Optional[float]]
    # Descriptive name of this unitque location
    place: Mapped[str] = mapped_column(String(255), nullable=False)
    # village, town, city, etc name
    town: Mapped[str] = mapped_column(String(255), nullable=False)  # .
    # province, county, etc..
    sub_region: Mapped[str] = mapped_column(String(255), nullable=False)
    # federal state, comunidad autonomica, etc..
    region: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str] = mapped_column(String(64), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)

    __table_args__ = (UniqueConstraint(longitude, latitude), {})


class Flags(Model):
    __tablename__ = "flags_t"

    flags_id: Mapped[int] = mapped_column(primary_key=True)
    # Temperature measurement type
    temperature_meas: Mapped[TemperatureType] = mapped_column(TemperatureType, nullable=False)
    # Huminity measurement type
    humidity_meas: Mapped[HumidityType] = mapped_column(HumidityType, nullable=False)
    # Tiemstamp measurement type
    timestamp_meas: Mapped[TimestampType] = mapped_column(TimestampType, nullable=False)


class Photometer(Model):
    __tablename__ = "photometer_t"

    phot_id: Mapped[int] = mapped_column(primary_key=True)
    # Either TAS or SQM
    model: Mapped[PhotModelType] = mapped_column(PhotModelType)
    # Photometer name
    name: Mapped[str] = mapped_column(String(10))
    # SQM serial id or TAS identifier (i.e. MAC)
    identifier: Mapped[str] = mapped_column(String(17))
    # Photometer sensor model
    sensor: Mapped[SensorType] = mapped_column(SensorType, default=Sensor.TSL237)
    # Field of view in degrees
    fov: Mapped[Optional[float]]
    # Photometer Zero Point (TAS only)
    zero_point: Mapped[Optional[float]]  # Zero Point id known (i.e. TAS)
    # Photometer level comment
    comment: Mapped[Optional[str]] = mapped_column(String(255))

    __table_args__ = (
        UniqueConstraint(name, identifier),
        {},
    )


class ObservationSet(Model):
    __tablename__ = "observation_set_t"

    obs_set_id: Mapped[int] = mapped_column(primary_key=True)
    # MD5 File digest to avoid duplicates
    digest: Mapped[str] = mapped_column(String(64), unique=True)
    # Temperature in Celsius, see flags for meaning
    temperature_1: Mapped[Optional[float]]
    # Temperature in Celsius, see flags for meaning
    temperature_2: Mapped[Optional[float]]
    # Humidity, see flags for meaning
    humidity_1: Mapped[Optional[float]]
    # Humidity, see flags for meaning
    humidity_2: Mapped[Optional[float]]
    # Weather conditions in free text form
    weather_conditions: Mapped[Optional[str]] = mapped_column(String(255))
    # Additional comments
    comment: Mapped[Optional[str]] = mapped_column(String(255))
    # Other observers list (comma separated)
    other_observers: Mapped[Optional[str]] = mapped_column(String(255))
    # Site image URL
    image_url: Mapped[Optional[str]] = mapped_column(String(255))


class Observation(Model):
    __tablename__ = "observation_t"

    obs_id: Mapped[int] = mapped_column(primary_key=True)
    date_id: Mapped[int] = mapped_column(ForeignKey("date_t.date_id"))
    time_id: Mapped[int] = mapped_column(ForeignKey("time_t.time_id"))
    observer_id: Mapped[int] = mapped_column(ForeignKey("observer_t.observer_id"))
    location_id: Mapped[int] = mapped_column(ForeignKey("location_t.location_id"))
    phot_id: Mapped[int] = mapped_column(ForeignKey("photometer_t.phot_id"))
    obs_set_id: Mapped[int] = mapped_column(ForeignKey("observation_set_t.obs_set_id"))
    flags_id: Mapped[int] = mapped_column(ForeignKey("flags_t.flags_id"))
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
    # Infrarred temnperature in Celsious, TAS only
    sky_temp: Mapped[Optional[float]]
    # Battery voltage, TAS only
    vbat: Mapped[Optional[float]]
