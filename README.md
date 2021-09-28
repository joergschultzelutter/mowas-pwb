# mowas-pwb
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## MOWAS Personal Warning Beacon
``mowas-pwb`` is a [MOWAS](https://de.wikipedia.org/wiki/MoWaS) Personal Warning Beacon service which sends emergency broadcasts from Germany's 'Modulares Warnsystem' to [DAPNET](https://www.hampager.de), [Telegram](https://www.telegram.org/) and email accounts. MOWAS supports various categories such as floods, earthquakes et al. You can install this program on platforms such as a Raspberry Pi and have it send you an alert in case an official warning message has been issued for your location(s).

## Feature set
- You can specify 1..n fixed sets of lat/lon warning areas which will be validated against MOWAS warnings.
- Additionally, licensed amateur radio operators are capable of specifying an APRS call sign whose lat/lon coordinates will be _dynamically_ monitored in addition to the static warning areas.
- You can specify a minimal warning level which needs to be met for triggering a message (e.g. ``Severe``, ``Extreme``). ``mowas-pwb`` will only send messages to the your devices if the message's status is greater or equal to the given warning level. 
- Additionally, you can specify a DAPNET-specific high priority message level. ``Alert``/``Update`` Messages whose warning levels meet or exceed this value will be sent out over DAPNET with a higher priority than standard messages.
- ``mowas-pwb`` supports two kinds of run intervals:
    - The standard run interval (default: 60 mins) is applied if a previous program cycle did not trigger any outgoing messages to the user or where the message's warning level does not meet the emergency level settings. This should be the default scenario. 
    - In case at least one ``Alert`` or ``Update`` message has been sent out to the user, ``mowas-pwb`` assumes that there is an ongoing emergency. The run interval will be set to a much lower value (default: 15 mins), thus ensuring that you will always be informed on the latest updates. If there are no new messages to be sent to the user or the message severity decreases, that value will reset itself to the standard run interval at the next run cycle.

Supported MOWAS features: 
- supports all current MOWAS categories (tempest, flood, wildfire, earthquake, emergency announcements)
- MOWAS categories can be enabled or disabled. You can also add new MOWAS categories if they are made avaiable through the official government feeds.
- supports alerts, updates and cancellation messages

## Program details
- [Installation and Configuration](docs/INSTALLATION.md)
- [Supported Command Line Parameters](docs/COMMANDS.md)
- [Additional info on processing logic, known issues et al](docs/ADDITIONAL_INFO.md)
- [Legal information](docs/LEGAL.md)

## The fine print

- APRS is a registered trademark of APRS Software and Bob Bruninga, WB4APR. Thank you Bob!
- aprs.fi services are provided by Heikki Hannikainen/OH7LZB - thank you Hessu!
