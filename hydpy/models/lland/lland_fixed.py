# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

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


class LambdaG(parametertools.FixedParameter):
    """Wärmeleitfähigkeit des Bodens (thermal conductivity of the top soil
    layer) [MJ/m/K/T]."""
    NDIM, TYPE, TIME, SPAN = 0, float, True, (0.0, None)
    INIT = 0.05184


class Sigma(parametertools.FixedParameter):
    """Stefan-Boltzmann-Konstante (Stefan-Boltzmann constant) [MJ/m²/K/T]."""
    NDIM, TYPE, TIME, SPAN = 0, float, True, (0.0, None)
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


class L(parametertools.FixedParameter):
    """Latente Verdunstungswärme bei 15°C (specific heat capacity of air)
    [MJ/m²/mm]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 2.4624


class CPLuft(parametertools.FixedParameter):
    """Spezifische Wärmekapazität Luft (heat of condensation for a
    water temperature of 15°C) [MJ/kg/K]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 0.001005
