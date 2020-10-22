# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, wildcard-import, unused-wildcard-import
"""This simple test model is nearly identical with |test_v1| but works
on 1-dimensional sequences instead on 0-dimensional sequences."""
# imports...
# ...from HydPy
from hydpy.exe.modelimports import *
from hydpy.core import modeltools
# ...from test
from hydpy.models.test import test_model
from hydpy.models.test import test_solver


class Model(modeltools.ELSModel):
    """Test model, Version 3."""
    SOLVERPARAMETERS = (
        test_solver.AbsErrorMax,
        test_solver.RelErrorMax,
        test_solver.RelDTMin,
        test_solver.RelDTMax,
    )
    SOLVERSEQUENCES = ()
    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    ADD_METHODS = ()
    PART_ODE_METHODS = (
        test_model.Calc_QV_V1,
    )
    FULL_ODE_METHODS = (
        test_model.Calc_SV_V1,
    )
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELS = ()


tester = Tester()
cythonizer = Cythonizer()
cythonizer.finalise()
