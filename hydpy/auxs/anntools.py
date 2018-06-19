# -*- coding: utf-8 -*-
"""This module implements rudimantary artificial neural network tools,
required for some models implemented in the HydPy framework.

A note for developers: some of the implemented features are to be applied
during model simulations are in some other way performance-critical.  Hence,
the actual calculations are defined in the Cython extension module
|annutils|.
"""

# import...
# ...from standard library
from __future__ import division, print_function
# ...from site-packages
import numpy
from hydpy import pyplot
# ...from HydPy
from hydpy.core import abctools
from hydpy.core import autodoctools
from hydpy.core import exceptiontools
from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.core import timetools
from hydpy.cythons import annutils   # pylint: disable=no-name-in-module


class ANN(object):
    """Multi-layer feed forward artificial neural network.

    The applied activation function is the logistic function:

      :math:`f(x) = \\frac{1}{1+exp(-x)}`

    Class |anntools.ANN| is intended to be subclassed for the derivation of
    very complex control parameters.  Its original purpose was to allow for
    defining arbitrary continuous relationsships between the water stored
    in a dam and the associated water stage (see model ...).  However,
    class |anntools.ANN| can also be applied directly, as shown in the
    following examples.  But if you are looking for a flexible stand-alone
    artifical neural network implementation in Python, you will find much
    more general tools easily.

    Firstly, define the most single artificial neural network consisting of
    only one input node, neuron, and output node respectively, and pass
    some arbitrary network parameters:

    >>> from hydpy import ANN, nan
    >>> ann = ANN()
    >>> ann(nmb_inputs=1, nmb_neurons=(1,), nmb_outputs=1,
    ...     weights_input=4.0, weights_output=3.0,
    ...     intercepts_hidden=-16.0, intercepts_output=-1.0)

    The following loop subsequently sets the values 0 to 8 as input values,
    performs the calculateion, and prints out the final output.  As to be
    expected, the results show the shape of the logistic function:

    >>> from hydpy import round_
    >>> for input_ in range(9):
    ...     ann.inputs[0] = input_
    ...     ann.process_actual_input()
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

    .. testsetup::

        >>> from matplotlib import pyplot
        >>> pyplot.close()

    The following example shows that everything works well for more complex
    single layer networks also (manual tests have been performed in a
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
    >>> ann.process_actual_input()
    >>> round_(ann.outputs)
    1.822222, 1.876983

    The next example shows how to solve the XOR problem with a two layer
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

    All intercepts of the neurons of the hidden layer are set to 750,
    so that an input of 500 results in an activation of approximately
    zero and an input of 1000 results in an activation of approximately
    one (note that matrix entries are not required should preferably be
    initialized with `nan` to avoid confusion):

    >>> ann.intercepts_hidden = [[-750.0, -750.0],
    ...                          [-750.0, nan]]

    The weighting factor between the both inputs and `H11` is 1000.
    Hence, one `True` input is sufficient to activate `H1`.  In contrast,
    the weighting factor between the both inputs and `H12` is 500 only.
    Hence, two `True` inputs are required to activate `H12`:

    >>> ann.weights_input= [[1000.0, 500.0],
    ...                     [1000.0, 500.0]]

    The weighting factor between `H11` and `H2` is 1000.  Hence, in
    principle, `H11` can activate `H2`.  However, the weighting factor
    between `H12` and `H2` is -1000.  Hence, `H12` is able to prevent
    `H2` from becoming activated even when `H11` is activated:

    >>> ann.weights_hidden= [[[1000.0, nan],
    ...                      [-1000.0, nan]]]

    To recapitulate, `H11` determines if at least one input is `True`,
    `H12` determines if both inputs are `True`, and `H2` determines
    if exactly one input is `True`, which is the solution for the XOR-problem:

    >>> ann
    ann(nmb_inputs=2,
        nmb_neurons=(2, 1),
        nmb_outputs=1,
        weights_input=[[1000.0, 500.0],
                       [1000.0, 500.0]],
        weights_hidden=[[[1000.0, nan],
                         [-1000.0, nan]]],
        weights_output=[[1.0]],
        intercepts_hidden=[[-750.0, -750.0],
                           [-750.0, nan]],
        intercepts_output=[0.0])

    The following calculation confirms that the network is properly
    configured:

    >>> for inputs in ((0.0, 0.0),
    ...                (1.0, 0.0),
    ...                (0.0, 1.0),
    ...                (1.0, 1.0)):
    ...    ann.inputs = inputs
    ...    ann.process_actual_input()
    ...    print(inputs[0], inputs[1], ann.outputs[0])
    0.0 0.0 0.0
    1.0 0.0 1.0
    0.0 1.0 1.0
    1.0 1.0 0.0

    To elaborate on the last calculation, the corresponding activations
    of the hidden neurons are shown. As both inputs are `True`, both
    `H12` (upper left value) and `H22` (upper right value) activated,
    but `H2` (lower left value) is not:

    >>> ann.neurons
    array([[ 1.,  1.],
           [ 0.,  0.]])

    The last defined configuration is used in some examples of the
    documentation of the members of class |anntools.ANN|:

    >>> from hydpy import dummies
    >>> dummies.ann = ann

    Note that Python class |anntools.ANN| handles a corresponding
    Cython extension class defined in |annutils|, which does not
    protect itself against segmentation faults. But class
    |anntools.ANN| takes up this task, meaning using its public
    members should always result in readable exceptions instead of
    program crashes, e.g.:

    >>> ANN().nmb_layers
    Traceback (most recent call last):
    ...
    AttributeNotReady: Attribute `nmb_layers` of object `ann` \
is not usable so far.
    """
    NDIM = 0
    TYPE = 'annutils.ANN'
    TIME = None
    SPAN = (None, None)

    parameterstep = parametertools.Parameter.__dict__['parameterstep']
    simulationstep = parametertools.Parameter.__dict__['simulationstep']

    def __init__(self):
        self.subpars = None
        self.fastaccess = objecttools.FastAccess()
        self._isready = exceptiontools.IsReady(
            false=('nmb_inputs', 'nmb_outputs', 'nmb_neurons'))
        self._cann = annutils.ANN()
        self._max_nmb_neurons = None

    def connect(self, subpars):
        """Connect the actual |anntools.ANN| object with the given
        |SubParameters| object."""
        self.subpars = subpars
        self.fastaccess = subpars.fastaccess
        setattr(self.fastaccess, self.name, self._cann)

    name = property(objecttools.name)

    def __call__(self, nmb_inputs=1, nmb_neurons=(1,), nmb_outputs=1,
                 weights_input=None, weights_output=None, weights_hidden=None,
                 intercepts_hidden=None, intercepts_output=None):
        self.nmb_inputs = nmb_inputs
        self.nmb_outputs = nmb_outputs
        self.nmb_neurons = nmb_neurons
        self.weights_input = weights_input
        self.weights_hidden = weights_hidden
        self.weights_output = weights_output
        self.intercepts_hidden = intercepts_hidden
        self.intercepts_output = intercepts_output
        del self.inputs
        del self.outputs
        del self.neurons

    def _update_shapes(self):
        if self._isready:
            del self.weights_input
            del self.weights_hidden
            del self.weights_output
            del self.intercepts_hidden
            del self.intercepts_output
            del self.inputs
            del self.outputs
            del self.neurons

    def _get_nmb_inputs(self):
        """Number of input nodes.

        >>> from hydpy import dummies
        >>> dummies.ann.nmb_inputs
        2
        """
        return self._cann.nmb_inputs

    def _set_nmb_inputs(self, value):
        self._cann.nmb_inputs = int(value)
        self._update_shapes()

    nmb_inputs = exceptiontools.protected_property(
        'nmb_inputs', _get_nmb_inputs, _set_nmb_inputs)

    def _get_nmb_outputs(self):
        """Number of output nodes.

        >>> from hydpy import dummies
        >>> dummies.ann.nmb_outputs
        1
        """
        return self._cann.nmb_outputs

    def _set_nmb_outputs(self, value):
        self._cann.nmb_outputs = int(value)
        self._update_shapes()

    nmb_outputs = exceptiontools.protected_property(
        'nmb_outputs', _get_nmb_outputs, _set_nmb_outputs)

    def _get_nmb_layers(self):
        """Number of hidden layers.

        >>> from hydpy import dummies
        >>> dummies.ann.nmb_layers
        2
        """
        return self._cann.nmb_layers

    nmb_layers = exceptiontools.dependent_property(
        'nmb_layers', _get_nmb_layers)

    def _get_nmb_neurons(self):
        """Number of neurons of the hidden layers.

        >>> from hydpy import dummies
        >>> dummies.ann.nmb_neurons
        (2, 1)
        """
        return tuple(numpy.asarray(self._cann.nmb_neurons))

    def _set_nmb_neurons(self, value):
        self._cann.nmb_neurons = numpy.array(value, dtype=int, ndmin=1)
        self._cann.nmb_layers = len(value)
        self._max_nmb_neurons = max(value)
        self._update_shapes()

    nmb_neurons = exceptiontools.protected_property(
        'nmb_neurons', _get_nmb_neurons, _set_nmb_neurons)

    def _get_weights_input(self):
        """Weights between all input nodes and neurons of the first hidden
        layer.

        The input nodes and the neurons are varied on the first axis and
        on the second axis of the 2-dimensional array:

        >>> from hydpy import ANN
        >>> ann = ANN()
        >>> ann(nmb_inputs=2, nmb_neurons=(3,))
        >>> ann.weights_input
        array([[ 0.,  0.,  0.],
               [ 0.,  0.,  0.]])

        It is allowed to set values via slicing:

        >>> ann.weights_input[:, 0] = 1.
        >>> ann.weights_input
        array([[ 1.,  0.,  0.],
               [ 1.,  0.,  0.]])

        If possible, type conversions are performed:

        >>> ann.weights_input = '2'
        >>> ann.weights_input
        array([[ 2.,  2.,  2.],
               [ 2.,  2.,  2.]])

        One can assign whole matrices directly:

        >>> import numpy
        >>> ann.weights_input = numpy.eye(2, 3)
        >>> ann.weights_input
        array([[ 1.,  0.,  0.],
        ...    [ 0.,  1.,  0.]])

        One can also delete the values contained in the array:

        >>> del ann.weights_input
        >>> ann.weights_input
        array([[ 0.,  0.,  0.],
        ...    [ 0.,  0.,  0.]])

        Errors like wrong shapes (or unconvertible inputs) result in error
        messages:

        >>> ann.weights_input = numpy.eye(3)
        Traceback (most recent call last):
        ...
        ValueError: While trying to set the input weights of the artificial \
neural network `ann` of element `?`, the following error occured: could not \
broadcast input array from shape (3,3) into shape (2,3)
        """
        return numpy.asarray(self._cann.weights_input)

    def _set_weights_input(self, values):
        if values is None:
            self._del_weights_input()
        else:
            try:
                self._cann.weights_input = numpy.full(self.shape_weights_input,
                                                      values, dtype=float)
            except BaseException:
                objecttools.augment_excmessage(
                    'While trying to set the input weights of the artificial '
                    'neural network `%s` of element `%s`'
                    % (self.name, objecttools.devicename(self)))

    def _del_weights_input(self):
        self._cann.weights_input = numpy.zeros(self.shape_weights_input)

    weights_input = exceptiontools.dependent_property(
        'weights_input', _get_weights_input,
        _set_weights_input, _del_weights_input)

    @property
    def shape_weights_input(self):
        """Shape of the array containing the input weights.

        >>> from hydpy import dummies
        >>> dummies.ann.shape_weights_input
        (2, 2)
        """
        return (self.nmb_inputs, self.nmb_neurons[0])

    @property
    def nmb_weights_input(self):
        """Number of input weights.

        >>> from hydpy import dummies
        >>> dummies.ann.nmb_weights_input
        4
        """
        return self.nmb_neurons[0]*self.nmb_inputs

    def _get_weights_output(self):
        """Weights between all neurons of the last hidden layer and the output
        nodes.

        The neurons and the output nodes are varied on the first axis and
        on the second axis of the 2-dimensional array:

        >>> from hydpy import ANN
        >>> ann = ANN()
        >>> ann(nmb_outputs=2, nmb_neurons=(3,))
        >>> ann.weights_output
        array([[ 0.,  0.],
               [ 0.,  0.],
               [ 0.,  0.]])

        It is allowed to set values via slicing:

        >>> ann.weights_output[:, 0] = 1.
        >>> ann.weights_output
        array([[ 1.,  0.],
               [ 1.,  0.],
               [ 1.,  0.]])

        If possible, type conversions are performed:

        >>> ann.weights_output = '2'
        >>> ann.weights_output
        array([[ 2.,  2.],
               [ 2.,  2.],
               [ 2.,  2.]])

        One can assign whole matrices directly:

        >>> import numpy
        >>> ann.weights_output = numpy.eye(3, 2)
        >>> ann.weights_output
        array([[ 1.,  0.],
               [ 0.,  1.],
               [ 0.,  0.]])

        One can also delete the values contained in the array:

        >>> del ann.weights_output
        >>> ann.weights_output
        array([[ 0.,  0.],
               [ 0.,  0.],
               [ 0.,  0.]])

        Errors like wrong shapes (or unconvertible inputs) result in error
        messages:

        >>> ann.weights_output = numpy.eye(3)
        Traceback (most recent call last):
        ...
        ValueError: While trying to set the output weights of the artificial \
neural network `ann` of element `?`, the following error occured: could not \
broadcast input array from shape (3,3) into shape (3,2)
        """
        return numpy.asarray(self._cann.weights_output)

    def _set_weights_output(self, values):
        if values is None:
            self._del_weights_output()
        else:
            try:
                self._cann.weights_output = numpy.full(
                    self.shape_weights_output, values, dtype=float)
            except BaseException:
                objecttools.augment_excmessage(
                    'While trying to set the output weights of the artificial '
                    'neural network `%s` of element `%s`'
                    % (self.name, objecttools.devicename(self)))

    def _del_weights_output(self):
        self._cann.weights_output = numpy.zeros(self.shape_weights_output)

    weights_output = exceptiontools.dependent_property(
        'weights_output', _get_weights_output,
        _set_weights_output, _del_weights_output)

    @property
    def shape_weights_output(self):
        """Shape of the array containing the output weights.

        >>> from hydpy import dummies
        >>> dummies.ann.shape_weights_output
        (1, 1)
        """
        return (self.nmb_neurons[-1], self.nmb_outputs)

    @property
    def nmb_weights_output(self):
        """Number of output weights.

        >>> from hydpy import dummies
        >>> dummies.ann.nmb_weights_output
        1
        """
        return self.nmb_neurons[-1]*self.nmb_outputs

    def _get_weights_hidden(self):
        """Weights between between the neurons of the different hidden layers.

        The layers are varied on the first axis, the neurons of the respective
        upstream layer on the second axis and the neurons of the respective
        downstream layer on the third axis of a 3-dimensional array:

        >>> from hydpy import ANN
        >>> ann = ANN()
        >>> ann(nmb_neurons=(3, 2, 3))
        >>> ann.weights_hidden
        array([[[  0.,   0.,  nan],
                [  0.,   0.,  nan],
                [  0.,   0.,  nan]],
        <BLANKLINE>
               [[  0.,   0.,   0.],
                [  0.,   0.,   0.],
                [ nan,  nan,  nan]]])

        It is allowed to set values via slicing:

        >>> ann.weights_hidden[1, :, 0] = 1.
        >>> ann.weights_hidden
        array([[[  0.,   0.,  nan],
                [  0.,   0.,  nan],
                [  0.,   0.,  nan]],
        <BLANKLINE>
               [[  1.,   0.,   0.],
                [  1.,   0.,   0.],
                [  1.,  nan,  nan]]])

        If possible, type conversions are performed:

        >>> ann.weights_hidden = '2'
        >>> ann.weights_hidden
        array([[[ 2.,  2.,  2.],
                [ 2.,  2.,  2.],
                [ 2.,  2.,  2.]],
        <BLANKLINE>
               [[ 2.,  2.,  2.],
                [ 2.,  2.,  2.],
                [ 2.,  2.,  2.]]])

        One can assign whole matrices directly:

        >>> import numpy
        >>> ann.weights_hidden = numpy.eye(3)
        >>> ann.weights_hidden
        array([[[ 1.,  0.,  0.],
                [ 0.,  1.,  0.],
                [ 0.,  0.,  1.]],
        <BLANKLINE>
               [[ 1.,  0.,  0.],
                [ 0.,  1.,  0.],
                [ 0.,  0.,  1.]]])

        One can also delete the values contained in the array:

        >>> del ann.weights_hidden
        >>> ann.weights_hidden
        array([[[  0.,   0.,  nan],
                [  0.,   0.,  nan],
                [  0.,   0.,  nan]],
        <BLANKLINE>
               [[  0.,   0.,   0.],
                [  0.,   0.,   0.],
                [ nan,  nan,  nan]]])

        Errors like wrong shapes (or unconvertible inputs) result in error
        messages:

        >>> ann.weights_hidden = numpy.eye(3, 2)
        Traceback (most recent call last):
        ...
        ValueError: While trying to set the hidden weights of the artificial \
neural network `ann` of element `?`, the following error occured: could not \
broadcast input array from shape (3,2) into shape (2,3,3)
        """
        return numpy.asarray(self._cann.weights_hidden)

    def _set_weights_hidden(self, values):
        if values is None:
            self._del_weights_hidden()
        else:
            try:
                self._cann.weights_hidden = numpy.full(
                    self.shape_weights_hidden, values, dtype=float)
            except BaseException:
                objecttools.augment_excmessage(
                    'While trying to set the hidden weights of the artificial '
                    'neural network `%s` of element `%s`'
                    % (self.name, objecttools.devicename(self)))

    def _del_weights_hidden(self):
        self._cann.weights_hidden = numpy.full(self.shape_weights_hidden,
                                               numpy.nan)
        for idx_layer in range(self.nmb_layers-1):
            for idx_neuron1 in range(self.nmb_neurons[idx_layer]):
                for idx_neuron2 in range(self.nmb_neurons[idx_layer+1]):
                    self._cann.weights_hidden[idx_layer,
                                              idx_neuron1,
                                              idx_neuron2] = 0.

    weights_hidden = exceptiontools.dependent_property(
        'weights_hidden', _get_weights_hidden,
        _set_weights_hidden, _del_weights_hidden)

    @property
    def shape_weights_hidden(self):
        """Shape of the array containing the activation of the hidden neurons.

        >>> from hydpy import dummies
        >>> dummies.ann.shape_weights_hidden
        (1, 2, 2)
        """
        if self.nmb_layers > 1:
            return (self.nmb_layers-1,
                    self._max_nmb_neurons,
                    self._max_nmb_neurons)
        return (0, 0, 0)

    @property
    def nmb_weights_hidden(self):
        """Number of hidden weights.

        >>> from hydpy import dummies
        >>> dummies.ann.nmb_weights_hidden
        2
        """
        nmb = 0
        for idx_layer in range(self.nmb_layers-1):
            nmb += self.nmb_neurons[idx_layer] * self.nmb_neurons[idx_layer+1]
        return nmb

    def _get_intercepts_hidden(self):
        """Intercepts of all neurons of the hidden layers.

        All intercepts are handled in a 1-dimensional array:

        >>> from hydpy import ANN
        >>> ann = ANN()
        >>> ann(nmb_neurons=(3, 2))
        >>> ann.intercepts_hidden
        array([[  0.,   0.,   0.],
               [  0.,   0.,  nan]])

        It is allowed to set values via slicing:

        >>> ann.intercepts_hidden[0, :] = 1.
        >>> ann.intercepts_hidden
        array([[  1.,   1.,   1.],
               [  0.,   0.,  nan]])

        If possible, type conversions are performed:

        >>> ann.intercepts_hidden = '2'
        >>> ann.intercepts_hidden
        array([[ 2.,  2.,  2.],
               [ 2.,  2.,  2.]])

        One can assign whole matrices directly:

        >>> import numpy
        >>> ann.intercepts_hidden = [1.0, 3.0, 2.0]
        >>> ann.intercepts_hidden
        array([[ 1.,  3.,  2.],
               [ 1.,  3.,  2.]])

        One can also delete the values contained in the array:

        >>> del ann.intercepts_hidden
        >>> ann.intercepts_hidden
        array([[  0.,   0.,   0.],
               [  0.,   0.,  nan]])

        Errors like wrong shapes (or unconvertible inputs) result in error
        messages:

        >>> ann.intercepts_hidden = [1.0, 3.0]
        Traceback (most recent call last):
        ...
        ValueError: While trying to set the neuron related intercepts of the \
artificial neural network `ann` of element `?`, the following error occured: \
could not broadcast input array from shape (2) into shape (2,3)

        The number of input intercepts is available as a property:

        >>> ann.nmb_intercepts_hidden
        5
        """
        return numpy.asarray(self._cann.intercepts_hidden)

    def _set_intercepts_hidden(self, values):
        if values is None:
            self._del_intercepts_hidden()
        else:
            try:
                self._cann.intercepts_hidden = numpy.full(
                    self.shape_intercepts_hidden, values, dtype=float)
            except BaseException:
                objecttools.augment_excmessage(
                    'While trying to set the neuron related intercepts of '
                    'the artificial neural network `%s` of element `%s`'
                    % (self.name, objecttools.devicename(self)))

    def _del_intercepts_hidden(self):
        self._cann.intercepts_hidden = numpy.full(
            self.shape_intercepts_hidden,
            numpy.nan)
        for idx_layer in range(self.nmb_layers):
            for idx_neuron in range(self.nmb_neurons[idx_layer]):
                self._cann.intercepts_hidden[idx_layer, idx_neuron] = 0.

    intercepts_hidden = exceptiontools.dependent_property(
        'intercepts_hidden', _get_intercepts_hidden,
        _set_intercepts_hidden, _del_intercepts_hidden)

    @property
    def shape_intercepts_hidden(self):
        """Shape if the array containing the intercepts of neurons of
        the hidden layers."""
        return (self.nmb_layers, self._max_nmb_neurons)

    @property
    def nmb_intercepts_hidden(self):
        """Number of input intercepts."""
        return sum(self.nmb_neurons)

    def _get_intercepts_output(self):
        """Intercepts of all output nodes.

        All intercepts are handled in a 1-dimensional array:

        >>> from hydpy import ANN
        >>> ann = ANN()
        >>> ann(nmb_outputs=3)
        >>> ann.intercepts_output
        array([ 0.,  0.,  0.])

        It is allowed to set values via slicing:

        >>> ann.intercepts_output[1:] = 1.
        >>> ann.intercepts_output
        array([ 0.,  1.,  1.])

        If possible, type conversions are performed:

        >>> ann.intercepts_output = '2'
        >>> ann.intercepts_output
        array([ 2.,  2.,  2.])

        One can assign whole matrices directly:

        >>> import numpy
        >>> ann.intercepts_output = [1.0, 3.0, 2.0]
        >>> ann.intercepts_output
        array([ 1.,  3.,  2.])

        One can also delete the values contained in the array:

        >>> del ann.intercepts_output
        >>> ann.intercepts_output
        array([ 0.,  0.,  0.])

        Errors like wrong shapes (or unconvertible inputs) result in error
        messages:

        >>> ann.intercepts_output = [1.0, 3.0]
        Traceback (most recent call last):
        ...
        ValueError: While trying to set the output node related intercepts \
of the artificial neural network `ann` of element `?`, the following error \
occured: could not broadcast input array from shape (2) into shape (3)
        """
        return numpy.asarray(self._cann.intercepts_output)

    def _set_intercepts_output(self, values):
        if values is None:
            self._del_intercepts_output()
        else:
            try:
                self._cann.intercepts_output = numpy.full(
                    self.shape_intercepts_output, values, dtype=float)
            except BaseException:
                objecttools.augment_excmessage(
                    'While trying to set the output node related intercepts '
                    'of the artificial neural network `%s` of element `%s`'
                    % (self.name, objecttools.devicename(self)))

    def _del_intercepts_output(self):
        self._cann.intercepts_output = numpy.zeros(
            self.shape_intercepts_output)

    intercepts_output = exceptiontools.dependent_property(
        'intercepts_output', _get_intercepts_output,
        _set_intercepts_output, _del_intercepts_output)

    @property
    def shape_intercepts_output(self):
        """Shape if the array containing the intercepts of neurons of
        the hidden layers.

        >>> from hydpy import dummies
        >>> dummies.ann.shape_intercepts_output
        (1,)
        """
        return (self.nmb_outputs,)

    @property
    def nmb_intercepts_output(self):
        """Number of output intercepts.

        >>> from hydpy import dummies
        >>> dummies.ann.nmb_intercepts_output
        1
        """
        return self.nmb_outputs

    def _get_inputs(self):
        """Values of the input nodes.

        All input values are handled in a 1-dimensional array:

        >>> from hydpy import ANN
        >>> ann = ANN()
        >>> ann(nmb_inputs=3)
        >>> ann.inputs
        array([ 0.,  0.,  0.])

        It is allowed to set values via slicing:

        >>> ann.inputs[1:] = 1.
        >>> ann.inputs
        array([ 0.,  1.,  1.])

        If possible, type conversions are performed:

        >>> ann.inputs = '2'
        >>> ann.inputs
        array([ 2.,  2.,  2.])

        One can assign whole matrices directly:

        >>> import numpy
        >>> ann.inputs = [1.0, 3.0, 2.0]
        >>> ann.inputs
        array([ 1.,  3.,  2.])

        One can also delete the values contained in the array:

        >>> del ann.inputs
        >>> ann.inputs
        array([ 0.,  0.,  0.])

        Errors like wrong shapes (or unconvertible inputs) result in error
        messages:

        >>> ann.inputs = [1.0, 3.0]
        Traceback (most recent call last):
        ...
        ValueError: While trying to set the inputs of the artificial neural \
network `ann` of element `?`, the following error occured: could not \
broadcast input array from shape (2) into shape (3)
        """
        return numpy.asarray(self._cann.inputs)

    def _set_inputs(self, values):
        try:
            self._cann.inputs = numpy.full(self.nmb_inputs,
                                           values, dtype=float)
        except BaseException:
            objecttools.augment_excmessage(
                'While trying to set the inputs of the artificial '
                'neural network `%s` of element `%s`'
                % (self.name, objecttools.devicename(self)))

    def _del_inputs(self):
        self._cann.inputs = numpy.zeros(self.nmb_inputs)

    inputs = exceptiontools.dependent_property(
        'inputs', _get_inputs, _set_inputs, _del_inputs)

    def _get_outputs(self):
        """Values of the output nodes.

        All output values are handled in a 1-dimensional array:

        >>> from hydpy import ANN
        >>> ann = ANN()
        >>> ann(nmb_outputs=3)
        >>> ann.outputs
        array([ 0.,  0.,  0.])

        It is not allowed to change output values manually:

        >>> ann.outputs = 1.0
        Traceback (most recent call last):
        ...
        AttributeError: Attribute `outputs` of object `ann` \
cannot be used this way.
        """
        return numpy.asarray(self._cann.outputs)

    def _del_outputs(self):
        self._cann.outputs = numpy.zeros(self.nmb_outputs)

    outputs = exceptiontools.dependent_property(
        'outputs', _get_outputs, fdel=_del_outputs)

    def _get_neurons(self):
        """The activation of the neurons of the hidden layers.

        >>> from hydpy import dummies
        >>> dummies.ann.neurons
        array([[ 1.,  1.],
               [ 0.,  0.]])
        """
        return numpy.array(self._cann.neurons)

    def _del_neurons(self):
        nmb_neurons = numpy.asarray(self._cann.nmb_neurons)
        self._cann.neurons = numpy.zeros((self.nmb_layers, max(nmb_neurons)))

    neurons = exceptiontools.dependent_property(
        'neurons', _get_neurons, fdel=_del_neurons)

    def process_actual_input(self):
        """Calculates the network output values based on the input values
        defined previously.

        For more information see the documentation on class |anntools.ANN|.
        """
        self._cann.process_actual_input()

    @property
    def nmb_weights(self):
        """Number of all input, inner, and output weights.

        >>> from hydpy import dummies
        >>> dummies.ann.nmb_weights
        7
        """
        return (self.nmb_weights_input +
                self.nmb_weights_hidden +
                self.nmb_weights_output)

    @property
    def nmb_intercepts(self):
        """Number of all inner and output intercepts.

        >>> from hydpy import dummies
        >>> dummies.ann.nmb_intercepts
        4
        """
        return self.nmb_intercepts_hidden + self.nmb_intercepts_output

    @property
    def nmb_parameters(self):
        """Sum of |anntools.ANN.nmb_weights| and |anntools.ANN.nmb_intercepts|.

        >>> from hydpy import dummies
        >>> dummies.ann.nmb_parameters
        11
        """
        return self.nmb_weights + self.nmb_intercepts

    def verify(self):
        """Raise a |RuntimeError| if the network's shape is not defined
        completely.


        >>> from hydpy import dummies
        >>> dummies.ann.verify()

        >>> from hydpy import ANN
        >>> ANN().verify()
        Traceback (most recent call last):
        ...
        RuntimeError: The shape of the the artificial neural network \
parameter `ann` of element `?` has not been defined so far.
        """
        if not self._isready:
            raise RuntimeError(
                'The shape of the the artificial neural network '
                'parameter %s has not been defined so far.'
                % objecttools.elementphrase(self))

    def assignrepr(self, prefix):
        """Return a string representation of the actual |anntools.ANN| object
        that is prefixed with the given string."""
        prefix = '%s%s(' % (prefix, self.name)
        blanks = len(prefix)*' '
        lines = [(objecttools.assignrepr_value(
            self.nmb_inputs, '%snmb_inputs=' % prefix)+',')]
        lines.append(objecttools.assignrepr_tuple(
            self.nmb_neurons, '%snmb_neurons=' % blanks)+',')
        lines.append(objecttools.assignrepr_value(
            self.nmb_outputs, '%snmb_outputs=' % blanks)+',')
        lines.append(objecttools.assignrepr_list2(
            self.weights_input, '%sweights_input=' % blanks)+',')
        if self.nmb_layers > 1:
            lines.append(objecttools.assignrepr_list3(
                self.weights_hidden, '%sweights_hidden=' % blanks)+',')
        lines.append(objecttools.assignrepr_list2(
            self.weights_output, '%sweights_output=' % blanks)+',')
        lines.append(objecttools.assignrepr_list2(
            self.intercepts_hidden, '%sintercepts_hidden=' % blanks)+',')
        lines.append(objecttools.assignrepr_list(
            self.intercepts_output, '%sintercepts_output=' % blanks)+')')
        return '\n'.join(lines)

    def __repr__(self):
        return self.assignrepr(prefix='')

    def plot(self, xmin, xmax, idx_input=0, idx_output=0, points=100,
             **kwargs):
        """Plot the relationship between a certain input (`idx_input`) and a
        certain output (`idx_output`) variable described by the actual
        |anntools.ANN| object.

        Define the lower and the upper bound of the x axis via arguments
        `xmin` and `xmax`.  The number of plotting points can be modified
        by argument `points`.  Additional `matplotlib` plotting arguments
        can be passed as keyword arguments.
        """
        xs_ = numpy.linspace(xmin, xmax, points)
        ys_ = numpy.zeros(xs_.shape)
        for idx, x__ in enumerate(xs_):
            self.inputs[idx_input] = x__
            self.process_actual_input()
            ys_[idx] = self.outputs[idx_output]
        pyplot.plot(xs_, ys_, **kwargs)


abctools.ParameterABC.register(ANN)
abctools.ANNABC.register(ANN)


def ann(**kwargs):
    """Return a new stand alone |anntools.ANN| object with the given parameter
    values.

    The purpose of this function is to allow for string representations of
    parameters containing multiple |anntools.ANN| instances.

    When passing no arguments, the default values of class |anntools.ANN| will
    be applied:

    >>> from hydpy import ANN
    >>> ann1 = ann()
    >>> ann1
    ann(nmb_inputs=1,
        nmb_neurons=(1,),
        nmb_outputs=1,
        weights_input=[[0.0]],
        weights_output=[[0.0]],
        intercepts_hidden=[[0.0]],
        intercepts_output=[0.0])

    Of course, all parameter values can be changed:

    >>> ann2 = ann(nmb_inputs=1, nmb_neurons=(1,), nmb_outputs=1,
    ...            weights_input=4.0, weights_output=3.0,
    ...            intercepts_hidden=-16.0, intercepts_output=-1.0)
    >>> ann2
    ann(nmb_inputs=1,
        nmb_neurons=(1,),
        nmb_outputs=1,
        weights_input=[[4.0]],
        weights_output=[[3.0]],
        intercepts_hidden=[[-16.0]],
        intercepts_output=[-1.0])

    The following line is just thought to make clear, that two independent
    |anntools.ANN| objects have been initialized (instead of changing the
    values of an existing |anntools.ANN| object vai its `call` method):

    >>> ann1 is ann2
    False
    """
    new_ann = ANN()
    new_ann(**kwargs)
    return new_ann


class SeasonalANN(object):
    """Handles relationships described by artificial neural networks that
    vary within an anual cycle.

    Class |anntools.SeasonalANN| is an alternative implementation of class
    |SeasonalParameter| specifically designed for handling multiple
    |anntools.ANN| objects that are valid for different times of the year,
    described by |TOY| objects.  The total output of a |anntools.SeasonalANN|
    object is a weighted mean of the output of one or two "normal" neural
    networks.  |anntools.SeasonalANN.ratios| used for weighting depend
    on the actual time of the year.

    To explain this in more detail, let us define a |anntools.SeasonalANN|
    object first, that contains three "normal" networks for January, 1,
    March, 1, and July, 1, respectively (note that this example is similar
    to the example used to describe class
    |SeasonalParameter|):

    >>> from hydpy import SeasonalANN, ann
    >>> seasonalann = SeasonalANN()
    >>> seasonalann.simulationstep = '1d'
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

    The confused time order in the initialization call above does not pose
    a problem, as |anntools.SeasonalANN| performs time sorting internally:

    >>> seasonalann
    seasonalann(toy_1_1_12_0_0=ann(nmb_inputs=1,
                                   nmb_neurons=(1,),
                                   nmb_outputs=1,
                                   weights_input=[[0.0]],
                                   weights_output=[[0.0]],
                                   intercepts_hidden=[[0.0]],
                                   intercepts_output=[1.0]),
                toy_3_1_12_0_0=ann(nmb_inputs=1,
                                   nmb_neurons=(1,),
                                   nmb_outputs=1,
                                   weights_input=[[0.0]],
                                   weights_output=[[0.0]],
                                   intercepts_hidden=[[0.0]],
                                   intercepts_output=[-1.0]),
                toy_7_1_12_0_0=ann(nmb_inputs=1,
                                   nmb_neurons=(1,),
                                   nmb_outputs=1,
                                   weights_input=[[4.0]],
                                   weights_output=[[3.0]],
                                   intercepts_hidden=[[-16.0]],
                                   intercepts_output=[-1.0]))

    The property |anntools.SeasonalANN.shape| does reflect the number of
    required weighting ratios for each time of year (in this example:
    366 days per year) and each neural network (in this example: three):

    >>> seasonalann.shape
    (366, 3)

    For safety reasons, |anntools.SeasonalANN.shape| should normally not
    be changed manually:

    >>> seasonalann.shape = (366, 4)
    Traceback (most recent call last):
    ...
    AttributeError: can't set attribute

    The following interactive shows how the |anntools.SeasonalANN.ratios|
    used for weighting are calculated:

    .. testsetup::

        >>> from bokeh import plotting, models, palettes
        ...
        >>> from hydpy import docs
        >>> import os
        >>> plotting.output_file(os.path.join(
        ...     docs.__path__[0], 'html', 'anntools.SeasonalANN.ratios.html'))
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
        ...                        click_policy='mute')
        >>> plot.add_layout(legend, 'right')
        >>> label_dict = {0: 'Jan 1',
        ...               60: 'Mar 1',
        ...               182: 'Jul 1'}
        >>> plot.xaxis.ticker =  sorted(label_dict.keys())
        >>> plot.xaxis.formatter = models.FuncTickFormatter(
        ...     code='var labels = %s; return labels[tick];' % label_dict)
        >>> dummy = plotting.save(plot)

    .. raw:: html

        <iframe
            src="anntools.SeasonalANN.ratios.html"
            width="100%"
            height="300px"
            frameborder=0
        ></iframe>

    For example, on July, 1 (which is the 183th day of a leap year),
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
    as explained for class |anntools.ANN|, except that the index of the
    actual time of year needs to be passed as the single argument of
    |anntools.SeasonalANN.process_actual_input|.  Passing the index value
    `182` activates the third network only, which is configured exactly
    as the one exemplifying class |anntools.ANN|:

    >>> from hydpy import round_
    >>> for input_ in range(9):
    ...     seasonalann.inputs[0] = input_
    ...     seasonalann.process_actual_input(182)
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

    For both networks all parameters except the output intercepts are
    zero.  Hence, the calculated output is independent of the given input.
    The output of the first network (1.0) dominates the output of the
    second network (-1.0):

    >>> from hydpy import round_
    >>> for input_ in range(9):
    ...     seasonalann.inputs[0] = input_
    ...     seasonalann.process_actual_input(12)
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
    consistent.  Hence some tests are performed:

    >>> seasonalann = SeasonalANN()
    >>> seasonalann.process_actual_input(0)
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
parameter `seasonalann` of element `?`, the following error occured: \
While trying to retrieve the month for TOY (time of year) object based \
on the string `_13_1_12`, the following error occured: \
The value of property `month` of TOY (time of year) objects must lie \
within the range `(1, 12)`, but the given value is `13`.

    >>> seasonalann(
    ...     ann(nmb_inputs=2, nmb_neurons=(1,), nmb_outputs=1,
    ...         weights_input=0.0, weights_output=0.0,
    ...         intercepts_hidden=0.0, intercepts_output=1.0))
    >>> seasonalann
    seasonalann(ann(nmb_inputs=2,
                    nmb_neurons=(1,),
                    nmb_outputs=1,
                    weights_input=[[0.0],
                                   [0.0]],
                    weights_output=[[0.0]],
                    intercepts_hidden=[[0.0]],
                    intercepts_output=[1.0]))

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

    Whenever a test fails, all networks are removed for safety:

    >>> seasonalann
    seasonalann()

    Alternatively, neural networks can be added individually via
    attribute access:

    >>> jan = ann(nmb_inputs=1, nmb_neurons=(1,), nmb_outputs=1,
    ...           weights_input=0.0, weights_output=0.0,
    ...           intercepts_hidden=0.0, intercepts_output=1.0)
    >>> seasonalann.toy_1_1_12 = jan

    Setting an attribute updates everything, e.g.:

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
on name `toy_7_1_12`, the following error occured: \
The number of input and output values of all neural networks contained \
by a seasonal neural network collection must be identical and be known \
by the containing object.  But the seasonal neural network collection \
`seasonalann` of element `?` assumes `1` input and `1` output values, \
while the network corresponding to the time of year `toy_7_1_12_0_0` \
requires `2` input and `1` output values.

    Besides setting new networks, getting and deleting them are also
    suppported:

    >>> seasonalann.toy_1_1_12 = jan
    >>> seasonalann.toy_1_1_12
    ann(nmb_inputs=1,
        nmb_neurons=(1,),
        nmb_outputs=1,
        weights_input=[[0.0]],
        weights_output=[[0.0]],
        intercepts_hidden=[[0.0]],
        intercepts_output=[1.0])
    >>> del seasonalann.toy_1_1_12

    These error messages related to attribute access are provided:

    >>> seasonalann.toy_1_1_12
    Traceback (most recent call last):
    ...
    AttributeError: While trying to look up for a neural network handled \
by the seasonal neural network collection `seasonalann` of element `?` \
based on name `toy_1_1_12`, the following error occured: No neural network \
is registered under a TOY object named `toy_1_1_12_0_0`.

    >>> del seasonalann.toy_1_1_12
    Traceback (most recent call last):
    ...
    AttributeError: While trying to remove a new neural network from the \
seasonal neural network collection `seasonalann` of element `?` based on \
name `toy_1_1_12`, the following error occured: No neural network is \
registered under a TOY object named `toy_1_1_12_0_0`.

    >>> seasonalann.toy_1_1_12 = 1
    Traceback (most recent call last):
    ...
    TypeError: While trying to assign a new neural network to the seasonal \
neural network collection `seasonalann` of element `?` based on name \
`toy_1_1_12`, the following error occured: Value `1` of type `int` has \
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
    TYPE = 'annutils.SeasonalANN'
    TIME = None
    SPAN = (None, None)

    parameterstep = parametertools.Parameter.__dict__['parameterstep']
    simulationstep = parametertools.Parameter.__dict__['simulationstep']

    def __init__(self):
        self.subpars = None
        self.fastaccess = objecttools.FastAccess()
        self._toy2ann = {}
        self.__sann = None
        self._do_refresh = True

    def connect(self, subpars):
        """Connect the actual |anntools.SeasonalANN| object with the given
        |SubParameters| object."""
        self.subpars = subpars
        self.fastaccess = subpars.fastaccess

    name = property(objecttools.name)

    def __call__(self, *args, **kwargs):
        self._toy2ann.clear()
        self._do_refresh = False
        try:
            if (len(args) > 1) or (args and kwargs):
                raise ValueError(
                    'Type `%s` accepts either a single positional argument or '
                    'an arbitrary number of keyword arguments, but for the '
                    'corresponding parameter of element `%s` %d positional '
                    'and %d keyword arguments have been given.'
                    % (objecttools.classname(self),
                       objecttools.devicename(self),
                       len(args), len(kwargs)))
            if args:
                kwargs['_1'] = args[0]
            for (toystr, value) in kwargs.items():
                if not isinstance(value, abctools.ANNABC):
                    raise TypeError(
                        'Type `%s` is not (a subclass of) type `ANN`.'
                        % objecttools.classname(value))
                try:
                    setattr(self, str(timetools.TOY(toystr)), value)
                except BaseException:
                    objecttools.augment_excmessage(
                        'While trying to add a season specific neural '
                        'network to parameter `%s` of element `%s`'
                        % (self.name, objecttools.devicename(self)))
        except BaseException as exc:
            self._toy2ann.clear()
            raise exc
        finally:
            self._do_refresh = True
            self.refresh()

    def refresh(self):
        """Prepare the actual |anntools.SeasonalANN| object for calculations.

        Dispite all automated refreshings explained in the general
        documentation on class |anntools.SeasonalANN|, it is still possible
        to destroy the inner consistency of a |anntools.SeasonalANN| instance,
        as it stores its |anntools.ANN| objects by reference.  This is shown
        by the following example:

        >>> from hydpy import SeasonalANN, ann
        >>> seasonalann = SeasonalANN()
        >>> seasonalann.simulationstep = '1d'
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
        informative error message.  Whenever you are afraid some
        inconsistency might have crept in, and you want to repair it,
        call method |anntools.SeasonalANN.refresh| explicitly:

        >>> seasonalann.refresh()
        >>> jan.nmb_inputs, jan.nmb_outputs
        (2, 3)
        >>> seasonalann.nmb_inputs, seasonalann.nmb_outputs
        (2, 3)
        """
        if self._do_refresh:
            if self.anns:
                self.__sann = annutils.SeasonalANN(self.anns)
                setattr(self.fastaccess, self.name, self._sann)
                self._setshape((None, self._sann.nmb_anns))
                if self._sann.nmb_anns > 1:
                    self._interp()
                else:
                    self._sann.ratios[:, 0] = 1.
                self.verify()
            else:
                self.__sann = None

    def verify(self):
        """Raise a |RuntimeError| and removes all handled neural networks,
        if the they are defined inconsistently.

        Dispite all automated safety checks explained in the general
        documentation on class |anntools.SeasonalANN|, it is still possible
        to destroy the inner consistency of a |anntools.SeasonalANN| instance,
        as it stores its |anntools.ANN| objects by reference.  This is shown
        by the following example:

        >>> from hydpy import SeasonalANN, ann
        >>> seasonalann = SeasonalANN()
        >>> seasonalann.simulationstep = '1d'
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
        informative error message.  Whenever you are afraid some
        inconsistency might have crept in, and you want to find out if this
        is actually the case, call method |anntools.SeasonalANN.verify|
        explicitly:

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
                'Seasonal artificial neural network collections need '
                'to handle at least one "normal" single neural network, '
                'but for the seasonal neural network `%s` of element '
                '`%s` none has been defined so far.'
                % (self.name, objecttools.devicename(self)))
        for toy, ann_ in self:
            ann_.verify()
            if ((self.nmb_inputs != ann_.nmb_inputs) or
                    (self.nmb_outputs != ann_.nmb_outputs)):
                self._toy2ann.clear()
                raise RuntimeError(
                    'The number of input and output values of all neural '
                    'networks contained by a seasonal neural network '
                    'collection must be identical and be known by the '
                    'containing object.  But the seasonal neural '
                    'network collection `%s` of element `%s` assumes '
                    '`%d` input and `%d` output values, while the network '
                    'corresponding to the time of year `%s` requires '
                    '`%d` input and `%d` output values.'
                    % (self.name, objecttools.devicename(self),
                       self.nmb_inputs, self.nmb_outputs,
                       toy,
                       ann_.nmb_inputs, ann_.nmb_outputs))

    def _interp(self):
        ratios = self.ratios
        ratios[:, :] = 0.0
        toys = self.toys
        for tdx, date in enumerate(
                timetools.TOY.centred_timegrid(self.simulationstep)):
            xnew = timetools.TOY(date)
            for idx_1, x_1 in enumerate(toys):
                if x_1 > xnew:
                    idx_0 = idx_1-1
                    x_0 = toys[idx_0]
                    break
            else:
                idx_0 = -1
                idx_1 = 0
                x_0 = toys[idx_0]
                x_1 = toys[idx_1]
            ratios[tdx, idx_1] = (xnew-x_0)/(x_1-x_0)
            ratios[tdx, idx_0] = 1.-ratios[tdx, idx_1]

    def _getshape(self):
        return tuple(int(sub) for sub in self.ratios.shape)

    def _setshape(self, shape):
        try:
            shape = (int(shape),)
        except TypeError:
            pass
        shp = list(shape)
        shp[0] = timetools.Period('366d')/self.simulationstep
        shp[0] = int(numpy.ceil(round(shp[0], 10)))
        getattr(self.fastaccess, self.name).ratios = numpy.zeros(
            shp, dtype=float)

    shape = property(
        _getshape,
        doc='The shape of array |anntools.SeasonalANN.ratios|.')

    @property
    def toys(self):
        """A sorted |tuple| of all contained |TOY| objects."""
        return tuple(toy for (toy, ann) in self)

    @property
    def anns(self):
        """A sorted |tuple| of all contained |anntools.ANN| objects."""
        return tuple(ann for (toy, ann) in self)

    @property
    def ratios(self):
        """Ratios for weighting the single neural network outputs."""
        return numpy.asarray(self._sann.ratios)

    @property
    def _sann(self):
        sann = self.__sann
        if sann:
            return sann
        else:
            raise RuntimeError(
                'The seasonal neural network collection `%s` of '
                'element `%s` has not been properly prepared so far.'
                % (self.name, objecttools.devicename(self)))

    @property
    def nmb_inputs(self):
        """Number of input values of all neural networks."""
        return self._sann.nmb_inputs

    @property
    def inputs(self):
        """General input data for all neural networks."""
        return numpy.asarray(self._sann.inputs)

    @property
    def nmb_outputs(self):
        """Number of output values of all neural networks."""
        return self._sann.nmb_outputs

    @property
    def outputs(self):
        """Weighted output of the individual neural networks."""
        return numpy.asarray(self._sann.outputs)

    def process_actual_input(self, idx_toy):
        """Calculate the network output values based on the input values
        defined previously for the given index referencing the actual
        time of year.
        """
        self._sann.process_actual_input(idx_toy)

    def plot(self, xmin, xmax, idx_input=0, idx_output=0, points=100,
             **kwargs):
        """Call method |ANN.plot| of all |anntools.ANN| objects
        handled bythe actual |anntools.SeasonalANN| object.
        """
        for toy, ann_ in self:
            ann_.plot(xmin, xmax,
                      idx_input=idx_input, idx_output=idx_output,
                      points=points,
                      label=str(toy),
                      **kwargs)
        pyplot.legend()

    def __getattribute__(self, name):
        if name.startswith('toy_'):
            try:
                try:
                    return self._toy2ann[timetools.TOY(name)]
                except KeyError:
                    raise AttributeError(
                        'No neural network is registered under '
                        'a TOY object named `%s`.'
                        % timetools.TOY(name))
            except BaseException:
                objecttools.augment_excmessage(
                    'While trying to look up for a neural network '
                    'handled by the seasonal neural network collection '
                    '`%s` of element `%s` based on name `%s`'
                    % (self.name, objecttools.devicename(self), name))
        else:
            return object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        if name.startswith('toy_'):
            try:
                if not isinstance(value, abctools.ANNABC):
                    raise TypeError(
                        '%s has been given, but a value of type '
                        '`ANN` is required.'
                        % objecttools.value_of_type(value).capitalize())
                self._toy2ann[timetools.TOY(name)] = value
                self.refresh()
            except BaseException:
                objecttools.augment_excmessage(
                    'While trying to assign a new neural network to '
                    'the seasonal neural network collection `%s` of '
                    'element `%s` based on name `%s`'
                    % (self.name, objecttools.devicename(self), name))
        else:
            object.__setattr__(self, name, value)

    def __delattr__(self, name):
        if name.startswith('toy_'):
            try:
                try:
                    del self._toy2ann[timetools.TOY(name)]
                except KeyError:
                    raise AttributeError(
                        'No neural network is registered under '
                        'a TOY object named `%s`.'
                        % timetools.TOY(name))
                self.refresh()
            except BaseException:
                objecttools.augment_excmessage(
                    'While trying to remove a new neural network from '
                    'the seasonal neural network collection `%s` of '
                    'element `%s` based on name `%s`'
                    % (self.name, objecttools.devicename(self), name))
        else:
            object.__delattr__(self, name)

    def __iter__(self):
        for toy, ann_ in sorted(self._toy2ann.items()):
            yield (toy, ann_)

    def __repr__(self):
        if not self:
            return self.name+'()'
        elif (len(self) == 1) and (self.toys[0] == timetools.TOY('1_1_0_0_0')):
            return self.anns[0].assignrepr('%s(' % self.name) + ')'
        lines = []
        blanks = ' '*(len(self.name)+1)
        for idx, (toy, ann_) in enumerate(self):
            if idx == 0:
                prefix = '%s(%s=' % (self.name, toy)
            else:
                prefix = '%s%s=' % (blanks, toy)
            lines.append(ann_.assignrepr(prefix))
        lines[-1] += ')'
        return ',\n'.join(lines)

    def __len__(self):
        return len(self._toy2ann)

    def __dir__(self):
        """
        >>> from hydpy import SeasonalANN, ann
        >>> seasonalann = SeasonalANN()
        >>> seasonalann(ann(nmb_inputs=1, nmb_neurons=(1,), nmb_outputs=1,
        ...                 weights_input=0.0, weights_output=0.0,
        ...                 intercepts_hidden=0.0, intercepts_output=1.0))
        >>> from hydpy.core.objecttools import assignrepr_values
        >>> print(assignrepr_values(sorted(dir(seasonalann)), '', 70))
        NDIM, SPAN, TIME, TYPE, anns, connect, fastaccess, inputs, name,
        nmb_inputs, nmb_outputs, outputs, parameterstep, plot,
        process_actual_input, ratios, refresh, shape, simulationstep, subpars,
        toy_1_1_0_0_0, toys, verify
        """
        return objecttools.dir_(self) + [str(toy) for toy in self.toys]


abctools.ParameterABC.register(SeasonalANN)
abctools.SeasonalANNABC.register(SeasonalANN)


autodoctools.autodoc_module()
