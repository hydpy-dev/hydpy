# -*- coding: utf-8 -*-
"""This module implements rudimantary artificial neural network tools,
required for some models implemented in the HydPy framework.

A note for developers: some of the implemented features are to be applied
during model simulations are in some other way performance-critical.  Hence,
the actual calculations are defined in the Cython extension module
:mod:`~hydpy.cythons.annutils`.
"""

# import...
# ...from standard library
from __future__ import division, print_function
# ...from site-packages
import numpy
# ...from HydPy
from hydpy.core import objecttools
from hydpy.core import autodoctools
from hydpy.cythons import annutils


class ANN(object):
    """Multi-layer feed forward artificial neural network.

    The applied activation function is the logistic function:

      :math:`f(x) = \\frac{1}{1+exp(-x)}`

    Class :class:`ANN` is intended to be subclassed for the derivation of
    very complex control parameters.  Its original purpose was to allow for
    defining arbitrary continuous relationsships between the water stored
    in a dam and the associated water stage (see model ...).  However,
    class :class:`ANN` can also be applied directly, as shown in the
    following examples.  But if you are looking for a flexible stand-alone
    artifical neural network implementation in Python, you will find much
    more general tools easily.

    Firstly, define the most single artificial neural network consisting of
    only one input node, neuron, and output node respectively, and pass
    some arbitrary network parameters:

    >>> from hydpy.auxs.anntools import ANN
    >>> ann = ANN()
    >>> ann(nmb_inputs=1, nmb_neurons=(1,), nmb_outputs=1,
    ...     weights_input=4.0, weights_output=3.0,
    ...     intercepts_hidden=-16.0, intercepts_output=-1.0)

    The following loop subsequently sets the values 0 to 8 as input values,
    performs the calculateion, and prints out the final output.  As to be
    expected, the results show the shape of the logistic function:

    >>> from hydpy.core.objecttools import round_
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

    A example for a multi layer networks is still missing...

    """

    def __init__(self):
        self.subpars = None
        self.fastaccess = objecttools.FastAccess()
        self._cann = annutils.ANN()

    def connect(self, subpars):
        self.subpars = subpars
        self.fastaccess = subpars.fastaccess
        setattr(self.fastaccess, self.name, self._cann)

    @property
    def name(self):
        return objecttools.classname(self).lower()

    def __call__(self, nmb_inputs=1, nmb_neurons=(1,), nmb_outputs=1,
                 weights_input=None, weights_output=None, weights_hidden=None,
                 intercepts_hidden=None, intercepts_output=None):
        self._cann.nmb_inputs = nmb_inputs
        self._cann.nmb_outputs = nmb_outputs
        self.nmb_neurons = nmb_neurons
        self.weights_input = weights_input
        self.weights_hidden = weights_hidden
        self.weights_output = weights_output
        self.intercepts_hidden = intercepts_hidden
        self.intercepts_output = intercepts_output
        del self.inputs
        del self.outputs
        self._update_hidden()

    def _update_shapes(self):
        del self.weights_input
        del self.weights_hidden
        del self.weights_output
        del self.intercepts_hidden
        del self.intercepts_output
        del self.inputs
        del self.outputs
        self._update_hidden()

    def _get_nmb_inputs(self):
        """Number of input nodes."""
        return self._cann.nmb_inputs

    def _set_nmb_inputs(self, value):
        self._cann.nmb_inputs = int(value)
        self._update_shapes()

    nmb_inputs = property(_get_nmb_inputs, _set_nmb_inputs)

    def _get_nmb_outputs(self):
        """Number of output nodes."""
        return self._cann.nmb_outputs

    def _set_nmb_outputs(self, value):
        self._cann.nmb_outputs = int(value)
        self._update_shapes()

    nmb_outputs = property(_get_nmb_outputs, _set_nmb_outputs)

    @property
    def nmb_layers(self):
        """Number of hidden layers."""
        return self._cann.nmb_layers

    def _get_nmb_neurons(self):
        """Number of neurons of the inner layers."""
        return tuple(numpy.asarray(self._cann.nmb_neurons))

    def _set_nmb_neurons(self, value):
        self._cann.nmb_neurons = numpy.array(value, dtype=int, ndmin=1)
        self._cann.nmb_layers = len(value)
        self._max_nmb_neurons = max(value)
        self._update_shapes()

    nmb_neurons = property(_get_nmb_neurons, _set_nmb_neurons)

    def _get_weights_input(self):
        """Weights between all input nodes and neurons of the first hidden
        layer.

        The input nodes and the neurons are varied on the first axis and
        on the second axis of the 2-dimensional array:

        >>> from hydpy.auxs.anntools import ANN
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
               [ 0.,  1.,  0.]])

        One can also delete the values contained in the array:

        >>> del ann.weights_input
        >>> ann.weights_input
        array([[ 0.,  0.,  0.],
               [ 0.,  0.,  0.]])

        Errors like wrong shapes (or unconvertible inputs) result in error
        messages:

        >>> ann.weights_input = numpy.eye(3)
        Traceback (most recent call last):
        ...
        ValueError: While trying to set the input weights of the artificial neural network `ann` of element `?`, the following error occured: could not broadcast input array from shape (3,3) into shape (2,3)

        The number of input weights is available as a property:

        >>> ann.nmb_weights_input
        6
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
                objecttools.augmentexcmessage(
                    'While trying to set the input weights of the artificial '
                    'neural network `%s` of element `%s`'
                    % (self.name, objecttools.devicename(self)))

    def _del_weights_input(self):
        self._cann.weights_input = numpy.zeros(self.shape_weights_input)

    weights_input = property(_get_weights_input,
                             _set_weights_input,
                             _del_weights_input)

    @property
    def shape_weights_input(self):
        """Shape of the array containing the input weights"""
        return (self.nmb_inputs, self.nmb_neurons[0])

    @property
    def nmb_weights_input(self):
        """Number of input weights."""
        return self.nmb_neurons[0]*self.nmb_inputs

    def _get_weights_output(self):
        """Weights between all neurons of the last hidden layer and the output
        nodes.

        The neurons and the output nodes are varied on the first axis and
        on the second axis of the 2-dimensional array:

        >>> from hydpy.auxs.anntools import ANN
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
        ValueError: While trying to set the output weights of the artificial neural network `ann` of element `?`, the following error occured: could not broadcast input array from shape (3,3) into shape (3,2)

        The number of output weights is available as a property:

        >>> ann.nmb_weights_output
        6
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
                objecttools.augmentexcmessage(
                    'While trying to set the output weights of the artificial '
                    'neural network `%s` of element `%s`'
                    % (self.name, objecttools.devicename(self)))

    def _del_weights_output(self):
        self._cann.weights_output = numpy.zeros(self.shape_weights_output)

    weights_output = property(_get_weights_output,
                              _set_weights_output,
                              _del_weights_output)

    @property
    def shape_weights_output(self):
        """Shape of the array containing the output weights"""
        return (self.nmb_neurons[-1], self.nmb_outputs)

    @property
    def nmb_weights_output(self):
        """Number of output weights."""
        return self.nmb_neurons[-1]*self.nmb_outputs

    def _get_weights_hidden(self):
        """Weights between between the neurons of the different hidden layers.

        The layers are varied on the first axis, the neurons of the respective
        upstream layer on the second axis and the neurons of the respective
        downstream layer on the third axis of a 3-dimensional array:

        >>> from hydpy.auxs.anntools import ANN
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
        ValueError: While trying to set the hidden weights of the artificial neural network `ann` of element `?`, the following error occured: could not broadcast input array from shape (3,2) into shape (2,3,3)

        The number of input weights is available as a property:

        >>> ann.nmb_weights_hidden
        12
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
                objecttools.augmentexcmessage(
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

    weights_hidden = property(_get_weights_hidden,
                              _set_weights_hidden,
                              _del_weights_hidden)

    @property
    def shape_weights_hidden(self):
        """Shape of the array containing the activations of the hidden neurons.
        """
        if self.nmb_layers > 1:
            return (self.nmb_layers-1,
                    self._max_nmb_neurons,
                    self._max_nmb_neurons)
        else:
            return (0, 0, 0)

    @property
    def nmb_weights_hidden(self):
        """Number of hidden weights."""
        nmb = 0
        for idx_layer in range(self.nmb_layers-1):
            nmb += self.nmb_neurons[idx_layer] * self.nmb_neurons[idx_layer+1]
        return nmb

    def _get_intercepts_hidden(self):
        """Intercepts of all neurons of the hidden layers.

        All intercepts are handled in a 1-dimensional array:

        >>> from hydpy.auxs.anntools import ANN
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
        ValueError: While trying to set the neuron related intercepts of the artificial neural network `ann` of element `?`, the following error occured: could not broadcast input array from shape (2) into shape (2,3)

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
                        self.shape_intercepts_hidden,  values, dtype=float)
            except BaseException:
                objecttools.augmentexcmessage(
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

    intercepts_hidden = property(_get_intercepts_hidden,
                                 _set_intercepts_hidden,
                                 _del_intercepts_hidden)

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

        >>> from hydpy.auxs.anntools import ANN
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
        ValueError: While trying to set the output node related intercepts of the artificial neural network `ann` of element `?`, the following error occured: could not broadcast input array from shape (2) into shape (3)

        The number of output intercepts is available as a property:

        >>> ann.nmb_intercepts_output
        3
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
                objecttools.augmentexcmessage(
                    'While trying to set the output node related intercepts '
                    'of the artificial neural network `%s` of element `%s`'
                    % (self.name, objecttools.devicename(self)))

    def _del_intercepts_output(self):
        self._cann.intercepts_output = numpy.zeros(
                                            self.shape_intercepts_output)

    intercepts_output = property(_get_intercepts_output,
                                 _set_intercepts_output,
                                 _del_intercepts_output)

    @property
    def shape_intercepts_output(self):
        """Shape if the array containing the intercepts of neurons of
        the hidden layers."""
        return (self.nmb_outputs,)

    @property
    def nmb_intercepts_output(self):
        """Number of output intercepts."""
        return self.nmb_outputs

    def _get_inputs(self):
        """Values of the input nodes.

        All input values are handled in a 1-dimensional array:

        >>> from hydpy.auxs.anntools import ANN
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
        ValueError: While trying to set the inputs of the artificial neural network `ann` of element `?`, the following error occured: could not broadcast input array from shape (2) into shape (3)
        """
        return numpy.asarray(self._cann.inputs)

    def _set_inputs(self, values):
        if values is None:
            self._del_inputs()
        else:
            try:
                self._cann.inputs = numpy.full(self.nmb_inputs,
                                               values, dtype=float)
            except BaseException:
                objecttools.augmentexcmessage(
                    'While trying to set the inputs of the artificial '
                    'neural network `%s` of element `%s`'
                    % (self.name, objecttools.devicename(self)))

    def _del_inputs(self):
        self._cann.inputs = numpy.zeros(self.nmb_inputs)

    inputs = property(_get_inputs, _set_inputs, _del_inputs)

    def _get_outputs(self):
        """Values of the output nodes.

        All output values are handled in a 1-dimensional array:

        >>> from hydpy.auxs.anntools import ANN
        >>> ann = ANN()
        >>> ann(nmb_outputs=3)
        >>> ann.outputs
        array([ 0.,  0.,  0.])

        It is not allowed to change output values manually:

        >>> ann.outputs = 1.0
        Traceback (most recent call last):
        ...
        AttributeError: can't set attribute
        """
        return numpy.asarray(self._cann.outputs)

    def _del_outputs(self):
        self._cann.outputs = numpy.zeros(self.nmb_outputs)

    outputs = property(_get_outputs, fdel=_del_outputs)

    def _get_inputs(self):
        """Values of the input nodes.

        All input values are handled in a 1-dimensional array:

        >>> from hydpy.auxs.anntools import ANN
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
        ValueError: While trying to set the inputs of the artificial neural network `ann` of element `?`, the following error occured: could not broadcast input array from shape (2) into shape (3)
        """
        return numpy.asarray(self._cann.inputs)

    def _set_inputs(self, values):
        if values is None:
            self._del_inputs()
        else:
            try:
                self._cann.inputs = numpy.full(self.nmb_inputs,
                                               values, dtype=float)
            except BaseException:
                objecttools.augmentexcmessage(
                    'While trying to set the inputs of the artificial '
                    'neural network `%s` of element `%s`'
                    % (self.name, objecttools.devicename(self)))

    def _del_inputs(self):
        self._cann.inputs = numpy.zeros(self.nmb_inputs)

    inputs = property(_get_inputs, _set_inputs, _del_inputs)

    def _update_hidden(self):
        nmb_neurons = numpy.asarray(self._cann.nmb_neurons)
        self._cann.neurons = numpy.zeros((self.nmb_layers, max(nmb_neurons)))

    def process_actual_input(self):
        """Calculates the network output values based on the input values
        defined previously.

        For more information see the documentation on class :class:`ANN`.
        """
        self._cann.process_actual_input()

    @property
    def nmb_weights(self):
        nmb = self.nmb_inputs*self.nmb_neurons[0]
        for idx_layer in range(self.nmb_layers-1):
            nmb += self.nmb_neurons[idx_layer]*self.nmb_neurons[idx_layer+1]
        nmb += self.nmb_neurons[-1]*self.nmb_outputs
        return nmb

    @property
    def nmb_intercepts(self):
        return (sum(self.nmb_neurons) + self.nmb_outputs)

    @property
    def nmb_parameters(self):
        return self.nmb_weights + self.nmb_intercepts

    def __repr__(self):
        lines = [(objecttools.assignrepr_value(
                self.nmb_inputs, 'ann(nmb_inputs=')+',')]
        lines.append(objecttools.assignrepr_tuple(
                self.nmb_neurons, '    nmb_neurons=')+',')
        lines.append(objecttools.assignrepr_value(
                self.nmb_outputs, '    nmb_outputs=')+',')
        lines.append(objecttools.assignrepr_list2(
                self.weights_input, '    weights_input=')+',')
        if self.nmb_layers > 1:
            lines.append(objecttools.assignrepr_list3(
                    self.weights_hidden, '    weights_hidden=')+',')
        lines.append(objecttools.assignrepr_list2(
                self.weights_output, '    weights_output=')+',')
        lines.append(objecttools.assignrepr_list2(
                self.intercepts_hidden, '    intercepts_hidden=')+',')
        lines.append(objecttools.assignrepr_list(
                self.intercepts_output, '    intercepts_output=')+')')
        return '\n'.join(lines)


autodoctools.autodoc_module()