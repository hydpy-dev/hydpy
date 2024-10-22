"""This module enables model developers to easily include linear and nonlinear
interpolation techniques into their model methods.

The implemented classes |SimpleInterpolator| and |SeasonalInterpolator| serve as base
classes for (very complex) control parameters.  Subclassing them is sufficient for
making the functionalities of the modules |interptools|, |anntools|, and |ppolytools|
available to the user.

The relevant models perform the interpolation during simulation runs, so we implemented
the related methods in the Cython extension module |interputils|.
"""

# import...
# ...from standard library
from __future__ import annotations
import abc
import itertools

# ...from site-packages
import numpy

# ...from HydPy
import hydpy
from hydpy import config
from hydpy.core import exceptiontools
from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.core import propertytools
from hydpy.core import timetools
from hydpy.core import variabletools
from hydpy.core.typingtools import *
from hydpy.cythons import interputils

if TYPE_CHECKING:
    from matplotlib import pyplot
else:
    pyplot = exceptiontools.OptionalImport("pyplot", ["matplotlib.pyplot"], locals())


class _Labeled:
    def _update_labels(self) -> None:
        xlabel = getattr(self, "XLABEL", None)
        if xlabel:
            pyplot.xlabel(xlabel)
        ylabel = getattr(self, "YLABEL", None)
        if ylabel:
            pyplot.ylabel(ylabel)


class InterpAlgorithm(_Labeled):
    """Base class for defining interpolation algorithms usable by classes
    |SimpleInterpolator| and |SeasonalInterpolator|."""

    nmb_inputs: propertytools.BaseProperty[Never, int]
    """The number of input values."""
    inputs: propertytools.BaseProperty[Never, VectorFloat]
    """The current input values."""
    nmb_outputs: propertytools.BaseProperty[Never, int]
    """The lastly calculated output values."""
    outputs: propertytools.BaseProperty[Never, VectorFloat]
    """The lastly calculated output values."""
    output_derivatives: propertytools.BaseProperty[Never, VectorFloat]
    """The lastly calculated first-order derivatives."""

    @abc.abstractmethod
    def calculate_values(self) -> None:
        """Calculate the output values based on the input values defined previously."""

    @abc.abstractmethod
    def calculate_derivatives(self, idx: int, /) -> None:
        """Calculate the derivatives of the output values with respect to the input
        value of the given index."""

    @abc.abstractmethod
    def verify(self) -> None:
        """Raise a |RuntimeError| if the actual |InterpAlgorithm| object is
        ill-defined."""

    @abc.abstractmethod
    def assignrepr(self, prefix: str, indent: int = 0) -> str:
        """Return a string representation of the actual |InterpAlgorithm| object
        prefixed with the given string."""

    def print_table(self, xs: VectorFloat | MatrixFloat) -> None:
        """Process the given input data and print the interpolated output values as
        well as all partial first-order derivatives.

        The documentation on class |PPoly| includes some examples of a strictly
        univariate interpolator.  Here, we take up some examples discussed for class
        |ANN| to show that method |InterpAlgorithm.print_table| also correctly reports
        all outputs and derivatives for multivariate interpolators.

        A single-input single-output example:

        >>> from hydpy import ANN, nan
        >>> ann = ANN(nmb_inputs=1, nmb_neurons=(1,), nmb_outputs=1,
        ...           weights_input=4.0, weights_output=3.0,
        ...           intercepts_hidden=-16.0, intercepts_output=-1.0)
        >>> ann.print_table([0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0])
        x    y          dy/dx
        0.0  -1.0       0.000001
        1.0  -0.999982  0.000074
        2.0  -0.998994  0.004023
        3.0  -0.946041  0.211952
        4.0  0.5        3.0
        5.0  1.946041   0.211952
        6.0  1.998994   0.004023
        7.0  1.999982   0.000074
        8.0  2.0        0.000001

        A multivariate example (three input and two output values result in six partial
        derivatives):

        >>> ann.nmb_inputs = 3
        >>> ann.nmb_neurons = (4,)
        >>> ann.nmb_outputs = 2
        >>> ann.weights_input = [[ 0.2, -0.1, -1.7,  0.6],
        ...                      [ 0.9,  0.2,  0.8,  0.0],
        ...                      [-0.5, -1.0,  2.3, -0.4]]
        >>> ann.weights_output = [[ 0.0,  2.0],
        ...                       [-0.5,  1.0],
        ...                       [ 0.4,  2.4],
        ...                       [ 0.8, -0.9]]
        >>> ann.intercepts_hidden = [ 0.9,  0.0, -0.4, -0.2]
        >>> ann.intercepts_output = [ 1.3, -2.0]
        >>> ann.print_table([[-0.1,  1.3,  1.6]])
        x1    x2   x3   y1        y2        dy1/dx1   dy2/dx1    dy1/dx2   dy2/dx2   \
dy1/dx3   dy2/dx3
        -0.1  1.3  1.6  1.822222  1.876983  0.099449  -0.103039  -0.01303  0.365739  \
0.027041  -0.203965

        A combined example (two inputs, one output):

        >>> ANN(nmb_inputs=2, nmb_neurons=(2, 1), nmb_outputs=1,
        ...     weights_input=[[1000.0, 500.0],
        ...                    [1000.0, 500.0]],
        ...     weights_hidden=[[[1000.0],
        ...                      [-1000.0]]],
        ...     weights_output=[[1.0]],
        ...     intercepts_hidden=[[-750.0, -750.0],
        ...                        [-750.0, nan]],
        ...     intercepts_output=[0.0],
        ... ).print_table([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
        x1   x2   y    dy/dx1  dy/dx2
        0.0  0.0  0.0  0.0     0.0
        1.0  0.0  1.0  0.0     0.0
        0.0  1.0  1.0  0.0     0.0
        1.0  1.0  0.0  0.0     0.0
        """
        r = objecttools.repr_

        ni, no = self.nmb_inputs, self.nmb_outputs
        nt = ni + no
        table = numpy.empty((len(xs) + 1, nt + ni * no), dtype=object)

        xns = "x" if ni == 1 else [f"x{i}" for i in range(1, ni + 1)]
        yns = "y" if no == 1 else [f"y{i}" for i in range(1, no + 1)]
        table[0, :ni] = xns
        table[0, ni:nt] = yns
        table[0, nt:] = [f"d{yn}/d{xn}" for xn, yn in itertools.product(xns, yns)]

        # Mypy problem? See issue https://github.com/python/mypy/issues/8586:
        xs_: float | Iterable[float]
        for ri, xs_ in enumerate(xs):
            ri += 1
            if isinstance(xs_, float):
                xs_ = (xs_,)
            for xi, x in enumerate(xs_):
                table[ri, xi] = r(x)
                self.inputs[xi] = x
            self.calculate_values()
            for yi, y in enumerate(self.outputs):
                table[ri, ni + yi] = r(y)
            for xi in range(ni):
                self.calculate_derivatives(xi)
                for yi in range(no):
                    table[ri, nt + no * xi + yi] = r(self.output_derivatives[yi])

        for j in range(table.shape[1] - 1):
            length = max(len(v) for v in table[:, j])
            table[:, j] = [v.ljust(length) for v in table[:, j]]
        for row in table:
            print(*row, sep="  ")

    def plot(
        self,
        xmin: float,
        xmax: float,
        *,
        idx_input: int = 0,
        idx_output: int = 0,
        points: int = 100,
        **kwargs: Any,
    ) -> pyplot.Figure:
        """Plot the relationship between particular input (`idx_input`) and output
        (`idx_output`) values defined by the actual |InterpAlgorithm| object.

        You need to define the lower and the upper bound of the x-axis via arguments
        `xmin` and `xmax`.  You can increase or decrease the accuracy of the plot by
        changing the number of points evaluated within this interval (default is 100).
        For visual configuration, pass arbitrary |matplotlib| `pyplot` plotting
        arguments as keyword arguments.

        See the documentation on classes |ANN| and |PPoly| for some examples.
        """
        xs_ = numpy.linspace(xmin, xmax, points)
        ys_ = numpy.zeros(xs_.shape)
        for idx, x__ in enumerate(xs_):
            self.inputs[idx_input] = x__
            self.calculate_values()
            ys_[idx] = self.outputs[idx_output]
        pyplot.plot(xs_, ys_, **kwargs)
        self._update_labels()
        return pyplot.gcf()


class BaseInterpolator(_Labeled):
    """Base class for |SimpleInterpolator| and |SeasonalInterpolator|."""

    NDIM = 0
    TIME = None
    SPAN = (None, None)

    name: str
    """Class name in lowercase letters."""
    subvars: parametertools.SubParameters
    """The |SubParameters| object containing the current |BaseInterpolator| object."""
    subpars: parametertools.SubParameters
    """The |SubParameters| object containing the current |BaseInterpolator| object."""
    fastaccess: parametertools.FastAccessParameter
    """The `fastaccess` object providing access to the interpolator functionalities
    implemented in Cython."""

    __hydpy__subclasscounter__: ClassVar[int]

    def __init_subclass__(cls) -> None:
        cls.name = cls.__name__.lower()
        subclasscounter = variabletools.Variable.__hydpy__subclasscounter__ + 1
        variabletools.Variable.__hydpy__subclasscounter__ = subclasscounter
        cls.__hydpy__subclasscounter__ = subclasscounter


class SimpleInterpolator(BaseInterpolator):
    """Parameter base class for handling interpolation problems.

    |SimpleInterpolator| serves as a base class for parameter objects that accept
    an |InterpAlgorithm| object as their "value", which allows model users to select
    interpolation algorithms and configure them according to the data at hand.  If, for
    example, linear interpolation is sufficient, one can prepare and hand over a
    |PPoly| object:

    >>> from hydpy.auxs.interptools import SimpleInterpolator
    >>> simpleinterpolator = SimpleInterpolator(None)
    >>> simpleinterpolator
    simpleinterpolator(?)

    >>> from hydpy import ANN, PPoly, print_vector
    >>> simpleinterpolator(PPoly.from_data(xs=[0.0, 1.0], ys=[0.0, 2.0]))
    >>> simpleinterpolator
    simpleinterpolator(
        PPoly(
            Poly(x0=0.0, cs=(0.0, 2.0)),
        )
    )

    Besides handling an |InterpAlgorithm| object and connecting it to its model
    instance, |SimpleInterpolator| provides no own functionalities.  Instead, its
    user-available properties and methods call the identically named properties and
    methods of the handled interpolator, thereby passing all possible arguments without
    modification.  Hence, read the documentation on the subclasses of |InterpAlgorithm|
    for further information.

    The following technical checks ensure the proper implementation of all delegations:

    >>> simpleinterpolator(ANN(nmb_inputs=2, nmb_outputs=3))
    >>> simpleinterpolator.nmb_inputs
    2
    >>> simpleinterpolator.nmb_outputs
    3
    >>> simpleinterpolator.algorithm.inputs = 1.0, 2.0
    >>> print_vector(simpleinterpolator.inputs)
    1.0, 2.0
    >>> simpleinterpolator.algorithm.outputs = 3.0, 4.0, 5.0
    >>> print_vector(simpleinterpolator.outputs)
    3.0, 4.0, 5.0
    >>> simpleinterpolator.algorithm.output_derivatives = 6.0, 7.0, 8.0
    >>> print_vector(simpleinterpolator.output_derivatives)
    6.0, 7.0, 8.0
    >>> from unittest.mock import patch
    >>> with patch.object(ANN, "verify") as mock:
    ...     assert simpleinterpolator.verify() is None
    >>> mock.assert_called_with()
    >>> with patch.object(ANN, "calculate_values") as mock:
    ...     assert simpleinterpolator.calculate_values() is None
    >>> mock.assert_called_with()
    >>> with patch.object(ANN, "calculate_derivatives") as mock:
    ...     assert simpleinterpolator.calculate_derivatives(3) is None
    >>> mock.assert_called_with(3)
    >>> with patch.object(ANN, "print_table") as mock:
    ...     assert simpleinterpolator.print_table(xs=[1.0, 2.0]) is None
    >>> mock.assert_called_with(xs=[1.0, 2.0])
    >>> kwargs = dict(xmin=0.0, xmax=1.0, idx_input=1, idx_output=2, points=10, opt="?")
    >>> with patch.object(ANN, "plot") as mock:
    ...     mock.return_value = "figure"
    ...     assert simpleinterpolator.plot(**kwargs) == "figure"
    >>> mock.assert_called_with(**kwargs)
    """

    TYPE = "interputils.SimpleInterpolator"

    _algorithm: InterpAlgorithm | None

    __simpleinterpolator: interputils.SimpleInterpolator | None

    def __init__(self, subvars: parametertools.SubParameters) -> None:
        self.subvars = subvars
        self.subpars = subvars
        self.fastaccess = parametertools.FastAccessParameter()
        self._algorithm = None
        self.__simpleinterpolator = None
        self._do_refresh = True

    def __hydpy__connect_variable2subgroup__(self) -> None:
        """Connect the actual |SimpleInterpolator| object with the given
        |SubParameters| object."""
        self.fastaccess = self.subpars.fastaccess
        setattr(self.fastaccess, self.name, self.__simpleinterpolator)

    def __call__(self, algorithm: InterpAlgorithm) -> None:
        self._algorithm = algorithm
        self.__simpleinterpolator = interputils.SimpleInterpolator(algorithm)
        setattr(self.fastaccess, self.name, self.__simpleinterpolator)

    @property
    def algorithm(self) -> InterpAlgorithm:
        """The handled interpolation algorithm.

        Trying to access the "I" object before defining it results in the following
        error:

        >>> from hydpy.auxs.interptools import SimpleInterpolator
        >>> SimpleInterpolator(None).algorithm
        Traceback (most recent call last):
        ...
        RuntimeError: For parameter `simpleinterpolator` of element `?`, no \
interpolator has been defined so far.
        """
        if self._algorithm:
            return self._algorithm
        raise RuntimeError(
            f"For parameter {objecttools.elementphrase(self)}, no interpolator has "
            f"been defined so far."
        )

    @property
    def nmb_inputs(self) -> int:
        """The number of input values."""
        return self.algorithm.nmb_inputs

    @property
    def nmb_outputs(self) -> int:
        """The number of output values."""
        return self.algorithm.nmb_outputs

    @property
    def inputs(self) -> VectorFloat:
        """The current input values."""
        return self.algorithm.inputs

    @property
    def outputs(self) -> VectorFloat:
        """The current input values."""
        return self.algorithm.outputs

    @property
    def output_derivatives(self) -> VectorFloat:
        """The current input values."""
        return self.algorithm.output_derivatives

    def verify(self) -> None:
        """Raise a |RuntimeError| if the current |InterpAlgorithm| object shows
        inconsistencies."""
        self.algorithm.verify()

    def calculate_values(self) -> None:
        """Calculate the output values based on the input values defined previously."""
        self.algorithm.calculate_values()

    def calculate_derivatives(self, idx: int, /) -> None:
        """Calculate the derivatives of the output values with respect to the input
        value of the given index."""
        self.algorithm.calculate_derivatives(idx)

    def print_table(self, xs: VectorFloat | MatrixFloat) -> None:
        """Process the given input data and print the interpolated output values as
        well as all partial first-order derivatives."""
        self.algorithm.print_table(xs=xs)

    def plot(
        self,
        xmin: float,
        xmax: float,
        *,
        idx_input: int = 0,
        idx_output: int = 0,
        points: int = 100,
        **kwargs: float | str | None,
    ) -> pyplot.Figure:
        """Plot the relationship between particular input (`idx_input`) and output
        (`idx_output`) values defined by the actual |InterpAlgorithm| object."""
        figure = self.algorithm.plot(
            xmin=xmin,
            xmax=xmax,
            idx_input=idx_input,
            idx_output=idx_output,
            points=points,
            **kwargs,
        )
        self._update_labels()
        return figure

    def __repr__(self) -> str:
        if self._algorithm is None:
            return f"{self.name}(?)"
        return "\n".join(
            (f"{self.name}(", self._algorithm.assignrepr(prefix="    ", indent=4), ")")
        )


class SeasonalInterpolator(BaseInterpolator):
    """Represent interpolation patterns showing an annual cycle.

    Class |SeasonalInterpolator| is an alternative implementation of class
    |SeasonalParameter| designed for handling multiple |InterpAlgorithm| objects that
    are valid for different times of the year.  The total output of
    |SeasonalInterpolator| is the weighted mean of the outputs of its |InterpAlgorithm|
    objects.  The required weights depend on the season and are available within the
    |SeasonalInterpolator.ratios| matrix.

    To explain this in more detail, we modify an example of the documentatiob on class
    |SeasonalParameter|.  Let us define a |SeasonalInterpolator| object that contains
    interpolators for January 1, March 1, and July 1, two of type |ANN| and one of type
    |PPoly|:

    >>> from hydpy import ANN, Poly, PPoly, pub, SeasonalInterpolator
    >>> pub.timegrids = "2000-01-01", "2000-10-01", "1d"
    >>> seasonalinterpolator = SeasonalInterpolator(None)
    >>> seasonalinterpolator(
    ...     _1_1_12=ANN(nmb_inputs=1, nmb_neurons=(1,), nmb_outputs=1,
    ...                 weights_input=0.0, weights_output=0.0,
    ...                 intercepts_hidden=0.0, intercepts_output=1.0),
    ...     _7_1_12=ANN(nmb_inputs=1, nmb_neurons=(1,), nmb_outputs=1,
    ...                 weights_input=4.0, weights_output=3.0,
    ...                 intercepts_hidden=-16.0, intercepts_output=-1.0),
    ...     _3_1_12=PPoly(Poly(x0=0.0, cs=(-1.0,))))

    The confusing time order in the initialisation call above does not pose a problem,
    as class |SeasonalInterpolator| performs time sorting internally:

    >>> seasonalinterpolator
    seasonalinterpolator(
        toy_1_1_12_0_0=ANN(
            weights_input=[[0.0]],
            weights_output=[[0.0]],
            intercepts_hidden=[[0.0]],
            intercepts_output=[1.0],
        ),
        toy_3_1_12_0_0=PPoly(
            Poly(x0=0.0, cs=(-1.0,)),
        ),
        toy_7_1_12_0_0=ANN(
            weights_input=[[4.0]],
            weights_output=[[3.0]],
            intercepts_hidden=[[-16.0]],
            intercepts_output=[-1.0],
        ),
    )

    Use method |SeasonalInterpolator.plot| to visualise all interpolators at once:

    >>> figure = seasonalinterpolator.plot(xmin=0.0, xmax=8.0)

    You can use the `pyplot` API of `matplotlib` to modify the figure or to save it to
    disk (or print it to the screen, in case the interactive mode of `matplotlib` is
    disabled):

    >>> from hydpy.core.testtools import save_autofig
    >>> save_autofig("SeasonalInterpolator_plot.png", figure=figure)

    .. image:: SeasonalInterpolator_plot.png

    Property |SeasonalInterpolator.shape| reflects the number of required weighting
    ratios for each time of year (in this example, 366 days per year) and each
    interpolator (in this example, three):

    >>> seasonalinterpolator.shape
    (366, 3)

    The following plot shows the |SeasonalInterpolator.ratios| used for weighting (note
    that the missing values for October, November, and December are irrelevant for the
    initialisation period):

    .. testsetup::

        >>> from matplotlib import pyplot
        >>> from hydpy.docs import autofigs
        >>> import os
        >>> for idx, toy in enumerate(seasonalinterpolator.toys):
        ...     _ = pyplot.plot(seasonalinterpolator.ratios[:, idx], label=str(toy))
        >>> _ = pyplot.legend()
        >>> _ = pyplot.xticks(ticks=[0, 60, 182], labels=["Jan 1", "Mar 1", "Jul 1"])
        >>> filename = "SeasonalInterpolator_ratios.png"
        >>> pyplot.savefig(os.path.join(autofigs.__path__[0], filename))
        >>> pyplot.clf()

    ... image:: SeasonalInterpolator_ratios.png

    For example, on July 1 (which is the 183rd day of a leap year), only the output of
    the third interpolator is relevant:

    >>> from hydpy import print_vector
    >>> print_vector(seasonalinterpolator.ratios[182])
    0.0, 0.0, 1.0

    On June 30 and July 2, the second and the first interpolators are also relevant:

    >>> print_vector(seasonalinterpolator.ratios[181])
    0.0, 0.008197, 0.991803
    >>> print_vector(seasonalinterpolator.ratios[183])
    0.005435, 0.0, 0.994565

    Inserting data, processing this data, and fetching the output works as explained
    for class |SimpleInterpolator|, except that you must additionally pass the index of
    the actual time of year.  For example, the index value `182` activates the third
    interpolator only, configured as in the first example of the documentation on |ANN|:

    >>> from hydpy import round_
    >>> for input_ in range(9):
    ...     seasonalinterpolator.inputs[0] = input_
    ...     seasonalinterpolator.calculate_values(182)
    ...     round_([input_, seasonalinterpolator.outputs[0]])
    0, -1.0
    1, -0.999982
    2, -0.998994
    3, -0.946041
    4, 0.5
    5, 1.946041
    6, 1.998994
    7, 1.999982
    8, 2.0

    To demonstrate that the final output values are the weighted mean of the output
    values of the different interpolators, we repeat the above example for January 13.
    For this day of the year, the first and the second interpolator have ratios of 0.8
    and 0.2, respectively:

    >>> print_vector(seasonalinterpolator.ratios[12])
    0.8, 0.2, 0.0

    Both interpolators calculate constant values.  The sum of the outputs of the first
    (1.0) and the second interpolator (-1.0) multiplied with their weights for January
    13 is 0.6.

    >>> seasonalinterpolator.calculate_values(12)
    >>> round_(seasonalinterpolator.outputs[0])
    0.6

    It is of great importance that all contained interpolators are consistent.  Class
    |SeasonalInterpolator| performs some related checks:

    >>> seasonalinterpolator = SeasonalInterpolator(None)
    >>> seasonalinterpolator.calculate_values(0)
    Traceback (most recent call last):
    ...
    RuntimeError: The parameter `seasonalinterpolator` of element `?` has not been \
properly prepared so far.

    >>> seasonalinterpolator(1)
    Traceback (most recent call last):
    ...
    TypeError: Type `int` is not (a subclass of) type `InterpAlgorithm`.

    >>> seasonalinterpolator(_13_1_12=PPoly(Poly(x0=0.0, cs=(0.0,))))
    Traceback (most recent call last):
    ...
    ValueError: While trying to add a season specific interpolator to parameter \
`seasonalinterpolator` of element `?`, the following error occurred: While trying to \
initialise a TOY object based on argument value `_13_1_12` of type `str`, the \
following error occurred: While trying to retrieve the month, the following error \
occurred: The value of property `month` of TOY (time of year) objects must lie within \
the range `(1, 12)`, but the given value is `13`.

    >>> seasonalinterpolator(PPoly(Poly(x0=0.0, cs=(0.0,))))
    >>> seasonalinterpolator
    seasonalinterpolator(
        PPoly(
            Poly(x0=0.0, cs=(0.0,)),
        )
    )

    >>> seasonalinterpolator(PPoly(Poly(x0=0.0, cs=(0.0,))),
    ...                      _7_1_12=PPoly(Poly(x0=1.0, cs=(1.0,))),
    ...                      _3_1_12=PPoly(Poly(x0=20, cs=(1.0,))))
    Traceback (most recent call last):
    ...
    ValueError: Type `SeasonalInterpolator` accepts either a single positional \
argument or an arbitrary number of keyword arguments, but for the corresponding \
parameter of element `?` 1 positional and 2 keyword arguments have been given.

    >>> seasonalinterpolator(_1_1_12=ANN(nmb_inputs=2, nmb_outputs=1),
    ...                      _7_1_12=PPoly(Poly(x0=1.0, cs=(1.0,))),
    ...                      _3_1_12=PPoly(Poly(x0=20, cs=(1.0,))))
    Traceback (most recent call last):
    ...
    RuntimeError: The number of input and output values of all interpolators \
handled by parameter `seasonalinterpolator` of element `?` must be defined in advance \
and be the same, which is not the case for at least two given interpolators.

    For safety, each failure results in a total loss of the previously defined
    interpolators:

    >>> seasonalinterpolator
    seasonalinterpolator()

    You can add interpolators via attribute access:

    >>> seasonalinterpolator.toy_1_1_12 = PPoly(Poly(x0=0.0, cs=(0.0,)))

    If you set an attribute, everything updates automatically, e.g.:

    >>> round_(seasonalinterpolator.ratios[0])
    1.0

    The mentioned safety checks also apply when adding interpolators via attribute
    access:

    >>> seasonalinterpolator.toy_7_1_12 = ANN(nmb_inputs=2, nmb_outputs=1)
    Traceback (most recent call last):
    ...
    RuntimeError: While trying to assign a new interpolator to parameter \
`seasonalinterpolator` of element `?` based on the string `toy_7_1_12`, the following \
error occurred: The number of input and output values of all interpolators handled by \
parameter `seasonalinterpolator` of element `?` must be defined in advance and be the \
same, which is not the case for at least two given interpolators.

    Besides setting new interpolators, getting and deleting them also works:

    >>> seasonalinterpolator.toy_1_1_12 = PPoly(Poly(x0=0.0, cs=(0.0,)))
    >>> seasonalinterpolator.toy_1_1_12
    PPoly(
        Poly(x0=0.0, cs=(0.0,)),
    )
    >>> del seasonalinterpolator.toy_1_1_12

    There are two error messages related to specific attribute access problems:

    >>> seasonalinterpolator.toy_1_1_12
    Traceback (most recent call last):
    ...
    AttributeError: While trying to look up for an interpolator handled by parameter \
`seasonalinterpolator` of element `?` based on the string `toy_1_1_12`, the following \
error occurred: No interpolator is registered under a TOY object named `toy_1_1_12_0_0`.

    >>> del seasonalinterpolator.toy_1_1_12
    Traceback (most recent call last):
    ...
    AttributeError: While trying to remove an interpolator from parameter \
`seasonalinterpolator` of element `?` based on the string `toy_1_1_12`, the following \
error occurred: No interpolator is registered under a TOY object named `toy_1_1_12_0_0`.

    >>> seasonalinterpolator.toy_1_1_12 = 1
    Traceback (most recent call last):
    ...
    TypeError: While trying to assign a new interpolator to parameter \
`seasonalinterpolator` of element `?` based on the string `toy_1_1_12`, the following \
error occurred: Value `1` of type `int` has been given, but an object of type \
`InterpAlgorithm` is required.

    Setting and deleting "normal" attributes is supported:

    >>> seasonalinterpolator.temp = 999
    >>> seasonalinterpolator.temp
    999
    >>> del seasonalinterpolator.temp
    >>> seasonalinterpolator.temp
    Traceback (most recent call last):
    ...
    AttributeError: 'SeasonalInterpolator' object has no attribute 'temp'
    """

    TYPE = "interputils.SeasonalInterpolator"

    nmb_algorithms: int

    _toy2algorithm: list[tuple[timetools.TOY, InterpAlgorithm]]
    _do_refresh: bool
    __seasonalinterpolator: interputils.SeasonalInterpolator | None

    def __init__(self, subvars: parametertools.SubParameters) -> None:
        self.subvars = subvars
        self.subpars = subvars
        self.fastaccess = parametertools.FastAccessParameter()
        self._toy2algorithm = []
        self.__seasonalinterpolator = None
        self._do_refresh = True

    @overload
    def __call__(self, __algorithm: InterpAlgorithm) -> None: ...

    @overload
    def __call__(self, **algorithm: InterpAlgorithm) -> None: ...

    def __call__(
        self, *algorithm: InterpAlgorithm, **algorithms: InterpAlgorithm
    ) -> None:
        self._toy2algorithm = []
        self._do_refresh = False
        try:
            if (len(algorithm) > 1) or (algorithm and algorithms):
                raise ValueError(
                    f"Type `{type(self).__name__}` accepts either a single positional "
                    f"argument or an arbitrary number of keyword arguments, but for "
                    f"the corresponding parameter of element "
                    f"`{objecttools.devicename(self)}` {len(algorithm)} positional "
                    f"and {len(algorithms)} keyword arguments have been given."
                )
            if algorithm:
                algorithms["_1"] = algorithm[0]
            for toystr, value in algorithms.items():
                if not isinstance(value, InterpAlgorithm):
                    raise TypeError(
                        f"Type `{type(value).__name__}` is not (a subclass of) type "
                        f"`InterpAlgorithm`."
                    )
                try:
                    self._add_toyalgorithpair(toystr, value)
                except BaseException:
                    objecttools.augment_excmessage(
                        f"While trying to add a season specific interpolator to "
                        f"parameter `{self.name}` of element "
                        f"`{objecttools.devicename(self)}`"
                    )
        except BaseException as exc:
            self._toy2algorithm.clear()
            raise exc
        finally:
            self._do_refresh = True
            self.refresh()

    def _add_toyalgorithpair(self, name: str, value: InterpAlgorithm) -> None:
        toy_new = timetools.TOY(name)
        if len(self._toy2algorithm) == 0:
            self._toy2algorithm.append((toy_new, value))
        secs_new = toy_new.seconds_passed
        if secs_new > self._toy2algorithm[-1][0].seconds_passed:
            self._toy2algorithm.append((toy_new, value))
        else:
            for idx, (toy_old, _) in enumerate(self._toy2algorithm[:]):
                secs_old = toy_old.seconds_passed
                if secs_new == secs_old:
                    self._toy2algorithm[idx] = toy_new, value
                    break
                if secs_new < secs_old:
                    self._toy2algorithm.insert(idx, (toy_new, value))
                    break

    def __hydpy__connect_variable2subgroup__(self) -> None:
        """Connect the actual |SeasonalInterpolator| object with the given
        |SubParameters| object."""
        self.fastaccess = self.subpars.fastaccess
        setattr(self.fastaccess, self.name, self.__seasonalinterpolator)

    def refresh(self) -> None:
        """Prepare the actual |SeasonalInterpolator| object for calculations.

        Class |SeasonalInterpolator| stores its |InterpAlgorithm| objects by reference.
        Therefore, despite all automated refreshings (explained in the general
        documentation on class |SeasonalInterpolator|), it is still possible to destroy
        the inner consistency of a |SeasonalInterpolator| instance:

        >>> from hydpy import ANN, SeasonalInterpolator
        >>> seasonalinterpolator = SeasonalInterpolator(None)
        >>> seasonalinterpolator.simulationstep = "1d"
        >>> jan = ANN(nmb_inputs=1, nmb_neurons=(1,), nmb_outputs=1,
        ...           weights_input=0.0, weights_output=0.0,
        ...           intercepts_hidden=0.0, intercepts_output=1.0)
        >>> seasonalinterpolator(_1_1_12=jan)
        >>> jan.nmb_inputs, jan.nmb_outputs = 2, 3
        >>> jan.nmb_inputs, jan.nmb_outputs
        (2, 3)
        >>> seasonalinterpolator.nmb_inputs, seasonalinterpolator.nmb_outputs
        (1, 1)

        Due to the Cython implementation of the actual interpolation, such an
        inconsistencies might result in a program crash without any informative error
        message.  Therefore, whenever you are think some inconsistency might have crept
        in and you want to repair it, call method |SeasonalInterpolator.refresh|
        manually:

        >>> seasonalinterpolator.refresh()
        >>> jan.nmb_inputs, jan.nmb_outputs
        (2, 3)
        >>> seasonalinterpolator.nmb_inputs, seasonalinterpolator.nmb_outputs
        (2, 3)
        """
        if self._do_refresh:
            if self.algorithms:
                self.__seasonalinterpolator = interputils.SeasonalInterpolator(
                    self.algorithms
                )
                setattr(self.fastaccess, self.name, self._seasonalinterpolator)
                self._prepare_shape()
                if self._seasonalinterpolator.nmb_algorithms > 1:
                    self._interp()
                else:
                    self._seasonalinterpolator.ratios[:, 0] = 1.0
                self.verify()
            else:
                self.__seasonalinterpolator = None

    def verify(self) -> None:
        """Raise a |RuntimeError| and remove all handled interpolators if they are
        defined inconsistently.

        Class |SeasonalInterpolator| stores its |InterpAlgorithm| objects by reference.
        Therefore, despite all automated refreshings (explained in the general
        documentation on class |SeasonalInterpolator|), it is still possible to destroy
        the inner consistency of a |SeasonalInterpolator| instance:

        >>> from hydpy import ANN, pub, SeasonalInterpolator
        >>> seasonalinterpolator = SeasonalInterpolator(None)
        >>> pub.options.simulationstep = "1d"
        >>> jan = ANN(nmb_inputs=1, nmb_neurons=(1,), nmb_outputs=1,
        ...           weights_input=0.0, weights_output=0.0,
        ...           intercepts_hidden=0.0, intercepts_output=1.0)
        >>> seasonalinterpolator(_1_1_12=jan)
        >>> jan.nmb_inputs, jan.nmb_outputs = 2, 3
        >>> jan.nmb_inputs, jan.nmb_outputs
        (2, 3)
        >>> seasonalinterpolator.nmb_inputs, seasonalinterpolator.nmb_outputs
        (1, 1)

        Due to the Cython implementation of the actual interpolation, such an
        inconsistencies might result in a program crash without any informative error
        message.  Therefore, whenever you are think some inconsistency might have crept
        in, and you want to know if your suspicion is correct, call method
        |SeasonalInterpolator.verify|.

        >>> seasonalinterpolator.verify()
        Traceback (most recent call last):
        ...
        RuntimeError: The number of input and output values of all interpolators \
handled by parameter `seasonalinterpolator` of element `?` must be defined in advance \
and be the same, which is not the case for at least two given interpolators.

        >>> seasonalinterpolator
        seasonalinterpolator()

        >>> seasonalinterpolator.verify()
        Traceback (most recent call last):
        ...
        RuntimeError: Seasonal interpolators need to handle at least one \
interpolation algorithm object, but for parameter `seasonalinterpolator` of element \
`?` none is defined so far.
        """
        if not self.algorithms:
            self._toy2algorithm = []
            raise RuntimeError(
                f"Seasonal interpolators need to handle at least one interpolation "
                f"algorithm object, but for parameter "
                f"{objecttools.elementphrase(self)} none is defined so far."
            )
        for _, seasonalinterpolator in self:
            seasonalinterpolator.verify()
            if (self.nmb_inputs != seasonalinterpolator.nmb_inputs) or (
                self.nmb_outputs != seasonalinterpolator.nmb_outputs
            ):
                self._toy2algorithm = []
                raise RuntimeError(
                    f"The number of input and output values of all interpolators "
                    f"handled by parameter {objecttools.elementphrase(self)} must be "
                    f"defined in advance and be the same, which is not the case for "
                    f"at least two given interpolators."
                )

    def _interp(self) -> None:
        ratios = self.ratios
        ratios[:, :] = numpy.nan
        toys = self.toys
        centred = timetools.TOY.centred_timegrid()
        for tdx, (date, rel) in enumerate(zip(*centred)):
            if rel:
                xnew = timetools.TOY(date)
                for idx_1, x_1 in enumerate(toys):
                    if x_1 > xnew:
                        idx_0 = idx_1 - 1
                        x_0 = toys[idx_0]
                        break
                else:
                    idx_0 = -1
                    idx_1 = 0
                    x_0 = toys[idx_0]
                    x_1 = toys[idx_1]
                ratios[tdx, :] = 0.0
                ratios[tdx, idx_1] = (xnew - x_0) / (x_1 - x_0)
                ratios[tdx, idx_0] = 1.0 - ratios[tdx, idx_1]

    @property
    def shape(self) -> tuple[int, int]:
        """The shape of array |SeasonalInterpolator.ratios|."""
        shape = self.ratios.shape
        return int(shape[0]), int(shape[1])

    def _prepare_shape(self) -> None:
        """Private on purpose."""
        nmb_weights = timetools.Period("366d") / hydpy.pub.options.simulationstep
        nmb_weights = int(numpy.ceil(round(nmb_weights, 10)))
        shape = (nmb_weights, self._seasonalinterpolator.nmb_algorithms)
        getattr(self.fastaccess, self.name).ratios = numpy.zeros(
            shape, dtype=config.NP_FLOAT
        )

    @property
    def toys(self) -> tuple[timetools.TOY, ...]:
        """A sorted |tuple| of all contained |TOY| objects."""
        return tuple(toy for (toy, _) in self)

    @property
    def algorithms(self) -> tuple[InterpAlgorithm, ...]:
        """A sorted |tuple| of all handled interpolators."""
        return tuple(seasonalinterpolator for (_, seasonalinterpolator) in self)

    @property
    def ratios(self) -> MatrixFloat:
        """The ratios for weighting the interpolator outputs."""
        return numpy.asarray(self._seasonalinterpolator.ratios)

    @property
    def _seasonalinterpolator(self) -> interputils.SeasonalInterpolator:
        seasonalinterpolator = self.__seasonalinterpolator
        if seasonalinterpolator:
            return seasonalinterpolator
        raise RuntimeError(
            f"The parameter {objecttools.elementphrase(self)} has not been properly "
            f"prepared so far."
        )

    @property
    def nmb_inputs(self) -> int:
        """The general number of input values of the interpolators."""
        return self._seasonalinterpolator.nmb_inputs

    @property
    def inputs(self) -> VectorFloat:
        """The general input data for the interpolators."""
        return numpy.asarray(self._seasonalinterpolator.inputs)

    @property
    def nmb_outputs(self) -> int:
        """The general number of output values of all interpolators."""
        return self._seasonalinterpolator.nmb_outputs

    @property
    def outputs(self) -> VectorFloat:
        """The weighted output of the interpolators."""
        return numpy.asarray(self._seasonalinterpolator.outputs)

    def calculate_values(self, idx: int, /) -> None:
        """Calculate the weighted output values based on the input values defined
        previously for the given index referencing the actual time of year."""
        self._seasonalinterpolator.calculate_values(idx)

    def plot(
        self,
        xmin: float,
        xmax: float,
        *,
        idx_input: int = 0,
        idx_output: int = 0,
        points: int = 100,
        legend: bool = True,
        **kwargs: float | str | None,
    ) -> pyplot.Figure:
        """Call method |InterpAlgorithm.plot| of all currently handled
        |InterpAlgorithm| objects."""
        for toy, seasonalinterpolator in self:
            figure = seasonalinterpolator.plot(
                xmin=xmin,
                xmax=xmax,
                idx_input=idx_input,
                idx_output=idx_output,
                points=points,
                label=str(toy),
                **kwargs,
            )
        if legend:
            pyplot.legend()
        self._update_labels()
        return figure

    def __getattr__(self, name: str) -> InterpAlgorithm:
        if name.startswith("toy_"):
            try:
                selected = timetools.TOY(name)
                for available, algorithm in self._toy2algorithm:
                    if selected == available:
                        return algorithm
                raise AttributeError(
                    f"No interpolator is registered under a TOY object named "
                    f"`{timetools.TOY(name)}`."
                )
            except BaseException:
                objecttools.augment_excmessage(
                    f"While trying to look up for an interpolator handled by "
                    f"parameter {objecttools.elementphrase(self)} based on the string "
                    f"`{name}`"
                )
        else:
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
            )

    def __setattr__(self, name: str, value: object) -> None:
        if name.startswith("toy_"):
            try:
                if not isinstance(value, InterpAlgorithm):
                    raise TypeError(
                        f"{objecttools.value_of_type(value).capitalize()} has been "
                        f"given, but an object of type `InterpAlgorithm` is required."
                    )
                self._add_toyalgorithpair(name, value)
                self.refresh()
            except BaseException:
                objecttools.augment_excmessage(
                    f"While trying to assign a new interpolator to parameter "
                    f"{objecttools.elementphrase(self)} based on the string `{name}`"
                )
        else:
            object.__setattr__(self, name, value)

    def __delattr__(self, name: str) -> None:
        if name.startswith("toy_"):
            try:
                selected = timetools.TOY(name)
                for idx, (available, _) in enumerate(self._toy2algorithm):
                    if selected == available:
                        break
                else:
                    raise AttributeError(
                        f"No interpolator is registered under a TOY object named "
                        f"`{timetools.TOY(name)}`."
                    ) from None
                del self._toy2algorithm[idx]
                self.refresh()
            except BaseException:
                objecttools.augment_excmessage(
                    f"While trying to remove an interpolator from parameter "
                    f"{objecttools.elementphrase(self)} based on the string `{name}`"
                )
        else:
            object.__delattr__(self, name)

    def __iter__(self) -> Iterator[tuple[timetools.TOY, InterpAlgorithm]]:
        return iter(self._toy2algorithm)

    def __repr__(self) -> str:
        if not self:
            return f"{self.name}()"
        lines = [f"{self.name}("]
        if (len(self) == 1) and (self.toys[0] == timetools.TOY0):
            lines.append(self.algorithms[0].assignrepr("    ", 4))
        else:
            for toy, seasonalinterpolator in self:
                line = seasonalinterpolator.assignrepr(f"    {toy}=", 4)
                lines.append(f"{line},")
        lines.append(")")
        return "\n".join(lines)

    def __len__(self) -> int:
        return len(self._toy2algorithm)

    def __dir__(self) -> list[str]:
        """
        >>> from hydpy import ANN, pub, SeasonalInterpolator
        >>> pub.timegrids = "2000-01-01", "2000-01-02", "1d"
        >>> si = SeasonalInterpolator(None)
        >>> si(
        ...     ANN(nmb_inputs=1, nmb_neurons=(1,), nmb_outputs=1,
        ...         weights_input=0.0, weights_output=0.0,
        ...         intercepts_hidden=0.0, intercepts_output=1.0))
        >>> sorted(set(dir(si)) - set(object.__dir__(si)))
        ['toy_1_1_0_0_0']
        """
        return cast(list[str], super().__dir__()) + [str(toy) for toy in self.toys]
