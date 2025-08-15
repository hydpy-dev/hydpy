# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import objecttools
from hydpy.core import parametertools

# ...from lland
from hydpy.models.lland.lland_constants import CONSTANTS
from hydpy.models.lland import lland_masks


class ParameterComplete(parametertools.ZipParameter):
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
    def refweights(self):
        """Alias for the associated instance of |FHRU| for calculating areal mean
        values."""
        return self.subpars.pars.derived.absfhru


class ParameterLand(ParameterComplete):
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


class ParameterSoil(ParameterComplete):
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


class ParameterSoilThreshold(ParameterSoil):
    """Base class for defining threshold parameters related to |WMax|.

    Base class |ParameterSoilThreshold| provides the convenience to define
    thresholds via the keyword argument `relative`. For example, you can
    define the value of parameter |PWP| as a portion of the current value
    of |WMax|:

    >>> from hydpy.models.lland import *
    >>> parameterstep("1d")
    >>> nhru(2)
    >>> lnk(ACKER, LAUBW)
    >>> wmax(100.0, 200.0)
    >>> pwp(relative=0.2)
    >>> pwp
    pwp(acker=20.0, laubw=40.0)

    Trimming works as to be expected:

    >>> pwp(relative=-0.2)
    >>> pwp
    pwp(0.0)

    You can also use the common ways to define soil parameter values:

    >>> pwp(acker=30.0, laubw=60.0)
    >>> pwp
    pwp(acker=30.0, laubw=60.0)
    >>> pwp(10.0)
    >>> pwp
    pwp(10.0)

    We do not allow to combine the keyword argument `relative` with other ones:

    >>> pwp(relative=True, acker=10.0)
    Traceback (most recent call last):
    ...
    TypeError: While trying to set the values of parameter `pwp` of \
element `?` with arguments `relative and acker`:  It is not allowed to use \
keyword `relative` and other keywords at the same time.

    Other possible errors related to the usage of |ParameterSoil| are
    reported as usual:

    >>> pwp(feld=20.0, acker=10.0)
    Traceback (most recent call last):
    ...
    TypeError: While trying to set the values of parameter `pwp` of \
element `?` based on keyword arguments `feld and acker`, the following error \
occurred: Keyword `feld` is not among the available model constants.
    """

    def __call__(self, *args, **kwargs) -> None:
        try:
            super().__call__(*args, **kwargs)
        except TypeError as exc:
            if "relative" in kwargs:
                if len(kwargs) == 1:
                    self(float(kwargs["relative"]) * self.subpars.wmax)
                else:
                    raise TypeError(
                        f"While trying to set the values of parameter "
                        f"{objecttools.elementphrase(self)} with arguments "
                        f"`{objecttools.enumeration(kwargs.keys())}`:  "
                        f"It is not allowed to use keyword `relative` and "
                        f"other keywords at the same time."
                    ) from None
            else:
                raise exc


class ParameterGlacier(ParameterComplete):
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


class LanduseMonthParameter(parametertools.KeywordParameter2D):
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
