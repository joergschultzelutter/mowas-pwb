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
from utils import convert_text_to_plain_ascii, remove_html_content
from warncell import read_warncell_info

# Set up the global logger variable
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)

def generate_dapnet_messages(mowas_messages_to_send: dict, warncell_data: dict):

    # This is our target list element which contains all messages that
    # are to be sent to our DAPNET account. One list entry equals one 
    # logical message along with its DAPNET priority. As DAPNET can only 
    # digest 80 chars per physical message, the send-to-DAPNET function 
    # will chop up the messages into multi-message packets, if necessary
    output_list = {}

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
                    msg = msg + convert_text_to_plain_ascii(remove_html_content(areas[idx])) + " "

        # Remove any trailing blanks
        msg = msg.rstrip()

        # and add our message to the dictionary
        message = {"msg": msg, "priority": dapnet_high_prio}
        output_list[mowas_message_id] = message

    return output_list


def generate_telegram_messages(mowas_messages_to_send: dict, warncell_data: dict):
    output_list = []
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
    return output_list


if __name__ == "__main__":
    success, warncell_data = read_warncell_info()
    if not success:
        logger.info("Cannot read warncell data")
        exit(0)

    #https://warnung.bund.de/bbk.status/status_032410000000.json

    mowas_messages_to_send = {"DE-BY-A-W083-20200828-000": {"headline": "Vorübergehende Änderung der Trinkwasserqualität: Chlorung besteht weiterhin", "urgency": "Immediate", "severity": "Minor", "description": "Die Chlorung besteht weiterhin.", "instruction": "Informieren Sie sich in den Medien, zum Beispiel im Lokalradio.<br/>Das Wasser muss nicht mehr abgekocht werden.", "sent": "2020-08-28T11:00:08+02:00", "msgtype": "Alert", "areas": ["Stadt Gersthofen, Gemeinde Gablingen"], "geocodes": ["097720000000"], "dapnet_high_prio": True}}
