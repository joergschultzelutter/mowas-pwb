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

# Set your OpenAI API key
my_api_key = 'YOUR_API_KEY'

def summarize_text(input_file_path):
    # Read the text from the input file
    with open(input_file_path, 'r', encoding='utf-8') as file:
        input_text = file.read()

    client = OpenAI(
        # This is the default and can be omitted
        api_key=my_api_key
    )
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
        print("The server could not be reached")
        print(e.__cause__)  # an underlying Exception, likely raised within httpx.
    except openai.RateLimitError as e:
        print("A 429 status code was received; we should back off a bit.")
    except openai.APIStatusError as e:
        print("Another non-200-range status code was received")
        print(e.status_code)
        print(e.response)
    return summary

if __name__ == "__main__":
    input_file_path = 'your_input_file.txt'  # Replace with the path to your input file
    output_summary = summarize_text(input_file_path)

    # Print the generated summary
    print("Generated Summary:")
    print(output_summary)
