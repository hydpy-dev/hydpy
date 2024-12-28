# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
import hydpy
from hydpy.core import parametertools

# ...from gland
from hydpy.models.gland import gland_control


class DOY(parametertools.DOYParameter):
    """References the "global" month of the year index array [-]."""


class Beta(parametertools.Parameter):
    """Percolation factor [T]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)

    def update(self) -> None:
        r"""Update |Beta| based on the equation
        :math:`5.25 \cdot (3600 / \Delta t)^{0.25}` :cite:p:`ref-Ficchí2017`.

        >>> from hydpy.models.gland import *
        >>> from hydpy import pub
        >>> parameterstep()

        For an hourly simulation step, the value of |Beta| agrees precisely with the
        given equation but is presented as a ratio:

        >>> simulationstep("1h")
        >>> derived.beta.update()
        >>> derived.beta
        beta(21/4)

        For a daily simulation step, the given equation does not precisely result in
        the usual GR4J ratio.  Hence, the nominator is rounded to an integer value:

        >>> simulationstep("1d")
        >>> derived.beta.update()
        >>> derived.beta
        beta(9/4)

        The values for intermediate or shorter simulation steps are modified in the
        same way:

        >>> simulationstep("3h")
        >>> derived.beta.update()
        >>> derived.beta
        beta(16/4)

        >>> simulationstep("15m")
        >>> derived.beta.update()
        >>> derived.beta
        beta(30/4)

        For testing purposes, you can set arbitrary values that are not affected by
        rounding:

        >>> derived.beta(8.0)
        >>> derived.beta
        beta(8.0)
        """
        self.value = (self._nominator) / 4.0

    @property
    def _nominator(self) -> int:
        return round(
            4.0 * (5.25 * (3600.0 / hydpy.pub.options.simulationstep.seconds) ** 0.25)
        )

    def __repr__(self) -> str:
        nominator = self._nominator
        if self.value == nominator / 4.0:
            return f"{self.name}({nominator}/4)"
        return super().__repr__()


class QFactor(parametertools.Parameter):
    """Factor for converting mm/stepsize to m³/s."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)

    CONTROLPARAMETERS = (gland_control.Area,)

    def update(self):
        """Update |QFactor| based on |Area| and the current simulation
        step size.

        >>> from hydpy.models.gland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> simulationstep('1d')
        >>> pub.options.reprdigits = 6
        >>> area(50.0)
        >>> derived.qfactor.update()
        >>> derived.qfactor
        qfactor(0.578704)

        change simulationstep to 1 h

        >>> simulationstep('1h')
        >>> derived.qfactor.update()
        >>> derived.qfactor
        qfactor(13.888889)

        """
        self(
            self.subpars.pars.control.area.value
            * 1000.0
            / hydpy.pub.options.simulationstep.seconds
        )
