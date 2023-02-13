# -*- coding: utf-8 -*-
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
from hydpy.core import exceptiontools
from hydpy.core import objecttools
from hydpy.core import propertytools
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

    The MA coefficients can be set manually:

    >>> from hydpy import MA
    >>> ma = MA(coefs=(0.8, 0.2))
    >>> ma
    MA(coefs=(0.8, 0.2))
    >>> ma.coefs = 0.2, 0.8
    >>> ma
    MA(coefs=(0.2, 0.8))

    Otherwise they are determined by method |MA.update_coefs|.  But this requires that
    an integrable function object is given.  Usually, this function object is an |IUH|
    subclass object, but (as in the following example) other function objects defining
    instantaneuous unit hydrographs are accepted.  However, they should be well-behaved
    (e.g. be relatively smooth, unimodal, strictly positive, unity integral surface in
    the positive range).

    For educational purposes, some discontinuous functions are applied in the following.
    One can suppress the associated warning messages with the following commands:

    >>> import warnings
    >>> from scipy import integrate
    >>> warnings.filterwarnings("ignore", category=integrate.IntegrationWarning)

    The first example is a simple rectangle impuls:

    >>> ma = MA(iuh=lambda x: 0.05 if x < 20.0 else 0.0)
    >>> ma.iuh.moment1 = 10.0
    >>> ma
    MA(coefs=(0.025, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05,
              0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05,
              0.025))

    The number of the coefficients can be modified by changing the class attribute
    |MA.smallest_coeff|:

    >>> ma.smallest_coeff = 0.03
    >>> ma.update_coefs()
    >>> ma
    MA(coefs=(0.025641, 0.051282, 0.051282, 0.051282, 0.051282, 0.051282,
              0.051282, 0.051282, 0.051282, 0.051282, 0.051282, 0.051282,
              0.051282, 0.051282, 0.051282, 0.051282, 0.051282, 0.051282,
              0.051282, 0.051282))


    The first two central moments of the time delay are a usefull measure for
    describing the operation of a MA model:

    >>> ma = MA(iuh=lambda x: 1.0 if x < 1.0 else 0.0)
    >>> ma.iuh.moment1 = 0.5
    >>> ma
    MA(coefs=(0.5, 0.5))
    >>> from hydpy import round_
    >>> round_(ma.moments, 6)
    0.5, 0.5

    The first central moment is the weigthed time delay (mean lag time).  The second
    central moment is the weighted mean deviation from the mean lag time (diffusion).

    MA objects can return the turning point in the recession part of their MA
    coefficients.  This can be demonstrated for the right side of the probability
    density function of the normal distribution with zero mean and a standard deviation
    (turning point) of 10:

    >>> from scipy import stats
    >>> ma = MA(iuh=lambda x: 2.0*stats.norm.pdf(x, 0.0, 2.0))
    >>> ma.iuh.moment1 = 1.35
    >>> ma
    MA(coefs=(0.195417, 0.346659, 0.24189, 0.13277, 0.057318, 0.019458,
              0.005193, 0.001089, 0.00018, 0.000023, 0.000002, 0.0, 0.0))
    >>> round_(ma.turningpoint)
    2, 0.24189

    Note that the first returned value is the index of the the MA coefficient closest
    to the turning point, and not a high precision estimate of the real turning point
    of the instantaneous unit hydrograph.

    You can also use the following ploting command to verify the position of the
    turning point, which is printed as a red dot.

    >>> ma.plot(threshold=0.9)

    .. testsetup::

        >>> from matplotlib import pyplot
        >>> pyplot.close()

    The turning point detection also works for functions which include both a rising
    and a falling limb.  This can be shown shifting the normal distribution to the
    right:

    >>> ma.iuh = lambda x: 1.02328*stats.norm.pdf(x, 4.0, 2.0)
    >>> ma.iuh.moment1 = 3.94
    >>> ma.update_coefs()
    >>> ma
    MA(coefs=(0.019322, 0.067931, 0.12376, 0.177364, 0.199966, 0.177364,
              0.12376, 0.067931, 0.029326, 0.009956, 0.002657, 0.000557,
              0.000092, 0.000012, 0.000001, 0.0, 0.0))
    >>> round_(ma.turningpoint)
    6, 0.12376

    When no turning point can be detected, an error is raised:

    >>> ma.coefs = 1.0, 1.0, 1.0
    >>> ma.turningpoint
    Traceback (most recent call last):
    ...
    RuntimeError: Not able to detect a turning point in the impulse response defined \
by the MA coefficients `1.0, 1.0, 1.0`.

    The next example requires reactivating the warning suppressed above:

    >>> warnings.filterwarnings("error", category=integrate.IntegrationWarning)

    The MA coefficients need to be approximated numerically.  For very spiky response
    function, the underlying integration algorithm might fail.  Then it is assumed that
    the complete mass of the response function is placed at a single delay time,
    defined by the property `moment1` of the instantaneous unit hydrograph.  Hopefully,
    this leads to plausible results.  However, we raise an additional warning message
    to allow users to determine the coefficients by a different approach:

    >>> ma.iuh = lambda x: 10.0 if 4.2 < x <= 4.3 else 0.0
    >>> ma.iuh.moment1 = 4.25
    >>> ma.update_coefs()   # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    UserWarning: During the determination of the MA coefficients corresponding to the \
instantaneous unit hydrograph ... a numerical integration problem occurred.  \
Please check the calculated coefficients: 0.0, 0.0, 0.0, 0.0, 0.75, 0.25.
    >>> ma
    MA(coefs=(0.0, 0.0, 0.0, 0.0, 0.75, 0.25))

    For very steep response functions, numerical integration might fail:

    >>> ma = MA(iuh=lambda x: stats.norm.pdf(x, 4.0, 1e-6))
    >>> ma.iuh.moment1 = 4.0
    >>> ma.update_coefs()   # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    RuntimeError: Cannot determine the MA coefficients corresponding to the \
instantaneous unit hydrograph `...`.

    For very fast responses, there should be only one MA coefficient that has the value
    1.  Method |MA.update_coefs| provides a heuristic for such cases where numerical
    integration fails.  As we are not sure that this heuristic works in all possible
    cases, |MA.update_coefs| raises the following warning in such cases:

    >>> ma = MA(iuh=lambda x: 1e6*numpy.exp(-1e6*x))
    >>> ma.iuh.moment1 = 6.931e-7
    >>> ma # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    UserWarning: During the determination of the MA coefficients corresponding to the \
instantaneous unit hydrograph `...` a numerical integration problem occurred.  Please \
check the calculated coefficients: 1.0.

    >>> ma
    MA(coefs=(1.0,))
    """

    smallest_coeff: float = 1e-9
    """Smalles MA coefficient to be determined at the end of the response."""

    _coefs: Optional[VectorFloat] = None

    def __init__(self, iuh=None, coefs=None) -> None:
        self.iuh = iuh
        if coefs is not None:
            self.coefs = coefs

    def _get_coefs(self) -> VectorFloat:
        """|numpy.ndarray| containing all MA coefficents."""
        if (coefs := self._coefs) is not None:
            return coefs
        self.update_coefs()
        assert (coefs := self._coefs) is not None
        return coefs

    def _set_coefs(self, values: VectorInputFloat) -> None:
        self._coefs = numpy.array(values, ndmin=1, dtype=float)

    def _del_coefs(self) -> None:
        self._coefs = None

    coefs = propertytools.Property(fget=_get_coefs, fset=_set_coefs, fdel=_del_coefs)

    @property
    def order(self) -> int:
        """MA order."""
        return len(self.coefs)

    def _quad(self, dt, t) -> None:
        return integrate.quad(self.iuh, max(t - 1.0 + dt, 0.0), t + dt)[0]

    def update_coefs(self) -> None:
        """(Re)calculate the MA coefficients based on the instantaneous unit
        hydrograph."""
        coefs: List[float] = []
        sum_coefs = 0.0
        moment1 = self.iuh.moment1
        for t in itertools.count(0.0, 1.0):
            points = (moment1 % 1,) if t <= moment1 <= (t + 2.0) else ()
            try:
                coef = integrate.quad(self._quad, 0.0, 1.0, args=(t,), points=points)[0]
            except integrate.IntegrationWarning:
                idx = int(moment1)
                coefs_ = numpy.zeros(idx + 2, dtype=float)
                weight = moment1 - idx
                coefs_[idx] = 1.0 - weight
                coefs_[idx + 1] = weight
                self.coefs = coefs_
                self._raise_integrationwarning(coefs_)
                break  # pragma: no cover
            sum_coefs += coef
            if (sum_coefs < 0.5) and (t > 10.0 * moment1):
                if moment1 < 0.01:
                    self.coefs = numpy.ones(1, dtype=float)
                    self._raise_integrationwarning(self.coefs)
                    break  # pragma: no cover
                raise RuntimeError(
                    f"Cannot determine the MA coefficients corresponding to the "
                    f"instantaneous unit hydrograph `{repr(self.iuh)}`."
                )
            if (sum_coefs > 0.9) and (coef < self.smallest_coeff):
                self.coefs = (coefs_ := numpy.asarray(coefs)) / sum(coefs_)
                break
            coefs.append(coef)

    def _raise_integrationwarning(self, coefs) -> None:
        warnings.warn(
            f"During the determination of the MA coefficients corresponding to the "
            f"instantaneous unit hydrograph `{repr(self.iuh)}` a numerical integration "
            f"problem occurred.  Please check the calculated coefficients: "
            f"{objecttools.repr_values(coefs)}."
        )

    @property
    def turningpoint(self) -> Tuple[int, float]:
        """Turning point (index and value tuple) in the recession part of the MA
        approximation of the instantaneous unit hydrograph."""
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
        return numpy.arange(self.order, dtype=float)

    @property
    def moments(self) -> Tuple[float, float]:
        """The first two time delay weighted statistical moments of the MA
        coefficients."""
        moment1 = statstools.calc_mean_time(self.delays, self.coefs)
        moment2 = statstools.calc_mean_time_deviation(self.delays, self.coefs, moment1)
        return moment1, moment2

    def plot(self, threshold=None, **kwargs) -> None:
        """Barplot of the MA coefficients."""
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

    def __repr__(self):
        return objecttools.assignrepr_tuple(self.coefs, "MA(coefs=", 70) + ")"


class ARMA:
    """Autoregressive-Moving Average model.

    One can sett all ARMA coefficients manually:

    >>> from hydpy import MA, ARMA
    >>> arma = ARMA(ar_coefs=(0.5,), ma_coefs=(0.3, 0.2))
    >>> arma.coefs
    (array([0.5]), array([0.3, 0.2]))
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
         ma_coefs=(0.019322, 0.054783, 0.08195, 0.107757, 0.104458,
                   0.07637, 0.041095, 0.01581, 0.004132, 0.000663,
                   0.00005))

    To verify that the ARMA model approximates the MA model with sufficient accuracy,
    one can query the achieved relative rmse value (|ARMA.rel_rmse|) or check the
    central moments of their responses to the standard delta time impulse:

    >>> from hydpy import round_
    >>> round_(arma.rel_rmse)
    0.0
    >>> round_(ma.moments)
    4.110496, 1.926798
    >>> round_(arma.moments)
    4.110496, 1.926798

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
         ma_coefs=(0.019322, 0.052688, 0.075125, 0.096488, 0.089453,
                   0.060854, 0.029041, 0.008929, 0.001397, 0.000001,
                   -0.000004, 0.00001, -0.000008, -0.000009, -0.000004,
                   -0.000001))

    The number of AR coeffcients is actually reduced.  However, there are now even more
    MA coefficients, possibly trying to compensate the lower accuracy of the AR
    coefficients, and there is a slight decrease in the precision of the moments:

    >>> arma.order
    (3, 16)
    >>> round_(arma.moments)
    4.110497, 1.926804
    >>> round_(arma.dev_moments)
    0.000007

    To also reduce the number of MA coefficients, one can set a higher MA-related
    tolerance value:

    >>> arma.max_dev_coefs = 1e-3
    >>> arma.update_coefs()
    >>> arma
    ARMA(ar_coefs=(0.788888, -0.256432, 0.034255),
         ma_coefs=(0.019321, 0.052687, 0.075124, 0.096486, 0.089452,
                   0.060853, 0.02904, 0.008929, 0.001397))

    Now the total number of coefficients is in fact decreased, and the loss in accuracy
    is still small:

    >>> arma.order
    (3, 9)
    >>> round_(arma.moments)
    4.110794, 1.927625
    >>> round_(arma.dev_moments)
    0.001125

    Further relaxing the tolerance values results in even less coefficients, but also
    in some slightly negative responses to a standard impulse:

    >>> arma.max_rel_rmse = 1e-2
    >>> arma.max_dev_coefs = 1e-2
    >>> arma.update_coefs()
    Traceback (most recent call last):
    ...
    UserWarning: Note that the smallest response to a standard impulse of the \
determined ARMA model is negative (`-0.000316`).
    >>> arma
    ARMA(ar_coefs=(0.736954, -0.166457),
         ma_coefs=(0.01946, 0.05418, 0.077804, 0.098741, 0.091295,
                   0.060797, 0.027226))
    >>> arma.order
    (2, 7)
    >>> from hydpy import print_values
    >>> print_values(arma.response)
    0.01946, 0.068521, 0.125062, 0.1795, 0.202761, 0.180343, 0.12638,
    0.063117, 0.025477, 0.008269, 0.001853, -0.000011, -0.000316,
    -0.000231, -0.000118, -0.000048, -0.000016

    It seems to be hard to find a parameter efficient approximation to the MA model in
    the given example. Generally, approximating ARMA models to MA models is more
    beneficial when functions with long tails are involved.  The most extreme example
    would be a simple exponential decline:

    >>> import numpy
    >>> ma = MA(iuh=lambda x: 0.1*numpy.exp(-0.1*x))
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

    >>> arma.plot(threshold=0.9)

    Violations of the tolerance values are reported as warnings:

    >>> arma.max_dev_coefs = 0.0
    >>> arma.update_coefs()
    Traceback (most recent call last):
    ...
    UserWarning: Method `update_ma_coefs` is not able to determine the MA coefficients \
of the ARMA model with the desired accuracy.  You can set the tolerance value \
´max_dev_coefs` to a higher value.  An accuracy of `0.000000000925` has been reached \
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
    UserWarning: Not able to detect a turning point in the impulse response defined by \
the MA coefficients `1.0, 1.0, 1.0`.

    When getting such warnings, you need to inspect the achieved coefficients manually.
    In the last case, when the turning point detection failed, method
    |ARMA.update_coefs| simplified the ARMA to the original MA model, which is a safe
    but not always a good choice:

    >>> import warnings
    >>> with warnings.catch_warnings():
    ...     warnings.simplefilter("ignore")
    ...     arma.update_coefs()
    >>> arma
    ARMA(ar_coefs=(),
         ma_coefs=(1.0, 1.0, 1.0))
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

    _ma_coefs: Optional[VectorFloat] = None
    _ar_coefs: Optional[VectorFloat] = None
    _rel_rmse: Optional[float]

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

    def _get_ar_coefs(self) -> VectorFloat:
        """The AR coefficients of the AR model."""
        if (ar_coefs := self._ar_coefs) is not None:
            return ar_coefs
        self.update_ar_coefs()
        assert (ar_coefs := self._ar_coefs) is not None
        return ar_coefs

    def _set_ar_coefs(self, values) -> None:
        self._ar_coefs = numpy.array(values, ndmin=1, dtype=float)

    def _del_ar_coefs(self) -> None:
        self._ar_coefs = None

    ar_coefs = propertytools.Property(
        fget=_get_ar_coefs, fset=_set_ar_coefs, fdel=_del_ar_coefs
    )

    def _get_ma_coefs(self) -> VectorFloat:
        """The MA coefficients of the ARMA model."""
        if (ma_coefs := self._ma_coefs) is not None:
            return ma_coefs
        self.update_ma_coefs()
        assert (ma_coefs := self._ma_coefs) is not None
        return ma_coefs

    def _set_ma_coefs(self, values: VectorInputFloat) -> None:
        self._ma_coefs = numpy.array(values, ndmin=1, dtype=float)

    def _del_ma_coefs(self) -> None:
        self._ma_coefs = None

    ma_coefs = propertytools.Property(
        fget=_get_ma_coefs, fset=_set_ma_coefs, fdel=_del_ma_coefs
    )

    @property
    def coefs(self) -> Tuple[VectorFloat, VectorFloat]:
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
    def order(self) -> Tuple[int, int]:
        """Number of both the AR and the MA coefficients."""
        return self.ar_order, self.ma_order

    def update_coefs(self) -> None:
        """Determine both the AR and the MA coefficients."""
        self.update_ar_coefs()
        self.update_ma_coefs()

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
        a = numpy.empty((m, n), dtype=float)
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
                self.norm_coefs()
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
        values: List[float] = []
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
    def moments(self) -> Tuple[float, float]:
        """The first two time delay weighted statistical moments of the ARMA
        response."""
        timepoints = self.ma.delays
        response = self.response
        moment1 = statstools.calc_mean_time(timepoints, response)
        moment2 = statstools.calc_mean_time_deviation(timepoints, response, moment1)
        return moment1, moment2

    def plot(self, threshold=None, **kwargs) -> None:
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

    def __repr__(self) -> str:
        return (
            f"{objecttools.assignrepr_tuple(self.ar_coefs, 'ARMA(ar_coefs=', 70)},\n"
            f"{objecttools.assignrepr_tuple(self.ma_coefs, '     ma_coefs=', 70)})"
        )
