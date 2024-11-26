# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools
from hydpy.models.musk import musk_control


class NmbRuns(parametertools.SolverParameter):
    """The number of (repeated) runs of the |RunModel.RUN_METHODS| of the current
    application model per simulation step [-].

    Model developers need to subclass |NmbRuns| for each application model to define a
    suitable `INIT` value.
    """

    NDIM = 0
    TYPE = int
    TIME = None


class ToleranceWaterDepth(parametertools.SolverParameter):
    """Acceptable water depth error for determining the reference water depth [m]."""

    NDIM = 0
    TYPE = float
    TIME = None
    SPAN = (0.0, None)
    INIT = 0.0


class ToleranceDischarge(parametertools.SolverParameter):
    """Acceptable discharge error for determining the reference water depth [m³/s]."""

    NDIM = 0
    TYPE = float
    TIME = None
    SPAN = (0.0, None)
    INIT = 0.000001

    CONTROLPARAMETERS = (musk_control.CatchmentArea,)

    def modify_init(self) -> float:
        r"""Adjust and return the value of class constant `INIT`.

        Ideally, in the long term, the iterative search for the reference water depth
        takes comparable computation time and yields comparable relative accuracy for
        channels that pass different amounts of water.  We use the catchment size as an
        indicator of the expected (average) amount of water.  For central European
        conditions, the average specific discharge is usually (much) larger than
        0.001 m³/s/km².  The error tolerance must be much lower, especially for
        handling low-flow situations.  Hence, the return value of method
        |ToleranceDischarge.modify_init| is based on one per mille of this specific
        discharge value:

        :math:`ToleranceDischarge = 0.001 / 1000 \cdot CatchmentArea`

        >>> from hydpy.models.musk import *
        >>> parameterstep()
        >>> from hydpy import round_
        >>> round_(solver.tolerancedischarge.INIT, 12)
        0.000001
        >>> catchmentarea(2000.0)
        >>> solver.tolerancedischarge.update()
        >>> solver.tolerancedischarge
        tolerancedischarge(0.002)
        """
        return self.INIT * self.subpars.pars.control.catchmentarea.value
