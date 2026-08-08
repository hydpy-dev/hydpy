# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core.typingtools import *

if TYPE_CHECKING:
    from hydpy.core import variabletools


class BaseSequence1D(sequencetools.ModelSequence):
    """Base class for all 1-dimensional sequence classes.

    >>> from hydpy.models.hland_96 import *
    >>> parameterstep()
    >>> nmbzones(5)
    >>> area(10.0)
    >>> zonearea(0.5, 1.5, 2.5, 1.0, 4.5)
    >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, SEALED)
    >>> zonez(2.0)
    >>> fc(200.0)
    >>> psi(1.0)
    >>> with model.add_aetmodel_v1("evap_aet_hbv96") as aetmodel:
    ...     factors.airtemperature = 0.0, 1.0, 2.0, 3.0, 4.0
    >>> airtemperature = aetmodel.sequences.factors.airtemperature
    >>> from hydpy import round_
    >>> round_(airtemperature.average_values())
    2.75
    >>> round_(airtemperature.average_values(airtemperature.availablemasks.soil))
    0.75
    """

    NDIM: Final[Literal[1]] = 1


class FactorSequence1D(sequencetools.FactorSequence, BaseSequence1D):
    """Base class for 1-dimensional factor sequences."""


class FluxSequence1D(sequencetools.FluxSequence, BaseSequence1D):
    """Base class for 1-dimensional flux sequences."""


class StateSequence1D(sequencetools.StateSequence, BaseSequence1D):
    """Base class for 1-dimensional state sequences."""
