#
# MOWAS Personal Warning Beacon
# Module: Reads all Warncells from the Deutscher Wetterdienst site
#         and returns them as a dictionary
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
import csv
import requests
import io
import logging

# Set up the global logger variable
logging.basicConfig(
	level=logging.INFO, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)

def read_warncell_info(url: str = "https://www.dwd.de/DE/leistungen/opendata/help/warnungen/cap_warncellids_csv.csv?__blob=publicationFile&v=3"):
	request_headers = {"User-Agent": "Mozilla"}

	# This is our target directory
	warncell_data = {}

	warncell_data_string = None

	# Download the Warncell data from the web site and retain the string if successful
	try:
		resp = requests.get(url=url,headers=request_headers)
	except:
		resp = None
	if resp:
		if resp.status_code == 200:
				warncell_data_string = resp.text
	
	# Do we have some data? Then let's try to process it
	if warncell_data_string:
		# We use custom field names as the original ones do contain Unicode
		# characters which will make it difficult for us to access the fields
		fieldnames=["warncellid","fullname","nuts_kennung","shortname","sign_kennung"]

		# Parse the content
		csvReader = csv.DictReader(io.StringIO(warncell_data_string),dialect="excel", delimiter=";",fieldnames=fieldnames)

		for elem in csvReader:
			warncellid = elem["warncellid"]
			full_name = elem["fullname"]
			short_name = elem["shortname"]
			val = {"full_name": full_name, "short_name": short_name}
			warncell_data[warncellid] = val

	return warncell_data	

if __name__ == "__main__":
	logger.info(read_warncell_info())
