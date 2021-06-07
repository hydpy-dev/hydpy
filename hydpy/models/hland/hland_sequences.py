# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Factor1DSequence(sequencetools.FactorSequence):
    """Base class for 1-dimensional factor subclasses that support aggregation with
    respect to |ZoneArea|.

    All |Factor1DSequence| subclasses must implement fitting mask objects individually.

    The following example shows how the subclass |TC| works:

    >>> from hydpy.models.hland import *
    >>> parameterstep("1d")
    >>> nmbzones(5)
    >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, SEALED)
    >>> zonearea(10.0, 20.0, 30.0, 35.0, 5.0)
    >>> factors.tc(5.0, 2.0, 4.0, 1.0, 6.0)
    >>> from hydpy import round_
    >>> round_(factors.tc.average_values())
    2.75
    """

    NDIM = 1

    @property
    def refweights(self):
        """Alias for the associated instance of |ZoneArea| for calculating areal
        values."""
        return self.subseqs.seqs.model.parameters.control.zonearea


class Flux1DSequence(sequencetools.FluxSequence):
    """Base class for 1-dimensional flux subclasses that support aggregation with
    respect to |ZoneArea|.

    All |Flux1DSequence| subclasses must implement fitting mask objects individually.

    The following example shows how the subclass |PC| works:

    >>> from hydpy.models.hland import *
    >>> parameterstep("1d")
    >>> nmbzones(5)
    >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, SEALED)
    >>> zonearea(10.0, 20.0, 30.0, 35.0, 5.0)
    >>> fluxes.pc(5.0, 2.0, 4.0, 1.0, 6.0)
    >>> from hydpy import round_
    >>> round_(fluxes.pc.average_values())
    2.75
    """

    @property
    def refweights(self):
        """Alias for the associated instance of |ZoneArea| for calculating areal
        values."""
        return self.subseqs.seqs.model.parameters.control.zonearea


class State1DSequence(sequencetools.StateSequence):
    """Base class for 1-dimensional state subclasses that support aggregation with
    respect to |ZoneArea|.

    All |State1DSequence| subclasses must implement fitting mask objects individually.

    The following example shows how subclass |SM| works, which implements mask |Soil|:

    >>> from hydpy.models.hland import *
    >>> parameterstep("1d")
    >>> nmbzones(4)
    >>> zonetype(FIELD, FOREST, GLACIER, ILAKE)
    >>> zonearea(10.0, 20.0, 30.0, 40.0)
    >>> fc(100.0)
    >>> states.sm(50.0, 20.0, 40.0, 10.0)
    >>> from hydpy import round_
    >>> round_(states.sm.average_values())
    30.0
    """

    @property
    def refweights(self):
        """Alias for the associated instance of |ZoneArea| for calculating
        areal values."""
        return self.subseqs.seqs.model.parameters.control.zonearea
