# mowas-pwb
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## MOWAS Personal Warning Beacon
``mowas-pwb`` is a [MOWAS](https://de.wikipedia.org/wiki/MoWaS) Personal Warning Beacon service which sends emergency broadcasts from Germany's 'Modulares Warnsystem' to [DAPNET](https://www.hampager.de), [Telegram](https://www.telegram.org/) and email accounts. MOWAS supports various categories such as floods, earthquakes et al. You can install this program on platforms such as a Raspberry Pi and have it send you an alert in case an official warning message has been issued for your location(s).

## Feature set
- You can specify 1..n fixed sets of lat/lon warning areas which will be validated against MOWAS warnings.
- Additionally, licensed amateur radio operators can specify an APRS call sign whose lat/lon coordinates will be _dynamically_ monitored in addition to the static warning areas
- You can specify a minimal warning level which needs to be met for triggering a message (e.g. ``Severe``, ``Extreme``). ``mowas-pwb`` will only send messages to the your devices if the message's status is greater or equal to the given warning level. 
- Additionally, you can specify a DAPNET-specific high priority message level. Alert/Update Messages whose warung levels meet or exceed this value will be sent out over DAPNET with a higher priority than standard messages.
- ``mowas-pwb`` supports two kinds of run intervals:
    - The standard run interval (default: 60 mins) is applied if a previous program cycle did NOT trigger any outgoing messages to the user. This should be the default scenario. 
    - In case at least one Alert or Update message has been sent out to the user, ``mowas-pwb`` assumes that there is an ongoing emergency. The run interval will be set to a lower value (default: 15 mins). If there are no new messages to be sent to the user, that value will reset itself to the standard run interval at the next run cycle.

Supported MOWAS features: 
- supports all current MOWAS categories (tempest, flood, wildfire, earthquake, emergency announcements)
- supports alerts, updates and cancellation messages

## Installation
- DAPNET, Telegram and/or email account  access credentials are required.
- For APRS tracking (``follow-the-ham`` option), a valid aprs.fi access key is required
- Download the repo
- Install the PIP packages along with their dependencies:
    - ``expiringdict``
    - ``numpy``
    - ``python-telegram-bot``
    - ``requests``
    - ``shapely``
    - ``unidecode``
- Create a copy of the ``mowas-pwb.cfg.TEMPLATE`` file and rename it to ``mowas-pwb.cfg``. Then amend its entries.
    - DAPNET: Specify user and password for the account that will have to send the message to the user via DAPNET API
    - Telegram: Specify the sender bot's access token (via ``The Botfather`` bot)
    - Email: specify user/password
    - If you want to use the ``follow-the-ham`` program option, populate the program's aprs.fi access key
    - Ultimately, you need to specify the coordinates that you want to monitor. Each coordinate tuple is separated by a 'space' character. There is no limit in how many points you can specify.
    - A configuration entry of ``mowas_watch_areas = 51.838879,8.32678 51.829722,9.448333`` would result in two coordinates that are going to be monitored independently from each other:
        - C1: ``lat = 51.838879``, ``lon = 8.32678``
        - C2: ``lat = 51.829722``, ``lon = 9.448333``
    - Specify which categories ``mowas-pwb`` is supposed to monitor. Valid values: ``TEMPEST``,``FLOOD``,``FLOOD_OLD``,``WILDFIRE``,``EARTHQUAKE``,``DISASTER``. Default = all categories; at least one category needs to be specified.
 - Finally, run the program. Specify a DAPNET ham radio call sign and/or a numeric Telegram user ID as targets. For your first run, I recommend using the ``generate_test_message`` program option - this will simply trigger a test message to DAPNET/Telegram, thus allowing you to tell whether your program configuration is ok.

## Command line parameters

The following section describes the command line parameters which can be used to influence the program's behavior. In addition to these parameters, settings such as the watch area(s) are configured in the program's config file - see separate section.

### Optional command line parameters

- ``configfile`` Specifies the program's config file name. Default is '__mowas-pwb.cfg__'
- ``generate_test_message`` Default value is ``False``. If you set this value to ``True``, the program will start up as usual but will send only _one_ test message to the specified recipient on DAPNET and/or Telegram. Once this data was sent to the respective APIs, the program will exit.
- ``disable-dapnet`` Default value is ``False``. Set this value to ``True`` if you want to disable all outgoing messages to DAPNET. Note: if you haven't configured your DAPNET access credentials, this option's value is automatically set to ``True``.
- ``disable-telegram`` Default value is ``False``. Set this value to ``True`` if you want to disable all outgoing messages to Telegram. Note: if you haven't configured your Telegram access credentials, this option's value is automatically set to ``True``.
- ``standard-run-interval`` This is the program's standard run interval in minutes; its minimum setting (and default value) is ``60``. Between each check of the MOWAS URLs, the program will sleep the specified number of minutes __unless__ at least one change has been detected which was sent to the user and the program will automatically switch to a different run interval. See ``emergency-run-interval`` for additional information.
- ``emergency-run-interval`` This is the standard run interval in minutes in case at least one __new__ or __updated__ emergency message has been detected (read: something has happened and we had to alert the user with a message). This parameter's minimum setting and default value is 15 (minutes) and its value is enforced to be lower than the one for __standard-run-interval__. 
- ``ttl`` This numeric value defines the time-to-live for the program's decaying memory dictionary in hours. Default is ``8`` (hours); once a message has been present in the program's decaying memory cache for __ttl__ hours, it will be resent to the user. See the separate chapter on how the TTL logic works.
- ``follow-the-ham`` This will _not_ provide you with the directions to the nearest restaurant :meat_on_bone: but enables you to track one APRS call sign's position. In addition to the program's default set of (static) coordinates which are monitored by default, this option will look up the user's call sign on aprs.fi, retrieve its lat/lon coordinates and then monitor these dynamic coordinates, too. This is a useful option if you're in a disaster area along with your APRS-capable HT and need to be aware of any dangers and emergencies that might be related to your current position. __Please use this option responsibly and only when necessary__. This program option is __not__ supposed to be used on a permanent basis. Remember: with great power comes great responsibility. This program option has no default setting, meaning that unless you specify a call sign, only the static coordinates from the program's config file will be monitored.
- ``warning-level``. Defines the minimal warning level that a message must have before the program considers it for processing. Currently, MOWAS supports four warning levels (listed in ascending order of importance): ``MINOR`` (default setting), ``MODERATE``, ``SEVERE`` and ``EXTREME``. If your message's warning level is below the given value for the ``warning-level`` parameter, it will be ignored - even if its coordinates match with your watch coordinates. 
- ``dapnet-high-prio-level``. Similar to the ``warning-level`` parameter, you can specify a MOWAS warning threshold for MOWAS messages of the "Alert" and "Update" categories. If the MOWAS messages' warning level is greater or equal to ``dapnet-high-pro-level``, then the outgoing DAPNET message will be sent to the user with high priority. In any other case, normal priority settings will be applied. Note that MOWAS "Cancel" messages will always be sent with standard priority. Default value for this option is ``SEVERE``.
- ``enable-covid-content``. By default, ``mowas-pwb`` __suppresses__ Covid related alerts. Due to the sheer amount of Covid related messages issued by the German government on a daily basis, I've added this constraint which simply omits all messages containing the terms ``covid`` or ``corona``. If you still want to receive these messages, you can set this option. 

If you have specified the ``follow-the-ham`` parameter AND aprs.fi's access key is configured,``mowas-pwb`` will initiate one request to aprs.fi during its startup process. This pre-check allows it to detect if the call sign does exist on aprs.fi and if the aprs.fi API access key is configured in a proper way. If that check is not passed successfully, the program startup will abort. Any _further_ errors in retrieving that call sign's position data during its processing cycles will _not_ cause a program error, though. ``mowas-pwb`` will simply continue to monitor the static watch areas which were specified in the program config file; the call sign's availability on aprs.fi simply might have expired.

### Mandatory command line parameters
- ``dapnet-destination-callsign`` Specifies the HAM radio operator's DAPNET call sign of the person that will receive our program's message(s). Additional SSID information can be specified but will not be honored by the program (DAPNET call signs have no SSIDs). This value has to be specified if the program is instructed to send data to DAPNET.
- ``telegram-destination-id`` This is the __numeric__ Telegram user ID of the person that will receive our program's message(s). You can use the Telegram bot ``userinfobot`` in order to figure out what your numeric Telegram user ID is. 

At least __one__ output option (DAPNET _or_ Telegram) needs to be configured in the program's config file and also provided via command line parameters - otherwise, the program will exit with an error message during startup.

## Program config file

``mowas-pwb`` comes with a program config file which mainly contains API keys. In order to use the program, you need to configure this file.

- ``aprsdotfi_api_key`` is the aprs.fi access key that is used if you tell the program to use the ``follow-the-ham`` option
- ``dapnet_login_callsign`` and ``dapnet_login_passcode`` are required for sending data to DAPNET
- ``mowas_watch_areas`` defines your watch areas. ``mowas-pwb`` will check these areas and if there is a match, it might forward you that warning message.
- ``telegram_bot_token`` defines the Telegram bot which will deliver potential warning messages to you.
- ``smtpimap_email_address`` and ``smtpimap_email_password`` are required for sending data from this email account to the user
- ``mowas_active_categories`` defines the number of MOWAS categories which will be monitored by ``mowas-pwb``. By default, this setting contains all available MOWAS categories.

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

# SMTP  / IMAP shared Credentials
# Providers like GMail require you to set an app-specific password
# (see https://myaccount.google.com/apppasswords)
# "NOT_CONFIGURED" disables the email account
smtpimap_email_address = NOT_CONFIGURED
smtpimap_email_password = NOT_CONFIGURED

# MOWAS categories to be monitored. These identifiers describe
# the MOWAS URLs from which this program is going to download
# data from and then tries to match the given watch coordinates 
# against potential warning messages. By default, all available
# MOWAS categories are about to be monitored. Please separate
# the categories with a comma. At least one (valid) category
# needs to be present.
# Valid values: TEMPEST, FLOOD, FLOOD_OLD (currently no longer
# in use by MOWAS), WILDFIRE, EARTHQUAKE, DISASTERS
mowas_active_categories = TEMPEST,FLOOD,FLOOD_OLD,WILDFIRE,EARTHQUAKE,DISASTERS
```

## TTL and general processing logic

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
- Obviously, the current version of this program does not scale and cannot support multiple user's needs with just one program instance.
- As the MOWAS APIs are not officially available to end users, government authorities might either terminate the services without notice and / or change the format settings of the services that are currently exposed (but not officially available to end users)
- Although all MOWAS messages do contain warncell references (which allows the program's DAPNET part to use the region's abbreviated region description), certain messages do contain invalid warncell identifiers. If such an case is encountered, MOWAS will use the (lenghty) original regional description instead. For DAPNET messages, the program will try to shorten that description by remmoving some clutter from that message.
- If you want to use this program for a different country's warning system:
    - remove the call for retrieving the 'warncell' information - this one is only relevant to German users
    - replace the MOWAS module with your country's native warn system parser code
    - change the DAPNET message group setting from ``dl-all`` (Germany) to your locale's transponder group.
- There is no message dupe check; if the same message is present in more than one MOWAS category and ``mowas-pwb`` deemed this message to be valid for your coordinates and program parameters' selection, you may receive that message more than once.
- You may want to set up you Telegram bot as a private bot. Good instructions on how to do this can be found here: [https://sarafian.github.io/low-code/2020/03/24/create-private-telegram-chatbot.html](https://sarafian.github.io/low-code/2020/03/24/create-private-telegram-chatbot.html)

## The fine print

- APRS is a registered trademark of APRS Software and Bob Bruninga, WB4APR. Thank you Bob!
- aprs.fi services are provided by Heikki Hannikainen/OH7LZB - thank you Hessu!

## Legal mumbo-jumbo

In reference to the European Union's GDPR regulations and other legal rules and regulations that I may not be aware of at this time:

- This is a hobby project. It has no commercial background whatsoever.

- Although official government warning message feeds are consumed by this program, ``mowas-pwb`` itself is not an official Government warning app. __If it breaks, you get to keep both pieces.__ Even though its purpose is to alert you during hazardous situations, don't rely on ``mowas-pwb``'s availability and content validity during a life-and-death situation. When in doubt, always consult additional sources of information such as TV, radio broadcasts and the Internet.

- Both DAPNET messaging option or the ``follow-the-ham`` aprs.fi tracking option __require you to be a licensed ham radio operator__. If you run this program in Telegram-or-Email-only mode, no ham radio license is required, though.

- In case the ``follow-the-ham`` option is used: The user's position information (as well as other APRS user's position data) which is used by this program is acquired from freely accessible data sources such as aprs.fi et al. These data sources gather APRS information from ham radio users who did decide to have their position information actively submitted to the APRS network. Any of these information sources can already be used for a various user's position inquiry.

- If you intend to host your own instance of ``mowas-pwb``, you need to provide API access keys to the following services:
    - sender's email and password and/or
    - telegram.org and/or
    - DAPNET / hampager.de. __Requires a valid ham radio license.__
    - optional: aprs.fi access key. __Requires a valid ham radio license.__

If you use this program, then you agree to these terms and conditions. Thank you.
