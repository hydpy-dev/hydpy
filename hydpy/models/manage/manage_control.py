# pylint: disable=missing-module-docstring

# import...
# ...from site-packages
import numpy

# ...from HydPy
from hydpy.core import parametertools

# ...from manage
from hydpy.models.manage import manage_parameters


class NmbSources(parametertools.NmbParameter):
    """ToDo [-]."""

    SPAN = (1, None)


class Active(manage_parameters.Parameter1D):
    """ToDo [-]."""

    TYPE, TIME, SPAN = bool, None, (False, True)

    def __call__(self, *args, **kwargs) -> None:
        self.values = False
        values = self.values
        sourcenames = self.subpars.pars.model.sourcenames
        for idx, (name, active) in enumerate(sorted(kwargs.items())):
            sourcenames.append(name)
            values[idx] = active
        self.subpars.pars.derived.nmbactivesources = numpy.sum(values)


class VolumeMin(manage_parameters.Parameter1D):
    """ToDo [million m³]."""

    TYPE, TIME, SPAN = float, None, (0.0, None)

    # def trim(self, lower=None, upper=None) -> bool:  # ToDo


class VolumeMax(manage_parameters.Parameter1D):
    """ToDo [million m³]."""

    TYPE, TIME, SPAN = float, None, (0.0, None)

    # def trim(self, lower=None, upper=None) -> bool:  # ToDo


class ReleaseMax(manage_parameters.Parameter1D):
    """ToDo [m³/s]."""

    TYPE, TIME, SPAN = float, None, (0.0, None)


class Demand(parametertools.CallbackParameter):
    """ToDo [m³/s]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
