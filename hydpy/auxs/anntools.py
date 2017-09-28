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
    """Simple 1-layer feed forward artificial neural network.

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
    >>> ann(nmb_inputs=1, nmb_neurons=1, nmb_outputs=1,
    ...     weights_input=4.0, weights_output=3.0,
    ...     intercepts_input=-16.0, intercepts_output=-1.0)

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
    networks also (manual tests have been performed in a spreadsheet program):

    >>> ann.nmb_inputs = 3
    >>> ann.nmb_neurons = 4
    >>> ann.nmb_outputs = 2
    >>> ann.weights_input = numpy.array([[ 0.2,  0.9, -0.5],
    ...                                  [-0.1,  0.2, -1.0],
    ...                                  [-1.7,  0.8,  2.3],
    ...                                  [ 0.6, -0.0, -0.4]])
    >>> ann.weights_output = numpy.array([[ 0.0,  2.0],
    ...                                   [-0.5,  1.0],
    ...                                   [ 0.4,  2.4],
    ...                                   [ 0.8, -0.9]])
    >>> ann.intercepts_input = numpy.array([ 0.9,  0.0, -0.4, -0.2])
    >>> ann.intercepts_output = numpy.array([ 1.3, -2.0])
    >>> ann.inputs = numpy.array([-0.1,  1.3,  1.6])
    >>> ann.process_actual_input()
    >>> round_(ann.outputs)
    1.822222, 1.876983
    """

    def __init__(self):
        self.subpars = None
        self.fastaccess = type('JustForDemonstrationPurposes', (),
                               {self.name: None})()
        self._cann = annutils.ANN()

    def connect(self, subpars):
        self.subpars = subpars
        self.fastaccess = subpars.fastaccess
        setattr(self.fastaccess, self.name, self._cann)

    @property
    def name(self):
        return objecttools.classname(self).lower()

    def __call__(self, nmb_inputs=1, nmb_neurons=1, nmb_outputs=1,
                 weights_input=None, weights_output=None,
                 intercepts_input=None, intercepts_output=None):
        self._cann.nmb_inputs = nmb_inputs
        self._cann.nmb_neurons = nmb_neurons
        self._cann.nmb_outputs = nmb_outputs
        self.weights_input = weights_input
        self.weights_output = weights_output
        self.intercepts_input = intercepts_input
        self.intercepts_output = intercepts_output
        del self.inputs
        del self.outputs

    def _update_shapes(self):
        del self.weights_input
        del self.weights_output
        del self.intercepts_input
        del self.intercepts_output
        del self.inputs
        del self.outputs

    def _get_nmb_inputs(self):
        """Number of input nodes."""
        return self._cann.nmb_inputs

    def _set_nmb_inputs(self, value):
        self._cann.nmb_inputs = int(value)
        self._update_shapes()

    nmb_inputs = property(_get_nmb_inputs, _set_nmb_inputs)

    def _get_nmb_neurons(self):
        """Number of neurons of the inner layer."""
        return self._cann.nmb_neurons

    def _set_nmb_neurons(self, value):
        self._cann.nmb_neurons = int(value)
        self._update_shapes()

    nmb_neurons = property(_get_nmb_neurons, _set_nmb_neurons)

    def _get_nmb_outputs(self):
        """Number of output nodes."""
        return self._cann.nmb_outputs

    def _set_nmb_outputs(self, value):
        self._cann.nmb_outputs = int(value)
        self._update_shapes()

    nmb_outputs = property(_get_nmb_outputs, _set_nmb_outputs)

    def _get_weights_input(self):
        """Weights between all input nodes and neurons.

        The neurons and the intput nodes are varied on the first axis and
        on the second axis of the 2-dimensional array:

        >>> from hydpy.auxs.anntools import ANN
        >>> ann = ANN()
        >>> ann(nmb_inputs=2, nmb_neurons=3)
        >>> ann.weights_input
        array([[ 0.,  0.],
               [ 0.,  0.],
               [ 0.,  0.]])

        It is allowed to set values via slicing:

        >>> ann.weights_input[:, 0] = 1.
        >>> ann.weights_input
        array([[ 1.,  0.],
               [ 1.,  0.],
               [ 1.,  0.]])

        If possible, type conversions are performed:

        >>> ann.weights_input = '2'
        >>> ann.weights_input
        array([[ 2.,  2.],
               [ 2.,  2.],
               [ 2.,  2.]])

        One can assign whole matrices directly:

        >>> import numpy
        >>> ann.weights_input = numpy.eye(3)[:, :-1]
        >>> ann.weights_input
        array([[ 1.,  0.],
               [ 0.,  1.],
               [ 0.,  0.]])

        One can also delete the values contained in the array:

        >>> del ann.weights_input
        >>> ann.weights_input
        array([[ 0.,  0.],
               [ 0.,  0.],
               [ 0.,  0.]])

        Errors like wrong shapes (or unconvertible inputs) result in error
        messages:

        >>> ann.weights_input = numpy.eye(3)
        Traceback (most recent call last):
        ...
        ValueError: While trying to set the input weights of the artificial neural network `ann` of element `?`, the following error occured: could not broadcast input array from shape (3,3) into shape (3,2)
        """
        return numpy.asarray(self._cann.weights_input)

    def _set_weights_input(self, values):
        if values is None:
            self._del_weights_input()
        else:
            try:
                self._cann.weights_input = numpy.full(
                    (self.nmb_neurons, self.nmb_inputs), values, dtype=float)
            except BaseException:
                objecttools.augmentexcmessage(
                    'While trying to set the input weights of the artificial '
                    'neural network `%s` of element `%s`'
                    % (self.name, objecttools.devicename(self)))

    def _del_weights_input(self):
        self._cann.weights_input = numpy.zeros((self.nmb_neurons,
                                                self.nmb_inputs))

    weights_input = property(_get_weights_input,
                             _set_weights_input,
                             _del_weights_input)

    def _get_weights_output(self):
        """Weights between all neurons and output nodes.

        The neurons and the output nodes are varied on the first axis and
        on the second axis of the 2-dimensional array:

        >>> from hydpy.auxs.anntools import ANN
        >>> ann = ANN()
        >>> ann(nmb_outputs=2, nmb_neurons=3)
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
        >>> ann.weights_output = numpy.eye(3)[:, :-1]
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
        """
        return numpy.asarray(self._cann.weights_output)

    def _set_weights_output(self, values):
        if values is None:
            self._del_weights_output()
        else:
            try:
                self._cann.weights_output = numpy.full(
                    (self.nmb_neurons, self.nmb_outputs), values, dtype=float)
            except BaseException:
                objecttools.augmentexcmessage(
                    'While trying to set the output weights of the artificial '
                    'neural network `%s` of element `%s`'
                    % (self.name, objecttools.devicename(self)))

    def _del_weights_output(self):
        self._cann.weights_output = numpy.zeros((self.nmb_neurons,
                                                 self.nmb_outputs))

    weights_output = property(_get_weights_output,
                              _set_weights_output,
                              _del_weights_output)

    def _get_intercepts_input(self):
        """Intercepts of all neurons.

        All intercepts are handled in a 1-dimensional array:

        >>> from hydpy.auxs.anntools import ANN
        >>> ann = ANN()
        >>> ann(nmb_neurons=3)
        >>> ann.intercepts_input
        array([ 0.,  0.,  0.])

        It is allowed to set values via slicing:

        >>> ann.intercepts_input[1:] = 1.
        >>> ann.intercepts_input
        array([ 0.,  1.,  1.])

        If possible, type conversions are performed:

        >>> ann.intercepts_input = '2'
        >>> ann.intercepts_input
        array([ 2.,  2.,  2.])

        One can assign whole matrices directly:

        >>> import numpy
        >>> ann.intercepts_input = [1.0, 3.0, 2.0]
        >>> ann.intercepts_input
        array([ 1.,  3.,  2.])

        One can also delete the values contained in the array:

        >>> del ann.intercepts_input
        >>> ann.intercepts_input
        array([ 0.,  0.,  0.])

        Errors like wrong shapes (or unconvertible inputs) result in error
        messages:

        >>> ann.intercepts_input = [1.0, 3.0]
        Traceback (most recent call last):
        ...
        ValueError: While trying to set the neuron related intercepts of the artificial neural network `ann` of element `?`, the following error occured: could not broadcast input array from shape (2) into shape (3)
        """
        return numpy.asarray(self._cann.intercepts_input)

    def _set_intercepts_input(self, values):
        if values is None:
            self._del_intercepts_input()
        else:
            try:
                self._cann.intercepts_input = numpy.full(self.nmb_neurons,
                                                         values, dtype=float)
            except BaseException:
                objecttools.augmentexcmessage(
                    'While trying to set the neuron related intercepts of '
                    'the artificial neural network `%s` of element `%s`'
                    % (self.name, objecttools.devicename(self)))

    def _del_intercepts_input(self):
        self._cann.intercepts_input = numpy.zeros(self.nmb_neurons)

    intercepts_input = property(_get_intercepts_input,
                                _set_intercepts_input,
                                _del_intercepts_input)

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
        """
        return numpy.asarray(self._cann.intercepts_output)

    def _set_intercepts_output(self, values):
        if values is None:
            self._del_intercepts_output()
        else:
            try:
                self._cann.intercepts_output = numpy.full(self.nmb_outputs,
                                                          values, dtype=float)
            except BaseException:
                objecttools.augmentexcmessage(
                    'While trying to set the output node related intercepts '
                    'of the artificial neural network `%s` of element `%s`'
                    % (self.name, objecttools.devicename(self)))

    def _del_intercepts_output(self):
        self._cann.intercepts_output = numpy.zeros(self.nmb_outputs)

    intercepts_output = property(_get_intercepts_output,
                                 _set_intercepts_output,
                                 _del_intercepts_output)

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

    def process_actual_input(self):
        """Calculates the network output values based on the input values
        defined previously.

        For more information see the documentation on class :class:`ANN`.
        """
        self._cann.process_actual_input()


autodoctools.autodoc_module()