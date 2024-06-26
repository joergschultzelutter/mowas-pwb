# mowas-pwb

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) [![CodeQL](https://github.com/joergschultzelutter/mowas-pwb/actions/workflows/codeql.yml/badge.svg)](https://github.com/joergschultzelutter/mowas-pwb/actions/workflows/codeql.yml)

## MOWAS Personal Warning Beacon

_Meet [KATWARN's](https://de.wikipedia.org/wiki/Katwarn) Open Source sibling_

![Demo](docs/img/map.jpg)

``mowas-pwb`` is a [MOWAS](https://de.wikipedia.org/wiki/MoWaS) <b>P</b>ersonal <b>W</b>arning <b>B</b>eacon service which sends emergency broadcasts from Germany's 'Modulares Warnsystem' to email accounts as well as every messenger supported by [Apprise](https://github.com/caronc/apprise). You can install this program on platforms such as the Raspberry Pi and have it send you an alert in case an official warning message has been issued for your location(s).

``mowas-pwb`` has been created to complement the existing programs [KATWARN](https://de.wikipedia.org/wiki/Katwarn), [Nina](https://de.wikipedia.org/wiki/NINA_(App)) and [BIWAPP](https://de.wikipedia.org/wiki/BIWAPP) in order to enable additional communication channels such as mail, SMS/pager or messengers such as Telegram, Signal, ...

## Feature set

- Provides messaging to Email and every messenger supported by [Apprise](https://www.github.com/caronc/apprise)
- Monitors 1..n static lat/lon coordinates for [MOWAS](https://de.wikipedia.org/wiki/MoWaS) events
- Licensed ham radio amateurs can track their current [APRS](http://www.aprs.org/) position, too (_dynamic_ position monitoring)
- Users can specify a minimal warning level which needs to be met by a [MOWAS](https://de.wikipedia.org/wiki/MoWaS) event for triggering alerts.
- Emergency alerts can be sent to specific Apprise clients (e.g. DAPNET) with high priority settings.
- In case of an emergency, ``mowas-pwb`` automatically switches to shorter 'emergency' run intervals. See [processing logic](docs/ADDITIONAL_INFO.md) for further details
- Distinguishes between messenger accounts with full message length capability and SMS/pager-based accounts. In order to digest the rather talkative input from the [Bundesamt für Bevölkerungsschutz und Katastrophenhilfe](https://www.bbk.bund.de/), the user can have OpenAI or Google PaLM digest and summarize the message text.

:de: International users: ``mowas-pwb`` supports automatic translation of German [MOWAS](https://de.wikipedia.org/wiki/MoWaS) content into your native language.

## Supported MOWAS features

- Supports all current [MOWAS](https://de.wikipedia.org/wiki/MoWaS) categories (tempest, flood, wildfire, earthquake, emergency announcements)
- All [MOWAS](https://de.wikipedia.org/wiki/MoWaS) categories can be enabled or disabled in the program's configuration file
- You can easily add new [MOWAS](https://de.wikipedia.org/wiki/MoWaS) categories if they are made available through the official government feeds.

## Output examples

- [mowas-pwb Telegram message](docs/img/telegram.jpg)
- [mowas-pwb DAPNET message](docs/img/pager.jpg)
- [mowas-pwb Mail message](docs/img/mail.jpg)

Note: Apart from the two Apprise-base messenger channels, ``mowas-pwb`` provides a native email output which grants the program more precise control over the message's content. The example screenshot for a Mail message used this output module. If you use Apprise's native 'Mail' plugin, your output will look different.

## Program details

- [Installation and Configuration](docs/INSTALLATION.md)
- [Supported Command Line Parameters](docs/COMMANDS.md)
- [Additional info on processing logic, known issues et al](docs/ADDITIONAL_INFO.md)
- [Legal information](docs/LEGAL.md)

## The fine print

- [APRS](http://www.aprs.org/) is a registered trademark of APRS Software and Bob Bruninga/WB4APR. Thank you Bob!
- [aprs.fi](http://www.aprs.fi/) services are provided by Heikki Hannikainen/OH7LZB - thank you Hessu!
- [MOWAS](https://de.wikipedia.org/wiki/MoWaS) feeds are provided by the [Bundesamt für Bevölkerungsschutz und Katastrophenhilfe](https://www.bbk.bund.de/)
