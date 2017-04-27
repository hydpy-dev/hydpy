# -*- coding: utf-8 -*-
"""ToDo

>>> from hydpy.models.lland import *
>>> (SIED_D, SIED_L, VERS, ACKER, WEINB, OBSTB, BODEN, GLETS, GRUE_I,
...  FEUCHT, GRUE_E, BAUMB, NADELW, LAUBW, MISCHW, WASSER)
(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16)
"""

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
NADELW= 13
"""Constant for `Nadelwald` (coniferous forest)."""
LAUBW = 14
"""Constant for `Laubwald` (deciduous forest)."""
MISCHW = 15
"""Constant for `Mischwald` (mixed forest)."""
WASSER = 16
"""Constant for `Wasser` (water)."""
CONSTANTS = {key: value for key, value in locals().items()
             if (key.isupper() and isinstance(value, int))}
"""Dictionary containing all constants defined by HydPy-L-Land."""