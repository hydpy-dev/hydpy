# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import parametertools


class HV(parametertools.LeftRightParameter):
    """Höhe Vorländer (height of both forelands) [m]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

    def update(self):
        """Update value based on :math:`HV=BBV/BNV`.

        Required Parameters:
            :class:`BBV`
            :class:`BNV`

        Examples:
            >>> from hydpy.models.lstream import *
            >>> parameterstep('1d')
            >>> bbv(left=10., right=40.)
            >>> bnv(left=10., right=20.)
            >>> derived.hv.update()
            >>> derived.hv
            hv(1.0, 2.0)
            >>> bbv(left=10., right=0.)
            >>> bnv(left=0., right=20.)
            >>> derived.hv.update()
            >>> derived.hv
            hv(0.0)
        """
        con = self.subpars.pars.control
        for idx in range(2):
            if (con.bbv[idx] > 0.) and (con.bnv[idx] > 0.):
                self[idx] = con.bbv[idx]/con.bnv[idx]
            else:
                self[idx] = 0.

class Sek(parametertools.SingleParameter):
    """ Sekunden im Simulationszeitschritt (Number of seconds of the selected
    simulation time step) [T]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

    def update(self):
        """Update value based on :math:`HL=BBR/BNR`.

        Required Parameters:
            :class:`BBR`
            :class:`BNR`

        Example:
            >>> from hydpy.models.lstream import *
            >>> parameterstep()
            >>> simulationstep('1d')
            >>> derived.sek.update()
            >>> derived.sek
            sek(86400.0)
        """
        self(self.simulationstep.seconds)

class DerivedParameters(parametertools.SubParameters):
    """Derived parameters of HydPy-L-Stream, indirectly defined by the user."""
    _PARCLASSES = (HV, Sek)
