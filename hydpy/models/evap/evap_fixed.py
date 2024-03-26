# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools


class StefanBoltzmannConstant(parametertools.FixedParameter):
    """Stefan-Boltzmann constant [W/m²/K]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 5.67e-08


class FactorCounterRadiation(parametertools.FixedParameter):
    """A factor for adjusting the atmospheric counter radiation [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 1.28


class GasConstantDryAir(parametertools.FixedParameter):
    """Gas constant for dry air [J/kg/K]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 287.058


class GasConstantWaterVapour(parametertools.FixedParameter):
    """Gas constant for water vapour [J/kg/K]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 461.495


class HeatCapacityAir(parametertools.FixedParameter):
    """Specific heat capacity of air [J/kg/K]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 1005.0


class HeatOfCondensation(parametertools.FixedParameter):
    """Latent condensation heat of water at 15°C [WT/kg]."""

    NDIM, TYPE, TIME, SPAN = 0, float, False, (0.0, None)
    INIT = 28.5


class RoughnessLengthGrass(parametertools.FixedParameter):
    """Roughness length for short grass [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 0.003


class PsychrometricConstant(parametertools.FixedParameter):
    """Psychrometric constant [hPa/K]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 0.655


class AerodynamicResistanceFactorMinimum(parametertools.FixedParameter):
    """The lowest allowed factor for calculating aerodynamic resistance [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 94.0
