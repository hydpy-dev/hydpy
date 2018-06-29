# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy import pub
from hydpy.core import parametertools
# ...from site-packages
import numpy
# ...model specific
from hydpy.models.lland import lland_parameters
from hydpy.models.lland.lland_constants import WASSER, FLUSS, SEE


class MOY(parametertools.IndexParameter):
    """References the "global" month of the year index array [-]."""
    NDIM, TYPE, TIME, SPAN = 1, int, None, (0, 11)

    def update(self):
        """Reference the actual |Indexer.monthofyear| array of the
        |Indexer| object stored in module |pub|.

        >>> from hydpy import pub
        >>> from hydpy import Timegrids, Timegrid
        >>> pub.timegrids = Timegrids(Timegrid('27.02.2004',
        ...                                    '3.03.2004',
        ...                                    '1d'))
        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> derived.moy.update()
        >>> derived.moy
        moy(1, 1, 1, 2, 2)
        """
        self.setreference(pub.indexer.monthofyear)


class AbsFHRU(lland_parameters.ParameterComplete):
    """Flächen der Hydrotope (areas of the respective HRUs) [km²]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

    def update(self):
        """Update |AbsFHRU| based on |FT| and |FHRU|.

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(2)
        >>> lnk(ACKER)
        >>> ft(100.0)
        >>> fhru(0.2, 0.8)
        >>> derived.absfhru.update()
        >>> derived.absfhru
        absfhru(20.0, 80.0)
        """
        control = self.subpars.pars.control
        self(control.ft*control.fhru)


class KInz(lland_parameters.LanduseMonthParameter):
    """Interzeptionskapazität bezogen auf die Bodenoberfläche (interception
    capacity normalized to the soil surface area) [mm]."""
    NDIM, TYPE, TIME, SPAN = 2, float, None, (0., None)

    def update(self):
        """Update |KInz| based on |HInz| and |LAI|.

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(2)
        >>> hinz(0.2)
        >>> lai.acker_jun = 1.0
        >>> lai.vers_dec = 2.0
        >>> derived.kinz.update()
        >>> from hydpy import round_
        >>> round_(derived.kinz.acker_jun)
        0.2
        >>> round_(derived.kinz.vers_dec)
        0.4
        """
        con = self.subpars.pars.control
        self(con.hinz*con.lai)


class WB(lland_parameters.ParameterComplete):
    """Absolute Mindestbodenfeuchte für die Basisabflussentstehung (threshold
       value of absolute soil moisture for base flow generation) [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

    def update(self):
        """Update |WB| based on |RelWB| and |NFk|.

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(2)
        >>> lnk(ACKER)
        >>> relwb(0.2)
        >>> nfk(100.0, 200.0)
        >>> derived.wb.update()
        >>> derived.wb
        wb(20.0, 40.0)
        """
        con = self.subpars.pars.control
        self(con.relwb*con.nfk)


class WZ(lland_parameters.ParameterComplete):
    """Absolute Mindestbodenfeuchte für die Interflowentstehung (threshold
       value of absolute soil moisture for interflow generation) [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

    def update(self):
        """Update |WZ| based on |RelWZ| and |NFk|.

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(2)
        >>> lnk(ACKER)
        >>> relwz(0.8)
        >>> nfk(100.0, 200.0)
        >>> derived.wz.update()
        >>> derived.wz
        wz(80.0, 160.0)
        """
        con = self.subpars.pars.control
        self(con.relwz*con.nfk)


class KB(parametertools.SingleParameter):
    """Konzentrationszeit des Basisabflusses (concentration time of baseflow)
    [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

    def update(self):
        """Update |KB| based on |EQB| and |TInd|.

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> eqb(10.0)
        >>> tind.value = 10.0
        >>> derived.kb.update()
        >>> derived.kb
        kb(100.0)
        """
        con = self.subpars.pars.control
        self(con.eqb*con.tind)


class KI1(parametertools.SingleParameter):
    """Konzentrationszeit des "unteren" Zwischenabflusses (concentration time
    of the first interflow component) [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

    def update(self):
        """Update |KI1| based on |EQI1| and |TInd|.

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> eqi1(5.0)
        >>> tind.value = 10.0
        >>> derived.ki1.update()
        >>> derived.ki1
        ki1(50.0)
        """
        con = self.subpars.pars.control
        self(con.eqi1*con.tind)


class KI2(parametertools.SingleParameter):
    """Konzentrationszeit des "oberen" Zwischenabflusses" (concentration time
    of the second interflow component) [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

    def update(self):
        """Update |KI2| based on |EQI2| and |TInd|.

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> eqi2(1.0)
        >>> tind.value = 10.0
        >>> derived.ki2.update()
        >>> derived.ki2
        ki2(10.0)
        """
        con = self.subpars.pars.control
        self(con.eqi2*con.tind)


class KD1(parametertools.SingleParameter):
    """Konzentrationszeit des "langsamen" Direktabflusses (concentration time
    of the slower component of direct runoff) [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

    def update(self):
        """Update |KD1| based on |EQD1| and |TInd|.

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> eqd1(0.5)
        >>> tind.value = 10.0
        >>> derived.kd1.update()
        >>> derived.kd1
        kd1(5.0)
        """
        con = self.subpars.pars.control
        self(con.eqd1*con.tind)


class KD2(parametertools.SingleParameter):
    """Konzentrationszeit des "schnellen" Direktabflusses (concentration time
    of the faster component of direct runoff) [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

    def update(self):
        """Update |KD2| based on |EQD2| and |TInd|.

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> eqd2(0.1)
        >>> tind.value = 10.0
        >>> derived.kd2.update()
        >>> derived.kd2
        kd2(1.0)
        """
        con = self.subpars.pars.control
        self(con.eqd2*con.tind)


class QFactor(parametertools.SingleParameter):
    """Factor for converting mm/stepsize to m³/s."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

    def update(self):
        """Update |QFactor| based on |FT| and the current simulation step size.

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> simulationstep('1d')
        >>> ft(10.0)
        >>> derived.qfactor.update()
        >>> derived.qfactor
        qfactor(0.115741)
        """
        con = self.subpars.pars.control
        self(con.ft*1000./self.simulationstep.seconds)


class DerivedParameters(parametertools.SubParameters):
    """Derived parameters of HydPy-H-Land, indirectly defined by the user."""
    CLASSES = (MOY,
               AbsFHRU,
               KInz,
               WB,
               WZ,
               KB,
               KI1,
               KI2,
               KD1,
               KD2,
               QFactor)
