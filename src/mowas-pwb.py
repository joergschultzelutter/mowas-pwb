#!/opt/local/bin/python3
#
# MOWAS Personal Warning Beacon
# Author: Joerg Schultze-Lutter, 2021
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
import logging
import signal
from mowas import process_mowas_data
from warncell import read_warncell_info
from utils import (
    get_program_config_from_file,
    signal_term_handler,
    get_command_line_params,
)
from outputgenerator import (
    generate_dapnet_messages,
    generate_email_messages,
    generate_telegram_messages,
)
from aprsdotfi import get_position_on_aprsfi
from telegramdotcom import send_telegram_message
from dapnet import send_dapnet_message
from mail import send_email_message
from staticmap import render_png_map
from expiringdict import ExpiringDict
import time
from apscheduler.schedulers.background import BackgroundScheduler
import apscheduler.schedulers.base
from mail import imap_garbage_collector
from test_data_generator import generate_test_data
import copy

# Set up the global logger variable
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info(msg="Startup ...")

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

    # get our configuration data from the external configuration file
    (
        success,
        mowas_aprsdotfi_api_key,
        mowas_dapnet_login_callsign,
        mowas_dapnet_login_passcode,
        mowas_watch_areas_config,
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
    ) = get_program_config_from_file(config_filename=mowas_configfile)
    if not success:
        logger.info(msg="Error while parsing the program config file; exiting...")
        exit(0)

    # Define some boolean hints on what is enabled and what is not
    # fmt: off
    mowas_aprsdotfi_enabled = False if mowas_aprsdotfi_api_key == "NOT_CONFIGURED" else True
    mowas_dapnet_enabled = False if mowas_dapnet_login_callsign == "NOT_CONFIGURED" else True
    mowas_telegram_enabled = False if mowas_telegram_bot_token == "NOT_CONFIGURED" else True
    mowas_email_enabled = False if (mowas_smtpimap_email_address == "NOT_CONFIGURED" or mowas_smtpimap_email_password == "NOT_CONFIGURED") else True
    mowas_imap_gc_enabled = False if (mowas_imap_server_port == 0 or mowas_imap_server_address == "NOT_CONFIGURED" or mowas_imap_mail_retention_max_days == 0 or not mowas_email_enabled) else True
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

    # Check if the user asks us to track a ham radio user but has not configured aprs.fi credentials
    if not mowas_aprsdotfi_enabled and mowas_follow_the_ham:
        logger.info(
            msg=f"Cannot track call sign for {mowas_follow_the_ham} - aprs.fi credentials are not configured; exiting..."
        )
        exit(0)

    # Check if the emergency sleep time is greater than the standard sleep time
    if mowas_emergency_run_interval > mowas_standard_run_interval:
        logger.info(
            msg=f"Interval 'emergency' settings of {mowas_emergency_run_interval} is greater than 'standard' setting of {mowas_standard_run_interval}; exiting ..."
        )
        exit(0)

    # If the user wants us to track a ham radio user AND has configured
    # the aprs.fi credentials, verify if we can access aprs.fi and if
    # that user's call sign can be found via the API

    success = False
    latitude = longitude = 0.0

    if mowas_aprsdotfi_enabled and mowas_follow_the_ham:
        success, latitude, longitude = get_position_on_aprsfi(
            aprsfi_callsign=mowas_follow_the_ham,
            aprsdotfi_api_key=mowas_aprsdotfi_api_key,
        )
        if not success:
            logger.info(
                msg=f"Cannot find call sign {mowas_follow_the_ham} or aprs.fi or its API access key is misconfigured/invalid; exiting ..."
            )
            exit(0)

    # Read the "Warncell" data which will later enables us to come up with proper
    # (short) names for MOWAS areas in question
    success, warncell_data = read_warncell_info()
    if not success:
        logger.info("Cannot read Warncell data from the DWD site; cannot continue")
        exit(0)

    #
    # We've checked all parameters - let's start with setting up our environment
    #

    # If we have just been asked to generate a test message then
    # let's do so and exit the program afterwards
    if mowas_generate_test_message:
        logger.info(msg="Configuration test enabled")
        # generate our fixed test data
        mowas_messages_to_send = generate_test_data()

        # Send to DAPNET if enabled
        if mowas_dapnet_enabled:
            logger.info(
                msg=f"Sending mowas-pwb test message to DAPNET account {mowas_dapnet_destination_callsign}"
            )
            success = generate_dapnet_messages(
                mowas_messages_to_send=mowas_messages_to_send,
                warncell_data=warncell_data,
                mowas_dapnet_destination_callsign=mowas_dapnet_destination_callsign,
                mowas_dapnet_login_callsign=mowas_dapnet_login_callsign,
                mowas_dapnet_login_passcode=mowas_dapnet_login_passcode,
            )
            logger.info(msg=f"DAPNET message success: {success}")

        # Send to Telegram if enabled
        if mowas_telegram_enabled:
            logger.info(
                msg=f"Sending mowas-pwb test message to Telegram account {mowas_telegram_destination_id}"
            )
            success = generate_telegram_messages(
                mowas_messages_to_send=mowas_messages_to_send,
                warncell_data=warncell_data,
                mowas_telegram_bot_token=mowas_telegram_bot_token,
                telegram_target_id=mowas_telegram_destination_id,
            )
            logger.info(msg=f"Telegram message success: {success}")

        # Send to mail account if enabled
        if mowas_email_enabled:
            logger.info(
                msg=f"Sending mowas-pwb test message to Email account {mowas_email_recipient}"
            )
            success = generate_email_messages(
                mowas_messages_to_send=mowas_messages_to_send,
                warncell_data=warncell_data,
                smtpimap_email_address=mowas_smtpimap_email_address,
                smtpimap_email_password=mowas_smtpimap_email_password,
                smtp_server_port=mowas_smtp_server_port,
                smtp_server_address=mowas_smtp_server_address,
                mail_recipient=mowas_email_recipient,
            )
            logger.info(msg=f"Email message success: {success}")
        logger.info(msg="Configuration test cycle complete; exiting")
        exit(0)

    # If we reach this point, then we are supposed to do some real work

    # Register the SIGTERM handler; this will allow a safe shutdown of the program
    logger.info(msg="Registering SIGTERM handler for safe shutdown...")
    signal.signal(signal.SIGTERM, signal_term_handler)

    # Set up the ExpiringDict for our entries
    mowas_message_cache = ExpiringDict(max_len=1000, max_age_seconds=mowas_time_to_live)

    # Check if we need to install/activate the Email garbage collector
    mail_gc_scheduler = None
    if mowas_imap_gc_enabled:
        logger.info(msg="Spinning up the IMAP garbage collector per our user's request")

        # Set up the scheduler
        mail_gc_scheduler = BackgroundScheduler()

        # Then add the Garbage Collector process as scheduler task
        mail_gc.scheduler.add_job(
            imap_garbage_collector,
            "interval",
            id="imap_garbage_collector",
            days=mowas_imap_mail_retention_max_days,
            args=[
                mowas_smtpimap_email_address,
                mowas_smtpimap_email_password,
                mowas_imap_server_port,
                mowas_imap_server_address,
                mowas_imap_mail_retention_max_days,
                mowas_imap_mailbox_name,
            ],
        )

        # And finally start the scheduler
        mail_gc_scheduler.start()
        logger.info(msg="IMAP garbage collector has been activated")

    logger.info(msg="Entering processing loop...")
    while True:

        # Set the program's run interval to default settings
        mowas_run_interval = mowas_standard_run_interval

        # use a copy of the watch areas as we may need to amend
        # this static information my adding the user's APRS
        # position data to it
        mowas_watch_areas = copy.deepcopy(mowas_watch_areas_config)

        # Do we need to track the user's config on aprs.fi?
        if mowas_follow_the_ham:
            logger.debug(
                msg=f"Trying to get lat/lon for {mowas_follow_the_ham} on aprs.fi ..."
            )
            # yes; let's get the latitude and longitude info
            success, latitude, longitude = get_position_on_aprsfi(
                aprsfi_callsign=mowas_follow_the_ham,
                aprsdotfi_api_key=mowas_aprsdotfi_api_key,
            )
            # Add the lat/lon combination to our copied watch list
            # If we were unable to find the call sign on aprs.fi,
            # we will NOT trigger an error
            if success:
                logger.debug(
                    msg=f"APRS.fi coordinate retrieval successful; adding coordinates to watchlist ..."
                )
                latlon = [latitude, longitude]
                mowas_watch_areas.append(latlon)
            else:
                logger.debug(
                    msg=f"Unable to retrieve coordinates on aprs.fi; user's coordinates will not be watched ..."
                )

        logger.debug(msg=f"Monitoring coordinates: {mowas_watch_areas}")

        try:
            logger.debug(msg=f"Processing MOWAS data ...")
            (
                mowas_message_cache,
                mowas_messages_to_send,
                got_alert_or_update,
            ) = process_mowas_data(
                coordinates=mowas_watch_areas,
                mowas_cache=mowas_message_cache,
                minimal_mowas_severity=mowas_warning_level,
                mowas_dapnet_high_prio_level=mowas_dapnet_high_prio_level,
                mowas_active_categories=mowas_active_categories,
                enable_covid_messaging=mowas_enable_covid_content,
            )

            # Did we find some new message updates that we need to send to the user?
            if len(mowas_messages_to_send.keys()) > 0:
                logger.info(msg=f"{len(mowas_messages_to_send)} new message(s) found")

                # Use the emergency run interval setting for the sleep
                # if we have received at least one alert or update msg
                if got_alert_or_update:
                    mowas_run_interval = mowas_emergency_run_interval

                # Check if we need to send something to DAPNET
                if mowas_dapnet_enabled:
                    logger.info(msg="Generating DAPNET notifications")
                    success = generate_dapnet_messages(
                        mowas_messages_to_send=mowas_messages_to_send,
                        warncell_data=warncell_data,
                        mowas_dapnet_destination_callsign=mowas_dapnet_destination_callsign,
                        mowas_dapnet_login_callsign=mowas_dapnet_login_callsign,
                        mowas_dapnet_login_passcode=mowas_dapnet_login_passcode,
                    )
                    logger.info(msg=f"Telegram message success: {success}")

                # Check if we need to send something to Telegram
                if mowas_telegram_enabled:
                    logger.info(msg="Generating Telegram notifications")
                    success = generate_telegram_messages(
                        mowas_messages_to_send=mowas_messages_to_send,
                        warncell_data=warncell_data,
                        mowas_telegram_bot_token=mowas_telegram_bot_token,
                        telegram_target_id=mowas_telegram_destination_id,
                    )
                    logger.info(msg=f"Telegram message success: {success}")

                # Finally, check if we need to send something via Email
                if mowas_email_enabled:
                    logger.info(msg="Preparing Email notifications")
                    success = generate_email_messages(
                        mowas_messages_to_send=mowas_messages_to_send,
                        warncell_data=warncell_data,
                        smtpimap_email_address=mowas_smtpimap_email_address,
                        smtpimap_email_password=mowas_smtpimap_email_password,
                        mail_recipient=mowas_email_recipient,
                    )
                    logger.info(msg=f"Email message success: {success}")
            else:
                logger.debug(msg="No new messages found")

            # Finally, go to sleep
            logger.info(msg=f"Entering sleep mode for {mowas_run_interval} mins...")
            time.sleep(mowas_run_interval * 60)
            logger.info(msg="Recovered from sleep mode ...")
        except (KeyboardInterrupt, SystemExit):
            logger.info(
                msg="Received KeyboardInterrupt or SystemExit in progress; shutting down ..."
            )
            # Check if we need to terminate the garbage collector scheduler
            if mowas_imap_gc_enabled and mail_gc_scheduler:
                logger.info(msg="Pausing IMAP Garbage Collector")
                mail_gc_scheduler.pause()
                mail_gc_scheduler.remove_all_jobs()
                logger.info(msg="Stopping IMAP Garbage Collector")
                if mail_gc_scheduler.state != apscheduler.schedulers.base.STATE_STOPPED:
                    try:
                        mail_gc_scheduler.shutdown()
                    except Exception as ex:
                        logger.info(
                            msg="Exception occurred during shutdown SystemExit loop"
                        )
            # Finally, terminate the loop
            break
