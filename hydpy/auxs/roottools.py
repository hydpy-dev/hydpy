# -*- coding: utf-8 -*-
"""This module specialises class |Submodel| for root-finding problems.

Module |roottools| provides Python interfaces only.  See the
Cython extension module `rootutils` for the actual implementations
of the mathematical algorithms.
"""

# import...
# ...from standard library
from typing import *

# ...from HydPy
from hydpy.core import modeltools

if TYPE_CHECKING:
    from hydpy.cythons import rootutils
else:
    from hydpy.cythons.autogen import rootutils


class Pegasus(modeltools.Submodel):
    """Root-finder based on the `Pegasus method`_.

    .. _`Pegasus method`: https://link.springer.com/article/10.1007/BF01932959

    The Pegasus method is a root-finding algorithm which sequentially
    decreases its search radius (like the simple bisection algorithm)
    and shows superlinear convergence properties (like the Newton-Raphson
    algorithm).  Our implementation adds a simple "interval widening"
    strategy that comes into play when the given initial interval does not
    contain the root.  This widening should be left for emergencies as
    it might be not always efficient.  So please try to provide to
    initial interval estimates that rather overestimate than underestimate
    the interval width.  Additionally, make sure you apply |Pegasus| on
    monotone functions only.
    """

    CYTHONBASECLASS = rootutils.PegasusBase  # pylint: disable=used-before-assignment
    PYTHONCLASS = rootutils.PegasusPython
    _cysubmodel: rootutils.PegasusBase

    def find_x(
        self,
        x0: float,
        x1: float,
        xmin: float,
        xmax: float,
        xtol: float,
        ytol: float,
        itermax: int,
    ) -> float:
        """Find the relevant root within the interval
        :math:`x0 \\leq x \\leq x1` with an accuracy meeting at least
        one of the absolute tolerance values `xtol` and `ytol` (or the
        accuracy achieved by performing the maximum number of iteration
        steps, defined by argument `itermax`).

        The arguments `xmin` and `xmax` define the smallest and largest
        allowed `x` value, respectively.  Method |Pegasus.find_x| never
        evaluates the underlying function for any `x` value outside these
        bounds, even if its "interval widening" strategy suggests so.
        Instead, it returns the relevant `xmin` or `xmax` value.

        In the following, we explain the details of our Pegasus implementation
        by using method |lland_model.Return_TempSSurface_V1|.

        Method |lland_model.Return_TempSSurface_V1| (used by application model
        |lland_v3|) implements the Pegasus iteration to determine the surface
        temperature of the snow layer with the help of the Pegasus subclass
        |lland_model.PegasusTempSSurface|.  For the correct surface
        temperature, the net energy gain of the surface (defined by method
        |lland_model.Return_EnergyGainSnowSurface_V1|) must be zero.
        Iteration is necessary, as some terms of the net energy gain (for
        example, the emitted longwave radiation) depend on the surface
        temperature in a non-linear manner.

        As a starting point, we use the setting provided by the documentation
        on method |lland_model.Return_TempSSurface_V1| but work in pure Python
        mode for flexibility (more specifically, to have direct access to
        method `find_x`) and focus on a single hydrological response unit
        for simplicity:

        >>> from hydpy import pub
        >>> with pub.options.usecython(False):
        ...     from hydpy.models.lland import *
        ...     simulationstep("1d")
        ...     parameterstep("1d")
        >>> nhru(1)
        >>> lnk(ACKER)
        >>> turb0(2.0)
        >>> turb1(2.0)
        >>> ktschnee(5.0)
        >>> derived.days.update()
        >>> inputs.relativehumidity = 60.0
        >>> states.waes.values = 1.0
        >>> fluxes.tkor = -3.0
        >>> fluxes.reducedwindspeed2m = 3.0
        >>> fluxes.actualvapourpressure = 2.9
        >>> fluxes.netshortwaveradiationsnow = 10.0
        >>> aides.temps = -2.0
        >>> aides.rlatm = 200.0

        Method |lland_model.Return_TempSSurface_V1| finds the following
        surface temperature value:

        >>> model.idx_hru = 0
        >>> from hydpy import round_
        >>> round_(model.return_tempssurface_v1(0))
        -8.307868

        We confirm that the net energy gain corresponding to this surface
        temperature is approximately zero to validate this result:

        >>> round_(model.return_energygainsnowsurface_v1(-8.3078682))
        0.0

        Method `apply_method0` always calls the appropriate target
        method, which is, for |lland_model.PegasusTempSSurface|,
        method |lland_model.Return_EnergyGainSnowSurface_V1|:

        >>> round_(model.pegasustempssurface.apply_method0(-8.3078682))
        0.0

        To check for some exceptional cases, we call the `find_x` method of
        class |lland_model.PegasusTempSSurface| directly.  First, we pass
        the same arguments as in method |lland_model.Return_TempSSurface_V1|
        and thus get the same result:

        >>> round_(model.pegasustempssurface.find_x(
        ...     -50.0, 5.0, -100.0, 100.0, 0.0, 1e-8, 10))
        -8.307868

        Through decreasing the maximum number of iterations, the result
        becomes less accurate:

        >>> round_(model.pegasustempssurface.find_x(
        ...     -50.0, 5.0, -100.0, 100.0, 0.0, 1e-8, 3))
        -8.312628
        >>> round_(model.return_energygainsnowsurface_v1(-8.312628))
        0.09905

        Use the `ytol` argument to control the achieved accuracy more
        explicitly:

        >>> round_(model.pegasustempssurface.find_x(
        ...     -50.0, 5.0, -100.0, 100.0, 0.0, 0.1, 10))
        -8.312628
        >>> round_(model.return_energygainsnowsurface_v1(-8.312628))
        0.09905

        Pass an `xtol` value larger than zero to stop iteration as soon as
        the search interval is small enough:

        >>> round_(model.pegasustempssurface.find_x(
        ...     -50.0, 5.0, -100.0, 100.0, 0.1, 1e-8, 10))
        -8.30786
        >>> round_(model.return_energygainsnowsurface_v1(-8.30786))
        -0.000171

        `x0` does not need to be smaller than `x1`, and `xmin` does not need to be
        smaller than `xmax` by necessity (the algorithm swaps values when necessary):

        >>> round_(model.pegasustempssurface.find_x(
        ...     50.0, -50.0, 100.0, -100.0, 0.0, 1e-8, 10))
        -8.307868

        An ill-defined initial interval might decrease efficiency but
        should usually not affect the result:

        >>> round_(model.pegasustempssurface.find_x(
        ...     0.0, 5.0, -100.0, 100.0, 0.0, 1e-8, 10))
        -8.307868
        >>> round_(model.pegasustempssurface.find_x(
        ...     -50.0, -20.0, -100.0, 100.0, 0.0, 1e-8, 10))
        -8.307868

        Defining proper values for arguments `xmin` and `xmax` provides a way to
        prevent possible program crashes.  As an example, we do not care about
        physics and set the snow layer's temperature to -300 °C.  Theoretically,
        the surface temperature must also be (unrealistically) low to prevent a
        considerable energy gain of the surface due to an extreme temperature
        gradient within the snow layer. However, -100 °C is the lowest value allowed,
        so method |lland_model.PegasusTempSSurface| returns this boundary-value.
        It is up to the model developer to handle such misleading responses
        (if possible):

        >>> aides.temps = -400
        >>> round_(model.pegasustempssurface.find_x(
        ...     -50.0, 5.0, -100.0, 100.0, 0.0, 1e-8, 10))
        -100.0
        >>> round_(model.return_energygainsnowsurface_v1(-100.0))
        -524.133374

        To demonstrate the upper boundary's functionality, we set the snow layer
        temperature to 4'000 °C (also not the most plausible value, of course):

        >>> aides.temps = 4000.0
        >>> round_(model.pegasustempssurface.find_x(
        ...     -50.0, 5.0, -100.0, 100.0, 0.0, 1e-8, 10))
        100.0
        >>> round_(model.return_energygainsnowsurface_v1(100.0))
        3561.059134

        Finally, we evaluate some additional snow layer temperatures
        to show that everything works consistently:

        >>> from hydpy import print_values
        >>> for temps in [-500, -400, -300, -4, -2, 2, 2000, 3000, 4000]:
        ...    aides.temps = temps
        ...    tempssurface = model.pegasustempssurface.find_x(
        ...        -50.0, 5.0, -100.0, 100.0, 0.0, 1e-8, 10)
        ...    energygain = model.return_energygainsnowsurface_v1(tempssurface)
        ...    print_values([temps, tempssurface, energygain])
        -500, -100.0, -1024.133374
        -400, -100.0, -524.133374
        -300, -100.0, -24.133374
        -4, -8.790047, 0.0
        -2, -8.307868, 0.0
        2, -7.353441, 0.0
        2000, 85.175508, 0.0
        3000, 97.204856, 0.0
        4000, 100.0, 3561.059134
        """
        return self._cysubmodel.find_x(x0, x1, xmin, xmax, xtol, ytol, itermax)

    def apply_method0(self, value: float) -> float:
        """Apply the model method relevant for root-finding."""
        return self._cysubmodel.apply_method0(value)
