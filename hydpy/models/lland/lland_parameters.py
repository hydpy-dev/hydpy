# pylint: disable=missing-module-docstring

from __future__ import annotations

import abc

from hydpy.core import parametertools
from hydpy.core.typingtools import *
from hydpy.models.lland.lland_constants import CONSTANTS
from hydpy.models.lland import lland_model
from hydpy.models.lland import lland_masks
from hydpy.models.lland import lland_variables

if TYPE_CHECKING:
    from hydpy.models.lland import lland_derived


class ParameterComplete(
    lland_variables.MixinHRUs, parametertools.ZipParameter, abc.ABC
):
    """Base class for 1-dimensional parameters relevant for all types
    of landuse.

    Class |ParameterComplete| of base model |lland| basically works
    like class |hland_parameters.ParameterComplete| of base model
    |hland|, but references |lland| specific parameters and constants,
    as shown in the following examples based on parameter |KG| (for
    explanations, see the documentation on class
    |hland_parameters.ParameterComplete|):

    >>> from hydpy.models.lland import *
    >>> parameterstep("1d")
    >>> nhru(5)
    >>> lnk(ACKER, VERS, GLETS, SEE, ACKER)
    >>> kg(acker=2.0, vers=1.0, glets=4.0, see=3.0)
    >>> kg
    kg(acker=2.0, glets=4.0, see=3.0, vers=1.0)
    >>> from hydpy import print_vector
    >>> print_vector(kg.values)
    2.0, 1.0, 4.0, 3.0, 2.0
    >>> kg(5.0, 4.0, 3.0, 2.0, 1.0)
    >>> derived.absfhru(0.0, 0.1, 0.2, 0.3, 0.4)
    >>> from hydpy import round_
    >>> round_(kg.average_values())
    2.0
    """

    constants = dict(CONSTANTS.items())
    mask = lland_masks.Complete()

    @property
    def refweights(self) -> lland_derived.AbsFHRU:
        """Alias for the associated instance of |FHRU| for calculating areal mean
        values."""
        model = cast(lland_model.Model, self.subpars.pars.model)
        return model.parameters.derived.absfhru


class ParameterLand(ParameterComplete, abc.ABC):
    """Base class for 1-dimensional parameters relevant for all hydrological
    response units except those of type |WASSER|, |FLUSS|, and |SEE|.

    |ParameterLand| works similar to |lland_parameters.ParameterComplete|.
    Some examples based on parameter |TGr|:

    >>> from hydpy.models.lland import *
    >>> parameterstep("1d")
    >>> nhru(5)
    >>> lnk(WASSER, ACKER, FLUSS, VERS, ACKER)
    >>> tgr(wasser=2.0, acker=1.0, fluss=4.0, vers=3.0)
    >>> tgr
    tgr(acker=1.0, vers=3.0)
    >>> tgr(acker=2.0, default=8.0)
    >>> tgr
    tgr(acker=2.0, vers=8.0)
    >>> derived.absfhru(nan, 1.0, nan, 1.0, 1.0)
    >>> from hydpy import round_
    >>> round_(tgr.average_values())
    4.0
    """

    mask = lland_masks.Land()


class ParameterSoil(ParameterComplete, abc.ABC):
    """Base class for 1-dimensional parameters relevant for all hydrological
    response units except those of type |WASSER|, |FLUSS|, |SEE|, and |VERS|.

    |ParameterLand| works similar to |lland_parameters.ParameterComplete|.
    Some examples based on parameter |WMax|:

    >>> from hydpy.models.lland import *
    >>> parameterstep("1d")
    >>> nhru(5)
    >>> lnk(WASSER, ACKER, LAUBW, VERS, ACKER)
    >>> wmax(wasser=300.0, acker=200.0, laubw=400.0, vers=300.0)
    >>> wmax
    wmax(acker=200.0, laubw=400.0)
    >>> wmax(acker=200.0, default=800.0)
    >>> wmax
    wmax(acker=200.0, laubw=800.0)
    >>> derived.absfhru(nan, 1.0, 1.0, nan, 1.0)
    >>> from hydpy import round_
    >>> round_(wmax.average_values())
    400.0
    """

    mask = lland_masks.Soil()


class ParameterSoilThreshold(ParameterSoil, abc.ABC):
    """Base class for defining threshold parameters related to |WMax|."""

    def _set_relative(self, *, relative: float) -> dict[str, float]:
        relative = float(relative)
        self.values = relative * self.subpars.wmax.values
        return {"relative": relative}

    KEYWORDS = parametertools.KeywordGroups(
        parametertools.KeywordGroup(
            parametertools.Keyword("relative"),
            dependencies=("wmax",),
            setter=_set_relative,
        )
    )


class ParameterGlacier(ParameterComplete, abc.ABC):
    """Base class for 1-dimensional parameters relevant for all |GLETS| zones.

    |ParameterLand| works similarly to |lland_parameters.ParameterComplete|.  Some
    examples based on parameter |FEis|:

    >>> from hydpy.models.lland import *
    >>> simulationstep("12h")
    >>> parameterstep("1d")
    >>> nhru(5)
    >>> lnk(ACKER, GLETS, FLUSS, VERS, GLETS)

    >>> feis(wasser=1.0, acker=1.0, glets=0.1, vers=1.0)
    >>> feis
    feis(0.1)

    >>> feis(default=0.2)
    >>> feis
    feis(0.2)

    >>> derived.absfhru(nan, 1.0, nan, nan, 1.0)
    >>> from hydpy import round_
    >>> round_(feis.average_values())
    0.1
    """

    mask = lland_masks.Glets()


class LanduseMonthParameter(parametertools.KeywordParameter2D, abc.ABC):
    """Base class for parameters which values depend both an the actual
    land use class and the actual month."""

    columnnames = (
        "jan",
        "feb",
        "mar",
        "apr",
        "mai",
        "jun",
        "jul",
        "aug",
        "sep",
        "oct",
        "nov",
        "dec",
    )
    rownames = tuple(
        key.lower()
        for (idx, key) in sorted((idx, key) for (key, idx) in CONSTANTS.items())
    )
