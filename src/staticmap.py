#
# MOWAS Personal Warning Beacon
# Module: Use py-staticmaps, plot an area of the map and set markers
# for the user's monitoring position(s)
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

import staticmaps
import logging
import tempfile

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)


def render_png_map(
    polygon_area: list,
    monitoring_positions: list,
    aprs_latitude: float = None,
    aprs_longitude: float = None,
):
    """
    Render a static PNG image of the destination area where a MOWAS event
    has occurred. Add markers for static and (APRS-)dynamic positions.
    Return the binary object back to the user
    Parameters
    ==========
    polygon_area : 'list'
            Polygon of the destination area
    monitoring_positions : 'list'
            Contains dictionary elements for latitude and longitude
    aprs_latitude : 'float'
            APRS dynamic latitude (if applicable)
    aprs_longitude : 'float'
            APRS dynamic longitude (if applicable)

    Returns
    =======
    file_name : 'str'
            'None' if not successful, otherwise name of the file that
            contains our rendered image
    """

    # Create the object
    context = staticmaps.Context()
    context.set_tile_provider(staticmaps.tile_provider_OSM)

    # render the map area
    context.add_object(
        staticmaps.Area(
            [staticmaps.create_latlng(lat, lng) for lat, lng in polygon_area],
            fill_color=staticmaps.parse_color("#0000002F"),
            width=2,
            color=staticmaps.BLUE,
        )
    )

    # Add the markers: static markers = red, APRS-dynamic marker: green
    for position in monitoring_positions:
        latitude = position["latitude"]
        longitude = position["longitude"]
        marker_color = (
            staticmaps.GREEN
            if latitude == aprs_latitude and longitude == aprs_longitude
            else staticmaps.RED
        )
        context.add_object(
            staticmaps.Marker(
                staticmaps.create_latlng(latitude, longitude),
                color=marker_color,
                size=12,
            )
        )

    # Create a temporary file name
    file_name = tempfile.NamedTemporaryFile().name

    try:
        # Try to render via pycairo - looks nicer
        if staticmaps.cairo_is_supported():
            image = context.render_cairo(800, 500)
            image.write_to_png(file_name)
        else:
            # if pycairo is not present, render via pillow
            image = context.render_pillow(800, 500)
            image.save(file_name, format="png")
    except Exception as ex:
        file_name = None

    return file_name


if __name__ == "__main__":
    pass
