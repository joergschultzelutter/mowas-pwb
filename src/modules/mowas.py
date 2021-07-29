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
from expiringdict import ExpiringDict

# Set up the global logger variable
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)


def download_mowas_data(base_url: str, url_path: str):

    with open("gefahrendurchsagen06.txt", "r") as f:
        if f.mode == "r":
            json_response = json.load(f)
            return True, json_response

    logger.info("Hier sollten wir nicht hinkommen")
    exit(0)

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


def process_mowas_data(coordinates: list, mowas_cache: ExpiringDict):
    mowas_new_messages_to_send = {}

    mowas_dictionary = {
    "TEMPEST": "/bbk.dwd/unwetter.json",
    "FLOOD_OLD": "/bbk.wsv/hochwasser.json",
    "FLOOD": "/bbk.lhp/hochwassermeldungen.json",
    "WILDFIRE": "/bbk.dwd/waldbrand.json",
    "EARTHQUAKE": "/bbk.bgr/erdbeben.json",
    "DANGER_ANNOUNCEMENTS": "/bbk.mowas/gefahrendurchsagen.json",
}
    typedef_mowas_severity = ["Minor","Moderate","Severe","Extreme"]
    typedef_mowas_msgtype = ["Alert","Cancel","Update"]
    typdef_mowas_status = ["Actual"]
    typedef_mowas_scope = ["Public"]
    typedef_mowas_certainty = ["Observed","Unknown"]
    typedef_mowas_urgency = ["Immediate","Unknown"]
    typedef_mowas_responsetype = ["Prepare","Monitor"]

    for mowas_category in mowas_dictionary:
        success, json_data = download_mowas_data(base_url="https://warnung.bund.de",url_path=mowas_dictionary[mowas_category])
        logger.info(msg=f"Success for mowas_category {mowas_category}: {success}")
        if success:
            for element in json_data:
        
                # Extract the message's identifier - this is our message's primary key
                mowas_identifier = element["identifier"]

                # get the message's msgtype. Can either be Alert, Update or Cancel
                mowas_msgtype=element["msgType"]
                assert mowas_msgtype in typedef_mowas_msgtype
               
                # Get the timestamp when this message was sent
                mowas_sent = element["sent"]

                # Now let's check what we are supposed to do with this message
                # If the message is of type "Cancel", remove it from our ExpiringDict
                # and continue with the next potential message.
                if mowas_msgtype == "Cancel":
                    if mowas_identifier in mowas_cache:
                        mowas_cache.pop(mowas_identifier)
                    continue
                # If we deal with an "Update", there are a few situations that need
                # to be taken upder advisement:
                # 1) Key does not yet exist in our dictionary. ACTION: we will add it
                #    The entry may never have been added to the dictionary OR was
                #    present in the past but did experience its end-of-life
                # 2) Key does exist within our dictionary, but msgtype is not "Update"
                #    In this particular case, we might switch from "Action" to "Update".
                #    As the message's coordinate ranges may have changed, we will remove
                #    the entry from our dictionary and re-add it
                # 3) Key does exist within our dictionary AND msgtype is "Update". This
                #    will trigger no action on our end
                elif mowas_msgtype == "Update":
                    # Do we have this entry in our expiring cache?
                    if mowas_identifier in mowas_cache:
                        # get the payload
                        mowas_payload = mowas_cache[mowas_identifier]

                        # then extract the msgtype from the payload
                        mowas_cache_msgtype = mowas_payload["msgtype"]
                        # Does its new status differ from the previous one? Then remove it 
                        # from our dictionary. This entry is either an Alert > Update or
                        # Update > Alert
                        if mowas_cache_msgtype != mowas_msgtype:
                            mowas_cache.pop(mowas_identifier)
                        else:
                            # Get the timestamp on when the data was sent
                            mowas_cache_sent = mowas_payload["sent"]
                            # See if the timestamps differ. Hint: this is a string comparison
                            # If both entries differ, then let's get rid of the previous entry 
                            if mowas_sent != mowas_cache_sent:
                                mowas_cache.pop(mowas_identifier)
        
                mowas_status = element["status"]
                if len(element["info"]) > 0:
                    mowas_severity=element["info"][0]["severity"]
                    mowas_headline=element["info"][0]["headline"]
                    mowas_description = None
                    if "description" in element["info"][0]:
                        mowas_description=element["info"][0]["description"]
                    mowas_instruction = None
                    if "instruction" in element["info"][0]:
                        mowas_instruction=element["info"][0]["instruction"]

                    areas = element["info"][0]["area"]
                    for area in areas:
                        polygon = area["polygon"]
                        splitted_array = [point.split(',') for point in polygon[0].split(" ")]
                        numpy_array = np.array(a, dtype=np.float64)
                        poly = Polygon(numpy_array)

                        for coord in coordinates:
                            latitude = coord["latitude"]
                            longitude = coord["longitude"]
                            p = Point(latitude,longitude)
                            match = p.within(poly) | p.intersects(poly)


    return mowas_cache, mowas_new_messages_to_send

if __name__ == "__main__":
    mowas_message_cache = ExpiringDict(max_len = 1000, max_age_seconds=30*60) 
    my_coordinates = [
        {
            "latitude": 8.9183,
            "longitude": 51.8127,
        },
        {
            "latitude": 24.976567,
            "longitude": 60.1612500,
        }
    ]
    pass