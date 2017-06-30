# -*- coding: utf-8 -*-
"""The HydPy-H-Land model (`hland`) allows for the subdivision of subbasins
into zones (hydrological response units).  Some processes, e.g. interception,
are calculated seperately for each zone.  This is why some parameters (e.g.
the interception capacity :class:`~hydpy.models.hland.hland_control.IcMax`)
and some sequences (e.g. the actual interception storage
:class:`~hydpy.models.hland.hland_states.Ic`) are 1-dimensional.  Each entry
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

>>> from hydpy.models.hland import *

these are available in your local namespace:

>>> FIELD, FOREST, GLACIER, ILAKE
(1, 2, 3, 4)
"""

FIELD = 1
"""Constant for the zone type `field`."""
FOREST = 2
"""Constant for the zone type `forest.`"""
GLACIER = 3
"""Constant for the zone type `glacier`."""
ILAKE = 4
"""Constant for the zone type `internal lake`."""
CONSTANTS = {key: value for key, value in locals().items()
             if (key.isupper() and isinstance(value, int))}
"""Dictionary containing all constants defined by HydPy-H-Land."""
