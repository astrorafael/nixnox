# ----------------------------------------------------------------------
# Copyright (c) 2022
#
# See the LICENSE file for details
# see the AUTHORS file for authors
# ----------------------------------------------------------------------

# ---------------------
# Third party libraries
# ---------------------

from enum import Enum


class Temperature(Enum):
    UNKNOWN = "No temperature"
    INITIAL_FINAL = "Initial & Final temperatures"
    MIN_MAX = "Min & Max temperatures"
    UNIQUE = "Individual temperature measurement"
    MEDIAN = "Median of temperature measurements"

class Humidity(Enum):
    UNKNOWN = "No humidity"
    INITIAL_FINAL = "Initial & Final humidities"
    MIN_MAX ="Max & Min humidities"
    UNIQUE = "Individual humidity measurement"
    MEDIAN = "Median of temperature measurements"

class Timestamp(Enum):
    INITIAl_FINAL = "Start & end timestamp"
    INITAL = "Start timestamp only"
    FINAL = "End timestamp only"
    UNIQUE = "Individual readings timestamp"

class Coordinates(Enum):
    SINGLE = "Single Coordinates"
    MEDIAN = "Median of Coordinates Values"

class ObserverType(Enum):
    PERSON = "Individual"
    ORG = "Organization"

class PhotometerModel(Enum):
    TAS = "TAS"
    SQM = "SQM"

class ValidState(Enum):
    CURRENT = "Current"
    EXPIRED = "Expired"

  