# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, wildcard-import, unused-wildcard-import
"""This simple test model is thought for testing numerical integration
strategies.  It can be seen from two perspectives.  On the one hand
it implements the Dahlquist test equation (on the real axis only), which is
related to stiff initial value problems.  On the other hand it describes a
simple storage with a linear loss term and without any input.  The loss rate
|Q| and the initial storage content |S| can be set as required.
"""
# imports...
# ...HydPy specific
from hydpy.exe.modelimports import *
from hydpy.core import modeltools
# ...from test
from hydpy.models.test import test_model
from hydpy.models.test import test_solver


class Model(modeltools.ELSModel):
    """Test model, Version 1."""
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
        test_model.Calc_Q_V1,
    )
    FULL_ODE_METHODS = (
        test_model.Calc_S_V1,
    )
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELS = ()


tester = Tester()
cythonizer = Cythonizer()
cythonizer.finalise()
