"""
The |statcorr.DOCNAME.long| base model provides features for the statistical
correction of simulated discharge based on observed discharge values.
"""

from hydpy.exe.modelimports import *
from hydpy.models.statcorr.statcorr_control import NmbSubmodels as _NmbSubmodels

ADDITIONAL_CONTROLPARAMETERS = (_NmbSubmodels,)
del _NmbSubmodels

from hydpy.models.statcorr.statcorr_model import (  # pylint: disable=wrong-import-position
    Model,
)

tester = Tester()
cythonizer = Cythonizer()
