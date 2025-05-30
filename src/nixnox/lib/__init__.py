# ----------------------------------------------------------------------
# Copyright (c) 2022
#
# See the LICENSE file for details
# see the AUTHORS file for authors
# ----------------------------------------------------------------------

# ---------------------
# Third party libraries
# ---------------------

from enum import StrEnum


class Temperature(StrEnum):
    UNKNOWN = "No temperature"
    INITIAL_FINAL = "Initial & Final temperatures"
    MIN_MAX = "Min & Max temperatures"
    UNIQUE = "Individual temperature measurement"
    MEDIAN = "Median of sensor temperature measurements"

class Humidity(StrEnum):
    UNKNOWN = "No humidity"
    INITIAL_FINAL = "Initial & Final humidities"
    MIN_MAX ="Max & Min humidities"
    UNIQUE = "Individual humidity measurement"
    MEDIAN = "Median of temperature measurements"

class Timestamp(StrEnum):
    UNKNOWN = "No timestamp"
    INITIAl_FINAL = "Start & end timestamp"
    INITAL = "Start timestamp only"
    FINAL = "End timestamp only"
    MIDTERM = "Mid term of indivitual timestamp readings"

class Coordinates(StrEnum):
    UNKNOWN = "No coordinates"
    SINGLE = "Single coordinates"
    MEDIAN = "Median of coordinates values"

class ObserverType(StrEnum):
    PERSON = "Person"
    ORG = "Organization"

class PhotometerModel(StrEnum):
    TAS = "TAS"
    SQM = "SQM"

class ValidState(StrEnum):
    CURRENT = "Current"
    EXPIRED = "Expired"

# As returned by Nominatim search
class PopulationCentre(StrEnum):
    VILLAGE = "village"
    MUNICIP = "municipality"
    TOWN = "town"
    CITY = "city"
  