# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from site-packages
import numpy

# ...from HydPy
import hydpy
from hydpy.core import parametertools

# ...from snow
from hydpy.models.snow import snow_control


class DOY(parametertools.DOYParameter):
    """References the "global" month of the year index array [-]."""

class ZLayers(parametertools.Parameter):
    """Elevation of the snow layers derived from |HypsoData| [m]"""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)

    CONTROLPARAMETERS = (
        snow_control.HypsoData,
        snow_control.NSnowLayers,
    )

    def update(self):
        """Update |ZLayers| based on |HypsoData|

        Number of snow layers = 5

        >>> from hydpy.models.snow import *
        >>> parameterstep('1d')
        >>> nsnowlayers(5)
        >>> hypsodata(471, 656.2, 749.4, 808, 868, 908, 948, 991.2, 1022.6, 1052, 1075,
        ...     1101, 1120.4, 1147.6, 1166.8, 1185, 1210, 1229, 1242, 1259, 1277, 1291,
        ...     1305.4, 1318, 1328, 1340, 1350.2, 1366.4, 1377, 1389, 1402, 1413, 1424,
        ...     1435, 1448.8, 1460, 1474.2, 1487.4, 1498, 1511, 1523, 1538, 1551.4,
        ...     1564, 1573, 1584, 1593, 1603.4, 1614, 1626, 1636, 1648, 1661.4, 1672,
        ...     1682, 1693, 1705, 1715, 1724, 1733, 1742, 1751, 1759, 1768, 1777, 1787,
        ...     1795, 1802, 1813, 1822, 1832, 1840, 1849, 1857.6, 1867, 1874, 1882.2,
        ...     1891, 1899, 1908.8, 1919, 1931, 1941, 1948, 1957.8, 1965, 1976, 1987,
        ...     1999, 2013, 2027, 2047, 2058, 2078, 2097, 2117, 2146, 2177, 2220.6,
        ...     2263.6, 2539)
        >>> derived.zlayers.update()
        >>> derived.zlayers
        zlayers(1075.0, 1402.0, 1636.0, 1832.0, 2027.0)

        Number of snow layers = 17:

        >>> nsnowlayers(17)

        >>> derived.zlayers.update()
        >>> derived.zlayers
        zlayers(808.0, 1052.0, 1185.0, 1291.0, 1366.4, 1435.0, 1511.0, 1584.0,
                1648.0, 1715.0, 1768.0, 1822.0, 1874.0, 1931.0, 1987.0, 2058.0,
                2177.0)

        Number of snow layers = 100:

        >>> nsnowlayers(100)

        >>> derived.zlayers.update()
        >>> derived.zlayers
        zlayers(471.0, 656.2, 749.4, 808.0, 868.0, 908.0, 948.0, 991.2, 1022.6,
                1052.0, 1075.0, 1101.0, 1120.4, 1147.6, 1166.8, 1185.0, 1210.0,
                1229.0, 1242.0, 1259.0, 1277.0, 1291.0, 1305.4, 1318.0, 1328.0,
                1340.0, 1350.2, 1366.4, 1377.0, 1389.0, 1402.0, 1413.0, 1424.0,
                1435.0, 1448.8, 1460.0, 1474.2, 1487.4, 1498.0, 1511.0, 1523.0,
                1538.0, 1551.4, 1564.0, 1573.0, 1584.0, 1593.0, 1603.4, 1614.0,
                1626.0, 1636.0, 1648.0, 1661.4, 1672.0, 1682.0, 1693.0, 1705.0,
                1715.0, 1724.0, 1733.0, 1742.0, 1751.0, 1759.0, 1768.0, 1777.0,
                1787.0, 1795.0, 1802.0, 1813.0, 1822.0, 1832.0, 1840.0, 1849.0,
                1857.6, 1867.0, 1874.0, 1882.2, 1891.0, 1899.0, 1908.8, 1919.0,
                1931.0, 1941.0, 1948.0, 1957.8, 1965.0, 1976.0, 1987.0, 1999.0,
                2013.0, 2027.0, 2047.0, 2058.0, 2078.0, 2097.0, 2117.0, 2146.0,
                2177.0, 2220.6, 2263.6)

        Number of snow layers = 50:

        >>> nsnowlayers(50)

        >>> derived.zlayers.update()
        >>> derived.zlayers
        zlayers(471.0, 749.4, 868.0, 948.0, 1022.6, 1075.0, 1120.4, 1166.8,
                1210.0, 1242.0, 1277.0, 1305.4, 1328.0, 1350.2, 1377.0, 1402.0,
                1424.0, 1448.8, 1474.2, 1498.0, 1523.0, 1551.4, 1573.0, 1593.0,
                1614.0, 1636.0, 1661.4, 1682.0, 1705.0, 1724.0, 1742.0, 1759.0,
                1777.0, 1795.0, 1813.0, 1832.0, 1849.0, 1867.0, 1882.2, 1899.0,
                1919.0, 1941.0, 1957.8, 1976.0, 1999.0, 2027.0, 2058.0, 2097.0,
                2146.0, 2220.6)

        >>> hypsodata(286, 309, 320, 327, 333, 338, 342, 347, 351, 356, 360, 365, 369, 373, 378, 382, 387, 393, 399,
        ...     405, 411, 417, 423, 428, 434, 439, 443, 448, 453, 458, 463, 469, 474, 480, 485, 491, 496, 501, 507,
        ...     513, 519, 524, 530, 536, 542, 548, 554, 560, 566, 571, 577, 583, 590, 596, 603, 609, 615, 622, 629,
        ...     636, 642, 649, 656, 663, 669, 677, 684, 691, 698, 706, 714, 722, 730, 738, 746, 754, 762, 770, 777,
        ...     786, 797, 808, 819, 829, 841, 852, 863, 875, 887, 901, 916, 934, 952, 972, 994, 1012, 1029, 1054, 1080,
        ...     1125, 1278)

        >>> nsnowlayers(5)

        >>> derived.zlayers.update()
        >>> derived.zlayers
        zlayers(360.0, 463.0, 577.0, 714.0, 916.0)
        """
        con = self.subpars.pars.control.fastaccess
        self.shape = con.nsnowlayers
        zlayers = numpy.zeros(shape=con.nsnowlayers)
        nmoy = 100 // con.nsnowlayers
        nreste = 100 % con.nsnowlayers
        ncont = 0
        for ilayer in range(con.nsnowlayers):
            if nreste > 0:
                nn = nmoy + 1
                nreste -= 1
            else:
                nn = nmoy
            if nn == 1:
                zlayers[ilayer] = con.hypsodata[ncont]
            elif nn == 2:
                zlayers[ilayer] = 0.5 * (
                    con.hypsodata[ncont] + con.hypsodata[ncont]
                )
            elif nn > 2:
                zlayers[ilayer] = con.hypsodata[int(ncont + nn / 2.0 + 1.0) - 1]
            ncont = ncont + nn
        self(zlayers)


class GThresh(parametertools.Parameter):
    """Accumulation threshold [mm]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)
    strict_valuehandling = False

    CONTROLPARAMETERS = (
        snow_control.MeanAnSolidPrecip,
        snow_control.CN4,
        snow_control.NSnowLayers,
    )

    def update(self):
        """Update |GThresh| based on mean annual solid precipitation
        |MeanAnSolidPrecip| and the percentage of annual snowfall |CN4| defining the
        melt threshold [-].

        >>> from hydpy.models.snow import *
        >>> parameterstep('1d')
        >>> nsnowlayers(5)
        >>> meanansolidprecip(700., 750., 730., 630., 700.)
        >>> cn4(0.6)
        >>> derived.gthresh.update()
        >>> derived.gthresh
        gthresh(420.0, 450.0, 438.0, 378.0, 420.0)
        """
        con = self.subpars.pars.control.fastaccess
        self.shape = con.nsnowlayers
        gthresh = numpy.array(con.meanansolidprecip) * con.cn4
        self(gthresh)
