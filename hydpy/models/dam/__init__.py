# -*- coding: utf-8 -*-
# pylint: disable=wildcard-import
"""
The HydPy-D base model provides features to implement water barriers like
dams, weirs, lakes, or polders.
"""
# import...
# ...from HydPy
from hydpy.core.modelimports import *
from hydpy.auxs.anntools import ann
# ...from dam
from hydpy.models.dam.dam_control import ControlParameters
from hydpy.models.dam.dam_derived import DerivedParameters
from hydpy.models.dam.dam_solver import SolverParameters
from hydpy.models.dam.dam_fluxes import FluxSequences
from hydpy.models.dam.dam_states import StateSequences
from hydpy.models.dam.dam_logs import LogSequences
from hydpy.models.dam.dam_aides import AideSequences
from hydpy.models.dam.dam_inlets import InletSequences
from hydpy.models.dam.dam_outlets import OutletSequences
from hydpy.models.dam.dam_receivers import ReceiverSequences
from hydpy.models.dam.dam_senders import SenderSequences
from hydpy.models.dam.dam_model import Model

autodoc_basemodel()

# pylint: disable=invalid-name
tester = Tester()
cythonizer = Cythonizer()
cythonizer.complete()
