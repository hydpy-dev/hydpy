"""
The |statcorr.DOCNAME.long| base model provides features for the statistical
correction of simulated variables based on observed values.
"""

from hydpy.exe.modelimports import *
from hydpy.models.statcorr.statcorr_model import Model

tester = Tester()
cythonizer = Cythonizer()
