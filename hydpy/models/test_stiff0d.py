# pylint: disable=unused-wildcard-import
"""|test_stiff0d| is a simple test model that serves to test numerical integration
strategies.  It can be seen from two perspectives.  On the one hand, it implements the
Dahlquist test equation (on the real axis only), which is related to stiff initial
value problems.  On the other hand, it describes a simple storage with a linear loss
term and without any input.  The loss rate |Q| and the initial storage content |S| can
be set as required.
"""
# imports...
# ...HydPy specific
from hydpy.exe.modelimports import *
from hydpy.core import modeltools

# ...from test
from hydpy.models.test import test_model
from hydpy.models.test import test_solver


class Model(modeltools.ELSModel):
    """|test_stiff0d.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(
        short="Test-Stiff-0D",
        description="test model for stiff ODEs and scalar sequences",
    )
    __HYDPY_ROOTMODEL__ = None

    SOLVERPARAMETERS = (
        test_solver.AbsErrorMax,
        test_solver.RelErrorMax,
        test_solver.RelDTMin,
        test_solver.RelDTMax,
    )
    SOLVERSEQUENCES = ()
    INLET_METHODS = ()
    OBSERVER_METHODS = ()
    RECEIVER_METHODS = ()
    ADD_METHODS = ()
    PART_ODE_METHODS = (test_model.Calc_Q_V1,)
    FULL_ODE_METHODS = (test_model.Calc_S_V1,)
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()


tester = Tester()
cythonizer = Cythonizer()
