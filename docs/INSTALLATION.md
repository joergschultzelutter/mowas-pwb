# Installation

## Requirements

- For APRS tracking (``follow-the-ham`` option), a valid aprs.fi access key is required. Get it here: [https://aprs.fi/page/api](https://aprs.fi/page/api)
- For automated translations, a free deepl.com API license key is required which can be obtained here: [https://www.deepl.com/pro-api?cta=header-pro-api](https://www.deepl.com/pro-api?cta=header-pro-api)
- In case you intend to use the Google PaLm or OpenAI APIs for text summarization, you need to provide the necessary API keys for the  ``-text-summarizer`` command option. Both ``internal`` and ``generic`` options do not use API keys.

## General instructions

- Download the repo. Then install the packages.

```bash
    user@phost:~/mowas-pwb $ pip install -r requirements.txt
```

- Dependent on your OS' flavor, you may be required to install the following additional packages:

```bash
    user@phost:~/mowas-pwb $ apt-get install libgeos-dev libopenjp2-7
```

- rename the configuration template

```bash
    user@phost:~/mowas-pwb/src $ mv mowas-pwb.cfg.TEMPLATE mowas-pwb.cfg
```

- edit the Apprise yml config file and add your messenger(s). Note: full-text messages and SMS messages should use separate config files

```bash
    user@phost:~/mowas-pwb/src $ vi apprise_demo_template.yml
```

- Start the program. In case all libraries have been installed, you should see the following:

```bash
    user@phost:~/mowas-pwb/src $ python mowas-pwb.py
    2021-12-20 21:39:00,719 mowas-pwb -INFO- Startup ...
    2021-12-20 21:39:00,725 mowas-pwb -INFO- No messenger target credentials configured or no messaging destinations specified; exiting ...
```

When you can see this message, all required libraries have been installed. You are now required to update the program configuration file.

## Program config file

``mowas-pwb`` comes with a program config file which mainly contains API keys. In order to use the program, you need to configure this file. 

- ``aprsdotfi_api_key`` is the aprs.fi access key that is used if you tell the program to use the ``follow-the-ham`` option
- ``mowas_watch_areas`` defines your static watch areas. ``mowas-pwb`` will check these areas and if there is a match, it might forward you that warning message.
- ``smtpimap_email_address``, ``smtpimap_email_password`` ``smtpimap_server_address`` and ``smtpimap_server_port`` are required for sending data from this email account to the user
- ``imap_server_address``, ``imap_server_port`` ``imap_mailbox_name`` and ``imap_mail_retention_max_days`` need to be properly populated if ``mowas-pwb`` is supposed to clean up your mail account's "Sent" folder after x days.  
- ``mowas_active_categories`` defines the number of MOWAS categories which will be monitored by ``mowas-pwb``. By default, this setting contains all available MOWAS categories.
- ``deepldotcom_api_key`` needs to be populated with a deepl.com API key in case you intend to use the program's auto-translation option
- ``openai_api_key`` and ``palm_api_key`` need to be populated in case you intend to use the Opeen AI / Google PaLm APIs for text summary purposes.

A variable with the value of

```python
NOT_CONFIGURED
```

will automatically ___disable___ the program option that is associated with this value

### IMAP garbage collector

:bangbang::bangbang::bangbang: __Potential loss of IMAP data - READ THIS CAREFULLY__ :bangbang::bangbang::bangbang:

The use of a separate email account for generating messages is __strongly__ recommended, __especially__ if you activate the IMAP garbage collector by specifying a value for ``imap_mail_retention_max_days`` that is different to zero.

When activated, the garbage collector will delete ALL of your mails in your 'Sent' mailbox, __regardless of who created them__. If you don't care about the generated emails in your account, keep the garbage collector's default setting of ```0``` days which will deactivate the GC process.

### Config file template

```python
[mowas_config]

# API key for www.aprs.fi access
# API key NOT_CONFIGURED disable aprs.fi access
aprsdotfi_api_key = NOT_CONFIGURED

# Lat / Lon coordinates that we intend to monitor
# Format: lat1,lon1<space>lat2,lon2<space>.....latn,lonn
# Example: 51.838879,8.32678 51.829722,9.448333
mowas_watch_areas = 51.838879,8.32678 51.829722,9.448333

# SMTP  / IMAP shared Credentials
# Providers like GMail require you to set an app-specific password
# (see https://myaccount.google.com/apppasswords)
# NOT_CONFIGURED disables the email account
smtpimap_email_address = NOT_CONFIGURED
smtpimap_email_password = NOT_CONFIGURED
smtp_server_address = smtp.gmail.com
smtp_server_port = 465

# This is an optional garbage disposal handler which auto-deletes
# all messages from your mail account. Any value different to "0"
# will activate the garbage collector and delete all messages after
#
# Do NOT activate this setting for non-dedicated
# mowas-pwb mail accounts as you WILL lose all of your emails in
# your "Sent" folder. You have been warned.
# 
# Server port 0, server address NOT CONFIGURED or retention_days=0
# will automatically disable the garbage collector
#
imap_server_address = imap.gmail.com
imap_server_port = 993
imap_mailbox_name = [Gmail]/Sent Mail

# IMAP garbage collector - delete 'sent' mails after x days
# 0 = disable garbage collector
imap_mail_retention_max_days = 0

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

# deepl.com API Key (www.deepl.com). You need to populate this value if
# you intend to use the program's auto-translation functionalities.
# You can register for a free API access key here:
# https://www.deepl.com/pro-api?cta=header-pro-api
deepldotcom_api_key = NOT_CONFIGURED

# OpenAI ChatGPT access key. Required if you want mowas-pwb to send messages
# via an abbreviated Apprise message config file with text summarizer
# option "openai", otherwise optional
openai_api_key = NOT_CONFIGURED

# OpenAI ChatGPT access key. Required if you want mowas-pwb to send messages
# via an abbreviated Apprise message config file with text summarizer
# option "palm", otherwise optional
palm_api_key = NOT_CONFIGURED
```

Apply the following changes to the file:

- __Email__: specify the __sender's__ user/password
- If you want to use the ``follow-the-ham`` program option, populate the program's aprs.fi access key
- Ultimately, you need to specify the coordinates that you want to monitor. Each coordinate tuple is separated by a 'space' character. There is no limit in how many points you can specify.
- A configuration entry of ``mowas_watch_areas = 51.838879,8.32678 51.829722,9.448333`` would result in two coordinates that are going to be monitored independently from each other:
    - C1: ``lat = 51.838879``, ``lon = 8.32678``
    - C2: ``lat = 51.829722``, ``lon = 9.448333``
- Specify which categories ``mowas-pwb`` is supposed to monitor. Valid values: ``TEMPEST``,``FLOOD``,``FLOOD_OLD``,``WILDFIRE``,``EARTHQUAKE``,``DISASTER``. Default = all categories; at least one category needs to be specified.
- ``openai_api_key`` and ``palm_api_key`` need to be populated in case you intend to use the Opeen AI / Google PaLm APIs for text summary purposes.
 - Finally, run the program. Specify an email address and/or Apprise YML file as targets. For your first run, I recommend using the ``generate_test_message`` program option - this will simply trigger a test message, thus allowing you to tell whether your program configuration is ok.

Now have a look at the [program's command line parameters](COMMANDS.md)
