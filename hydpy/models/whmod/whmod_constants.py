# -*- coding: utf-8 -*-

from hydpy.core import parametertools

GRAS = parametertools.IntConstant(1)
"""WHMod: 0"""
LAUBWALD = parametertools.IntConstant(2)
"""WHMod: 1"""
MAIS = parametertools.IntConstant(3)
"""WHMod: 2"""
NADELWALD = parametertools.IntConstant(4)
"""WHMod: 3"""
SOMMERWEIZEN = parametertools.IntConstant(5)
"""WHMod: 4"""
WINTERWEIZEN = parametertools.IntConstant(6)
"""WHMod: 5"""
ZUCKERRUEBEN = parametertools.IntConstant(7)
"""WHMod: 6"""
VERSIEGELT = parametertools.IntConstant(8)
"""WHMod: 7"""
WASSER = parametertools.IntConstant(9)
"""WHMod: 8"""

SAND = parametertools.IntConstant(10)
SAND_BINDIG = parametertools.IntConstant(11)
LEHM = parametertools.IntConstant(12)
TON = parametertools.IntConstant(13)
SCHLUFF = parametertools.IntConstant(14)
TORF = parametertools.IntConstant(15)


CONSTANTS = parametertools.Constants()
LANDUSE_CONSTANTS = parametertools.Constants(
    **{key: value for key, value in CONSTANTS.items() if value <= WASSER}
)
SOIL_CONSTANTS = parametertools.Constants(
    **{key: value for key, value in CONSTANTS.items() if value >= SAND}
)

# Make only the constants available on wildcard-imports.
__all__ = list(CONSTANTS.keys())
