# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools
from hydpy.models.evap import evap_sequences


class CloudCoverage(sequencetools.StateSequence):
    """Degree of cloud coverage [-]."""

    NDIM, NUMERIC, SPAN = 0, False, (0.0, 1.0)


class SoilResistance(evap_sequences.StateSequence1D):
    """Actual soil surface resistance [s/m]."""

    SPAN = (0.0, None)
