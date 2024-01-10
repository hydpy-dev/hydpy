# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools

# ...from lland
from hydpy.models.wland import wland_control
from hydpy.models.wland import wland_masks


class BaseFluxSequence1D(sequencetools.FluxSequence):
    """Base class for |FluxSequence1DComplete| and |FluxSequence1DLand| that supports
    aggregation with respect to |AUR|."""

    CONTROLPARAMETERS = (wland_control.AUR,)

    @property
    def refweights(self):
        """Alias for the associated instance of |AUR| for calculating areal values."""
        return self.subseqs.seqs.model.parameters.control.aur


class FluxSequence1DComplete(BaseFluxSequence1D):
    """Base class for 1-dimensional flux sequences that contain values for all
    hydrological response units.

    The following example shows how subclass |PET| works:

    >>> from hydpy.models.wland import *
    >>> parameterstep()
    >>> nu(4)
    >>> lt(FIELD, CONIFER, SEALED, WATER)
    >>> aur(0.1, 0.2, 0.3, 0.4)
    >>> fluxes.pe = 5.0, 2.0, 4.0, 1.0
    >>> from hydpy import round_
    >>> round_(fluxes.pe.average_values())
    2.5
    """

    mask = wland_masks.Complete()


class FluxSequence1DLand(BaseFluxSequence1D):
    """Base class for 1-dimensional flux sequences that contain values for the
    land-related hydrological response units.

    The following example shows how subclass |EI| works:

    >>> from hydpy.models.wland import *
    >>> parameterstep()
    >>> nu(5)
    >>> lt(FIELD, CONIFER, SEALED, FIELD, WATER)
    >>> aur(0.05, 0.1, 0.15, 0.2, 0.5)
    >>> fluxes.ei = 5.0, 2.0, 4.0, 1.0, nan
    >>> from hydpy import round_
    >>> round_(fluxes.ei.average_values())
    2.5
    """

    mask = wland_masks.Land()


class FluxSequence1DSoil(BaseFluxSequence1D):
    """Base class for 1-dimensional flux sequences that contain values for the
    soil-related hydrological response units.

    The following example shows how subclass |PET| works:

    >>> from hydpy.models.wland import *
    >>> parameterstep()
    >>> nu(5)
    >>> lt(FIELD, CONIFER, SEALED, FIELD, WATER)
    >>> aur(0.1, 0.2, 0.12, 0.3, 0.2)
    >>> fluxes.pet = 5.0, 2.0, 4.0, 1.0, nan
    >>> from hydpy import round_
    >>> round_(fluxes.pet.average_values())
    2.0
    """

    mask = wland_masks.Soil()


class StateSequence1DLand(sequencetools.StateSequence):
    """Base class for 1-dimensional state sequences that support aggregation with
    respect to |AUR| for all land-related hydrological response units.

    The following example shows how subclass |IC| works:

    >>> from hydpy.models.wland import *
    >>> parameterstep()
    >>> nu(5)
    >>> lt(FIELD, CONIFER, SEALED, FIELD, WATER)
    >>> aur(0.05, 0.1, 0.15, 0.2, 0.5)
    >>> states.ic = 5.0, 2.0, 4.0, 1.0, nan
    >>> from hydpy import round_
    >>> round_(states.ic.average_values())
    2.5
    """

    CONTROLPARAMETERS = (wland_control.AUR,)

    mask = wland_masks.Land()

    @property
    def refweights(self):
        """Alias for the associated instance of |AUR| for calculating areal values."""
        return self.subseqs.seqs.model.parameters.control.aur
