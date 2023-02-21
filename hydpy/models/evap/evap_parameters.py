# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools
from hydpy.core.typingtools import *

if TYPE_CHECKING:
    from hydpy.core import variabletools


class LandMonthParameter(parametertools.KeywordParameter2D):
    """Base class for parameters whose values depend on the actual month and land cover
    type.

    >>> from hydpy import pub
    >>> pub.timegrids = "2000-01-01", "2001-01-01", "1d"
    >>> from hydpy.models.wland_v001 import *
    >>> parameterstep()
    >>> nu(2)
    >>> al(10.0)
    >>> aur(0.2, 0.8)
    >>> lt(FIELD, TREES)
    >>> with model.add_petmodel_v1("evap_mlc"):
    ...     pass
    >>> model.petmodel.parameters.control.landmonthfactor  # doctest: +ELLIPSIS
    landmonthfactor(sealed=[nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,
                    ...
                    mixed=[nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,
                           nan, nan])
    """

    columnnames = (
        "jan",
        "feb",
        "mar",
        "apr",
        "may",
        "jun",
        "jul",
        "aug",
        "sep",
        "oct",
        "nov",
        "dec",
    )
    rownames: Tuple[str, ...] = ("any",)
