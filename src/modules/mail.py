#
# mowas-pwb: Email modules
# Author: Joerg Schultze-Lutter, 2021
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

import logging
import smtplib
import imaplib
#from email.message import EmailMessage
import re
import datetime
from utility_modules import read_program_config

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)

# The following two variables define the templates for the outgoing email
# The first one is simple plain text whereas the second one is HTML
#
# YES - I KNOW. Normal people would import this from a file. Welcome to Team Different.

plaintext_template = """\
AUTOMATED EMAIL - PLEASE DO NOT RESPOND

mowas-pwb report:

This position report was requested by REPLACE_USERSCALLSIGN via APRS and was processed by MPAD (Multi-Purpose APRS Daemon). Generated at REPLACE_DATETIME_CREATED
More info on MPAD can be found here: https://www.github.com/joergschultzelutter/mpad
---
Proudly made in the district of Holzminden, Lower Saxony, Germany. 73 de DF1JSL
"""

html_template = """\
<h2>Automated email - please do not respond</h2>
<p>mowas-pwb report</p>
<ul>
<li><a href="REPLACE_APRSDOTFI" target="_blank" rel="noopener">aprs.fi</a></li>
<li><a href="REPLACE_FINDUDOTCOM" target="_blank" rel="noopener">FindU.com</a></li>
<li><a href="REPLACE_GOOGLEMAPS" target="_blank" rel="noopener">Google Maps</a>&nbsp;</li>
<li><a href="REPLACE_QRZDOTCOM" target="_blank" rel="noopener">QRZ.com</a>&nbsp;</li>
</ul>
<table border="1">
<thead>
<tr style="background-color: #bbbbbb;">
<td><strong>Position details</strong></td>
<td><strong>Values</strong></td>
</tr>
</thead>
<tbody>
<tr>
<td><strong>&nbsp;Maidenhead</strong> Grid Locator</td>
<td>&nbsp;REPLACE_MAIDENHEAD</td>
</tr>
<tr>
<td><strong>&nbsp;DMS</strong> Degrees and Decimal Minutes&nbsp;</td>
<td>&nbsp;REPLACE_DMS</td>
</tr>
<tr>
<td><strong>&nbsp;UTM</strong> Universal Transverse Mercator</td>
<td>&nbsp;REPLACE_UTM</td>
</tr>
<tr>
<td>
<p><strong>&nbsp;MGRS</strong> Military Grid Reference System</p>
<p><strong>&nbsp;USNG</strong> United States National Grid</p>
</td>
<td>&nbsp;REPLACE_MGRS</td>
</tr>
<tr>
<td>
<p><strong>&nbsp;Latitude and Longitude</strong></p>
</td>
<td>&nbsp;REPLACE_LATLON</td>
</tr>
<tr>
<td>
<p><strong>&nbsp;Altitude</strong></p>
</td>
<td>&nbsp;REPLACE_ALTITUDE</td>
</tr>
<tr>
<td>
<p><strong>&nbsp;Last heard on APRS-IS</strong></p>
</td>
<td>&nbsp;REPLACE_LASTHEARD</td>
</tr>
<tr>
<td>
<p><strong>&nbsp;Address data</strong></p>
</td>
<td>
<p>&nbsp;REPLACE_ADDRESS_DATA</p>
</td>
</tr>
</tbody>
</table>
<p>This position report was requested by <strong>REPLACE_USERSCALLSIGN</strong> via APRS and was processed by <a href="https://aprs.fi/#!call=a%2FMPAD&amp;timerange=3600&amp;tail=3600" target="_blank" rel="noopener">MPAD (Multi-Purpose APRS Daemon)</a>. Generated at <strong>REPLACE_DATETIME_CREATED</strong></p>
<p>More info on MPAD can be found here: <a href="https://www.github.com/joergschultzelutter/mpad" target="_blank" rel="noopener">https://www.github.com/joergschultzelutter/mpad</a></p>
<hr />
<p>Proudly made in the district of Holzminden, Lower Saxony, Germany. 73 de DF1JSL</p>
"""

mail_subject_template = "APRS Position Report for REPLACE_MESSAGECALLSIGN"


def send_email_position_report(response_parameters: dict):
    """
    Prepare an APRS-IS email message with an aprs.fi position_report

    Parameters
    ==========
    response_parameters : 'dict'
        The all-knowing dictionary with our settings and parser values

    Returns
    =======
    success: 'bool'
        False in case an error has occurred
    output_list: 'list'
        List item, containing the message(s) that are going to be sent
        back to the APRS user (does not contain any email content)
    """

    smtpimap_email_address = response_parameters["smtpimap_email_address"]
    smtpimap_email_password = response_parameters["smtpimap_email_password"]

    # copy the templates
    plaintext_message = plaintext_template
    html_message = html_template
    subject_message = mail_subject_template


    # add the Time Created information
    utc_create_time = datetime.datetime.utcnow()
    msg_string = f"{utc_create_time.strftime('%d-%b-%Y %H:%M:%S')} UTC"
    plaintext_message = plaintext_message.replace(
        "REPLACE_DATETIME_CREATED", msg_string
    )
    html_message = html_message.replace("REPLACE_DATETIME_CREATED", msg_string)

    # Finally, generate the message
    msg = EmailMessage()
    msg["Subject"] = subject_message
    msg["From"] = f"MPAD Multi-Purpose APRS Daemon <{smtpimap_email_address}>"
    msg["To"] = mail_recipient
    msg.set_content(plaintext_message)
    msg.add_alternative(html_message, subtype="html")

    success, output_message = send_message_via_snmp(
        smtpimap_email_address=smtpimap_email_address,
        smtpimap_email_password=smtpimap_email_password,
        message_to_send=msg,
    )
    output_list = [output_message]
    return output_list


def imap_garbage_collector(smtpimap_email_address: str, smtpimap_email_password: str):
    """
    Delete all messages in the MPAD user's iMAP account that are older than x days

    Parameters
    ==========
    smtpimap_email_address : 'str'
        email address for login
    smtpimap_email_password: 'str'
        password for login

    Returns
    =======
    """

    # Check if the garbage collector has been disabled and
    # abort the process if necessary
    if mpad_config.mpad_imap_mail_retention_max_days == 0:
        return

    regex_string = r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
    matches = re.search(
        pattern=regex_string, string=smtpimap_email_address, flags=re.IGNORECASE
    )
    if (
        matches
        and mpad_config.mpad_imap_server_port != 0
        and mpad_config.mpad_imap_server_address
    ):
        cutoff = (
            datetime.date.today()
            - datetime.timedelta(days=mpad_config.mpad_imap_mail_retention_max_days)
        ).strftime("%d-%b-%Y")
        query_parms = f'(BEFORE "{cutoff}")'
        with imaplib.IMAP4_SSL(
            host=mpad_config.mpad_imap_server_address,
            port=mpad_config.mpad_imap_server_port,
        ) as imap:
            logger.info(msg="Starting IMAP garbage collector process")
            typ, dat = imap.login(
                user=smtpimap_email_address, password=smtpimap_email_password
            )
            if typ == "OK":
                logger.info(msg="IMAP login successful")
                # typ, dat = imap.list()     # get list of mailboxes
                typ, dat = imap.select(mailbox=mpad_config.mpad_imap_mailbox_name)
                if typ == "OK":
                    logger.info(msg=f"IMAP folder SELECT for {mpad_config.mpad_imap_mailbox_name} successful")
                    typ, msgnums = imap.search(None, "ALL", query_parms)
                    if typ == "OK":
                        for num in msgnums[0].split():
                            imap.store(num, "+FLAGS", "\\Deleted")
                        imap.expunge()
                        logger.info(
                            msg=f"Have executed IMAP cleanup with params '{query_parms}'"
                        )
                    imap.close()
                else:
                    logger.info(
                        msg=f"IMAP mailbox {mpad_config.mpad_imap_mailbox_name} does not exist"
                    )
                imap.logout()
            else:
                logger.info(
                    msg=f"Cannot perform IMAP login; user={smtpimap_email_address}, server={mpad_config.mpad_imap_server_address}, port={mpad_config.mpad_imap_server_port}"
                )


def send_message_via_snmp(
    smtpimap_email_address: str,
    smtpimap_email_password: str,
    message_to_send: EmailMessage,
):
    """
    Send an email via SMTP

    Parameters
    ==========
    smtpimap_email_address : 'str'
        email address for login
    smtpimap_email_password: 'str'
        password for login
    message_to_send: 'str'
        The message that has already been prepared for
        the end user

    Returns
    =======
    success: 'bool'
        True if successful
    output_messagee: 'str'
        status that corresponds to the SMTP delivery process
    """

    success = False
    output_message = ""
    # Check if the email address has been configured. By default, this value
    # is set to NOT_CONFIGURED in the program's template on github
    # if the mail address looks ok, then we assume that the user has
    # done his homework and had completed his local setup
    regex_string = r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
    matches = re.search(
        pattern=regex_string, string=smtpimap_email_address, flags=re.IGNORECASE
    )
    if (
        matches
        and mpad_config.mpad_smtp_server_port != 0
        and mpad_config.mpad_smtp_server_address
    ):
        with smtplib.SMTP_SSL(
            host=mpad_config.mpad_smtp_server_address,
            port=mpad_config.mpad_smtp_server_port,
        ) as smtp:
            try:
                code, resp = smtp.login(
                    user=smtpimap_email_address, password=smtpimap_email_password
                )
            except (smtplib.SMTPException, smtplib.SMTPAuthenticationError) as e:
                output_message = (
                    "Cannot connect to SMTP server or other issue; cannot send mail"
                )
                logger.info(msg=output_message)
                return False, output_message
            if code in [235, 503]:
                try:
                    smtp.send_message(msg=message_to_send)
                except:
                    output_message = "Connected to SMTP but Cannot send email"
                    logger.info(msg=output_message)
                    return False, output_message

            success = True
            output_message = (
                "The requested position report was emailed to its recipient"
            )
            smtp.quit()
    else:
        output_message = (
            "This MPAD instance is not configured for email position messages"
        )
    return success, output_message


if __name__ == "__main__":
    (
        success,
        aprsdotfi_api_key,
        openweathermap_api_key,
        aprsis_callsign,
        aprsis_passcode,
        dapnet_callsign,
        dapnet_passcode,
        smtpimap_email_address,
        smtpimap_email_password,
    ) = read_program_config()
    imap_garbage_collector(smtpimap_email_address, smtpimap_email_password)
