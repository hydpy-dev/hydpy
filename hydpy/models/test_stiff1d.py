# -*- coding: utf-8 -*-
# pylint: disable=unused-wildcard-import
"""|test_stiff1d| similar to |test_stiff0d| but works on 1-dimensional sequences
instead of 0-dimensional sequences."""
# imports...
# ...from HydPy
from hydpy.exe.modelimports import *
from hydpy.core import modeltools

# ...from test
from hydpy.models.test import test_model
from hydpy.models.test import test_solver


class Model(modeltools.ELSModel):
    """|test_stiff1d.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(
        short="Test-Stiff-1D",
        description="test model for stiff ODEs and 1-dimensional sequences",
    )

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
    PART_ODE_METHODS = (test_model.Calc_QV_V1,)
    FULL_ODE_METHODS = (test_model.Calc_SV_V1,)
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()


tester = Tester()
cythonizer = Cythonizer()
