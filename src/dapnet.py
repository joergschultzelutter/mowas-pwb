#
# MOWAS Personal Warning Beacon
# Module: DAPNET communication core
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
import logging
import json
from utils import make_pretty_dapnet_messages
import requests
from requests.auth import HTTPBasicAuth
import time

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)


def send_dapnet_message(
    to_callsign: str,
    message: str,
    dapnet_login_callsign: str,
    dapnet_login_passcode: str,
    dapnet_api_transmitter_group: str = "dl-all",
    dapnet_api_server="http://www.hampager.de:8080/calls",
    dapnet_high_priority_message: bool = False,
    simulate_send: bool = False,
):
    """
    Send content to the DAPNET network
    Parameters
    ==========
    to_callsign : 'str'
        Target Call Sign that will receive the message (SSID content will be removed)
    message : 'str'
        Message String that will be sent to the user. May trigger 1..n messages,
        depending on the message length
    dapnet_login_callsign: 'str'
        login user name to the DAPNET API
    dapnet_login_passcode: 'str'
        login password to the DAPNET API
    dapnet_api_transmitter_group: 'str'
        Default is 'dl-all' as the program only targets
        German users. Change this if necessary.
    dapnet_api_server: 'str'
        DAPNET API server
    dapnet_high_priority_message: 'bool'
        send message as high priority True/False
    simulate_send: 'bool'
        Set to true if you want to simulate sending
        content to the DAPNET network

    Returns
    =======
    success : 'bool'
            True if operation was successful
    """

    success = False

    if dapnet_login_callsign.upper() == "N0CALL":
        logger.info(
            msg="mowas-pwb: DAPNET API credentials are not configured, cannot send msg"
        )
        success = False
    else:
        # Get rid of the SSID in the TO callsign (if accidentally present)
        dapnet_to_callsign = to_callsign.split("-")[0].upper()

        destination_list = make_pretty_dapnet_messages(
            message_to_add=message, add_sep=True
        )

        # Send the message(s)
        logger.info(msg=f"Sending multipart message to DAPNET, consisting of {len(destination_list)} separate messages")
        for destination_message in destination_list:

            dapnet_payload = {
                "text": f"{destination_message}",
                "callSignNames": [f"{dapnet_to_callsign}"],
                "transmitterGroupNames": [f"{dapnet_api_transmitter_group}"],
                "emergency": dapnet_high_priority_message,
            }
            dapnet_payload_json = json.dumps(dapnet_payload)
            if not simulate_send:
                logger.debug(msg=f"Sending content to DAPNET server: {destination_message}")
                response = requests.post(
                    url=dapnet_api_server,
                    data=dapnet_payload_json,
                    auth=HTTPBasicAuth(
                        username=dapnet_login_callsign, password=dapnet_login_passcode
                    ),
                )  # Exception handling einbauen
                if response.status_code != 201:
                    success = False
                    logger.info(
                        msg=f"FAILED to send DAPNET message to {dapnet_to_callsign} via '{dapnet_api_transmitter_group}'"
                    )
                    return success
                logger.info(
                    msg=f"Successfully sent message {destination_list.index(destination_message)+1} of {len(destination_list)} to DAPNET"
                )
                # do not spam the DAPNET API; wait a few secs before sending out the next message
                if (
                    destination_list.index(destination_message)
                    < len(destination_list) - 1
                ):
                    logger.debug(msg="Sleep")
                    time.sleep(10.0)
            else:
                logger.info(
                    msg=f"Simulating DAPNET 'Send'; message='{destination_message}'"
                )
        success = True
        logger.info(
            msg="All parts of the message were successfully transmitted to DAPNET"
        )

    return success


if __name__ == "__main__":
    pass
