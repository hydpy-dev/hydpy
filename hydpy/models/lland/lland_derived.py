# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...

# ...from site-packages
import numpy

# ...from HydPy
import hydpy
from hydpy.core import exceptiontools
from hydpy.core import objecttools
from hydpy.core import parametertools

# ...from lland
from hydpy.models.lland import lland_control
from hydpy.models.lland import lland_fixed
from hydpy.models.lland import lland_parameters
from hydpy.models.lland.lland_constants import LAUBW, MISCHW, NADELW


class MOY(parametertools.MOYParameter):
    """References the "global" month of the year index array [-]."""


class DOY(parametertools.DOYParameter):
    """References the "global" day of the year index array [-]."""


class Seconds(parametertools.SecondsParameter):
    """The length of the actual simulation step size in seconds [s]."""


class Hours(parametertools.HoursParameter):
    """The length of the actual simulation step size in hours [h]."""


class Days(parametertools.DaysParameter):
    """The length of the actual simulation step size in days [d]."""


class SCT(parametertools.SCTParameter):
    """References the "global" standard clock time array [-]."""


class UTCLongitude(parametertools.UTCLongitudeParameter):
    """Longitude of the centre of the local time zone [°]."""


class NmbLogEntries(parametertools.Parameter):
    """The number of log entries required for a memory duration of 24 hours
    [-]."""

    NDIM, TYPE, TIME, SPAN = 0, int, None, (1, None)

    def update(self):
        """Calculate the number of entries and adjust the shape of all
        relevant log sequences.

        The aimed memory duration is one day.  Hence, the number of the
        required log entries depends on the simulation step size:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> from hydpy import pub
        >>> nhru(2)
        >>> pub.timegrids = "2000-01-01", "2000-01-02", "1h"
        >>> derived.nmblogentries.update()
        >>> derived.nmblogentries
        nmblogentries(24)
        >>> logs
        wet0([[nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,
               nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]])
        loggedteml(nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,
                   nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan)
        loggedrelativehumidity(nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,
                               nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,
                               nan, nan, nan, nan)
        loggedsunshineduration(nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,
                               nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,
                               nan, nan, nan, nan)
        loggedglobalradiation(nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,
                              nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,
                              nan, nan, nan, nan)
        loggedwindspeed2m(nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,
                          nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,
                          nan, nan)

        To prevent from loosing information, updating parameter |NmbLogEntries|
        resets the shape of the relevant log sequences only when necessary:

        >>> logs.wet0 = 1.0
        >>> logs.loggedteml = 2.0
        >>> logs.loggedrelativehumidity.shape = (6,)
        >>> logs.loggedrelativehumidity = 3.0
        >>> derived.nmblogentries.update()
        >>> logs   # doctest: +ELLIPSIS
        wet0([[1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
               1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]])
        loggedteml(2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0,
                   2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0)
        loggedrelativehumidity(nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,
                               nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,
                               nan, nan, nan, nan)
        ...

        There is an explicit check for inappropriate simulation step sizes:

        >>> pub.timegrids = "2000-01-01 00:00", "2000-01-01 10:00", "5h"
        >>> derived.nmblogentries.update()
        Traceback (most recent call last):
        ...
        ValueError: The value of parameter `nmblogentries` of element `?` \
cannot be determined for a the current simulation step size.  The fraction of \
the memory period (1d) and the simulation step size (5h) leaves a remainder.

        .. testsetup::

            >>> del pub.timegrids
        """
        nmb = "1d" / hydpy.pub.options.simulationstep
        if nmb % 1:
            raise ValueError(
                f"The value of parameter {objecttools.elementphrase(self)} "
                f"cannot be determined for a the current simulation step "
                f"size.  The fraction of the memory period (1d) and the "
                f"simulation step size ({hydpy.pub.timegrids.stepsize}) "
                f"leaves a remainder."
            )
        self(nmb)
        nmb = int(nmb)
        logs = self.subpars.pars.model.sequences.logs
        for seq in logs:
            shape = exceptiontools.getattr_(seq, "shape", (None,))
            if nmb != shape[-1]:
                seq.shape = nmb


class LatitudeRad(parametertools.Parameter):
    """The latitude [rad]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (-1.5708, 1.5708)

    CONTROLPARAMETERS = (lland_control.Latitude,)

    def update(self):
        """Update |LatitudeRad| based on parameter |Latitude|.

        >>> from hydpy import round_
        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> for value in (-90.0, -45.0, 0.0, 45.0, 90.0):
        ...     latitude(value)
        ...     derived.latituderad.update()
        ...     round_(latitude.value, end=": ")
        ...     round_(derived.latituderad.value)
        -90.0: -1.570796
        -45.0: -0.785398
        0.0: 0.0
        45.0: 0.785398
        90.0: 1.570796
        """
        self.value = 3.141592653589793 / 180.0 * self.subpars.pars.control.latitude


class AbsFHRU(lland_parameters.ParameterComplete):
    """Flächen der Hydrotope (areas of the respective HRUs) [km²]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)

    CONTROLPARAMETERS = (
        lland_control.FT,
        lland_control.FHRU,
    )

    def update(self):
        """Update |AbsFHRU| based on |FT| and |FHRU|.

        >>> from hydpy.models.lland import *
        >>> parameterstep("1d")
        >>> nhru(2)
        >>> lnk(ACKER)
        >>> ft(100.0)
        >>> fhru(0.2, 0.8)
        >>> derived.absfhru.update()
        >>> derived.absfhru
        absfhru(20.0, 80.0)
        """
        control = self.subpars.pars.control
        self.value = control.ft * control.fhru


class KInz(lland_parameters.LanduseMonthParameter):
    """Interzeptionskapazität bezogen auf die Bodenoberfläche (interception
    capacity normalized to the soil surface area) [mm]."""

    NDIM, TYPE, TIME, SPAN = 2, float, None, (0.0, None)

    CONTROLPARAMETERS = (
        lland_control.HInz,
        lland_control.LAI,
    )

    def update(self):
        """Update |KInz| based on |HInz| and |LAI| :cite:`ref-LARSIM`
        (based on :cite:`ref-Dickinson1984`).

        >>> from hydpy.models.lland import *
        >>> parameterstep("1d")
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
        self.value = con.hinz * con.lai


class HeatOfFusion(lland_parameters.ParameterLand):
    """Heat which is necessary to melt the frozen soil water content."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)

    FIXEDPARAMETERS = (
        lland_fixed.BoWa2Z,
        lland_fixed.RSchmelz,
    )

    def update(self):
        """Update |HeatOfFusion| based on |RSchmelz| and |BoWa2Z|.

        Basic equation:

           :math:`HeatOfFusion = RSchmelz \\cdot BoWa2Z`

        >>> from hydpy.models.lland import *
        >>> parameterstep("1d")
        >>> nhru(2)
        >>> lnk(ACKER, LAUBW)
        >>> derived.heatoffusion.update()
        >>> derived.heatoffusion
        heatoffusion(26.72)
        """
        fixed = self.subpars.pars.fixed
        self.value = fixed.rschmelz * fixed.bowa2z


class Fr(lland_parameters.LanduseMonthParameter):
    """Reduktionsfaktor für Strahlung :cite:`ref-LARSIM`
    (basierend auf :cite:`ref-LUBWLUWG2015`) (reduction factor for short- and
    long wave radiation) :cite:`ref-LARSIM` (based on :cite:`ref-LUBWLUWG2015`)
    [-]."""

    NDIM, TYPE, TIME, SPAN = 2, float, None, (0.0, None)

    CONTROLPARAMETERS = (
        lland_control.LAI,
        lland_control.P1Strahl,
        lland_control.P2Strahl,
    )

    def update(self):
        """Update |Fr| based on |LAI|, |P1Strahl| and |P2Strahl|.

        Basic equation for forests:
          :math:`Fr = P1Strahl - P2Strahl \\cdot LAI`

        Note that |Fr| is one for all other land use classes than |LAUBW|,
        |MISCHW|, and |NADELW|,  and that we do not trim |Fr| to prevent
        negative values for large leaf area index values:

        >>> from hydpy.models.lland import *
        >>> parameterstep("1d")
        >>> p1strahl(0.5)
        >>> p2strahl(0.1)
        >>> lai.acker_jan = 1.0
        >>> lai.laubw_feb = 3.0
        >>> lai.mischw_mar = 5.0
        >>> lai.nadelw_apr = 7.0
        >>> derived.fr.update()
        >>> from hydpy import round_
        >>> round_(derived.fr.acker_jan)
        1.0
        >>> round_(derived.fr.laubw_feb)
        0.2
        >>> round_(derived.fr.mischw_mar)
        0.0
        >>> round_(derived.fr.nadelw_apr)
        -0.2
        """
        con = self.subpars.pars.control
        values = self.values
        for idx, lais in enumerate(con.lai.values):
            if idx + 1 in (LAUBW, MISCHW, NADELW):
                values[idx, :] = con.p1strahl - con.p2strahl * lais
            else:
                values[idx, :] = 1.0


class NFk(lland_parameters.ParameterSoil):
    """Nutzbare Feldkapazität (usable field capacity) [mm]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)

    CONTROLPARAMETERS = (
        lland_control.PWP,
        lland_control.FK,
    )

    def update(self):
        """Update |NFk| based on |PWP| and |FK|.

        >>> from hydpy.models.lland import *
        >>> parameterstep("1d")
        >>> nhru(1)
        >>> lnk(ACKER)
        >>> fk(100.0)
        >>> pwp(20.0)
        >>> derived.nfk.update()
        >>> derived.nfk
        nfk(80.0)
        """
        con = self.subpars.pars.control
        self.value = con.fk - con.pwp


class KB(parametertools.Parameter):
    """Konzentrationszeit des Basisabflusses (concentration time of baseflow)
    [T]."""

    NDIM, TYPE, TIME, SPAN = 0, float, False, (0.0, None)

    CONTROLPARAMETERS = (
        lland_control.EQB,
        lland_control.TInd,
    )

    def update(self):
        """Update |KB| based on |EQB| and |TInd|.

        >>> from hydpy.models.lland import *
        >>> simulationstep("1h")
        >>> parameterstep("1d")
        >>> eqb(10.0)
        >>> tind(10.0)
        >>> derived.kb.update()
        >>> derived.kb
        kb(100.0)
        """
        con = self.subpars.pars.control
        self.value = con.eqb * con.tind


class KI1(parametertools.Parameter):
    """Konzentrationszeit des "unteren" Zwischenabflusses (concentration time
    of the first interflow component) [T]."""

    NDIM, TYPE, TIME, SPAN = 0, float, False, (0.0, None)

    CONTROLPARAMETERS = (
        lland_control.EQI1,
        lland_control.TInd,
    )

    def update(self):
        """Update |KI1| based on |EQI1| and |TInd|.

        >>> from hydpy.models.lland import *
        >>> simulationstep("1h")
        >>> parameterstep("1d")
        >>> eqi1(5.0)
        >>> tind(10.0)
        >>> derived.ki1.update()
        >>> derived.ki1
        ki1(50.0)
        """
        con = self.subpars.pars.control
        self.value = con.eqi1 * con.tind


class KI2(parametertools.Parameter):
    """Konzentrationszeit des "oberen" Zwischenabflusses" (concentration time
    of the second interflow component) [T]."""

    NDIM, TYPE, TIME, SPAN = 0, float, False, (0.0, None)

    CONTROLPARAMETERS = (
        lland_control.EQI2,
        lland_control.TInd,
    )

    def update(self):
        """Update |KI2| based on |EQI2| and |TInd|.

        >>> from hydpy.models.lland import *
        >>> simulationstep("1h")
        >>> parameterstep("1d")
        >>> eqi2(1.0)
        >>> tind(10.0)
        >>> derived.ki2.update()
        >>> derived.ki2
        ki2(10.0)
        """
        con = self.subpars.pars.control
        self.value = con.eqi2 * con.tind


class KD1(parametertools.Parameter):
    """Konzentrationszeit des "langsamen" Direktabflusses (concentration time
    of the slower component of direct runoff) [T]."""

    NDIM, TYPE, TIME, SPAN = 0, float, False, (0.0, None)

    CONTROLPARAMETERS = (
        lland_control.EQD1,
        lland_control.TInd,
    )

    def update(self):
        """Update |KD1| based on |EQD1| and |TInd|.

        >>> from hydpy.models.lland import *
        >>> simulationstep("1h")
        >>> parameterstep("1d")
        >>> eqd1(0.5)
        >>> tind(10.0)
        >>> derived.kd1.update()
        >>> derived.kd1
        kd1(5.0)
        """
        con = self.subpars.pars.control
        self.value = con.eqd1 * con.tind


class KD2(parametertools.Parameter):
    """Konzentrationszeit des "schnellen" Direktabflusses (concentration time
    of the faster component of direct runoff) [T]."""

    NDIM, TYPE, TIME, SPAN = 0, float, False, (0.0, None)

    CONTROLPARAMETERS = (
        lland_control.EQD2,
        lland_control.TInd,
    )

    def update(self):
        """Update |KD2| based on |EQD2| and |TInd|.

        >>> from hydpy.models.lland import *
        >>> simulationstep("1h")
        >>> parameterstep("1d")
        >>> eqd2(0.1)
        >>> tind(10.0)
        >>> derived.kd2.update()
        >>> derived.kd2
        kd2(1.0)
        """
        con = self.subpars.pars.control
        self.value = con.eqd2 * con.tind


class QBGAMax(parametertools.Parameter):
    """Maximaler Abfluss aus dem Basisabfluss-Gebietsspeicher (maximum outflow
    from the storage compartment for base flow) [mm/T]."""

    NDIM, TYPE, TIME, SPAN = 0, float, True, (0.0, None)

    CONTROLPARAMETERS = (
        lland_control.GSBMax,
        lland_control.VolBMax,
    )
    DERIVEDPARAMETERS = (KB,)

    def update(self):
        r"""Update based on :math:`QBGAMax = (GSBMax \cdot VolBMax) / KB`.

        >>> from hydpy.models.lland import *
        >>> simulationstep("1h")
        >>> parameterstep("1d")
        >>> volbmax(100.0)
        >>> gsbmax(2.0)
        >>> derived.kb(50.0)
        >>> derived.qbgamax.update()
        >>> derived.qbgamax
        qbgamax(4.0)

        For zero runoff concentration time, we generally set |QBGAMax| to zero,
        even if |VolBMax| is also to zero:

        >>> volbmax(0.0)
        >>> derived.kb(0.0)
        >>> derived.qbgamax.update()
        >>> derived.qbgamax
        qbgamax(inf)
        """
        con = self.subpars.pars.control
        der = self.subpars
        if der.kb > 0.0:
            self.value = (con.gsbmax * con.volbmax) / der.kb
        else:
            self.value = numpy.inf


class QFactor(parametertools.Parameter):
    """Factor for converting mm/stepsize to m³/s."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)

    CONTROLPARAMETERS = (lland_control.FT,)

    def update(self):
        """Update |QFactor| based on |FT| and the current simulation step size.

        >>> from hydpy.models.lland import *
        >>> parameterstep("1d")
        >>> simulationstep("1d")
        >>> ft(10.0)
        >>> derived.qfactor.update()
        >>> derived.qfactor
        qfactor(0.115741)
        """
        con = self.subpars.pars.control
        self.value = con.ft * 1000.0 / hydpy.pub.options.simulationstep.seconds
