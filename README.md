# mowas-pwb

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## MOWAS Personal Warning Beacon

_Meet [KATWARN's](https://de.wikipedia.org/wiki/Katwarn) Open Source Cousin_.

![Demo](docs/img/map.jpg)

``mowas-pwb`` is a [MOWAS](https://de.wikipedia.org/wiki/MoWaS) Personal Warning Beacon service which sends emergency broadcasts from Germany's 'Modulares Warnsystem' to [DAPNET](https://www.hampager.de), [Telegram](https://www.telegram.org/) and email accounts. You can install this program on platforms such as the Raspberry Pi and have it send you an alert in case an official warning message has been issued for your location(s).

## Output examples

- [mowas-pwb Telegram message](docs/img/telegram.jpg)
- [mowas-pwb Mail message](docs/img/mail.jpg)

## Feature set

- Supports messaging to Telegram, Email and DAPNET accounts
- Monitors 1..n static lat/lon coordinates for MOWAS events
- Licensed ham Radio amateurs can track their current APRS position, too (_dynamic_ coordinates monitoring)
- Users can specify a minimal warning level which needs to be met by a MOWAS event for triggering alerts.
- Emergency alerts can be sent to DAPNET users with high priority settings.
- In case of an emergency, ``mowas-pwb`` automatically switches to shorter 'emergency' run intervals. See [processing logic](docs/ADDITIONAL_INFO.md) for further details

International users: ``mowas-pwb`` supports auto-translation of the German MOWAS content to your native language

## Supported MOWAS features

- Supports all current MOWAS categories (tempest, flood, wildfire, earthquake, emergency announcements)
- All MOWAS categories can be enabled or disabled in the program's configuration file
- You can easily add new MOWAS categories if they are made available through the official government feeds.

## Program details

- [Installation and Configuration](docs/INSTALLATION.md)
- [Supported Command Line Parameters](docs/COMMANDS.md)
- [Additional info on processing logic, known issues et al](docs/ADDITIONAL_INFO.md)
- [Legal information](docs/LEGAL.md)

## The fine print

- APRS is a registered trademark of APRS Software and Bob Bruninga/WB4APR. Thank you Bob!
- aprs.fi services are provided by Heikki Hannikainen/OH7LZB - thank you Hessu!
- MOWAS feeds are provided by the [Bundesamt für Bevölkerungsschutz und Katastrophenhilfe](https://www.bbk.bund.de/)
