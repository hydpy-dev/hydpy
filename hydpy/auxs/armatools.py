"""This module provides additional features for module |iuhtools|, related to
Autoregressive-Moving Average (ARMA) models."""

# import...
# ...from standard library
import itertools
import warnings

# ...from site-packages
import numpy

# ...from HydPy
import hydpy
from hydpy import config
from hydpy.core import exceptiontools
from hydpy.core import objecttools
from hydpy.auxs import statstools
from hydpy.core.typingtools import *

if TYPE_CHECKING:
    from matplotlib import pyplot
    from scipy import integrate
else:
    pyplot = exceptiontools.OptionalImport("pyplot", ["matplotlib.pyplot"], locals())
    integrate = exceptiontools.OptionalImport(
        "integrate", ["scipy.integrate"], locals()
    )


class MA:
    """Moving Average Model.

    You can set the MA coefficients manually:

    >>> from hydpy import MA
    >>> ma = MA(coefs=(0.8, 0.2))
    >>> ma
    MA(coefs=(0.8, 0.2))
    >>> ma.coefs = 0.2, 0.8
    >>> ma
    MA(coefs=(0.2, 0.8))

    Otherwise, they are determined by method |MA.update_coefs| based on an integrable
    function.  Usually, this function is an |IUH| subclass instance, but (as in the
    following example) other function objects defining instantaneous unit hydrographs
    are acceptable, too.  However, they should be well-behaved (e.g. be relatively
    smooth, unimodal, and strictly positive and have an integral surface of one in the
    positive range).

    For educational purposes, we apply some (problematic) discontinuous functions in
    the following.  The first example is a simple rectangle impulse:

    >>> import numpy
    >>> def iuh(x):
    ...     y = numpy.zeros(x.shape)
    ...     y[x < 20.0] = 0.05
    ...     return y
    >>> ma = MA(iuh=iuh)

    As our custom function object cannot estimate the first moment of its response on
    its own, we need to assign this information manually:

    >>> ma.iuh.moment1 = 10.0

    The limited precision of method |MA.update_coefs| results in observable
    inaccuracies at the impulse's edges:

    >>> ma.update_coefs()  # doctest: +ELLIPSIS
    >>> ma
    MA(coefs=(0.025025, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05,
              0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05,
              0.05, 0.024975))

    In such cases, you can increase the number of nodes at which method
    |MA.update_coefs| evaluates the impulse function at the cost of more computation
    time:

    >>> ma.nmb_nodes = 100000
    >>> ma.update_coefs()
    >>> ma
    MA(coefs=(0.025, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05,
              0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05,
              0.025))

    You can modify the number of resulting coefficients via the attribute
    |MA.smallest_coeff|:

    >>> ma.smallest_coeff = 0.03
    >>> ma.nmb_nodes = 1000
    >>> ma.update_coefs()
    >>> ma
    MA(coefs=(0.025666, 0.051281, 0.051281, 0.051281, 0.051281, 0.051281,
              0.051281, 0.051281, 0.051281, 0.051281, 0.051281, 0.051281,
              0.051281, 0.051281, 0.051281, 0.051281, 0.051281, 0.051281,
              0.051281, 0.051281))

    The first two central moments of the time delay subsume describing how an MA model
    behaves:

    >>> def iuh(x):
    ...     y = numpy.zeros(x.shape)
    ...     y[x < 1.0] = 1.0
    ...     return y
    >>> ma = MA(iuh=iuh)
    >>> ma.iuh.moment1 = 0.5
    >>> ma
    MA(coefs=(0.500253, 0.499747))
    >>> from hydpy import round_
    >>> round_(ma.moments, 6)
    0.499747, 0.5

    The first central moment is the weighted time delay (mean lag time).  The second
    central moment is the weighted mean deviation from the mean lag time (diffusion).

    MA objects can return the turning point in the recession part of their MA
    coefficients.  We demonstrate this for the right side of the probability density
    function of the normal distribution with zero mean and a standard deviation
    (turning point) of 10:

    >>> from scipy import stats
    >>> ma = MA(iuh=lambda x: 2.0 * stats.norm.pdf(x, 0.0, 2.0))
    >>> ma.iuh.moment1 = 1.35
    >>> ma
    MA(coefs=(0.195578, 0.346589, 0.241841, 0.132744, 0.057307, 0.019454,
              0.005192, 0.001089, 0.00018, 0.000023, 0.000002, 0.0, 0.0))
    >>> round_(ma.turningpoint)
    2, 0.241841

    Note that the first returned value is the index of the MA coefficient closest to
    the turning point, and not a high-precision estimate of the real turning point of
    the instantaneous unit hydrograph.

    You can also use the following plotting command to verify the position of the
    turning point (printed as a red dot):

    >>> figure = ma.plot(threshold=0.9)
    >>> from hydpy.core.testtools import save_autofig
    >>> save_autofig(f"MA_plot.png", figure)

        .. image:: MA_plot.png
           :width: 400

    Turning point detection also works for functions which include both a rising and a
    falling limb.  We show this by shifting the normal distribution to the right:

    >>> ma.iuh = lambda x: 1.02328 * stats.norm.pdf(x, 4.0, 2.0)
    >>> ma.iuh.moment1 = 3.94
    >>> ma.update_coefs()
    >>> ma
    MA(coefs=(0.019335, 0.06793, 0.123759, 0.177362, 0.199964, 0.177362,
              0.123759, 0.06793, 0.029326, 0.009956, 0.002657, 0.000557,
              0.000092, 0.000012, 0.000001, 0.0, 0.0))
    >>> round_(ma.turningpoint)
    6, 0.123759

    For MA models of order one, property |MA.turningpoint| returns the index and value
    of the first ordinate:

    >>> ma.coefs = [1.0]
    >>> round_(ma.turningpoint)
    0, 1.0

    Undetectable turning points result in the following error:

    >>> ma.coefs = 1.0, 1.0, 1.0
    >>> ma.turningpoint
    Traceback (most recent call last):
    ...
    RuntimeError: Not able to detect a turning point in the impulse response defined \
by the MA coefficients `1.0, 1.0, 1.0`.

    For very spiky response functions, the underlying integration algorithm might fail.
    Then it is assumed that the complete mass of the response function happens at a
    single delay time, defined by the property `moment1` of the instantaneous unit
    hydrograph.  In this case, we also raise an additional warning message to allow
    users to determine the coefficients using an alternative approach:

    >>> def iuh(x):
    ...     y = numpy.zeros(x.shape)
    ...     y[(4.23 < x) & (x < 4.24)] = 10.0
    ...     return y
    >>> ma.iuh = iuh
    >>> ma.iuh.moment1 = 4.25
    >>> from hydpy.core.testtools import warn_later
    >>> with warn_later():
    ...     ma.update_coefs()  # doctest: +ELLIPSIS
    UserWarning: During the determination of the MA coefficients corresponding to the \
instantaneous unit hydrograph ... a numerical integration problem occurred.  \
Please check the calculated coefficients: 0.0, 0.0, 0.0, 0.0, 0.75, 0.25.

    >>> ma
    MA(coefs=(0.0, 0.0, 0.0, 0.0, 0.75, 0.25))

    For speedy responses, there should usually be only one MA coefficient:

    >>> ma = MA(iuh=lambda x: 1e6 * numpy.exp(-1e6 * x))
    >>> ma.iuh.moment1 = 6.931e-7
    >>> with warn_later():  # doctest: +ELLIPSIS
    ...     ma
    MA(coefs=(1.0,))
    UserWarning: During the determination of the MA coefficients corresponding to the \
instantaneous unit hydrograph `...` a numerical integration problem occurred.  Please \
check the calculated coefficients: 1.0.
    """

    smallest_coeff: float = 1e-9  # 1e-6
    """Smallest MA coefficient allowed at the end of the response."""

    nmb_nodes = 1000
    """The number of nodes usually applied for numerically integrating all MA 
    coefficients."""

    nmb_nodes_extra = 100000
    """The number of nodes applied for numerically integrating the MA coefficient if
    the instantaneous unit hydrograph has a small delay time.
    
    |MA.nmb_nodes_extra| is ignored if set to a smaller value than |MA.nmb_nodes|. 
    """

    _coefs: VectorFloat | None = None

    def __init__(self, iuh=None, coefs=None) -> None:
        self.iuh = iuh
        if coefs is not None:
            self.coefs = coefs

    @property
    def coefs(self) -> VectorFloat:
        """|numpy.ndarray| containing all MA coefficents."""

        if (coefs := self._coefs) is not None:
            return coefs
        self.update_coefs()
        assert (coefs := self._coefs) is not None
        return coefs

    @coefs.setter
    def coefs(self, values: VectorInputFloat) -> None:
        self._coefs = numpy.array(values, ndmin=1, dtype=config.NP_FLOAT)

    @coefs.deleter
    def coefs(self) -> None:
        self._coefs = None

    @property
    def order(self) -> int:
        """MA order."""
        return len(self.coefs)

    def update_coefs(self) -> None:
        """(Re)Calculate the MA coefficients based on the instantaneous unit
        hydrograph."""

        coefs: list[float] = []
        sum_coefs = 0.0
        max_coef = 0.0
        moment1 = self.iuh.moment1

        n = self.nmb_nodes
        nodes = numpy.linspace(0.0, 1.0 - 1.0 / n, n)
        responses = numpy.zeros(2 * n, dtype=config.NP_FLOAT)
        weights = numpy.linspace(1.0, 2 * n - 1, 2 * n - 1)
        weights[n:] = weights[: n - 1][::-1]
        weights /= n**2

        for t in itertools.count(0.0, 1.0):

            responses[:n] = responses[n:]
            responses[n:] = self.iuh(nodes + t)

            if (t == 0) and (moment1 < 1.0) and ((m := self.nmb_nodes_extra) > n):
                fine_nodes = numpy.linspace(0.0 / m, 1.0 - 1.0 / m, m)
                fine_responses = self.iuh(fine_nodes)
                fine_weights = numpy.linspace(m, 1.0, m) / m / m
                coef = numpy.dot(fine_weights, fine_responses)
            else:
                coef = numpy.dot(weights, responses[1:])

            sum_coefs += coef

            if (sum_coefs > 0.9) and (coef < self.smallest_coeff):
                self.coefs = (coefs_ := numpy.asarray(coefs)) / sum(coefs_)
                if (sum_coefs < 0.99) or (sum_coefs > 1.01):
                    self._raise_integrationwarning()
                return

            if (coef < self.smallest_coeff / 10.0 < max_coef) or (
                (sum_coefs < 0.5) and (t > 10.0 * moment1)
            ):
                idx = int(moment1)
                coefs_ = numpy.zeros(idx + 2, dtype=config.NP_FLOAT)
                weight = moment1 - idx
                coefs_[idx] = 1.0 - weight
                coefs_[idx + 1] = weight
                self.coefs = coefs_
                self._raise_integrationwarning()
                return

            max_coef = max(max_coef, coef)
            coefs.append(coef)

    def _raise_integrationwarning(self) -> None:
        warnings.warn(
            f"During the determination of the MA coefficients corresponding to the "
            f"instantaneous unit hydrograph `{repr(self.iuh)}` a numerical integration "
            f"problem occurred.  Please check the calculated coefficients: "
            f"{objecttools.repr_values(self.coefs)}."
        )

    @property
    def turningpoint(self) -> tuple[int, float]:
        """Turning point (index and value tuple) in the recession part of the MA
        approximation of the instantaneous unit hydrograph."""

        if self.order == 1:
            return 0, self.coefs[0]

        coefs = self.coefs
        old_dc = coefs[1] - coefs[0]
        for idx in range(self.order - 2):
            new_dc = coefs[idx + 2] - coefs[idx + 1]
            if (old_dc < 0.0) and (new_dc > old_dc):
                return idx, coefs[idx]
            old_dc = new_dc

        raise RuntimeError(
            f"Not able to detect a turning point in the impulse response "
            f"defined by the MA coefficients `{objecttools.repr_values(coefs)}`."
        )

    @property
    def delays(self) -> VectorFloat:
        """Time delays related to the individual MA coefficients."""
        return numpy.arange(self.order, dtype=config.NP_FLOAT)

    @property
    def moments(self) -> tuple[float, float]:
        """The first two time delay weighted statistical moments of the MA
        coefficients."""
        moment1 = statstools.calc_mean_time(self.delays, self.coefs)
        moment2 = statstools.calc_mean_time_deviation(self.delays, self.coefs, moment1)
        return moment1, moment2

    def plot(self, threshold=None, **kwargs) -> pyplot.Figure:
        """Create a barplot of the MA coefficients."""

        try:
            # Works under matplotlib 3.
            pyplot.bar(
                x=self.delays + 0.5, height=self.coefs, width=1.0, fill=False, **kwargs
            )
        except TypeError:  # pragma: no cover
            # Works under matplotlib 2.
            pyplot.bar(
                left=self.delays + 0.5,
                height=self.coefs,
                width=1.0,
                fill=False,
                **kwargs,
            )
        pyplot.xlabel("time")
        pyplot.ylabel("response")
        if threshold is not None:
            cumsum = numpy.cumsum(self.coefs)
            idx = numpy.where(cumsum > threshold * cumsum[-1])[0][0]
            pyplot.xlim(0.0, idx)
        idx, value = self.turningpoint
        pyplot.plot(idx, value, "ro")
        return pyplot.gcf()

    def __repr__(self):
        return objecttools.assignrepr_tuple(self.coefs, "MA(coefs=", 70) + ")"


class ARMA:
    """Autoregressive-Moving Average model.

    One can set all ARMA coefficients manually:

    >>> from hydpy import MA, ARMA, print_matrix
    >>> arma = ARMA(ar_coefs=(0.5,), ma_coefs=(0.3, 0.2))
    >>> print_matrix(arma.coefs)
    | 0.5 |
    | 0.3, 0.2 |
    >>> arma
    ARMA(ar_coefs=(0.5,),
         ma_coefs=(0.3, 0.2))

    >>> arma.ar_coefs = ()
    >>> arma.ma_coefs = range(20)
    >>> arma
    ARMA(ar_coefs=(),
         ma_coefs=(0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0,
                   11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0))

    Alternatively, they are determined by method |ARMA.update_coefs|, which requires an
    available |MA|.  We use the MA model based on the shifted normal distribution of
    the documentation on class |MA| as an example:

    >>> from scipy import stats
    >>> ma = MA(iuh=lambda x: 1.02328 * stats.norm.pdf(x, 4.0, 2.0))
    >>> ma.iuh.moment1 = 3.94
    >>> arma = ARMA(ma_model=ma)
    >>> arma
    ARMA(ar_coefs=(0.680483, -0.228511, 0.047283, -0.006022, 0.000377),
         ma_coefs=(0.019335, 0.054772, 0.081952, 0.107755, 0.104457,
                   0.076369, 0.041094, 0.01581, 0.004132, 0.000663,
                   0.00005))

    To verify that the ARMA model approximates the MA model with sufficient accuracy,
    one can query the achieved relative rmse value (|ARMA.rel_rmse|) or check the
    central moments of their responses to the standard delta time impulse:

    >>> from hydpy import round_
    >>> round_(arma.rel_rmse)
    0.0
    >>> round_(ma.moments)
    4.110439, 1.926845
    >>> round_(arma.moments)
    4.110439, 1.926845

    On can check the accuray of the approximation directly via the property
    |ARMA.dev_moments|, which is the sum of the absolute values of the deviations of
    both methods:

    >>> round_(arma.dev_moments)
    0.0

    For the first six digits, there is no difference.  However, the total number of
    coefficients is only reduced by one:

    >>> ma.order
    17
    >>> arma.order
    (5, 11)

    To reduce the determined number or AR coefficients, one can set a higher AR-related
    tolerance value:

    >>> arma.max_rel_rmse = 1e-3
    >>> arma.update_coefs()
    >>> arma
    ARMA(ar_coefs=(0.788899, -0.256436, 0.034256),
         ma_coefs=(0.019335, 0.052676, 0.075127, 0.096486, 0.089452,
                   0.060853, 0.02904, 0.008929, 0.001397, 0.000001,
                   -0.000004, 0.00001, -0.000008, -0.000009, -0.000004,
                   -0.000001))

    The number of AR coeffcients is actually reduced.  However, there are now even more
    MA coefficients, possibly trying to compensate the lower accuracy of the AR
    coefficients, and there is a slight decrease in the precision of the moments:

    >>> arma.order
    (3, 16)
    >>> round_(arma.moments)
    4.110441, 1.926851
    >>> round_(arma.dev_moments)
    0.000007

    To also reduce the number of MA coefficients, one can set a higher MA-related
    tolerance value:

    >>> arma.max_dev_coefs = 1e-3
    >>> arma.update_coefs()
    >>> arma
    ARMA(ar_coefs=(0.788888, -0.256432, 0.034255),
         ma_coefs=(0.019335, 0.052675, 0.075126, 0.096485, 0.089451,
                   0.060852, 0.02904, 0.008928, 0.001397))

    Now the total number of coefficients is in fact decreased, and the loss in accuracy
    is still small:

    >>> arma.order
    (3, 9)
    >>> round_(arma.moments)
    4.110737, 1.927672
    >>> round_(arma.dev_moments)
    0.001125

    Further relaxing the tolerance values results in even less coefficients, but also
    in some slightly negative responses to a standard impulse:

    >>> arma.max_rel_rmse = 1e-2
    >>> arma.max_dev_coefs = 1e-2
    >>> from hydpy.core.testtools import warn_later
    >>> with warn_later():
    ...     arma.update_coefs()
    UserWarning: Note that the smallest response to a standard impulse of the \
determined ARMA model is negative (`-0.000336`).
    >>> arma
    ARMA(ar_coefs=(0.736953, -0.166457),
         ma_coefs=(0.019474, 0.054169, 0.077806, 0.09874, 0.091294,
                   0.060796, 0.027226))
    >>> arma.order
    (2, 7)
    >>> from hydpy import print_vector
    >>> print_vector(arma.response)
    0.019474, 0.06852, 0.12506, 0.179497, 0.202758, 0.18034, 0.126378,
    0.063116, 0.025477, 0.008269, 0.001853, -0.000011, -0.000316,
    -0.000231, -0.000118, -0.000048, -0.000016

    It seems to be hard to find a parameter efficient approximation to the MA model in
    the given example. Generally, approximating ARMA models to MA models is more
    beneficial when functions with long tails are involved.  The most extreme example
    would be a simple exponential decline:

    >>> import numpy
    >>> ma = MA(iuh=lambda x: 0.1 * numpy.exp(-0.1 * x))
    >>> ma.iuh.moment1 = 6.932
    >>> arma = ARMA(ma_model=ma)

    In the given example a number of 185 MA coefficients can be reduced to a total
    number of three ARMA coefficients with no relevant loss of accuracy:

    >>> ma.order
    185
    >>> arma.order
    (1, 2)
    >>> round_(arma.dev_moments)
    0.0

    Use the following plotting command to see why 2 MA coeffcients instead of one are
    required in the above example:

    >>> figure = arma.plot(threshold=0.9)
    >>> from hydpy.core.testtools import save_autofig
    >>> save_autofig(f"ARMA_plot.png", figure)

        .. image:: ARMA_plot.png
           :width: 400

    Violations of the tolerance values are reported as warnings:

    >>> arma.max_dev_coefs = 0.0
    >>> arma.update_coefs()
    Traceback (most recent call last):
    ...
    UserWarning: Method `update_ma_coefs` is not able to determine the MA coefficients \
of the ARMA model with the desired accuracy.  You can set the tolerance value \
´max_dev_coefs` to a higher value.  An accuracy of `0.000000000924` has been reached \
using `185` MA coefficients.

    >>> arma.max_rel_rmse = 0.0
    >>> arma.update_coefs()
    Traceback (most recent call last):
    ...
    UserWarning: Method `update_ar_coefs` is not able to determine the AR coefficients \
of the ARMA model with the desired accuracy.  You can either set the tolerance value \
`max_rel_rmse` to a higher value or increase the allowed `max_ar_order`.  An accuracy \
of `0.0` has been reached using `10` coefficients.

    >>> arma.ma.coefs = 1.0, 1.0, 1.0
    >>> arma.update_coefs()
    Traceback (most recent call last):
    ...
    UserWarning: Not able to detect a turning point in the impulse response defined \
by the MA coefficients `1.0, 1.0, 1.0`.

    When getting such warnings, you need to inspect the achieved coefficients manually.
    In the last case, when the turning point detection failed, method
    |ARMA.update_coefs| simplified the ARMA to the original MA model, which is safe but
    not always a good choice:

    >>> import warnings
    >>> with warnings.catch_warnings(action="ignore"):
    ...     arma.update_coefs()
    >>> arma
    ARMA(ar_coefs=(),
         ma_coefs=(0.333333, 0.333333, 0.333333))
    """

    max_ar_order: int = 10
    """Maximum number of AR coefficients that are to be determined by method
    |ARMA.update_coefs|."""

    max_rel_rmse: float = 1e-6
    """Maximum relative root mean squared error to be accepted by method
    |ARMA.update_coefs|."""

    max_dev_coefs: float = 1e-6
    """Maximum deviation of the sum of all coefficents from one to be accepted by 
    method |ARMA.update_coefs|."""

    _ma_coefs: VectorFloat | None = None
    _ar_coefs: VectorFloat | None = None
    _rel_rmse: float | None

    def __init__(self, ma_model=None, ar_coefs=None, ma_coefs=None) -> None:
        self.ma = ma_model
        if ar_coefs is not None:
            self.ar_coefs = ar_coefs
        if ma_coefs is not None:
            self.ma_coefs = ma_coefs
        self._rel_rmse = None

    @property
    def rel_rmse(self) -> float:
        """Relative root mean squared error the last time achieved by method
        |ARMA.update_coefs|.

        >>> from hydpy.auxs.armatools import ARMA
        >>> ARMA().rel_rmse
        Traceback (most recent call last):
        ...
        RuntimeError: The relative root mean squared error has not been determined so \
far.
        """
        if (rel_rmse := self._rel_rmse) is None:
            raise RuntimeError(
                "The relative root mean squared error has not been determined so far."
            )
        return rel_rmse

    @property
    def ar_coefs(self) -> VectorFloat:
        """The AR coefficients of the ARMA model.

        |property| |ARMA.ar_coefs| does not recalculate already defined coefficients
        automatically for efficiency:

        >>> from hydpy import MA, ARMA, print_vector
        >>> arma = ARMA(ar_coefs=(0.5,), ma_coefs=(0.3, 0.2))
        >>> from scipy import stats
        >>> arma.ma = MA(iuh=lambda x: 1.02328 * stats.norm.pdf(x, 4.0, 2.0))
        >>> arma.ma.iuh.moment1 = 3.94
        >>> print_vector(arma.ar_coefs)
        0.5

        You can trigger the recalculation by removing the available coefficients first:

        >>> del arma.ar_coefs
        >>> print_vector(arma.ar_coefs)
        0.680483, -0.228511, 0.047283, -0.006022, 0.000377
        >>> arma
        ARMA(ar_coefs=(0.680483, -0.228511, 0.047283, -0.006022, 0.000377),
             ma_coefs=(0.019335, 0.054772, 0.081952, 0.107755, 0.104457,
                       0.076369, 0.041094, 0.01581, 0.004132, 0.000663,
                       0.00005))
        """
        if (ar_coefs := self._ar_coefs) is not None:
            return ar_coefs
        self.update_coefs()
        assert (ar_coefs := self._ar_coefs) is not None
        return ar_coefs

    @ar_coefs.setter
    def ar_coefs(self, values) -> None:
        self._ar_coefs = numpy.array(values, ndmin=1, dtype=config.NP_FLOAT)

    @ar_coefs.deleter
    def ar_coefs(self) -> None:
        self._ar_coefs = None

    @property
    def ma_coefs(self) -> VectorFloat:
        """The MA coefficients of the ARMA model.

        |property| |ARMA.ma_coefs| does not recalculate already defined coefficients
        automatically for efficiency:

        >>> from hydpy import MA, ARMA, print_vector
        >>> arma = ARMA(ar_coefs=(0.5,), ma_coefs=(0.3, 0.2))
        >>> from scipy import stats
        >>> arma.ma = MA(iuh=lambda x: 1.02328 * stats.norm.pdf(x, 4.0, 2.0))
        >>> arma.ma.iuh.moment1 = 3.94
        >>> print_vector(arma.ma_coefs)
        0.3, 0.2

        You can trigger the recalculation by removing the available coefficients first:

        >>> del arma.ma_coefs
        >>> print_vector(arma.ma_coefs)
        0.019335, 0.054772, 0.081952, 0.107755, 0.104457, 0.076369, 0.041094,
        0.01581, 0.004132, 0.000663, 0.00005
        >>> arma
        ARMA(ar_coefs=(0.680483, -0.228511, 0.047283, -0.006022, 0.000377),
             ma_coefs=(0.019335, 0.054772, 0.081952, 0.107755, 0.104457,
                       0.076369, 0.041094, 0.01581, 0.004132, 0.000663,
                       0.00005))
        """
        if (ma_coefs := self._ma_coefs) is not None:
            return ma_coefs
        self.update_coefs()
        assert (ma_coefs := self._ma_coefs) is not None
        return ma_coefs

    @ma_coefs.setter
    def ma_coefs(self, values: VectorInputFloat) -> None:
        self._ma_coefs = numpy.array(values, ndmin=1, dtype=config.NP_FLOAT)

    @ma_coefs.deleter
    def ma_coefs(self) -> None:
        self._ma_coefs = None

    @property
    def coefs(self) -> tuple[VectorFloat, VectorFloat]:
        """Tuple containing both the AR and the MA coefficients."""
        return self.ar_coefs, self.ma_coefs

    @property
    def ar_order(self) -> int:
        """Number of AR coefficients."""
        return len(self.ar_coefs)

    @property
    def ma_order(self) -> int:
        """Number of MA coefficients"""
        return len(self.ma_coefs)

    @property
    def order(self) -> tuple[int, int]:
        """Number of both the AR and the MA coefficients."""
        return self.ar_order, self.ma_order

    def update_coefs(self) -> None:
        """Determine both the AR and the MA coefficients."""
        self.update_ar_coefs()
        self.update_ma_coefs()
        self.norm_coefs()

    @property
    def effective_max_ar_order(self) -> int:
        """The maximum number of AR coefficients that shall or can be determined.

        It is the minimum of |ARMA.max_ar_order| and the number of coefficients of the
        pure |MA| after their turning point.
        """
        try:
            return min(self.max_ar_order, self.ma.order - self.ma.turningpoint[0] - 1)
        except RuntimeError as exc:
            warnings.warn(str(exc))
            return 0

    def update_ar_coefs(self) -> None:
        """Determine the AR coefficients.

        The number of AR coefficients is subsequently increased until the required
        precision |ARMA.max_rel_rmse| or the maximum number of AR coefficients
        (see |ARMA.effective_max_ar_order|) is reached.  In the second case,
        |ARMA.update_ar_coefs| raises a warning.
        """
        del self.ar_coefs
        if (max_ar_order := self.effective_max_ar_order) == 0:
            self.ar_coefs = ()
        else:
            for ar_order in range(1, max_ar_order + 1):
                self.calc_all_ar_coefs(ar_order, self.ma)
                if self.rel_rmse < self.max_rel_rmse:
                    break
            else:
                with hydpy.pub.options.reprdigits(12):
                    warnings.warn(
                        f"Method `update_ar_coefs` is not able to determine the AR "
                        f"coefficients of the ARMA model with the desired accuracy.  "
                        f"You can either set the tolerance value `max_rel_rmse` to a "
                        f"higher value or increase the allowed `max_ar_order`.  An "
                        f"accuracy of `{objecttools.repr_(self._rel_rmse)}` has been "
                        f"reached using `{self.effective_max_ar_order}` coefficients."
                    )

    @property
    def dev_moments(self) -> float:
        """Sum of the absolute deviations between the central moments of the
        instantaneous unit hydrograph and the ARMA approximation."""
        m1, m2 = self.moments, self.ma.moments
        return abs(m1[0] - m2[0]) + abs(m1[1] - m2[1])

    def norm_coefs(self) -> None:
        """Multiply all coefficients by the same factor, so that their sum becomes
        one."""
        sum_coefs = self.sum_coefs
        self.ar_coefs /= sum_coefs
        self.ma_coefs /= sum_coefs

    @property
    def sum_coefs(self) -> float:
        """The sum of all AR and MA coefficients"""
        return float(numpy.sum(self.ar_coefs) + numpy.sum(self.ma_coefs))

    @property
    def dev_coefs(self) -> float:
        """Absolute deviation of |ARMA.sum_coefs| from one."""
        return abs(self.sum_coefs - 1.0)

    def calc_all_ar_coefs(self, ar_order: int, ma_model: MA) -> None:
        """Determine the AR coeffcients based on a least squares approach.

        The argument `ar_order` defines the number of AR coefficients to be determined.
        The argument `ma_order` defines a pure |MA| model. The least squares approach
        is applied on all those coefficents of the pure MA model, which are associated
        with the part of the recession curve behind its turning point.

        The attribute |ARMA.rel_rmse| is updated with the resulting relative root mean
        square error.
        """
        turning_idx, _ = ma_model.turningpoint
        values = ma_model.coefs[turning_idx:]
        self.ar_coefs, residuals = numpy.linalg.lstsq(
            self.get_a(values, ar_order), self.get_b(values, ar_order), rcond=-1
        )[:2]
        if len(residuals) == 1:
            self._rel_rmse = numpy.sqrt(residuals[0]) / numpy.sum(values)
        else:
            self._rel_rmse = 0.0

    @staticmethod
    def get_a(values, n):
        """Extract the independent variables of the given values and return them as a
        matrix with n columns in a form suitable for the least squares approach applied
        in method |ARMA.update_ar_coefs|.
        """
        m = len(values) - n
        a = numpy.empty((m, n), dtype=config.NP_FLOAT)
        for i in range(m):
            i0 = i - 1 if i > 0 else None
            i1 = i + n - 1
            a[i] = values[i1:i0:-1]
        return numpy.array(a)

    @staticmethod
    def get_b(values, n):
        """Extract the dependent variables of the values in a vector with n entries in
        a form suitable for the least squares approach applied in method
        |ARMA.update_ar_coefs|.
        """
        return numpy.array(values[n:])

    def update_ma_coefs(self) -> None:
        """Determine the MA coefficients.

        The number of MA coefficients is subsequently increased until the required
        precision (|ARMA.max_dev_coefs|) or the or the order of the original |MA| model
        is reached.  In the second case, |ARMA.update_ma_coefs| raises a warning.
        """
        self.ma_coefs = []
        for ma_order in range(1, self.ma.order + 1):
            self.calc_next_ma_coef(ma_order, self.ma)
            if self.dev_coefs < self.max_dev_coefs:
                break
        else:
            with hydpy.pub.options.reprdigits(12):
                warnings.warn(
                    f"Method `update_ma_coefs` is not able to determine the MA "
                    f"coefficients of the ARMA model with the desired accuracy.  You "
                    f"can set the tolerance value ´max_dev_coefs` to a higher value.  "
                    f"An accuracy of `{objecttools.repr_(self.dev_coefs)}` has been "
                    f"reached using `{self.ma.order}` MA coefficients."
                )
        if numpy.min(self.response) < 0.0:
            warnings.warn(
                f"Note that the smallest response to a standard impulse of the "
                f"determined ARMA model is negative "
                f"(`{objecttools.repr_(numpy.min(self.response))}`)."
            )

    def calc_next_ma_coef(self, ma_order, ma_model) -> None:
        """Determine the MA coefficients of the ARMA model based on its predetermined
        AR coefficients and the MA ordinates of the given |MA| model.

        The MA coefficients are determined one at a time, beginning with the first one.
        Each ARMA MA coefficient in set in a manner that allows for the exact
        reproduction of the equivalent pure MA coefficient with all relevant ARMA
        coefficients.
        """
        idx = ma_order - 1
        coef = ma_model.coefs[idx]
        for jdx, ar_coef in enumerate(self.ar_coefs):
            zdx = idx - jdx - 1
            if zdx >= 0:
                coef -= ar_coef * ma_model.coefs[zdx]
        self.ma_coefs = numpy.concatenate((self.ma_coefs, numpy.asarray([coef])))

    @property
    def response(self) -> VectorFloat:
        """Return the response to a standard dt impulse."""
        values: list[float] = []
        sum_values = 0.0
        ma_coefs = self.ma_coefs
        ar_coefs = self.ar_coefs
        ma_order = self.ma_order
        for idx in range(len(self.ma.delays)):
            value = 0.0
            if idx < ma_order:
                value += ma_coefs[idx]
            for jdx, ar_coef in enumerate(ar_coefs):
                zdx = idx - jdx - 1
                if zdx >= 0:
                    value += ar_coef * values[zdx]
            values.append(value)
            sum_values += value
        return numpy.array(values)

    @property
    def moments(self) -> tuple[float, float]:
        """The first two time delay weighted statistical moments of the ARMA
        response."""
        timepoints = self.ma.delays
        response = self.response
        moment1 = statstools.calc_mean_time(timepoints, response)
        moment2 = statstools.calc_mean_time_deviation(timepoints, response, moment1)
        return moment1, moment2

    def plot(self, threshold=None, **kwargs) -> pyplot.Figure:
        """Barplot of the ARMA response."""
        try:
            # Works under matplotlib 3.
            pyplot.bar(
                x=self.ma.delays + 0.5,
                height=self.response,
                width=1.0,
                fill=False,
                **kwargs,
            )
        except TypeError:  # pragma: no cover
            # Works under matplotlib 2.
            pyplot.bar(
                left=self.ma.delays + 0.5,
                height=self.response,
                width=1.0,
                fill=False,
                **kwargs,
            )
        pyplot.xlabel("time")
        pyplot.ylabel("response")
        if threshold is not None:
            cumsum = numpy.cumsum(self.response)
            idx = numpy.where(cumsum > threshold * cumsum[-1])[0][0]
            pyplot.xlim(0.0, idx)
        return pyplot.gcf()

    def __repr__(self) -> str:
        return (
            f"{objecttools.assignrepr_tuple(self.ar_coefs, 'ARMA(ar_coefs=', 70)},\n"
            f"{objecttools.assignrepr_tuple(self.ma_coefs, '     ma_coefs=', 70)})"
        )
