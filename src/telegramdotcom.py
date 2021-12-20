#
# MOWAS Personal Warning Beacon
# Module: Send message to telegram user account
# Author: Joerg Schultze-Lutter, 2021
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

import logging
from telegram import ParseMode, Bot, error

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)


def send_telegram_message(
    bot_token: str,
    user_id: int,
    message: str,
    is_html_content: bool = False,
    simulate_send: bool = False,
    static_image: bytes = None,
):
    """
    Send content to the Telegram API
    Parameters
    ==========
    bot_token : 'str'
        ID of the bot that will send out the message
    user_id : 'int'
        Numeric Telegram user ID
        Use Telegram's 'userinfobot' for the
        retrieval of your user ID
    message: 'str'
        Message that will be sent to the user
    is_html_content: 'bool'
        Set to True if 'message'contains HTML formatting
        Default is False
    simulate_send: 'bool'
        Set to True if you want to simulate sending
        content to the Telegram API
    static_image: bytes
        contains the encoded PNG static image
        (None if image could not get generated)

    Returns
    =======
    success: 'bool'
        True if process was successful
    """

    success = True
    if not simulate_send:
        logger.info(msg="Sending Message to Telegram API")
        mybot = Bot(token=bot_token)
        try:
            if is_html_content:
                # send our message
                mybot.sendMessage(
                    chat_id=user_id,
                    text=message,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=False,
                )
            else:
                mybot.sendMessage(chat_id=user_id, text=message)

            # Image present? Then send it, too
            if static_image:
                mybot.send_photo(chat_id=user_id, photo=static_image)

        except error.Unauthorized:
            logger.info(
                msg="Cannot send the message to your Telegram account (reason:unauthorized)!"
            )
            logger.info(
                msg="Check your configured credentials. Ensure to have established an INITIAL connection between your destination account and your bot account!"
            )
            success = False
        except:
            logger.info(msg="Unknown error occurred while sending data to Telegram")
            success = False

    else:
        logger.info(msg=f"Simulating Telegram message 'Send'; message='{message}'")
        success = True
    return success


if __name__ == "__main__":
    pass
