#
# mowas-pwb: Deepl translator code
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
from utils import get_program_config_from_file
import deepl

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)


def translate_content(
    deepl_api_key: str,
    target_language: str,
    original_text: str,
    original_language: str = "de",
):
    """
    Translates the input text via deepl.com API

    Parameters
    ==========
    deepl_api_key : 'str'
        deepl.com API access key
    target_language : 'str'
        iso639-1 target language code
    original_text: 'str'
        text that is to be translated
    original_language: 'str'
       iso639-1 source language code

    Returns
    =======
    response : 'str'
            Translated text (or original text in case of errors)
    """

    try:
        translator = deepl.Translator(deepl_api_key)
        result = translator.translate_text(
            original_text, target_lang=target_language, source_lang=original_language
        )
        response = result.text
    except:
        response = original_text
        logger.debug(msg="Cannot translate; deepl.com exception occurred")

    return response


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

    if success:
        logger.info(
            msg=translate_content(
                deepl_api_key=mowas_deepldotcom_api_key,
                target_language="FR",
                original_text="Hallo Welt",
            )
        )
