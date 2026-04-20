# pylint: disable=missing-module-docstring

import hydpy
from hydpy.models.tm import tm_parameters
from hydpy.models.tm import tm_control


class QF(tm_parameters.Parameter0D):
    """Factor for converting mm/T to m³/s."""

    SPAN = (0.0, None)

    CONTROLPARAMETERS = (tm_control.A,)

    def update(self) -> None:
        """Update |QF| based on |A| and the current simulation step size.

        >>> from hydpy.models.tm import *
        >>> simulationstep("2h")
        >>> parameterstep()
        >>> a(3.0)
        >>> derived.qf.update()
        >>> derived.qf
        qf(0.416667)
        """
        self(
            self.subpars.pars.control.a
            * 1000.0
            / hydpy.pub.options.simulationstep.seconds
        )
