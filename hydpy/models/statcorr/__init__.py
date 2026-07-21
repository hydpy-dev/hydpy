"""
The Statcorr model is...
"""

from hydpy.exe.modelimports import *
from hydpy.models.statcorr import statcorr_control

ADDITIONAL_CONTROLPARAMETERS = (
    statcorr_control.LoggingWindow,
    statcorr_control.NmbOutputCorrModels,
    statcorr_control.PropagateCorrection,
)

from hydpy.models.statcorr.statcorr_model import Model

tester = Tester()
cythonizer = Cythonizer()
