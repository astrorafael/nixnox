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

    date_id: Mapped[int] = mapped_column(primary_key=True)
    sql_date: Mapped[str] = mapped_column(String(10))  # YYYY-MM-DD
    date: Mapped[str] = mapped_column(String(10))  # DD/MM/YYYY
    day: Mapped[int]
    day_year: Mapped[int]
    julian_day: Mapped[float]
    weekday: Mapped[str] = mapped_column(String(9))
    weekday_abbr: Mapped[str] = mapped_column(String(3))
    weekday_num: Mapped[int]
    month_num: Mapped[int]
    month: Mapped[str] = mapped_column(String(8))  # January, February, March, ...
    month_abbr: Mapped[str] = mapped_column(String(3))  # Jan, Feb, Mar, ...
    year: Mapped[int]


class Time(Model):
    __tablename__ = "time_t"

    time_id: Mapped[int] = mapped_column(primary_key=True)
    time: Mapped[str] = mapped_column(String(8))  # HH:MM:SS
    hour: Mapped[int]
    minute: Mapped[int]
    second: Mapped[int]
    day_fraction: Mapped[float]


class Observer(Model):
    __tablename__ = "observer_t"

    observer_id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[ObserverEnum] = mapped_column(ObserverEnum, nullable=False)
    name: Mapped[str] = mapped_column(String(255))  # Full name or organization name
    nickname: Mapped[Optional[str]] = mapped_column(String(12), nullable=True)  # if person
    affiliation: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # if person
    acronym: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)  # both types
    website_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # both types
    email: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # both types
    valid_since: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    valid_until: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    valid_state: Mapped[ValidStateType] = mapped_column(ValidStateType, nullable=False)

    __table_args__ = (UniqueConstraint(name, valid_since, valid_until), {})


class Location(Model):
    __tablename__ = "location_t"

    location_id: Mapped[int] = mapped_column(primary_key=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # in decimal degrees
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # in decimal degrees
    msl: Mapped[Optional[float]]  # metersa above sea level in meters
    place: Mapped[str] = mapped_column(String(255), nullable=False)  # the actual place name
    town: Mapped[str] = mapped_column(String(255), nullable=False)  # village, town, city, etc.
    sub_region: Mapped[str] = mapped_column(String(255), nullable=False)  # province, etc.
    region: Mapped[str] = mapped_column(
        String(255), nullable=False
    )  # fedral state, comunidad autonomica, etc..
    country: Mapped[str] = mapped_column(String(64), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)

    __table_args__ = (UniqueConstraint(longitude, latitude), {})


class Flags(Model):
    __tablename__ = "flags_t"

    flags_id: Mapped[int] = mapped_column(primary_key=True)
    temperature_meas: Mapped[TemperatureType] = mapped_column(TemperatureType, nullable=False)
    humidity_meas: Mapped[HumidityType] = mapped_column(HumidityType, nullable=False)
    timestamp_meas: Mapped[TimestampType] = mapped_column(TimestampType, nullable=False)


class Photometer(Model):
    __tablename__ = "photometer_t"

    phot_id: Mapped[int] = mapped_column(primary_key=True)
    model: Mapped[PhotModelType] = mapped_column(PhotModelType)
    name: Mapped[str] = mapped_column(String(10))
    identifier: Mapped[str] = mapped_column(String(17))  # SQM serial id or TAS identifier
    sensor: Mapped[SensorType] = mapped_column(SensorType, default=Sensor.TSL237)
    fov: Mapped[Optional[float]]  # Field of view in degrees
    zero_point: Mapped[Optional[float]]  # Zero Point id known (i.e. TAS)
    comment: Mapped[Optional[str]] = mapped_column(String(255))  # Photometer level comment

    __table_args__ = (
        UniqueConstraint(name, identifier),
        {},
    )


class ObservationSet(Model):
    __tablename__ = "observation_set_t"

    obs_set_id: Mapped[int] = mapped_column(primary_key=True)
    digest: Mapped[str] = mapped_column(String(64), unique=True)  # MD5 hash
    temperature_1: Mapped[Optional[float]]  # See flags for details
    temperature_2: Mapped[Optional[float]]
    humidity_1: Mapped[Optional[float]]  # See flags for details
    humidity_2: Mapped[Optional[float]]
    weather_conditions: Mapped[Optional[str]] = mapped_column(
        String(255)
    )  # weather conditions In free text form
    comment: Mapped[Optional[str]] = mapped_column(String(255))  # Observation set comment
    other_observers: Mapped[Optional[str]] = mapped_column(String(255))  # other observers list
    image_url: Mapped[Optional[str]] = mapped_column(String(255))  # site image as an URL


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

    azimuth: Mapped[float]  # In decimal degrees
    altitude: Mapped[float]  # In decimal degrees
    zenital: Mapped[float]  # 90 - altitude
    magnitude: Mapped[float]
    frequency: Mapped[Optional[float]]  # Only for TAS
    sky_temp: Mapped[Optional[float]]  # Only for TAS
