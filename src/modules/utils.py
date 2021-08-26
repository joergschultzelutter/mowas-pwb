#
# MOWAS Personal Warning Beacon
# Module: various utility functions used by the program
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

import numpy as np
import configparser
from unidecode import unidecode
import re
import logging
import sys
import argparse
import string

# Set up the global logger variable
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)


def get_program_config_from_file(config_filename: str):
    config = configparser.ConfigParser()
    success = False

    mowas_aprsdotfi_api_key = mowas_dapnet_login_callsign = None
    mowas_dapnet_login_passcode = mowas_watch_areas_string = None
    mowas_telegram_bot_token = None
    mowas_watch_areas = []

    try:
        config.read(config_filename)
        mowas_aprsdotfi_api_key = config.get("mowas_config", "aprsdotfi_api_key")
        mowas_dapnet_login_callsign = config.get(
            "mowas_config", "dapnet_login_callsign"
        )
        mowas_dapnet_login_passcode = config.get(
            "mowas_config", "dapnet_login_passcode"
        )
        mowas_watch_areas_string = config.get("mowas_config", "mowas_watch_areas")
        mowas_telegram_bot_token = config.get("mowas_config", "telegram_bot_token")
        success = True
    except:
        mowas_aprsdotfi_api_key = mowas_dapnet_login_callsign = None
        mowas_dapnet_login_passcode = mowas_watch_areas_string = None
        mowas_telegram_bot_token = None
        mowas_watch_areas = []
        success = False

    if success:
        try:
            a = [point.split(",") for point in mowas_watch_areas_string.split(" ")]
            b = np.array(a, dtype=np.float64)
            mowas_watch_areas = b.tolist()
            success = True
        except:
            c = []
            logger.info(
                msg="Error in configuration file; cannot create MOWAS watch areas list"
            )
            success = False

    return (
        success,
        mowas_aprsdotfi_api_key,
        mowas_dapnet_login_callsign,
        mowas_dapnet_login_passcode,
        mowas_watch_areas,
        mowas_telegram_bot_token,
    )


def signal_term_handler(signal_number, frame):
    """
    Signal handler for SIGTERM signals. Ensures that the program
    gets terminated in a safe way, thus allowing all databases etc
    to be written to disc.

    Parameters
    ==========
    signal_number:
                    The signal number
    frame:
                    Signal frame

    Returns
    =======
    """

    logger.info(msg="Received SIGTERM; forcing clean program exit")
    sys.exit(0)


def make_pretty_dapnet_messages(
    message_to_add: str,
    destination_list: list = None,
    max_len: int = 80,
    separator_char: str = " ",
    add_sep: bool = True,
    force_outgoing_unicode_messages: bool = False,
):
    """
    Pretty Printer for DAPNET messages. As DAPNET messages are likely to be split
    up (due to the 80 chars message len limitation), this function prevents
    'hard cuts'. Any information that is to be injected into message
    destination list is going to be checked wrt its length. If
    len(current content) + len(message_to_add) exceeds the max_len value,
    the content will not be added to the current list string but to a new
    string in the list.

    Parameters
    ==========
    message_to_add: 'str'
                    message string that is to be added to the list in a pretty way
                    If string is longer than 80 chars, we will truncate the information
    destination_list: 'list'
                    List with string elements which will be enriched with the
                    'mesage_to_add' string. Default: empty list aka user wants new list
    max_len: 'int':
                    Max length of the list's string len. 80 for DAPNET messages
    separator_char: 'str'
                    Separator that is going to be used for dividing the single
                    elements that the user is going to add
    add_sep: 'bool'
                    True = we will add the separator when more than one item
                                       is in our string. This is the default
                    False = do not add the separator (e.g. if we add the
                                                    very first line of text, then we don't want a
                                                    comma straight after the location
    force_outgoing_unicode_messages: 'bool'
                    False = all outgoing UTF-8 content will be down-converted
                                                    to ASCII content
                    True = all outgoing UTF-8 content will sent out 'as is'

    Returns
    =======
    destination_list: 'list'
                    List array, containing 1..n human readable strings with
                    the "message_to_add' input data
    """
    # Dummy handler in case the list is completely empty
    # or a reference to a list item has not been specified at all
    # In this case, create an empty list
    if not destination_list:
        destination_list = [""]

    # replace non-permitted APRS characters from the
    # message text
    # see APRS specification pg. 71
    message_to_add = re.sub("[{}|~]+", "", message_to_add)

    # Check if the user wants unicode messages. Default is ASCII
    if not force_outgoing_unicode_messages:
        # Convert the message to plain ascii
        # Unidecode does not take care of German special characters
        # Therefore, we need to 'translate' them first
        message_to_add = convert_text_to_plain_ascii(message_string=message_to_add)

    # If new message is longer than max len then split it up with
    # max chunks of max_len bytes and add it to the array.
    # This should never happen but better safe than sorry.
    # Keep in mind that we only transport plain text anyway.
    if len(message_to_add) > max_len:
        split_data = message_to_add.split()
        for split in split_data:
            # if string is short enough then add it by calling ourself
            # with the smaller text chunk
            if len(split) < max_len:
                destination_list = make_pretty_dapnet_messages(
                    message_to_add=split,
                    destination_list=destination_list,
                    max_len=max_len,
                    separator_char=separator_char,
                    add_sep=add_sep,
                    force_outgoing_unicode_messages=force_outgoing_unicode_messages,
                )
            else:
                # string exceeds max len; split it up and add it as is
                string_list = split_string_to_string_list(
                    message_string=split, max_len=max_len
                )
                for msg in string_list:
                    destination_list.append(msg)
    else:  # try to insert
        # Get very last element from list
        string_from_list = destination_list[-1]

        # element + new string > max len? no: add to existing string, else create new element in list
        if len(string_from_list) + len(message_to_add) + 1 <= max_len:
            delimiter = ""
            if len(string_from_list) > 0 and add_sep:
                delimiter = separator_char
            string_from_list = string_from_list + delimiter + message_to_add
            destination_list[-1] = string_from_list
        else:
            destination_list.append(message_to_add)

    return destination_list


def split_string_to_string_list(message_string: str, max_len: int = 80):
    """
    Force-split the string into chunks of max_len size and return a list of
    strings. This function is going to be called if the string that the user
    wants to insert exceeds more than e.g. 80 characters. In this unlikely
    case, we may not be able to add the string in a pretty format - but
    we will split it up for the user and ensure that none of the data is lost

    Parameters
    ==========
    message_string: 'str'
                    message string that is to be divided into 1..n strings of 'max_len"
                    text length
    max_len: 'int':
                    Max length of the list's string len. Default = 67 for APRS messages

    Returns
    =======
    split_strings: 'list'
                    List array, containing 1..n strings with a max len of 'max_len'
    """
    split_strings = [
        message_string[index : index + max_len]
        for index in range(0, len(message_string), max_len)
    ]
    return split_strings


def convert_text_to_plain_ascii(message_string: str):
    """
    Converts a string to plain ASCII

    Parameters
    ==========
    message_string: 'str'
                    Text that needs to be converted

    Returns
    =======
    hex-converted text to the user
    """
    message_string = (
        message_string.replace("Ä", "Ae")
        .replace("Ö", "Oe")
        .replace("Ü", "Ue")
        .replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
    )
    message_string = unidecode(message_string)
    return message_string


def standard_run_interval_check(interval_value):
    interval_value = int(interval_value)
    if interval_value < 60:
        raise argparse.ArgumentTypeError("Minimum standard interval is 60 (minutes)")
    return interval_value

def emergency_run_interval_check(interval_value):
    interval_value = int(interval_value)
    if interval_value < 15:
        raise argparse.ArgumentTypeError("Minimum emergency interval is 15 (minutes)")
    return interval_value

def get_command_line_params():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--configfile",
        default="mowas-pwb.cfg",
        type=argparse.FileType("r"),
        help="Program config file name",
    )

    parser.add_argument(
        "--disable-dapnet",
        dest="disable_dapnet",
        action="store_true",
        help="Disables any messages to be sent out to DAPNET even if the config file contains proper credentials",
    )

    parser.add_argument(
        "--disable-telegram",
        dest="disable_telegram",
        action="store_true",
        help="Disables any messages to be sent out to Telegram even if the config file contains proper credentials",
    )

    parser.add_argument(
        "--generate-test-message",
        dest="generate_test_message",
        action="store_true",
        help="Generates a DAPNET / Telegram test message (whereas this config is enabled) and exits the program",
    )

    parser.add_argument(
        "--standard-run-interval",
        dest="standard_run_interval",
        default=60,
        type=standard_run_interval_check,
        help="MOWAS check interval in case no previous incident for the given watch area has been detected. Minimal value = 60 (minutes)",
    )

    parser.add_argument(
        "--emergency-run-interval",
        dest="emergency_run_interval",
        default=15,
        type=emergency_run_interval_check,
        help="MOWAS check interval in case at least one incident for the given watch area has been detected. Minimal value = 15 (minutes)",
    )

    parser.add_argument(
        "--ttl",
        dest="time_to_live",
        default=8 * 60,
        type=int,
        help="Message 'time to live' setting in minutes. Default value is 480m mins = 8h",
    )

    parser.add_argument(
        "--dapnet-destination-callsign",
        default=None,
        dest="dapnet_destination_callsign",
        type=str,
        help="DAPNET destination call sign which will receive the MOWAS messages",
    )

    parser.add_argument(
        "--telegram-destination-id",
        default=0,
        dest="telegram_destination_id",
        type=int,
        help="Telegram user ID which will receive the MOWAS messages (use bot 'UserInfoBot')",
    )

    parser.add_argument(
        "--follow-the-ham",
        default=None,
        dest="follow_the_ham",
        type=str,
        help="Adds a call sign's current coordinates to the MOWAS coordinates monitored by this program",
    )

    parser.add_argument(
        "--warning_level",
        choices={"MINOR", "MODERATE", "SEVERE", "EXTREME"},
        default="MINOR",
        type=str.upper,
        help="Minimal warning level for MOWAS messages",
    )

    parser.add_argument(
        "--dapnet_high_prio_level",
        choices={"MINOR", "MODERATE", "SEVERE", "EXTREME"},
        default="SEVERE",
        type=str.upper,
        help="Defines the minimal level at which DAPNET messages will be sent out with high priority (rather than using standard settings)",
    )

    parser.set_defaults(add_example_data=False)

    args = parser.parse_args()

    mowas_configfile = args.configfile.name
    mowas_standard_run_interval = args.standard_run_interval
    mowas_emergency_run_interval = args.emergency_run_interval
    mowas_dapnet_destination_callsign = args.dapnet_destination_callsign
    mowas_telegram_destination_id = args.telegram_destination_id
    mowas_disable_telegram = args.disable_telegram
    mowas_disable_dapnet = args.disable_dapnet
    mowas_follow_the_ham = args.follow_the_ham
    mowas_generate_test_message = args.generate_test_message
    mowas_warning_level = args.warning_level
    mowas_time_to_live = args.time_to_live
    mowas_dapnet_high_prio_level = args.dapnet_high_prio_level

    # Convert requested call sign to upper case whereas present
    if mowas_follow_the_ham:
        mowas_follow_the_ham = mowas_follow_the_ham.upper()
        # Get rid of the SSID in the TO callsign (if accidentally present)
        mowas_follow_the_ham = mowas_follow_the_ham.split("-")[0].upper()

    # Convert the MOWAS Warning Level to the MOWAS-Native format:
    # First character = Uppercase, remainder is lowercase
    mowas_warning_level = string.capwords(mowas_warning_level)
    mowas_dapnet_high_prio_level = string.capwords(mowas_dapnet_high_prio_level)

    return (
        mowas_configfile,
        mowas_standard_run_interval,
        mowas_emergency_run_interval,
        mowas_dapnet_destination_callsign,
        mowas_telegram_destination_id,
        mowas_disable_telegram,
        mowas_disable_dapnet,
        mowas_follow_the_ham,
        mowas_generate_test_message,
        mowas_warning_level,
        mowas_time_to_live,
        mowas_dapnet_high_prio_level,
    )
