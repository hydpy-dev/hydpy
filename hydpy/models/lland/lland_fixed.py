# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring
"""
.. _`Wikipedia page on latent heat`: https://en.wikipedia.org/wiki/Latent_heat
"""
# import...
# ...from HydPy
from hydpy.core import parametertools


class CPWasser(parametertools.FixedParameter):
    """Spezifische Wärmekapazität von Wasser (specific heat capacity of water)
    [MJ/mm/K]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)
    INIT = 0.0041868


class CPEis(parametertools.FixedParameter):
    """Spezifische Wärmekapazität von Eis bei 0 °C (specific heat capacity of
    ice at a temperature of 0 °C) [MJ/mm/K]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)
    INIT = 0.00209


class RSchmelz(parametertools.FixedParameter):
    """Spezifische Schmelzwärme von Wasser (specific melt heat of water)
    [MJ/mm]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)
    INIT = 0.334


class Pi(parametertools.FixedParameter):
    """π [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 3.141592653589793


class Z(parametertools.FixedParameter):
    """Halbe Mächtigkeit der in der Temperaturmodellierung betrachteten
    Bodensäule (the half thickness of the surface soil layer relevant for
    modelling soil temperature) [m]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 0.1


class BoWa2Z(parametertools.FixedParameter):
    """Bodenwassergehalt der Bodenschicht bis zu einer Tiefe 2z (soil water
    content of the soil layer down two a depth of 2z) [mm]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0, None)
    INIT = 80.


class LambdaG(parametertools.FixedParameter):
    """Wärmeleitfähigkeit des Bodens (thermal conductivity of the top soil
    layer) [MJ/m/K/T]."""
    NDIM, TYPE, TIME, SPAN = 0, float, True, (0.0, None)
    INIT = 0.05184


class Sigma(parametertools.FixedParameter):
    """Stefan-Boltzmann-Konstante (Stefan-Boltzmann constant) [MJ/m²/K/d]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 4.89888e-09


class RDryAir(parametertools.FixedParameter):
    """Gaskonstante für trockene Luft (gas constant for dry air) [MJ/kg/K]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 0.287058


class RWaterVapour(parametertools.FixedParameter):
    """Gaskonstante für Wasserdampf (gas constant for water vapour)
    [MJ/kg/K]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 0.461495


class LW(parametertools.FixedParameter):
    """Latente Verdunstungswärme bei 15°C (heat of condensation at at
    temperature of 15°C) [MJ/m²/mm]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 2.4624


class LWE(parametertools.FixedParameter):
    """Mittlere latente Verdunstungswärme für Wasser und Eis (average heat
    of condensation for water and ice) [MJ/m²/mm].

    Following the equations given on the `Wikipedia page on latent heat`_,
    we calculate the latent heat of water and the latent heat of sublimation
    both at a temperature of 0°C...

    >>> from hydpy import round_
    >>> t = 0.0
    >>> round_((2500.8-2.36*t+0.0016*t**2-0.00006*t**3)/1000)
    2.5008
    >>> round_((2834.1-0.29*t-0.004*t**2)/1000)
    2.8341

    ... and use their average as the default value for parameter |LWE|:

    >>> round_((2.8341+2.5008)/2)
    2.66745
    >>> from hydpy.models.lland.lland_fixed import LWE
    >>> round_(LWE.INIT)
    2.66745
    """
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 2.66745


class CPLuft(parametertools.FixedParameter):
    """Spezifische Wärmekapazität Luft (heat of condensation for a
    water temperature of 15°C) [MJ/kg/K]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 0.001005


class Psy(parametertools.FixedParameter):
    """Psychrometerkonstante bei Normaldruck (psychrometric constant at
    normal pressure) [kPa/°C]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 0.0655


class PsyInv(parametertools.FixedParameter):
    """Kehrwert der Psychrometerkonstante über Schnee und Eis bei 0°C
    (inverse psychrometric constant for ice and snow at 0°C) [°C/kPa]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 17.6


class Z0(parametertools.FixedParameter):
    """Rauhigkeitslänge für Wiese (roughness length for short grass) [m]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 0.003


class Sol(parametertools.FixedParameter):
    """Solarkonstante (solar constant) [m]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 118.1088


class FrAtm(parametertools.FixedParameter):
    """Empirischer Faktor zur Berechnung der atmosphärischen Gegenstrahlung
     (empirical factor for the calculation of atmospheric radiation) [-]"""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)
    INIT = 1.28


class CG(parametertools.FixedParameter):
    """Volumetrische Wärmekapazität des Bodens (volumetric heat capacity of
    soil) [MJ/m³/°C]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)
    INIT = 1.5
