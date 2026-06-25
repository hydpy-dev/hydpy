"""
|sw1d.DOCNAME.long| provides features for implementing models for approximating the
1-dimensional shallow water equations in a "hydrodynamic" manner to account for
situations like backwater effects that "hydrological" methods cannot handle well.
"""

from hydpy.auxs.anntools import ANN
from hydpy.auxs.ppolytools import Poly, PPoly
from hydpy.exe.modelimports import *
from hydpy.models.sw1d.sw1d_control import NmbSegments as _NmbSegments

ADDITIONAL_CONTROLPARAMETERS = (_NmbSegments,)  # ToDo: Turn into a model member?
del _NmbSegments

from hydpy.models.sw1d.sw1d_model import Model  # pylint: disable=wrong-import-position

tester = Tester()
cythonizer = Cythonizer()
