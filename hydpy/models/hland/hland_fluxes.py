# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
# ...from hland
from hydpy.models.hland import hland_sequences


class TMean(hland_sequences.Flux1DSequence):
    """Mean subbasin temperature [°C]."""
    NDIM, NUMERIC = 0, False


class TC(hland_sequences.Flux1DSequence):
    """Corrected temperature [°C]."""
    NDIM, NUMERIC = 1, False


class FracRain(hland_sequences.Flux1DSequence):
    """Fraction rainfall / total precipitation [-]."""
    NDIM, NUMERIC = 1, False


class RfC(hland_sequences.Flux1DSequence):
    """Actual precipitation correction related to liquid precipitation [-]."""
    NDIM, NUMERIC = 1, False


class SfC(hland_sequences.Flux1DSequence):
    """Actual precipitation correction related to frozen precipitation [-]."""
    NDIM, NUMERIC = 1, False


class PC(hland_sequences.Flux1DSequence):
    """Corrected precipitation [mm]."""
    NDIM, NUMERIC = 1, False


class EP(hland_sequences.Flux1DSequence):
    """Potential evaporation [mm]."""
    NDIM, NUMERIC = 1, False


class EPC(hland_sequences.Flux1DSequence):
    """Corrected potential evaporation [mm]."""
    NDIM, NUMERIC = 1, False


class EI(hland_sequences.Flux1DSequence):
    """Interception evaporation [mm]."""
    NDIM, NUMERIC = 1, False


class TF(hland_sequences.Flux1DSequence):
    """Throughfall [mm]."""
    NDIM, NUMERIC = 1, False


class GlMelt(hland_sequences.Flux1DSequence):
    """Glacier melt [mm]."""
    NDIM, NUMERIC = 1, False


class Melt(hland_sequences.Flux1DSequence):
    """Actual melting of frozen water stored in the snow layer [mm]."""
    NDIM, NUMERIC = 1, False


class Refr(hland_sequences.Flux1DSequence):
    """Actual (re)freezing of liquid water stored in the snow layer [mm]."""
    NDIM, NUMERIC = 1, False


class In_(hland_sequences.Flux1DSequence):
    """Snow module release/soil module inflow [mm]."""
    NDIM, NUMERIC = 1, False


class R(hland_sequences.Flux1DSequence):
    """Effective soil response [mm]."""
    NDIM, NUMERIC = 1, False


class EA(hland_sequences.Flux1DSequence):
    """Actual soil evaporation [mm]."""
    NDIM, NUMERIC = 1, False


class CFPot(hland_sequences.Flux1DSequence):
    """Potential capillary flow [mm]."""
    NDIM, NUMERIC = 1, False


class CF(hland_sequences.Flux1DSequence):
    """Actual capillary flow [mm]."""
    NDIM, NUMERIC = 1, False


class ContriArea(sequencetools.FluxSequence):
    """Fraction of the `soil area` contributing to runoff generation [-]."""
    NDIM, NUMERIC = 0, False


class InUZ(sequencetools.FluxSequence):
    """Inflow to the upper zone layer [mm]."""
    NDIM, NUMERIC = 0, False


class Perc(sequencetools.FluxSequence):
    """Percolation from the upper to the lower zone layer [mm]."""
    NDIM, NUMERIC = 0, False


class Q0(sequencetools.FluxSequence):
    """Outflow from the upper zone layer [mm]."""
    NDIM, NUMERIC = 0, False


class EL(sequencetools.FluxSequence):
    """Actual lake evaporation [mm]."""
    NDIM, NUMERIC = 1, False


class Q1(sequencetools.FluxSequence):
    """Outflow from the lower zone layer [mm]."""
    NDIM, NUMERIC = 0, False


class InUH(sequencetools.FluxSequence):
    """Input of the triangle unit hydrograph  [m]."""
    NDIM, NUMERIC = 0, False


class OutUH(sequencetools.FluxSequence):
    """Output of the triangle unit hydrograph  [m]."""
    NDIM, NUMERIC = 0, False


class QT(sequencetools.FluxSequence):
    """Total model outflow [mm]."""
    NDIM, NUMERIC = 0, False


class FluxSequences(sequencetools.FluxSequences):
    """Flux sequences of the HydPy-H-Land model."""
    CLASSES = (TMean,
               TC,
               FracRain,
               RfC,
               SfC,
               PC,
               EP,
               EPC,
               EI,
               TF,
               GlMelt,
               Melt,
               Refr,
               In_,
               R,
               EA,
               CFPot,
               CF,
               Perc,
               ContriArea,
               InUZ,
               Q0,
               EL,
               Q1,
               InUH,
               OutUH,
               QT)
