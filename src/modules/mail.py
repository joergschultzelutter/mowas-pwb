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
from utils import read_program_config

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)

# The following two variables define the templates for the outgoing email
# The first one is simple plain text whereas the second one is HTML
#
# YES - I KNOW. Normal people would import this from a file. Welcome to Team Different.




def send_email_message(plaintext_message: str, html_message: str, subject_message: str, smtpimap_email_address: str, smtpimap_email_password: str, mail_recipient: str):
    """
    Send an already prepared email message to an SMTP server

    Parameters
    ==========

    Returns
    =======
    """


    # Finally, generate the message
    msg = EmailMessage()
    msg["Subject"] = subject_message
    msg["From"] = f"MOWAS Personal Warning Beacon <{smtpimap_email_address}>"
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
