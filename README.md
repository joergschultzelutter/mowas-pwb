# mowas-pwb

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## MOWAS Personal Warning Beacon

``mowas-pwb`` is a [MOWAS](https://de.wikipedia.org/wiki/MoWaS) Personal Warning Beacon service which sends emergency broadcasts from Germany's 'Modulares Warnsystem' to [DAPNET](https://www.hampager.de), [Telegram](https://www.telegram.org/) and email accounts. MOWAS supports various categories such as floods, earthquakes et al. You can install this program on platforms such as a Raspberry Pi and have it send you an alert in case an official warning message has been issued for your location(s).

## Feature set

- Users can specify 1..n static sets of lat/lon warning coordinates which will be matched against the MOWAS warning feeds.
- In addition, licensed amateur radio operators are capable of specifying an APRS call sign whose lat/lon coordinates will be _dynamically_ monitored in addition to the static warning coordinates. This option can be of use if you have to visit a disaster area and want to receive alerts based on your (ham radio transceiver's) _current_ position.
- Users can specify a minimal warning level which needs to be met for triggering a message (e.g. ``Severe``, ``Extreme``). ``mowas-pwb`` will only send you notifications if the warning message's status is greater or equal to the given warning level.
- Users an activate alert messages for their Telegram account, receive them via email or have them forwarded as DAPNET messages
- Users can specify a DAPNET-specific high priority message level. MOWAS ``Alert``/``Update`` messages whose warning levels meet or exceed this message level will be sent out over DAPNET with a higher priority than standard messages, thus enforcing expedited delivery.
- International users: All MOWAS warning messages are broadcasted in German which can be a hassle if you don't speak any German but want to be advised on emergencies around your area. ``mowas-pwb`` can have these messages auto-translated for you. In order to avoid misunderstandings, both the German and the translated message will be sent to you. Note: This feature is limited to Email and Telegram messages. DAPNET will not be supported unless you use "English" as the destination language.
- ``mowas-pwb`` supports two kinds of run intervals:
  - The standard run interval (default and minimal setting: 60 mins) is applied if a previous program cycle did _not_ trigger any outgoing messages to the user _or_ where the message's warning level does not meet the emergency level settings. This is the default scenario - nothing is going on, so ``mowas-pwb`` just taps the government feeds every hour for potential updates and generates ourput messages, when necessary
  - In case at least one ``Alert`` or ``Update`` message __with high priority__ has been sent out to the user, ``mowas-pwb`` assumes that there is an ongoing emergency and has a more detailed look at what might be going on. As a result, the default run interval of 60 minutes is no longer applicable and will be set to a much lower value (default and minimal setting: 15 mins), thus ensuring that you will always be up to date wrt the latest updates. If there are no _new_ messages to be sent to the user or the message severity decreases, that value will reset itself to the standard run interval at the next run cycle. ``mowas-pwb`` will keep track of the messages that have already been sent to you, thus preventing you from getting spammed with messages - see [processing logic](docs/ADDITIONAL_INFO.md)

Supported MOWAS features:

- supports all current MOWAS categories (tempest, flood, wildfire, earthquake, emergency announcements)
- All MOWAS categories can be enabled or disabled in the program's configuration file. 
- You can easily add new MOWAS categories if they are made available through the official government feeds.

## Program details

- [Installation and Configuration](docs/INSTALLATION.md)
- [Supported Command Line Parameters](docs/COMMANDS.md)
- [Additional info on processing logic, known issues et al](docs/ADDITIONAL_INFO.md)
- [Legal information](docs/LEGAL.md)

## The fine print

- APRS is a registered trademark of APRS Software and Bob Bruninga/WB4APR. Thank you Bob!
- aprs.fi services are provided by Heikki Hannikainen/OH7LZB - thank you Hessu!
