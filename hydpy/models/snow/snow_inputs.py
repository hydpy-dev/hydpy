# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools


class P(sequencetools.InputSequence):
    """Precipitation [mm/T]."""

    NDIM, NUMERIC = 0, False
    STANDARD_NAME = sequencetools.StandardInputNames.PRECIPITATION


class T(sequencetools.InputSequence):
    """Mean air temperature [°C]."""

    NDIM, NUMERIC = 0, False
    STANDARD_NAME = sequencetools.StandardInputNames.AIR_TEMPERATURE


class TMin(sequencetools.InputSequence):
    """Minimum air temperature [°C]."""

    NDIM, NUMERIC = 0, False
    STANDARD_NAME = sequencetools.StandardInputNames.MINIMUM_AIR_TEMPERATURE


class TMax(sequencetools.InputSequence):
    """Maximum air temperature [°C]."""

    NDIM, NUMERIC = 0, False
    STANDARD_NAME = sequencetools.StandardInputNames.MAXIMUM_AIR_TEMPERATURE
