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
import os.path

# Set up the global logger variable
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)


def get_program_config_from_file(config_filename: str = "mowas-pwb.cfg"):
    config = configparser.ConfigParser()

    try:
        config.read(config_filename)
        mowas_aprsdotfi_api_key = config.get("mowas_config", "aprsdotfi_api_key")
        mowas_watch_areas_string = config.get("mowas_config", "mowas_watch_areas")
        a = [point.split(",") for point in mowas_watch_areas_string.split(" ")]
        b = np.array(a, dtype=np.float64)
        mowas_watch_areas = b.tolist()

        mowas_deepldotcom_api_key = config.get("mowas_config", "deepldotcom_api_key")

        mowas_openai_api_key = config.get("mowas_config", "openai_api_key")
        mowas_palm_api_key = config.get("mowas_config", "palm_api_key")

        mowas_smtpimap_email_address = config.get(
            "mowas_config", "smtpimap_email_address"
        )
        mowas_smtpimap_email_password = config.get(
            "mowas_config", "smtpimap_email_password"
        )
        mowas_smtp_server_address = config.get("mowas_config", "smtp_server_address")
        mowas_smtp_server_port = config.get("mowas_config", "smtp_server_port")
        try:
            mowas_smtp_server_port = int(mowas_smtp_server_port)
        except ValueError:
            mowas_smtp_server_port = 0
            mowas_smtp_server_address = "NOT_CONFIGURED"
        mowas_imap_server_address = config.get("mowas_config", "imap_server_address")
        mowas_imap_server_port = config.get("mowas_config", "imap_server_port")
        try:
            mowas_imap_server_port = int(mowas_imap_server_port)
        except ValueError:
            mowas_imap_server_port = 0
        mowas_imap_server_address = "NOT_CONFIGURED"
        mowas_imap_mailbox_name = config.get("mowas_config", "imap_mailbox_name")
        mowas_imap_mail_retention_max_days = config.get(
            "mowas_config", "imap_mail_retention_max_days"
        )
        try:
            mowas_imap_mail_retention_max_days = int(mowas_imap_mail_retention_max_days)
        except Exception as ex:
            mowas_imap_mail_retention_max_days = 0
        mowas_acs = config.get("mowas_config", "mowas_active_categories")

        mowas_active_categories = [
            s.strip().upper() for s in mowas_acs.split(",") if mowas_acs != ""
        ]
        if len(mowas_active_categories) == 0:
            logger.info(
                msg="Config file error; at least one MOWAS category needs to be specified"
            )
            raise ValueError("Error in config file")

        for ac in mowas_active_categories:
            if ac not in [
                "TEMPEST",
                "FLOOD",
                "FLOOD_OLD",
                "WILDFIRE",
                "EARTHQUAKE",
                "DISASTERS",
            ]:
                logger.info(msg=f"Config file error; received category '{ac}'")
                raise ValueError("Error in config file")

        success = True
    except Exception as ex:
        logger.info(
            msg="Error in configuration file; Check if your config format is correct."
        )
        mowas_aprsdotfi_api_key = None
        mowas_smtpimap_email_address = mowas_smtpimap_email_password = None
        mowas_watch_areas = mowas_active_categories = []
        mowas_imap_mail_retention_max_days = mowas_imap_server_port = 0
        mowas_smtp_server_port = 0
        mowas_smtp_server_address = mowas_imap_server_address = None
        mowas_imap_mailbox_name = mowas_deepldotcom_api_key = None
        mowas_openai_api_key = mowas_palm_api_key = None
        success = False

    return (
        success,
        mowas_aprsdotfi_api_key,
        mowas_watch_areas,
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
        mowas_openai_api_key,
        mowas_palm_api_key,
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


def does_file_exist(file_name: str):
    """
    Checks if the given file exists. Returns True/False.

    Parameters
    ==========
    file_name: str
                    our file name
    Returns
    =======
    status: bool
        True /False
    """
    return os.path.isfile(file_name)


def make_pretty_sms_messages(
    message_to_add: str,
    destination_list: list = None,
    max_len: int = 67,
    separator_char: str = " ",
    add_sep: bool = True,
    force_outgoing_unicode_messages: bool = False,
):
    """
    Pretty Printer for SMS-type messages. As SMS-type messages are likely to be split
    up (due to their message len limitations), this function prevents
    'hard cuts'. Any information that is to be injected into message
    destination list is going to be checked wrt its length. If
    len(current content) + len(message_to_add) exceeds the max_len value,
    the content will not be added to the current list string but to a new
    string in the list.

    Parameters
    ==========
    message_to_add: 'str'
                    message string that is to be added to the list in a pretty way
                    If string is longer than 'max_len' chars, we will truncate the information
    destination_list: 'list'
                    List with string elements which will be enriched with the
                    'mesage_to_add' string. Default: empty list aka user wants new list
    max_len: 'int':
                    Max length of the list's string len. Default: 67 (APRS)
    separator_char: 'str'
                    Separator that is going to be used for dividing the single
                    elements that the user is going to add
    add_sep: 'bool'
                    True =  we will add the separator when more than one item
                            is in our string. This is the default
                    False = do not add the separator (e.g. if we add the
                            very first line of text, then we don't want a
                            comma straight after the location)
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
        destination_list = []

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
                destination_list = make_pretty_sms_messages(
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
        if len(destination_list) > 0:
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


def language_check(language_value):
    # fmt:off
    supported_languages = ["bg","cs","da","el","en-gb","en-us","es","et","fi","fr","hu","it","ja","lt","lv","nl","pl","pt-br","pt-pt","ro","ru","sk","sl","sv","zh"]
    # fmt:on
    if language_value:
        language_value = language_value.lower()
        if language_value not in supported_languages:
            raise argparse.ArgumentTypeError(
                f"Unsupported target language {language_value}; supported: {supported_languages}"
            )
        else:
            return language_value
    else:
        return None


def get_command_line_params():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--configfile",
        default="mowas-pwb.cfg",
        type=argparse.FileType("r"),
        help="Program config file name",
    )

    parser.add_argument(
        "--messenger-config-file",
        default=None,
        type=str,
        help="Config file name for regular messenger full-content messages",
    )

    parser.add_argument(
        "--sms-messenger-config-file",
        default=None,
        type=str,
        help="Config file name for sms-like messengers",
    )

    parser.add_argument(
        "--sms-message-length",
        dest="sms_message_length",
        default=67,
        type=int,
        help="Default message length for SMS messages",
    )

    parser.add_argument(
        "--sms-message-split",
        dest="sms_message_split",
        action="store_true",
        default=False,
        help="If enabled, all SMS messages will be split into multiple messages which ",
    )

    parser.add_argument(
        "--generate-test-message",
        dest="generate_test_message",
        action="store_true",
        help="Generates a generic test message (whereas this config is enabled) and exits the program",
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
        "--follow-the-ham",
        default=None,
        dest="follow_the_ham",
        type=str,
        help="Adds a call sign's current coordinates to the MOWAS coordinates monitored by this program",
    )

    parser.add_argument(
        "--warning-level",
        choices={"MINOR", "MODERATE", "SEVERE", "EXTREME"},
        default="MINOR",
        type=str.upper,
        help="Minimal warning level for MOWAS messages",
    )

    parser.add_argument(
        "--high-prio-level",
        choices={"MINOR", "MODERATE", "SEVERE", "EXTREME"},
        default="SEVERE",
        type=str.upper,
        help="Defines the minimal level at which messages will be sent out with high priority (rather than using standard settings)",
    )

    parser.add_argument(
        "-text-summarizer",
        choices={"generic", "internal", "openai", "palm"},
        default="internal",
        type=str.lower,
        help="Text summarizer post processor - shortens the text for mobile devices. Choose from these options: internal, generic, openai, palm. Default: internal.",
    )

    parser.add_argument(
        "--email-recipient",
        default=None,
        dest="email_recipient",
        type=str,
        help="Email recipient that will receive MOWAS messages",
    )

    parser.add_argument(
        "--enable-covid-content",
        dest="enable_covid_content",
        action="store_true",
        help="As there is a torrent of Covid-19 related news on a daily basis, mowas-pwb removes these messages by default. If you still want to receive those messages, then enable this setting",
    )

    parser.add_argument(
        "--translate-to",
        default=None,
        type=language_check,
        dest="target_language",
        help="ISO639-1 target language for MOWAS messages (will not be invoked for SMS-type messages)",
    )

    parser.add_argument(
        "--localfile",
        default=None,
        type=str,
        help="local MOWAS JSON file (for testing purposes only)",
    )

    parser.set_defaults(add_example_data=False)

    args = parser.parse_args()

    mowas_configfile = args.configfile.name
    mowas_messenger_configfile = args.messenger_config_file
    mowas_sms_messenger_configfile = args.sms_messenger_config_file
    mowas_localfile = args.localfile
    mowas_standard_run_interval = args.standard_run_interval
    mowas_emergency_run_interval = args.emergency_run_interval
    mowas_follow_the_ham = args.follow_the_ham
    mowas_generate_test_message = args.generate_test_message
    mowas_warning_level = args.warning_level
    mowas_time_to_live = args.time_to_live
    mowas_high_prio_level = args.high_prio_level
    mowas_email_recipient = args.email_recipient
    mowas_enable_covid_content = args.enable_covid_content
    mowas_target_language = args.target_language
    mowas_text_summarizer = args.text_summarizer
    mowas_sms_message_length = args.sms_message_length
    mowas_sms_message_split = args.sms_message_split

    # Did the user specify an optional JSON file for testing?
    # if yes, check if that file exists
    if mowas_localfile:
        if not does_file_exist(mowas_localfile):
            raise ValueError(
                f"Local MOWAS test file '{mowas_localfile}' does not exist"
            )

    # Did the user specify an optional generic full message file?
    # if yes, check if that file exists
    if mowas_messenger_configfile:
        if not does_file_exist(mowas_messenger_configfile):
            raise ValueError(
                f"Provided MOWAS messenger config file '{mowas_messenger_configfile}' does not exist"
            )

    # Did the user specify an optional generic message file for SMS messengers?
    # if yes, check if that file exists
    if mowas_sms_messenger_configfile:
        if not does_file_exist(mowas_sms_messenger_configfile):
            raise ValueError(
                f"Provided MOWAS short message config file '{mowas_sms_messenger_configfile}' does not exist"
            )

    # Convert requested call sign to upper case whereas present
    if mowas_follow_the_ham:
        mowas_follow_the_ham = mowas_follow_the_ham.upper()
        # Get rid of the SSID in the TO callsign (if accidentally present)
        mowas_follow_the_ham = mowas_follow_the_ham.split("-")[0].upper()

    # Convert the MOWAS Warning Level to the MOWAS-Native format:
    # First character = Uppercase, remainder is lowercase
    mowas_warning_level = string.capwords(mowas_warning_level)
    mowas_high_prio_level = string.capwords(mowas_high_prio_level)

    # check if message limit for SMS messages is smaller than 67
    # (67 = APRS) which -among all SMS messengers- is the smallest
    # message length that is known to me
    if mowas_sms_message_length < 67:
        raise ValueError("SMS message minimum length must be 67 or greater")

    return (
        mowas_configfile,
        mowas_standard_run_interval,
        mowas_emergency_run_interval,
        mowas_follow_the_ham,
        mowas_generate_test_message,
        mowas_warning_level,
        mowas_time_to_live,
        mowas_high_prio_level,
        mowas_email_recipient,
        mowas_enable_covid_content,
        mowas_target_language,
        mowas_localfile,
        mowas_messenger_configfile,
        mowas_sms_messenger_configfile,
        mowas_text_summarizer,
        mowas_sms_message_length,
        mowas_sms_message_split,
    )


def remove_html_content(message_string: str):
    if message_string:
        return re.sub("<[^<]+?>", " ", message_string)
    else:
        return message_string


if __name__ == "__main__":
    pass
