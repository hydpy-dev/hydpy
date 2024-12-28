# pylint: disable=missing-module-docstring

from hydpy.core import sequencetools


class P(sequencetools.InputSequence):
    """Precipitation [mm]."""

    NDIM, NUMERIC = 0, False
    STANDARD_NAME = sequencetools.StandardInputNames.PRECIPITATION


class T(sequencetools.InputSequence):
    """Daily mean air temperature [°C]."""

    NDIM, NUMERIC = 0, False
    STANDARD_NAME = sequencetools.StandardInputNames.AIR_TEMPERATURE


class TMin(sequencetools.InputSequence):
    """Daily minimum air temperature [°C]."""

    # todo: check tmin < tmax?

    NDIM, NUMERIC = 0, False
    STANDARD_NAME = sequencetools.StandardInputNames.MINIMUM_AIR_TEMPERATURE


class TMax(sequencetools.InputSequence):
    """Daily maximum air temperature [°C]."""

    NDIM, NUMERIC = 0, False
    STANDARD_NAME = sequencetools.StandardInputNames.MAXIMUM_AIR_TEMPERATURE
