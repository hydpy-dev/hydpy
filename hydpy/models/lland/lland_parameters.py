# -*- coding: utf-8 -*-
"""
ToDo
"""

# import...
# ...standard library
from __future__ import division, print_function
# ...third party
import numpy
# ...HydPy specific
from hydpy import pub
from hydpy.core import objecttools
from hydpy.core import parametertools
# ...model specific
from hydpy.models.lland.lland_constants import CONSTANTS

class MultiParameter(parametertools.ZipParameter):
    """Base class for handling parameters of the HydPy-L-Land model
    (potentially) handling multiple values.

    Class :class:`MultiParameter` of HydPy-L-Land basically works like
    Class :class:`~hydpy.models.lland.lland_parameters.MultiParameter` of
    HydPy-L-Land, except that keyword arguments specific to HydPy-L-Land
    are applied (field, for_m, wat..., see module
    :mod:`~hydpy.models.lland.lland_constants`) and except that parameter
    :class:`~hydpy.models.lland.lland_control.NmbGRUs` is the number of
    entries:

    >>> from hydpy.models.lland.lland_parameters import MultiParameter
    >>> mp = MultiParameter()
    >>> mp.shape
    Traceback (most recent call last):
    ...
    RuntimeError: Shape information for parameter `multiparameter` can only be retrieved after it has been defined.  You can do this manually, but usually it is done automatically by defining the value of parameter `nhru` first in each parameter control file.
    """
    REQUIRED_VALUES = REQUIRED_VALUES = tuple(CONSTANTS.values())
    MODEL_CONSTANTS = CONSTANTS

    @property
    def refparameter(self):
        """Alias for the associated instance of
        :class:`~hydpy.models.lland.lland_control.LandUse`.
        """
        return self.subpars.pars.control.lnk

    def _getshape(self):
        """Return a tuple containing the lengths in all dimensions of the
        parameter values.
        """
        try:
            return parametertools.ZipParameter._getshape(self)
        except RuntimeError:
            raise RuntimeError('Shape information for parameter `%s` can '
                               'only be retrieved after it has been defined. '
                               ' You can do this manually, but usually it is '
                               'done automatically by defining the value of '
                               'parameter `nhru` first in each parameter '
                               'control file.' % self.name)
    shape = property(_getshape, parametertools.ZipParameter._setshape)


class LanduseMonthParameter(parametertools.MultiParameter):

    def __call__(self, *args, **kwargs):
        self.shape = (len(CONSTANTS), 12)
        try:
            parametertools.MultiParameter.__call__(self, *args, **kwargs)
        except NotImplementedError:
            for (key, idx) in CONSTANTS.items():
                try:
                    values = kwargs.pop(key.lower())
                except KeyError:
                    raise ValueError('When defining parameter %s of element '
                                     '%s via keyword arguments, values for '
                                     'each type of land use type must be '
                                     'given, but keyword/land use `%s` is '
                                     'missing.'
                                     % (self.name,
                                        objecttools.devicename(self),
                                        key.lower()))
                self.values[idx-1,:] = values

    def __repr__(self):
        lines = self.commentrepr()
        blanks = (len(self.name)+1) * ' '
        sorted_ = sorted((idx, key) for (key, idx) in CONSTANTS.items())
        for (idx, key) in sorted_:
            valuerepr = ', '.join(objecttools.repr_(value)
                                  for value in self.values[idx-1,:])
            line = ('%s=[%s],' % (key.lower(), valuerepr))
            if idx == 1:
                lines.append('%s(%s' % (self.name, line))
            else:
                lines.append('%s%s' % (blanks, line))
        lines[-1] = lines[-1][:-1]+')'
        return '\n'.join(lines)

    def __getattr__(self, key):
        idx = CONSTANTS.get(key.upper(), None) if key.islower() else None
        if idx is None:
            return parametertools.MultiParameter.__getattr__(self, key)
        else:
            return self.values[idx-1, :]

    def __setattr__(self, key, values):
        idx = CONSTANTS.get(key.upper(), None) if key.islower() else None
        if idx is None:
            parametertools.MultiParameter.__setattr__(self, key, values)
        else:
            try:
                self.values[idx-1, :] = values
            except BaseException:
                objecttools.augmentexcmessage('While trying to assign new '
                                              'values to parameter `%s` of '
                                              'element `%s` for land use `%s`'
                                              % (key.lower(), self.name,
                                                 objecttools.devicename(self)))

    def __dir__(self):
        return (objecttools.dir_(self) +
                [key.lower() for key in CONSTANTS.keys()])


class Parameters(parametertools.Parameters):
    """All parameters of the HydPy-L-Land model."""
