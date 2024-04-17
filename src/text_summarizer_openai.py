#
# mowas-pwb: Text summarizer (OpenAI / ChatGPT module)
# Author: Joerg Schultze-Lutter, 2023
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
# Shorten and abbreviate the original input text which - unfortunately - is
# usually provided by the BBK site in epic proportions. We try to shorten the
# text as much as possible, thus rendering the output text to a format that is
# more compatible with e.g. SMS devices.
#
import openai
from openai import OpenAI
import logging
import json

# Set up the global logger variable
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)


def text_summarizer_openai(input_text: str, api_key: str, **kwargs):
    """
    Summarize and abbreviate text via OpenAI
    ==========
    input_text: 'str'
        The text that we want to shorten and
        abbreviate
    api_key: 'str'
        OpenAI API Key

    Returns
    =======
    response: 'str'
        Our abbreviated text
    """

    client = OpenAI(api_key=api_key)

    system_role_description = """Du bist ein hilfreicher AI-Assistent, der darauf spezialisiert ist,  
    eingehenden Text soweit wie möglich idealerweise bis auf Stichpunktebene zu verkürzen. Die 
    Texteingaben des Nutzers werden dabei Wetter- und Unwetter-Warnmeldungen sein. Diese beinhalten 
    in der Regel eine Menge überflüssige Informationen und ggf. HTML-Links und Formatierungen. 
    Deine Aufgabe ist es, den Text soweit eingehenden Text soweit wie möglich idealerweise bis 
    auf Stichpunktebene zu verkürzen, HTLML-Tags sowie -Links zu entfernen und nur diese Stichpunkte 
    zurückzugeben. Der ausgehende Text wird später an Pager und Mobiltelefone übertragen; es ist somit 
    von großer Wichtigkeit, daß der Text einerseits so kurz wie irgend möglich zusammengefaßt wird 
    und andererseits alle für den Empfänger relevanten Daten beinhaltet."""

    user_content = f"""Hier kommt die Nachricht:\r\n----\r\n{input_text}\r\n----"""

    result = None

    try:
        summary = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_role_description,
                },
                {
                    "role": "user",
                    "content": user_content,
                },
            ],
            model="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=2048,
        )
        result = summary.choices[0].message.content
    except openai.APIConnectionError as e:
        logger.error(msg="Unable to connect to OpenAI server")
        logger.error(e.__cause__)
        result = None
    except openai.RateLimitError as e:
        logger.error(msg="We have hit the API rate limit")
        result = None
    except openai.APIStatusError as e:
        logger.error(msg=f"HTTP{e.status_code}: {e.response}")
        result = None
    except Exception as e:
        logger.error(msg="Other exception occurred")
        logger.error(e.__cause__)
        result = None

    return result


if __name__ == "__main__":
    pass
