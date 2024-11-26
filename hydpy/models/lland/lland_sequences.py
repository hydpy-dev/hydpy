# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools

# ...from lland
from hydpy.models.lland import lland_derived


class Flux1DSequence(sequencetools.FluxSequence):
    """Base class for 1-dimensional flux subclasses that support
    aggregation with respect to |AbsFHRU|.

    All |Flux1DSequence| subclasses should stick to the mask |Complete|.

    The following example shows how subclass |NKor| works:

    >>> from hydpy.models.lland import *
    >>> parameterstep("1d")
    >>> nhru(4)
    >>> lnk(ACKER, GLETS, VERS, SEE)
    >>> derived.absfhru(10.0, 20.0, 30.0, 40.0)
    >>> fluxes.nkor(5.0, 2.0, 4.0, 1.0)
    >>> from hydpy import round_
    >>> round_(fluxes.nkor.average_values())
    2.5
    """

    DERIVEDPARAMETERS = (lland_derived.AbsFHRU,)

    @property
    def refweights(self):
        """Alias for the associated instance of |AbsFHRU| for calculating
        areal values."""
        return self.subseqs.seqs.model.parameters.derived.absfhru


class State1DSequence(sequencetools.StateSequence):
    """Base class for 1-dimensional state subclasses that support
    aggregation with respect to |AbsFHRU|.

    All |State1DSequence| subclasses must implement fitting mask objects
    individually.

    The following example shows how subclass |BoWa| works, which
    implements mask |Land|:

    >>> from hydpy.models.lland import *
    >>> parameterstep("1d")
    >>> nhru(4)
    >>> lnk(ACKER, GLETS, VERS, SEE)
    >>> wmax(100.0)
    >>> derived.absfhru(10.0, 20.0, 30.0, 40.0)
    >>> states.bowa(50.0, 20.0, 40.0, 10.0)
    >>> from hydpy import round_
    >>> round_(states.bowa.average_values())
    30.0
    """

    DERIVEDPARAMETERS = (lland_derived.AbsFHRU,)

    @property
    def refweights(self):
        """Alias for the associated instance of |AbsFHRU| for calculating
        areal values."""
        return self.subseqs.seqs.model.parameters.derived.absfhru
