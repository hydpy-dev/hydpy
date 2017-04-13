# -*- coding: utf-8 -*-
"""Author: Wuestenfeld
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
from hydpy.models.globwat.globwat_constants import RADRYTROP, RAHUMTROP, RAHIGHL, RASUBTROP, RATEMP, RLSUBTROP, RLTEMP, RLBOREAL, FOREST, DESERT, WATER, IRRCPR, IRRCNPR, OTHER, CONSTANTS


class Parameters(parametertools.Parameters):
    """All parameters of the globwat model."""

    def update(self):
        """Determines the values of the parameters handled by
        :class:`DerivedParameters` based on the values of the parameters
        handled by :class:`ControlParameters`.
        """
        der = self.derived
        self.calc_smax()
        self.calc_seav()
        self.calc_ia()        
        der.moy.setreference(pub.indexer.monthofyear)
        
    """ Berechnung der abgeleiteten Parameter SMax und SEav aus SCMax und RtD """
        
    def calc_smax(self):
        
        con = self.control
        der = self.derived
        
        der.smax.shape = con.scmax.shape
        der.smax(con.scmax * con.rtd)
        
    def calc_seav(self):
        
        con = self.control
        der = self.derived
        
        der.seav.shape = con.scmax.shape
        der.seav(der.smax * .5)
        
    def calc_ia(self):
        
        con = self.control
        der = self.derived
        
        der.ia(con.irra/con.ta)
        

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