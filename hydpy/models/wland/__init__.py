"""
.. _`WALRUS`: https://www.wur.nl/en/Research-Results/Chair-groups/Environmental-Sciences/Hydrology-and-Quantitative-Water-Management-Group/Research/WALRUS-1.htm  # pylint: disable=line-too-long

Base model |wland| is the core of the *HydPy* implementation of all `WALRUS`_ type
models :cite:p:`ref-Brauer2014`, focussing on the interaction between surface water
and near-surface groundwater.
"""

# import...
# ...from HydPy
from hydpy.exe.modelimports import *

# ...from wland
from hydpy.models.wland.wland_constants import (
    SAND,
    LOAMY_SAND,
    SANDY_LOAM,
    SILT_LOAM,
    LOAM,
    SANDY_CLAY_LOAM,
    SILT_CLAY_LOAM,
    CLAY_LOAM,
    SANDY_CLAY,
    SILTY_CLAY,
    CLAY,
    SEALED,
    FIELD,
    WINE,
    ORCHARD,
    SOIL,
    PASTURE,
    WETLAND,
    TREES,
    CONIFER,
    DECIDIOUS,
    MIXED,
)
from hydpy.models.wland.wland_model import Model
from hydpy.models.wland.wland_constants import *
from hydpy.models.wland.wland_masks import Masks

tester = Tester()
cythonizer = Cythonizer()
