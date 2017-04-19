# -*- coding: utf-8 -*-

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

    Class :class:`MultiParameter` of HydPy-L-Land basically works like
    Class :class:`~hydpy.models.lland.lland_parameters.MultiParameter` of
    HydPy-H-Land, except that keyword arguments specific to HydPy-L-Land
    are applied (acker, nadelw, wasser..., see module
    :mod:`~hydpy.models.lland.lland_constants`) and except that parameter
    :class:`~hydpy.models.lland.lland_control.NHRU` determines the number of
    entries:

    >>> from hydpy.models.lland.lland_parameters import MultiParameter
    >>> from hydpy.models.lland import *
    >>> parameterstep('1d')
    >>> mp = MultiParameter()
    >>> mp.subpars = control
    >>> mp.shape
    Traceback (most recent call last):
    ...
    RuntimeError: Shape information for parameter `multiparameter` can only be retrieved after it has been defined.  You can do this manually, but usually it is done automatically by defining the value of parameter `nhru` first in each parameter control file.
    """
    REQUIRED_VALUES = tuple(lland_constants.CONSTANTS.values())
    MODEL_CONSTANTS = lland_constants.CONSTANTS

    @property
    def refparameter(self):
        """Alias for the associated instance of
        :class:`~hydpy.models.lland.lland_control.LNK`.
        """
        return self.subpars.pars.control.lnk

    @property
    def shapeparameter(self):
        """Alias for the associated instance of
        :class:`~hydpy.models.lland.lland_control.NHRU`.
        """
        return self.subpars.pars.control.nhru


class MultiParameterLand(MultiParameter):
    """Base class for handling parameters of the lland model (potentially)
    handling multiple values relevant for non water HRUs.
    """
    REQUIRED_VALUES = tuple(value for (key, value) 
                            in lland_constants.CONSTANTS.items()
                            if value != 'WASSER')

class MultiParameterSoil(MultiParameter):
    """Base class for handling parameters of the lland model (potentially)
    handling multiple values relevant for non water HRUs without sealed
    surfaces.
    """
    REQUIRED_VALUES = tuple(value for (key, value) 
                            in lland_constants.CONSTANTS.items()
                            if value not in ('WASSER', 'VERS'))


class LanduseMonthParameter(parametertools.ConstTimeParameter):
    """"""
    CONSTANTS = lland_constants.CONSTANTS
    NMBCOLUMS = 12
    
    
class Parameters(parametertools.Parameters):
    """All parameters of the HydPy-L-Land model."""
