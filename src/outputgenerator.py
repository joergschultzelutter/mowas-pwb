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
    get_program_config_from_file,
    does_file_exist,
    make_pretty_sms_messages,
)
from warncell import read_warncell_info
from mail import send_email_message
from datetime import datetime

from expiringdict import ExpiringDict
from test_data_generator import generate_test_data
import apprise

# Set up the global logger variable
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)


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
    success: 'bool'
        True if operation was successful
    """

    # Set a default status
    success = False

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
<th>Latitude</td>
<th>Longitude</td>
<th>UTM</strong></td>
<th>Grid</td>
<th>Address</td>
<th>APRS</td>
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
<th>Latitude</td>
<th>Longitude</td>
<th>UTM</strong></td>
<th>Grid</td>
<th>Address</td>
<th>APRS</td>
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
<p><center><img src="cid:{image_cid}" /></center></p>
<hr />
<p>This report was processed by <a href="https://www.github.com/joergschultzelutter/mowas-pwb" target="_blank" rel="noopener">mowas-pwb</a>. Generated at <strong>REPLACE_DATETIME_CREATED</strong>. Proudly made in the district of Holzminden, Lower Saxony, Germany. 73 de DF1JSL</p>    
    """

    html_address_element_template = """\
<tr>
<td><center>REPLACE_LATITUDE</center></td>
<td><center>REPLACE_LONGITUDE</center></td>
<td><center>REPLACE_UTM</center></td>
<td><center>REPLACE_MAIDENHEAD</center></td>
<td>REPLACE_ADDRESS</td>
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
        instruction = "" if not instruction else instruction
        contact = mowas_messages_to_send[mowas_message_id]["contact"]
        contact = "" if not contact else contact
        sent = mowas_messages_to_send[mowas_message_id]["sent"]
        msgtype = mowas_messages_to_send[mowas_message_id]["msgtype"]
        areas = mowas_messages_to_send[mowas_message_id]["areas"]
        geocodes = mowas_messages_to_send[mowas_message_id]["geocodes"]
        high_prio = mowas_messages_to_send[mowas_message_id]["high_prio"]
        latlon_polygon = mowas_messages_to_send[mowas_message_id]["latlon_polygon"]
        # fmt: off
        coords_matching_latlon = mowas_messages_to_send[mowas_message_id]["coords_matching_latlon"]
        if "lang" in mowas_messages_to_send[mowas_message_id]:
            lang_headline = mowas_messages_to_send[mowas_message_id]["lang_headline"]
            lang_description = mowas_messages_to_send[mowas_message_id]["lang_description"]
            lang_instruction = mowas_messages_to_send[mowas_message_id]["lang_instruction"]
            lang_instruction = "" if not lang_instruction else lang_instruction
            lang_contact = mowas_messages_to_send[mowas_message_id]["lang_contact"]
        else:
            lang_headline = lang_instruction = lang_contact = lang_description = None
        # fmt: on

        # get the rendered image (output value will be 'None' in case it cannot be rendered)
        file_name = mowas_messages_to_send[mowas_message_id]["static_image"]
        html_image = None

        try:
            with open(file_name, "rb") as file:
                html_image = file.read()
        except FileNotFoundError:
            logger.debug(msg=f"File '{file_name}' not found")
            html_image = None
        except Exception as e:
            logger.debug(msg=f"Exception occurred: '{e}'")
            html_image = None

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
            aprs = (
                '<span style="background-color:#00FF00">&nbsp;&nbsp;&nbsp;&nbsp;y&nbsp;&nbsp;&nbsp;&nbsp;</span>'
                if aprs_c
                else '<span style="background-color:#FF0000">&nbsp;&nbsp;&nbsp;&nbsp;n&nbsp;&nbsp;&nbsp;&nbsp;</span>'
            )

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
        logger.info(
            msg=f"Sending Email Message to {smtp_server_address}:{smtp_server_port}"
        )

        # Ultimately, send this particular message via Email and then loop to the next one
        success = send_email_message(
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
    return success


def generate_apprise_message(
    mowas_messages_to_send: dict,
    warncell_data: dict,
    apprise_config_file: str,
    abbreviated_message_format: bool = False,
    sms_message_length: int = 67,
    sms_message_split: bool = False,
):
    """
    Generates Apprise messages and triggers transmission to the user

    Parameters
    ==========
    mowas_messages_to_send : 'dict'
        dictionary, containing all messages that are to be sent to the end user
    warncell_data: 'dict'
        warncell data; these are references to German municipal areas, cities etc
    apprise_config_file: 'str'
        Apprise Yaml configuration file
    Returns
    =======
    success: 'bool'
        True if successful
    """

    # predefine the output value
    success = False

    logger.debug(msg="Starting Apprise message processing")

    if not does_file_exist(apprise_config_file):
        logger.error(
            msg=f"Apprise config file {apprise_config_file} does not exist; aborting"
        )
        return False

    # We want multi-line HTML messages. <br> does not work in e.g. Telegram
    newline = "\n"

    # Create the Apprise instance
    apobj = apprise.Apprise()

    # Create an Config instance
    config = apprise.AppriseConfig()

    # Add a configuration source:
    config.add(apprise_config_file)

    # Make sure to add our config into our apprise object
    apobj.add(config)

    # Generate the message(s)
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
        high_prio = mowas_messages_to_send[mowas_message_id]["high_prio"]
        coords_matching_latlon = mowas_messages_to_send[mowas_message_id][
            "coords_matching_latlon"
        ]
        sms_message = mowas_messages_to_send[mowas_message_id]["sms_message"]

        # get the rendered image's file name (will be 'None' in case it cannot be rendered)
        html_image = mowas_messages_to_send[mowas_message_id]["static_image"]

        # did the user request translated content?
        if "lang" in mowas_messages_to_send[mowas_message_id]:
            # yes; get the translated content
            # fmt: off
            lang_headline = mowas_messages_to_send[mowas_message_id]["lang_headline"]
            lang_description = mowas_messages_to_send[mowas_message_id]["lang_description"]
            lang_instruction = mowas_messages_to_send[mowas_message_id]["lang_instruction"]
            lang_contact = mowas_messages_to_send[mowas_message_id]["lang_contact"]
            lang_sms_message = mowas_messages_to_send[mowas_message_id]["lang_sms_message"]
            # fmt: on

            # if we send regular messages, then let's prepare the target fields
            if not abbreviated_message_format:
                # and amend out target fields
                headline = f"{lang_headline} (<i>{headline}</i>)"
                description = f"{lang_description} (<i>{description}</i>)"
                instruction = f"{lang_instruction} (<i>{instruction}</i>)"
                contact = f"{lang_contact} (<i>{contact}</i>)"
            else:
                headline = instruction = contact = ""
                description = f"{lang_sms_message}"

        # Create the message timestamp
        utc_create_time = datetime.utcnow()
        msg_string = f"{utc_create_time.strftime('%d-%b-%Y %H:%M:%S')} UTC"

        if abbreviated_message_format:
            # Set Apprise's notify icon based on the message's priority
            # (might not be supported by every messenger type)
            notify_type = (
                apprise.NotifyType.FAILURE if high_prio else apprise.NotifyType.WARNING
            )

            # We are not supposed to split the messages?
            # then use what we have and truncate

            if not sms_message_split:
                target_messages = [description[:sms_message_length]]
            else:
                target_messages = make_pretty_sms_messages(
                    message_to_add=description, max_len=sms_message_length
                )

            # Finally, send the messages
            for target_message in target_messages:
                # Send the notification. We go full SMS mode, so no titles/images/...
                apobj.notify(
                    body=target_message,
                    tag="all",
                    notify_type=notify_type,
                )
            success = True
        else:
            # Generate the message as HTML content
            apprise_message = f"<b>Message headline:</b> {headline}" + newline + newline

            apprise_message = (
                apprise_message + "<u><i>Message details</i></u>" + newline
            )

            apprise_message = (
                apprise_message + f"<b>Description:</b> {description}" + newline
            )
            apprise_message = (
                apprise_message + f"<b>Instructions:</b> {instruction}" + newline
            )
            apprise_message = apprise_message + f"<b>Contact:</b> {contact}" + newline

            apprise_message = (
                apprise_message + f"<b>Message Type:</b> {msgtype}" + newline
            )
            apprise_message = apprise_message + f"<b>Urgency:</b> {urgency}" + newline
            apprise_message = apprise_message + f"<b>Severity:</b> {severity}" + newline
            apprise_message = (
                apprise_message + f"<b>Timestamp:</b> {sent}" + newline + newline
            )

            apprise_message = (
                apprise_message + "<u><i>Address details</i></u>" + newline
            )

            for coords in coords_matching_latlon:
                latitude = coords["latitude"]
                longitude = coords["longitude"]
                address = coords["address"]
                utm = coords["utm"]
                maidenhead = coords["maidenhead"]
                aprs = coords["aprs_coordinates"]

                apprise_message = (
                    apprise_message
                    + f"<b>Lat / Lon:</b> <pre>{latitude}</pre> / <pre>{longitude}</pre>"
                )
                if aprs:
                    apprise_message = (
                        apprise_message
                        + f" (<i>This is the user's latest APRS position; see green pin on map</i>)"
                    )
                apprise_message = apprise_message + newline
                apprise_message = (
                    apprise_message + f"<b>UTM:</b> <pre>{utm}</pre>" + newline
                )
                apprise_message = (
                    apprise_message + f"<b>Grid:</b> <pre>{maidenhead}</pre>" + newline
                )
                apprise_message = (
                    apprise_message + f"<b>Address:</b> {address}" + newline + newline
                )

                # Create the message timestamp
                utc_create_time = datetime.utcnow()
                msg_string = f"{utc_create_time.strftime('%d-%b-%Y %H:%M:%S')} UTC"

            # We are done with preparing the message body
            # Create the message header
            apprise_header = (
                f"<u><i>mowas-pwb Notification</i> (generated at {msg_string})</u>\n\n"
            )

            # Set Apprise's notify icon based on the message's priority
            # (might not be supported by every messenger type)
            notify_type = (
                apprise.NotifyType.FAILURE if high_prio else apprise.NotifyType.WARNING
            )

            # Send the notification
            apobj.notify(
                body=apprise_message,
                title=apprise_header,
                tag="all",
                attach=html_image,
                notify_type=notify_type,
            )

            success = True

    logger.debug(msg="Finished Apprise message processing")
    return success


if __name__ == "__main__":
    pass
