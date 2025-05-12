# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------


# --------------------
# System wide imports
# -------------------


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
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lica.sqlalchemy.dbase import Model

from lica.asyncio.photometer import Sensor

from .. import (
    ObserverType,
    ValidState,
    PhotometerModel,
    Temperature,
    Humidity,
    Coordinates,
    Timestamp,
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

CoordinatesType: Enum = Enum(
    Coordinates,
    name="coordinates_type",
    create_constraint=False,
    metadata=Model.metadata,
    validate_strings=True,
    values_callable=lambda x: [e.value.title() for e in x],
)

# --------
# Entities
# --------


class Date(Model):
    __tablename__ = "nx_date_t"

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
    __tablename__ = "nx_time_t"

    # HHMMSS as integer
    time_id: Mapped[int] = mapped_column(primary_key=True)
    # HH:MM:SS string
    time: Mapped[str] = mapped_column(String(8))
    hour: Mapped[int]
    minute: Mapped[int]
    second: Mapped[int]
    day_fraction: Mapped[float]


class Observer(Model):
    __tablename__ = "nx_observer_t"

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

    def __repr__(self) -> str:
        return (
            f"dict(type={self.type!s}, name={self.name}, nickname={self.nickname}, affiliation={self.affiliation}, "
            f"acronym={self.acronym}, website_url={self.website_url}, email={self.email}, "
            f"valid_since={self.valid_since!s}, valid_until={self.valid_until!s}, valid_state={self.valid_state!s})"
        )

    def to_table(self) -> dict:
        """To be written as Astropy's table metadata"""
        return dict(
            type=self.type.value,
            name=self.name,
            nickname=self.nickname,
            affiliation=self.affiliation,
            acronym=self.acronym,
            website_url=self.website_url,
            email=self.email,
            valid_since=self.valid_since.isoformat(),
            valid_until=self.valid_until.isoformat(),
            valid_state=self.valid_state.value,
        )


class Location(Model):
    __tablename__ = "nx_location_t"

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
    town: Mapped[str] = mapped_column(String(255), nullable=False)
    # province, county, etc..
    sub_region: Mapped[str] = mapped_column(String(255), nullable=False)
    # federal state, comunidad autonomica, etc..
    region: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str] = mapped_column(String(64), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)

    __table_args__ = (UniqueConstraint("longitude", "latitude"), {})

    def __repr__(self) -> str:
        return (
            f"Location(longitude={self.longitude!s}, latitude={self.latitude!s}, masl={self.masl!s}, coords_meas={self.coords_meas!s},"
            f"place={self.place}, town={self.town}, sub_region={self.sub_region}, region={self.region}, country={self.country}, "
            f"timezone={self.timezone})"
        )

    def to_table(self) -> dict:
        """To be written as Astropy's table metadata"""
        return dict(
            longitude=self.longitude,
            latitude=self.latitude,
            masl=self.masl,
            coords_meas=self.coords_meas.value,
            place=self.place,
            town=self.town,
            sub_region=self.sub_region,
            region=self.region,
            country=self.country,
            timezone=self.timezone,
        )


class Photometer(Model):
    __tablename__ = "nx_photometer_t"

    phot_id: Mapped[int] = mapped_column(primary_key=True)
    # Either TAS or SQM
    model: Mapped[PhotModelType] = mapped_column(PhotModelType)
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
        {},
    )

    def __repr__(self) -> str:
        return (
            f"Photometer(model={self.model!s}, name={self.name}, sensor={self.sensor!s}, "
            f"fov={self.fov!s}, zero_point={self.zero_point!s}, comment={self.comment})"
        )

    def to_table(self) -> dict:
        return dict(
            model=self.model.value,
            name=self.name,
            sensor=self.sensor.value,
            fov=self.fov,
            zero_point=self.zero_point,
            comment=self.comment,
        )


class Observation(Model):
    __tablename__ = "nx_observation_t"

    obs_id: Mapped[int] = mapped_column(primary_key=True)
    # Identifier is the original filename, without path or extension
    identifier: Mapped[str] = mapped_column(String(128))
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

    def __repr__(self) -> str:
        return (
            f"Observation(identifier={self.identifier!s}, digest={self.digest}, "
            f"temperature_1={self.temperature_1!s}, temperature_2={self.temperature_2!s}, temperature_meas={self.temperature_meas.value} "
            f"humidity_1={self.humidity_1!s}, humidity_2={self.humidity_2!s}, humidity_meas={self.humidity_meas.value}, "
            f"timestamp_1={self.timestamp_1!s}, timestamp_2={self.timestamp_2!s}, timestamp_meas={self.timestamp_meas.value}, , "
            f"weather_conditions={self.weather_conditions}, image_url={self.image_url}, other_observers={self.other_observers}, "
            f"comment={self.comment})"
        )

    def to_table(self) -> dict:
        return dict(
            identifier=self.identifier,
            digest=self.digest,
            temperature_1=self.temperature_1,
            temperature_2=self.temperature_2,
            temperature_meas=self.temperature_meas.value,
            humidity_1=self.humidity_1,
            humidity_2=self.humidity_2,
            humidity_meas=self.humidity_meas.value,
            timestamp_1=self.timestamp_1,
            timestamp_2=self.timestamp_2,
            timestamp_meas=self.timestamp_meas.value,
            weather_conditions=self.weather_conditions,
            image_url=self.image_url,
            other_observers=self.other_observers,
            comment=self.comment,
        )


class Measurement(Model):
    __tablename__ = "nx_measurement_t"

    meas_id: Mapped[int] = mapped_column(primary_key=True)
    date_id: Mapped[int] = mapped_column(ForeignKey("nx_date_t.date_id"))
    time_id: Mapped[int] = mapped_column(ForeignKey("nx_time_t.time_id"))
    observer_id: Mapped[int] = mapped_column(ForeignKey("nx_observer_t.observer_id"))
    location_id: Mapped[int] = mapped_column(ForeignKey("nx_location_t.location_id"))
    phot_id: Mapped[int] = mapped_column(ForeignKey("nx_photometer_t.phot_id"))
    obs_id: Mapped[int] = mapped_column(ForeignKey("nx_observation_t.obs_id"))
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

    # We can't establish uniqueness of measurements because manual measurements
    # don't have a unique timestamps, only an initial, final or mid-term timestamp

    def utc_time(self) -> datetime:
        utc = str(self.date_id) + " " + self.time.time
        return datetime.strptime(utc, "%Y%m%d %H:%M:%S").replace(tzinfo=timezone.utc)

    def local_time(self, timezone: str) -> datetime:
        return self.utc_time().astimezone(pytz.timezone(timezone))
