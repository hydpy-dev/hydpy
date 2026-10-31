"""
The |statcorr.DOCNAME.long| base model provides features for the statistical
correction of simulated discharge based on observed discharge values.
"""

from hydpy.exe.modelimports import *
from hydpy.models.statcorr import statcorr_control

ADDITIONAL_CONTROLPARAMETERS = (
    statcorr_control.NmbSubmodels,
    statcorr_control.Propagate,
)

from hydpy.models.statcorr.statcorr_model import (  # pylint: disable=wrong-import-position
    Model,
)

tester = Tester()
cythonizer = Cythonizer()
