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
from email.message import EmailMessage
from email.utils import make_msgid
import re
import datetime
from utils import get_program_config_from_file

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)

# The following two variables define the templates for the outgoing email
# The first one is simple plain text whereas the second one is HTML
#
# YES - I KNOW. Normal people would import this from a file. Welcome to Team Different.


def send_email_message(
    plaintext_message: str,
    html_message: str,
    subject_message: str,
    smtpimap_email_address: str,
    smtpimap_email_password: str,
    mail_recipient: str,
    smtp_server_address: str,
    smtp_server_port: int,
    html_image: bytes = None,
):
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

    # Image present? Then encode it properly
    if html_image:
        image_cid = make_msgid()
        msg.add_alternative(
            html_message.format(image_cid=image_cid[1:-1]), subtype="html"
        )
        x = msg.get_payload()

        msg.get_payload()[1].add_related(
            html_image, maintype="image", subtype="png", cid=image_cid
        )
    else:
        # otherwise, send the HTML content without an image
        msg.add_alternative(html_message, subtype="html")

    success, output_message = send_message_via_snmp(
        smtpimap_email_address=smtpimap_email_address,
        smtpimap_email_password=smtpimap_email_password,
        message_to_send=msg,
        smtp_server_address=smtp_server_address,
        smtp_server_port=smtp_server_port,
    )
    output_list = [output_message]
    return output_list


def imap_garbage_collector(
    smtpimap_email_address: str,
    smtpimap_email_password: str,
    imap_server_port: int,
    imap_server_address: str,
    imap_mail_retention_max_days: int,
    imap_mailbox_name: str,
):
    """
    Delete all messages in the user's iMAP account that are older than x days

    Parameters
    ==========
    smtpimap_email_address : 'str'
        email address for login
    smtpimap_email_password: 'str'
        password for login
    imap_server_port: 'int'
        IMAP server port for the garbage collector
        0 = disables garbage collector
    imap_server_address: 'str'
        IMAP server URL for the garbage collector
        Can be set to 'None' in case you want to
        force-disable the garbage collector
    imap_mail_retention_max_days: 'int'
        Delete mails from "sent" folder after x days
        Set this to zero if you want to disable the
        garbage collector
    imap_mailbox_name: 'str'
        "Sent" folder's name on the mail server

    Returns
    =======
    """

    # Check if the garbage collector has been disabled and
    # abort the process if necessary
    if mowas_imap_mail_retention_max_days == 0:
        return

    regex_string = r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
    matches = re.search(
        pattern=regex_string, string=smtpimap_email_address, flags=re.IGNORECASE
    )
    if matches and imap_server_port != 0 and imap_server_address:
        cutoff = (
            datetime.date.today()
            - datetime.timedelta(days=imap_mail_retention_max_days)
        ).strftime("%d-%b-%Y")
        query_parms = f'(BEFORE "{cutoff}")'
        with imaplib.IMAP4_SSL(
            host=imap_server_address,
            port=imap_server_port,
        ) as imap:
            logger.info(msg="Starting IMAP garbage collector process")
            typ, dat = imap.login(
                user=smtpimap_email_address, password=smtpimap_email_password
            )
            if typ == "OK":
                logger.info(msg="IMAP login successful")
                # typ, dat = imap.list()     # get list of mailboxes
                typ, dat = imap.select(mailbox=imap_mailbox_name)
                if typ == "OK":
                    logger.info(
                        msg=f"IMAP folder SELECT for {imap_mailbox_name} successful"
                    )
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
                    logger.info(msg=f"IMAP mailbox {imap_mailbox_name} does not exist")
                imap.logout()
            else:
                logger.info(
                    msg=f"Cannot perform IMAP login; user={smtpimap_email_address}, server={imap_server_address}, port={imap_server_port}"
                )


def send_message_via_snmp(
    smtpimap_email_address: str,
    smtpimap_email_password: str,
    message_to_send: EmailMessage,
    smtp_server_port: int,
    smtp_server_address: str,
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
    smtp_server_port: int
        SMTP server port
    smtp_server_address: str
        SMTP server address

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
    if matches and smtp_server_port != 0 and smtp_server_address:
        with smtplib.SMTP_SSL(
            host=smtp_server_address,
            port=smtp_server_port,
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
        output_message = "This mowas-pwb instance is not configured for email messages"
    return success, output_message


if __name__ == "__main__":
    (
        success,
        mowas_aprsdotfi_api_key,
        mowas_dapnet_login_callsign,
        mowas_dapnet_login_passcode,
        mowas_watch_areas,
        mowas_telegram_bot_token,
        mowas_smtpimap_email_address,
        mowas_smtpimap_email_password,
        mowas_smtp_server_address,
        mowas_smtp_server_port,
        mowas_active_categories,
        mowas_imap_server_address,
        mowas_imap_server_port,
        mowas_imap_mailbox_name,
        mowas_imap_mail_retention_max_days,
        mowas_deepldotcom_api_key,
    ) = get_program_config_from_file()
