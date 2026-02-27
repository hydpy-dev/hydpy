# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools

# ...from wland
from hydpy.models.wland import wland_sequences


class PC(sequencetools.FluxSequence):
    """Corrected precipitation [mm/T]."""

    NDIM = 0
    NUMERIC = True
    SPAN = (0.0, None)


class PE(wland_sequences.FluxSequence1DComplete):
    """Potential evaporation from the interception and the surface water storage
    [mm/T]."""

    NDIM = 1
    NUMERIC = False


class PET(wland_sequences.FluxSequence1DSoil):
    """Potential evapotranspiration from the vadose zone [mm/T]."""

    NDIM = 1
    NUMERIC = False


class TF(wland_sequences.FluxSequence1DLand):
    """Total amount of throughfall [mm/T]."""

    NDIM = 1
    NUMERIC = True
    SPAN = (0.0, None)


class EI(wland_sequences.FluxSequence1DLand):
    """Interception evaporation [mm/T]."""

    NDIM = 1
    NUMERIC = True
    SPAN = (0.0, None)


class RF(wland_sequences.FluxSequence1DLand):
    """Rainfall (or, more concrete, the liquid amount of throughfall) [mm/T]."""

    NDIM = 1
    NUMERIC = True
    SPAN = (0.0, None)


class SF(wland_sequences.FluxSequence1DLand):
    """Snowfall (or, more concrete, the frozen amount of throughfall) [mm/T]."""

    NDIM = 1
    NUMERIC = True
    SPAN = (0.0, None)


class PM(wland_sequences.FluxSequence1DLand):
    """Potential snowmelt [mm/T]."""

    NDIM = 1
    NUMERIC = False
    SPAN = (0.0, None)


class AM(wland_sequences.FluxSequence1DLand):
    """Actual snowmelt [mm/T]."""

    NDIM = 1
    NUMERIC = True
    SPAN = (0.0, None)


class PS(sequencetools.FluxSequence):
    """Precipitation that enters the surface water reservoir [mm/T]."""

    NDIM = 0
    NUMERIC = True
    SPAN = (0.0, None)


class PVE(sequencetools.FluxSequence):
    """Rainfall (and snowmelt) entering the vadose zone in the elevated region
    [mm/T]."""

    NDIM = 0
    NUMERIC = True
    SPAN = (0.0, None)


class PV(sequencetools.FluxSequence):
    """Rainfall (and snowmelt) entering the vadose zone in the lowland region [mm/T]."""

    NDIM = 0
    NUMERIC = True
    SPAN = (0.0, None)


class PQ(sequencetools.FluxSequence):
    """Rainfall (and snowmelt) entering the quickflow reservoir [mm/T]."""

    NDIM = 0
    NUMERIC = True
    SPAN = (0.0, None)


class ETVE(sequencetools.FluxSequence):
    """Actual evapotranspiration from the vadose zone in the elevated region [mm/T]."""

    NDIM = 0
    NUMERIC = True
    SPAN = (None, None)


class ETV(sequencetools.FluxSequence):
    """Actual evapotranspiration from the vadose zone in the lowland region [mm/T]."""

    NDIM = 0
    NUMERIC = True
    SPAN = (None, None)


class ES(sequencetools.FluxSequence):
    """Actual evaporation from the surface water  [mm/T]."""

    NDIM = 0
    NUMERIC = True
    SPAN = (None, None)


class ET(sequencetools.FluxSequence):
    """Total actual evapotranspiration [mm/T]."""

    NDIM = 0
    NUMERIC = False
    SPAN = (None, None)


class GR(sequencetools.FluxSequence):
    """Groundwater recharge in the elevated region [mm/T]."""

    NDIM = 0
    NUMERIC = True
    SPAN = (None, None)


class FXS(sequencetools.FluxSequence):
    """Surface water supply/extraction (normalised to |ASR|) [mm/T]."""

    NDIM = 0
    NUMERIC = True
    SPAN = (0.0, None)


class FXG(sequencetools.FluxSequence):
    """Seepage/extraction (normalised to |ALR|) [mm/T]."""

    NDIM = 0
    NUMERIC = True
    SPAN = (0.0, None)


class CDG(sequencetools.FluxSequence):
    """Change in the groundwater depth due to percolation and capillary rise [mm/T]."""

    NDIM = 0
    NUMERIC = True
    SPAN = (None, None)


class FGSE(sequencetools.FluxSequence):
    """Groundwater flow between the elevated and the lowland region [mm/T]."""

    NDIM = 0
    NUMERIC = True
    SPAN = (None, None)


class FGS(sequencetools.FluxSequence):
    """Groundwater drainage/surface water infiltration [mm/T]."""

    NDIM = 0
    NUMERIC = True
    SPAN = (None, None)


class FQS(sequencetools.FluxSequence):
    """Quickflow [mm/T]."""

    NDIM = 0
    NUMERIC = True
    SPAN = (0.0, None)


class RH(sequencetools.FluxSequence):
    """Runoff height [mm/T]."""

    NDIM = 0
    NUMERIC = True
    SPAN = (0.0, None)


class R(sequencetools.FluxSequence):
    """Runoff [m³/s]."""

    NDIM = 0
    NUMERIC = False
    SPAN = (0.0, None)
