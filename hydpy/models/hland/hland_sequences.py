# pylint: disable=missing-module-docstring

from hydpy.core.typingtools import *
from hydpy.core import sequencetools
from hydpy.models.hland import hland_model
from hydpy.models.hland import hland_derived


class Factor1DSequence(sequencetools.FactorSequence):
    """Base class for 1-dimensional factor subclasses that support aggregation with
    respect to |RelZoneAreas|.

    All |Factor1DSequence| subclasses must implement fitting mask objects individually.

    The following example shows how the subclass |TC| works:

    >>> from hydpy.models.hland import *
    >>> parameterstep()
    >>> nmbzones(5)
    >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, SEALED)
    >>> derived.relzoneareas(0.1, 0.2, 0.3, 0.35, 0.05)
    >>> factors.tc(5.0, 2.0, 4.0, 1.0, 6.0)
    >>> from hydpy import round_
    >>> round_(factors.tc.average_values())
    2.75
    """

    NDIM: Final[Literal[1]] = 1

    @property
    def refweights(self) -> hland_derived.RelZoneAreas:
        """Alias for the associated instance of |RelZoneAreas| for calculating areal
        values."""
        model = cast(hland_model.Model, self.subseqs.seqs.model)
        return model.parameters.derived.relzoneareas


class Flux1DSequence(sequencetools.FluxSequence):
    """Base class for 1-dimensional flux subclasses that support aggregation with
    respect to |RelZoneAreas|.

    All |Flux1DSequence| subclasses must implement fitting mask objects individually.

    The following example shows how the subclass |PC| works:

    >>> from hydpy.models.hland import *
    >>> parameterstep("1d")
    >>> nmbzones(5)
    >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, SEALED)
    >>> derived.relzoneareas(0.1, 0.2, 0.3, 0.35, 0.05)
    >>> fluxes.pc(5.0, 2.0, 4.0, 1.0, 6.0)
    >>> from hydpy import round_
    >>> round_(fluxes.pc.average_values())
    2.75
    """

    NDIM: Final[Literal[1]] = 1

    @property
    def refweights(self) -> hland_derived.RelZoneAreas:
        """Alias for the associated instance of |RelZoneAreas| for calculating areal
        values."""
        model = cast(hland_model.Model, self.subseqs.seqs.model)
        return model.parameters.derived.relzoneareas


class State1DSequence(sequencetools.StateSequence):
    """Base class for 1-dimensional state subclasses that support aggregation with
    respect to |RelZoneAreas|.

    All |State1DSequence| subclasses must implement fitting mask objects individually.

    The following example shows how subclass |SM| works, which implements mask |Soil|:

    >>> from hydpy.models.hland import *
    >>> parameterstep("1d")
    >>> nmbzones(5)
    >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, SEALED)
    >>> derived.relzoneareas(0.0625, 0.125, 0.1875, 0.25, 0.375)
    >>> fc(100.0)
    >>> states.sm = 50.0, 20.0, 40.0, 10.0, nan
    >>> from hydpy import round_
    >>> round_(states.sm.average_values())
    30.0
    """

    NDIM: Final[Literal[1]] = 1

    @property
    def refweights(self) -> hland_derived.RelZoneAreas:
        """Alias for the associated instance of |RelZoneAreas| for calculating
        areal values."""
        model = cast(hland_model.Model, self.subseqs.seqs.model)
        return model.parameters.derived.relzoneareas
