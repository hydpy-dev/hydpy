# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools


class NmbRuns(parametertools.SolverParameter):
    """The number of (repeated) runs of the |RunModel.RUN_METHODS| of the current
    application model per simulation step [-].

    Model developers need to subclass |NmbRuns| for each application model to define a
    suitable `INIT` value.
    """

    NDIM = 0
    TYPE = int
    TIME = None
    SPAN = (1, None)


class ToleranceWaterLevel(parametertools.SolverParameter):
    """Acceptable water level error for determining the reference water level [m]."""

    #  ToDo: find a way to determine a reasonable tolerance value automatically
    NDIM = 0
    TYPE = float
    TIME = None
    SPAN = (0.0, None)
    INIT = 0.0


class ToleranceDischarge(parametertools.SolverParameter):
    """Acceptable discharge error for determining the reference water level [m³/s]."""

    #  ToDo: find a way to determine a reasonable tolerance value automatically
    NDIM = 0
    TYPE = float
    TIME = None
    SPAN = (0.0, None)
    INIT = 1e-10
