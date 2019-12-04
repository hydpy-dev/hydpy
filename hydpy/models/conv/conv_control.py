# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from standard library
from typing import *
# ...from site-packages
import numpy
# ...from HydPy
from hydpy.core import devicetools
from hydpy.core import parametertools
from hydpy.core import variabletools


class Coordinates(parametertools.Parameter):
    """Base class for |InputCoordinates| and |OutputCoordinates|.

    We use the derived class |InputCoordinates| as an example:

    >>> from hydpy.models.conv import *
    >>> parameterstep()

    |Coordinates| subclasses define 2-dimensional sequences.  Hence, we
    must define their shape first:

    >>> inputcoordinates
    inputcoordinates(?)
    >>> inputcoordinates.values
    Traceback (most recent call last):
    ...
    AttributeError: Shape information for variable `inputcoordinates` \
can only be retrieved after it has been defined.

    However, you usually do this automatically when assigning new
    values.  Use keyword arguments to define the names of the relevant
    input nodes as well as their coordinates:

    >>> inputcoordinates(in1=(1.0, 3.0))
    >>> inputcoordinates
    inputcoordinates(in1=(1.0, 3.0))
    >>> inputcoordinates.values
    array([[ 1.,  3.]])

    Defining new coordinates removes the old ones:

    >>> inputcoordinates(in2=(2.0, 4.0),
    ...                  in0=(3.0, 5.0),
    ...                  in3=(4.0, 6.0))
    >>> inputcoordinates
    inputcoordinates(in2=(2.0, 4.0),
                     in0=(3.0, 5.0),
                     in3=(4.0, 6.0))
    >>> inputcoordinates.values
    array([[ 2.,  4.],
           [ 3.,  5.],
           [ 4.,  6.]])

    You are free to change individual coordinate values (the rows of the
    data array contain the different value pairs; the row order
    corresponds to the definition order when "calling" the parameter):

    >>> inputcoordinates.values[1, 0] = 9.0
    >>> inputcoordinates
    inputcoordinates(in2=(2.0, 4.0),
                     in0=(9.0, 5.0),
                     in3=(4.0, 6.0))

    The attribute `nodes` stores the correctly ordered nodes:

    >>> inputcoordinates.nodes
    (Node("in2", variable="Q"), Node("in0", variable="Q"), \
Node("in3", variable="Q"))
    """
    NDIM, TYPE, TIME, SPAN = 2, float, None, (None, None)

    def __init__(self, subvars: variabletools.SubgroupType):
        super().__init__(subvars)
        self.nodes: Tuple[devicetools.Node, ...] = ()

    def __call__(self, *args, **kwargs) -> None:
        nodes = []
        coordinates = numpy.empty((len(kwargs), 2), dtype=float)
        for idx, (name, values) in enumerate(kwargs.items()):
            nodes.append(devicetools.Node(name))
            coordinates[idx, :] = values
        self.nodes = tuple(nodes)
        self.__hydpy__set_shape__((len(nodes), 2))
        self.__hydpy__set_value__(coordinates)

    def __repr__(self) -> str:
        prefix = f'{self.name}('
        blanks = ' '*len(prefix)
        lines = []
        if self.nodes:
            for idx, node in enumerate(self.nodes):
                entry = f'{node.name}={tuple(self.values[idx, :])}'
                if not idx:
                    lines.append(f'{prefix}{entry}')
                else:
                    lines.append(f'{blanks}{entry}')
                if idx < len(self.nodes)-1:
                    lines[-1] += ','
                else:
                    lines[-1] += ')'
            return '\n'.join(lines)
        return f'{prefix}?)'


class InputCoordinates(Coordinates):
    """Coordinates of the inlet nodes."""


class OutputCoordinates(Coordinates):
    """Coordinates of the outlet nodes."""


class MaxNmbInputs(parametertools.Parameter):
    """The maximum number of input locations to be taken into account for
    interpolating the values of a specific output location [-].

    When passing no value, parameter |MaxNmbInputs| queries it from the shape
    of parameter |InputCoordinates|:

    >>> from hydpy.models.conv import *
    >>> parameterstep()
    >>> inputcoordinates(in2=(2.0, 4.0),
    ...                  in0=(3.0, 5.0),
    ...                  in3=(4.0, 6.0))
    >>> maxnmbinputs()
    >>> maxnmbinputs
    maxnmbinputs(3)

    You can define alternative values manually:

    >>> maxnmbinputs(2)
    >>> maxnmbinputs
    maxnmbinputs(2)
    """
    NDIM, TYPE, TIME, SPAN = 0, int, None, (1, None)

    def __call__(self, *args, **kwargs):
        if not args and not kwargs:
            super().__call__(self.subpars.inputcoordinates.shape[0])
        else:
            super().__call__(*args, **kwargs)

    def trim(self, lower=None, upper=None):
        """Assure that the value of |MaxNmbInputs| does not exceed the
        number of available input locations.

        >>> from hydpy.models.conv import *
        >>> parameterstep()
        >>> inputcoordinates(in2=(2.0, 4.0),
        ...                  in0=(3.0, 5.0),
        ...                  in3=(4.0, 6.0))
        >>> maxnmbinputs(0)
        Traceback (most recent call last):
        ...
        ValueError: The value `0` of parameter `maxnmbinputs` of \
element `?` is not valid.
        >>> maxnmbinputs(4)
        Traceback (most recent call last):
        ...
        ValueError: The value `4` of parameter `maxnmbinputs` of \
element `?` is not valid.
        """
        if upper is None:
            upper = self.subpars.inputcoordinates.shape[0]
        super().trim(lower, upper)
