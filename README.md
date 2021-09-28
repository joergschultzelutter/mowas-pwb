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

## Program details
- [Installation and Configuration](docs/INSTALLATION.md)
- [Supported Command Line Parameters](docs/COMMANDS.md)
- [Additional info on processing logic, known issues et al](docs/ADDITIONAL_INFO.md)

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
