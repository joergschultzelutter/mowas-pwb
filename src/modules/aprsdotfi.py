#
# MOWAS Personal Warning Beacon
# Module: get user's position on APRS.fi
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

import requests
from .utils import get_program_config_from_file
import logging

# Default user agent which is used by the program for sending requests to aprs.fi
default_user_agent = f"mowas-pwb (+https://github.com/joergschultzelutter/mowas-pwb/)"

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)


def get_position_on_aprsfi(aprsfi_callsign: str, aprsdotfi_api_key: str):
    """
    Get the position of the given call sign on aprs.fi
    Call sign is taken 'as is', e.g. with or without SSID.

    If a query for the user's call sign returns more than one position,
    then only the very first call sign position on aprs.fi
    is used by the program.

    Parameters
    ==========
    aprsfi_callsign: 'str'
            Call sign that we want to get the lat/lon coordinates for
    aprsdotfi_api_key: 'str'
            aprs.fi api access key

    Returns
    =======
    success: 'bool'
            True if call was successful
    latitude: 'float'
            latitude position if user was found on aprs.fi
    longitude: 'float'
            longitude position if user was found on aprs.fi
    """

    headers = {"User-Agent": default_user_agent}

    success = False
    latitude = longitude = 0.0

    result = "fail"
    found = 0  # number of entries found in aprs.fi request (if any)

    aprsfi_callsign = aprsfi_callsign.upper()

    try:
        resp = requests.get(
            url=f"https://api.aprs.fi/api/get?name={aprsfi_callsign}&what=loc&apikey={aprsdotfi_api_key}&format=json",
            headers=headers,
        )
    except:
        resp = None
    if resp:
        if resp.status_code == 200:
            try:
                json_content = resp.json()
            except:
                json_content = {}
            # extract web service result. Can either be 'ok' or 'fail'
            if "result" in json_content:
                result = json_content["result"]
            if result == "ok":
                # extract number of result sets in the response. Must be > 0
                # regardless of the available number of results, we will only
                # use the first result
                if "found" in json_content:
                    found = json_content["found"]
                if found > 0:
                    # We extract only the very first entry and disregard
                    # entries 2..n whereas ever present
                    # now extract lat/lon/altitude/lasttime

                    # Check if lat/lon are present; this is the essential information that we need to continue
                    if (
                        "lat" not in json_content["entries"][0]
                        and "lng" in json_content["entries"][0]
                    ):
                        success = False
                    else:
                        success = True
                        try:
                            latitude = float(json_content["entries"][0]["lat"])
                            longitude = float(json_content["entries"][0]["lng"])
                        except ValueError:
                            latitude = longitude = 0
                            success = False
        return (success, latitude, longitude)


if __name__ == "__main__":
    (
        success,
        mowas_aprsdotfi_api_key,
        mowas_dapnet_login_callsign,
        mowas_dapnet_login_passcode,
        mowas_watch_areas,
        mowas_telegram_bot_token,
        mowas_smtpimap_email_address,
        mowas_smtpimap_email_password,
        mowas_smtp_server_address,
        mowas_smtp_server_port,
        mowas_active_categories,
        mowas_imap_server_address,
        mowas_imap_server_port,
        mowas_imap_mailbox_name,
        mowas_imap_mail_retention_max_days,
        mowas_deepldotcom_api_key,
    ) = get_program_config_from_file()
    if success:
        logger.info(get_position_on_aprsfi("vriendschap", mowas_aprsdotfi_api_key))
