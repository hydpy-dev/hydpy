# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools
from hydpy.core import sequencetools


class Sequence1DNLayers(sequencetools.ModelSequence):
    """Base class for sequences with different values for individual layers."""

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

    NDIM, NUMERIC = 1, False


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

    NDIM, NUMERIC = 1, False


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

    NDIM, NUMERIC = 1, False


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

    NDIM, NUMERIC = 1, False
