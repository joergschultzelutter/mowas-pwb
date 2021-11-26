#
# Geopy address lookup based on lat/lon
# Author: Joerg Schultze-Lutter, 2021
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

from geopy.geocoders import Nominatim
import logging
import requests

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)

# Default user agent which is used by the program for sending requests to aprs.fi
default_user_agent = f"mowas-pwb (+https://github.com/joergschultzelutter/mowas-pwb/)"


def get_reverse_geopy_data(latitude: float, longitude: float, language: str = "de"):
    """
    Get human-readable address data for a lat/lon combination
    ==========
    latitude: 'float'
        Latitude
    longitude: 'float'
        Longitude
    language: 'str'
        iso3166-2 language code
    Returns
    =======
    success: 'bool'
        True if query was successful
    response_data: 'dict'
        Response dict with city, country, ...
    """

    address = city = country = country_code = county = None
    zipcode = state = street = street_number = district = None

    # Geopy Nominatim user agent
    geolocator = Nominatim(user_agent=default_user_agent)

    success = False
    try:
        # Lookup with zoom level 18 (building)
        location = geolocator.reverse(
            query=f"{latitude} {longitude}",
            language=language,
            zoom=18,
            addressdetails=True,
            exactly_one=True,
        )
    except:
        location = None
    if location:
        address = location.address
        if "address" in location.raw:
            success = True
            if "city" in location.raw["address"]:
                city = location.raw["address"]["city"]
            if "town" in location.raw["address"]:
                city = location.raw["address"]["town"]
            if "village" in location.raw["address"]:
                city = location.raw["address"]["village"]
            if "hamlet" in location.raw["address"]:
                city = location.raw["address"]["hamlet"]
            if "county" in location.raw["address"]:
                county = location.raw["address"]["county"]
            if "country_code" in location.raw["address"]:
                country_code = location.raw["address"]["country_code"]
                country_code = country_code.upper()
            if "country" in location.raw["address"]:
                country = location.raw["address"]["country"]
            if "district" in location.raw["address"]:
                district = location.raw["address"]["district"]
            if "postcode" in location.raw["address"]:
                zipcode = location.raw["address"]["postcode"]
            if "road" in location.raw["address"]:
                street = location.raw["address"]["road"]
            if "house_number" in location.raw["address"]:
                street_number = location.raw["address"]["house_number"]
            if "state" in location.raw["address"]:
                state = location.raw["address"]["state"]
            if not city:
                if "man_made" in location.raw["address"]:
                    city = location.raw["address"]["man_made"]
            if not city:
                if "neighborhood" in location.raw["address"]:
                    city = location.raw["address"]["neighborhood"]

    response_data = {
        "city": city,
        "state": state,
        "county": county,
        "country": country,
        "district": district,
        "country_code": country_code,
        "zipcode": zipcode,
        "street": street,
        "street_number": street_number,
        "address": address,
    }

    return success, response_data


if __name__ == "__main__":
    logger.info(get_reverse_geopy_data(latitude=37.7790262, longitude=-122.4199061))
