# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools
# ...from lland
from hydpy.models.lland import lland_control
from hydpy.models.lland import lland_parameters


class MOY(parametertools.MOYParameter):
    """References the "global" month of the year index array [-]."""


class AbsFHRU(lland_parameters.ParameterComplete):
    """Flächen der Hydrotope (areas of the respective HRUs) [km²]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

    CONTROLPARAMETERS = (
        lland_control.FT,
        lland_control.FHRU,
    )

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
        self.value = control.ft*control.fhru


class KInz(lland_parameters.LanduseMonthParameter):
    """Interzeptionskapazität bezogen auf die Bodenoberfläche (interception
    capacity normalized to the soil surface area) [mm]."""
    NDIM, TYPE, TIME, SPAN = 2, float, None, (0., None)

    CONTROLPARAMETERS = (
        lland_control.HInz,
        lland_control.LAI,
    )

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
        self.value = con.hinz*con.lai


class KB(parametertools.Parameter):
    """Konzentrationszeit des Basisabflusses (concentration time of baseflow)
    [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

    CONTROLPARAMETERS = (
        lland_control.EQB,
        lland_control.TInd,
    )

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
        self.value = con.eqb*con.tind


class KI1(parametertools.Parameter):
    """Konzentrationszeit des "unteren" Zwischenabflusses (concentration time
    of the first interflow component) [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

    CONTROLPARAMETERS = (
        lland_control.EQI1,
        lland_control.TInd,
    )

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
        self.value = con.eqi1*con.tind


class KI2(parametertools.Parameter):
    """Konzentrationszeit des "oberen" Zwischenabflusses" (concentration time
    of the second interflow component) [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

    CONTROLPARAMETERS = (
        lland_control.EQI2,
        lland_control.TInd,
    )

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
        self.value = con.eqi2*con.tind


class KD1(parametertools.Parameter):
    """Konzentrationszeit des "langsamen" Direktabflusses (concentration time
    of the slower component of direct runoff) [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

    CONTROLPARAMETERS = (
        lland_control.EQD1,
        lland_control.TInd,
    )

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
        self.value = con.eqd1*con.tind


class KD2(parametertools.Parameter):
    """Konzentrationszeit des "schnellen" Direktabflusses (concentration time
    of the faster component of direct runoff) [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

    CONTROLPARAMETERS = (
        lland_control.EQD2,
        lland_control.TInd,
    )

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
        self.value = con.eqd2*con.tind


class QFactor(parametertools.Parameter):
    """Factor for converting mm/stepsize to m³/s."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

    CONTROLPARAMETERS = (
        lland_control.FT,
    )

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
        self.value = con.ft*1000./self.simulationstep.seconds
