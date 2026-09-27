# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools
from hydpy.core import variabletools
from hydpy.core.typingtools import *


class Exchange(sequencetools.InputSequence):
    """ToDo The water level at two locations [m]."""

    NDIM = 0

