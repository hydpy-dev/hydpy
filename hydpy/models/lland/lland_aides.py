# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class SNRatio(sequencetools.AideSequence):
    """Ratio of frozen precipitation to total precipitation [-]."""

    NDIM = 1
    NUMERIC = False


class RLAtm(sequencetools.AideSequence):
    """Atmosphärische Gegenstrahlung (longwave radiation emitted from the
    atmosphere) [W/m²]."""

    NDIM = 1
    NUMERIC = False


class TempS(sequencetools.AideSequence):
    """Temperatur der Schneedecke (temperature of the snow layer) [°C].

    Note that the value of sequence |TempS| is |numpy.nan| for snow-free
    surfaces.
    """

    NDIM = 1
    NUMERIC = False


class TempSInz(sequencetools.AideSequence):
    """Temperatur des interzepierten Schnees (temperature of the intercepted snow) [°C].

    Note that the value of sequence |TempSInz| is |numpy.nan| for missing intercepted
    snow.
    """

    NDIM = 1
    NUMERIC = False
