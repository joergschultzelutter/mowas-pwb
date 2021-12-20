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
import deepl

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)


def translate_text_string(
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
    except Exception as ex:
        response = original_text
        logger.debug(msg="Cannot translate; deepl.com exception occurred")

    return response


def translate_text_list(
    deepl_api_key: str,
    target_language: str,
    original_text: list,
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
    original_text: 'list'
        list of texts that are to be translated
    original_language: 'str'
       iso639-1 source language code

    Returns
    =======
    response : 'list'
            Translated texts (or original texts in case of errors)
    """

    try:
        translator = deepl.Translator(deepl_api_key)
        result = translator.translate_text(
            original_text, target_lang=target_language, source_lang=original_language
        )
        response = [str(item) for item in result]
    except Exception as ex:
        response = original_text
        logger.debug(msg="Cannot translate; deepl.com exception occurred")

    return response


if __name__ == "__main__":
    pass
