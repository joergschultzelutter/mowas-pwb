# mowas-pwb
[MOWAS](https://de.wikipedia.org/wiki/MoWaS) personal warning beacon

- User can specify 1..n fixed sets of lat/lon coordinates which will be validated against MOWAS warnings.
- Additionally, licensed amateur radio operators can specify an APRS call sign whose lat/lon coordinates will also be monitored
- User can specify a minimal warning level which needs to be met for triggering a message (e.g. "Severe", "Extreme"). mowas-pwb will only send messages to the user if the message's sttatus is greater or equal to the given warning level.
- In addition to the aforementioned warning level, the user can specify a warning level threshold. Only messages whose status is greater or equal to this threshold level will be forwarded to the user's DAPNET account with high priority - all other messages will be suppressed. This is useful if you are e.g. only interested in warning messages of e.g. a disaster scope.

Supported MOWAS features: 
- supports all current MOWAS categories (tempest, flood, wildfire, earthquake, emergency announcements)
- supports alerts, updates and cancellation messages

## Command line parameters

### Optional command line parameters

- ``configfile`` Specifies the program's config file name. Default is '__mowas-pwb.cfg__'
- ``generate_test_message`` If this setting is specified, the program will start up as usual but will send only one test message to the specified recipient on DAPNET and/or Telegram. Once this data was sent to the respective APIs, the program will exit.
- ``disable-dapnet`` Disables any outgoing messages to DAPNET. Note: if you haven't configured your DAPNET access credentials, this option is automatically activated.
- ``disable-telegram`` Disables any outgoing messages to Telegram. Note: if you haven't configured your Telegram access credentials, this option is automatically activated.
- ``standard-run-interval`` This is the program's standard run interval in minutes; its minimum setting (and default value) is 60. Between each check of the MOWAS URLs, the program will sleep the specified number of minutes __unless__ at least one change has been detected which was sent to the user and the program will automatically switch to a different run interval. See ``emergency-run-interval`` for additional information.
- ``emergency-run-interval`` This is the standard run interval in minutes in case at least one new or updated emergency message has been detected (read: something has happened and we had to alert the user with a message). This parameter's minimum setting and default value is 15 (minutes) and its value is enforced to be lower than the one for __standard-run-interval__.
- ``ttl`` This numeric value defines the time-to-live for the program's decaying memory dictionary in hours. Default is 8 (hours); once a message has been present in the program's decaying memory cache for __ttl__ hours, it will be resent to the user. See the separate chapter on how the TTL logic works
- ``dapnet-destination-callsign`` Specifies the HAM radio operator's DAPNET call sign. This is the person that will receive our program's message(s). Additional SSID information can be specified but will not be honored by the program. Default is ```None```. Value has to be specified if the program is instructed to send data to DAPNET.
- ``telegram-destination-id`` This is the NUMERIC Telegram user ID. This is the person that will receive our program's message(s). You can use the Telegram bot __telegraminfobot__ for the retrieval of your numeric Telegram user ID. Value has to be specified if the program is instructed to send data to Telegram.
- ``follow-the-ham`` Nope, this will not give you the directions to the nearest restaurant (mmmh, haaaammm - yummmmmy) but allows you to track one APRS call sign with or without SSID. In addition to the program's default set of coordinates that are monitored by default, this option will look up the user's call sign on aprs.fi, retrieve its lat/lon coordinates and then monitor these coordinates, too. Useful option if you're in the field and need to be aware of any dangers and emergencies that might be related to your current position. __Please use this option responsibly and only when necessary__. It is not supposed to be used on a permanent basis. Remember: with great power comes great responsibility.
- ``warning-level``. Defines the minimal warning level that a message must have before the program recognizes it for processing. Currently, MOWS supports four warning levels (listed in ascending order of importance): __MINOR__(default setting), __MODERATE__, __SEVERE__ and __EXTREME__. If your message's warning level is below the given value for the ``warning-level`` parameter, it will be ignored - even if its coordinates match with your watch coordinates.
- ``dapnet-high-prio-level``. Similar to the ``warning-level`` parameter, you can specify a MOWAS warning threshold for MOWAS messages of the "Alert" and "Update" categories. If the MOWAS messages' warning level is greater or equal to ``dapnet-high-pro-level``, then the outgoing DAPNET message will be sent to the user with high priority. In any other case, normal priority settings will be applied. Note that MOWAS "Cancel" messages will always be sent with standard priority.

## Program config file

mowas-pwb comes with a program config file which mainly contains API keys. In order to use the program, you need to configure this file.

- ``aprsdotfi_api_key`` is the aprs.fi access key that is used if you tell the program to use the ``follow-the-ham`` option
- ``dapnet_login_callsign`` and ``dapnet_login_passcode`` are required for sending data to DAPNET
- ``mowas_watch_areas`` defines your watch areas. mowas-pwb will check these areas and if there is a match, it might forward you that warning message.
- ``telegram_bot_token`` defines the Telegram bot which will deliver potential warning messages to you.

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

mowas-pwb uses a decaying memory dictionary which will prevent message duplicates being sent to the user. The program's default life span for a messsage is 8 hours. If a MOWAS message (identified by its unique MOWAS message ID) has been sent to the user, it will enter this decaying dictionary. The same MOWAS message ID's content will be resent to the user if:

- the MOWAS message ID is already present in the dictionary but changed its status (e.g. a message's status was changed from "Alert" to "Update")
- the MOWAS message ID's is already present in the dictionary, its status in the dictionary AND in the current message is "Update" AND its update time stamp has changed. This indicates a message that was at least updated twice ("Alert" -> "Update" (1) --> "Update" (2))
- the MOWAS message ID is NOT present in the dictionary AND its status is either "Alert" or "Update". We may never either have never encountered this message yet or it was already present in our dictionary but its entry has already expired. In that case, we will simply resend the message again and re-add the MOWAS message ID to our dictionary.

### MOWAS "Cancel" message type

Similar to the "Alert" and "Update" message types, mowas-pwb will handle "Cancel" messages in the following way:

- If the MOWAS message ID is already present in the dictionary and its status has changed from "Alert"/"Update" to "Cancel", mowas-pwb will send out a cancel message to the user for one last time. The MOWAS message ID is then removed from the decaying dictionary.
- If the MOWAS message ID is NOT present in the dictionary AND its status is "Cancel", the program will ignore this message. The MOWAS interface has no official documentation and it is unknown for how long a "Cancel" message will be present in the data stream. Rather than re-sending "Cancel" messages over and over, the program will ignore these cases.

The potential side effect for this constraint is that if you start the program and there is a MOWAS "Cancel" message for your watch area(s), you will not receive a message by the program. You WOULD have received one if that area had either been in "Alert" or "Update" status, though. Anyway, as the imminent danger is over, that cancellation message will no longer be sent to the user.

## Known issues

- In order to match with a given watch area, the user's coordinates (```mowas_watch_areas``` from the program config file) have either to be inside of the polygon or intersect with that polygon.
- Currently, there is no option that enables the user to specify and additional proximity to that polygon ("Polygon plus 10km distance")
- This program uses native MOWAS data. All warning messages are in German - there does not seem to be an international message warning interface.
- Obviously, the current version of this program does not scale and cannot support multiple user's needs with just one instance.

## The fine print

- If you intend to host an instance of this program, any of the following options require you to obtain an amateur radio license:
    - Sending messages to DAPNET (requires: DAPNET access credentials)
    - Usage of the program's __follow-the-ham__ option. (requires: aprs.fi access credentials)
- It is still possible to run and host the program as a Telegram-only messaging option.
- APRS is a registered trademark of APRS Software and Bob Bruninga, WB4APR.

## Legal mumbo-jumbo

In reference to the European Union's GDPR regulations and other legal rules and regulations that I may not be aware of at this time:

- This is a hobby project. It has no commercial background whatsoever.

- If you intend to host this software and exchange data with APRS-IS, you need to be a licensed ham radio operator. You also need to provide an APRS passcode for logging on to APRS-IS. If you don't know what this is and how to get such a passcode, then don't host an an instance of this program.

- The user's position information (as well as other APRS user's position data) which is used by this program is acquired from freely accessible data sources such as aprs.fi et al. These data sources gather APRS information from ham radio users who did decide to have their position information actively submitted to the APRS network. Any of these information sources can already be used for a various user's position inquiry.

- If you intend to host your own instance of mowas-pwb, you need to provide API access keys to the following services:
    - telegram.org (if you want the program to send messages to your Telegram account)
    - DAPNET / hampager.de (if you want the program to send messages to your DAPNET account)
    - optional: aprs.fi access key.

- Don't rely on this service's availability.

If you use this program, then you agree to these terms and conditions. Thank you.
