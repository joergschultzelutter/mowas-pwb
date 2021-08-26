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

- __configfile__ Specifies the program's config file name. Default is 'mowas-pwb.cfg'
- __generate_test_message__ If this setting is specified, the program will start up as usual but will send only one test message to the specified recipient on DAPNET and/or Telegram. Once this data was sent to the respective APIs, the program will exit.
- __disable-dapnet__ Disables any outgoing messages to DAPNET. Note: if you haven't configured your DAPNET access credentials, this option is automatically activated.
- __disable-telegram__ Disables any outgoing messages to Telegram. Note: if you haven't configured your Telegram access credentials, this option is automatically activated.
- __standard-run-interval__ This is the program's standard run interval in minutes; its minimum setting (and default value) is 60. Between each check of the MOWAS URLs, the program will sleep the specified number of minutes __unless__ at least one change has been detected which was sent to the user and the program will automatically switch to a different run interval. See __emergency-run-interval__ for additional information.
- __emergency-run-interval__ This is the standard run interval in minutes in case at least one new or updated emergency message has been detected (read: something has happened and we had to alert the user with a message). This parameter's minimum setting and default value is 15 (minutes) and its value is enforced to be lower than the one for __standard-run-interval__.
- __ttl__ This numeric value defines the time-to-live for the program's decaying memory dictionary in hours. Default is 8 (hours); once a message has been present in the program's decaying memory cache for __ttl__ hours, it will be resent to the user. See the separate chapter on how the TTL logic works
- __dapnet-destination-callsign__ Specifies the HAM radio operator's DAPNET call sign. This is the person that will receive our program's message(s). Additional SSID information can be specified but will not be honored by the program. Default is ```None```. Value has to be specified if the program is instructed to send data to DAPNET.
- __telegram-destination-id__ This is the NUMERIC Telegram user ID. This is the person that will receive our program's message(s). You can use the Telegram bot ```telegraminfobot``` for the retrieval of your numeric Telegram user ID. Value has to be specified if the program is instructed to send data to Telegram.
- __follow-the-ham__ Nope, this will not give you the directions to the nearest restaurant (mmmh, haaaam - yummmmmy) but allows you to track one APRS call sign with or without SSID. In addition to the program's default set of coordinates that are monitored by default, this option will look up the user's call sign on aprs.fi, retrieve its lat/lon coordinates and then monitor these coordinates, too. Useful option if you're in the field and need to be aware of any dangers and emergencies that might be related to your current position. __Please use this option responsibly and only when necessary__. It is not supposed to be used on a permanent basis. Remember: with great power comes great responsibility.
- __warning-level__. Defines the minimal warning level that a message must have before the program recognizes it for processing. Currently, MOWS supports four warning levels (listed in ascending order of importance): ```MINOR```(default setting), ```MODERATE```, ```SEVERE``` and ```EXTREME```. If your message's warning level is below the given value for the __warning-level__ parameter, it will be ignored - even if its coordinates match with your watch coordinates.
- __dapnet-high-prio-level__. Similar to the __warning-level__ parameter, you can specify a MOWAS warning threshold for MOWAS messages of the "Alert" and "Update" categories. If the MOWAS messages' warning level is greater or equal to __dapnet-high-pro-level__, then the outgoing DAPNET message will be sent to the user with high priority. In any other case, normal priority settings will be applied. Note that MOWAS "Cancel" messages will always be sent with standard priority.


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


- If you intend to host your own instance of MPAD, you need to provide API access keys to the following services:
    - telegram.org (if you want the program to send messages to your Telegram account)
    - DAPNET / hampager.de (if you want the program to send messages to your DAPNET account)
    - optional: aprs.fi access key.

- Don't rely on this service's availability.

If you use this program, then you agree to these terms and conditions. Thank you.
