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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
import logging
import signal
from modules.mowas import process_mowas_data
from modules.utils import (
	get_program_config_from_file,
	signal_term_handler,
	get_command_line_params,
)
from modules.aprsdotfi import get_position_on_aprsfi
from modules.telegramdotcom import send_telegram_message
from modules.dapnet import send_dapnet_message
from expiringdict import ExpiringDict
import time

# Set up the global logger variable
logging.basicConfig(
	level=logging.INFO, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)


if __name__ == "__main__":

	# Get our command line parameters
	(
		mowas_configfile,
		mowas_test_configuration,
		mowas_run_interval,
		mowas_dapnet_destination_callsign,
		mowas_telegram_destination_id,
		mowas_disable_telegram,
		mowas_disable_dapnet,
		mowas_follow_the_ham,
		mowas_generate_test_message,
		mowas_warning_level,
		mowas_time_to_live
	) = get_command_line_params()

	# User wants to disable both DAPNET and Telegram? 
	if mowas_disable_dapnet and mowas_disable_telegram:
		logger.info(
			msg="User has disabled both output options (DAPNET and Telegram); exiting..."
		)
		exit(0)

	# get our configuration data from the external configuration file
	(
		success,
		mowas_aprsdotfi_api_key,
		mowas_dapnet_login_callsign,
		mowas_dapnet_login_passcode,
		mowas_watch_areas,
		mowas_telegram_bot_token,
	) = get_program_config_from_file(config_filename=mowas_configfile)
	if not success:
		logger.info(msg="Error while parsing the program config file; exiting...")
		exit(0)

	# Define some boolean hints on what is enabled and what is not
	# fmt: off
	mowas_aprsdotfi_enabled = False if mowas_aprsdotfi_api_key == "NOT_CONFIGURED" else True
	mowas_dapnet_enabled = False if mowas_dapnet_login_callsign == "NOT_CONFIGURED" else True
	mowas_telegram_enabled = False if mowas_telegram_bot_token == "NOT_CONFIGURED" else True
	# fmt: on

	# some basic checks on whether the user wants us to do the impossible :-)
	if not mowas_dapnet_enabled and not mowas_telegram_enabled:
		logger.info(msg="No target credentials (DAPNET and Telegram) configured; exiting ...")
		exit(0)

	if mowas_telegram_enabled and mowas_telegram_destination_id == 0:
		logger.info(msg="Valid Telegram destination ID is missing; exiting ...")
		exit(0)

	if mowas_dapnet_enabled and mowas_dapnet_destination_callsign == None:
		logger.info(msg="Valid DAPNET destination call sign is missing; exiting ...")
		exit(0)

	# Check if the user asks us to track a ham radio user but has not configured aprs.fi credentials
	if not mowas_aprsdotfi_enabled and mowas_follow_the_ham:
		logger.info(
			msg=f"Cannot track call sign for {mowas_follow_the_ham} - aprs.fi credentials are not configured; exiting..."
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
				msg=f"Cannot find call sign {mowas_follow_the_ham} or aprs.fi access key is misconfigured; exiting ..."
			)
			exit(0)

	#
	# We've checked all parameters - let's start with setting up our environment
	#

	# If we have just been asked to generate a test message then
	# let's do so and exit the program afterwards
	if mowas_generate_test_message:
		message = "mowas-pwd is properly configured if you were able to receive this message"
		if mowas_dapnet_enabled:
			logger.info(msg = f"Sending mowas-wbw test message to DAPNET account {mowas_dapnet_destination_callsign}")
			success = send_dapnet_message(to_callsign=mowas_dapnet_destination_callsign,message=message,message_status="Alert",dapnet_login_callsign=mowas_dapnet_login_callsign,dapnet_login_passcode=mowas_dapnet_login_passcode)
			logger.info (msg=f"DAPNET message status: {success}")
		if mowas_telegram_enabled:
			logger.info(msg = f"Sending mowas-pwb test message to Telegram account {mowas_telegram_destination_id}")
			success = send_telegram_message(bot_token=mowas_telegram_bot_token,user_id=mowas_telegram_destination_id,message=message)
			logger.info (msg=f"Telefram message status: {success}")
		exit(0)	

	# If we reach this point, then we are supposed to do some real work

	# Register the SIGTERM handler; this will allow a safe shutdown of the program
	logger.info(msg="Registering SIGTERM handler for safe shutdown...")
	signal.signal(signal.SIGTERM, signal_term_handler)

	mowas_message_cache = ExpiringDict(max_len = 1000, max_age_seconds=mowas_time_to_live) 

	while True:
		try:
			mowas_message_cache, mowas_messages_to_send = process_mowas_data(coordinates=mowas_watch_areas,mowas_cache=mowas_message_cache, minimal_mowas_severity=mowas_warning_level)
			if len(mowas_messages_to_send) > 0:
				logger.debug(msg=f"{len(mowas_messages_to_send)} new messages found")

			# Finally, go to sleep
			time.sleep(mowas_run_interval * 60)
		except (KeyboardInterrupt, SystemExit):
			logger.info(
				msg="KeyboardInterrupt or SystemExit in progress; shutting down ..."
			)
			break
