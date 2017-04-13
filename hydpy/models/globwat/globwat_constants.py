""" The HydPy-GlobWat model (`globwat`) allows for the subdivision of subbasins
into zones (hydrological response units).  Some processes, e.g. interception,
are calculated seperately for each zone.  This is why some parameters (e.g.
the interception capacity :class:`~hydpy.models.globwat.globwat_control.IcMax`)
and some sequences (e.g. the actual interception storage
:class:`~hydpy.models.globwat.globwat_states.Ic`) are 1-dimensional. Each entry
represents the value of a different zone.

In contrasts to the original HBV96 model, the HydPy-H-Land model allows for
arbitrary definitions of zones.  Nevertheless, the original distinction
in accordance with four different zone types is still supported.  The
parameter :class:`~hydpy.models.hland.hland_control.ZoneType` defines,
which entry of e.g. :class:`~hydpy.models.hland.hland_control.IcMax` is
related to which zone type via integer values.  Note that for zones of
type `field` and `forest`, the same equations are applied. (Usually, 
larger :class:`~hydpy.models.hland.hland_control.IcMax` values and smaller
:class:`~hydpy.models.hland.hland_control.CFMax` are assigned to `forest`
zones due to their higher leaf area index and the associated decrease in
solar radiation.) On the contrary, zones of type `glacier` and `ilake` are
partly connected to different process equations.  


For comprehensibility, this module introduces the relevant integer constants.
Through performing a wildcard import

>>> from hydpy.models.globwat import *

these are available in your local namespace, e.g.:

>>> RADRYTROP
1
"""

RADRYTROP = 1
"""Constant for the vegetation class `rainfed agriculture: dry tropics`."""
RAHUMTROP = 2
"""Constant for the vegetation class `rainfed agriculture: humid tropics.`"""
RAHIGHL = 3
"""Constant for the vegetation class `rainfed agriculture: highlands`."""
RASUBTROP = 4
"""Constant for the vegetation class `rainfed agriculture: subtropics`."""
RATEMP = 5
"""Constant for the vegetation class `rainfed agriculture: temperate`."""
RLSUBTROP = 6
"""Constant for the vegetation class `rangelands: subtropics`."""
RLTEMP = 7
"""Constant for the vegetation class `rangelands: temperate`."""
RLBOREAL = 8
"""Constant for the vegetation class `rangelands: boreal`."""
FOREST = 9
"""Constant for the vegetation class `forest`."""
DESERT = 10 
"""Constant for the vegetation class `desert`."""
WATER = 11
"""Constant for the vegetation class `water`."""
IRRCPR = 12
"""Constant for the vegetation class `irrigated crops: paddy rice`."""
IRRCNPR = 13
"""Constant for the vegetation class `irrigated crops: other than paddy rice`."""
OTHER = 14
"""Constant for the vegetation class `other`."""
CONSTANTS = {key: value for key, value in locals().items()
             if (key.isupper() and isinstance(value, int))}     

#CONSTANTS = {'rainfed agriculture: dry tropics': RADRYTROP,
#             'rainfed agriculture: humid tropics': RAHUMTROP,
#             'rainfed agriculture: highlands': RAHIGHL,
#             'rainfed agriculture: subtropics': RASUBTROP,
#             'rainfed agriculture: temperate': RATEMP,
#             'rangelands: subtropics': RLSUBTROP,
#             'rangelands: temperate': RLTEMP,
#             'rangelands: boreal': RLBOREAL,
#             'forest': FOREST,
#             'desert': DESERT,
#             'water': WATER,
#             'irrigated crops: paddy rice': IRRCPR,
#             'irrigated crops: other than paddy rice': IRRCNPR,
#             'other': OTHER,
#             }
