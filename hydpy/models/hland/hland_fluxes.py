# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools

# ...from hland
from hydpy.models.hland import hland_masks
from hydpy.models.hland import hland_sequences


class PC(hland_sequences.Flux1DSequence):
    """Corrected precipitation [mm/T]."""

    mask = hland_masks.Complete()


class EI(hland_sequences.Flux1DSequence):
    """Interception evaporation [mm/T]."""

    mask = hland_masks.Interception()


class TF(hland_sequences.Flux1DSequence):
    """Throughfall [mm/T]."""

    mask = hland_masks.Interception()


class SPL(hland_sequences.Flux1DSequence):
    """Subbasin-internal redistribution loss of the snow's ice content [mm/T]."""

    mask = hland_masks.Snow()


class WCL(hland_sequences.Flux1DSequence):
    """Subbasin-internal redistribution loss of the snow's water content [mm/T]."""

    mask = hland_masks.Snow()


class SPG(hland_sequences.Flux1DSequence):
    """Subbasin-internal redistribution gain of the snow's ice content [mm/T]."""

    mask = hland_masks.Snow()


class WCG(hland_sequences.Flux1DSequence):
    """Subbasin-internal redistribution gain of the snow's water content [mm/T]."""

    mask = hland_masks.Snow()


class GlMelt(hland_sequences.Flux1DSequence):
    """Glacier melt [mm/T]."""

    mask = hland_masks.Glacier()


class Melt(hland_sequences.Flux2DSequence):
    """Actual melting of frozen water stored in the snow layer [mm/T]."""

    mask = hland_masks.Snow()


class Refr(hland_sequences.Flux2DSequence):
    """Actual (re)freezing of liquid water stored in the snow layer [mm/T]."""

    mask = hland_masks.Snow()


class In_(hland_sequences.Flux1DSequence):
    """Snow module release/soil module inflow [mm/T]."""

    mask = hland_masks.Snow()


class R(hland_sequences.Flux1DSequence):
    """Effective soil response [mm/T].

    Note that PREVAH uses the abbreviation `DSUZ` instead of the HBV96 abbreviation `R`.
    """

    mask = hland_masks.Soil()


class SR(hland_sequences.Flux1DSequence):
    """Sealed surface runoff [mm/T]."""

    mask = hland_masks.Sealed()


class EA(hland_sequences.Flux1DSequence):
    """Actual soil evaporation [mm/T]."""

    mask = hland_masks.Soil()


class CFPot(hland_sequences.Flux1DSequence):
    """Potential capillary flow [mm/T]."""

    mask = hland_masks.Soil()


class CF(hland_sequences.Flux1DSequence):
    """Actual capillary flow [mm/T]."""

    mask = hland_masks.Soil()


class InUZ(sequencetools.FluxSequence):
    """Inflow to the upper zone layer [mm/T]."""

    NDIM, NUMERIC = 0, False


class Perc(sequencetools.FluxSequence):
    """Percolation from the upper to the lower zone layer [mm/T]."""

    NDIM, NUMERIC = 0, False


class DP(hland_sequences.Flux1DSequence):
    """Deep percolation rate [mm/T].

    Note that PREVAH uses the abbreviation `Perc`, which is also the abbreviation used
    by HBV96.  However, |Perc| is 0-dimensional while |DP| is 1-dimensional, which is
    why we need to define separate sequence classes with different names.
    """

    mask = hland_masks.UpperZone()


class Q0(sequencetools.FluxSequence):
    """Outflow from the upper zone layer [mm/T]."""

    NDIM, NUMERIC = 0, False


class QVs1(hland_sequences.Flux1DSequence):
    """Percolation from the surface flow reservoir [mm/T].

    Note that COSERO uses the abbreviation `QVS1ZON` instead.
    """

    mask = hland_masks.UpperZone()


class QAb1(hland_sequences.Flux1DSequence):
    """Surface flow [mm/T].

    Note that COSERO uses the abbreviation `QAB1ZON` instead.
    """

    mask = hland_masks.UpperZone()


class QVs2(hland_sequences.Flux1DSequence):
    """Percolation from the interflow reservoir [mm/T].

    Note that COSERO uses the abbreviation `QVS2ZON` instead.
    """

    mask = hland_masks.UpperZone()


class QAb2(hland_sequences.Flux1DSequence):
    """Interflow [mm/T].

    Note that COSERO uses the abbreviation `QAB2ZON` instead.
    """

    mask = hland_masks.UpperZone()


class EL(hland_sequences.Flux1DSequence):
    """Actual lake evaporation [mm/T]."""

    mask = hland_masks.ILake()


class Q1(sequencetools.FluxSequence):
    """Outflow from the lower zone layer [mm/T]."""

    NDIM, NUMERIC = 0, False


class RS(hland_sequences.Flux1DSequence):
    """Surface runoff [mm/T]."""

    mask = hland_masks.UpperZone()


class RI(hland_sequences.Flux1DSequence):
    """Interflow [mm/T]."""

    mask = hland_masks.UpperZone()


class GR1(hland_sequences.Flux1DSequence):
    """Recharge into the fast response groundwater reservoir [mm/T]."""

    mask = hland_masks.UpperZone()


class RG1(hland_sequences.Flux1DSequence):
    """Discharge from the fast response groundwater reservoir [mm/T]."""

    mask = hland_masks.UpperZone()


class GR2(sequencetools.FluxSequence):
    """Recharge into the first-order slow response groundwater reservoir [mm/T]."""

    NDIM = 0
    NUMERIC = False


class RG2(sequencetools.FluxSequence):
    """Discharge from the first-order slow response groundwater reservoir [mm/T]."""

    NDIM = 0
    NUMERIC = False


class GR3(sequencetools.FluxSequence):
    """Recharge into the second-order slow response groundwater reservoir [mm/T]."""

    NDIM = 0
    NUMERIC = False


class RG3(sequencetools.FluxSequence):
    """Discharge from the second-order slow response groundwater reservoir [mm/T]."""

    NDIM = 0
    NUMERIC = False


class InRC(sequencetools.FluxSequence):
    """Input of the runoff concentration submodel [mm/T]."""

    NDIM = 0
    NUMERIC = False


class OutRC(sequencetools.FluxSequence):
    """Output of the runoff concentration submodel [mm/T]."""

    NDIM = 0
    NUMERIC = False


class RO(sequencetools.FluxSequence):
    """Sum of all flow components [mm/T]."""

    NDIM = 0
    NUMERIC = False


class RA(sequencetools.FluxSequence):
    """Actual abstraction from runoff [mm/T]."""

    NDIM = 0
    NUMERIC = False


class RT(sequencetools.FluxSequence):
    """Total model outflow [mm/T]."""

    NDIM = 0
    NUMERIC = False


class QT(sequencetools.FluxSequence):
    """Total model outflow [m³/s]."""

    NDIM = 0
    NUMERIC = False
