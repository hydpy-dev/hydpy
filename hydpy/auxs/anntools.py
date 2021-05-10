# -*- coding: utf-8 -*-
"""This module implements rudimentary artificial neural network tools
required for some models implemented in the *HydPy* framework.

The relevant models apply some of the neural network features during
simulation runs, which is why we implement these features in the Cython
extension module |annutils|.
"""

# import...
# ...from standard library
import weakref
from typing import *

# ...from site-packages
import numpy

# ...from HydPy
import hydpy
from hydpy.core import exceptiontools
from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.core import propertytools
from hydpy.core import timetools
from hydpy.core import variabletools
from hydpy.core.typingtools import *
from hydpy.cythons.autogen import annutils


if TYPE_CHECKING:
    from matplotlib import pyplot
else:
    pyplot = exceptiontools.OptionalImport("pyplot", ["matplotlib.pyplot"], locals())


class _ANNArrayProperty(
    propertytools.DependentProperty[
        propertytools.InputType,
        propertytools.OutputType,
    ],
):

    _obj2cann: Dict[Any, annutils.ANN] = weakref.WeakKeyDictionary()

    def __init__(
        self,
        protected: propertytools.ProtectedProperties,
        doc: str,
    ) -> None:
        super().__init__(
            protected=protected,
            fget=self._fget,
            fset=self._fset,
            fdel=self._fdel,
        )
        self.set_doc(doc)

    @classmethod
    def add_cann(cls, obj: Any, cann: annutils.ANN) -> None:
        """Log the given Cython based ANN for the given object."""
        cls._obj2cann[obj] = cann

    @property
    def _shape(self) -> str:
        return f"shape_{self.name}"

    def _fget(self, obj: "ANN") -> propertytools.OutputType:
        cann = self._obj2cann[obj]
        return numpy.asarray(getattr(cann, self.name))

    def _fset(self, obj: "ANN", value: Optional[propertytools.InputType]) -> None:
        if value is None:
            self.fdel(obj)
        else:
            try:
                cann = self._obj2cann[obj]
                shape = getattr(obj, self._shape)
                if self.name == "activation":
                    array = numpy.full(shape, value, dtype=int)
                else:
                    array = numpy.full(shape, value, dtype=float)
                setattr(cann, self.name, array)
            except BaseException:
                descr = " ".join(reversed(self.name.split("_")))
                objecttools.augment_excmessage(
                    f"While trying to set the {descr} of the artificial "
                    f"neural network {objecttools.elementphrase(obj)}"
                )

    def _fdel(self, obj: "ANN") -> None:
        cann = self._obj2cann[obj]
        if self.name == "activation":
            array = numpy.ones(getattr(obj, self._shape), dtype=int)
        else:
            array = numpy.zeros(getattr(obj, self._shape), dtype=float)
        setattr(cann, self.name, array)


class BaseANN:
    """Base for implementing artificial neural networks classes."""

    XLABEL: str
    YLABEL: str
    name: str

    def __init_subclass__(cls) -> None:
        cls.name = cls.__name__.lower()
        subclasscounter = variabletools.Variable.__hydpy__subclasscounter__ + 1
        variabletools.Variable.__hydpy__subclasscounter__ = subclasscounter
        cls.__hydpy__subclasscounter__ = subclasscounter

    def _update_labels(self) -> None:
        xlabel = getattr(self, "XLABEL", None)
        if xlabel:
            pyplot.xlabel(xlabel)
        ylabel = getattr(self, "YLABEL", None)
        if ylabel:
            pyplot.ylabel(ylabel)


class ANN(BaseANN):
    """Multi-layer feed-forward artificial neural network.

    By default, class |anntools.ANN| uses the logistic function
    :math:`f(x) = \\frac{1}{1+exp(-x)}` to calculate the activation of
    the neurons of the hidden layer.  Alternatively, one can select the
    identity function :math:`f(x) = x` or a variant of the logistic
    function for filtering specific inputs.  See property
    |anntools.ANN.activation| for more information on how to do this.

    Usually, one applies class |anntools.ANN| for the derivation of very
    complex control parameters.  Its original purpose was to allow for
    defining arbitrary continuous relationships between the water stored
    in a dam and the associated water stage (see model |dam_v001|).
    However, for testing purposes class |anntools.ANN| can also be applied
    directly, as shown in the following examples.

    Firstly, define the most simple artificial neural network consisting of
    only one input node, one hidden neuron, and one output node, and pass
    some arbitrary network parameters:

    >>> from hydpy import ANN, nan
    >>> ann = ANN(None)
    >>> ann(nmb_inputs=1, nmb_neurons=(1,), nmb_outputs=1,
    ...     weights_input=4.0, weights_output=3.0,
    ...     intercepts_hidden=-16.0, intercepts_output=-1.0)

    The following loop subsequently sets the values 0 to 8 as input values,
    performs the calculation, and prints out the final output.  As to be
    expected, the results show the shape of the logistic function:

    >>> from hydpy import round_
    >>> for input_ in range(9):
    ...     ann.inputs[0] = input_
    ...     ann.calculate_values()
    ...     round_([input_, ann.outputs[0]])
    0, -1.0
    1, -0.999982
    2, -0.998994
    3, -0.946041
    4, 0.5
    5, 1.946041
    6, 1.998994
    7, 1.999982
    8, 2.0

    One can also directly plot the resulting graph:

    >>> ann.plot(0.0, 8.0)

    You can use the `pyplot` API of `matplotlib` to modify the figure
    or to save it to disk (or print it to the screen, in case the
    interactive mode of `matplotlib` is disabled):

    >>> from hydpy.core.testtools import save_autofig
    >>> save_autofig("ANN_plot.png")

    .. image:: ANN_plot.png

    Some models might require the derivative of certain outputs with respect
    to individual inputs.  One example is application model the |dam_v006|,
    which uses class |anntools.ANN| to model the relationship between water
    storage and stage of a lake.  During a simulation run , it additionally
    needs to know the area of the water surface, which is the derivative of
    storage with respect to stage.  For such purposes, class |anntools.ANN|
    provides method |anntools.ANN.calculate_derivatives|.  In the following
    example, we apply this method and compare its results with finite
    difference approximations:

    >>> d_input = 1e-8
    >>> for input_ in range(9):
    ...     ann.inputs[0] = input_-d_input/2.0
    ...     ann.calculate_values()
    ...     value0 = ann.outputs[0]
    ...     ann.inputs[0] = input_+d_input/2.0
    ...     ann.calculate_values()
    ...     value1 = ann.outputs[0]
    ...     derivative = (value1-value0)/d_input
    ...     ann.inputs[0] = input_
    ...     ann.calculate_values()
    ...     ann.calculate_derivatives(0)
    ...     round_([input_, derivative, ann.output_derivatives[0]])
    0, 0.000001, 0.000001
    1, 0.000074, 0.000074
    2, 0.004023, 0.004023
    3, 0.211952, 0.211952
    4, 3.0, 3.0
    5, 0.211952, 0.211952
    6, 0.004023, 0.004023
    7, 0.000074, 0.000074
    8, 0.000001, 0.000001

    Note the following two potential pitfalls (both due to improving the
    computational efficiency of method |anntools.ANN.calculate_derivatives|):
    First, for networks with more than one hidden layer, you must call
    |anntools.ANN.calculate_values| before calling
    |anntools.ANN.calculate_derivatives|.  Second, method
    |anntools.ANN.calculate_derivatives| calculates the derivatives
    with respect to a single input only, to be selected by the `idx_input`
    argument.  However, it works fine to call method
    |anntools.ANN.calculate_values| ones and to call
    |anntools.ANN.calculate_derivatives| multiple times afterwards. Then
    you can subsequently pass different index values to calculate the
    derivatives with respect to multiple inputs.

    The following example shows that everything works well for more complex
    single layer networks also (we checked the results manually using a
    spreadsheet program):

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
    >>> ann.inputs = [-0.1,  1.3,  1.6]
    >>> ann.calculate_values()
    >>> round_(ann.outputs)
    1.822222, 1.876983

    We again validate the calculated derivatives by comparison with numerical
    approximations:

    >>> for idx_input in range(3):
    ...     ann.calculate_derivatives(idx_input)
    ...     round_(ann.output_derivatives)
    0.099449, -0.103039
    -0.01303, 0.365739
    0.027041, -0.203965

    >>> d_input = 1e-8
    >>> for idx_input in range(3):
    ...     input_ = ann.inputs[idx_input]
    ...     ann.inputs[idx_input] = input_-d_input/2.0
    ...     ann.calculate_values()
    ...     values0 = ann.outputs.copy()
    ...     ann.inputs[idx_input] = input_+d_input/2.0
    ...     ann.calculate_values()
    ...     values1 = ann.outputs.copy()
    ...     ann.inputs[idx_input] = input_
    ...     round_((values1-values0)/d_input)
    0.099449, -0.103039
    -0.01303, 0.365739
    0.027041, -0.203965

    The next example shows how to solve the XOR problem with a two-layer
    network.  As usual, `1` stands for `True` and `0` stands for `False`.

    We define a network with two inputs (`I1` and `I2`), two neurons in
    the first hidden layer (`H11` and `H12`), one neuron in the second
    hidden layer (`H2`), and a single output (`O1`):

    >>> ann.nmb_inputs = 2
    >>> ann.nmb_neurons = (2, 1)
    >>> ann.nmb_outputs = 1

    The value of `O1` shall be identical with the activation of `H2`:

    >>> ann.weights_output = 1.0
    >>> ann.intercepts_output = 0.0

    We set all intercepts of the neurons of the hidden layer to 750
    (and initialise unnecessary matrix entries with "nan" to avoid
    confusion). Therefore, an input of 500 or 1000 results in an
    activation state of approximately zero or one, respectively. :

    >>> ann.intercepts_hidden = [[-750.0, -750.0],
    ...                          [-750.0, nan]]

    The weighting factor between both inputs and `H11` is 1000.
    Hence, one `True` input is sufficient to activate `H1`.  In contrast,
    the weighting factor between both inputs and `H12` is 500.
    Hence, two `True` inputs are required to activate `H12`:

    >>> ann.weights_input= [[1000.0, 500.0],
    ...                     [1000.0, 500.0]]

    The weighting factor between `H11` and `H2` is 1000.  Hence, in
    principle, `H11` can activate `H2`.  However, the weighting factor
    between `H12` and `H2` is -1000.  Hence, `H12` prevents `H2` from
    becoming activated even when `H11` is activated:

    >>> ann.weights_hidden= [[[1000.0],
    ...                      [-1000.0]]]

    To recapitulate, `H11` determines if at least one input is `True`,
    `H12` determines if both inputs are `True`, and `H2` determines if
    precisely  one input is `True`, which is the solution for the XOR-problem:

    >>> ann
    ann(
        nmb_inputs=2,
        nmb_neurons=(2, 1),
        weights_input=[[1000.0, 500.0],
                       [1000.0, 500.0]],
        weights_hidden=[[[1000.0],
                         [-1000.0]]],
        weights_output=[[1.0]],
        intercepts_hidden=[[-750.0, -750.0],
                           [-750.0, nan]],
        intercepts_output=[0.0],
    )

    The following calculation confirms the proper configuration of our network:

    >>> for inputs in ((0.0, 0.0),
    ...                (1.0, 0.0),
    ...                (0.0, 1.0),
    ...                (1.0, 1.0)):
    ...    ann.inputs = inputs
    ...    ann.calculate_values()
    ...    round_([inputs[0], inputs[1], ann.outputs[0]])
    0.0, 0.0, 0.0
    1.0, 0.0, 1.0
    0.0, 1.0, 1.0
    1.0, 1.0, 0.0

    To elaborate on the last calculation, we show the corresponding
    activations of the hidden neurons. As both inputs are `True`, both
    `H12` (upper left value) and `H22` (upper right value) are activated,
    but `H2` (lower left value) is not:

    >>> ann.neurons
    array([[1., 1.],
           [0., 0.]])

    Due to sharp response function, the derivatives with respect to both
    inputs are approximately zero:

    >>> for inputs in ((0.0, 0.0),
    ...                (1.0, 0.0),
    ...                (0.0, 1.0),
    ...                (1.0, 1.0)):
    ...    ann.inputs = inputs
    ...    ann.calculate_values()
    ...    ann.calculate_derivatives(0)
    ...    round_([inputs[0], inputs[1], ann.output_derivatives[0]])
    0.0, 0.0, 0.0
    1.0, 0.0, 0.0
    0.0, 1.0, 0.0
    1.0, 1.0, 0.0

    To better validate the calculation of derivatives for multi-layer
    networks, we decrease the weights (and, accordingly, the intercepts)
    of our network, making its response more smooth:

    >>> ann(nmb_inputs=2,
    ...     nmb_neurons=(2, 1),
    ...     nmb_outputs=1,
    ...     weights_input=[[10.0, 5.0],
    ...                    [10.0, 5.0]],
    ...     weights_hidden=[[[10.0],
    ...                      [-10.0]]],
    ...     weights_output=[[1.0]],
    ...     intercepts_hidden=[[-7.5, -7.5],
    ...                        [-7.5, nan]],
    ...     intercepts_output=[0.0])

    The results of method |anntools.ANN.calculate_derivatives| again agree
    with those of the finite difference approximation:

    >>> for inputs in ((0.0, 0.0),
    ...                (1.0, 0.0),
    ...                (0.0, 1.0),
    ...                (1.0, 1.0)):
    ...     ann.inputs = inputs
    ...     ann.calculate_values()
    ...     ann.calculate_derivatives(0)
    ...     derivative1 = ann.output_derivatives[0]
    ...     ann.calculate_derivatives(1)
    ...     derivative2 = ann.output_derivatives[0]
    ...     round_([inputs[0], inputs[1], derivative1, derivative2])
    0.0, 0.0, 0.000015, 0.000015
    1.0, 0.0, 0.694609, 0.694609
    0.0, 1.0, 0.694609, 0.694609
    1.0, 1.0, -0.004129, -0.004129

    >>> d_input = 1e-8
    >>> for inputs in ((0.0, 0.0),
    ...                (1.0, 0.0),
    ...                (0.0, 1.0),
    ...                (1.0, 1.0)):
    ...     derivatives = []
    ...     for idx_input in range(2):
    ...         ann.inputs = inputs
    ...         ann.inputs[idx_input] = inputs[idx_input]-d_input/2.0
    ...         ann.calculate_values()
    ...         value0 = ann.outputs[0]
    ...         ann.inputs[idx_input] = inputs[idx_input]+d_input/2.0
    ...         ann.calculate_values()
    ...         value1 = ann.outputs[0]
    ...         derivatives.append((value1-value0)/d_input)
    ...     round_([inputs[0], inputs[1]] + derivatives)
    0.0, 0.0, 0.000015, 0.000015
    1.0, 0.0, 0.694609, 0.694609
    0.0, 1.0, 0.694609, 0.694609
    1.0, 1.0, -0.004129, -0.004129

    Note that Python class |anntools.ANN| handles a corresponding Cython
    extension class defined in |annutils|, which does not protect itself
    against segmentation faults. But class  |anntools.ANN| takes up this
    task, meaning using its public members should always result in readable
    exceptions instead of program crashes, e.g.:

    >>> ANN(None).nmb_layers
    Traceback (most recent call last):
    ...
    hydpy.core.exceptiontools.AttributeNotReady: Attribute `nmb_layers` \
of object `ann` is not usable so far.  At least, you have to prepare \
attribute `nmb_inputs` first.

    You can compare |anntools.ANN| objects for equality.  The following exhaustive
    tests ensure that one |anntools.ANN| is only considered equal with another
    |anntools.ANN| object with the same network shape and parameter values:

    >>> ann == ann
    True

    >>> ann == 1
    False

    >>> ann2 = ANN(None)
    >>> ann2(nmb_inputs=2,
    ...      nmb_neurons=(2, 1),
    ...      nmb_outputs=1,
    ...      weights_input=[[10.0, 5.0],
    ...                     [10.0, 5.0]],
    ...      weights_hidden=[[[10.0],
    ...                       [-10.0]]],
    ...      weights_output=[[1.0]],
    ...      intercepts_hidden=[[-7.5, -7.5],
    ...                         [-7.5, nan]],
    ...      intercepts_output=[0.0])
    >>> ann == ann2
    True

    >>> ann2.weights_input[0, 0] = nan
    >>> ann == ann2
    False
    >>> ann2.weights_input[0, 0] = 10.0
    >>> ann == ann2
    True

    >>> ann2.weights_hidden[0, 1, 0] = 5.0
    >>> ann == ann2
    False
    >>> ann2.weights_hidden[0, 1, 0] = -10.0
    >>> ann == ann2
    True

    >>> ann2.weights_output[0, 0] = 2.0
    >>> ann == ann2
    False
    >>> ann2.weights_output[0, 0] = 1.0
    >>> ann == ann2
    True

    >>> ann2.intercepts_hidden[1, 0] = nan
    >>> ann == ann2
    False
    >>> ann2.intercepts_hidden[1, 0] = -7.5
    >>> ann == ann2
    True

    >>> ann2.intercepts_output[0] = 0.1
    >>> ann == ann2
    False
    >>> ann2.intercepts_output[0] = 0.0
    >>> ann == ann2
    True

    >>> ann2.activation[0, 0] = 0
    >>> ann == ann2
    False
    >>> ann2.activation[0, 0] = 1
    >>> ann == ann2
    True

    >>> ann2(nmb_inputs=1,
    ...      nmb_neurons=(2, 1),
    ...      nmb_outputs=1)
    >>> ann == ann2
    False

    >>> ann2(nmb_inputs=2,
    ...      nmb_neurons=(1, 1),
    ...      nmb_outputs=1)
    >>> ann == ann2
    False

    >>> ann2(nmb_inputs=2,
    ...      nmb_neurons=(2, 1),
    ...      nmb_outputs=2)
    >>> ann == ann2
    False
    """

    NDIM = 0
    TYPE = "annutils.ANN"
    TIME = None
    SPAN = (None, None)

    __max_nmb_neurons: Optional[int]

    def __init__(self, subvars: parametertools.SubParameters):
        self.subvars = subvars
        self.subpars = subvars
        self.fastaccess = parametertools.FastAccessParameter()
        self._cann = annutils.ANN()
        _ANNArrayProperty.add_cann(self, self._cann)
        self.__max_nmb_neurons = None

    def __hydpy__connect_variable2subgroup__(self) -> None:
        """Connect the actual |anntools.ANN| object with the given
        |SubParameters| object."""
        self.fastaccess = self.subpars.fastaccess
        setattr(self.fastaccess, self.name, self._cann)

    def __call__(
        self,
        *,
        nmb_inputs: int = 1,
        nmb_neurons: Tuple[int, ...] = (1,),
        nmb_outputs: int = 1,
        weights_input: Optional[MatrixInput[float]] = None,
        weights_output: Optional[MatrixInput[float]] = None,
        weights_hidden=None,
        intercepts_hidden: Optional[MatrixInput[float]] = None,
        intercepts_output: Optional[VectorInput[float]] = None,
        activation: Optional[MatrixInput[int]] = None,
    ) -> None:
        self.nmb_inputs = nmb_inputs
        self.nmb_outputs = nmb_outputs
        self.nmb_neurons = nmb_neurons
        self.weights_input = weights_input
        self.weights_hidden = weights_hidden
        self.weights_output = weights_output
        self.intercepts_hidden = intercepts_hidden
        self.intercepts_output = intercepts_output
        self.activation = activation
        del self.inputs
        del self.outputs
        del self.output_derivatives
        del self.neurons
        del self.neuron_derivatives

    def __update_shapes(self) -> None:
        if self.__protectedproperties.allready(self):
            del self.weights_input
            del self.weights_hidden
            del self.weights_output
            del self.intercepts_hidden
            del self.intercepts_output
            del self.activation
            del self.inputs
            del self.outputs
            del self.output_derivatives
            del self.neurons
            del self.neuron_derivatives

    def _get_nmb_inputs(self) -> int:  # pylint: disable=method-hidden
        """The number of input nodes.

        >>> from hydpy import ANN
        >>> ann = ANN(None)
        >>> ann(nmb_inputs=2, nmb_neurons=(2, 1), nmb_outputs=3)
        >>> ann.nmb_inputs
        2
        >>> ann.nmb_inputs = 3
        >>> ann.nmb_inputs
        3
        """
        return self._cann.nmb_inputs

    def _set_nmb_inputs(self, value: int) -> None:
        self._cann.nmb_inputs = int(value)
        self.__update_shapes()

    def _del_nmb_inputs(self) -> None:
        pass

    nmb_inputs = propertytools.ProtectedProperty[int, int](
        fget=_get_nmb_inputs,
        fset=_set_nmb_inputs,
        fdel=_del_nmb_inputs,
    )
    nmb_inputs: int  # type: ignore[no-redef]
    # to improve PyCharm code completion; required until PyCharm is fixed

    def _get_nmb_outputs(self) -> int:
        """The number of output nodes.

        >>> from hydpy import ANN
        >>> ann = ANN(None)
        >>> ann(nmb_inputs=2, nmb_neurons=(2, 1), nmb_outputs=3)
        >>> ann.nmb_outputs
        3
        >>> ann.nmb_outputs = 2
        >>> ann.nmb_outputs
        2
        >>> del ann.nmb_outputs
        >>> ann.nmb_outputs
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: Attribute `nmb_outputs` \
of object `ann` has not been prepared so far.
        """
        return self._cann.nmb_outputs

    def _set_nmb_outputs(self, value: int) -> None:
        self._cann.nmb_outputs = int(value)
        self.__update_shapes()

    def _del_nmb_outputs(self) -> None:
        pass

    nmb_outputs = propertytools.ProtectedProperty[int, int](
        fget=_get_nmb_outputs,
        fset=_set_nmb_outputs,
        fdel=_del_nmb_outputs,
    )
    nmb_outputs: int  # type: ignore[no-redef]
    # to improve PyCharm code completion; required until PyCharm is fixed

    def _get_nmb_neurons(self) -> Tuple[int, ...]:  # pylint: disable=method-hidden
        """The number of neurons of the hidden layers.

        >>> from hydpy import ANN
        >>> ann = ANN(None)
        >>> ann(nmb_inputs=2, nmb_neurons=(2, 1), nmb_outputs=3)
        >>> ann.nmb_neurons
        (2, 1)
        >>> ann.nmb_neurons = (3,)
        >>> ann.nmb_neurons
        (3,)
        >>> del ann.nmb_neurons
        >>> ann.nmb_neurons
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: Attribute `nmb_neurons` \
of object `ann` has not been prepared so far.
        """
        return tuple(numpy.asarray(self._cann.nmb_neurons))

    def _set_nmb_neurons(self, value: Tuple[int, ...]) -> None:
        self._cann.nmb_neurons = numpy.array(value, dtype=int, ndmin=1)
        self._cann.nmb_layers = len(value)
        self.__max_nmb_neurons = max(value)
        self.__update_shapes()

    def _del_nmb_neurons(self) -> None:
        pass

    nmb_neurons = propertytools.ProtectedProperty[Tuple[int, ...], Tuple[int, ...]](
        fget=_get_nmb_neurons,
        fset=_set_nmb_neurons,
        fdel=_del_nmb_neurons,
    )

    nmb_neurons: Tuple[int, ...]  # type: ignore[no-redef]
    # to improve PyCharm code completion; required until PyCharm is fixed

    __protectedproperties = propertytools.ProtectedProperties(
        nmb_inputs, nmb_outputs, nmb_neurons
    )

    @property
    def nmb_weights_input(self) -> int:
        """The number of input weights.

        >>> from hydpy import ANN
        >>> ann = ANN(None)
        >>> ann(nmb_inputs=3, nmb_neurons=(2, 1), nmb_outputs=1)
        >>> ann.nmb_weights_input
        6
        """
        return self.nmb_neurons[0] * self.nmb_inputs

    @property
    def shape_weights_input(self) -> Tuple[int, int]:
        """The shape of the array containing the input weights.

        The first integer value is the number of input nodes; the second
        integer value is the number of neurons of the first hidden layer:

        >>> from hydpy import ANN
        >>> ann = ANN(None)
        >>> ann(nmb_inputs=3, nmb_neurons=(2, 1), nmb_outputs=1)
        >>> ann.shape_weights_input
        (3, 2)
        """
        return self.nmb_inputs, self.nmb_neurons[0]

    weights_input = _ANNArrayProperty[Optional[MatrixInput[float]], Matrix[float]](
        protected=__protectedproperties,
        doc="""The weights between all input nodes and neurons of the first 
        hidden layer.
        
        The "weight properties" of class |anntools.ANN| are usable as 
        explained in-depth for the input weights below. 
    
        The input nodes and the neurons vary on the first axis and the
        second axis of the 2-dimensional array, respectively (see property 
        |anntools.ANN.shape_weights_input|):

        >>> from hydpy import ANN
        >>> ann = ANN(None)
        >>> ann(nmb_inputs=2, nmb_neurons=(3,))
        >>> ann.weights_input
        array([[0., 0., 0.],
               [0., 0., 0.]])
        
        The following error occurs when either the number of input nodes or 
        of hidden neurons is unknown:
        
        >>> del ann.nmb_inputs
        >>> ann.weights_input
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: Attribute \
`weights_input` of object `ann` is not usable so far.  At least, \
you have to prepare attribute `nmb_inputs` first.
        >>> ann.nmb_inputs = 2

        It is allowed to set values via slicing:
        
        >>> ann.weights_input[:, 0] = 1.
        >>> ann.weights_input
        array([[1., 0., 0.],
               [1., 0., 0.]])

        If possible, property |anntools.ANN.weights_input| performs type 
        conversions:

        >>> ann.weights_input = "2"
        >>> ann.weights_input
        array([[2., 2., 2.],
               [2., 2., 2.]])

        One can assign whole matrices directly:

        >>> import numpy
        >>> ann.weights_input = numpy.eye(2, 3)
        >>> ann.weights_input
        array([[1., 0., 0.],
               [0., 1., 0.]])

        One can also delete the values contained in the array:

        >>> del ann.weights_input
        >>> ann.weights_input
        array([[0., 0., 0.],
               [0., 0., 0.]])

        Errors like wrong shapes (or unconvertible inputs) result in error
        messages:

        >>> ann.weights_input = numpy.eye(3)
        Traceback (most recent call last):
        ...
        ValueError: While trying to set the input weights of the artificial \
neural network `ann` of element `?`, the following error occurred: could not \
broadcast input array from shape (3,3) into shape (2,3)
        """,
    )

    @property
    def shape_weights_output(self) -> Tuple[int, int]:
        """The shape of the array containing the output weights.

        The first integer value is the number of neurons of the first hidden
        layer; the second integer value is the number of output nodes:

        >>> from hydpy import ANN
        >>> ann = ANN(None)
        >>> ann(nmb_inputs=2, nmb_neurons=(2, 1), nmb_outputs=3)
        >>> ann.shape_weights_output
        (1, 3)
        """
        return self.nmb_neurons[-1], self.nmb_outputs

    @property
    def nmb_weights_output(self) -> int:
        """The number of output weights.

        >>> from hydpy import ANN
        >>> ann = ANN(None)
        >>> ann(nmb_inputs=2, nmb_neurons=(2, 4), nmb_outputs=3)
        >>> ann.nmb_weights_output
        12
        """
        return self.nmb_neurons[-1] * self.nmb_outputs

    weights_output = _ANNArrayProperty[Optional[MatrixInput[float]], Matrix[float]](
        protected=__protectedproperties,
        doc="""The weights between all neurons of the last hidden layer and 
        the output nodes.

        See the documentation on properties |anntools.ANN.shape_weights_output|
        and |anntools.ANN.weights_input| for further information.
        """,
    )

    @property
    def shape_weights_hidden(self) -> Tuple[int, int, int]:
        """The shape of the array containing the activation of the hidden
        neurons.

        The first integer value is the number of connection between the
        hidden layers. The second integer value is the maximum number of
        neurons of all hidden layers feeding information into another
        hidden layer (all except the last one). The third integer
        value is the maximum number of the neurons of all hidden layers
        receiving information from another hidden layer (all except the
        first one):

        >>> from hydpy import ANN
        >>> ann = ANN(None)
        >>> ann(nmb_inputs=6, nmb_neurons=(4, 3, 2), nmb_outputs=6)
        >>> ann.shape_weights_hidden
        (2, 4, 3)
        >>> ann(nmb_inputs=6, nmb_neurons=(4,), nmb_outputs=6)
        >>> ann.shape_weights_hidden
        (0, 0, 0)
        """
        if self.nmb_layers > 1:
            nmb_neurons = self.nmb_neurons
            return (self.nmb_layers - 1, max(nmb_neurons[:-1]), max(nmb_neurons[1:]))
        return 0, 0, 0

    @property
    def nmb_weights_hidden(self) -> int:
        """The number of hidden weights.

        >>> from hydpy import ANN
        >>> ann = ANN(None)
        >>> ann(nmb_inputs=2, nmb_neurons=(4, 3, 2), nmb_outputs=3)
        >>> ann.nmb_weights_hidden
        18
        """
        nmb = 0
        for idx_layer in range(self.nmb_layers - 1):
            nmb += self.nmb_neurons[idx_layer] * self.nmb_neurons[idx_layer + 1]
        return nmb

    weights_hidden = _ANNArrayProperty(
        protected=__protectedproperties,
        doc="""The weights between the neurons of the different hidden layers.

        See the documentation on properties |anntools.ANN.shape_weights_hidden|
        and |anntools.ANN.weights_input| for further information.
        """,
    )

    @property
    def shape_intercepts_hidden(self) -> Tuple[int, int]:
        """The shape of the array containing the intercepts of neurons of
        the hidden layers.

        The first integer value is to the number of hidden layers;
        the second integer value is the maximum number of neurons of
        all hidden layers:

        >>> from hydpy import ANN
        >>> ann = ANN(None)
        >>> ann(nmb_inputs=6, nmb_neurons=(4, 3, 2), nmb_outputs=6)
        >>> ann.shape_intercepts_hidden
        (3, 4)
        """
        return self.nmb_layers, self.__max_nmb_neurons

    @property
    def nmb_intercepts_hidden(self) -> int:
        """The number of input intercepts."""
        return sum(self.nmb_neurons)

    intercepts_hidden = _ANNArrayProperty[Optional[MatrixInput[float]], Matrix[float]](
        protected=__protectedproperties,
        doc="""The intercepts of all neurons of the hidden layers.

        See the documentation on properties 
        |anntools.ANN.shape_intercepts_hidden| and 
        |anntools.ANN.weights_input| for further information.
        """,
    )

    @property
    def shape_intercepts_output(self) -> Tuple[int]:
        """The shape of the array containing the intercepts of neurons of
        the hidden layers.

        The only integer value is the number of output nodes:

        >>> from hydpy import ANN
        >>> ann = ANN(None)
        >>> ann(nmb_inputs=2, nmb_neurons=(2, 1), nmb_outputs=3)
        >>> ann.shape_intercepts_output
        (3,)
        """
        return (self.nmb_outputs,)

    @property
    def nmb_intercepts_output(self) -> int:
        """The number of output intercepts.

        >>> from hydpy import ANN
        >>> ann = ANN(None)
        >>> ann(nmb_inputs=2, nmb_neurons=(2, 1), nmb_outputs=3)
        >>> ann.nmb_intercepts_output
        3
        """
        return self.nmb_outputs

    intercepts_output = _ANNArrayProperty[Optional[VectorInput[float]], Vector[float]](
        protected=__protectedproperties,
        doc="""The intercepts of all output nodes.

        See the documentation on properties 
        |anntools.ANN.shape_intercepts_output| and 
        |anntools.ANN.weights_input| for further information.
        """,
    )

    @property
    def shape_activation(self) -> Tuple[int, int]:
        """The shape of the array defining the activation function for each
        neuron of the hidden layers.

        The first integer value is to the number of hidden layers;
        the second integer value is the maximum number of neurons of
        all hidden layers:

        >>> from hydpy import ANN
        >>> ann = ANN(None)
        >>> ann(nmb_inputs=6, nmb_neurons=(4, 3, 2), nmb_outputs=6)
        >>> ann.shape_activation
        (3, 4)
        """
        return self.nmb_layers, self.__max_nmb_neurons

    activation = _ANNArrayProperty[Optional[MatrixInput[int]], Matrix[int]](
        protected=__protectedproperties,
        doc="""Indices for selecting suitable activation functions for the
        neurons of the hidden layers.
        
        By default, |anntools.ANN| uses the logistic function for calculating 
        the activation of the neurons of the hidden layers and uses the 
        identity function for the output nodes.  However, property 
        |anntools.ANN.activation| allows defining other activation functions 
        for the hidden neurons individually.  So far, one can select the
        identity function and a "filter version" of the logistic function
        as alternatives -- others might follow. 
        
        Assume a neuron receives input :math:`i_1` and :math:`i_2` from 
        two nodes of the input layer or its upstream hidden layer.  We 
        weight these input values as usual:
        
            :math:`x_1 = c + w_1 \\cdot i_1 + w_2 \\cdot i_2`
        
        When selecting the identity function through setting the index value 
        "0", the activation of the considered neuron is:
            
            :math:`a_1 = x_1`
        
        Using the identity function is helpful for educational examples
        and for bypassing input through one layer without introducing
        nonlinearity.
        
        When selecting the logistic function through setting the index value 
        "1", the activation of the considered neuron is:
        
            :math:`a_1 = 1-\\frac{1}{1+exp(x_1)}`
        
        The logistic function is a standard function for constructing neural 
        networks.  It allows to approximate any relationship within a specific 
        range and accuracy, provided the neural network is large enough.
        
        When selecting the "filter version" of the logistic function through 
        setting the index value "2", the activation of the considered neuron 
        is:
        
            :math:`a_1 = 1-\\frac{1}{1+exp(x_1)} \\cdot i_1`
            
        "Filter version" means that our neuron now filters the input of the 
        single input node placed at the corresponding position of its layer.  
        This activation function helps force the output of a neural network 
        to be zero but never negative beyond a certain threshold.          
        
        Similar to the main documentation on class |anntools.ANN|, we define 
        a relatively complex network to show that both the "normal" and
        the derivative calculations work.  This time, we set the activation
        function explicitly.  "1" stands for the logistic function, which
        we first use for all hidden neurons:
        
        >>> from hydpy.auxs.anntools import ANN
        >>> from hydpy import round_
        >>> ann = ANN(None)
        >>> ann(nmb_inputs=2,
        ...     nmb_neurons=(2, 2),
        ...     nmb_outputs=2,
        ...     weights_input=[[0.2, -0.1],
        ...                    [-1.7, 0.6]],
        ...     weights_hidden=[[[-.5, 1.0],
        ...                      [0.4, 2.4]]],
        ...     weights_output=[[0.8, -0.9],
        ...                     [0.5, -0.4]],
        ...     intercepts_hidden=[[0.9, 0.0],
        ...                        [-0.4, -0.2]],
        ...     intercepts_output=[1.3, -2.0],
        ...     activation=[[1, 1],
        ...                 [1, 1]])    
        >>> ann.inputs = -0.1,  1.3
        >>> ann.calculate_values()
        >>> round_(ann.outputs)
        2.074427, -2.734692
        >>> for idx_input in range(2):
        ...     ann.calculate_derivatives(idx_input)
        ...     round_(ann.output_derivatives)
        -0.006199, 0.006571
        0.039804, -0.044169
        
        In the next example, we want to apply the identity function for the
        second neuron of the first hidden layer and the first neuron of the
        second hidden layer.  Therefore, we pass its index value "0" to the 
        corresponding |anntools.ANN.activation| entries:
        
        >>> ann.activation = [[1, 0], [0, 1]]
        >>> ann
        ann(
            nmb_inputs=2,
            nmb_neurons=(2, 2),
            nmb_outputs=2,
            weights_input=[[0.2, -0.1],
                           [-1.7, 0.6]],
            weights_hidden=[[[-0.5, 1.0],
                             [0.4, 2.4]]],
            weights_output=[[0.8, -0.9],
                            [0.5, -0.4]],
            intercepts_hidden=[[0.9, 0.0],
                               [-0.4, -0.2]],
            intercepts_output=[1.3, -2.0],
            activation=[[1, 0],
                        [0, 1]],
        )
        
        The agreement between the analytical and the numerical derivatives 
        gives us confidence everything works fine:
             
        >>> ann.calculate_values()
        >>> round_(ann.outputs)
        1.584373, -2.178468
        >>> for idx_input in range(2):
        ...     ann.calculate_derivatives(idx_input)
        ...     round_(ann.output_derivatives)
        -0.056898, 0.060219
        0.369807, -0.394801
        >>> d_input = 1e-8
        >>> for idx_input in range(2):
        ...     input_ = ann.inputs[idx_input]
        ...     ann.inputs[idx_input] = input_-d_input/2.0
        ...     ann.calculate_values()
        ...     values0 = ann.outputs.copy()
        ...     ann.inputs[idx_input] = input_+d_input/2.0
        ...     ann.calculate_values()
        ...     values1 = ann.outputs.copy()
        ...     ann.inputs[idx_input] = input_
        ...     round_((values1-values0)/d_input)
        -0.056898, 0.060219
        0.369807, -0.394801
        
        Finally, we perform the same check for the "filter version" of the
        logistic function:
        
        >>> ann.activation = [[1, 2], [2, 1]]
        >>> ann.calculate_values()
        >>> round_(ann.outputs)
        1.825606, -2.445682
        >>> for idx_input in range(2):
        ...     ann.calculate_derivatives(idx_input)
        ...     round_(ann.output_derivatives)
        0.009532, -0.011236
        -0.001715, 0.02872
        >>> d_input = 1e-8
        >>> for idx_input in range(2):
        ...     input_ = ann.inputs[idx_input]
        ...     ann.inputs[idx_input] = input_-d_input/2.0
        ...     ann.calculate_values()
        ...     values0 = ann.outputs.copy()
        ...     ann.inputs[idx_input] = input_+d_input/2.0
        ...     ann.calculate_values()
        ...     values1 = ann.outputs.copy()
        ...     ann.inputs[idx_input] = input_
        ...     round_((values1-values0)/d_input)
        0.009532, -0.011236
        -0.001715, 0.02872
        """,
    )

    @property
    def shape_inputs(self) -> Tuple[int]:
        """The shape of the array containing the input values.

        The only integer value is the number of input nodes:

        >>> from hydpy import ANN
        >>> ann = ANN(None)
        >>> ann(nmb_inputs=5, nmb_neurons=(2, 1), nmb_outputs=2)
        >>> ann.shape_inputs
        (5,)
        """
        return (self.nmb_inputs,)

    inputs = _ANNArrayProperty[Optional[VectorInput[float]], Vector[float]](
        protected=__protectedproperties,
        doc="""The values of the input nodes.

        See the documentation on properties |anntools.ANN.shape_inputs|
        and |anntools.ANN.weights_input| for further information.
        """,
    )

    @property
    def shape_outputs(self) -> Tuple[int]:
        """The shape of the array containing the output values.

        The only integer value is the number of output nodes:

        >>> from hydpy import ANN
        >>> ann = ANN(None)
        >>> ann(nmb_inputs=2, nmb_neurons=(2, 1), nmb_outputs=6)
        >>> ann.shape_outputs
        (6,)
        """
        return (self.nmb_outputs,)

    outputs = _ANNArrayProperty[Optional[VectorInput[float]], Vector[float]](
        protected=__protectedproperties,
        doc="""The values of the output nodes.

        See the documentation on properties |anntools.ANN.shape_outputs|
        and |anntools.ANN.weights_input| for further information.
        """,
    )

    @property
    def shape_output_derivatives(self) -> Tuple[int]:
        """The shape of the array containing the output derivatives.

        The only integer value is the number of output nodes:

        >>> from hydpy import ANN
        >>> ann = ANN(None)
        >>> ann(nmb_inputs=2, nmb_neurons=(2, 1), nmb_outputs=6)
        >>> ann.shape_output_derivatives
        (6,)
        """
        return (self.nmb_outputs,)

    output_derivatives = _ANNArrayProperty[Optional[Vector[float]], Vector[float]](
        protected=__protectedproperties,
        doc="""The derivatives of the output nodes.

        See the documentation on properties 
        |anntools.ANN.shape_output_derivatives| and 
        |anntools.ANN.weights_input| for further information.
        """,
    )

    def _get_nmb_layers(self) -> int:
        """The number of hidden layers.

        >>> from hydpy import ANN
        >>> ann = ANN(None)
        >>> ann(nmb_inputs=2, nmb_neurons=(2, 1), nmb_outputs=3)
        >>> ann.nmb_layers
        2
        """
        return self._cann.nmb_layers

    nmb_layers = propertytools.DependentProperty[int, int](
        protected=__protectedproperties,
        fget=_get_nmb_layers,
    )

    def _get_shape_neurons(self) -> Tuple[int, int]:
        """The shape of the array containing the activities of the neurons
        of the hidden layers.

        The first integer value is the number of hidden layers; the
        second integer value is the maximum number of neurons of all
        hidden layers:

        >>> from hydpy import ANN
        >>> ann = ANN(None)
        >>> ann(nmb_inputs=2, nmb_neurons=(4, 3, 2), nmb_outputs=6)
        >>> ann.shape_neurons
        (3, 4)
        """
        return self.nmb_layers, self.__max_nmb_neurons

    shape_neurons = propertytools.DependentProperty[Tuple[int, int], Tuple[int, int]](
        protected=__protectedproperties,
        fget=_get_shape_neurons,
    )

    neurons = _ANNArrayProperty[Optional[MatrixInput[float]], Matrix[float]](
        protected=__protectedproperties,
        doc="""The derivatives of the activation of the neurons of the 
        hidden layers.

        See the documentation on properties |anntools.ANN.shape_neurons|
        and |anntools.ANN.weights_input| for further information.
        """,
    )

    def _get_shape_neuron_derivatives(self) -> Tuple[int, int]:
        """The shape of the array containing the derivatives of the activities
        of the neurons of the hidden layers.

        The first integer value is the number of hidden layers; the
        second integer value is the maximum number of neurons of all
        hidden layers:

        >>> from hydpy import ANN
        >>> ann = ANN(None)
        >>> ann(nmb_inputs=2, nmb_neurons=(4, 3, 2), nmb_outputs=6)
        >>> ann.shape_neuron_derivatives
        (3, 4)
        """
        return self.nmb_layers, self.__max_nmb_neurons

    shape_neuron_derivatives = propertytools.DependentProperty[
        Tuple[int, int], Tuple[int, int]
    ](
        protected=__protectedproperties,
        fget=_get_shape_neuron_derivatives,
    )

    neuron_derivatives = _ANNArrayProperty[Optional[MatrixInput[float]], Matrix[float]](
        protected=__protectedproperties,
        doc="""The derivatives of the activation of the neurons of the 
        hidden layers.

        See the documentation on properties 
        |anntools.ANN.shape_neuron_derivatives| and 
        |anntools.ANN.weights_input| for further information.
        """,
    )

    def calculate_values(self) -> None:
        """Calculate the network output values based on the input values
        defined previously.

        For more information, see the documentation on class |anntools.ANN|.
        """
        self._cann.calculate_values()

    def calculate_derivatives(self, idx_input: int) -> None:
        """Calculate the derivatives of the network output values with
        respect to the input value of the given index.

        For more information, see the documentation on class |anntools.ANN|.
        """
        self._cann.calculate_derivatives(idx_input)

    @property
    def nmb_weights(self) -> int:
        """The number of all input, inner, and output weights.

        >>> from hydpy import ANN
        >>> ann = ANN(None)
        >>> ann(nmb_inputs=1, nmb_neurons=(2, 3), nmb_outputs=4)
        >>> ann.nmb_weights
        20
        """
        return (
            self.nmb_weights_input + self.nmb_weights_hidden + self.nmb_weights_output
        )

    @property
    def nmb_intercepts(self) -> int:
        """The number of all inner and output intercepts.

        >>> from hydpy import ANN
        >>> ann = ANN(None)
        >>> ann(nmb_inputs=1, nmb_neurons=(2, 3), nmb_outputs=4)
        >>> ann.nmb_intercepts
        9
        """
        return self.nmb_intercepts_hidden + self.nmb_intercepts_output

    @property
    def nmb_parameters(self) -> int:
        """The sum of |anntools.ANN.nmb_weights| and
        |anntools.ANN.nmb_intercepts|.

        >>> from hydpy import ANN
        >>> ann = ANN(None)
        >>> ann(nmb_inputs=1, nmb_neurons=(2, 3), nmb_outputs=4)
        >>> ann.nmb_parameters
        29
        """
        return self.nmb_weights + self.nmb_intercepts

    def verify(self) -> None:
        """Raise a |RuntimeError| if the network's shape is not defined
        completely.

        >>> from hydpy import ANN
        >>> ANN(None).verify()
        Traceback (most recent call last):
        ...
        RuntimeError: The shape of the the artificial neural network \
parameter `ann` of element `?` has not been defined so far.
        """
        if not self.__protectedproperties.allready(self):
            raise RuntimeError(
                f"The shape of the the artificial neural network parameter "
                f"{objecttools.elementphrase(self)} has not been defined so far."
            )

    def assignrepr(self, prefix, indent=0) -> str:
        """Return a string representation of the actual |anntools.ANN| object
        prefixed with the given string."""
        blanks = (indent + 4) * " "
        lines = [f"{prefix}{self.name}("]
        if self.nmb_inputs != 1:
            lines.append(f"{blanks}nmb_inputs={self.nmb_inputs},")
        if self.nmb_neurons != (1,):
            lines.append(f"{blanks}nmb_neurons={self.nmb_neurons},")
        if self.nmb_outputs != 1:
            lines.append(f"{blanks}nmb_outputs={self.nmb_outputs},")
        lines.append(
            objecttools.assignrepr_list2(self.weights_input, f"{blanks}weights_input=")
            + ","
        )
        if self.nmb_layers > 1:
            lines.append(
                objecttools.assignrepr_list3(
                    self.weights_hidden, f"{blanks}weights_hidden="
                )
                + ","
            )
        lines.append(
            objecttools.assignrepr_list2(
                self.weights_output, f"{blanks}weights_output="
            )
            + ","
        )
        lines.append(
            objecttools.assignrepr_list2(
                self.intercepts_hidden, f"{blanks}intercepts_hidden="
            )
            + ","
        )
        lines.append(
            objecttools.assignrepr_list(
                self.intercepts_output, f"{blanks}intercepts_output="
            )
            + ","
        )
        if numpy.any(self.activation != 1):
            lines.append(
                objecttools.assignrepr_list2(self.activation, f"{blanks}activation=")
                + ","
            )
        lines.append(f'{indent*" "})')
        return "\n".join(lines)

    def __repr__(self) -> str:
        return self.assignrepr(prefix="")

    def plot(
        self,
        xmin: float,
        xmax: float,
        idx_input: int = 0,
        idx_output: int = 0,
        points: int = 100,
        **kwargs: Optional[Union[float, str]],
    ) -> None:
        """Plot the relationship between a particular input (`idx_input`)
        and a particular output (`idx_output`) variable described by the
        actual |anntools.ANN| object.

        Define the lower and the upper bound of the x-axis via arguments
        `xmin` and `xmax`.  Modify the number of plotted points via
        argument `points`.  Pass additional `matplotlib` plotting arguments
        as keyword arguments.
        """
        # pylint: disable=unsubscriptable-object
        # pylint: disable=unsupported-assignment-operation
        # pylint is wrong about "self.inputs"
        xs_ = numpy.linspace(xmin, xmax, points)
        ys_ = numpy.zeros(xs_.shape)
        for idx, x__ in enumerate(xs_):
            self.inputs[idx_input] = x__
            self.calculate_values()
            ys_[idx] = self.outputs[idx_output]
        pyplot.plot(xs_, ys_, **kwargs)
        self._update_labels()

    def __hash__(self) -> int:
        return id(self)

    def __eq__(self, other: object) -> bool:
        def _equal_array(
            x: Union[Vector[float], Matrix[int], Matrix[float]],
            y: Union[Vector[float], Matrix[int], Matrix[float]],
        ) -> bool:
            idxs = ~(numpy.isnan(x) * numpy.isnan(y))
            return bool(numpy.all(x[idxs] == y[idxs]))

        if id(self) == id(other):
            return True
        if isinstance(other, ANN):
            return (
                self.shape_inputs == other.shape_inputs
                and self.shape_neurons == other.shape_neurons
                and self.shape_outputs == other.shape_outputs
                and _equal_array(self.weights_input[:], other.weights_input[:])
                and _equal_array(self.weights_hidden, other.weights_hidden)
                and _equal_array(self.weights_output, other.weights_output)
                and _equal_array(self.intercepts_hidden, other.intercepts_hidden)
                and _equal_array(self.intercepts_output, other.intercepts_output)
                and _equal_array(self.activation, other.activation)
            )
        return NotImplemented


def ann(
    *,
    nmb_inputs: int = 1,
    nmb_neurons: Tuple[int, ...] = (1,),
    nmb_outputs: int = 1,
    weights_input: Optional[MatrixInput[float]] = None,
    weights_output: Optional[MatrixInput[float]] = None,
    weights_hidden=None,
    intercepts_hidden: Optional[MatrixInput[float]] = None,
    intercepts_output: Optional[VectorInput[float]] = None,
    activation: Optional[MatrixInput[int]] = None,
) -> ANN:
    """Return a new stand-alone |anntools.ANN| object with the given parameter
    values.

    The purpose of this function is to allow for string representations of
    parameters containing multiple |anntools.ANN| instances.

    When passing no arguments, the default values of class |anntools.ANN|
    apply:

    >>> from hydpy import ann
    >>> ann1 = ann()
    >>> ann1
    ann(
        weights_input=[[0.0]],
        weights_output=[[0.0]],
        intercepts_hidden=[[0.0]],
        intercepts_output=[0.0],
    )

    Of course, you can change any parameter value:

    >>> ann2 = ann(nmb_inputs=1, nmb_neurons=(1,), nmb_outputs=1,
    ...            weights_input=4.0, weights_output=3.0,
    ...            intercepts_hidden=-16.0, intercepts_output=-1.0)
    >>> ann2
    ann(
        weights_input=[[4.0]],
        weights_output=[[3.0]],
        intercepts_hidden=[[-16.0]],
        intercepts_output=[-1.0],
    )

    The following line clarifies that we initialised two independent
    |anntools.ANN| objects (instead of changing the values of an existing
    |anntools.ANN| object vai its `call` method):

    >>> ann1 is ann2
    False
    """
    new_ann = ANN(None)
    new_ann(
        nmb_inputs=nmb_inputs,
        nmb_neurons=nmb_neurons,
        nmb_outputs=nmb_outputs,
        weights_input=weights_input,
        weights_output=weights_output,
        weights_hidden=weights_hidden,
        intercepts_hidden=intercepts_hidden,
        intercepts_output=intercepts_output,
        activation=activation,
    )
    return new_ann


class SeasonalANN(BaseANN):
    """Handles relationships described by artificial neural networks that
    vary within an annual cycle.

    Class |anntools.SeasonalANN| is an alternative implementation of class
    |SeasonalParameter| specifically designed for handling multiple
    |anntools.ANN| objects that are valid for different times of the year,
    described by |TOY| objects.  The total output of a |anntools.SeasonalANN|
    object is a weighted mean of the output of one or two "normal" neural
    networks.  Property |anntools.SeasonalANN.ratios| provides the weights
    for the different times of the year.

    To explain this in more detail, we modify an example of the documentation
    on class.  let us define a |anntools.SeasonalANN| object that contains
    three "normal" networks for January, 1, March, 1, and July, 1,
    respectively:

    >>> from hydpy import ann, pub, SeasonalANN
    >>> pub.options.reprdigits = 6
    >>> pub.timegrids = "2000-01-01", "2000-10-01", "1d"
    >>> seasonalann = SeasonalANN(None)
    >>> seasonalann(
    ...     _1_1_12=ann(nmb_inputs=1, nmb_neurons=(1,), nmb_outputs=1,
    ...                 weights_input=0.0, weights_output=0.0,
    ...                 intercepts_hidden=0.0, intercepts_output=1.0),
    ...     _7_1_12=ann(nmb_inputs=1, nmb_neurons=(1,), nmb_outputs=1,
    ...                 weights_input=4.0, weights_output=3.0,
    ...                 intercepts_hidden=-16.0, intercepts_output=-1.0),
    ...     _3_1_12=ann(nmb_inputs=1, nmb_neurons=(1,), nmb_outputs=1,
    ...                 weights_input=0.0, weights_output=0.0,
    ...                 intercepts_hidden=0.0, intercepts_output=-1.0))

    The confusing time order in the initialization call above does not pose a
    problem, as class |anntools.SeasonalANN| performs time sorting internally:

    >>> seasonalann
    seasonalann(
        toy_1_1_12_0_0=ann(
            weights_input=[[0.0]],
            weights_output=[[0.0]],
            intercepts_hidden=[[0.0]],
            intercepts_output=[1.0],
        ),
        toy_3_1_12_0_0=ann(
            weights_input=[[0.0]],
            weights_output=[[0.0]],
            intercepts_hidden=[[0.0]],
            intercepts_output=[-1.0],
        ),
        toy_7_1_12_0_0=ann(
            weights_input=[[4.0]],
            weights_output=[[3.0]],
            intercepts_hidden=[[-16.0]],
            intercepts_output=[-1.0],
        ),
    )

    One can easily plot the resulting graphs of all networks:

    >>> seasonalann.plot(0.0, 8.0)

    You can use the `pyplot` API of `matplotlib` to modify the figure
    or to save it to disk (or print it to the screen, in case the
    interactive mode of `matplotlib` is disabled):

    >>> from hydpy.core.testtools import save_autofig
    >>> save_autofig("SeasonalANN_plot.png")

    .. image:: SeasonalANN_plot.png

    The property |anntools.SeasonalANN.shape| does reflect the number of
    required weighting ratios for each time of year (in this example
    366 days per year) and each neural network (in this example three):

    >>> seasonalann.shape
    (366, 3)

    For safety reasons, |anntools.SeasonalANN.shape| should normally not
    be changed manually:

    >>> seasonalann.shape = (366, 4)
    Traceback (most recent call last):
    ...
    AttributeError: can't set attribute

    The following interactive plot shows the |anntools.SeasonalANN.ratios|
    used for weighting(note the missing values for October, November, and
    December, being not relevant for the initialisation period):

    .. testsetup::

        >>> from bokeh import plotting, models, palettes
        >>> from hydpy import docs
        >>> import os
        >>> plotting.output_file(os.path.join(
        ...     docs.__path__[0], "html_", "anntools.SeasonalANN.ratios.html"))
        >>> hover = models.HoverTool(tooltips=[
        ...     ("(x,y)", "($x, $y)")])
        >>> plot = plotting.figure(toolbar_location="above",
        ...                        plot_width=500, plot_height=300)
        >>> plot.tools.append(hover)
        >>> legend_entries = []
        >>> for idx, (toy, color) in enumerate(
        ...         zip(seasonalann.toys, palettes.Dark2_5)):
        ...     line = plot.line(range(366), seasonalann.ratios[:, idx],
        ...                      alpha=0.8, muted_alpha=0.2, color=color)
        ...     line.muted = True
        ...     legend_entries.append((str(toy), [line]))
        >>> legend = models.Legend(items=legend_entries,
        ...                        location=(10, 0),
        ...                        click_policy="mute")
        >>> plot.add_layout(legend, "right")
        >>> label_dict = {0: "Jan 1",
        ...               60: "Mar 1",
        ...               182: "Jul 1"}
        >>> plot.xaxis.ticker =  sorted(label_dict.keys())
        >>> plot.xaxis.formatter = models.FuncTickFormatter(
        ...     code=f"var labels = {label_dict}; return labels[tick];")
        >>> dummy = plotting.save(plot)

    .. raw:: html

        <iframe
            src="anntools.SeasonalANN.ratios.html"
            width="100%"
            height="300px"
            frameborder=0
        ></iframe>

    For example, on July, 1 (which is the 183rd day of a leap year),
    only the output of the third network is relevant:

    >>> from hydpy import print_values
    >>> print_values(seasonalann.ratios[182])
    0.0, 0.0, 1.0

    On Juni, 30, and July, 2, also the second and the first neural network
    are relevant, respectively:

    >>> print_values(seasonalann.ratios[181])
    0.0, 0.008197, 0.991803
    >>> print_values(seasonalann.ratios[183])
    0.005435, 0.0, 0.994565

    Inserting data, processing this data, and fetching the output works
    as explained for class |anntools.ANN|, except that you must additionally
    pass the index of the actual time of year.  Passing the index value
    `182` activates the third network only, being configured as the one
    exemplifying class |anntools.ANN|:

    >>> from hydpy import round_
    >>> for input_ in range(9):
    ...     seasonalann.inputs[0] = input_
    ...     seasonalann.calculate_values(182)
    ...     round_([input_, seasonalann.outputs[0]])
    0, -1.0
    1, -0.999982
    2, -0.998994
    3, -0.946041
    4, 0.5
    5, 1.946041
    6, 1.998994
    7, 1.999982
    8, 2.0

    To see that the final output values are actually the weighted mean
    of the output values of the single neural networks, we repeat the
    above example for January, 13, where the first and the second neural
    network have ratios of 0.8 and 0.2 respectively:

    >>> print_values(seasonalann.ratios[12])
    0.8, 0.2, 0.0

    For both networks, all parameters except the output intercepts are
    zero.  Hence, the calculated output is independent of the given input.
    The output of the first network (1.0) dominates the output of the
    second network (-1.0):

    >>> from hydpy import round_
    >>> for input_ in range(9):
    ...     seasonalann.inputs[0] = input_
    ...     seasonalann.calculate_values(12)
    ...     round_([input_, seasonalann.outputs[0]])
    0, 0.6
    1, 0.6
    2, 0.6
    3, 0.6
    4, 0.6
    5, 0.6
    6, 0.6
    7, 0.6
    8, 0.6

    It is of great importance that all contained neural networks are
    consistent.  Hence class |anntools.SeasonalANN| performs some
    related checks:

    >>> seasonalann = SeasonalANN(None)
    >>> seasonalann.calculate_values(0)
    Traceback (most recent call last):
    ...
    RuntimeError: The seasonal neural network collection `seasonalann` \
of element `?` has not been properly prepared so far.

    >>> seasonalann(1)
    Traceback (most recent call last):
    ...
    TypeError: Type `int` is not (a subclass of) type `ANN`.

    >>> seasonalann(
    ...     _13_1_12=ann(nmb_inputs=2, nmb_neurons=(1,), nmb_outputs=1,
    ...                  weights_input=0.0, weights_output=0.0,
    ...                  intercepts_hidden=0.0, intercepts_output=1.0))
    Traceback (most recent call last):
    ...
    ValueError: While trying to add a season specific neural network to \
parameter `seasonalann` of element `?`, the following error occurred: \
While trying to initialise a TOY object based on argument value `_13_1_12` \
of type `str`, the following error occurred: While trying to retrieve \
the month, the following error occurred: The value of property `month` \
of TOY (time of year) objects must lie within the range `(1, 12)`, \
but the given value is `13`.

    >>> seasonalann(
    ...     ann(nmb_inputs=2, nmb_neurons=(1,), nmb_outputs=1,
    ...         weights_input=0.0, weights_output=0.0,
    ...         intercepts_hidden=0.0, intercepts_output=1.0))
    >>> seasonalann
    seasonalann(
        ann(
            nmb_inputs=2,
            weights_input=[[0.0],
                           [0.0]],
            weights_output=[[0.0]],
            intercepts_hidden=[[0.0]],
            intercepts_output=[1.0],
        )
    )

    >>> seasonalann(
    ...     ann(nmb_inputs=2, nmb_neurons=(1,), nmb_outputs=1,
    ...         weights_input=0.0, weights_output=0.0,
    ...         intercepts_hidden=0.0, intercepts_output=1.0),
    ...     _7_1_12=ann(nmb_inputs=1, nmb_neurons=(1,), nmb_outputs=1,
    ...                 weights_input=4.0, weights_output=3.0,
    ...                 intercepts_hidden=-16.0, intercepts_output=-1.0),
    ...     _3_1_12=ann(nmb_inputs=1, nmb_neurons=(1,), nmb_outputs=1,
    ...                 weights_input=0.0, weights_output=0.0,
    ...                 intercepts_hidden=0.0, intercepts_output=-1.0))
    Traceback (most recent call last):
    ...
    ValueError: Type `SeasonalANN` accepts either a single positional \
argument or an arbitrary number of keyword arguments, but for the \
corresponding parameter of element `?` 1 positional and 2 keyword \
arguments have been given.

    >>> seasonalann(
    ...     _1_1_12=ann(nmb_inputs=2, nmb_neurons=(1,), nmb_outputs=1,
    ...                 weights_input=0.0, weights_output=0.0,
    ...                 intercepts_hidden=0.0, intercepts_output=1.0),
    ...     _7_1_12=ann(nmb_inputs=1, nmb_neurons=(1,), nmb_outputs=1,
    ...                 weights_input=4.0, weights_output=3.0,
    ...                 intercepts_hidden=-16.0, intercepts_output=-1.0),
    ...     _3_1_12=ann(nmb_inputs=1, nmb_neurons=(1,), nmb_outputs=1,
    ...                 weights_input=0.0, weights_output=0.0,
    ...                 intercepts_hidden=0.0, intercepts_output=-1.0))
    Traceback (most recent call last):
    ...
    RuntimeError: The number of input and output values of all neural \
networks contained by a seasonal neural network collection must be \
identical and be known by the containing object.  But the seasonal \
neural network collection `seasonalann` of element `?` assumes `2` input \
and `1` output values, while the network corresponding to the time of \
year `toy_3_1_12_0_0` requires `1` input and `1` output values.

    For safety, each failure results in a total loss of the previously
    defined networks:

    >>> seasonalann
    seasonalann()

    Alternatively, neural networks can be added individually via
    attribute access:

    >>> jan = ann(nmb_inputs=1, nmb_neurons=(1,), nmb_outputs=1,
    ...           weights_input=0.0, weights_output=0.0,
    ...           intercepts_hidden=0.0, intercepts_output=1.0)
    >>> seasonalann.toy_1_1_12 = jan

    If you set an attribute, everything updates automatically, e.g.:

    >>> round_(seasonalann.ratios[0])
    1.0

    The mentioned safety checks do also apply when adding networks
    via attribute access, e.g.:

    >>> seasonalann.toy_7_1_12 = ann(nmb_inputs=2,
    ...                              nmb_neurons=(1,),
    ...                              nmb_outputs=1,
    ...                              weights_input=0.0,
    ...                              weights_output=0.0,
    ...                              intercepts_hidden=0.0,
    ...                              intercepts_output=1.0)
    Traceback (most recent call last):
    ...
    RuntimeError: While trying to assign a new neural network to the \
seasonal neural network collection `seasonalann` of element `?` based \
on name `toy_7_1_12`, the following error occurred: \
The number of input and output values of all neural networks contained \
by a seasonal neural network collection must be identical and be known \
by the containing object.  But the seasonal neural network collection \
`seasonalann` of element `?` assumes `1` input and `1` output values, \
while the network corresponding to the time of year `toy_7_1_12_0_0` \
requires `2` input and `1` output values.

    Besides setting new networks, getting and deleting them also works:

    >>> seasonalann.toy_1_1_12 = jan
    >>> seasonalann.toy_1_1_12
    ann(
        weights_input=[[0.0]],
        weights_output=[[0.0]],
        intercepts_hidden=[[0.0]],
        intercepts_output=[1.0],
    )
    >>> del seasonalann.toy_1_1_12

    These are the error messages related to attribute access problems:

    >>> seasonalann.toy_1_1_12
    Traceback (most recent call last):
    ...
    AttributeError: While trying to look up for a neural network handled \
by the seasonal neural network collection `seasonalann` of element `?` \
based on name `toy_1_1_12`, the following error occurred: No neural network \
is registered under a TOY object named `toy_1_1_12_0_0`.

    >>> del seasonalann.toy_1_1_12
    Traceback (most recent call last):
    ...
    AttributeError: While trying to remove a new neural network from the \
seasonal neural network collection `seasonalann` of element `?` based on \
name `toy_1_1_12`, the following error occurred: No neural network is \
registered under a TOY object named `toy_1_1_12_0_0`.

    >>> seasonalann.toy_1_1_12 = 1
    Traceback (most recent call last):
    ...
    TypeError: While trying to assign a new neural network to the seasonal \
neural network collection `seasonalann` of element `?` based on name \
`toy_1_1_12`, the following error occurred: Value `1` of type `int` has \
been given, but a value of type `ANN` is required.

    Setting and deleting "normal" attributes is supported:

    >>> seasonalann.temp = 999
    >>> seasonalann.temp
    999
    >>> del seasonalann.temp
    >>> seasonalann.temp
    Traceback (most recent call last):
    ...
    AttributeError: 'SeasonalANN' object has no attribute 'temp'
    """

    NDIM = 0
    TYPE = "annutils.SeasonalANN"
    TIME = None
    SPAN = (None, None)

    subvars: parametertools.SubParameters
    subpars: parametertools.SubParameters
    fastaccess: parametertools.FastAccessParameter
    __sann: Optional[annutils.SeasonalANN]

    def __init__(self, subvars: parametertools.SubParameters):
        self.subvars = subvars
        self.subpars = subvars
        self.fastaccess = parametertools.FastAccessParameter()
        self._toy2ann: Dict[timetools.TOY, ANN] = {}
        self.__sann = None
        self._do_refresh = True

    @overload
    def __call__(self, __ann: ANN) -> None:
        ...

    @overload
    def __call__(self, **anns: ANN) -> None:
        ...

    def __call__(self, *ann_: ANN, **anns: ANN) -> None:
        self._toy2ann.clear()
        self._do_refresh = False
        try:
            if (len(ann_) > 1) or (ann_ and anns):
                raise ValueError(
                    f"Type `{type(self).__name__}` accepts either a single "
                    f"positional argument or an arbitrary number of keyword "
                    f"arguments, but for the corresponding parameter of element "
                    f"`{objecttools.devicename(self)}` {len(ann_)} positional "
                    f"and {len(anns)} keyword arguments have been given."
                )
            if ann_:
                anns["_1"] = ann_[0]
            for (toystr, value) in anns.items():
                if not isinstance(value, ANN):
                    raise TypeError(
                        f"Type `{type(value).__name__}` is not "
                        f"(a subclass of) type `ANN`."
                    )
                try:
                    setattr(self, str(timetools.TOY(toystr)), value)
                except BaseException:
                    objecttools.augment_excmessage(
                        f"While trying to add a season specific neural "
                        f"network to parameter `{self.name}` of element "
                        f"`{objecttools.devicename(self)}`"
                    )
        except BaseException as exc:
            self._toy2ann.clear()
            raise exc
        finally:
            self._do_refresh = True
            self.refresh()

    def __hydpy__connect_variable2subgroup__(self) -> None:
        """Connect the actual |anntools.SeasonalANN| object with the given
        |SubParameters| object."""
        self.fastaccess = self.subpars.fastaccess
        setattr(self.fastaccess, self.name, self.__sann)

    def refresh(self) -> None:
        """Prepare the actual |anntools.SeasonalANN| object for calculations.

        Class |anntools.SeasonalANN| stores its |anntools.ANN| objects by
        reference.  Therefore, despite all automated refreshings (explained
        in the general documentation on class |anntools.SeasonalANN|), it
        is still possible to destroy the inner consistency of a
        |anntools.SeasonalANN| instance:

        >>> from hydpy import SeasonalANN, ann
        >>> seasonalann = SeasonalANN(None)
        >>> seasonalann.simulationstep = "1d"
        >>> jan = ann(nmb_inputs=1, nmb_neurons=(1,), nmb_outputs=1,
        ...           weights_input=0.0, weights_output=0.0,
        ...           intercepts_hidden=0.0, intercepts_output=1.0)
        >>> seasonalann(_1_1_12=jan)
        >>> jan.nmb_inputs, jan.nmb_outputs = 2, 3
        >>> jan.nmb_inputs, jan.nmb_outputs
        (2, 3)
        >>> seasonalann.nmb_inputs, seasonalann.nmb_outputs
        (1, 1)

        Due to the C level implementation of the mathematical core of
        both |anntools.ANN| and |anntools.SeasonalANN| in module |annutils|,
        such an inconsistency might result in a program crash without any
        informative error message.  Whenever you are think some inconsistency
        might have crept in and you want to repair it, call method
        |anntools.SeasonalANN.refresh| explicitly:

        >>> seasonalann.refresh()
        >>> jan.nmb_inputs, jan.nmb_outputs
        (2, 3)
        >>> seasonalann.nmb_inputs, seasonalann.nmb_outputs
        (2, 3)
        """
        # pylint: disable=unsupported-assignment-operation
        if self._do_refresh:
            if self.anns:
                self.__sann = annutils.SeasonalANN(self.anns)
                setattr(self.fastaccess, self.name, self._sann)
                self._prepare_shape()
                if self._sann.nmb_anns > 1:
                    self._interp()
                else:
                    self._sann.ratios[:, 0] = 1.0
                self.verify()
            else:
                self.__sann = None

    def verify(self) -> None:
        """Raise a |RuntimeError| and remove all handled neural networks,
        if they are defined inconsistently.

        Class |anntools.SeasonalANN| stores its |anntools.ANN| objects by
        reference.  Therefore, despite all automated refreshings (explained
        in the general documentation on class |anntools.SeasonalANN|), it
        is still possible to destroy the inner consistency of a
        |anntools.SeasonalANN| instance:

        >>> from hydpy import SeasonalANN, ann
        >>> seasonalann = SeasonalANN(None)
        >>> seasonalann.simulationstep = "1d"
        >>> jan = ann(nmb_inputs=1, nmb_neurons=(1,), nmb_outputs=1,
        ...           weights_input=0.0, weights_output=0.0,
        ...           intercepts_hidden=0.0, intercepts_output=1.0)
        >>> seasonalann(_1_1_12=jan)
        >>> jan.nmb_inputs, jan.nmb_outputs = 2, 3
        >>> jan.nmb_inputs, jan.nmb_outputs
        (2, 3)
        >>> seasonalann.nmb_inputs, seasonalann.nmb_outputs
        (1, 1)

        Due to the C level implementation of the mathematical core of both
        |anntools.ANN| and |anntools.SeasonalANN| in module |annutils|,
        such an inconsistency might result in a program crash without any
        informative error message. Whenever you think some inconsistency
        might have crept in and you want to find out if your suspicion is
        right, call method |anntools.SeasonalANN.verify| explicitly.

        >>> seasonalann.verify()
        Traceback (most recent call last):
        ...
        RuntimeError: The number of input and output values of all neural \
networks contained by a seasonal neural network collection must be \
identical and be known by the containing object.  But the seasonal \
neural network collection `seasonalann` of element `?` assumes `1` input \
and `1` output values, while the network corresponding to the time of \
year `toy_1_1_12_0_0` requires `2` input and `3` output values.

        >>> seasonalann
        seasonalann()

        >>> seasonalann.verify()
        Traceback (most recent call last):
        ...
        RuntimeError: Seasonal artificial neural network collections need \
to handle at least one "normal" single neural network, but for the seasonal \
neural network `seasonalann` of element `?` none has been defined so far.
        """
        if not self.anns:
            self._toy2ann.clear()
            raise RuntimeError(
                f"Seasonal artificial neural network collections need "
                f'to handle at least one "normal" single neural network, '
                f"but for the seasonal neural network `{self.name}` of element "
                f"`{objecttools.devicename(self)}` none has been defined so far."
            )
        for toy, ann_ in self:
            ann_.verify()
            if (self.nmb_inputs != ann_.nmb_inputs) or (
                self.nmb_outputs != ann_.nmb_outputs
            ):
                self._toy2ann.clear()
                raise RuntimeError(
                    f"The number of input and output values of all neural networks "
                    f"contained by a seasonal neural network collection must be "
                    f"identical and be known by the containing object.  But the "
                    f"seasonal neural network collection `{self.name}` of element "
                    f"`{objecttools.devicename(self)}` assumes `{self.nmb_inputs}` "
                    f"input and `{self.nmb_outputs}` output values, while the "
                    f"network corresponding to the time of year `{toy}` requires "
                    f"`{ann_.nmb_inputs}` input and `{ann_.nmb_outputs}` output values."
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
    def shape(self) -> Tuple[int, ...]:
        """The shape of array |anntools.SeasonalANN.ratios|."""
        return tuple(int(sub) for sub in self.ratios.shape)

    def _prepare_shape(self) -> None:
        """Private on purpose."""
        nmb_weights = timetools.Period("366d") / hydpy.pub.options.simulationstep
        nmb_weights = int(numpy.ceil(round(nmb_weights, 10)))
        shape = (nmb_weights, self._sann.nmb_anns)
        getattr(self.fastaccess, self.name).ratios = numpy.zeros(shape, dtype=float)

    @property
    def toys(self) -> Tuple[timetools.TOY, ...]:
        """A sorted |tuple| of all contained |TOY| objects."""
        return tuple(toy for (toy, _) in self)

    @property
    def anns(self) -> Tuple[ANN, ...]:
        """A sorted |tuple| of all contained |anntools.ANN| objects."""
        return tuple(ann_ for (_, ann_) in self)

    @property
    def ratios(self) -> numpy.ndarray:
        """The ratios for weighting the single neural network outputs."""
        return numpy.asarray(self._sann.ratios)

    @property
    def _sann(self) -> annutils.SeasonalANN:
        sann = self.__sann
        if sann:
            return sann
        raise RuntimeError(
            f"The seasonal neural network collection `{self.name}` of element "
            f"`{objecttools.devicename(self)}` has not been properly prepared so far."
        )

    @property
    def nmb_inputs(self) -> int:
        """The number of input values of all neural networks."""
        return self._sann.nmb_inputs

    @property
    def inputs(self) -> numpy.ndarray:
        """The general input data for all neural networks."""
        return numpy.asarray(self._sann.inputs)

    @property
    def nmb_outputs(self) -> int:
        """The number of output values of all neural networks."""
        return self._sann.nmb_outputs

    @property
    def outputs(self) -> numpy.ndarray:
        """The weighted output of the individual neural networks."""
        return numpy.asarray(self._sann.outputs)

    def calculate_values(self, idx_toy: int) -> None:
        """Calculate the network output values based on the input values
        defined previously for the given index referencing the actual
        time of year."""
        self._sann.calculate_values(idx_toy)

    def plot(
        self,
        xmin: float,
        xmax: float,
        idx_input: int = 0,
        idx_output: int = 0,
        points: int = 100,
        **kwargs: Optional[Union[float, str]],
    ) -> None:
        """Call method |anntools.ANN.plot| of all |anntools.ANN| objects
        handled by the actual |anntools.SeasonalANN| object.
        """
        for toy, ann_ in self:
            ann_.plot(
                xmin,
                xmax,
                idx_input=idx_input,
                idx_output=idx_output,
                points=points,
                label=str(toy),
                **kwargs,
            )
        pyplot.legend()
        self._update_labels()

    def __getattr__(self, name: str) -> ANN:
        if name.startswith("toy_"):
            try:
                try:
                    return self._toy2ann[timetools.TOY(name)]
                except KeyError:
                    raise AttributeError(
                        f"No neural network is registered under a "
                        f"TOY object named `{timetools.TOY(name)}`."
                    ) from None
            except BaseException:
                objecttools.augment_excmessage(
                    f"While trying to look up for a neural network handled "
                    f"by the seasonal neural network collection `{self.name}` "
                    f"of element `{objecttools.devicename(self)}` based on "
                    f"name `{name}`"
                )
        else:
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
            )

    def __setattr__(self, name: str, value: object) -> None:
        if name.startswith("toy_"):
            try:
                if not isinstance(value, ANN):
                    raise TypeError(
                        f"{objecttools.value_of_type(value).capitalize()} has been "
                        f"given, but a value of type `ANN` is required."
                    )
                self._toy2ann[timetools.TOY(name)] = value
                self.refresh()
            except BaseException:
                objecttools.augment_excmessage(
                    f"While trying to assign a new neural network to the seasonal "
                    f"neural network collection `{self.name}` of element "
                    f"`{objecttools.devicename(self)}` based on name `{name}`"
                )
        else:
            object.__setattr__(self, name, value)

    def __delattr__(self, name: str) -> None:
        if name.startswith("toy_"):
            try:
                try:
                    del self._toy2ann[timetools.TOY(name)]
                except KeyError:
                    raise AttributeError(
                        f"No neural network is registered under a "
                        f"TOY object named `{timetools.TOY(name)}`."
                    ) from None
                self.refresh()
            except BaseException:
                objecttools.augment_excmessage(
                    f"While trying to remove a new neural network from the "
                    f"seasonal neural network collection `{self.name}` of "
                    f"element `{objecttools.devicename(self)}` based on "
                    f"name `{name}`"
                )
        else:
            object.__delattr__(self, name)

    def __iter__(self) -> Iterator[Tuple[timetools.TOY, ANN]]:
        return ((toy, ann_) for (toy, ann_) in sorted(self._toy2ann.items()))

    def __repr__(self) -> str:
        if not self:
            return f"{self.name}()"
        lines = [f"{self.name}("]
        if (len(self) == 1) and (self.toys[0] == timetools.TOY0):
            lines.append(self.anns[0].assignrepr("    ", 4))
        else:
            for toy, ann_ in self:
                line = ann_.assignrepr(f"    {toy}=", 4)
                lines.append(f"{line},")
        lines.append(")")
        return "\n".join(lines)

    def __len__(self) -> int:
        return len(self._toy2ann)

    def __dir__(self) -> List[str]:
        """
        >>> from hydpy import ann, pub, SeasonalANN
        >>> seasonalann = SeasonalANN(None)
        >>> seasonalann(
        ...     ann(nmb_inputs=1, nmb_neurons=(1,), nmb_outputs=1,
        ...         weights_input=0.0, weights_output=0.0,
        ...         intercepts_hidden=0.0, intercepts_output=1.0))
        >>> print(*dir(seasonalann))
        NDIM SPAN TIME TYPE anns calculate_values fastaccess inputs name \
nmb_inputs nmb_outputs outputs plot ratios refresh shape subpars subvars \
toy_1_1_0_0_0 toys verify
        """
        return objecttools.dir_(self) + [str(toy) for toy in self.toys]
