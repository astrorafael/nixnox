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

class MyEnum(Enum):
    pass

    # def __repr__(self):
    #     return self.value

    # def __str__(self):
    #     return self.value

class Temperature(MyEnum):
    UNKNOWN = "No temperature"
    INITIAL_FINAL = "Initial & Final temperatures"
    MIN_MAX = "Min & Max temperatures"
    UNIQUE = "Individual temperature measurement"

class Humidity(MyEnum):
    UNKNOWN = "No humidity"
    INITIAL_FINAL = "Initial & Final humidities"
    MIN_MAX ="Max & Min humidities"
    UNIQUE = "Individual humidity measurement"

class Timestamp(MyEnum):
    INITIAl_FINAL = "Start & end timestamp"
    INITAL = "Start timestamp only"
    FINAL = "End timestamp only"
    UNIQUE = "Individual readings timestamp"

class ObserverType(MyEnum):
    PERSON = "Individual"
    ORG = "Organization"

class PhotometerModel(MyEnum):
    TAS = "TAS"
    SQM = "SQM"

class ValidState(MyEnum):
    CURRENT = "Current"
    EXPIRED = "Expired"

  