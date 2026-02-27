# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools
from hydpy.core.typingtools import *

# ...from snow
from hydpy.models.snow import snow_parameters


class NLayers(parametertools.NmbParameter):
    """Number of snow layers  [-]."""

    TIME = None
    SPAN = (1, None)


class ZLayers(snow_parameters.Parameter1DLayers):
    """Height of each snow layer [m].

    You can use method |snow_model.BaseModel.prepare_layers| to determine the values of
    |ZLayers| based on the catchment's elevation distribution.
    """

    TIME = None


class LayerArea(snow_parameters.Parameter1DLayers):
    """Area of snow layer as a percentage of total area [-].

    Calling method |snow_model.BaseModel.prepare_layers| to determine the values of
    parameter |ZLayers| also sets all entries of parameter |LayerArea| to the same
    average value.
    """

    TIME = None
    SPAN = (0.0, 1.0)


class GradP(parametertools.Parameter):
    """Altitude gradient of precipitation [1/m]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    TIME = None
    INIT = 0.00041


class GradTMean(snow_parameters.Parameter1D366):
    """Altitude gradient of daily mean air temperature for each day of the year
    [°C/100m]."""

    TYPE: Final = float
    TIME = None
    SPAN = (0.0, None)


class GradTMin(snow_parameters.Parameter1D366):
    """Altitude gradient of daily minimum air temperature for each day of the year
    [°C/100m]."""

    TYPE: Final = float
    TIME = None
    SPAN = (0.0, None)


class GradTMax(snow_parameters.Parameter1D366):
    """Altitude gradient of daily maximum air temperature for each day of the year
    [°C/100m]."""

    TYPE: Final = float
    TIME = None
    SPAN = (0.0, None)


class MeanAnSolidPrecip(snow_parameters.Parameter1DLayers):
    """Mean annual solid precipitation [mm/a]."""

    TIME = None
    SPAN = (0.0, None)


class CN1(parametertools.Parameter):
    """Temporal weighting coefficient for the snow pack's thermal state [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    TIME = None
    SPAN = (0.0, 1.0)


class CN2(parametertools.Parameter):
    """Degree-day melt coefficient [mm/°C/T]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    TIME = True
    SPAN = (0.0, None)


class CN3(parametertools.Parameter):
    """Accumulation threshold [mm]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    TIME = None
    SPAN = (0.0, None)


class CN4(parametertools.Parameter):
    """Fraction of annual snowfall defining the melt threshold [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    TIME = None
    SPAN = (0.0, 1.0)


class Hysteresis(parametertools.Parameter):
    """Flag that indicates whether hysteresis of build-up and melting of the snow cover
    should be considered [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = bool
    TIME = None
    SPAN = (False, True)
    INIT = False
