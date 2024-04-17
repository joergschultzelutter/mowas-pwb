#
# mowas-pwb: Internal text summarizer
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


def text_summarizer_internal(input_text: str, **kwargs):
    """
    Summarize and abbreviate text
    ==========
    input_text: 'str'
        The text that we want to shorten and
        abbreviate
    Returns
    =======
    response: 'str'
        Our abbreviated text
    """

    return input_text


if __name__ == "__main__":
    print(text_summarizer_internal("This is a very long text"))
