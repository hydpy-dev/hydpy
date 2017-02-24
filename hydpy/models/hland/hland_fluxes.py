# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from ...framework import sequencetools


class TMean(sequencetools.FluxSequence):
    """Mean subbasin temperature [°C]."""
    NDIM, NUMERIC = 0, False

class TC(sequencetools.FluxSequence):
    """Corrected temperature [°C]."""
    NDIM, NUMERIC = 1, False

class FracRain(sequencetools.FluxSequence):
    """Fraction rainfall / total precipitation [-]."""
    NDIM, NUMERIC = 1, False

class RfC(sequencetools.FluxSequence):
    """Actual precipitation correction related to liquid precipitation [-]."""
    NDIM, NUMERIC = 1, False

class SfC(sequencetools.FluxSequence):
    """Actual precipitation correction related to frozen precipitation [-]."""
    NDIM, NUMERIC = 1, False

class PC(sequencetools.FluxSequence):
    """Corrected precipitation [mm]."""
    NDIM, NUMERIC = 1, False

class EP(sequencetools.FluxSequence):
    """Potential evaporation [mm]."""
    NDIM, NUMERIC = 1, False

class EPC(sequencetools.FluxSequence):
    """Corrected potential evaporation [mm]."""
    NDIM, NUMERIC = 1, False

class EI(sequencetools.FluxSequence):
    """Interception evaporation [mm]."""
    NDIM, NUMERIC = 1, False

class TF(sequencetools.FluxSequence):
    """Throughfall [mm]."""
    NDIM, NUMERIC = 1, False

class TFWat(sequencetools.FluxSequence):
    """Liquid throughfall [mm]."""
    NDIM, NUMERIC = 1, False

class TFIce(sequencetools.FluxSequence):
    """Frozen throughfall [mm]."""
    NDIM, NUMERIC = 1, False

class GlMelt(sequencetools.FluxSequence):
    """Glacier melt [mm]."""
    NDIM, NUMERIC = 1, False

class MeltPot(sequencetools.FluxSequence):
    """Potential melting of frozen water stored in the snow layer [mm]."""
    NDIM, NUMERIC = 1, False

class Melt(sequencetools.FluxSequence):
    """Actual melting of frozen water stored in the snow layer [mm]."""
    NDIM, NUMERIC = 1, False

class RefrPot(sequencetools.FluxSequence):
    """Potential (re)freezing of liquid water stored in the snow layer [mm]."""
    NDIM, NUMERIC = 1, False

class Refr(sequencetools.FluxSequence):
    """Actual (re)freezing of liquid water stored in the snow layer [mm]."""
    NDIM, NUMERIC = 1, False

class In_(sequencetools.FluxSequence):
    """Snow module release / soil module inflow [mm]."""
    NDIM, NUMERIC = 1, False

class R(sequencetools.FluxSequence):
    """Effective soil response [mm]."""
    NDIM, NUMERIC = 1, False

class EA(sequencetools.FluxSequence):
    """Actual soil evaporation [mm]."""
    NDIM, NUMERIC = 1, False

class CFPot(sequencetools.FluxSequence):
    """Potential capillary flow [mm]."""
    NDIM, NUMERIC = 1, False

class CF(sequencetools.FluxSequence):
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
    """Flux sequences of the hland model."""
    _SEQCLASSES = (TMean, TC, FracRain, RfC, SfC, PC, EP, EPC, EI, TF, TFWat,
                   TFIce, GlMelt, MeltPot, Melt, RefrPot, Refr, In_, R,
                   EA, CFPot, CF, Perc, ContriArea, InUZ, Q0, EL, Q1,
                   InUH, OutUH, QT)
