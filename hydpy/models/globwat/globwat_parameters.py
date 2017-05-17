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
#from hydpy.models.globwat.globwat_constants import RADRYTROP, RAHUMTROP, RAHIGHL, RASUBTROP, RATEMP, RLSUBTROP, RLTEMP, RLBOREAL, FOREST, DESERT, WATER, IRRCPR, IRRCNPR, OTHER, CONSTANTS
from hydpy.models.globwat.globwat_constants import *


class Parameters(parametertools.Parameters):
    """All parameters of the globwat model."""

    def update(self):
        """Determines the values of the parameters handled by
        :class:`DerivedParameters` based on the values of the parameters
        handled by :class:`ControlParameters`.
        """
        #der = self.derived
        self.calc_smax()
        self.calc_seav()
        #self.calc_ia()
        #der.moy.setreference(pub.indexer.monthofyear)
        self.calc_relarea()
        self.calc_irrigation()

    """Calculating derived parameter Irrigation, SMax, SEAv and RelArea"""

    def calc_irrigation(self):
        """settig irrigation true or false for vegetationclasses.

        Required control parameter:
          :class:`~hydpy.models.globwat.globwat_control.Vegetationclass`

        Calculated derived parameter:
          :class:`~hydpy.models.globwat.globwat_derived.irrigation`
        """

        con = self.control
        der = self.derived
        for (idx, vegclass) in enumerate(con.vegetationclass):
            if vegclass in (IRRCPR, IRRCNPR,
#                            IRR_GER, IRR_CZE, IRR_AUT,
#                            IRR_POL, IRR_HUN, IRR_SUI, IRR_ITA, IRR_SLO,
#                            IRR_CRO, IRR_BYH, IRR_ALB, IRR_SER, IRR_SLV,
#                            IRR_UKR, IRR_BUL, IRR_ROM, IRR_MLD
            ):
                der.irrigation[idx] = True
            else:
                der.irrigation[idx] = False

    def calc_smax(self):
        """calculation of derived parameter maximum soil moisture.

        Required control parameter:
          :class:`~hydpy.models.globwat.globwat_control.SCMax`
          :class:`~hydpy.models.globwat.globwat_control.Rtd`

        Calculated derived parameter:
          :class:`~hydpy.models.globwat.globwat_derived.SMax`

        Basic equation:
          :math:`S_{max} = SC_{max} \\cdot Rt_d`

        Examples:

        >>> from hydpy.models.globwat import *
        >>> parameterstep()
        >>> nmbgrids(1)
        >>> control.scmax(50.)
        >>> control.rtd(.6)
        >>> parameters.calc_smax()
        >>> derived.smax
        smax(30.0)
        """
        con = self.control
        der = self.derived
        der.smax(con.scmax * con.rtd)

    def calc_seav(self):
        """calculation of derived parameter easily available soil moisture.

        Required derived parameter:
          :class:`~hydpy.models.globwat.globwat_derived.SMax`

        Calculated derived parameter:
          :class:`~hydpy.models.globwat.globwat_derived.SEAv`

        Basic equation:
          :math:`S_{eav} = S_{max} \\cdot 0.5`

        Examples:

        >>> from hydpy.models.globwat import *
        >>> parameterstep()
        >>> nmbgrids(1)
        >>> derived.smax(30.)
        >>> parameters.calc_seav()
        >>> derived.seav
        seav(15.0)
        """
        der = self.derived
        der.seav(der.smax * .5)

    def calc_relarea(self):
        """calculation of derived parameter relative area.

        Required control parameter:
          :class:`~hydpy.models.globwat.globwat_control.Area`

        Calculated derived parameter:
          :class:`~hydpy.models.globwat.globwat_derived.RelArea`

        Basic equation:
          :math:`A_{rel} = \\frac {A_Grid}{\\sum A_Grids,n}`

        Examples:

        >>> from hydpy.models.globwat import *
        >>> parameterstep()
        >>> nmbgrids(3)
        >>> control.area(10., 10., 20.)
        >>> parameters.calc_relarea()
        >>> derived.relarea
        relarea(0.25, 0.25, 0.5)
        """
        con = self.control
        der = self.derived
        der.relarea(con.area/sum(con.area))


class LanduseMonthParameter(parametertools.KeywordParameter2D):
    """Base class for parameters which values depend both an the actual
    land use class and the actual month.
    """
    COLNAMES = ('jan', 'feb', 'mar', 'apr', 'mai', 'jun',
                'jul', 'aug', 'sep', 'oct', 'nov', 'dec')
    ROWNAMES = tuple(key.lower() for (idx, key)
                     in (sorted((idx, key) for (key, idx) in
                         CONSTANTS.items())))