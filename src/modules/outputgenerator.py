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
from staticmap import render_png_map
from latlonlookup import get_reverse_geopy_data
import random
import time

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

        newline = "\n"

        # Generate the message as HTML content
        telegram_message = f"<b>mowas-pwb notification</b>: "
        telegram_message = telegram_message + f"<b>{headline}</b>" + newline + newline
        telegram_message = (
            telegram_message + f"<b>Message Type:<\b> {msgtype}" + newline
        )
        telegram_message = telegram_message + f"<b>Urgency:<\b> {urgency}" + newline
        telegram_message = telegram_message + f"<b>Severity:<\b> {severity}" + newline
        telegram_message = (
            telegram_message + f"<b>Timestamp:<\b> {sent}" + newline + newline
        )
        telegram_message = (
            telegram_message + f"<b>Description:<\b> {description}" + newline + newline
        )
        telegram_message = telegram_message + f"<b>Instructions:<\b> {instruction}"

        # Ultimately, send this particular message to Telegram and then loop to the next one
        send_telegram_message(
            bot_token=mowas_telegram_bot_token,
            user_id=telegram_target_id,
            message=telegram_message,
            is_html_content=True,
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
    aprs_latitude: float = None,
    aprs_longitude: float = None,
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

MOWAS Personal Warning Beacon - Report. Affected coordinates:
    
REPLACE_PLAINTEXT_ADDRESSES

Message Headline:       REPLACE_HEADLINE
Message Type:           REPLACE_MESSAGE_TYPE
Urgency:                REPLACE_URGENCY
Severity:               REPLACE_SEVERITY
Message Timestamp:      REPLACE_TIMESTAMP
Description:            REPLACE_DESCRIPTION
Instructions:           REPLACE_INSTRUCTIONS

This position report was processed by mowas-pwb. Generated at REPLACE_DATETIME_CREATED
More info on mowas-pwb can be found here: https://www.github.com/joergschultzelutter/mowas-pwb
---

Proudly made in the district of Holzminden, Lower Saxony, Germany. 73 de DF1JSL
    """

    # Email template without image (HTML)
    html_template_without_image = """\
<h2>Automated email - please do not respond</h2>
<p>MOWAS Personal Warning Beacon - Report. Affected coordinates:</p>
<h3>Affected coordinates</h3>
<table border="1">
<thead>
<tr style="background-color: #bbbbbb;">
<td><strong>Latitude</strong></td>
<td><strong>Longitude</strong></td>
<td><strong>Address</strong></td>
<td><strong>User's APRS pos</strong></td>
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
&nbsp;
<p>This report was processed by <a href="https://www.github.com/joergschultzelutter/mowas-pwb" target="_blank" rel="noopener">mowas-pwb</a>. Generated at <strong>REPLACE_DATETIME_CREATED</strong></p>
<hr />
<p>Proudly made in the district of Holzminden, Lower Saxony, Germany. 73 de DF1JSL</p>
    """

    # Email template with image (HTML)
    html_template_with_image = """\
<h2>Automated email - please do not respond</h2>
<p>MOWAS Personal Warning Beacon - Report</p>
<h3>Affected coordinates</h3>
<table border="1">
<thead>
<tr style="background-color: #bbbbbb;">
<td><strong>Latitude</strong></td>
<td><strong>Longitude</strong></td>
<td><strong>Address</strong></td>
<td><strong>User's APRS pos</strong></td>
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
<hr />
<p><img src="cid:{image_cid}" /></p>
<hr />
<p>This report was processed by <a href="https://www.github.com/joergschultzelutter/mowas-pwb" target="_blank" rel="noopener">mowas-pwb</a>. Generated at <strong>REPLACE_DATETIME_CREATED</strong>. Proudly made in the district of Holzminden, Lower Saxony, Germany. 73 de DF1JSL</p>    
    """

    html_address_element_template = """\
<tr>
<td>REPLACE_LATITUDE</td>
<td>REPLACE_LONGITUDE</td>
<td>REPLACE_ADDRESS</td>
<td><center>REPLACE_APRS</center></td>
</tr>
    """

    plaintext_address_element_template = (
        "Lat/Lon: REPLACE_LATITUDE/REPLACE_LONGITUDE. Address: REPLACE_ADDRESS"
    )

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
        sent = mowas_messages_to_send[mowas_message_id]["sent"]
        msgtype = mowas_messages_to_send[mowas_message_id]["msgtype"]
        areas = mowas_messages_to_send[mowas_message_id]["areas"]
        geocodes = mowas_messages_to_send[mowas_message_id]["geocodes"]
        dapnet_high_prio = mowas_messages_to_send[mowas_message_id]["dapnet_high_prio"]
        latlon_polygon = mowas_messages_to_send[mowas_message_id]["latlon_polygon"]
        # fmt: off
        coords_matching_latlon = mowas_messages_to_send[mowas_message_id]["coords_matching_latlon"]
        # fmt: on

        # Render our static map image (output value will be 'None' in case it cannot be rendered)
        html_image = render_png_map(
            polygon_area=latlon_polygon,
            monitoring_positions=coords_matching_latlon,
            aprs_latitude=aprs_latitude,
            aprs_longitude=aprs_longitude,
        )

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
            success, responsedata = get_reverse_geopy_data(
                latitude=latitude, longitude=longitude
            )
            if success:
                address = responsedata["address"]
                aprs = (
                    "X"
                    if aprs_latitude == latitude and aprs_longitude == longitude
                    else ""
                )

                # Prepare the HTML part
                msg = html_address_element_template
                msg = msg.replace("REPLACE_LATITUDE", str(latitude))
                msg = msg.replace("REPLACE_LONGITUDE", str(longitude))
                msg = msg.replace("REPLACE_ADDRESS", address)
                msg = msg.replace("REPLACE_APRS", aprs)
                html_address_coords.append(msg)

                # Prepare the plain text message part
                msg = plaintext_address_element_template
                msg = msg.replace("REPLACE_LATITUDE", str(latitude))
                msg = msg.replace("REPLACE_LONGITUDE", str(longitude))
                msg = msg.replace("REPLACE_ADDRESS", address)
                if aprs == "X":
                    msg = msg + " (User's APRS Position)"
                plaintext_address_coords.append(msg)

                # Check if we have more than one element in our target list
                # if yes, honor the OSM usage policy
                if len(coords_matching_latlon) > 1:
                    # https://operations.osmfoundation.org/policies/nominatim/ requires us
                    # to obey to its usage policy. We need to make sure that between each
                    # request to OSM that there will be a random sleep period between 1200
                    # and 2000 msec
                    sleep_time = random.uniform(1.2, 2)
                    time.sleep(sleep_time)

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

        html_message = html_message.replace("REPLACE_HEADLINE", headline)
        plaintext_message = plaintext_message.replace("REPLACE_HEADLINE", headline)

        html_message = html_message.replace("REPLACE_MESSAGE_TYPE", msgtype)
        plaintext_message = plaintext_message.replace("REPLACE_MESSAGE_TYPE", msgtype)

        html_message = html_message.replace("REPLACE_URGENCY", urgency)
        plaintext_message = plaintext_message.replace("REPLACE_URGENCY", urgency)

        html_message = html_message.replace("REPLACE_SEVERITY", severity)
        plaintext_message = plaintext_message.replace("REPLACE_SEVERITY", severity)

        html_message = html_message.replace("REPLACE_TIMESTAMP", sent)
        plaintext_message = plaintext_message.replace("REPLACE_TIMESTAMP", sent)

        html_message = html_message.replace("REPLACE_DESCRIPTION", description)
        plaintext_message = plaintext_message.replace(
            "REPLACE_DESCRIPTION", description
        )

        html_message = html_message.replace("REPLACE_INSTRUCTIONS", instruction)
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

    # fmt: off
    mowas_messages_to_send = {
        "DE-BY-A-W083-20200828-000": {
            "headline": "Vorübergehende Änderung der Trinkwasserqualität: Chlorung besteht weiterhin",
            "urgency": "Immediate",
            "severity": "Minor",
            "description": "Die Chlorung besteht weiterhin.",
            "instruction": "Informieren Sie sich in den Medien, zum Beispiel im Lokalradio. Das Wasser muss nicht mehr abgekocht werden.",
            "sent": "2020-08-28T11:00:08+02:00",
            "msgtype": "Alert",
            "areas": ["Stadt Gersthofen, Gemeinde Gablingen"],
            "geocodes": ["097720000000"],
            "dapnet_high_prio": True,
            "latlon_polygon": [(48.4794, 10.771), (48.4781, 10.773), (48.4786, 10.7749), (48.4786, 10.7764), (48.4781, 10.7779), (48.4777, 10.7795), (48.4778, 10.7813), (48.4776, 10.7832), (48.4771, 10.7832), (48.4762, 10.7837), (48.4756, 10.7843), (48.4753, 10.7848), (48.4745, 10.7858), (48.4738, 10.7862), (48.4727, 10.7859), (48.4722, 10.7866), (48.4727, 10.7882), (48.4728, 10.7903), (48.4725, 10.7916), (48.4723, 10.7943), (48.4721, 10.7955), (48.4724, 10.798), (48.473, 10.7992), (48.4732, 10.8008), (48.4734, 10.8052), (48.4735, 10.8062), (48.4729, 10.8089), (48.4724, 10.8115), (48.4723, 10.8154), (48.4738, 10.8147), (48.4738, 10.8155), (48.4738, 10.8184), (48.4757, 10.8184), (48.4759, 10.8219), (48.4752, 10.8223), (48.4744, 10.8225), (48.4735, 10.8222), (48.4727, 10.8216), (48.4719, 10.8212), (48.4707, 10.8214), (48.47, 10.8219), (48.4706, 10.8239), (48.4709, 10.8256), (48.47, 10.8264), (48.4704, 10.8278), (48.4694, 10.8294), (48.4698, 10.8317), (48.4698, 10.8347), (48.4698, 10.8376), (48.4694, 10.8443), (48.4699, 10.8446), (48.4699, 10.8481), (48.4684, 10.8484), (48.4685, 10.8495), (48.4685, 10.8506), (48.4672, 10.851), (48.4674, 10.8563), (48.468, 10.8578), (48.4674, 10.8579), (48.4674, 10.8592), (48.4625, 10.8597), (48.4623, 10.8608), (48.4612, 10.861), (48.4601, 10.861), (48.4591, 10.8609), (48.4591, 10.8668), (48.4587, 10.8668), (48.4575, 10.8666), (48.4574, 10.8685), (48.4565, 10.8688), (48.4556, 10.8688), (48.455, 10.8683), (48.454, 10.8674), (48.4525, 10.8669), (48.4494, 10.8665), (48.4478, 10.8655), (48.4467, 10.8652), (48.4466, 10.8614), (48.4437, 10.8619), (48.4423, 10.8621), (48.4453, 10.8579), (48.4457, 10.8573), (48.446, 10.8564), (48.4449, 10.8566), (48.4428, 10.8571), (48.4428, 10.855), (48.4419, 10.8553), (48.4419, 10.8527), (48.438, 10.8539), (48.4379, 10.8462), (48.437, 10.8467), (48.4369, 10.8437), (48.4371, 10.843), (48.437, 10.8408), (48.4363, 10.8381), (48.4359, 10.8386), (48.4357, 10.8395), (48.4349, 10.8404), (48.435, 10.8378), (48.4352, 10.8356), (48.4348, 10.8339), (48.4343, 10.8318), (48.4343, 10.8304), (48.437, 10.8301), (48.437, 10.8286), (48.4383, 10.8291), (48.4387, 10.8269), (48.4394, 10.8266), (48.4423, 10.828), (48.4437, 10.829), (48.4439, 10.8266), (48.444, 10.8249), (48.4426, 10.8235), (48.4426, 10.8219), (48.4419, 10.8217), (48.4413, 10.8218), (48.4406, 10.822), (48.4404, 10.8196), (48.4388, 10.8189), (48.4379, 10.8184), (48.4371, 10.8167), (48.4376, 10.8142), (48.4369, 10.8145), (48.4372, 10.813), (48.4363, 10.8095), (48.4358, 10.8084), (48.4355, 10.8063), (48.4351, 10.8043), (48.4349, 10.8029), (48.4341, 10.8027), (48.4345, 10.8012), (48.4327, 10.8), (48.432, 10.8004), (48.4331, 10.7984), (48.4326, 10.7969), (48.4335, 10.7951), (48.4346, 10.7957), (48.4343, 10.7972), (48.4357, 10.7961), (48.4363, 10.7964), (48.437, 10.7978), (48.4386, 10.7983), (48.4392, 10.7979), (48.4395, 10.7957), (48.4398, 10.7911), (48.4397, 10.7897), (48.4396, 10.788), (48.4401, 10.788), (48.4403, 10.7859), (48.441, 10.7854), (48.4417, 10.7872), (48.4423, 10.7869), (48.4433, 10.7894), (48.4426, 10.7898), (48.4436, 10.7901), (48.4448, 10.7912), (48.4458, 10.7921), (48.448, 10.7836), (48.448, 10.7799), (48.4486, 10.7767), (48.4483, 10.7746), (48.4482, 10.7734), (48.4492, 10.7732), (48.4495, 10.7737), (48.4497, 10.772), (48.45, 10.7696), (48.4506, 10.7682), (48.4505, 10.7646), (48.4512, 10.7644), (48.4525, 10.7654), (48.4533, 10.7665), (48.4537, 10.7675), (48.4542, 10.7673), (48.4549, 10.7674), (48.4566, 10.7672), (48.458, 10.7675), (48.4592, 10.7669), (48.4602, 10.766), (48.4608, 10.7654), (48.4615, 10.7658), (48.4617, 10.767), (48.4627, 10.766), (48.464, 10.7645), (48.4648, 10.7634), (48.4658, 10.7627), (48.4668, 10.7621), (48.4685, 10.7596), (48.4698, 10.7569), (48.471, 10.754), (48.4721, 10.7527), (48.4729, 10.7512), (48.4743, 10.7522), (48.4749, 10.7537), (48.4773, 10.756), (48.4767, 10.7568), (48.4771, 10.7579), (48.477, 10.7588), (48.4757, 10.7601), (48.4756, 10.7614), (48.4758, 10.7621), (48.4767, 10.7633), (48.477, 10.7648), (48.4774, 10.7664), (48.4776, 10.7678), (48.4783, 10.7684), (48.4786, 10.7694), (48.4794, 10.7702), (48.4794, 10.771)],
            "coords_matching_latlon": [{'latitude': 48.4781, 'longitude': 10.774}, {'latitude': 48.4781, 'longitude': 10.773}]
        }
    }
    # fmt: on
    generate_email_messages(
        mowas_messages_to_send=mowas_messages_to_send,
        warncell_data=warncell_data,
        smtpimap_email_address=mowas_smtpimap_email_address,
        smtpimap_email_password=mowas_smtpimap_email_password,
        mail_recipient="joerg.schultze.lutter@gmail.com",
        smtp_server_address=mowas_smtp_server_address,
        smtp_server_port=mowas_smtp_server_port,
        aprs_latitude=48.4781,
        aprs_longitude=10.774,
    )
