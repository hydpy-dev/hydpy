# -*- coding: utf-8 -*-
"""Author: Wuestenfeld"""

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy import pub
from hydpy.core import parametertools
# ...model specific
from hydpy.models.globwat import globwat_parameters
from hydpy.models.globwat.globwat_constants import *

SAFETY = 1e-14


class Irrigation(parametertools.MultiParameter):
    """landuse equipped for irrigation (True or False) [-]."""
    NDIM, TYPE, TIME, SPAN = 1, int, None, (None, None)

    def update(self):
        """settig irrigation true or false for vegetationclasses.

        Required control parameter:
          :class:`~hydpy.models.globwat.globwat_control.Vegetationclass`

        Calculated derived parameter:
          :class:`Irrigation`
        """

        con = self.subpars.pars.control
        for (idx, vegclass) in enumerate(con.vegetationclass):
            if vegclass in (IRRCPR, IRRCNPR,
                            IRR_GER, IRR_CZE, IRR_AUT,
                            IRR_POL, IRR_HUN, IRR_SUI, IRR_ITA, IRR_SLO,
                            IRR_CRO, IRR_BYH, IRR_ALB, IRR_SER, IRR_SLV,
                            IRR_UKR, IRR_BUL, IRR_ROM, IRR_MLD
            ):
                self[idx] = 1
            else:
                self[idx] = 0

class SMax(parametertools.MultiParameter):
    """maximum soil moisture storage [mm]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

    def update(self):
        """calculation of derived parameter maximum soil moisture.

        Required control parameter:
          :class:`~hydpy.models.globwat.globwat_control.SCMax`
          :class:`~hydpy.models.globwat.globwat_control.Rtd`

        Calculated derived parameter:
          :class:`SMax`

        Basic equation:
          :math:`S_{max} = SC_{max} \\cdot Rt_d`

        Examples:

        >>> from hydpy.models.globwat import *
        >>> parameterstep()
        >>> nmbgrids(1)
        >>> control.scmax(50.)
        >>> control.rtd(.6)
        >>> derived.smax.update()
        >>> derived.smax
        smax(30.0)
        """
        con = self.subpars.pars.control
        self(con.scmax * con.rtd)

class SEAv(parametertools.MultiParameter):
    """easily available soil moisture [mm]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

    def update(self):
        """calculation of derived parameter easily available soil moisture.

        Required derived parameter:
          :class:`~hydpy.models.globwat.globwat_derived.SMax`

        Calculated derived parameter:
          :class:`SEAv`

        Basic equation:
          :math:`S_{eav} = S_{max} \\cdot 0.5`

        Examples:

        >>> from hydpy.models.globwat import *
        >>> parameterstep()
        >>> nmbgrids(1)
        >>> derived.smax(30.)
        >>> derived.seav.update()
        >>> derived.seav
        seav(15.0)
        """
        der = self.subpars
        self(der.smax * .5)

class MOY(parametertools.IndexParameter):
    """References the "global" month of the year index array [-]."""
    NDIM, TYPE, TIME, SPAN = 1, int, None, (0, 11)

    def update(self):
        self.setreference(pub.indexer.monthofyear)

class RelArea(parametertools.MultiParameter):
    """relative area [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0, 1)

    def update(self):
        """calculation of derived parameter relative area.

        Required control parameter:
          :class:`~hydpy.models.globwat.globwat_control.Area`

        Calculated derived parameter:
          :class:`RelArea`

        Basic equation:
          :math:`A_{rel} = \\frac {A_Grid}{\\sum A_Grids,n}`

        Examples:

        >>> from hydpy.models.globwat import *
        >>> parameterstep()
        >>> nmbgrids(3)
        >>> control.area(10., 10., 20.)
        >>> derived.relarea.update()
        >>> derived.relarea
        relarea(0.25, 0.25, 0.5)
        """
        con = self.subpars.pars.control
        self(con.area/sum(con.area))

class QFactor(parametertools.SingleParameter):
    """Factor for converting mm/stepsize to m³/s."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

    def update(self):
        con = self.subpars.pars.control
        self(con.area[0]*1000./self.simulationstep.seconds)

class DerivedParameters(parametertools.SubParameters):
    """Derived parameters of globwat, indirectly defined by the user."""
    _PARCLASSES = (Irrigation, SMax, SEAv, MOY, RelArea, QFactor)
