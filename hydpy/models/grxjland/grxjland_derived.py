# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from site-packages
import numpy

# ...from HydPy
import hydpy
from hydpy.core import parametertools

# ...from snow
from hydpy.models.grxjland import grxjland_control


class DOY(parametertools.DOYParameter):
    """References the "global" month of the year index array [-]."""


class UH1(parametertools.Parameter):
    """Unit hydrograph UH1 ordinates [-]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, 1.0)
    strict_valuehandling = False

    CONTROLPARAMETERS = (grxjland_control.X4,)

    def update(self):
        """Update |UH1| based on |X4|.

        .. note::

            This method also updates the shape of log sequence |Q9|.

        |X4| determines the time base of the unit hydrograph.  A value of
        |X4| being not larger than the simulation step size is
        identical with applying no unit hydrograph at all:

        >>> from hydpy.models.grxjland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> simulationstep('1d')
        >>> pub.options.reprdigits = 6
        >>> x4(0.6)
        >>> derived.uh1.update()
        >>> logs.quh1.shape
        (1,)
        >>> derived.uh1
        uh1(1.0)

        Note that, due to difference of the parameter and the simulation
        step size in the given example, the largest assignment resulting
        in a `inactive` unit hydrograph is 1/2:

        >>> x4(1.)
        >>> derived.uh1.update()
        >>> logs.quh1.shape
        (1,)
        >>> derived.uh1
        uh1(1.0)

        |X4| larger than 1

        >>> x4(1.8)
        >>> derived.uh1.update()
        >>> logs.quh1.shape
        (2,)
        >>> derived.uh1
        uh1(0.230048, 0.769952)

        >>> x4(6.3)
        >>> derived.uh1.update()
        >>> logs.quh1.shape
        (7,)
        >>> derived.uh1
        uh1(0.010038, 0.046746, 0.099694, 0.16474, 0.239926, 0.324027, 0.11483)

        Check for sum equal to 1
        >>> import numpy
        >>> numpy.sum(derived.uh1)
        1.0

        """
        x4 = self.subpars.pars.control.x4
        quh1 = self.subpars.pars.model.sequences.logs.quh1
        # Determine UH parameters...
        if x4 <= 1.0:
            # ...when x4 smaller than or equal to the simulation time step.
            self.shape = 1
            quh1.shape = 1
            self(1.0)
        else:
            index = numpy.arange(1, numpy.ceil(x4) + 1)
            sh1j = (index / x4) ** 2.5
            sh1j_1 = ((index - 1) / x4) ** 2.5
            sh1j[index >= x4] = 1
            sh1j_1[index - 1 >= x4] = 1
            self.shape = len(sh1j)
            uh1 = self.values
            quh1.shape = len(uh1)
            uh1[:] = sh1j - sh1j_1

            # sum should be equal to one but better normalize
            self(uh1 / numpy.sum(uh1))


class UH2(parametertools.Parameter):
    """Unit hydrograph UH2 ordinates [-]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, 1.0)
    strict_valuehandling = False

    CONTROLPARAMETERS = (grxjland_control.X4,)

    def update(self):
        """Update |UH2| based on |X4|.

        .. note::

            This method also updates the shape of log sequence |Q1|.

        2 x |X4| determines the time base of the unit hydrograph. If X4 is smaller or
        equal to 1, UH2 has two ordinates:

        >>> from hydpy.models.grxjland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> simulationstep('1d')
        >>> pub.options.reprdigits = 6
        >>> x4(0.6)
        >>> derived.uh2.update()
        >>> logs.quh2.shape
        (2,)
        >>> derived.uh2
        uh2(0.967925, 0.032075)

        |X4| larger than 1

        >>> x4(2.8)
        >>> derived.uh2.update()
        >>> logs.quh2.shape
        (6,)
        >>> derived.uh2
        uh2(0.038113, 0.177487, 0.368959, 0.292023, 0.112789, 0.010628)

        Check for sum equal to 1
        >>> import numpy
        >>> numpy.sum(derived.uh2)
        1.0

        |X4| smaller or equal to 0.5
        >>> x4(0.5)
        >>> derived.uh2.update()
        >>> logs.quh2.shape
        (2,)
        >>> derived.uh2
        uh2(1.0, 0.0)

        Check for sum equal to 1
        >>> import numpy
        >>> numpy.sum(derived.uh2)
        1.0

        """
        x4 = self.subpars.pars.control.x4
        quh2 = self.subpars.pars.model.sequences.logs.quh2
        # Determine UH parameters...
        if x4 <= 1.0:
            index = numpy.arange(1, 3)
        else:
            index = numpy.arange(1, numpy.ceil(x4 * 2) + 1)

        nmb_uhs = len(index)
        sh2j = numpy.zeros(shape=nmb_uhs)
        sh2j_1 = numpy.zeros(shape=nmb_uhs)

        for idx in range(nmb_uhs):
            if index[idx] <= x4:
                sh2j[idx] = 0.5 * (index[idx] / x4) ** 2.5
            elif x4 < index[idx] < 2.0 * x4:
                sh2j[idx] = 1.0 - 0.5 * (2.0 - index[idx] / x4) ** 2.5
            else:
                sh2j[idx] = 1

            if index[idx] - 1 <= x4:
                sh2j_1[idx] = 0.5 * ((index[idx] - 1) / x4) ** 2.5
            elif x4 < index[idx] - 1 < 2.0 * x4:
                sh2j_1[idx] = 1.0 - 0.5 * (2.0 - (index[idx] - 1) / x4) ** 2.5
            else:
                sh2j_1[idx] = 1

        self.shape = len(index)
        quh2.shape = len(index)
        uh2 = self.values
        uh2[:] = sh2j - sh2j_1
        self(uh2 / numpy.sum(uh2))


class QFactor(parametertools.Parameter):
    """Factor for converting mm/stepsize to m³/s."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)

    CONTROLPARAMETERS = (grxjland_control.Area,)

    def update(self):
        """Update |QFactor| based on |Area| and the current simulation
        step size.

        >>> from hydpy.models.grxjland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> simulationstep('1d')
        >>> pub.options.reprdigits = 6
        >>> area(50.0)
        >>> derived.qfactor.update()
        >>> derived.qfactor
        qfactor(0.578704)

        change simulatio step to 1 h

        >>> simulationstep('1h')
        >>> derived.qfactor.update()
        >>> derived.qfactor
        qfactor(13.888889)

        """
        self(
            self.subpars.pars.control.area
            * 1000.0
            / hydpy.pub.options.simulationstep.seconds
        )


class ZLayers(parametertools.Parameter):
    """Elevation of the snow layers derived from |HypsoData| [m]"""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)

    CONTROLPARAMETERS = (
        grxjland_control.HypsoData,
        grxjland_control.NSnowLayers,
    )

    def update(self):
        """Update |ZLayers| based on |HypsoData|

        Number of snow layers = 5

        >>> from hydpy.models.grxjland import *
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
        zlayers(1052.0, 1389.0, 1626.0, 1822.0, 2013.0)

        Number of snow layers = 17:

        >>> nsnowlayers(17)

        >>> derived.zlayers.update()
        >>> derived.zlayers
        zlayers(749.4, 1022.6, 1166.8, 1277.0, 1350.2, 1424.0, 1498.0, 1573.0,
                1636.0, 1705.0, 1759.0, 1813.0, 1867.0, 1919.0, 1976.0, 2047.0,
                2146.0)

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
        zlayers(563.6, 778.7, 888.0, 969.6, 1037.3, 1088.0, 1134.0, 1175.9,
                1219.5, 1250.5, 1284.0, 1311.7, 1334.0, 1358.3, 1383.0, 1407.5,
                1429.5, 1454.4, 1480.8, 1504.5, 1530.5, 1557.7, 1578.5, 1598.2,
                1620.0, 1642.0, 1666.7, 1687.5, 1710.0, 1728.5, 1746.5, 1763.5,
                1782.0, 1798.5, 1817.5, 1836.0, 1853.3, 1870.5, 1886.6, 1903.9,
                1925.0, 1944.5, 1961.4, 1981.5, 2006.0, 2037.0, 2068.0, 2107.0,
                2161.5, 2242.1)
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
                    con.hypsodata[ncont] + con.hypsodata[ncont + 1]
                )
            elif nn > 2:
                zlayers[ilayer] = con.hypsodata[int(ncont + nn / 2.0 - 1.0)]
            ncont = ncont + nn
        self(zlayers)


class GThresh(parametertools.Parameter):
    """Accumulation threshold [mm]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)
    strict_valuehandling = False

    CONTROLPARAMETERS = (
        grxjland_control.MeanAnSolidPrecip,
        grxjland_control.CN4,
        grxjland_control.NSnowLayers,
    )

    def update(self):
        """Update |GThresh| based on mean annual solid precipitation
        |MeanAnSolidPrecip| and the percentage of annual snowfall |CN4| defining the
        melt threshold [-].

        >>> from hydpy.models.grxjland import *
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
