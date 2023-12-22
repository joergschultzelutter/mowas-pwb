#
# mowas-pwb: Text summarizer (ChatGPT module)
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

# Set up the global logger variable
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)


def text_summarizer_gpt(input_text: str, api_key: str, **kwargs):
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

    summary = None

    try:
        summary = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": f"Summarize this: {input_text}",
                }
            ],
            model="gpt-3.5-turbo",
        )
    except openai.APIConnectionError as e:
        logger.error(msg="Unable to connect to OpenAI server")
        logger.error(e.__cause__)
    except openai.RateLimitError as e:
        logger.error(msg="We have hit the API rate limit")
    except openai.APIStatusError as e:
        logger.error(msg=f"HTTP{e.status_code}: {e.response}")

    return summary


if __name__ == "__main__":
    pass
