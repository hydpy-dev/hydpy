""" The HydPy-GlobWat model (`globwat`) allows for the subdivision of subbasins
into zones (hydrological response units).  Some processes, e.g. interception,
are calculated seperately for each zone.  This is why some parameters (e.g.
the interception capacity :class:`~hydpy.models.globwat.globwat_control.IcMax`)
and some sequences (e.g. the actual interception storage
:class:`~hydpy.models.globwat.globwat_states.Ic`) are 1-dimensional. Each entry
represents the value of a grid zone.

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
IRR_GER = 14
"""Constant for the vegetation class `irrigation germany`."""
IRR_CZE = 15
"""Constant for the vegetation class `irrigation czech republic`."""
IRR_AUT = 16
"""Constant for the vegetation class `irrigation austria`."""
IRR_POL = 17
"""Constant for the vegetation class `irrigation poland`."""
IRR_HUN = 18
"""Constant for the vegetation class `irrigation hungary`."""
IRR_SUI = 19
"""Constant for the vegetation class `irrigation switzerland`."""
IRR_ITA = 20
"""Constant for the vegetation class `irrigation italy`."""
IRR_SLO = 21
"""Constant for the vegetation class `irrigation slovenia`."""
IRR_CRO = 22
"""Constant for the vegetation class `irrigation croatia`."""
IRR_BYH = 23
"""Constant for the vegetation class `irrigation bosnia and herzegovina`."""
IRR_ALB = 24
"""Constant for the vegetation class `irrigation albania`."""
IRR_SER = 25
"""Constant for the vegetation class `irrigation serbia`."""
IRR_SLV = 26
"""Constant for the vegetation class `irrigation slovakia`."""
IRR_UKR = 27
"""Constant for the vegetation class `irrigation ukraine`."""
IRR_BUL = 28
"""Constant for the vegetation class `irrigation bulgaria`."""
IRR_ROM = 29
"""Constant for the vegetation class `irrigation romania`."""
IRR_MLD = 30
"""Constant for the vegetation class `irrigation moldovia`."""
OTHER = 99
"""Constant for the vegetation class `other`."""
CONSTANTS = {key: value for key, value in locals().items()
             if (key.isupper() and isinstance(value, int))}