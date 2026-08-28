# pylint: disable=missing-module-docstring

import numpy

from hydpy.core import exceptiontools
from hydpy.core import parametertools
from hydpy.core import sequencetools
from hydpy.core.typingtools import *
from hydpy.models.snow import snow_control
from hydpy.models.snow import snow_derived
from hydpy.models.snow import snow_model
from hydpy.models.snow import snow_masks


class BaseSequence(sequencetools.ModelSequence):
    """Base class for |BaseSequence1D| and |BaseSequence2D|."""

    @property
    def refweights(self) -> snow_derived.ZoneAreaFraction:
        """Alias for the associated instance of |ZoneAreaFraction| for calculating
        areal values."""
        model = cast(snow_model.Model, self.subseqs.seqs.model)
        return model.parameters.derived.zoneareafraction


class BaseSequence1D(BaseSequence):
    """Base class for 1-dimensional sequences with a length according to |NumberZones|.

    The following example shows that the shape of sequence |Throughfall| is set
    automatically, and that weighted averaging is supported:

    >>> from hydpy import pub
    >>> pub.timegrids = "2000-01-01", "2000-01-02", "1d"
    >>> from hydpy.models.hland_96 import *
    >>> parameterstep("1d")
    >>> area(10.0)
    >>> nmbzones(4)
    >>> zonetype(FIELD, FOREST, ILAKE, GLACIER)
    >>> zonearea(4.0, 3.0, 2.0, 1.0)
    >>> zonez(10.0, 40.0, 30.0, 20.0)
    >>> with model.add_snowmodel_v1("snow_dd") as snowmodel:
    ...     redistributionpaths(n_zones=1)
    ...     fluxes.throughfall = 1.0, 4.0, 3.0, 2.0
    >>> from hydpy import round_
    >>> throughfall = snowmodel.sequences.fluxes.throughfall
    >>> round_(throughfall.average_values())
    2.4
    >>> round_(throughfall.average_values(throughfall.availablemasks.land))
    2.25

    .. testsetup::

        >>> del pub.timegrids
    """

    NDIM: Final[Literal[1]] = 1

    mask = snow_masks.Complete()

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        if isinstance(p, snow_control.NumberZones):
            self.__hydpy__change_shape_if_necessary__((p.value,))


class FactorSequence1D(BaseSequence1D, sequencetools.FactorSequence):
    """Base class for 1-dimensional factor sequences."""


class FluxSequence1D(BaseSequence1D, sequencetools.FluxSequence):
    """Base class for 1-dimensional flux sequences."""


class AideSequence1D(BaseSequence1D, sequencetools.AideSequence):
    """Base class for 1-dimensional aide sequences."""


class BaseSequence2D(BaseSequence, sequencetools.ModelIOSequence):
    """Base class for 1-dimensional sequences with the length of the first and the
    second axis according to |NumberZones| and |NumberDivisions|, respectively.

    The following example shows that the shape of sequence |ActualMelt| is set
    automatically, and that weighted averaging is supported:

    >>> from hydpy import pub
    >>> pub.timegrids = "2000-01-01", "2000-01-02", "1d"
    >>> from hydpy.models.hland_96 import *
    >>> parameterstep("1d")
    >>> area(10.0)
    >>> nmbzones(4)
    >>> zonetype(FIELD, FOREST, ILAKE, GLACIER)
    >>> zonearea(4.0, 3.0, 2.0, 1.0)
    >>> zonez(10.0, 40.0, 30.0, 20.0)
    >>> with model.add_snowmodel_v1("snow_dd") as snowmodel:
    ...     numberdivisions(2)
    ...     redistributionpaths(n_zones=1)
    ...     fluxes.actualmelt = [[0.5, 3.5, 2.5, 1.5], [1.5, 4.5, 3.5, 2.5]]
    >>> from hydpy import round_
    >>> actualmelt = snowmodel.sequences.fluxes.actualmelt
    >>> round_(actualmelt.average_values())
    2.4
    >>> round_(actualmelt.average_values(actualmelt.availablemasks.land))
    2.25

    .. testsetup::

        >>> del pub.timegrids
    """

    NDIM: Final[Literal[2]] = 2

    mask = snow_masks.Complete()

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        v1: int | None
        v2: int | None
        if isinstance(p, snow_control.NumberZones):
            v1 = exceptiontools.getattr_(p.subpars.numberdivisions, "value", None)
            v2 = p.value
        elif isinstance(p, snow_control.NumberDivisions):
            v1 = p.value
            v2 = exceptiontools.getattr_(p.subpars.numberzones, "value", None)
        else:
            return  # ToDo: switch to "assert False" after NLayers has been removed
        if (v1 is not None) and (v2 is not None):
            self.__hydpy__change_shape_if_necessary__((v1, v2))

    @property
    def valuevector(self) -> VectorFloat:
        """Values of the individual zones; each entry is the average of the values of
        all snow classes of a specific zone.

        We take subclass |IceContent| as an example:

        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> numberzones(3)
        >>> numberdivisions(2)
        >>> derived.zoneareafraction(1.0 / 3.0)
        >>> states.icecontent = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
        >>> from hydpy import print_vector
        >>> print_vector(states.icecontent.valuevector)
        2.5, 3.5, 4.5

        The definition of |BaseSequence2D.valuevector| of |BaseSequence2D| allows
        applying method |Variable.average_values| as for 1-dimensional zone-related
        sequences:

        >>> print_vector([states.icecontent.average_values()])
        3.5
        """
        return numpy.mean(self.value, axis=0)

    @property
    def seriesmatrix(self) -> MatrixFloat:
        """Time series of the values of the individual zones; each entry is the average
        of the values of all snow classes of a specific zone.

        We take subclass |IceContent| as an example:

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2000-01-05", "1d"
        >>> from hydpy.models.snow import *
        >>> parameterstep()
        >>> numberzones(3)
        >>> numberdivisions(2)
        >>> derived.zoneareafraction(1.0 / 3.0)
        >>> states.icecontent.prepare_series()
        >>> states.icecontent.series = [[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]],
        ...                             [[2.0, 3.0, 4.0], [5.0, 6.0, 7.0]],
        ...                             [[3.0, 4.0, 5.0], [6.0, 7.0, 8.0]],
        ...                             [[4.0, 5.0, 6.0], [7.0, 8.0, 9.0]]]
        >>> from hydpy import print_vector
        >>> for values in states.icecontent.seriesmatrix:
        ...     print_vector(values)
        2.5, 3.5, 4.5
        3.5, 4.5, 5.5
        4.5, 5.5, 6.5
        5.5, 6.5, 7.5

        The definition of |BaseSequence2D.seriesmatrix| of |BaseSequence| allows
        applying method |IOSequence.average_series| as for 1-dimensional zone-related
        sequences:

        >>> print_vector(states.icecontent.average_series())
        3.5, 4.5, 5.5, 6.5

        .. testsetup::

            >>> del pub.timegrids
        """
        return numpy.mean(self.series, axis=1)


class FactorSequence2D(BaseSequence2D, sequencetools.FactorSequence):
    """Base class for 2-dimensional factor sequences."""


class FluxSequence2D(BaseSequence2D, sequencetools.FluxSequence):
    """Base class for 2-dimensional flux sequences."""


class StateSequence2D(BaseSequence2D, sequencetools.StateSequence):
    """Base class for 2-dimensional state sequences."""


class Sequence1DNLayers(sequencetools.ModelSequence):
    """Base class for sequences with different values for individual layers."""

    NDIM: Final[Literal[1]] = 1

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        self.__hydpy__change_shape_if_necessary__((p.value,))

    @property
    def refweights(self) -> parametertools.Parameter:
        """Alias for the associated instance of |LayerArea| for calculating aggregated
        values for layer-specific flux sequences."""
        return self.subseqs.seqs.model.parameters.control.layerarea


class Factor1DNLayers(Sequence1DNLayers, sequencetools.FactorSequence):
    """Base class for factor sequences with different values for individual layers.

    The following example shows that the shape of sequence |TLayer| is set
    automatically, and that weighted averaging is possible:

    >>> from hydpy.models.snow import *
    >>> parameterstep()
    >>> nlayers(4)
    >>> layerarea(0.1, 0.2, 0.3, 0.4)
    >>> factors.tlayer(3.0, 1.0, 4.0, 2.0)
    >>> from hydpy import round_
    >>> round_(factors.tlayer.average_values())
    2.5
    """


class Flux1DNLayers(Sequence1DNLayers, sequencetools.FluxSequence):
    """Base class for flux sequences with different values for individual layers.

    The following example shows that the shape of sequence |PLayer| is set
    automatically, and that weighted averaging is possible:

    >>> from hydpy.models.snow import *
    >>> parameterstep()
    >>> nlayers(4)
    >>> layerarea(0.1, 0.2, 0.3, 0.4)
    >>> fluxes.player(3.0, 1.0, 4.0, 2.0)
    >>> from hydpy import round_
    >>> round_(fluxes.player.average_values())
    2.5
    """


class State1DNLayers(Sequence1DNLayers, sequencetools.StateSequence):
    """Base class for state sequences with different values for individual layers.

    The following example shows that the shape of sequence |G| is set automatically,
    and that weighted averaging is possible:

    >>> from hydpy.models.snow import *
    >>> parameterstep()
    >>> nlayers(4)
    >>> layerarea(0.1, 0.2, 0.3, 0.4)
    >>> states.g(3.0, 1.0, 4.0, 2.0)
    >>> from hydpy import round_
    >>> round_(states.g.average_values())
    2.5
    """


class Log1DNLayers(Sequence1DNLayers, sequencetools.LogSequence):
    """Base class for log sequences with different values for individual layers.

    The following example shows that the shape of sequence |GLocalMax| is set
    automatically, and that weighted averaging is possible:

    >>> from hydpy.models.snow import *
    >>> parameterstep()
    >>> nlayers(4)
    >>> layerarea(0.1, 0.2, 0.3, 0.4)
    >>> logs.glocalmax(3.0, 1.0, 4.0, 2.0)
    >>> from hydpy import round_
    >>> round_(logs.glocalmax.average_values())
    2.5
    """
