"""
.. _`Wikipedia page on latent heat`: https://en.wikipedia.org/wiki/Latent_heat
"""

# import...
# ...from HydPy
from hydpy.core import parametertools
from hydpy.core.typingtools import *


class CPWasser(parametertools.FixedParameter):
    """Spezifische Wärmekapazität von Wasser (specific heat capacity of water)
    [WT/kg/K]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    TIME = False
    SPAN = (0.0, None)
    INIT = 0.04845833333333333


class CPEis(parametertools.FixedParameter):
    """Spezifische Wärmekapazität von Eis bei 0 °C (specific heat capacity of ice at a
    temperature of 0 °C) [WT/kg/K]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    TIME = False
    SPAN = (0.0, None)
    INIT = 0.024189814814814813


class RSchmelz(parametertools.FixedParameter):
    """Spezifische Schmelzwärme von Wasser (specific melt heat of water) [WT/kg]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    TIME = False
    SPAN = (0.0, None)
    INIT = 3.865740740740741


class Pi(parametertools.FixedParameter):
    """π [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, None)
    INIT = 3.141592653589793


class Z(parametertools.FixedParameter):
    """Halbe Mächtigkeit der in der Temperaturmodellierung betrachteten Bodensäule (the
    half thickness of the surface soil layer relevant for modelling soil temperature)
    [m]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, None)
    INIT = 0.1


class BoWa2Z(parametertools.FixedParameter):
    """Bodenwassergehalt der Bodenschicht bis zu einer Tiefe 2z (soil water content of
    the soil layer down two a depth of 2z) [mm]."""

    NDIM: Final[Literal[1]] = 1
    TYPE: Final = float
    SPAN = (0, None)
    INIT = 80.0


class LambdaG(parametertools.FixedParameter):
    """Wärmeleitfähigkeit des Bodens (thermal conductivity of the top soil layer)
    [W/m/K]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, None)
    INIT = 0.6


class Sigma(parametertools.FixedParameter):
    """Stefan-Boltzmann-Konstante (Stefan-Boltzmann constant) [W/m²/K]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, None)
    INIT = 5.67e-08


class LWE(parametertools.FixedParameter):
    """Mittlere latente Verdunstungswärme für Wasser und Eis (average heat of
    condensation for water and ice) [WT/kg].

    Following the equations given on the `Wikipedia page on latent heat`_, we calculate
    the latent heat of water and the latent heat of sublimation both at a temperature
    of 0°C...

    >>> from hydpy import round_
    >>> t = 0.0
    >>> round_((2500.8-2.36*t+0.0016*t**2-0.00006*t**3)*1000/60/60/24)
    28.944444
    >>> round_((2834.1-0.29*t-0.004*t**2)*1000/60/60/24)
    32.802083

    ... and use their average as the default value for parameter |LWE|:

    >>> round_((28.944444+32.802083)/2)
    30.873264
    >>> from hydpy.models.lland.lland_fixed import LWE
    >>> round_(LWE.INIT)
    30.873264
    """

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    TIME = False
    SPAN = (0.0, None)
    INIT = 30.87326388888889


class PsyInv(parametertools.FixedParameter):
    """Kehrwert der Psychrometerkonstante über Schnee und Eis bei 0°C (inverse
    psychrometric constant for ice and snow at 0°C) [K/hPa]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, None)
    INIT = 1.76


class Z0(parametertools.FixedParameter):
    """Rauhigkeitslänge für Wiese (roughness length for short grass) [m]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, None)
    INIT = 0.003


class FrAtm(parametertools.FixedParameter):
    """Empirischer Faktor zur Berechnung der atmosphärischen Gegenstrahlung (empirical
    factor for the calculation of atmospheric radiation) [-]"""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, None)
    INIT = 1.28


class CG(parametertools.FixedParameter):
    """Volumetrische Wärmekapazität des Bodens (volumetric heat capacity of soil)
    [WT/m³/K]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    TIME = False
    INIT = 17.36111111111111
