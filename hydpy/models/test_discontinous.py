# pylint: disable=unused-wildcard-import
"""|test_discontinous| serves to test numerical integration strategies only.  It can be
seen from two perspectives.  On the one hand, it implements a simple discontinuous
equation, which causes trouble for numerical integration algorithms.  On the other
hand, it describes simple storage with a constant loss over time as long as some
storage content is left.  The loss rate |Q| and the initial storage content |S| can be
set as required.
"""
# imports...
# ...from HydPy
from hydpy.exe.modelimports import *
from hydpy.core import modeltools

# ...from test
from hydpy.models.test import test_model
from hydpy.models.test import test_solver


class Model(modeltools.ELSModel):
    """|test_discontinous.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(
        short="Test-Discontinuous", description="test model for discontinuous ODEs"
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
    RECEIVER_METHODS = ()
    ADD_METHODS = ()
    PART_ODE_METHODS = (test_model.Calc_Q_V2,)
    FULL_ODE_METHODS = (test_model.Calc_S_V1,)
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()


tester = Tester()
cythonizer = Cythonizer()
