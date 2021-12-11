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
import logging
from utils import (
    convert_text_to_plain_ascii,
    remove_html_content,
    get_program_config_from_file,
)
from warncell import read_warncell_info
from telegramdotcom import send_telegram_message
from dapnet import send_dapnet_message
from mail import send_email_message
from datetime import datetime
from geodata import (
    get_reverse_geopy_data,
    convert_latlon_to_utm,
    convert_latlon_to_maidenhead,
)
import random
import time
from mowas import process_mowas_data
from expiringdict import ExpiringDict


# Set up the global logger variable
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)


def generate_dapnet_messages(
    mowas_messages_to_send: dict,
    warncell_data: dict,
    mowas_dapnet_destination_callsign: str,
    mowas_dapnet_login_callsign: str,
    mowas_dapnet_login_passcode: str,
):
    """
    Generates DAPNET messages and triggers transmission to the user

    Parameters
    ==========
    mowas_messages_to_send : 'dict'
        dictionary, containing all messages that are to be sent to the end user
    warncell_data: 'dict'
        warncell data; these are references to German municipal areas, cities etc
    mowas_dapnet_destination_callsign: str
        This is the RECIPIENT's ham radio call sign. SSID can be omitted but will
        be ignored as part of the 'send' process
    mowas_dapnet_login_callsign: str
        This is the SENDER's DAPNET User ID
    mowas_dapnet_login_passcode: str
        This is the SENDER's DAPNET User passcode
    Returns
    =======
    """

    logger.debug(msg="Starting DAPNET message processing")

    # Iterate through our list of messages
    # Get all of the information that is associated with our message
    for mowas_message_id in mowas_messages_to_send:
        headline = mowas_messages_to_send[mowas_message_id]["headline"]
        urgency = mowas_messages_to_send[mowas_message_id]["urgency"]
        severity = mowas_messages_to_send[mowas_message_id]["severity"]
        description = mowas_messages_to_send[mowas_message_id]["description"]
        instruction = mowas_messages_to_send[mowas_message_id]["instruction"]
        sent = mowas_messages_to_send[mowas_message_id]["sent"]
        msgtype = mowas_messages_to_send[mowas_message_id]["msgtype"]
        areas = mowas_messages_to_send[mowas_message_id]["areas"]
        geocodes = mowas_messages_to_send[mowas_message_id]["geocodes"]
        dapnet_high_prio = mowas_messages_to_send[mowas_message_id]["dapnet_high_prio"]

        # Construct the outgoing message
        #
        # Everything needs to be converted to plain ASCII 7-bit
        # Message always starts with an indicator whether this is an Alert, Update or Cancel
        # A: => Alert, U: => Update, C: => Cancel
        msg = f"{msgtype[0:1]}:"

        # Remove potential HTML content from msg headline, convert it to ASCII and add it to the message
        msg = msg + convert_text_to_plain_ascii(remove_html_content(headline)) + " "

        # Remove potential HTML content from msg instructions, convert it to ASCII and add it to the message
        msg = msg + convert_text_to_plain_ascii(remove_html_content(instruction)) + " "

        # retrieve the affected geocode(s), get the area data and add the short name for that area to the message
        for geocode in geocodes:
            # Do we know the geocode? Then let's use it
            if geocode in warncell_data:
                short_name = warncell_data[geocode]["short_name"]
                # does not contain HTML content so we only need to convert it to ASCII-7
                msg = msg + convert_text_to_plain_ascii(short_name) + " "
            else:
                # We did not find the geocode; use the rather lengthy original MOWAS description instead
                # Description and Warncell area share the same order which means that by referencing to the
                # geocode's index, we know the position of the full-blown text
                idx = geocodes.index(geocode)
                if len(areas) <= idx + 1:
                    msg = (
                        msg
                        + convert_text_to_plain_ascii(remove_html_content(areas[idx]))
                        + " "
                    )

        # Remove any trailing blanks
        msg = msg.rstrip()

        # Finally, send this particular message to DAPNET and then loop to the next message
        logger.debug(msg="Sending message to DAPNET")
        send_dapnet_message(
            message=msg,
            to_callsign=mowas_dapnet_destination_callsign,
            dapnet_login_callsign=mowas_dapnet_login_callsign,
            dapnet_login_passcode=mowas_dapnet_login_passcode,
            dapnet_high_priority_message=dapnet_high_prio,
        )

    logger.debug(msg="Finished DAPNET message processing")


def generate_telegram_messages(
    mowas_messages_to_send: dict,
    warncell_data: dict,
    mowas_telegram_bot_token: str,
    telegram_target_id: int,
):

    """
    Generates Telegram messages and triggers transmission to the user

    Parameters
    ==========
    mowas_messages_to_send : 'dict'
        dictionary, containing all messages that are to be sent to the end user
    warncell_data: 'dict'
        warncell data; these are references to German municipal areas, cities etc
    mowas_telegram_bot_token: str
        This is the SENDER's bot token ID
    telegram_target_id: str
        This is the RECIPIENT's telegram ID in NUMERIC format. Use the Telegram
        Bot 'UserInfoBot' to get this data for your accout
    Returns
    =======
    """

    logger.debug(msg="Starting Telegram message processing")

    # We want multi-line HTML messages in Telegram. <br> does NOT work
    newline = "\n"

    for mowas_message_id in mowas_messages_to_send:
        headline = mowas_messages_to_send[mowas_message_id]["headline"]
        urgency = mowas_messages_to_send[mowas_message_id]["urgency"]
        severity = mowas_messages_to_send[mowas_message_id]["severity"]
        description = mowas_messages_to_send[mowas_message_id]["description"]
        contact = mowas_messages_to_send[mowas_message_id]["contact"]
        instruction = mowas_messages_to_send[mowas_message_id]["instruction"]
        sent = mowas_messages_to_send[mowas_message_id]["sent"]
        msgtype = mowas_messages_to_send[mowas_message_id]["msgtype"]
        areas = mowas_messages_to_send[mowas_message_id]["areas"]
        geocodes = mowas_messages_to_send[mowas_message_id]["geocodes"]
        dapnet_high_prio = mowas_messages_to_send[mowas_message_id]["dapnet_high_prio"]
        coords_matching_latlon = mowas_messages_to_send[mowas_message_id][
            "coords_matching_latlon"
        ]

        # get the rendered image (output value will be 'None' in case it cannot be rendered)
        html_image = mowas_messages_to_send[mowas_message_id]["static_image"]

        # did the user request translated content?
        if "lang" in mowas_messages_to_send[mowas_message_id]:
            # yes; get the translated content
            # fmt: off
            lang_headline = mowas_messages_to_send[mowas_message_id]["lang_headline"]
            lang_description = mowas_messages_to_send[mowas_message_id]["lang_description"]
            lang_instruction = mowas_messages_to_send[mowas_message_id]["lang_instruction"]
            lang_contact = mowas_messages_to_send[mowas_message_id]["lang_contact"]
            # fmt: on

            # and amend out target fields
            headline = f"{lang_headline} (<i>{headline}</i>)"
            description = f"{lang_description} (<i>{description}</i>)"
            instruction = f"{lang_instruction} (<i>{instruction}</i>)"
            contact = f"{lang_contact} (<i>{contact}</i>)"

        # Create the message timestamp
        utc_create_time = datetime.utcnow()
        msg_string = f"{utc_create_time.strftime('%d-%b-%Y %H:%M:%S')} UTC"

        # Generate the message as HTML content
        telegram_message = (
            f"<u><i>mowas-pwb Notification</i> (generated at {msg_string})</u>"
            + newline
            + newline
        )

        telegram_message = telegram_message + f"<b>Message headline:</b>{headline}" + newline + newline

        telegram_message = telegram_message + "<u><i>Message details</i></u>" + newline

        telegram_message = (
            telegram_message + f"<b>Description:</b> {description}" + newline
        )
        telegram_message = (
            telegram_message + f"<b>Instructions:</b> {instruction}" + newline
        )
        telegram_message = (
            telegram_message + f"<b>Contact:</b> {contact}" + newline
        )

        telegram_message = (
            telegram_message + f"<b>Message Type:</b> {msgtype}" + newline
        )
        telegram_message = telegram_message + f"<b>Urgency:</b> {urgency}" + newline
        telegram_message = telegram_message + f"<b>Severity:</b> {severity}" + newline
        telegram_message = telegram_message + f"<b>Timestamp:</b> {sent}" + newline + newline

        telegram_message = telegram_message + "<u><i>Address details</i></u>" + newline

        for coords in coords_matching_latlon:
            latitude = coords["latitude"]
            longitude = coords["longitude"]
            address = coords["address"]
            utm = coords["utm"]
            maidenhead = coords["maidenhead"]
            aprs = coords["aprs_coordinates"]

            telegram_message = (
                telegram_message
                + f"<b>Lat / Lon:</b> <pre>{latitude}</pre> / <pre>{longitude}</pre>"
            )
            if aprs:
                telegram_message = (
                    telegram_message
                    + f" (<i>This is the user's latest APRS position</i>)"
                )
            telegram_message = telegram_message + newline
            telegram_message = (
                telegram_message + f"<b>UTM:</b> <pre>{utm}</pre>" + newline
            )
            telegram_message = (
                telegram_message + f"<b>Grid:</b> <pre>{maidenhead}</pre>" + newline
            )
            telegram_message = (
                telegram_message + f"<b>Address:</b> {address}" + newline+newline
            )

        # Ultimately, send this particular message to Telegram and then loop to the next one
        send_telegram_message(
            bot_token=mowas_telegram_bot_token,
            user_id=telegram_target_id,
            message=telegram_message,
            is_html_content=True,
            static_image=html_image,
        )

    logger.debug(msg="Finished Telegram message processing")


def generate_email_messages(
    mowas_messages_to_send: dict,
    warncell_data: dict,
    smtpimap_email_address: str,
    smtpimap_email_password: str,
    smtp_server_address: str,
    smtp_server_port: int,
    mail_recipient: str,
):
    """
    Generates Email messages and triggers transmission to the user

    Parameters
    ==========
    mowas_messages_to_send : 'dict'
        dictionary, containing all messages that are to be sent to the end user
    warncell_data: 'dict'
        warncell data; these are references to German municipal areas, cities etc
    smtpimap_email_address: str
        This is the SENDER's SMTP Email Address
    smtpimap_email_password: str
        This is the SENDER's SMTP Email Password
    mail_recipient: str
        This is the RECIPIENT's email address
    Returns
    =======
    """

    # Email template (plain text)
    plaintext_template = """\
AUTOMATED EMAIL - PLEASE DO NOT RESPOND

MOWAS Personal Warning Beacon - Report. Matching coordinates:
    
REPLACE_PLAINTEXT_ADDRESSES

Message Headline:       REPLACE_HEADLINE
Message Type:           REPLACE_MESSAGE_TYPE
Urgency:                REPLACE_URGENCY
Severity:               REPLACE_SEVERITY
Message Timestamp:      REPLACE_TIMESTAMP
Description:            REPLACE_DESCRIPTION
Instructions:           REPLACE_INSTRUCTIONS
Contact:                REPLACE_CONTACT

This position report was processed by mowas-pwb. Generated at REPLACE_DATETIME_CREATED
More info on mowas-pwb can be found here: https://www.github.com/joergschultzelutter/mowas-pwb
---

Proudly made in the district of Holzminden, Lower Saxony, Germany. 73 de DF1JSL
    """

    # Email template without image (HTML)
    html_template_without_image = """\
<h2>Automated email - please do not respond</h2>
<p>MOWAS Personal Warning Beacon - Report. Matching coordinates:</p>
<h3>Affected coordinates</h3>
<table border="1">
<thead>
<tr style="background-color: #bbbbbb;">
<td><strong>Latitude</strong></td>
<td><strong>Longitude</strong></td>
<td><strong>UTM</strong></td>
<td><strong>Maidenhead</strong></td>
<td><strong>Address</strong></td>
<td><strong>APRS</strong></td>
</tr>
</thead>
<tbody>
REPLACE_HTML_ADDRESSES
</tbody>
</table>
<h3>Message Details</h3>
<li><strong>&nbsp;Headline</strong>&nbsp;:&nbsp;REPLACE_HEADLINE</li>
<li><strong>&nbsp;Message Type</strong>&nbsp;:&nbsp;REPLACE_MESSAGE_TYPE</li>
<li><strong>&nbsp;Urgency</strong>&nbsp;:&nbsp;REPLACE_URGENCY</li>
<li><strong>&nbsp;Severity</strong>&nbsp;:&nbsp;REPLACE_SEVERITY</li>
<li><strong>&nbsp;Message Timestamp</strong>&nbsp;:&nbsp;REPLACE_TIMESTAMP</li>
<li><strong>&nbsp;Description</strong>&nbsp;:&nbsp;REPLACE_DESCRIPTION</li>
<li><strong>&nbsp;Instructions</strong>&nbsp;:&nbsp;REPLACE_INSTRUCTIONS</li>
<li><strong>&nbsp;Contact</strong>&nbsp;:&nbsp;REPLACE_CONTACT</li>
&nbsp;
<p>This report was processed by <a href="https://www.github.com/joergschultzelutter/mowas-pwb" target="_blank" rel="noopener">mowas-pwb</a>. Generated at <strong>REPLACE_DATETIME_CREATED</strong></p>
<hr />
<p>Proudly made in the district of Holzminden, Lower Saxony, Germany. 73 de DF1JSL</p>
    """

    # Email template with image (HTML)
    html_template_with_image = """\
<h2>Automated email - please do not respond</h2>
<p>MOWAS Personal Warning Beacon - Report</p>
<h3>Matching coordinates</h3>
<table border="1">
<thead>
<tr style="background-color: #bbbbbb;">
<td><strong>Latitude</strong></td>
<td><strong>Longitude</strong></td>
<td><strong>UTM</strong></td>
<td><strong>Grid</strong></td>
<td><strong>Address</strong></td>
<td><strong>APRS</strong></td>
</tr>
</thead>
<tbody>
REPLACE_HTML_ADDRESSES
</tbody>
</table>
<h3>Message Details</h3>
<li><strong>&nbsp;Headline</strong>&nbsp;:&nbsp;REPLACE_HEADLINE</li>
<li><strong>&nbsp;Message Type</strong>&nbsp;:&nbsp;REPLACE_MESSAGE_TYPE</li>
<li><strong>&nbsp;Urgency</strong>&nbsp;:&nbsp;REPLACE_URGENCY</li>
<li><strong>&nbsp;Severity</strong>&nbsp;:&nbsp;REPLACE_SEVERITY</li>
<li><strong>&nbsp;Message Timestamp</strong>&nbsp;:&nbsp;REPLACE_TIMESTAMP</li>
<li><strong>&nbsp;Description</strong>&nbsp;:&nbsp;REPLACE_DESCRIPTION</li>
<li><strong>&nbsp;Instructions</strong>&nbsp;:&nbsp;REPLACE_INSTRUCTIONS</li>
<li><strong>&nbsp;Contact</strong>&nbsp;:&nbsp;REPLACE_CONTACT</li>
<hr />
<p><img src="cid:{image_cid}" /></p>
<hr />
<p>This report was processed by <a href="https://www.github.com/joergschultzelutter/mowas-pwb" target="_blank" rel="noopener">mowas-pwb</a>. Generated at <strong>REPLACE_DATETIME_CREATED</strong>. Proudly made in the district of Holzminden, Lower Saxony, Germany. 73 de DF1JSL</p>    
    """

    html_address_element_template = """\
<tr>
<td><center>REPLACE_LATITUDE</center></td>
<td><center>REPLACE_LONGITUDE</center></td>
<td><center>REPLACE_UTM</center></td>
<td><center>REPLACE_MAIDENHEAD</center></td>
<td><center>REPLACE_ADDRESS</center></td>
<td><center>REPLACE_APRS</center></td>
</tr>
    """

    plaintext_address_element_template = "Lat/Lon: REPLACE_LATITUDE/REPLACE_LONGITUDE. UTM: REPLACE_UTM. Grid: REPLACE_MAIDENHEAD. Address: REPLACE_ADDRESS"

    # Email template - mail subject
    mail_subject_template = (
        "MOWAS Personal Warning Beacon -  Report REPLACE_DATETIME_CREATED"
    )

    logger.debug(msg="Starting Email message processing")
    for mowas_message_id in mowas_messages_to_send:
        headline = mowas_messages_to_send[mowas_message_id]["headline"]
        urgency = mowas_messages_to_send[mowas_message_id]["urgency"]
        severity = mowas_messages_to_send[mowas_message_id]["severity"]
        description = mowas_messages_to_send[mowas_message_id]["description"]
        instruction = mowas_messages_to_send[mowas_message_id]["instruction"]
        contact = mowas_messages_to_send[mowas_message_id]["contact"]
        sent = mowas_messages_to_send[mowas_message_id]["sent"]
        msgtype = mowas_messages_to_send[mowas_message_id]["msgtype"]
        areas = mowas_messages_to_send[mowas_message_id]["areas"]
        geocodes = mowas_messages_to_send[mowas_message_id]["geocodes"]
        dapnet_high_prio = mowas_messages_to_send[mowas_message_id]["dapnet_high_prio"]
        latlon_polygon = mowas_messages_to_send[mowas_message_id]["latlon_polygon"]
        # fmt: off
        coords_matching_latlon = mowas_messages_to_send[mowas_message_id]["coords_matching_latlon"]
        # fmt: on
        if "lang" in mowas_messages_to_send[mowas_message_id]:
            lang_headline = mowas_messages_to_send[mowas_message_id]["lang_headline"]
            lang_description = mowas_messages_to_send[mowas_message_id][
                "lang_description"
            ]
            lang_instruction = mowas_messages_to_send[mowas_message_id][
                "lang_instruction"
            ]
            lang_contact = mowas_messages_to_send[mowas_message_id]["lang_contact"]
        else:
            lang_headline = lang_instruction = lang_contact = lang_description = None

        # get the rendered image (output value will be 'None' in case it cannot be rendered)
        html_image = mowas_messages_to_send[mowas_message_id]["static_image"]

        # try to build the HTML section which contains our addresses.
        # There should be at least one - otherwise, we should never have
        # generated this message
        #
        # For each lat/lon coordinate set, the program will go a reverse
        # address lookup on OpenStreetMap and get that position's real
        # address. If ONE of these elements is also identical to the
        # user's current APRS coordinates, the address will get
        # highlighted accordingly.
        #
        # Note: there is no dupe check - ideally, you should never
        # have specified the same set of coordinates.

        # Target list elements for HTML content and plain text
        html_address_coords = []
        plaintext_address_coords = []

        for coords in coords_matching_latlon:
            latitude = coords["latitude"]
            longitude = coords["longitude"]
            address = coords["address"]
            utm = coords["utm"]
            maidenhead = coords["maidenhead"]
            aprs_c = coords["aprs_coordinates"]

            # set a marker if these are coordinates originating from
            # the user's APRS position
            aprs = "X" if aprs_c else ""

            # Prepare the HTML part
            msg = html_address_element_template
            msg = msg.replace("REPLACE_LATITUDE", str(latitude))
            msg = msg.replace("REPLACE_LONGITUDE", str(longitude))
            msg = msg.replace("REPLACE_UTM", utm)
            msg = msg.replace("REPLACE_MAIDENHEAD", maidenhead)
            msg = msg.replace("REPLACE_ADDRESS", address)
            msg = msg.replace("REPLACE_APRS", aprs)
            html_address_coords.append(msg)

            # Prepare the plain text message part
            msg = plaintext_address_element_template
            msg = msg.replace("REPLACE_LATITUDE", str(latitude))
            msg = msg.replace("REPLACE_LONGITUDE", str(longitude))
            msg = msg.replace("REPLACE_UTM", utm)
            msg = msg.replace("REPLACE_MAIDENHEAD", maidenhead)
            msg = msg.replace("REPLACE_ADDRESS", address)
            if aprs == "X":
                msg = msg + " (User's APRS Position)"
            plaintext_address_coords.append(msg)

        # Use the generated list items in order to create the final content for the address info
        html_list_of_addresses = "\n".join([str(elem) for elem in html_address_coords])
        plaintext_list_of_addresses = "\n".join(
            [str(elem) for elem in plaintext_address_coords]
        )

        # Copy the mail template content to different variables
        plaintext_message = plaintext_template
        mail_subject_message = mail_subject_template

        # Use a different HTML message template in case we were unable to render the image
        html_message = (
            html_template_with_image if html_image else html_template_without_image
        )

        # Create the mail subject
        mail_subject_message = f"{msgtype.upper()} - {severity}: {mail_subject_message}"

        # Replace the template content
        html_message = html_message.replace(
            "REPLACE_HTML_ADDRESSES", html_list_of_addresses
        )
        plaintext_message = plaintext_message.replace(
            "REPLACE_PLAINTEXT_ADDRESSES", plaintext_list_of_addresses
        )

        if not lang_headline:
            html_message = html_message.replace("REPLACE_HEADLINE", headline)
        else:
            html_message = html_message.replace(
                "REPLACE_HEADLINE", lang_headline + " (<i>" + headline + "</i>)"
            )
        plaintext_message = plaintext_message.replace("REPLACE_HEADLINE", headline)

        html_message = html_message.replace("REPLACE_MESSAGE_TYPE", msgtype)
        plaintext_message = plaintext_message.replace("REPLACE_MESSAGE_TYPE", msgtype)

        html_message = html_message.replace("REPLACE_URGENCY", urgency)
        plaintext_message = plaintext_message.replace("REPLACE_URGENCY", urgency)

        html_message = html_message.replace("REPLACE_SEVERITY", severity)
        plaintext_message = plaintext_message.replace("REPLACE_SEVERITY", severity)

        html_message = html_message.replace("REPLACE_TIMESTAMP", sent)
        plaintext_message = plaintext_message.replace("REPLACE_TIMESTAMP", sent)

        if not lang_contact:
            html_message = html_message.replace("REPLACE_CONTACT", contact)
        else:
            html_message = html_message.replace(
                "REPLACE_CONTACT", lang_contact + " (<i>" + contact + "</i>)"
            )
        plaintext_message = plaintext_message.replace("REPLACE_CONTACT", contact)

        if not lang_description:
            html_message = html_message.replace("REPLACE_DESCRIPTION", description)
        else:
            html_message = html_message.replace(
                "REPLACE_DESCRIPTION",
                lang_description + " (<i>" + description + "</i>)",
            )
        plaintext_message = plaintext_message.replace(
            "REPLACE_DESCRIPTION", description
        )

        if not lang_instruction:
            html_message = html_message.replace("REPLACE_INSTRUCTIONS", instruction)
        else:
            html_message = html_message.replace(
                "REPLACE_INSTRUCTIONS",
                lang_instruction + " (<i>" + instruction + "</i>)",
            )
        plaintext_message = plaintext_message.replace(
            "REPLACE_INSTRUCTIONS", instruction
        )

        # add the Time Created information
        utc_create_time = datetime.utcnow()
        msg_string = f"{utc_create_time.strftime('%d-%b-%Y %H:%M:%S')} UTC"
        plaintext_message = plaintext_message.replace(
            "REPLACE_DATETIME_CREATED", msg_string
        )
        html_message = html_message.replace("REPLACE_DATETIME_CREATED", msg_string)
        mail_subject_message = mail_subject_message.replace(
            "REPLACE_DATETIME_CREATED", msg_string
        )
        # Ultimately, send this particular message via Email and then loop to the next one
        send_email_message(
            plaintext_message=plaintext_message,
            html_message=html_message,
            subject_message=mail_subject_message,
            smtpimap_email_address=smtpimap_email_address,
            smtpimap_email_password=smtpimap_email_password,
            smtp_server_address=smtp_server_address,
            smtp_server_port=smtp_server_port,
            mail_recipient=mail_recipient,
            html_image=html_image,
        )

    logger.debug(msg="Finished Email message processing")


if __name__ == "__main__":
    success, warncell_data = read_warncell_info()
    if not success:
        logger.info("Cannot read warncell data")
        exit(0)

    # https://warnung.bund.de/bbk.status/status_032410000000.json

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
    if not success:
        exit(0)

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
        [48.4781, 10.773],
    ]

    mowas_cache, mowas_messages_to_send, got_alert_or_update = process_mowas_data(
        coordinates=my_coordinates,
        mowas_cache=mowas_message_cache,
        minimal_mowas_severity="Minor",
        mowas_dapnet_high_prio_level="Minor",
    #    target_language="en-us",
        deepl_api_key=mowas_deepldotcom_api_key,
        aprs_latitude=48.4781,
        aprs_longitude=10.774,
    )

    testmethod = "telegram"

    if testmethod == "email":
        # fmt: on
        generate_email_messages(
            mowas_messages_to_send=mowas_messages_to_send,
            warncell_data=warncell_data,
            smtpimap_email_address=mowas_smtpimap_email_address,
            smtpimap_email_password=mowas_smtpimap_email_password,
            mail_recipient="joerg.schultze.lutter@gmail.com",
            smtp_server_address=mowas_smtp_server_address,
            smtp_server_port=mowas_smtp_server_port,
        )

    if testmethod == "telegram":
        generate_telegram_messages(
            mowas_messages_to_send=mowas_messages_to_send,
            warncell_data=warncell_data,
            mowas_telegram_bot_token=mowas_telegram_bot_token,
            telegram_target_id=140582719,
        )

    if testmethod == "dapnet":
        generate_dapnet_messages(
            mowas_messages_to_send=mowas_messages_to_send,
            warncell_data=warncell_data,
            mowas_dapnet_destination_callsign="DF1JSL",
            mowas_dapnet_login_callsign=mowas_dapnet_login_callsign,
            mowas_dapnet_login_passcode=mowas_dapnet_login_passcode,
        )
