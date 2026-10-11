# pylint: disable=missing-module-docstring

import abc

from hydpy.core import exceptiontools
from hydpy.core import parametertools
from hydpy.core import variabletools
from hydpy.models.hland import hland_control


class MixinZones(variabletools.Variable, abc.ABC):
    """Mixin class for 1-dimensional parameters and sequences whose shape depends on
    the value of parameter |NmbZones|.

    We take parameter |IcMax| as an example:

    >>> from hydpy.models.hland import *
    >>> parameterstep()
    >>> nmbzones(3)
    >>> icmax.shape
    (3,)

    Redefining the same number of zones does not delete the already available data:

    >>> icmax(2.0)
    >>> nmbzones(3)
    >>> icmax
    icmax(2.0)

    Changing the number of zones reshapes the parameter and requires resetting its
    values:

    >>> nmbzones(2)
    >>> icmax
    icmax(?)
    """

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        if isinstance(p, hland_control.NmbZones):
            self.__hydpy__change_shape_if_necessary__((p.value,))


class MixinZonesZones(variabletools.Variable, abc.ABC):
    """Mixin class for 2-dimensional parameters and sequences whose shape depends
    twice on the value of parameter |NmbZones|.

    We take parameter |SRed| as an example:

    >>> from hydpy.models.hland import *
    >>> parameterstep()
    >>> nmbzones(3)
    >>> sred.shape
    (3, 3)

    Redefining the same number of zones does not delete the already available data,
    while changing it does:

    >>> sred.values = 0.0
    >>> nmbzones(3)
    >>> from hydpy import print_matrix
    >>> print_matrix(sred.values)
    | 0.0, 0.0, 0.0 |
    | 0.0, 0.0, 0.0 |
    | 0.0, 0.0, 0.0 |
    >>> nmbzones(2)
    >>> sred
    sred(?)
    """

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        if isinstance(p, hland_control.NmbZones):
            self.__hydpy__change_shape_if_necessary__((p.value, p.value))


class MixinSnowClasses(variabletools.Variable, abc.ABC):
    """Mixin class for 1-dimensional parameters and sequences whose shape depends on
    the value of parameter |SClass|.

    We take parameter |SFDist| as an example:

    >>> from hydpy.models.hland import *
    >>> parameterstep()
    >>> sclass(2)
    >>> sfdist.shape
    (2,)

    Redefining the same number of snow classes does not delete the already available
    data, while changing it does:

    >>> sfdist(1.0)
    >>> sclass(2)
    >>> sfdist
    sfdist(1.0)
    >>> sclass(3)
    >>> sfdist
    sfdist(?)
    """

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        if isinstance(p, hland_control.SClass):
            self.__hydpy__change_shape_if_necessary__((p.value,))


class MixinSnowClassesZones(variabletools.Variable, abc.ABC):
    """Mixin class for 2-dimensional parameters and sequences whose shape depends on
    the values of the parameters |SClass| and |NmbZones|.

    We take the state sequence |SP| as an example.  |SClass| determines the length of
    its first axis and |NmbZones| the length of its second axis.  Its shape remains
    undefined as long as either parameter value is missing:

    >>> from hydpy.models.hland import *
    >>> parameterstep()
    >>> nmbzones(2)
    >>> states.sp.shape
    Traceback (most recent call last):
    ...
    hydpy.core.exceptiontools.AttributeNotReady: Shape information for variable `sp` \
can only be retrieved after it has been defined.
    >>> sclass(3)
    >>> states.sp.shape
    (3, 2)

    The order of defining both parameters does not matter:

    >>> from hydpy import reverse_model_wildcard_import
    >>> reverse_model_wildcard_import()
    >>> from hydpy.models.hland import *
    >>> parameterstep()
    >>> sclass(3)
    >>> states.sp.shape
    Traceback (most recent call last):
    ...
    hydpy.core.exceptiontools.AttributeNotReady: Shape information for variable `sp` \
can only be retrieved after it has been defined.
    >>> nmbzones(2)
    >>> states.sp.shape
    (3, 2)

    Redefining the same values does not delete the already available data, while
    changing one of them does:

    >>> states.sp = 2.0
    >>> sclass(3)
    >>> nmbzones(2)
    >>> states.sp
    sp([[2.0, 2.0],
        [2.0, 2.0],
        [2.0, 2.0]])
    >>> sclass(2)
    >>> states.sp
    sp([[nan, nan],
        [nan, nan]])
    """

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        if isinstance(p, hland_control.NmbZones):
            sclass = exceptiontools.getattr_(p.subpars.sclass, "value", None)
            if sclass is not None:
                self.__hydpy__change_shape_if_necessary__((sclass, p.value))
        elif isinstance(p, hland_control.SClass):
            nmbzones = exceptiontools.getattr_(p.subpars.nmbzones, "value", None)
            if nmbzones is not None:
                self.__hydpy__change_shape_if_necessary__((p.value, nmbzones))
