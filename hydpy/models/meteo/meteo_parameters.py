# pylint: disable=missing-module-docstring

import abc

from hydpy.core import masktools
from hydpy.core import parametertools
from hydpy.models.meteo import meteo_variables


class ZipParameter1D(meteo_variables.MixinHRUs, parametertools.ZipParameter, abc.ABC):
    """Base class for 1-dimensional parameters that provide additional keyword-based
    zipping functionalities."""

    constants = {}
    mask = masktools.SubmodelIndexMask()
