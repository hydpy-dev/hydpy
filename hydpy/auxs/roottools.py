# -*- coding: utf-8 -*-
"""This module specialises class |Submodel| for root-finding problems.

Module |roottools| provides Python interfaces only.  See the
Cython extension module |rootutils| for the actual implementations
of the mathematical algorithms.
"""

# import...
# ...from HydPy
from hydpy.core import modeltools
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

    CYTHONBASECLASS = rootutils.PegasusBase
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
        by using method |lland_model.Calc_TempsSurface_V1|.

        Method |lland_model.Calc_TempsSurface_V1| (used by application model
        |lland_v3|) implements the Pegasus iteration to determine the surface
        temperature of the snow layer with the help of the Pegasus subclass
        |lland_model.PegasusTempSSurface|.  For the correct surface
        temperature, the net energy gain of the surface (defined by method
        |lland_model.Calc_EnergyBalanceSurface_V1|) must be zero.  Iteration
        is necessary, as some terms of the net energy gain (for example, the
        emitted longwave radiation) depend on the surface temperature
        in a non-linear manner.

        As a starting point, we use the setting provided by the documentation
        on method |lland_model.Calc_TempsSurface_V1| but focus on a single
        hydrological response unit only:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(1)
        >>> turb0(2.0)
        >>> turb1(2.0)
        >>> fratm(1.28)
        >>> tempssurfaceflag(True)
        >>> derived.seconds(24*60*60)
        >>> derived.k = 0
        >>> inputs.sunshineduration = 10.0
        >>> inputs.relativehumidity = 60.0
        >>> states.waes.values = 1.0
        >>> fluxes.actualvapourpressure = 0.29
        >>> fluxes.netshortwaveradiation = 1.0
        >>> fluxes.possiblesunshineduration = 12.0
        >>> fluxes.tkor = -3.0
        >>> fluxes.windspeed10m = 3.0
        >>> aides.temps = -2.0

        Method |lland_model.Calc_TempsSurface_V1| finds the following
        surface temperature value:

        >>> model.calc_tempssurface_v1()
        >>> fluxes.tempssurface
        tempssurface(-4.832608)

        To validate this result, we confirm that the net energy gain
        corresponding to this surface temperature is approximately zero:

        >>> from hydpy import round_
        >>> round_(model.calc_energybalancesurface_v1(
        ...     fluxes.tempssurface.values[0]))
        0.0

        Method `apply_method0` always calls the appropriate target
        method, which is, for |lland_model.PegasusTempSSurface|,
        method |lland_model.Calc_EnergyBalanceSurface_V1|:

        >>> round_(model.pegasustempssurface.apply_method0(
        ...     fluxes.tempssurface.values[0]))
        0.0

        To check for some exceptional cases, we call the `find_x` method of
        class |lland_model.PegasusTempSSurface| directly.  First, we pass
        the same arguments as in method |lland_model.Calc_TempsSurface_V1|
        and thus get the same result:

        >>> round_(model.pegasustempssurface.find_x(
        ...     -50.0, 5.0, -100.0, 100.0, 0.0, 1e-8, 10))
        -4.832608

        Through decreasing the maximum number of iterations, the result
        becomes less accurate:

        >>> round_(model.pegasustempssurface.find_x(
        ...     -50.0, 5.0, -100.0, 100.0, 0.0, 1e-8, 2))
        -4.951621
        >>> round_(model.calc_energybalancesurface_v1(
        ...     fluxes.tempssurface.values[0]))
        0.206736

        Use the `ytol` argument to control the achieved accuracy more
        explicitly:

        >>> round_(model.pegasustempssurface.find_x(
        ...     -50.0, 5.0, -100.0, 100.0, 0.0, 0.1, 10))
        -4.833198
        >>> round_(model.calc_energybalancesurface_v1(
        ...     fluxes.tempssurface.values[0]))
        0.001025

        Pass an `xtol` value larger than zero to stop iteration as soon as
        the search interval is small enough:

        >>> round_(model.pegasustempssurface.find_x(
        ...     -50.0, 5.0, -100.0, 100.0, 0.1, 1e-8, 10))
        -4.832608
        >>> round_(model.calc_energybalancesurface_v1(
        ...     fluxes.tempssurface.values[0]))
        -0.000001

        `x0` does not need to be smaller than `x1`:

        >>> round_(model.pegasustempssurface.find_x(
        ...     50.0, -50.0, -100.0, 100.0, 0.0, 1e-8, 10))
        -4.832608

        An ill-defined initial interval might decrease efficiency but
        should usually not affect the result:

        >>> round_(model.pegasustempssurface.find_x(
        ...     0.0, 5.0, -100.0, 100.0, 0.0, 1e-8, 10))
        -4.832608
        >>> round_(model.pegasustempssurface.find_x(
        ...     -50.0, -20.0, -100.0, 100.0, 0.0, 1e-8, 10))
        -4.832608

        Defining proper values for arguments `xmin` and `xmax` provides
        a way to prevent possible program crashes.  As an
        example, we do not care about physics and set the temperature
        of the snow layer to -400 °C.  Now, theoretically, the surface
        temperature must also be (unrealistically) low to prevent from a
        considerable energy gain of the surface due to an extreme temperature
        gradient within the snow layer. However, -100 °C is the lowest value
        allowed, which is why method |lland_model.PegasusTempSSurface|
        returns this boundary-value.  It is up to the model developer to
        handle such misleading responses (if possible):

        >>> aides.temps = -400
        >>> round_(model.pegasustempssurface.find_x(
        ...     -50.0, 5.0, -100.0, 100.0, 0.0, 1e-8, 10))
        -100.0
        >>> round_(model.calc_energybalancesurface_v1(
        ...     fluxes.tempssurface.values[0]))
        -40.944988

        To demonstrate the functionality of the upper boundary, we set the
        snow layer temperature to 4'000 °C (also not the most plausible
        value, of course):

        >>> aides.temps = 4000.0
        >>> round_(model.pegasustempssurface.find_x(
        ...     -50.0, 5.0, -100.0, 100.0, 0.0, 1e-8, 10))
        100.0
        >>> round_(model.calc_energybalancesurface_v1(
        ...     fluxes.tempssurface.values[0]))
        805.038124

        Finally, we evaluate some additional snow layer temperatures
        to show that everything works consistently:

        >>> from hydpy import print_values
        >>> for temps in [-500, -400, -300, -4, -2, 2, 2000, 3000, 4000]:
        ...    aides.temps = temps
        ...    tempssurface = model.pegasustempssurface.find_x(
        ...        -50.0, 5.0, -100.0, 100.0, 0.0, 1e-8, 10)
        ...    energybalancesurface = model.calc_energybalancesurface_v1(
        ...         tempssurface)
        ...    print_values([temps, tempssurface, energybalancesurface])
        -500, -100.0, -84.144988
        -400, -100.0, -40.944988
        -300, -98.161514, 0.0
        -4, -5.331078, 0.0
        -2, -4.832608, 0.0
        2, -3.844281, 0.0
        2000, 97.879015, 0.0
        3000, 100.0, 373.038124
        4000, 100.0, 805.038124
        """
        return self._cysubmodel.find_x(x0, x1, xmin, xmax, xtol, ytol, itermax)

    def apply_method0(self, value: float) -> float:
        """Apply the model method relevant for root-finding."""
        return self._cysubmodel.apply_method0(value)
