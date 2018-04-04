# -*- coding: utf-8 -*-
"""The HydPy-L-Land model (|lland|) allows for the subdivision of subbasins
into hydrological response units (hru).  Some processes, e.g. interception,
are calculated seperately for each zone.  This is why some parameters (e.g.
the usable field capacity |NFk|) and some sequences (e.g. the actual soil
water storage |BoWa|) are 1-dimensional.  Each entry represents the value
of a different hru.

In contrasts to the original LARSIM model, the HydPy-L-Land model allows for
arbitrary definitions of units.  Nevertheless, the original distinction
in accordance with sixteen different landuse types is still supported.  The
parameter |Lnk| defines which entry of e.g. parameter |NFk| is related to
which land use type via integer values.  Note that for the units of the most
land use types, the same equations are applied. Only units of type |VERS|,
|WASSER|, |FLUSS|, and |SEE| are partly connected to different process
equations.

For comprehensibility, this module introduces the relevant integer constants.
Through performing a wildcard import

>>> from hydpy.models.lland import *

these are available in your local namespace:

>>> (SIED_D, SIED_L, VERS, ACKER, WEINB, OBSTB, BODEN, GLETS, GRUE_I,
...  FEUCHT, GRUE_E, BAUMB, NADELW, LAUBW, MISCHW, WASSER, FLUSS, SEE)
(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18)
"""
from hydpy.core import parametertools

SIED_D = 1
"""Constant for `Siedlung, dicht` (settlement, dense)."""
SIED_L = 2
"""Constant for `Siedlung, locker` (settlement, light)."""
VERS = 3
"""Constant for `versiegelt` (sealed)."""
ACKER = 4
"""Constant for `Acker` (fields)."""
WEINB = 5
"""Constant for `Weinbau` (viniculture)."""
OBSTB = 6
"""Constant for `Obstbau` (intensive orchards)."""
BODEN = 7
"""Constant for `unbewachsener Boden` (unsealed soil, not overgrown)."""
GLETS = 8
"""Constant for `Gletscher` (`glacier`)."""
GRUE_I = 9
"""Constant for `Grünland, intensiv` (intensive pasture)."""
FEUCHT = 10
"""Constant for `Feuchtflächen` (wetlands)."""
GRUE_E = 11
"""Constant for `Grünland, extensiv` (extensive pasture)."""
BAUMB = 12
"""Constant for `lockerer Baumbestand` (sparsely populated forest)."""
NADELW = 13
"""Constant for `Nadelwald` (coniferous forest)."""
LAUBW = 14
"""Constant for `Laubwald` (deciduous forest)."""
MISCHW = 15
"""Constant for `Mischwald` (mixed forest)."""
WASSER = 16
"""Constant for `Wasser` (water areas).

    **This constant is deprecated. Use constant `FLUSS` instead.**
"""
FLUSS = 17
"""Constant for `Fluss` (river surface)."""
SEE = 18
"""Constant for `See` (lake surface)."""

CONSTANTS = parametertools.Constants()
"""Dictionary containing all constants defined by HydPy-L-Land."""

# Make only the constants available on wildcard-imports.
__all__ = list(CONSTANTS.keys())
