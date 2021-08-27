# mowas-pwb
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## MOWAS Personal Warning Beacon
``mowas-pwb`` is a [MOWAS](https://de.wikipedia.org/wiki/MoWaS) Personal Warning Beacon service which sends emergency broadcasts from Germany's 'Modulares Warnsystem' to [DAPNET](https://www.hampager.de) and [Telegram](https://www.telegram.org/) accounts. MOWAS supports various categories such as floods, earthquakes et al. You can install this program on platforms such as a Raspberry Pi.

## Feature set
- You can specify 1..n fixed sets of lat/lon warning areas which will be validated against MOWAS warnings.
- Additionally, licensed amateur radio operators can specify an APRS call sign whose lat/lon coordinates will be _dynamically_ monitored in addition to the static warning areas
- You can specify a minimal warning level which needs to be met for triggering a message (e.g. "Severe", "Extreme"). ``mowas-pwb`` will only send messages to the your devices if the message's sttatus is greater or equal to the given warning level.
- In addition to the aforementioned warning level, you can specify a warning level threshold. Only messages whose status is greater or equal to this threshold level will be forwarded to the user's DAPNET account with high priority - all other messages will be suppressed. This is useful if you are e.g. only interested in warning messages of e.g. a disaster scope.
- ``mowas-pwb`` supports two kinds of run intervals:
    - The standard run interval (default: 60 mins) is applied if a previous program cycle did NOT trigger any outgoing messages to the user. This should be the default scenario. 
    - In case at least one Alert or Update message has been sent out to the user, ``mowas-pwb`` assumes that there is an ongoing emergency. The run interval will be set to a lower value (default: 15 mins). If there are no new messages to be sent to the user, that value will reset itself to the standard run interval at the next run cycle.

Supported MOWAS features: 
- supports all current MOWAS categories (tempest, flood, wildfire, earthquake, emergency announcements)
- supports alerts, updates and cancellation messages

## Installation
- DAPNET and/or Telegrams access credentials are required.
- For APRS tracking, a valid aprs.fi access key is required
- Download the repo
- Install the PIP packages:
    - ``expiringdict``
    - ``numpy``
    - ``python-telegram-bot``
    - ``requests``
    - ``shapely``
    - ``unidecode``
- Create a copy of the ``mowas-pwb.cfg.TEMPLATE`` file and rename it to ``mowas-pwb.cfg``. Then amend its entries.
    - DAPNET: Specify user and password for the account that will have to send the message to the user via DAPNET API
    - Telegram: Specify the sender bot's access token
    - If you want to use the ``follow-the-ham`` program option, populate the program's aprs.fi access key
    - Ultimately, you need to specify the coordinates that you want to monitor. Each coordinate tuple is separated by a 'space' character. There is no limit in how many points you can specify.
    - A configuration entry of ``mowas_watch_areas = 51.838879,8.32678 51.829722,9.448333`` would result in two coordinates that are going to be monitored independently from each other:
        - C1: ``lat = 51.838879``, ``lon = 8.32678``
        - C2: ``lat = 51.829722``, ``lon = 9.448333``
 - Finally, run the program. Specify a DAPNET ham radio call sign and/or a numeric Telegram user ID as targets. For your first run, I recommend using the ``generate_test_message`` program option - this will simply trigger a test message to DAPNET/Telegram, thus allowing you to tell whether your program configuration is ok.

## Command line parameters

### Optional command line parameters with defaults

- ``configfile`` Specifies the program's config file name. Default is '__mowas-pwb.cfg__'
- ``generate_test_message`` If this setting is specified, the program will start up as usual but will send only one test message to the specified recipient on DAPNET and/or Telegram. Once this data was sent to the respective APIs, the program will exit.
- ``disable-dapnet`` Disables any outgoing messages to DAPNET. Note: if you haven't configured your DAPNET access credentials, this option is automatically activated.
- ``disable-telegram`` Disables any outgoing messages to Telegram. Note: if you haven't configured your Telegram access credentials, this option is automatically activated.
- ``standard-run-interval`` This is the program's standard run interval in minutes; its minimum setting (and default value) is 60. Between each check of the MOWAS URLs, the program will sleep the specified number of minutes __unless__ at least one change has been detected which was sent to the user and the program will automatically switch to a different run interval. See ``emergency-run-interval`` for additional information.
- ``emergency-run-interval`` This is the standard run interval in minutes in case at least one new or updated emergency message has been detected (read: something has happened and we had to alert the user with a message). This parameter's minimum setting and default value is 15 (minutes) and its value is enforced to be lower than the one for __standard-run-interval__.
- ``ttl`` This numeric value defines the time-to-live for the program's decaying memory dictionary in hours. Default is 8 (hours); once a message has been present in the program's decaying memory cache for __ttl__ hours, it will be resent to the user. See the separate chapter on how the TTL logic works
- ``follow-the-ham`` This will _not_ give you the directions to the nearest restaurant (mmmh, :meat_on_bone: - yummy) but allows you to track one APRS call sign with or without SSID. In addition to the program's default set of coordinates that are monitored by default, this option will look up the user's call sign on aprs.fi, retrieve its lat/lon coordinates and then monitor these coordinates, too. This is a useful option if you're in a disaster area along with your APRS-capable HT and need to be aware of any dangers and emergencies that might be related to your current position. __Please use this option responsibly and only when necessary__. It is __not__ supposed to be used on a permanent basis. Remember: with great power comes great responsibility.
- ``warning-level``. Defines the minimal warning level that a message must have before the program recognizes it for processing. Currently, MOWAS supports four warning levels (listed in ascending order of importance): __MINOR__ (default setting), __MODERATE__, __SEVERE__ and __EXTREME__. If your message's warning level is below the given value for the ``warning-level`` parameter, it will be ignored - even if its coordinates match with your watch coordinates.
- ``dapnet-high-prio-level``. Similar to the ``warning-level`` parameter, you can specify a MOWAS warning threshold for MOWAS messages of the "Alert" and "Update" categories. If the MOWAS messages' warning level is greater or equal to ``dapnet-high-pro-level``, then the outgoing DAPNET message will be sent to the user with high priority. In any other case, normal priority settings will be applied. Note that MOWAS "Cancel" messages will always be sent with standard priority.

If you have specified the ``follow-the-ham`` parameter AND aprs.fi's access key is configured, the program will initiate one request to aprs.fi during its startup process. This will allow you to detect if the call sign does exist on aprs.fi and if the aprs.fi access key is configured in a proper way. If this check is not passed successfully, the program startup will abort. Any _further_ errors in retrieving that call sign's position data will _not_ cause an error, though. The program will simply continue to monitor the watch area that was provided to it through its program config file; the call sign's availability on aprs.fi simply might have expired.

### Mandatory command line parameters
- ``dapnet-destination-callsign`` Specifies the HAM radio operator's DAPNET call sign. This is the person that will receive our program's message(s). Additional SSID information can be specified but will not be honored by the program. This value has to be specified if the program is instructed to send data to DAPNET.
- ``telegram-destination-id`` This is the NUMERIC Telegram user ID. This is the person that will receive our program's message(s). You can use the Telegram bot ``userinfobot`` for the retrieval of your numeric Telegram user ID. This value has to be specified if the program is instructed to send data to Telegram.

At least one output option (DAPNET _or_ Telegram) needs to be configured in the program's config file and also provided via command line parameters - otherwise, the program will exit with an error message during startup.

## Program config file

``mowas-pwb`` comes with a program config file which mainly contains API keys. In order to use the program, you need to configure this file.

- ``aprsdotfi_api_key`` is the aprs.fi access key that is used if you tell the program to use the ``follow-the-ham`` option
- ``dapnet_login_callsign`` and ``dapnet_login_passcode`` are required for sending data to DAPNET
- ``mowas_watch_areas`` defines your watch areas. ``mowas-pwb`` will check these areas and if there is a match, it might forward you that warning message.
- ``telegram_bot_token`` defines the Telegram bot which will deliver potential warning messages to you.

A variable with the value of 
```python 
NOT_CONFIGURED
``` 
will automatically disable the program option that is associated with this value

```python
[mowas_config]

# API key for www.aprs.fi access
# API key "NOT_CONFIGURED" disable aprs.fi access
aprsdotfi_api_key = NOT_CONFIGURED

# DAPNET access credentials
# Callsign "NOT_CONFIGURED" disables DAPNET access
dapnet_login_callsign = NOT_CONFIGURED
dapnet_login_passcode = -1

# Lat / Lon coordinates that we intend to monitor
# Format: lat1,lon1<space>lat2,lon2<space>.....latn,lonn
# Example: 51.838879,8.32678 51.829722,9.448333
mowas_watch_areas = 51.8127,8.32678 51.829722,9.448333 48.4794,10.771

# Telegram bot token - this is the bot that will send out the message
# "NOT_CONFIGURED" disables Telegram access
telegram_bot_token = NOT_CONFIGURED
```

## TTL and processing logic

### MOWAS "Alert" and "Update" message types

``mowas-pwb`` uses a decaying memory dictionary which will prevent message duplicates being sent to the user. The program's default life span for a messsage is 8 hours. If a MOWAS message (identified by its unique MOWAS message ID) has been sent to the user, it will enter this decaying dictionary. The same MOWAS message ID's content will be resent to the user if:

- the MOWAS message ID is already present in the dictionary but changed its status (e.g. a message's status was changed from "Alert" to "Update")
- the MOWAS message ID's is already present in the dictionary, its status in the dictionary AND in the current message is "Update" AND its update time stamp has changed. This indicates a message that was at least updated twice ("Alert" -> "Update" (1) --> "Update" (2))
- the MOWAS message ID is NOT present in the dictionary AND its status is either "Alert" or "Update". We may never either have never encountered this message yet or it was already present in our dictionary but its entry has already expired. In that case, we will simply resend the message again and re-add the MOWAS message ID to our dictionary.

If at least one "Alert" or "Update" message has been detected during a program cycle __which was deemed to be forwarded to the user__, ``mowas-pwb`` will assume that there is an incident going on. The sleep interval will change from 60 to 15 mins (default settings), thus allowing the program to stay up to date with any ongoing changes.

### MOWAS "Cancel" message type

Similar to the "Alert" and "Update" message types, ``mowas-pwb`` will handle "Cancel" messages in the following way:

- If the MOWAS message ID is already present in the dictionary and its status has changed from "Alert"/"Update" to "Cancel", ``mowas-pwb`` will send out a cancel message to the user for one last time. The MOWAS message ID is then removed from the decaying dictionary.
- If the MOWAS message ID is NOT present in the dictionary AND its status is "Cancel", the program will ignore this message. The MOWAS interface has no official documentation and it is unknown for how long a "Cancel" message will be present in the data stream. Rather than re-sending "Cancel" messages over and over, the program will ignore these cases.

The potential side effect for this constraint is that if you start the program and there is a MOWAS "Cancel" message for your watch area(s), you will not receive a message by the program. You WOULD have received one if that area had either been in "Alert" or "Update" status, though. Anyway, as the imminent danger is over, that cancellation message will no longer be sent to the user.

## Known issues

- In order to match with a given watch area, the user's coordinates (```mowas_watch_areas``` from the program config file) have either to be inside of the polygon or intersect with that polygon.
- Currently, there is no option that enables the user to specify and additional proximity to that polygon ("Polygon plus 10km distance")
- This program uses native MOWAS data. All warning messages are in German - there does not seem to be an international message warning interface.
- Obviously, the current version of this program does not scale and cannot support multiple user's needs with just one instance.
- Sometimes, the warncell info provided by MOWAS cannot be found in the official warncell registry. If that is the case, the (usually longer) descriptive area text from the original MOWAS message is used instead.
- If you want to use this program for a different country's warning system:
    - remove the call for retrieving the 'warncell' information
    - replace the MOWAS module with your country's native warn system parser code

## The fine print

- APRS is a registered trademark of APRS Software and Bob Bruninga, WB4APR. Thank you Bob!
- aprs.fi services are provided by Heikki Hannikainen/OH7LZB - thank you Hessu!

## Legal mumbo-jumbo

In reference to the European Union's GDPR regulations and other legal rules and regulations that I may not be aware of at this time:

- This is a hobby project. It has no commercial background whatsoever.

- Both DAPNET messaging option or the ``follow-the-ham`` tracking option require you to be a licensed ham radio operator. If you run this program in Telegram-only mode, no ham radio license is required, though.

- The user's position information (as well as other APRS user's position data) which is used by this program is acquired from freely accessible data sources such as aprs.fi et al. These data sources gather APRS information from ham radio users who did decide to have their position information actively submitted to the APRS network. Any of these information sources can already be used for a various user's position inquiry.

- If you intend to host your own instance of ``mowas-pwb``, you need to provide API access keys to the following services:
    - telegram.org
    - DAPNET / hampager.de. Requires ham radio license.
    - optional: aprs.fi access key. Requires ham radio license.

- Don't rely on this service's availability. When in doubt, always consult other means of communication such as radio / TV broadcasts or cell broadcast messages (once the latter are finally available in Germany - hey, it's only been 20 years since this technology has been invented; don't rush)

If you use this program, then you agree to these terms and conditions. Thank you.
