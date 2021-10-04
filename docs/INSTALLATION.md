# Installation
## General instructions
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
    - Telegram: 
        - Specify the sender bot's access token (via ``The Botfather`` bot).
        - Note that in order to permit the new bot to send data to your destination account, you __must__ first initiate a one-time chat between your Telegram target account and that bot - or the program will not be able to send messages to that account. 
            - Just select the bot of yours in Telegram, click the __Start__ button and you're good to go. This is a Telegram security setting which ```mowas-pwb``` cannot bypass. 
            - If you don't establish the initial connection or stop the bot, sending messages to Telegram will fail and these failures will be noted in the program's log file.
    - Email: specify user/password
    - If you want to use the ``follow-the-ham`` program option, populate the program's aprs.fi access key
    - Ultimately, you need to specify the coordinates that you want to monitor. Each coordinate tuple is separated by a 'space' character. There is no limit in how many points you can specify.
    - A configuration entry of ``mowas_watch_areas = 51.838879,8.32678 51.829722,9.448333`` would result in two coordinates that are going to be monitored independently from each other:
        - C1: ``lat = 51.838879``, ``lon = 8.32678``
        - C2: ``lat = 51.829722``, ``lon = 9.448333``
    - Specify which categories ``mowas-pwb`` is supposed to monitor. Valid values: ``TEMPEST``,``FLOOD``,``FLOOD_OLD``,``WILDFIRE``,``EARTHQUAKE``,``DISASTER``. Default = all categories; at least one category needs to be specified.
 - Finally, run the program. Specify a DAPNET ham radio call sign and/or a numeric Telegram user ID as targets. For your first run, I recommend using the ``generate_test_message`` program option - this will simply trigger a test message to DAPNET/Telegram/Email, thus allowing you to tell whether your program configuration is ok.

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
