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
import io
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)


def render_png_map(
    polygon_area: list,
    monitoring_positions: list,
    aprs_latitude: float = 0.0,
    aprs_longitude: float = 0.0,
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
    iobuffer : 'bytes'
            'None' if not successful, otherwise binary representation
            of the image
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

    # create a buffer as we need to write to write to memory
    iobuffer = io.BytesIO()

    try:
        # Try to render via pycairo - looks nicer
        if staticmaps.cairo_is_supported():
            image = context.render_cairo(800, 500)
            image.write_to_png(iobuffer)
        else:
            # if pycairo is not present, render via pillow
            image = context.render_pillow(800, 500)
            image.save(iobuffer)

        # reset the buffer position
        iobuffer.seek(0)

        # get the buffer value and return it
        view = iobuffer.getvalue()
    except:
        view = None

    return view


if __name__ == "__main__":
    # fmt: off
    polygon = [(48.4794, 10.771), (48.4781, 10.773), (48.4786, 10.7749), (48.4786, 10.7764), (48.4781, 10.7779), (48.4777, 10.7795), (48.4778, 10.7813), (48.4776, 10.7832), (48.4771, 10.7832), (48.4762, 10.7837), (48.4756, 10.7843), (48.4753, 10.7848), (48.4745, 10.7858), (48.4738, 10.7862), (48.4727, 10.7859), (48.4722, 10.7866), (48.4727, 10.7882), (48.4728, 10.7903), (48.4725, 10.7916), (48.4723, 10.7943), (48.4721, 10.7955), (48.4724, 10.798), (48.473, 10.7992), (48.4732, 10.8008), (48.4734, 10.8052), (48.4735, 10.8062), (48.4729, 10.8089), (48.4724, 10.8115), (48.4723, 10.8154), (48.4738, 10.8147), (48.4738, 10.8155), (48.4738, 10.8184), (48.4757, 10.8184), (48.4759, 10.8219), (48.4752, 10.8223), (48.4744, 10.8225), (48.4735, 10.8222), (48.4727, 10.8216), (48.4719, 10.8212), (48.4707, 10.8214), (48.47, 10.8219), (48.4706, 10.8239), (48.4709, 10.8256), (48.47, 10.8264), (48.4704, 10.8278), (48.4694, 10.8294), (48.4698, 10.8317), (48.4698, 10.8347), (48.4698, 10.8376), (48.4694, 10.8443), (48.4699, 10.8446), (48.4699, 10.8481), (48.4684, 10.8484), (48.4685, 10.8495), (48.4685, 10.8506), (48.4672, 10.851), (48.4674, 10.8563), (48.468, 10.8578), (48.4674, 10.8579), (48.4674, 10.8592), (48.4625, 10.8597), (48.4623, 10.8608), (48.4612, 10.861), (48.4601, 10.861), (48.4591, 10.8609), (48.4591, 10.8668), (48.4587, 10.8668), (48.4575, 10.8666), (48.4574, 10.8685), (48.4565, 10.8688), (48.4556, 10.8688), (48.455, 10.8683), (48.454, 10.8674), (48.4525, 10.8669), (48.4494, 10.8665), (48.4478, 10.8655), (48.4467, 10.8652), (48.4466, 10.8614), (48.4437, 10.8619), (48.4423, 10.8621), (48.4453, 10.8579), (48.4457, 10.8573), (48.446, 10.8564), (48.4449, 10.8566), (48.4428, 10.8571), (48.4428, 10.855), (48.4419, 10.8553), (48.4419, 10.8527), (48.438, 10.8539), (48.4379, 10.8462), (48.437, 10.8467), (48.4369, 10.8437), (48.4371, 10.843), (48.437, 10.8408), (48.4363, 10.8381), (48.4359, 10.8386), (48.4357, 10.8395), (48.4349, 10.8404), (48.435, 10.8378), (48.4352, 10.8356), (48.4348, 10.8339), (48.4343, 10.8318), (48.4343, 10.8304), (48.437, 10.8301), (48.437, 10.8286), (48.4383, 10.8291), (48.4387, 10.8269), (48.4394, 10.8266), (48.4423, 10.828), (48.4437, 10.829), (48.4439, 10.8266), (48.444, 10.8249), (48.4426, 10.8235), (48.4426, 10.8219), (48.4419, 10.8217), (48.4413, 10.8218), (48.4406, 10.822), (48.4404, 10.8196), (48.4388, 10.8189), (48.4379, 10.8184), (48.4371, 10.8167), (48.4376, 10.8142), (48.4369, 10.8145), (48.4372, 10.813), (48.4363, 10.8095), (48.4358, 10.8084), (48.4355, 10.8063), (48.4351, 10.8043), (48.4349, 10.8029), (48.4341, 10.8027), (48.4345, 10.8012), (48.4327, 10.8), (48.432, 10.8004), (48.4331, 10.7984), (48.4326, 10.7969), (48.4335, 10.7951), (48.4346, 10.7957), (48.4343, 10.7972), (48.4357, 10.7961), (48.4363, 10.7964), (48.437, 10.7978), (48.4386, 10.7983), (48.4392, 10.7979), (48.4395, 10.7957), (48.4398, 10.7911), (48.4397, 10.7897), (48.4396, 10.788), (48.4401, 10.788), (48.4403, 10.7859), (48.441, 10.7854), (48.4417, 10.7872), (48.4423, 10.7869), (48.4433, 10.7894), (48.4426, 10.7898), (48.4436, 10.7901), (48.4448, 10.7912), (48.4458, 10.7921), (48.448, 10.7836), (48.448, 10.7799), (48.4486, 10.7767), (48.4483, 10.7746), (48.4482, 10.7734), (48.4492, 10.7732), (48.4495, 10.7737), (48.4497, 10.772), (48.45, 10.7696), (48.4506, 10.7682), (48.4505, 10.7646), (48.4512, 10.7644), (48.4525, 10.7654), (48.4533, 10.7665), (48.4537, 10.7675), (48.4542, 10.7673), (48.4549, 10.7674), (48.4566, 10.7672), (48.458, 10.7675), (48.4592, 10.7669), (48.4602, 10.766), (48.4608, 10.7654), (48.4615, 10.7658), (48.4617, 10.767), (48.4627, 10.766), (48.464, 10.7645), (48.4648, 10.7634), (48.4658, 10.7627), (48.4668, 10.7621), (48.4685, 10.7596), (48.4698, 10.7569), (48.471, 10.754), (48.4721, 10.7527), (48.4729, 10.7512), (48.4743, 10.7522), (48.4749, 10.7537), (48.4773, 10.756), (48.4767, 10.7568), (48.4771, 10.7579), (48.477, 10.7588), (48.4757, 10.7601), (48.4756, 10.7614), (48.4758, 10.7621), (48.4767, 10.7633), (48.477, 10.7648), (48.4774, 10.7664), (48.4776, 10.7678), (48.4783, 10.7684), (48.4786, 10.7694), (48.4794, 10.7702), (48.4794, 10.771)]
    markers = [{'latitude': 48.4781, 'longitude': 10.774}, {'latitude': 48.4781, 'longitude': 10.773}]
    # fmt: on

    buffer = render_png_map(polygon, markers, 48.4781, 10.773)
    if buffer:
        logger.debug("Received content")
