"""
.. _`LARSIM`: http://www.larsim.de/en/the-model/
.. _`Bremicker`: \
http://www.larsim.info/fileadmin/files/Dokumentation/FSH-Bd11-Bremicker.pdf

Base model |lland| is the core of the *HydPy* implementation of all
`LARSIM`_ type models (`Bremicker`).  It consists of routines for the
preparation of meteorological input, the calculation of potential
evaporation, the simulation of water stored on plants, in the snow
layer and the soil, as well as runoff concentration.
"""

# import...
# ...from HydPy
from hydpy.exe.modelimports import *

# ...from lland
from hydpy.models.lland.lland_constants import (
    SIED_D,
    SIED_L,
    VERS,
    ACKER,
    WEINB,
    OBSTB,
    BODEN,
    GLETS,
    GRUE_I,
    FEUCHT,
    GRUE_E,
    BAUMB,
    NADELW,
    LAUBW,
    MISCHW,
    WASSER,
    FLUSS,
    SEE,
)
from hydpy.models.lland.lland_model import Model
from hydpy.models.lland.lland_masks import Masks

tester = Tester()
cythonizer = Cythonizer()
