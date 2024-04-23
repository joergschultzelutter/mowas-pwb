#
# MOWAS Personal Warning Beacon
# Module: Renders a sample output message which is used
# by the program for its configuration test
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

import json
from staticmap import render_png_map

# Sample JSON file - contains everything but the static image
meinjson = """
{
	"MOWAS-BEISPIEL-MELDUNG": {
		"headline": "mowas-pwb Konfigurationstest",
		"urgency": "Immediate",
		"severity": "Minor",
		"description": "Bei Empfang dieser Nachricht ist mowas-pwb ordnungsgemäß konfiguriert",
		"instruction": "Vielen Dank für die Benutzung dieser Software",
		"sms_message": "mowas-pwb Konfigurationstest ok",
		"sent": "2020-08-28T11:00:08+02:00",
		"msgtype": "Alert",
		"areas": ["Kreis Holzminden"],
		"geocodes": ["103255000"],
		"high_prio": false,
		"latlon_polygon": [
			[52.038744328437716, 9.57555944842884],
			[51.99559190725656, 9.607361808813355],
			[51.986011627699106, 9.625762226308055],
			[51.96441372144737, 9.646755001930773],
			[51.968619010348384, 9.662546118738195],
			[51.95522390668395, 9.687141354499134],
			[51.964698829006785, 9.698112193778385],
			[51.96679201178659, 9.70979867259881],
			[51.98282725640571, 9.714755171915922],
			[51.97979458187127, 9.7213137188826],
			[51.978170854444954, 9.742929659416584],
			[51.97988732403177, 9.739841885350042],
			[51.982850984068435, 9.744730933112894],
			[51.98315482124891, 9.758726134184863],
			[51.97326407633042, 9.775506505776136],
			[51.96668566857317, 9.779514352440032],
			[51.963357029851686, 9.77502380161898],
			[51.952842630401946, 9.806973069650564],
			[51.94293339032796, 9.820122176302242],
			[51.94312759486955, 9.824577336196029],
			[51.935388713241956, 9.824078385902842],
			[51.93159446015562, 9.829376619110022],
			[51.928632583295986, 9.83740056287372],
			[51.929952946929745, 9.849186743695725],
			[51.91791586945389, 9.862218073206277],
			[51.91470639668946, 9.881318706131665],
			[51.906155154127724, 9.894247866054425],
			[51.90094279772548, 9.894811228166482],
			[51.90907911291776, 9.881817409400785],
			[51.906573266276865, 9.877131748463885],
			[51.90856559228036, 9.87295091938984],
			[51.901069782752465, 9.879802647895897],
			[51.896511293083364, 9.86823258100444],
			[51.898600964673854, 9.860322262842354],
			[51.8966445661943, 9.8528759459371],
			[51.88627723923712, 9.829400388923625],
			[51.88484082874812, 9.803327963670206],
			[51.87043494529567, 9.795105226251344],
			[51.8644583571788, 9.78402392392271],
			[51.867217557175884, 9.758681566183968],
			[51.88048949278378, 9.728071470319597],
			[51.88149688774518, 9.718417054947045],
			[51.87753204344272, 9.705214974352849],
			[51.87273385113904, 9.710109244517245],
			[51.86201954841436, 9.68874750592156],
			[51.8538782498405, 9.682210050043013],
			[51.84843346995731, 9.688452102461218],
			[51.83966726480776, 9.682624961121917],
			[51.8325659855862, 9.657704626202102],
			[51.83611673878842, 9.652265972962246],
			[51.829114764154696, 9.643089340058944],
			[51.824716521359285, 9.646961258091862],
			[51.81803886306491, 9.642876663845861],
			[51.81667887963068, 9.630302831777364],
			[51.81093659176945, 9.61655187100371],
			[51.7897866868496, 9.57918050736889],
			[51.77551123306167, 9.581358999801397],
			[51.76272331195732, 9.561347663236173],
			[51.755379942096, 9.564484922499046],
			[51.739913036995794, 9.557454860535374],
			[51.73990639576791, 9.542050797997573],
			[51.72771899353904, 9.503190372430534],
			[51.70571654878278, 9.466739756935224],
			[51.695741905104605, 9.44078078690489],
			[51.690978946726865, 9.437373514954745],
			[51.677790479825504, 9.439503568728583],
			[51.67328897182182, 9.423241913769084],
			[51.66130649102391, 9.428370416067601],
			[51.663049872949365, 9.43611291660999],
			[51.65353047017968, 9.437128285990022],
			[51.647269252221086, 9.417317501499635],
			[51.64664627229889, 9.382290535780049],
			[51.64984028650623, 9.374706085604766],
			[51.66541958622654, 9.379039258010819],
			[51.67398855618006, 9.395687618730015],
			[51.6894787994349, 9.386758146570173],
			[51.702438727837745, 9.401646120568106],
			[51.7193901804808, 9.387318166956437],
			[51.731971436563704, 9.394415502869775],
			[51.73809621041093, 9.378877584219053],
			[51.74401116511933, 9.375500345512807],
			[51.750233853688165, 9.383725124016713],
			[51.757850971280654, 9.384336129984948],
			[51.75937197251013, 9.402696727087568],
			[51.77104112518946, 9.409550769057262],
			[51.794799409755434, 9.448156881625152],
			[51.79701537819286, 9.43636741209957],
			[51.80345181662804, 9.440817445496858],
			[51.80488327321521, 9.43090136314349],
			[51.8106919027483, 9.430547391051556],
			[51.81049191450199, 9.42732997137859],
			[51.8249330241551, 9.440521309241053],
			[51.827813929447665, 9.436722796092909],
			[51.82922116793286, 9.442178494680874],
			[51.840278045208244, 9.43314949909676],
			[51.851499582812195, 9.455737620473604],
			[51.85770311706846, 9.46143598035474],
			[51.8627974277045, 9.459648734905093],
			[51.8562216564235, 9.437366927413075],
			[51.85559295545741, 9.404902437940205],
			[51.86035816978298, 9.392852288645358],
			[51.86487896427862, 9.362865542207839],
			[51.85361074030374, 9.334699754871258],
			[51.85506096219108, 9.323343735912374],
			[51.85605151099195, 9.335757386310352],
			[51.878640121571564, 9.340165313235987],
			[51.880201093328246, 9.344326577754753],
			[51.89633987733517, 9.345152584250561],
			[51.91731613193209, 9.331904481969195],
			[51.917050911768065, 9.32325503358241],
			[51.92280706260275, 9.314943365319364],
			[51.92271961930251, 9.30889275999427],
			[51.93111280960659, 9.307945159957137],
			[51.93369190271889, 9.35073388534796],
			[51.939643215961645, 9.35600284350749],
			[51.9420443954605, 9.366014642903924],
			[51.94877174383705, 9.359740466736316],
			[51.950142322043, 9.363673658938668],
			[51.95449427060699, 9.361204756134867],
			[51.96017752583586, 9.342925236049433],
			[51.96654744344435, 9.341444856270455],
			[51.97522353550911, 9.349249857528685],
			[51.97687809088871, 9.360395704775952],
			[51.9723555568043, 9.364427443697327],
			[51.97787018908518, 9.385368952830424],
			[51.97773952936136, 9.407179818178182],
			[51.98348322866398, 9.41923539433972],
			[51.98117667739177, 9.426036285700542],
			[51.98270055071135, 9.44150171235862],
			[51.98921899988157, 9.448198135407527],
			[51.989433326432994, 9.455172757452603],
			[51.99588404261489, 9.457297679021934],
			[51.99827847740631, 9.466428197582843],
			[52.00140591200676, 9.467513857451632],
			[52.0020832984091, 9.48256371456211],
			[52.00670810942167, 9.489068105929327],
			[52.01504916827333, 9.48694893875197],
			[52.01436130653914, 9.49069654014787],
			[52.01847864726148, 9.49356474943296],
			[52.02082159772938, 9.503105068255726],
			[52.01792118137733, 9.5162201194369],
			[52.02221769899572, 9.538829630204402],
			[52.03472457638023, 9.535969003108374],
			[52.03724232651191, 9.531439963578382],
			[52.03981538700603, 9.553846663660057],
			[52.044123487179725, 9.562859953202773],
			[52.038744328437716, 9.57555944842884]
		],
		"coords_matching_latlon": [{
			"latitude": 51.81901,
			"longitude": 9.5139941,
			"address": "Niemanns Villa, Schießhäuser Straße, Holzminden, Landkreis Holzminden, Niedersachsen, 37603, Deutschland",
			"maidenhead": "JO41st16",
			"utm": "32 U 535428 5741033",
			"aprs_coordinates": true
		}, {
			"latitude": 51.9016773,
			"longitude": 9.6425367,
			"address": "Homburg, Tillrundweg, Stadtoldendorf, Samtgemeinde Eschershausen-Stadtoldendorf, Landkreis Holzminden, Niedersachsen, 37627, Deutschland",
			"maidenhead": "JO41tv76",
			"utm": "32 U 544207 5750298",
			"aprs_coordinates": false
		}],
		"contact": "https://www.github.com/joergschultzelutter/mowas-pwb",
		"lang": "en-us",
		"lang_headline": "mowas-pwb configuration test",
		"lang_description": "With receipt of this message mowas-pwb is properly configured",
		"lang_instruction": "Thank you for using this software",
		"lang_contact": "https://www.github.com/joergschultzelutter/mowas-pwb",
		"lang_sms_message": "mowas-pwb configuration test: ok"
	}
}"""


def generate_test_data():
    """
    Converts the JSON input to a dict, renders the static image and returns the dict

    Parameters
    ==========

    Returns
    =======
    target_dict: 'dict'
        target dictionary which contains a valid response object plus map
    """

    target_dict = json.loads(meinjson)
    latlon_polygon = target_dict["MOWAS-BEISPIEL-MELDUNG"]["latlon_polygon"]
    coords_matching_latlon = target_dict["MOWAS-BEISPIEL-MELDUNG"][
        "coords_matching_latlon"
    ]

    # render the image
    image_file_name = render_png_map(
        polygon_area=latlon_polygon,
        monitoring_positions=coords_matching_latlon,
        aprs_latitude=51.81901,
        aprs_longitude=9.5139941,
    )
    target_dict["MOWAS-BEISPIEL-MELDUNG"]["static_image"] = image_file_name
    return target_dict


if __name__ == "__main__":
    pass
