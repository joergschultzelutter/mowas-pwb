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
    generate_email_messages,
    generate_generic_apprise_message,
)
from aprsdotfi import get_position_on_aprsfi
from mail import send_email_message
from staticmap import render_png_map
from expiringdict import ExpiringDict
import time
from apscheduler.schedulers.background import BackgroundScheduler
import apscheduler.schedulers.base
from mail import imap_garbage_collector
from test_data_generator import generate_test_data
import copy
import asyncio
import os

# Set up the global logger variable
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)


def image_garbage_collector(mowas_messages_to_send: dict):
    logger.debug(msg="Starting image files garbage collector")

    for mowas_message_id in mowas_messages_to_send:
        file_name = mowas_messages_to_send[mowas_message_id]["static_image"]
        if os.path.isfile(file_name):
            os.remove(file_name)

    logger.debug(msg="Finishing image files garbage collector")


if __name__ == "__main__":
    logger.info(msg="Startup ...")

    # Get our command line parameters
    (
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
    ) = get_command_line_params()

    # Check if the user has specified ANY messaging configuration
    if (
        mowas_email_recipient == None
        and mowas_sms_messenger_configfile == None
        and mowas_messenger_configfile == None
    ):
        logger.info(msg="User has disabled all output options; exiting...")
        exit(0)

    # get our configuration data from the external configuration file
    (
        success,
        mowas_aprsdotfi_api_key,
        mowas_watch_areas_config,
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
    ) = get_program_config_from_file(config_filename=mowas_configfile)
    if not success:
        logger.info(msg="Error while parsing the program config file; exiting...")
        exit(0)

    # Define some boolean hints on what is enabled and what is not
    # fmt: off
    mowas_openai_enabled = False if mowas_openai_api_key == "NOT_CONFIGURED" else True
    mowas_palm_enabled = False if mowas_palm_api_key == "NOT_CONFIGURED" else True
    mowas_aprsdotfi_enabled = False if mowas_aprsdotfi_api_key == "NOT_CONFIGURED" else True
    mowas_email_enabled = False if (mowas_smtpimap_email_address == "NOT_CONFIGURED" or mowas_smtpimap_email_password == "NOT_CONFIGURED") else True
    mowas_imap_gc_enabled = False if (mowas_imap_server_port == 0 or mowas_imap_server_address == "NOT_CONFIGURED" or mowas_imap_mail_retention_max_days == 0 or not mowas_email_enabled) else True
    # fmt: on

    # some basic checks on whether the user wants us to do the impossible :-)
    if mowas_email_enabled and mowas_email_recipient is None:
        logger.info(msg="Valid destination email is missing; disabling Email")
        mowas_email_enabled = False

    if (
        mowas_email_enabled
        and not mowas_sms_messenger_configfile
        and not mowas_messenger_configfile
    ):
        logger.info(
            msg="No messenger target credentials configured or no messaging destinations specified; exiting ..."
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

    # Check if the user wants to use OpenAI as port processor: do we have an API key?
    if mowas_text_summarizer == "openai" and not mowas_openai_enabled:
        logger.info(
            msg="If you want to use the OpenAI post processor, then you need to specify an API key in the config file. Exiting."
        )
        exit(0)

    # Check if the user wants to use Google PaLM as port processor: do we have an API key?
    if mowas_text_summarizer == "palm" and not mowas_palm_enabled:
        logger.info(
            msg="If you want to use the Google PaLM post processor, then you need to specify an API key in the config file. Exiting."
        )
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

        if mowas_messenger_configfile:
            logger.info(
                msg=f"Sending mowas-pwb test message to MOWAS 'regular' config file {mowas_messenger_configfile}"
            )
            success = generate_generic_apprise_message(
                mowas_messages_to_send=mowas_messages_to_send,
                warncell_data=warncell_data,
                apprise_config_file=mowas_messenger_configfile,
            )
            logger.info(msg=f"Full message success: {success}")

        if mowas_sms_messenger_configfile:
            logger.info(
                msg=f"Sending mowas-pwb test message to MOWAS 'SMS' config file {mowas_sms_messenger_configfile}"
            )
            success = generate_generic_apprise_message(
                mowas_messages_to_send=mowas_messages_to_send,
                warncell_data=warncell_data,
                apprise_config_file=mowas_sms_messenger_configfile,
            )
            logger.info(msg=f"SMS message success: {success}")

        # Remove all local image files
        image_garbage_collector(mowas_messages_to_send=mowas_messages_to_send)

        logger.info(msg="Configuration test cycle complete; exiting")
        exit(0)

    # If we reach this point, then we are supposed to do some real work

    # Register the SIGTERM handler; this will allow a safe shutdown of the program
    logger.info(msg="Registering SIGTERM handler for safe shutdown...")
    signal.signal(signal.SIGTERM, signal_term_handler)

    # Set up the ExpiringDict for our entries
    # User has specified target value in minutes but we need seconds
    # so let's multiply by 60
    mowas_message_cache = ExpiringDict(
        max_len=1000, max_age_seconds=mowas_time_to_live * 60
    )

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

    logger.debug(msg="Entering processing loop...")
    while True:
        # Set the program's run interval to default settings
        mowas_run_interval = mowas_standard_run_interval

        # use a deep copy of the watch areas as we may need to amend
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
                logger.debug(msg=f"Amended watchlist: {mowas_watch_areas}")
            else:
                logger.debug(
                    msg=f"Unable to retrieve coordinates on aprs.fi; user's coordinates will not be watched ..."
                )
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
                mowas_high_prio_level=mowas_high_prio_level,
                mowas_active_categories=mowas_active_categories,
                enable_covid_messaging=mowas_enable_covid_content,
                local_file_name=mowas_localfile,
            )

            # Did we find some new message updates that we need to send to the user?
            if len(mowas_messages_to_send.keys()) > 0:
                logger.info(msg=f"{len(mowas_messages_to_send)} new message(s) found")

                # Use the emergency run interval setting for the sleep
                # if we have received at least one alert or update msg
                if got_alert_or_update:
                    mowas_run_interval = mowas_emergency_run_interval

                # Check if we need to send something via Email
                if mowas_email_enabled:
                    logger.debug(msg="Generating Email notifications")
                    success = generate_email_messages(
                        mowas_messages_to_send=mowas_messages_to_send,
                        warncell_data=warncell_data,
                        smtpimap_email_address=mowas_smtpimap_email_address,
                        smtpimap_email_password=mowas_smtpimap_email_password,
                        mail_recipient=mowas_email_recipient,
                        smtp_server_address=mowas_smtp_server_address,
                        smtp_server_port=mowas_smtp_server_port,
                    )
                    logger.debug(msg=f"Email message success: {success}")

                # Check if we need to send something via Apprise 'full msg' config
                if mowas_messenger_configfile:
                    logger.debug(msg="Generating Apprise 'full msg' notifications")
                    success = generate_generic_apprise_message(
                        mowas_messages_to_send=mowas_messages_to_send,
                        warncell_data=warncell_data,
                        apprise_config_file=mowas_messenger_configfile,
                    )
                    logger.info(msg=f"Apprise 'full msg' success: {success}")

                # Check if we need to send something via Apprise 'SMS msg' config
                if mowas_sms_messenger_configfile:
                    logger.debug(msg="Generating Apprise 'SMS msg' notifications")
                    success = generate_generic_apprise_message(
                        mowas_messages_to_send=mowas_messages_to_send,
                        warncell_data=warncell_data,
                        apprise_config_file=mowas_sms_messenger_configfile,
                    )
                    logger.info(msg=f"Apprise 'SMS msg' success: {success}")

                # Remove all local image files
                image_garbage_collector(mowas_messages_to_send=mowas_messages_to_send)
            else:
                logger.debug(msg="No new messages found")

            # Exit the loop if we were testing with a local file
            if mowas_localfile:
                break

            # Finally, go to sleep
            logger.debug(msg=f"Entering sleep mode for {mowas_run_interval} mins...")
            time.sleep(mowas_run_interval * 60)
            logger.debug(msg="Recovered from sleep mode ...")
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
