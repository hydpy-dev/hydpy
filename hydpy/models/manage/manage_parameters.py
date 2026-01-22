# pylint: disable=missing-module-docstring

# import...
# ...from site-packages
import numpy

# ...from HydPy
from hydpy.core import parametertools


class Parameter1D(parametertools.Parameter):
    """ToDo [-]."""

    NDIM = 1

    def __hydpy__let_par_set_shape__(self, p: parametertools.NmbParameter, /) -> None:
        self.shape = p.value

    def __call__(self, *args, **kwargs) -> None:
        self.values = numpy.nan
        for i, name in enumerate(self.subpars.pars.model.sourcenames):
            self.values[i] = kwargs[name]
