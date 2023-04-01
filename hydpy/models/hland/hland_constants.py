# -*- coding: utf-8 -*-
"""Base model |hland| allows dividing subbasins into zones (hydrological response
units).  It applies the equations related to some processes (for example, interception)
separately for each zone.  Consequently, parameters such as the interception capacity
|IcMax| and sequences such as the actual interception storage |Ic| are 1-dimensional.
Each entry represents the value of a different zone.

In contrast to the original HBV96 model, |hland| allows defining individual parameter
values for each zone, which provides flexibility but might be a little overwhelming in
many use cases.  Hence, we also support the original HBV96-distinction into the zone
types "field", "forest", "glacier", and "ilake" (internal lake).  In addition, we allow
the designation of the type "sealed" (sealed area).  Parameter "ZoneType" specifies the
type of each response unit via one of the integer constants |FIELD|, |FOREST|,
|GLACIER|, |ILAKE|, and |SEALED|. By performing a wildcard import, these constants
become available in your local namespace:

>>> from hydpy.models.hland import *
>>> FIELD, FOREST, GLACIER, ILAKE, SEALED
(1, 2, 3, 4, 5)
"""
from hydpy.core import parametertools

FIELD = parametertools.IntConstant(1)
"""Constant for the zone type `field`."""
FOREST = parametertools.IntConstant(2)
"""Constant for the zone type `forest`."""
GLACIER = parametertools.IntConstant(3)
"""Constant for the zone type `glacier`."""
ILAKE = parametertools.IntConstant(4)
"""Constant for the zone type `internal lake`."""
SEALED = parametertools.IntConstant(5)
"""Constant for the zone type `sealed surface`."""

CONSTANTS = parametertools.Constants()
"""Dictionary containing all constants defined by HydPy-H-Land."""

__all__ = [
    "FIELD",
    "FOREST",
    "GLACIER",
    "ILAKE",
    "SEALED",
]
