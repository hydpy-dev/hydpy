# pylint: disable=missing-module-docstring

from hydpy.core import parametertools
from hydpy.core import sequencetools
from hydpy.core.typingtools import *
from hydpy.models.arma import arma_derived


class LogIn(sequencetools.LogSequence):
    """Recent and past inflow portions for applying the different MA processes [m³/s].

    The number of rows of |LogIn| matches the number of response functions, and the
    number of columns matches the highest number of MA coefficients:

    >>> from hydpy.models.arma import *
    >>> parameterstep("1d")
    >>> responses(((1.0, 2.0), (1.0,)), th_3=((1.0,), (1.0, 2.0, 3.0)))
    >>> derived.nmb.update()
    >>> logs.login
    login([[nan, nan, nan],
           [nan, nan, nan]])

    Updating parameter |Nmb| again does not reset the available values as long as the
    required shape remains unchanged:

    >>> logs.login = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
    >>> derived.nmb.update()
    >>> logs.login
    login([[1.0, 2.0, 3.0],
           [4.0, 5.0, 6.0]])

    Otherwise, it does:

    >>> responses(((1.0, 2.0), (1.0,)), th_3=((1.0,), (1.0, 2.0)))
    >>> derived.nmb.update()
    >>> logs.login
    login([[nan, nan],
           [nan, nan]])

    The shape remains unchanged when the value of |Nmb| does not agree with the number
    of response functions defined by parameter |Responses|, which is only possible
    when setting it manually instead of calling method |Nmb.update|:

    >>> derived.nmb(3)
    >>> logs.login.shape
    (2, 2)
    """

    NDIM: Final[Literal[2]] = 2

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        if isinstance(p, arma_derived.Nmb):
            responses = p.subpars.pars.control.responses
            if len(responses) == p.value:
                orders = responses.ma_orders
                self.__hydpy__change_shape_if_necessary__(
                    (p.value, max(orders, default=0))
                )


class LogOut(sequencetools.LogSequence):
    """Past outflow portions for applying different AR processes [m³/s].

    |LogOut| works like |LogIn|, except that its number of columns agrees with the
    highest number of AR coefficients:

    >>> from hydpy.models.arma import *
    >>> parameterstep("1d")
    >>> responses(((1.0, 2.0), (1.0,)), th_3=((1.0,), (1.0, 2.0, 3.0)))
    >>> derived.nmb.update()
    >>> logs.logout.shape
    (2, 2)
    """

    NDIM: Final[Literal[2]] = 2

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        if isinstance(p, arma_derived.Nmb):
            responses = p.subpars.pars.control.responses
            if len(responses) == p.value:
                orders = responses.ar_orders
                self.__hydpy__change_shape_if_necessary__(
                    (p.value, max(orders, default=0))
                )
