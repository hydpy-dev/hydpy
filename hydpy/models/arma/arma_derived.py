# pylint: disable=missing-module-docstring

import numpy

from hydpy.core import parametertools
from hydpy.core.typingtools import *
from hydpy.models.arma import arma_control


class Nmb(parametertools.NmbParameter):
    """Number of response functions [-]."""

    SPAN = (0, None)

    CONTROLPARAMETERS = (arma_control.Responses,)

    def update(self) -> None:
        """Determine the number of response functions.

        >>> from hydpy.models.arma import *
        >>> parameterstep("1d")
        >>> responses(((1.0, 2.0), (1.0,)), th_3=((1.0,), (1.0, 2.0, 3.0)))
        >>> derived.nmb.update()
        >>> derived.nmb
        nmb(2)

        Updating |Nmb| also adjusts the shapes of all sequences that depend on the
        number of response functions, if necessary (see the mixin class |MixinNmb| and
        the log sequences |LogIn| and |LogOut|).
        """
        self(len(self.subpars.pars.control.responses))


class MaxQ(parametertools.Parameter):
    """Maximum discharge values of the respective ARMA models [m³/s]."""

    NDIM: Final[Literal[1]] = 1
    TYPE: Final = float
    SPAN = (0, None)

    CONTROLPARAMETERS = (arma_control.Responses,)

    def update(self) -> None:
        """Determine the maximum discharge values.

        >>> from hydpy.models.arma import *
        >>> parameterstep("1d")
        >>> responses(((1., 2.), (1.,)), th_3=((1.,), (1., 2., 3.)))
        >>> derived.maxq.update()
        >>> derived.maxq
        maxq(0.0, 3.0)
        """
        responses = self.subpars.pars.control.responses
        self.shape = len(responses)
        self.value = responses.thresholds


class DiffQ(parametertools.Parameter):
    """Differences between the values of |MaxQ| [m³/s]."""

    NDIM: Final[Literal[1]] = 1
    TYPE: Final = float
    SPAN = (0, None)

    CONTROLPARAMETERS = (arma_control.Responses,)

    def update(self) -> None:
        """Determine the "max Q deltas".

        >>> from hydpy.models.arma import *
        >>> parameterstep("1d")
        >>> responses(((1., 2.), (1.,)), th_3=((1.,), (1., 2., 3.)))
        >>> derived.diffq.update()
        >>> derived.diffq
        diffq(3.0)
         >>> responses(((1., 2.), (1.,)))
        >>> derived.diffq.update()
        >>> derived.diffq
        diffq([])
        """
        responses = self.subpars.pars.control.responses
        self.shape = len(responses) - 1
        self.value = numpy.diff(responses.thresholds)


class AR_Order(parametertools.Parameter):
    """Number of AR coefficients of the different responses [-]."""

    NDIM: Final[Literal[1]] = 1
    TYPE: Final = int
    SPAN = (0, None)

    CONTROLPARAMETERS = (arma_control.Responses,)

    def update(self) -> None:
        """Determine the total number of AR coefficients.

        >>> from hydpy.models.arma import *
        >>> parameterstep("1d")
        >>> responses(((1., 2.), (1.,)), th_3=((1.,), (1., 2., 3.)))
        >>> derived.ar_order.update()
        >>> derived.ar_order
        ar_order(2, 1)
        """
        responses = self.subpars.pars.control.responses
        self.shape = len(responses)
        self.value = responses.ar_orders


class MA_Order(parametertools.Parameter):
    """Number of MA coefficients of the different responses [-]."""

    NDIM: Final[Literal[1]] = 1
    TYPE: Final = int
    SPAN = (0, None)

    CONTROLPARAMETERS = (arma_control.Responses,)

    def update(self) -> None:
        """Determine the total number of MA coefficients.

        >>> from hydpy.models.arma import *
        >>> parameterstep("1d")
        >>> responses(((1., 2.), (1.,)), th_3=((1.,), (1., 2., 3.)))
        >>> derived.ma_order.update()
        >>> derived.ma_order
        ma_order(1, 3)
        """
        responses = self.subpars.pars.control.responses
        self.shape = len(responses)
        self.value = responses.ma_orders


class AR_Coefs(parametertools.Parameter):
    """AR coefficients of the different responses [-]."""

    NDIM: Final[Literal[2]] = 2
    TYPE: Final = float

    CONTROLPARAMETERS = (arma_control.Responses,)

    def update(self) -> None:
        """Determine all AR coefficients.

        >>> from hydpy.models.arma import *
        >>> parameterstep("1d")
        >>> responses(((1., 2.), (1.,)), th_3=((1.,), (1., 2., 3.)))
        >>> derived.ar_coefs.update()
        >>> derived.ar_coefs
        ar_coefs([[1.0, 2.0],
                  [1.0, nan]])
        """
        coefs = self.subpars.pars.control.responses.ar_coefs
        self.shape = coefs.shape
        self.value = coefs


class MA_Coefs(parametertools.Parameter):
    """MA coefficients of the different responses [-]."""

    NDIM: Final[Literal[2]] = 2
    TYPE: Final = float

    CONTROLPARAMETERS = (arma_control.Responses,)

    def update(self) -> None:
        """Determine all MA coefficients.

        >>> from hydpy.models.arma import *
        >>> parameterstep("1d")
        >>> responses(((1., 2.), (1.,)), th_3=((1.,), (1., 2., 3.)))
        >>> derived.ma_coefs.update()
        >>> derived.ma_coefs
        ma_coefs([[1.0, nan, nan],
                  [1.0, 2.0, 3.0]])
        """
        coefs = self.subpars.pars.control.responses.ma_coefs
        self.shape = coefs.shape
        self.value = coefs
