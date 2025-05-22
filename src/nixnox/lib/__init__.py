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
    MEDIAN = "Median of sensor temperature measurements"

class Humidity(Enum):
    UNKNOWN = "No humidity"
    INITIAL_FINAL = "Initial & Final humidities"
    MIN_MAX ="Max & Min humidities"
    UNIQUE = "Individual humidity measurement"
    MEDIAN = "Median of temperature measurements"

class Timestamp(Enum):
    UNKNOWN = "No timestamp"
    INITIAl_FINAL = "Start & end timestamp"
    INITAL = "Start timestamp only"
    FINAL = "End timestamp only"
    MIDTERM = "Mid term of indivitual timestamp readings"

class Coordinates(Enum):
    UNKNOWN = "No coordinates"
    SINGLE = "Single coordinates"
    MEDIAN = "Median of coordinates values"

class ObserverType(Enum):
    PERSON = "Individual"
    ORG = "Organization"

class PhotometerModel(Enum):
    TAS = "TAS"
    SQM = "SQM"

class ValidState(Enum):
    CURRENT = "Current"
    EXPIRED = "Expired"

# As returned by Nominatim search
class PopulationCentre(Enum):
    VILLAGE = "village"
    MUNICIP = "municipality"
    TOWN = "town"
    CITY = "city"
  