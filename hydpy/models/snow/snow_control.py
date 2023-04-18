# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# from site-packages

# ...from HydPy
from hydpy.core import exceptiontools
from hydpy.core import objecttools
from hydpy.core import parametertools

# ...from snow


class ZInputs(parametertools.Parameter):
    """Elevation of input precipitation and temperature station [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)


class NSnowLayers(parametertools.Parameter):
    """Number of snow layers  [-].

    Note that |NSnowLayers| determines the length of the 1-dimensional
    HydPy-Snow parameters and sequences.  This requires that the value of
    the respective |NSnowLayers| instance is set before any of the values
    of these 1-dimensional parameters or sequences are set.  Changing the
    value of the |NSnowLayers| instance necessitates setting their values
    again.

    Examples:

        >>> from hydpy.models.snow import *
        >>> parameterstep('1d')
        >>> nsnowlayers(5)
        >>> meanansolidprecip.shape
        (5,)
        >>> layerarea.shape
        (5,)
        >>> derived.gthresh.shape
        (5,)
    """

    # todo Muss Länge mit 101 begrenzt sein?
    NDIM, TYPE, TIME, SPAN = 0, int, None, (1, 101)

    def __call__(self, *args, **kwargs):
        """The prefered way to pass a value to |NmbZones| instances within
        parameter control files.  Sets the shape of most 1-dimensional
        snow parameter objects and sequence objects
        additionally.
        """
        old_value = exceptiontools.getattr_(self, "value", None)
        super().__call__(*args, **kwargs)
        new_value = self.value

        if new_value != old_value:
            for subpars in self.subpars.pars.model.parameters:
                for par in subpars:
                    if (par.NDIM > 0) and (
                        par.name
                        not in (
                            "gradtmean",
                            "gradtmin",
                            "gradtmax",
                        )
                    ):
                        par.shape = new_value
            for subseqs in self.subpars.pars.model.sequences:
                for seq in subseqs:
                    if seq.NDIM > 0:
                        seq.shape = self.value


class ZLayers(parametertools.Parameter):
    """Height of each snow layer [m]

    The height for each snow layer can be set directly:

    >>> from hydpy.models.snow import *
    >>> parameterstep("1d")
    >>> nsnowlayers(5)
    >>> zlayers(400.0, 1000.0, 2000.0, 3000.0, 4000.0)
    >>> zlayers
    zlayers(400.0, 1000.0, 2000.0, 3000.0, 4000.0)

    Alternatively, the z values can be set using the hypsodata option. An array of
    length 101 must then be specified, containing min, q01 to q99 and max of the
    catchment elevation distribution [m].

    >>> zlayers(hypsodata =
    ...     [ 471. ,  656.2,  749.4,  808. ,  868. ,  908. ,  948. ,  991.2,
    ...       1022.6, 1052. , 1075. , 1101. , 1120.4, 1147.6, 1166.8, 1185. ,
    ...       1210. , 1229. , 1242. , 1259. , 1277. , 1291. , 1305.4, 1318. ,
    ...       1328. , 1340. , 1350.2, 1366.4, 1377. , 1389. , 1402. , 1413. ,
    ...       1424. , 1435. , 1448.8, 1460. , 1474.2, 1487.4, 1498. , 1511. ,
    ...       1523. , 1538. , 1551.4, 1564. , 1573. , 1584. , 1593. , 1603.4,
    ...       1614. , 1626. , 1636. , 1648. , 1661.4, 1672. , 1682. , 1693. ,
    ...       1705. , 1715. , 1724. , 1733. , 1742. , 1751. , 1759. , 1768. ,
    ...       1777. , 1787. , 1795. , 1802. , 1813. , 1822. , 1832. , 1840. ,
    ...       1849. , 1857.6, 1867. , 1874. , 1882.2, 1891. , 1899. , 1908.8,
    ...       1919. , 1931. , 1941. , 1948. , 1957.8, 1965. , 1976. , 1987. ,
    ...       1999. , 2013. , 2027. , 2047. , 2058. , 2078. , 2097. , 2117. ,
    ...       2146. , 2177. , 2220.6, 2263.6, 2539. ])
    >>> zlayers
    zlayers(1075.0, 1402.0, 1636.0, 1832.0, 2027.0)
    >>> layerarea(0.6, 0.1, 0.1, 0.1, 0.1)
    >>> from hydpy import round_
    >>> round(zlayers.average_values(), 1)
    1334.7

    >>> nsnowlayers(70)
    >>> zlayers(hypsodata =
    ...     [ 471. ,  656.2,  749.4,  808. ,  868. ,  908. ,  948. ,  991.2,
    ...      1022.6, 1052. , 1075. , 1101. , 1120.4, 1147.6, 1166.8, 1185. ,
    ...      1210. , 1229. , 1242. , 1259. , 1277. , 1291. , 1305.4, 1318. ,
    ...      1328. , 1340. , 1350.2, 1366.4, 1377. , 1389. , 1402. , 1413. ,
    ...      1424. , 1435. , 1448.8, 1460. , 1474.2, 1487.4, 1498. , 1511. ,
    ...      1523. , 1538. , 1551.4, 1564. , 1573. , 1584. , 1593. , 1603.4,
    ...      1614. , 1626. , 1636. , 1648. , 1661.4, 1672. , 1682. , 1693. ,
    ...      1705. , 1715. , 1724. , 1733. , 1742. , 1751. , 1759. , 1768. ,
    ...      1777. , 1787. , 1795. , 1802. , 1813. , 1822. , 1832. , 1840. ,
    ...      1849. , 1857.6, 1867. , 1874. , 1882.2, 1891. , 1899. , 1908.8,
    ...      1919. , 1931. , 1941. , 1948. , 1957.8, 1965. , 1976. , 1987. ,
    ...      1999. , 2013. , 2027. , 2047. , 2058. , 2078. , 2097. , 2117. ,
    ...      2146. , 2177. , 2220.6, 2263.6, 2539. ])
    >>> zlayers
    zlayers(471.0, 749.4, 868.0, 948.0, 1022.6, 1075.0, 1120.4, 1166.8,
            1210.0, 1242.0, 1277.0, 1305.4, 1328.0, 1350.2, 1377.0, 1402.0,
            1424.0, 1448.8, 1474.2, 1498.0, 1523.0, 1551.4, 1573.0, 1593.0,
            1614.0, 1636.0, 1661.4, 1682.0, 1705.0, 1724.0, 1742.0, 1751.0,
            1759.0, 1768.0, 1777.0, 1787.0, 1795.0, 1802.0, 1813.0, 1822.0,
            1832.0, 1840.0, 1849.0, 1857.6, 1867.0, 1874.0, 1882.2, 1891.0,
            1899.0, 1908.8, 1919.0, 1931.0, 1941.0, 1948.0, 1957.8, 1965.0,
            1976.0, 1987.0, 1999.0, 2013.0, 2027.0, 2047.0, 2058.0, 2078.0,
            2097.0, 2117.0, 2146.0, 2177.0, 2220.6, 2263.6)

    Only the keyword hypsodata is allowed:

    >>> zlayers(option="hypsodata")
    Traceback (most recent call last):
    ...
    ValueError: Besides the standard keyword arguments, parameter `zlayers` of \
element `?` does only support the keyword argument `hypsodata`, but `option` is given.

    The hypsodata argument has to be of length 101:

    >>> zlayers(hypsodata=[200.0, 300.0, 400.0])
    Traceback (most recent call last):
    ...
    ValueError: If the hypsodata option is to be used exactly 101 values must be \
given. But 3 values were given

    If more than one keyword argument is given, an error is raised:

    >>> zlayers(option="hypsodata", hypsodata=[200.0, 300.0, 400.0])
    Traceback (most recent call last):
    ...
    ValueError: Parameter `zlayers` of element `?` does not accept multiple keyword \
arguments, but the following are given: option and hypsodata
    """

    CONTROLPARAMETERS = ()
    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)
    INIT = 0.0

    def __call__(self, *args, **kwargs):
        try:
            super().__call__(*args, **kwargs)
        except NotImplementedError:
            if len(kwargs) > 1:
                raise ValueError(
                    f"Parameter {objecttools.elementphrase(self)} does not "
                    f"accept multiple keyword arguments, but the following "
                    f"are given: {objecttools.enumeration(kwargs.keys())}"
                ) from None
            if "hypsodata" not in kwargs:
                raise ValueError(
                    f"Besides the standard keyword arguments, parameter "
                    f"{objecttools.elementphrase(self)} does only support "
                    f"the keyword argument `hypsodata`, but `{tuple(kwargs)[0]}` "
                    f"is given."
                ) from None
            con = self.subpars
            self.values = 0.0
            hypsodata = kwargs["hypsodata"]
            if len(hypsodata) != 101:
                raise ValueError(
                    f"If the hypsodata option is to be used exactly 101 values "
                    f"must be given. But {len(hypsodata)} values were given"
                ) from None
            nmoy = 100 // con.nsnowlayers
            nreste = 100 % con.nsnowlayers
            ncont = 0
            for ilayer in range(int(con.nsnowlayers)):
                if nreste > 0:
                    nn = nmoy + 1
                    nreste -= 1
                else:
                    nn = nmoy
                if nn <= 2:
                    self.values[ilayer] = hypsodata[ncont]
                elif nn > 2:
                    self.values[ilayer] = hypsodata[int(ncont + nn / 2.0)]
                ncont = ncont + nn

    @property
    def refweights(self):
        """Weights for calculating mean."""
        return self.subpars.layerarea


class LayerArea(parametertools.Parameter):
    """Area of snow layer as a percentage of total area [-]"""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, 1.0)


class GradP(parametertools.Parameter):
    """Altitude gradient precipitation [1/m]"""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)
    INIT = 0.00041


class GradTMean(parametertools.Parameter):
    """Array of length 366 : gradient of daily mean temperature for each day of year
    [°C/100m]."""

    # todo Monatswerte oder toy ?
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)

    def __call__(self, *args, **kwargs):
        """Set shape of GradTMean to 366"""
        self.shape = 366
        super().__call__(*args, **kwargs)


class GradTMin(parametertools.Parameter):
    """Array of length 366 : gradient of daily minimum temperature for each day of
    year [°C/100m]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0, None)

    def __call__(self, *args, **kwargs):
        """Set shape of GradTMin to 366"""
        self.shape = 366
        super().__call__(*args, **kwargs)


class GradTMax(parametertools.Parameter):
    """Array of length 366 : elevation gradient of daily maximum temperature for each
    day of year [°C/100m]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0, None)

    def __call__(self, *args, **kwargs):
        """Set shape of HypsoData to 366"""
        self.shape = 366
        super().__call__(*args, **kwargs)


class MeanAnSolidPrecip(parametertools.Parameter):
    """Mean annual solid precipitation [mm/a]"""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0, None)


class CN1(parametertools.Parameter):
    """weighting coefficient for snow pack thermal state [-]"""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0, None)


class CN2(parametertools.Parameter):
    """Degree-day melt coefficient [mm/°C/T]"""

    NDIM, TYPE, TIME, SPAN = 0, float, True, (0, None)


class CN3(parametertools.Parameter):
    """Accumulation threshold [mm]"""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0, None)


class CN4(parametertools.Parameter):
    """Percentage (between 0 and 1) of annual snowfall defining the melt threshold
    [-]"""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0, 1)
