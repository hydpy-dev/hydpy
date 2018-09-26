# -*- coding: utf-8 -*-
"""Note that module type |Pub| adds functionality to this module."""
# import from...
# ...the standard library
from typing import Dict, Callable
import sys as _sys
# ...from HydPy
import hydpy

projectname: str
options: 'hydpy.core.optionstools.Options'
indexer: 'hydpy.core.indextools.Indexer'
networkmanager: 'hydpy.core.filetools.NetworkManager'
controlmanager: 'hydpy.core.filetools.ControlManager'
conditionmanager: 'hydpy.core.filetools.ConditionManager'
sequencemanager: 'hydpy.core.filetools.SequenceManager'
timegrids: 'hydpy.core.timetools.Timegrids'
selections: 'hydpy.core.selectiontools.Selections'

scriptfunctions: Dict[str, Callable] = {}

_is_hydpy_bundled = getattr(_sys, 'frozen', False)
"""This parameter is set `True` within HydPy executables only.
Then different features that do not make much sense within an
executable (e.g. the cythonization of models) are disabled.
"""
