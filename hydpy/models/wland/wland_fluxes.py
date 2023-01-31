# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class PC(sequencetools.FluxSequence):
    """Corrected precipitation [mm/T]."""

    NDIM, NUMERIC, SPAN = 0, True, (0.0, None)


class PETL(sequencetools.FluxSequence):
    """Adjusted potential evapotranspiration of the land areas [mm/T]."""

    NDIM, NUMERIC, SPAN = 1, True, (0.0, None)


class PES(sequencetools.FluxSequence):
    """Adjusted potential evaporation of the surface water area [mm/T]."""

    NDIM, NUMERIC, SPAN = 0, True, (0.0, None)


class TF(sequencetools.FluxSequence):
    """Total amount of throughfall [mm/T]."""

    NDIM, NUMERIC, SPAN = 1, True, (0.0, None)


class EI(sequencetools.FluxSequence):
    """Interception evaporation [mm/T]."""

    NDIM, NUMERIC, SPAN = 1, True, (0.0, None)


class RF(sequencetools.FluxSequence):
    """Rainfall (or, more concrete, the liquid amount of throughfall) [mm/T]."""

    NDIM, NUMERIC, SPAN = 1, True, (0.0, None)


class SF(sequencetools.FluxSequence):
    """Snowfall (or, more concrete, the frozen amount of throughfall) [mm/T]."""

    NDIM, NUMERIC, SPAN = 1, True, (0.0, None)


class PM(sequencetools.FluxSequence):
    """Potential snowmelt [mm/T]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)


class AM(sequencetools.FluxSequence):
    """Actual snowmelt [mm/T]."""

    NDIM, NUMERIC, SPAN = 1, True, (0.0, None)


class PS(sequencetools.FluxSequence):
    """Precipitation entering the surface water reservoir [mm/T]."""

    NDIM, NUMERIC, SPAN = 0, True, (0.0, None)


class PV(sequencetools.FluxSequence):
    """Rainfall (and snowmelt) entering the vadose zone [mm/T]."""

    NDIM, NUMERIC, SPAN = 0, True, (0.0, None)


class PQ(sequencetools.FluxSequence):
    """Rainfall (and snowmelt) entering the quickflow reservoir [mm/T]."""

    NDIM, NUMERIC, SPAN = 0, True, (0.0, None)


class ETV(sequencetools.FluxSequence):
    """Actual evapotranspiration from the vadose zone [mm/T]."""

    NDIM, NUMERIC, SPAN = 0, True, (None, None)


class ES(sequencetools.FluxSequence):
    """Actual evaporation from the surface water  [mm/T]."""

    NDIM, NUMERIC, SPAN = 0, True, (None, None)


class ET(sequencetools.FluxSequence):
    """Total actual evapotranspiration [mm/T]."""

    NDIM, NUMERIC, SPAN = 0, False, (None, None)


class FXS(sequencetools.FluxSequence):
    """Surface water supply/extraction (normalised to |AS_|) [mm/T]."""

    NDIM, NUMERIC, SPAN = 0, True, (0.0, None)


class FXG(sequencetools.FluxSequence):
    """Seepage/extraction (normalised to |AL|) [mm/T]."""

    NDIM, NUMERIC, SPAN = 0, True, (0.0, None)


class CDG(sequencetools.FluxSequence):
    """Change in the groundwater depth due to percolation and capillary rise [mm/T]."""

    NDIM, NUMERIC, SPAN = 0, True, (None, None)


class FGS(sequencetools.FluxSequence):
    """Groundwater drainage/surface water infiltration [mm/T]."""

    NDIM, NUMERIC, SPAN = 0, True, (None, None)


class FQS(sequencetools.FluxSequence):
    """Quickflow [mm/T]."""

    NDIM, NUMERIC, SPAN = 0, True, (0.0, None)


class RH(sequencetools.FluxSequence):
    """Runoff height [mm/T]."""

    NDIM, NUMERIC, SPAN = 0, True, (0.0, None)


class R(sequencetools.FluxSequence):
    """Runoff [m³/s]."""

    NDIM, NUMERIC, SPAN = 0, False, (0.0, None)
