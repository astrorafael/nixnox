# ----------------------------------------------------------------------
# Copyright (c) 2020
#
# See the LICENSE file for details
# see the AUTHORS file for authors
# ----------------------------------------------------------------------

# --------------------
# System wide imports
# -------------------

import math
import logging

from typing import Any, Tuple, Optional

# -------------------

# -------------------
# Third party imports
# -------------------

from timezonefinder import TimezoneFinder
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter


# -----------
# Own imports
# -----------

from . import PopulationCentre

# ----------------
# Module constants
# ----------------

# Distance to consider all coordinates to be the same place
# between tessdb and MongoDB
# Experimentally determined by establishing a growth curve
# with 1, 10, 50, 100, 150, 200 & 500 m
NEARBY_DISTANCE = 200  # meters
EARTH_RADIUS = 6371009.0  # in meters

# ----------------
# Global variables
# ----------------

geolocator = Nominatim(user_agent="STARS4ALL project")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=2)
tzfinder = TimezoneFinder()


# get the root logger
log = logging.getLogger(__name__.split(".")[-1])


def distance(coords_A: Tuple[float, float], coords_B: Tuple[float, float]):
    """
    Compute approximate geographical distance (arc) [meters] between two points on Earth
    Coods_A and Coords_B are tuples (longitude, latitude)
    Accurate for small distances only
    """
    longitude_A = coords_A[0]
    longitude_B = coords_B[0]
    latitude_A = coords_A[1]
    latitude_B = coords_B[1]
    try:
        delta_long = math.radians(longitude_A - longitude_B)
        delta_lat = math.radians(latitude_A - latitude_B)
        mean_lat = math.radians((latitude_A + latitude_B) / 2)
        result = round(
            EARTH_RADIUS * math.sqrt(delta_lat**2 + (math.cos(mean_lat) * delta_long) ** 2), 0
        )
    except TypeError:
        result = None
    return result


def geolocate(longitude: float, latitude: float) -> Optional[dict[str, Any]]:
    location = geolocator.reverse(f"{latitude}, {longitude}", language="en")
    if location is None:
        log.error(
            "Nominatim didn't find a location for longitude=%s, latitude=%s)", longitude, latitude
        )
        return None
    metadata = location.raw["address"]
    result = dict()
    result["latitude"] = latitude
    result["longitude"] = longitude
    found = False
    for place_type in (
        "leisure",
        "amenity",
        "tourism",
        "building",
        "road",
        "hamlet",
    ):
        try:
            result["place"] = metadata[place_type]
        except KeyError:
            continue
        else:
            found = True
            if place_type == "road" and metadata.get("house_number"):
                result["place"] = metadata[place_type] + ", " + metadata["house_number"]
                result["place_type"] = "road + house_number"
            else:
                result["place_type"] = place_type
            break
    if found:
        log.info("Nominatim place name proposal: '%s' (%s)", result["place"], result["place_type"])
    else:
        result["place"] = None
        result["place_type"] = None
        log.warn("No valid Nominatim place name to suggest")

    for location_type in [loc.value for loc in PopulationCentre]: # Village, town, city, etc.
        try:
            result["pop_centre"] = metadata[location_type]
            result["pop_centre_type"] = PopulationCentre(location_type)
        except KeyError:
            result["pop_centre"] = None
            result["pop_centre_type"] = None
            continue
        else:
            found = True
            break
    if found:
        log.info("Nominatim population centre name proposal: %s (%s)", result["pop_centre"], result["pop_centre_type"])
    else:
        log.warn("No valid Nominatim population centre name to suggest")

    for province_type in ("state_district", "province"):
        try:
            result["sub_region"] = metadata[province_type]
            result["sub_region_type"] = province_type
        except KeyError:
            result["sub_region"] = None
            result["sub_region_type"] = None
            continue
        else:
            found = True
            break
    if found:
        log.info(
            "Nominatim sub_region name proposal: %s (%s)",
            result["sub_region"],
            result["sub_region_type"],
        )
    else:
        log.warn("No valid Nominatim sub_region name to suggest")
    result["region"] = metadata.get("state", None)
    result["region_type"] = "state"
    log.info("Nominatim region name proposal: %s (%s)", result["region"], result["region_type"])
    result["country"] = metadata.get("country", None)
    result["timezone"] = tzfinder.timezone_at(lng=longitude, lat=latitude)
    log.info("TZFinder suggested the following Time Zone: %s", result["timezone"])
    return result
