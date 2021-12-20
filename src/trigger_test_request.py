#
# MOWAS Personal Warning Beacon
# Simple wrapper code for message offline testing
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
from utils import get_program_config_from_file, get_command_line_params
from warncell import read_warncell_info
from outputgenerator import (
    generate_email_messages,
    generate_dapnet_messages,
    generate_telegram_messages,
)
from test_data_generator import generate_test_data


# Set up the global logger variable
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)


def msggen():
    # get config file values
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

    # Get our command line parameters
    (
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
        mowas_disable_email,
        mowas_email_recipient,
        mowas_enable_covid_content,
        mowas_target_language,
    ) = get_command_line_params()

    # User wants to disable both DAPNET and Telegram?
    if mowas_disable_dapnet and mowas_disable_telegram and mowas_disable_email:
        logger.info(
            msg="User has disabled all output options (DAPNET, email and Telegram); exiting..."
        )
        exit(0)

    success, warncell_data = read_warncell_info()
    if not success:
        logger.info("Cannot read warncell data")
        exit(0)

    # Define some boolean hints on what is enabled and what is not
    # fmt: off
    mowas_dapnet_enabled = False if mowas_dapnet_login_callsign == "NOT_CONFIGURED" else True
    mowas_telegram_enabled = False if mowas_telegram_bot_token == "NOT_CONFIGURED" else True
    mowas_email_enabled = False if (mowas_smtpimap_email_address == "NOT_CONFIGURED" or mowas_smtpimap_email_password == "NOT_CONFIGURED") else True
    # fmt: on

    # some basic checks on whether the user wants us to do the impossible :-)

    if mowas_telegram_enabled and mowas_telegram_destination_id == 0:
        logger.info(msg="Valid Telegram destination ID is missing; disabling Telegram")
        mowas_telegram_enabled = False

    if mowas_dapnet_enabled and mowas_dapnet_destination_callsign is None:
        logger.info(
            msg="Valid DAPNET destination call sign is missing; disabling DAPNET"
        )
        mowas_dapnet_enabled = False

    if mowas_email_enabled and mowas_email_recipient is None:
        logger.info(msg="Valid destination email is missing; disabling Email")
        mowas_email_enabled = False

    if (
        not mowas_dapnet_enabled
        and not mowas_telegram_enabled
        and not mowas_email_enabled
    ):
        logger.info(
            msg="No target credentials (DAPNET, Email or Telegram) configured or no messaging destinations specified; exiting ..."
        )
        exit(0)

    # Generate a fixed test message
    mowas_messages_to_send = generate_test_data()

    # List contains the message types that we want to send out
    testmethods = ["telegram", "dapnet", "email"]

    if "email" in testmethods:
        if mowas_email_enabled:
            logger.info(
                msg=f"Sending mowas-pwb test message to Email account {mowas_email_recipient}"
            )
            logger.info(
                generate_email_messages(
                    mowas_messages_to_send=mowas_messages_to_send,
                    warncell_data=warncell_data,
                    smtpimap_email_address=mowas_smtpimap_email_address,
                    smtpimap_email_password=mowas_smtpimap_email_password,
                    mail_recipient=mowas_email_recipient,
                    smtp_server_address=mowas_smtp_server_address,
                    smtp_server_port=mowas_smtp_server_port,
                )
            )

    if "telegram" in testmethods:
        if mowas_telegram_enabled:
            logger.info(
                msg=f"Sending mowas-pwb test message to Telegram account {mowas_telegram_destination_id}"
            )
            logger.info(
                generate_telegram_messages(
                    mowas_messages_to_send=mowas_messages_to_send,
                    warncell_data=warncell_data,
                    mowas_telegram_bot_token=mowas_telegram_bot_token,
                    telegram_target_id=mowas_telegram_destination_id,
                )
            )

    if "dapnet" in testmethods:
        if mowas_dapnet_enabled:
            logger.info(
                msg=f"Sending mowas-pwb test message to DAPNET account {mowas_dapnet_destination_callsign}"
            )
            logger.info(
                generate_dapnet_messages(
                    mowas_messages_to_send=mowas_messages_to_send,
                    warncell_data=warncell_data,
                    mowas_dapnet_destination_callsign=mowas_dapnet_destination_callsign,
                    mowas_dapnet_login_callsign=mowas_dapnet_login_callsign,
                    mowas_dapnet_login_passcode=mowas_dapnet_login_passcode,
                )
            )


if __name__ == "__main__":
    msggen()
