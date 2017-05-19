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


class LanduseMonthParameter(parametertools.KeywordParameter2D):
    """Base class for parameters which values depend both an the actual
    land use class and the actual month.
    """
    COLNAMES = ('jan', 'feb', 'mar', 'apr', 'mai', 'jun',
                'jul', 'aug', 'sep', 'oct', 'nov', 'dec')
    ROWNAMES = tuple(key.lower() for (idx, key)
                     in (sorted((idx, key) for (key, idx) in
                         CONSTANTS.items())))
