# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from site-packages
import numpy
# ...from HydPy
from hydpy.core import parametertools
# ...from grxjland
from hydpy.models.grxjland import grxjland_control


class DOY(parametertools.DOYParameter):
    """References the "global" month of the year index array [-]."""

class UH1(parametertools.Parameter):
    """Unit hydrograph UH1 ordinates [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., 1.)
    strict_valuehandling = False

    CONTROLPARAMETERS = (
        grxjland_control.X4,
    )

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
        if x4 <= 1.:
            # ...when x4 smaller than or equal to the simulation time step.
            self.shape = 1
            quh1.shape = 1
            self(1.)
        else:
            index = numpy.arange(1, numpy.ceil(x4) + 1)
            sh1j = (index / x4)**2.5
            sh1j_1 = ((index - 1) / x4)**2.5
            sh1j[index >= x4] = 1
            sh1j_1[index - 1 >= x4] = 1
            self.shape = len(sh1j)
            uh1 = self.values
            quh1.shape = len(uh1)
            uh1[:] = sh1j - sh1j_1
            
            # sum should be equal to one but better normalize
            self(uh1/numpy.sum(uh1))
            
            
class UH2(parametertools.Parameter):
    """Unit hydrograph UH2 ordinates [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., 1.)
    strict_valuehandling = False

    CONTROLPARAMETERS = (
        grxjland_control.X4,
    )

    def update(self):
        """Update |UH2| based on |X4|.

        .. note::

            This method also updates the shape of log sequence |Q1|.

        2 x |X4| determines the time base of the unit hydrograph. If X4 is smaller or equal to 1, UH2 has two ordinates:

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
        
        """
        x4 = self.subpars.pars.control.x4
        quh2 = self.subpars.pars.model.sequences.logs.quh2
        # Determine UH parameters...
        if x4 <= 1.:
            index = numpy.arange(1, 3)
        else:
            index = numpy.arange(1, numpy.ceil(x4 * 2) + 1)
        
        sh2j = numpy.zeros(shape = len(index))
        sh2j_1 = numpy.zeros(shape = len(index))
        
        for idx in range(len(index)):
            if index[idx] <= x4:
                sh2j[idx] = 0.5 * (index[idx] / x4) ** 2.5
            elif index[idx] > x4 and index[idx] < 2. * x4:
                sh2j[idx] = 1. - 0.5 * (2. - index[idx] / x4) ** 2.5
            else:
                sh2j[idx] = 1
                
            if index[idx] - 1 <= x4:
                sh2j_1[idx] = 0.5 * ((index[idx] - 1) / x4) ** 2.5
            elif index[idx] - 1 > x4 and index[idx] - 1 < 2. * x4:
                sh2j_1[idx] = 1. - 0.5 * (2. - (index[idx] - 1) / x4) ** 2.5
            else:
                sh2j_1[idx] = 1
         

        self.shape = len(index)
        quh2.shape = len(index)
        uh2 = self.values
        uh2[:] = sh2j - sh2j_1
        self(uh2/numpy.sum(uh2))

class QFactor(parametertools.Parameter):
    """Factor for converting mm/stepsize to m³/s."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

    CONTROLPARAMETERS = (
        grxjland_control.Area,
    )

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
        self(self.subpars.pars.control.area*1000. /
             self.subpars.qfactor.simulationstep.seconds)


class ZLayers(parametertools.Parameter):
    """Elevation of the snow layers derived from |HypsoData| [m]"""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

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
        >>> hypsodata(471, 656.2, 749.4, 808, 868, 908, 948, 991.2, 1022.6, 1052, 1075, 1101, 1120.4, 1147.6,
        ...     1166.8, 1185, 1210, 1229, 1242, 1259, 1277, 1291, 1305.4, 1318, 1328, 1340, 1350.2, 1366.4,
        ...     1377, 1389, 1402, 1413, 1424, 1435, 1448.8, 1460, 1474.2, 1487.4, 1498, 1511, 1523, 1538,
        ...     1551.4, 1564, 1573, 1584, 1593, 1603.4, 1614, 1626, 1636, 1648, 1661.4, 1672, 1682, 1693,
        ...     1705, 1715, 1724, 1733, 1742, 1751, 1759, 1768, 1777, 1787, 1795, 1802, 1813, 1822, 1832,
        ...     1840, 1849, 1857.6, 1867, 1874, 1882.2, 1891, 1899, 1908.8, 1919, 1931, 1941, 1948, 1957.8,
        ...     1965, 1976, 1987, 1999, 2013, 2027, 2047, 2058, 2078, 2097, 2117, 2146, 2177, 2220.6, 2263.6, 2539)
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
                nreste = nreste - 1
            else:
                nn = nmoy
            if nn == 1:
                zlayers[ilayer] = con.hypsodata[ncont]
            elif nn == 2:
                zlayers[ilayer] = 0.5 * (con.hypsodata[ncont] + con.hypsodata[ncont + 1])
            elif nn > 2:
                zlayers[ilayer] = con.hypsodata[int(ncont + nn / 2. - 1.)]
            ncont = ncont + nn
        self(zlayers)


class GThresh(parametertools.Parameter):
    """Accumulation threshold [mm]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)
    strict_valuehandling = False

    CONTROLPARAMETERS = (
        grxjland_control.MeanAnSolidPrecip,
        grxjland_control.CN4,
        grxjland_control.NSnowLayers,
    )

    def update(self):
        """Update |GThresh| based on mean annual solid precipitation |MeanAnSolidPrecip| and
        the percentage of annual snowfall |CN4| defining the melt threshold [-].

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
        gthresh = self.values
        gthresh = numpy.array(con.meanansolidprecip) * con.cn4
        self(gthresh)