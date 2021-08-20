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
from modules.utils import get_program_config_from_file, make_pretty_dapnet_messages
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
    message_status: str,
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
    dapnet_login_password: 'str'
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

    # Check if we have received a valid MOWAS status
    message_status = message_status.upper()
    assert message_status in ("ALERT", "UPDATE", "CANCEL")

    message_short_status = f"{message_status[0]}:"

    if dapnet_login_callsign.upper() == "N0CALL":
        logger.info(
            msg="mowas-pwb: DAPNET API credentials are not configured, cannot send msg"
        )
        success = False
    else:
        # Get rid of the SSID in the TO callsign (if accidentally present)
        dapnet_to_callsign = to_callsign.split("-")[0].upper()

        # Start with the message identifier: A/U/C: --> Alert/Update/Cancel
        destination_list = make_pretty_dapnet_messages(
            message_to_add=message_short_status, add_sep=False
        )
        destination_list = make_pretty_dapnet_messages(
            message_to_add=message, destination_list=destination_list, add_sep=False
        )

        # Send the message(s)
        for destination_message in destination_list:

            dapnet_payload = {
                "text": f"{dapnet_from_callsign.upper()}: {message_txt}",
                "callSignNames": [f"{dapnet_to_callsign}"],
                "transmitterGroupNames": [f"{dapnet_api_transmitter_group}"],
                "emergency": dapnet_high_priority_message,
            }
            dapnet_payload_json = json.dumps(dapnet_payload)
            if not simulate_send:
                logger.debug(msg="Sending content to DAPNET server")
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
                    msg=f"Successfully sent message {destination_list.index(destination_message)} of {len(destination_list)-1} to DAPNET"
                )
                if destination_list.index(destination_message) < len(destination_list) - 1:
                    time.sleep(10.0)
            else:
                logger.debug(msg=f"Simulating DAPNET 'Send'; message='{destination_message}'")
        success = True
        logger.info(
            msg="All parts of the message were successfully transmitted to DAPNET"
        )

    return success


if __name__ == "__main__":
    (
        success,
        mowas_aprsdotfi_api_key,
        mowas_dapnet_login_callsign,
        mowas_dapnet_login_passcode,
        mowas_watch_areas,
    ) = get_program_config_from_file("mowas-pwb.cfg")
    if success:
        logger.info(
            send_dapnet_message(
                to_callsign="DF1JSL-8",
                message="Die Besten der Besten der Besten, Sir",
                message_status="Alert",
                dapnet_login_callsign=mowas_dapnet_login_callsign,
                dapnet_login_passcode=mowas_dapnet_login_passcode,
                dapnet_high_priority_message=False,
            )
        )
