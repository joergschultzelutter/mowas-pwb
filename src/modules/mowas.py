#
# DAPNET Personal Warning Beacon
# Module: Get MOWAS data, check for lat/lon applicability and return
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
import re
import json
import logging
from pprint import pformat
import requests
import numpy as np
from shapely.geometry import Point, Polygon

# Set up the global logger variable
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)


def get_mowas_data(base_url: str, url_path: str):

    url=f"{base_url}{url_path}"
    json_response=None

    try:
        resp = requests.get(url)
    except:
        resp = None
    if resp:
        if resp.status_code == 200:
            # Crude yet effective check. MOWAS does perform redirects and the
            # requests library's "history" flag does not seem to be set for these
            # cases, thus preventing us to tell whether the requested site did
            # experience a redirect or not. We simply check if we did receive
            # something (allegedly) useful and try to convert the content to JSON
            if resp.text.startswith("[") and resp.text.endswith("]"):
                try:
                    json_response = resp.json()
                except:
                    json_response = None
            else:
                json_response = None
        else:
            json_response = None

    success = True if json_response else False
    return success, json_response


if __name__ == "__main__":
    mowas_dictionary = {
    "TEMPEST": "/bbk.dwd/unwetter.json",
    "FLOOD_OLD": "/bbk.wsv/hochwasser.json",
    "FLOOD": "/bbk.lhp/hochwassermeldungen.json",
    "WILDFIRE": "/bbk.dwd/waldbrand.json",
    "EARTHQUAKE": "/bbk.bgr/erdbeben.json",
    "DANGER_ANNOUNCEMENTS": "/bbk.mowas/gefahrendurchsagen.json",
}
    mowas_severity = ["Minor","Moderate","Severe","Extreme"]
    mowas_msgtype = ["Alert","Cancel"]
    mowas_status = ["Actual"]
    mowas_scope = ["Public"]
    mowas_certainty = ["Observed","Unknown"]
    mowas_urgency = ["Immediate","Unknown"]
    mowas_responsetype = ["Prepare","Monitor"]

    for mowas_category in mowas_dictionary:
        success, json_data = get_mowas_data(base_url="https://warnung.bund.de",url_path=mowas_dictionary[mowas_category])
        logger.info(msg=f"Success for mowas_category {mowas_category}: {success}")
        if success:
            for element in json_data:
                mowas_identifier = element["identifier"]
                mowas_status = element["status"]
                if len(element["info"]) > 0:
                    mowas_msgtype=element["msgType"]
                    mowas_severity=element["info"][0]["severity"]
                    mowas_headline=element["info"][0]["headline"]
                    if "description" in element["info"][0]:
                        mowas_description=element["info"][0]["description"]
                    else:
                        mowas_description=""
                    if "instruction" in element["info"][0]:
                        mowas_instruction=element["info"][0]["instruction"]
                    else:
                        mowas_instruction=""

                    logger.info(msg=f"Identifier {mowas_identifier}, Status={mowas_status}, MsgType={mowas_msgtype}, Severity={mowas_severity}, Headline={mowas_headline}")
                    areas = element["info"][0]["area"]
                    for area in areas:
                        polygon = area["polygon"]
                        a = [point.split(',') for point in polygon[0].split(" ")]
                        b = np.array(a, dtype=np.float64)

                        # Create Point objects
                        p1 = Point(8.9183, 51.8127)
                        p2 = Point(24.976567, 60.1612500)
                        poly = Polygon(b)
                        # print (poly)

                        # print(p1.within(poly))
                        #print(p1.intersects(poly))
