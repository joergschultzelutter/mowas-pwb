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
import argparse
import sys
import signal
from modules.mowas import process_mowas_data
from modules.utils import get_program_config_from_file, signal_term_handler

# Set up the global logger variable
logging.basicConfig(
	level=logging.INFO, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)




if __name__ == "__main__":


	parser = argparse.ArgumentParser()

	parser.add_argument(
		"--configfile",
		default="mowas-pwb.cfg",
		type=argparse.FileType("r"),
		help="Program config file name",
	)

	parser.add_argument(
		"--test_configuration",
		dest="test_configuration",
		action="store_true",
		help="Checks the program config, sends one test message to the activated channel(s) and then exits the program",
	)

	parser.add_argument(
		"--disable_dapnet",
		dest="disable_dapnet",
		action="store_true",
		help="Disables any messages to be sent out to DAPNET and disregaards the DAPNET credentials from the cfg file",
	)

	parser.add_argument(
		"--disable_telegram",
		dest="disable_telegram",
		action="store_true",
		help="Disables any messages to be sent out to Telegram and disregaards the Telegram credentials from the cfg file",
	)

	parser.add_argument(
		"--run-interval",
		dest="run_interval",
		default=30,
		type=int,
		help="Run interval (minutes)",
	)

	parser.add_argument(
		"--dapnet-destination-callsign",
		default="DF1JSL",
		dest="dapnet_destination_callsign",
		type=str,
		help="DAPNET destination call sign which will receive the messages",
	)

	parser.add_argument(
		"--telegram-destination-id",
		default=0,
		dest="telegram_destination_id",
		type=int,
		help="Telegram user ID (use bot 'UserInfoBot')",
	)

	parser.set_defaults(add_example_data=False)

	args = parser.parse_args()

	mowas_configfile = args.configfile.name
	mowas_test_configuration = args.test_configuration
	mowas_run_interval = args.run_interval
	mowas_dapnet_destination_callsign = args.dapnet_destination_callsign
	mowas_telegram_destination_id = args.telegram_destination_id
	mowas_disable_telegram = args.disable_telegram
	mowas_disable_dapnet = args.disable_dapnet

	if mowas_disable_dapnet and mowas_disable_telegram:
		logger.info(msg="User has disabled both output options; exiting...")
		exit(0)

	success, mowas_aprsdotfi_api_key, mowas_dapnet_login_callsign, mowas_dapnet_login_passcode, mowas_watch_areas = get_program_config_from_file(config_filename=mowas_configfile)
	if not success:
		logger.info(msg="Error while parsing the program config file; exiting...")
		exit(0)

	mowas_aprsdotfi_enabled = False if mowas_aprsdotfi_api_key == "NOT_CONFIGURED" else True
	mowas_dapnet_enabled = False if mowas_dapnet_login_callsign == "NOT_CONFIGURED" else True

	# Register the SIGTERM handler; this will allow a safe shutdown of the program
	logger.info(msg="Registering SIGTERM handler for safe shutdown...")
	signal.signal(signal.SIGTERM, signal_term_handler)

	try:
		pass
	except (KeyboardInterrupt, SystemExit):
		logger.info(
			msg="KeyboardInterrupt or SystemExit in progress; shutting down ..."
		)