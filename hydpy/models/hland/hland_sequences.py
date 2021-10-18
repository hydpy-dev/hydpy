# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from site-packages
import numpy

# ...from HydPy
from hydpy.core.typingtools import *
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
    >>> zonearea.values = 10.0, 20.0, 30.0, 35.0, 5.0
    >>> factors.tc(5.0, 2.0, 4.0, 1.0, 6.0)
    >>> from hydpy import round_
    >>> round_(factors.tc.average_values())
    2.75
    """

    NDIM = 1
    NUMERIC = False

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
    >>> zonearea.values = 10.0, 20.0, 30.0, 35.0, 5.0
    >>> fluxes.pc(5.0, 2.0, 4.0, 1.0, 6.0)
    >>> from hydpy import round_
    >>> round_(fluxes.pc.average_values())
    2.75
    """

    NDIM = 1
    NUMERIC = False

    @property
    def refweights(self):
        """Alias for the associated instance of |ZoneArea| for calculating areal
        values."""
        return self.subseqs.seqs.model.parameters.control.zonearea


class Flux2DSequence(sequencetools.FluxSequence):
    """Base class for 2-dimensional state subclasses that support aggregation with
    respect to |ZoneArea|.

    All |Flux2DSequence| subclasses must implement fitting mask objects individually.

    The following example shows how subclass |Melt| works, which implements mask |Snow|:

    >>> from hydpy.models.hland import *
    >>> parameterstep("1d")
    >>> nmbzones(5)
    >>> sclass(2)
    >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, SEALED)
    >>> zonearea.values = 10.0, 20.0, 30.0, 40.0, 60.0
    >>> fluxes.melt = [[40.0, 10.0, 30.0, nan, 0.0],
    ...                [60.0, 30.0, 50.0, nan, 20.0]]
    >>> from hydpy import round_
    >>> round_(fluxes.melt.average_values())
    22.5
    """

    NDIM = 2
    NUMERIC = False

    @property
    def refweights(self):
        """Alias for the associated instance of |ZoneArea| for calculating areal
        values."""
        return self.subseqs.seqs.model.parameters.control.zonearea

    @property
    def valuevector(self) -> Vector[float]:
        """Values of the individual zones; each entry is the average of the values of
        all snow classes of a specific zone.

        We take subclass |SP| as an example:

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> nmbzones(3)
        >>> sclass(2)
        >>> zonetype(FIELD)
        >>> zonearea.values = 1.0, 1.0, 1.0
        >>> states.sp = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
        >>> from hydpy import print_values
        >>> print_values(states.sp.valuevector)
        2.5, 3.5, 4.5

        The definition of |State2DSequence.valuevector| of |State2DSequence| allows
        applying method |Variable.average_values| like for the 1-dimensional
        zone-related sequences of |hland|:

        >>> print_values([states.sp.average_values()])
        3.5
        """
        return numpy.mean(self.value, axis=0)

    @property
    def seriesmatrix(self) -> Matrix[float]:
        """Time series of the values of the individual zones; each entry is the average
        of the values of all snow classes of a specific zone.

        We take subclass |SP| as an example:

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2000-01-05", "1d"
        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> nmbzones(3)
        >>> sclass(2)
        >>> zonetype(FIELD)
        >>> zonearea.values = 1.0, 1.0, 1.0
        >>> states.sp.activate_ram()
        >>> states.sp.series = [[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]],
        ...                     [[2.0, 3.0, 4.0], [5.0, 6.0, 7.0]],
        ...                     [[3.0, 4.0, 5.0], [6.0, 7.0, 8.0]],
        ...                     [[4.0, 5.0, 6.0], [7.0, 8.0, 9.0]]]
        >>> from hydpy import print_values
        >>> for values in states.sp.seriesmatrix:
        ...     print_values(values)
        2.5, 3.5, 4.5
        3.5, 4.5, 5.5
        4.5, 5.5, 6.5
        5.5, 6.5, 7.5

        The definition of |State2DSequence.seriesmatrix| of |State2DSequence| allows
        applying method |IOSequence.average_series| like for the 1-dimensional
        zone-related sequences of |hland|:

        >>> print_values(states.sp.average_series())
        3.5, 4.5, 5.5, 6.5
        """
        return numpy.mean(self.series, axis=1)


class State1DSequence(sequencetools.StateSequence):
    """Base class for 1-dimensional state subclasses that support aggregation with
    respect to |ZoneArea|.

    All |State1DSequence| subclasses must implement fitting mask objects individually.

    The following example shows how subclass |SM| works, which implements mask |Soil|:

    >>> from hydpy.models.hland import *
    >>> parameterstep("1d")
    >>> nmbzones(5)
    >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, SEALED)
    >>> zonearea.values = 10.0, 20.0, 30.0, 40.0, 50.0
    >>> fc(100.0)
    >>> states.sm = 50.0, 20.0, 40.0, 10.0, nan
    >>> from hydpy import round_
    >>> round_(states.sm.average_values())
    30.0
    """

    NDIM = 1
    NUMERIC = False

    @property
    def refweights(self):
        """Alias for the associated instance of |ZoneArea| for calculating
        areal values."""
        return self.subseqs.seqs.model.parameters.control.zonearea


class State2DSequence(sequencetools.StateSequence):
    """Base class for 2-dimensional state subclasses that support aggregation with
    respect to |ZoneArea|.

    All |State2DSequence| subclasses must implement fitting mask objects individually.

    The following example shows how subclass |SP| works, which implements mask |Snow|:

    >>> from hydpy.models.hland import *
    >>> parameterstep("1d")
    >>> nmbzones(5)
    >>> sclass(2)
    >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, SEALED)
    >>> zonearea.values = 10.0, 20.0, 30.0, 40.0, 60.0
    >>> states.sp = [[40.0, 10.0, 30.0, nan, 0.0],
    ...              [60.0, 30.0, 50.0, nan, 20.0]]
    >>> from hydpy import round_
    >>> round_(states.sp.average_values())
    22.5
    """

    NDIM = 2
    NUMERIC = False

    @property
    def refweights(self):
        """Alias for the associated instance of |ZoneArea| for calculating areal
        values."""
        return self.subseqs.seqs.model.parameters.control.zonearea

    @property
    def valuevector(self) -> Vector[float]:
        """Values of the individual zones; each entry is the average of the values of
        all snow classes of a specific zone.

        We take subclass |SP| as an example:

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> nmbzones(3)
        >>> sclass(2)
        >>> zonetype(FIELD)
        >>> zonearea.values = 1.0, 1.0, 1.0
        >>> states.sp = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
        >>> from hydpy import print_values
        >>> print_values(states.sp.valuevector)
        2.5, 3.5, 4.5

        The definition of |State2DSequence.valuevector| of |State2DSequence| allows
        applying method |Variable.average_values| like for the 1-dimensional
        zone-related sequences of |hland|:

        >>> print_values([states.sp.average_values()])
        3.5
        """
        return numpy.mean(self.value, axis=0)

    @property
    def seriesmatrix(self) -> Matrix[float]:
        """Time series of the values of the individual zones; each entry is the average
        of the values of all snow classes of a specific zone.

        We take subclass |SP| as an example:

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2000-01-05", "1d"
        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> nmbzones(3)
        >>> sclass(2)
        >>> zonetype(FIELD)
        >>> zonearea.values = 1.0, 1.0, 1.0
        >>> states.sp.activate_ram()
        >>> states.sp.series = [[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]],
        ...                     [[2.0, 3.0, 4.0], [5.0, 6.0, 7.0]],
        ...                     [[3.0, 4.0, 5.0], [6.0, 7.0, 8.0]],
        ...                     [[4.0, 5.0, 6.0], [7.0, 8.0, 9.0]]]
        >>> from hydpy import print_values
        >>> for values in states.sp.seriesmatrix:
        ...     print_values(values)
        2.5, 3.5, 4.5
        3.5, 4.5, 5.5
        4.5, 5.5, 6.5
        5.5, 6.5, 7.5

        The definition of |State2DSequence.seriesmatrix| of |State2DSequence| allows
        applying method |IOSequence.average_series| like for the 1-dimensional
        zone-related sequences of |hland|:

        >>> print_values(states.sp.average_series())
        3.5, 4.5, 5.5, 6.5
        """
        return numpy.mean(self.series, axis=1)
