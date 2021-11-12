#
# MOWAS Personal Warning Beacon
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
import json
import logging
import requests
import numpy as np
from shapely.geometry import Point, Polygon
from expiringdict import ExpiringDict
from utils import remove_html_content

# Set up the global logger variable
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)


def download_mowas_data(base_url: str, url_path: str):
    """
    Function which (tries to) download content from the MOWAS servers
    Parameters
    ==========
    base_url : 'str'
            Server base URL (usually fixed, e.g. https://warnung.bund.de)
    url_path : 'str'
            Server URL path (dependent on the MOWAS category that we intend to download)
    Returns
    =======
    success : 'bool'
            True if operation was successful
    json_response: 'dict'
            Dictionary which contains the corresponding JSON object
    """

    with open("gefahr06.txt", "r") as f:
        if f.mode == "r":
            json_response = json.load(f)
            return True, json_response
    """
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
	"""


def process_mowas_data(
    coordinates: list,
    mowas_cache: ExpiringDict,
    minimal_mowas_severity: str = "Minor",
    mowas_dapnet_high_prio_level: str = "Minor",
    mowas_active_categories: list = [
        "TEMPEST",
        "FLOOD",
        "FLOOD_OLD",
        "WILDFIRE",
        "EARTHQUAKE",
        "DISASTERS",
    ],
    enable_covid_messaging: bool = False,
):
    """
    Process our MOWAS data and return a dictionary with messages that are to be sent to the user
    Parameters
    ==========
    coordinates : 'list'
            List item, containing 0..n dictionaries with lat/lon coordinates that we are supposed to check
    mowas_cache : 'ExpiringDict'
            ExpiringDict which contains the "Alert" and "Update" messages from a previous run that were
            sent to the user. "Cancel" messages are not included - they may only be sent out once.
    minimal_mowas_severity : 'str'
            Needs to contain a valid severity level (see definition of 'typedef_mowas_severity')
            Program uses a ranking mechanism for its ">=" evaluation
    Returns
    =======
    mowas_cache : 'ExpiringDict'
            (Potentially) updated version of the mowas_cache input parameter
    mowas_messages_to_send: 'dict'
            Dictionary which contains the messages that we may need to send to the user
    """

    # Dictionary which may contain our outgoing messages (if present)
    mowas_messages_to_send = {}

    # These are the official MOWAS URLs which our code will try to query
    # Some of these URLs have no (longer?) any content
    mowas_dictionary = {
        "TEMPEST": "/bbk.dwd/unwetter.json",
        "FLOOD_OLD": "/bbk.wsv/hochwasser.json",
        "FLOOD": "/bbk.lhp/hochwassermeldungen.json",
        "WILDFIRE": "/bbk.dwd/waldbrand.json",
        "EARTHQUAKE": "/bbk.bgr/erdbeben.json",
        "DISASTERS": "/bbk.mowas/gefahrendurchsagen.json",
    }

    # Definitions for all possible valid values that MOWAS may provide us with
    # Important:
    # 'typedef_mowas_security' requires value changes to be added in increasing
    # severity levels - we use this list for quite a few queries
    typedef_mowas_severity = ["Minor", "Moderate", "Severe", "Extreme"]
    typedef_mowas_msgtype = ["Alert", "Cancel", "Update"]
    typdef_mowas_status = ["Actual"]
    typedef_mowas_scope = ["Public"]
    typedef_mowas_certainty = ["Observed", "Unknown"]
    typedef_mowas_urgency = ["Immediate", "Unknown"]
    typedef_mowas_responsetype = ["Prepare", "Monitor"]

    # Check if we have received something whose value we already know
    assert minimal_mowas_severity in typedef_mowas_severity
    assert mowas_dapnet_high_prio_level in typedef_mowas_severity

    # message marker which tells us that we have received at least one
    # Alert or Update message
    got_alert_or_update = False

    # For each of our own categories, try to download the MOWAS data
    for mowas_category in mowas_dictionary:
        # Only process this category if it is set as "active"
        # in the program config file
        if mowas_category in mowas_active_categories:
            # OK, let's try to get that data from the government server
            success, json_data = download_mowas_data(
                base_url="https://warnung.bund.de",
                url_path=mowas_dictionary[mowas_category],
            )
            logger.debug(msg=f"Processing mowas_category {mowas_category}: {success}")
            if success:
                for element in json_data:
                    # general marker which tells us whether we should send this message
                    # if it meets all criteria
                    process_this_message = False

                    # Extract the message's identifier - this is our message's primary key
                    mowas_identifier = element["identifier"]

                    # get the message's msgtype. Can either be Alert, Update or Cancel
                    mowas_msgtype = element["msgType"]
                    assert mowas_msgtype in typedef_mowas_msgtype

                    # Get the timestamp when this message was sent
                    mowas_sent = element["sent"]

                    # Now let's check what we are supposed to do with this message
                    # If the message is of type "Cancel", remove it from our ExpiringDict
                    # (if present). The program guarantees that only the message types
                    # "Alert" and "Update" are present in our list
                    if mowas_msgtype == "Cancel":
                        # Check if this message is present in our dict and remove it
                        if mowas_identifier in mowas_cache:
                            mowas_cache.pop(mowas_identifier)
                            # We still want to send this "Cancel" message to the user
                            # so let's ensure that we remember to do so. Still, the
                            # cancel message is only sent if the message's geocoordinates
                            # match with what the user has provided us with
                            process_this_message = True

                    # If we deal with an "Update", there are a few situations that need
                    # to be taken upder advisement:
                    # 1) Key does not yet exist in our dictionary. ACTION: we will add it
                    # 	 The entry may never have been added to the dictionary OR was
                    # 	 present in the past but did experience its end-of-life
                    # 2) Key does exist within our dictionary, but msgtype is not "Update"
                    # 	 In this particular case, we might switch from "Action" to "Update".
                    # 	 As the message's coordinate ranges may have changed, we will remove
                    # 	 the entry from our dictionary and re-add it
                    # 3) Key does exist within our dictionary AND msgtype is "Update". This
                    # 	 will trigger no action on our end UNLESS the old "Update" message's
                    # 	 time stamp differs with the one from the new message
                    elif mowas_msgtype == "Update":
                        # Do we have this entry in our expiring cache?
                        if mowas_identifier in mowas_cache:
                            # get the payload
                            mowas_payload = mowas_cache[mowas_identifier]

                            # then extract the msgtype from the payload
                            mowas_cache_msgtype = mowas_payload["msgtype"]
                            # Does its new status differ from the previous one? Then remove it
                            # from our dictionary. This entry is either an Alert > Update or
                            # Update > Alert (the latter should never happen)
                            if mowas_cache_msgtype != mowas_msgtype:
                                mowas_cache.pop(mowas_identifier)
                            else:
                                # message types are both "Update"
                                # Get the timestamp on when the data was sent
                                mowas_cache_sent = mowas_payload["sent"]
                                # See if the timestamps differ. Hint: this is a string comparison
                                # If both entries differ, then let's get rid of the previous entry
                                if mowas_sent != mowas_cache_sent:
                                    mowas_cache.pop(mowas_identifier)
                                    # As the time stamps differ, remember that we may need to send
                                    # this message if it fits our criteria
                                    process_this_message = True
                        else:
                            # msgtype is "Update" but the message is not within our cache
                            # Potential root causes:
                            # 1) message was in the cache but has expired (and got removed)
                            # 2) message was never in the case (e.g. due to a program restart)
                            process_this_message = True
                    elif mowas_msgtype == "Alert":
                        # Is this entry NOT in our expiring cache? Then let's process it
                        # Assumptions:
                        # 1) Message status cannot move back from "Update" to "Alert"
                        # 2) Whenever an "Alert" gets updated, its msgtype changes to "Update"
                        if mowas_identifier not in mowas_cache:
                            process_this_message = True

                    # Now that we have determined if we should process this message or not,
                    # let's have a look at the actual message itself - that is, if
                    # we are supposed to process it.
                    if process_this_message:
                        mowas_status = element["status"]

                        # All MOWAS messages only seen to have one (1) sub element only
                        # but let's ensure that our present message actually has one.
                        # Future program versions may also need to process elements 2..n
                        # in case they are present.
                        if len(element["info"]) > 0:

                            # Get the Severity
                            mowas_severity = element["info"][0]["severity"]

                            # Crash for now if we encounter an unknown severity
                            assert mowas_severity in typedef_mowas_severity

                            # Loop to the next element in case our current message's
                            # severity level is too low (based on the user's input parameters)
                            if typedef_mowas_severity.index(
                                mowas_severity
                            ) < typedef_mowas_severity.index(minimal_mowas_severity):
                                continue

                            # Check the priority level of the future message to DAPNET and bump it up if necessary
                            # but lower its priority if we deal with a "Cancel" message
                            if mowas_msgtype != "Cancel":
                                dapnet_high_prio_msg = (
                                    True
                                    if typedef_mowas_severity.index(
                                        mowas_dapnet_high_prio_level
                                    )
                                    >= typedef_mowas_severity.index(mowas_severity)
                                    else False
                                )
                            else:
                                dapnet_high_prio_msg = False

                            # Now let's extract the remaining information before we take a look at the message's geometric structure
                            mowas_headline = element["info"][0]["headline"]
                            mowas_urgency = element["info"][0]["urgency"]
                            mowas_severity = element["info"][0]["severity"]
                            mowas_description = (
                                element["info"][0]["description"]
                                if "description" in element["info"][0]
                                else None
                            )
                            mowas_instruction = mowas_instruction = (
                                element["info"][0]["instruction"]
                                if "instruction" in element["info"][0]
                                else None
                            )

                            # Extract the list of areas from the element
                            areas = element["info"][0]["area"]

                            # If any of the given lat/lon coordinates from the user match with
                            # any of the given areas from this message, then we may want to send out
                            # this message to the user
                            area_matches_with_user_latlon = False

                            # If we find a match then this list will contain all areas for
                            # which we found a match related to our lat/lon coordinates
                            areas_matching_latlon = []
                            areas_matching_latlon_abbrev = []   # Abbreviated version for DAPNET as we only have 80 chars
                            geocodes_matching_latlon = []
                            coords_matching_latlon = []

                            for area in areas:
                                polygon = area["polygon"]
                                # fmt: off
                                # First, convert original MOWAS data to an array list
                                lonlat_array = [point.split(",") for point in polygon[0].split(" ")]
                                # and then convert it from lon/lat to lat/lon as we need that format later
                                latlon_array = [(float(val[1]), float(val[0])) for val in lonlat_array]
                                # fmt: on

                                #
                                numpy_array = np.array(latlon_array, dtype=np.float64)
                                poly = Polygon(numpy_array)

                                # Coord has the format latitude,longitude
                                for coord in coordinates:
                                    latitude = coord[0]
                                    longitude = coord[1]

                                    # Let's create our coordinate that we want to check
                                    p = Point(latitude, longitude)

                                    # Check if we are either inside of the polygon or
                                    # touch its borders
                                    area_match = p.within(poly) or p.intersects(poly)

                                    # and set our global marker if we have found something
                                    area_matches_with_user_latlon = (
                                        True
                                        if area_match
                                        else area_matches_with_user_latlon
                                    )

                                    # if we have found something for the current area, then
                                    # let's remember the area for which we had a match
                                    if area_match:
                                        area_desc = area["areaDesc"]
                                        if "geocode" in area:
                                            geocodes = area["geocode"]
                                            for geocode in geocodes:
                                                geocode_value = geocode["value"]

                                        # We have a match? Then let's remember what we have
                                        # Try to shorten the area names as this string is rather lengthy
                                        if area_desc not in areas_matching_latlon:


                                            area_desc_abbrev = area_desc.replace(
                                                "Gemeinde/Stadt: ", "", 1
                                            )
                                            area_desc_abbrev = area_desc_abbrev.replace(
                                                "Landkreis/Stadt: ", "", 1
                                            )
                                            area_desc_abbrev = area_desc_abbrev.replace(
                                                "Bundesland: ", "", 1
                                            )
                                            area_desc_abbrev = area_desc_abbrev.replace(
                                                "Freistaat ", "", 1
                                            )
                                            area_desc_abbrev = area_desc_abbrev.replace(
                                                "Freie Hansestadt ", "", 1
                                            )
                                            area_desc_abbrev = area_desc_abbrev.replace(
                                                "Land: ", "", 1
                                            )
                                            area_desc_abbrev = area_desc_abbrev.replace(
                                                "Land ", "", 1
                                            )
                                            areas_matching_latlon.append(area_desc)
                                            areas_matching_latlon_abbrev.append(area_desc_abbrev)

                                        # Save the geocodes, too. This is our primary mean of identification
                                        # area_desc will only be used of the geocode cannot be found
                                        # (MOWAS does seem to use incorrect geocodes from time to time)
                                        if (
                                            geocode_value
                                            not in geocodes_matching_latlon
                                        ):
                                            geocodes_matching_latlon.append(
                                                geocode_value
                                            )

                                        # Remember the set of coordinates which caused that match
                                        coordinates = {
                                            "latitude": latitude,
                                            "longitude": longitude
                                        }
                                        if coordinates not in coords_matching_latlon:
                                            coords_matching_latlon.append(coordinates)

                            # We went through all areas - now let's see of we found something
                            if area_matches_with_user_latlon:
                                # Check if Covid content is present. If yes, then check if
                                # the user wants to receive Covid news
                                add_data = True

                                # Check if the message contains Covid content and flag the
                                # message as "not to be added" if related content has been found
                                if not enable_covid_messaging:
                                    content = [
                                        mowas_headline.lower(),
                                        mowas_description.lower(),
                                        mowas_instruction.lower(),
                                    ]
                                    if any(
                                        "covid" in s
                                        for s in content or "corona" in s
                                        for s in content
                                    ):
                                        add_data = False

                                # Add to the expiring dict unless it is a "Cancel" msg
                                if mowas_msgtype != "Cancel":
                                    # Create the expiring dictionary's payload...
                                    mowas_cache_payload = {
                                        "msgtype": mowas_msgtype,
                                        "sent": mowas_sent,
                                    }
                                    # ... and add the entry to the expiring dict
                                    if add_data:
                                        mowas_cache[
                                            mowas_identifier
                                        ] = mowas_cache_payload

                                # Create the outgoing message's payload ...
                                mowas_messages_to_sent_payload = {
                                    "headline": remove_html_content(message_string=mowas_headline),
                                    "urgency": mowas_urgency,
                                    "severity": mowas_severity,
                                    "description": remove_html_content(message_string=mowas_description),
                                    "instruction": remove_html_content(message_string=mowas_instruction),
                                    "sent": mowas_sent,
                                    "msgtype": mowas_msgtype,
                                    "areas": areas_matching_latlon,
                                    "areas_matching_latlon_abbrev": areas_matching_latlon_abbrev,
                                    "geocodes": geocodes_matching_latlon,
                                    "dapnet_high_prio": dapnet_high_prio_msg,
                                    "latlon_polygon": latlon_array,
                                    "coords_matching_latlon": coords_matching_latlon,
                                }
                                # ... and add it to our dictionary (or update an existing element)
                                # This code assumes that MOWAS uses unique message identifiers across
                                # its various categories
                                if add_data:

                                    # Check if we have already received this message
                                    if mowas_identifier not in mowas_messages_to_send:
                                        # No - then let's add it
                                        mowas_messages_to_send[
                                            mowas_identifier
                                        ] = mowas_messages_to_sent_payload
                                    else:
                                        # Message is already present; we may need to update it
                                        existing_message = mowas_messages_to_send[mowas_identifier]
                                        existing_coords = existing_message["coords_matching_latlon"]

                                        # amend the existing set of coordinates, if necessary
                                        for coord in coords_matching_latlon:
                                            if coord not in existing_coords:
                                                existing_coords.append(coord)

                                        # replace the entry in the dict element
                                        existing_message["coords_matching_latlon"] = existing_coords

                                        # Finally, update the amended entry
                                        mowas_messages_to_send[mowas_identifier] = existing_message

                                # Finally, check if the message is either "Alert" or
                                # "Update". We need this info at a later point in time
                                if mowas_msgtype in ("Alert", "Update"):
                                    got_alert_or_update = True

    # Return the expiring cache and our messages to the user
    return mowas_cache, mowas_messages_to_send, got_alert_or_update


if __name__ == "__main__":
    mowas_message_cache = ExpiringDict(max_len=1000, max_age_seconds=30 * 60)

    mowas_cache_payload = {
        "msgtype": "Update",
        "sent": "2020-08-28T11:00:08+02:00",
    }

    #    mowas_message_cache["DE-BY-A-W083-20200828-000"] = mowas_cache_payload

    # Coordinates = latitude, longitude
    my_coordinates = [
        [
            48.4781,
            10.774,
        ],
        [
            48.4781,
            10.773
        ]
    ]
    logger.info(
        process_mowas_data(
            coordinates=my_coordinates,
            mowas_cache=mowas_message_cache,
            minimal_mowas_severity="Minor",
            mowas_dapnet_high_prio_level="Minor",
        )
    )
