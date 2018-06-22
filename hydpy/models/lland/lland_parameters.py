# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring


# import...
# ...standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import parametertools
# ...model specific
from hydpy.models.lland import lland_constants


class MultiParameter(parametertools.ZipParameter):
    """Base class for handling parameters of the HydPy-L-Land model
    (potentially) handling multiple values.

    Class |lland_parameters.MultiParameter| of HydPy-L-Land basically
    works like class |hland_parameters.MultiParameter| of HydPy-H-Land,
    except that keyword arguments specific to HydPy-L-Land are applied
    (acker, nadelw, wasser..., see module |lland_constants|) and except
    that parameter |NHRU| determines the number of entries:

    >>> from hydpy.models.lland.lland_parameters import MultiParameter
    >>> from hydpy.models.lland import *
    >>> parameterstep('1d')
    >>> mp = MultiParameter()
    >>> mp.subpars = control
    >>> mp.shape
    Traceback (most recent call last):
    ...
    RuntimeError: Shape information for parameter `multiparameter` can only \
be retrieved after it has been defined.  You can do this manually, but \
usually it is done automatically by defining the value of parameter `nhru` \
first in each parameter control file.
    """
    REQUIRED_VALUES = tuple(lland_constants.CONSTANTS.values())
    MODEL_CONSTANTS = lland_constants.CONSTANTS

    @property
    def refindices(self):
        """Alias for the associated instance of |Lnk|."""
        return self.subpars.pars.control.lnk

    @property
    def shapeparameter(self):
        """Alias for the associated instance of |NHRU|."""
        return self.subpars.pars.control.nhru


class MultiParameterLand(MultiParameter):
    """Base class for handling parameters of HydPy-L-Land (potentially)
    handling multiple values relevant for non water HRUs.
    """
    REQUIRED_VALUES = tuple(
        value for (key, value)
        in lland_constants.CONSTANTS.items()
        if value not in ('WASSER', 'SEE', 'FLUSS'))


class MultiParameterSoil(MultiParameter):
    """Base class for handling parameters of HydPy-L-Land (potentially)
    handling multiple values relevant for non water HRUs without sealed
    surfaces.
    """
    REQUIRED_VALUES = tuple(
        value for (key, value)
        in lland_constants.CONSTANTS.items()
        if value not in ('WASSER', 'SEE', 'FLUSS', 'VERS'))


class LanduseMonthParameter(parametertools.KeywordParameter2D):
    """Base class for parameters which values depend both an the actual
    land use class and the actual month.
    """
    COLNAMES = ('jan', 'feb', 'mar', 'apr', 'mai', 'jun',
                'jul', 'aug', 'sep', 'oct', 'nov', 'dec')
    ROWNAMES = tuple(
        key.lower() for (idx, key) in sorted(
            (idx, key) for (key, idx) in lland_constants.CONSTANTS.items()))
