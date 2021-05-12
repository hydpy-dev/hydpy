# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from standard library
import warnings

# ...from site-packages
import numpy

# ...from HydPy
import hydpy
from hydpy.core import parametertools

# ...from hland
from hydpy.models.hland import hland_parameters
from hydpy.models.hland import hland_control
from hydpy.models.hland.hland_constants import ILAKE, GLACIER, SEALED

_ZERO_DIVISION_MESSAGE = "divide by zero encountered in true_divide"


class RelSoilArea(parametertools.Parameter):
    """Relative area of all |FIELD| and |FOREST| zones [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, 1.0)

    CONTROLPARAMETERS = (
        hland_control.ZoneArea,
        hland_control.ZoneType,
        hland_control.Area,
    )

    def update(self):
        """Update |RelSoilArea| based on |Area|, |ZoneArea|, and |ZoneType|.

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> nmbzones(5)
        >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, SEALED)
        >>> area(100.0)
        >>> zonearea(10.0, 20.0, 15.0, 25.0, 30.0)
        >>> derived.relsoilarea.update()
        >>> derived.relsoilarea
        relsoilarea(0.3)
        """
        con = self.subpars.pars.control
        temp = con.zonearea.values.copy()
        temp[con.zonetype.values == GLACIER] = 0.0
        temp[con.zonetype.values == ILAKE] = 0.0
        temp[con.zonetype.values == SEALED] = 0.0
        self(numpy.sum(temp) / con.area)


class RelLandArea(parametertools.Parameter):
    """Relative area of all |FIELD|, |FOREST|, |GLACIER|, and |SEALED| zones [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, 1.0)

    CONTROLPARAMETERS = (
        hland_control.ZoneArea,
        hland_control.ZoneType,
        hland_control.Area,
    )

    def update(self):
        """Update |RelLandArea| based on |Area|, |ZoneArea|, and |ZoneType|.

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> nmbzones(5)
        >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, SEALED)
        >>> area(100.0)
        >>> zonearea(10.0, 20.0, 30.0, 15.0, 25.0)
        >>> derived.rellandarea.update()
        >>> derived.rellandarea
        rellandarea(0.85)
        """
        con = self.subpars.pars.control
        temp = con.zonearea.values.copy()
        temp[con.zonetype.values == ILAKE] = 0.0
        self(numpy.sum(temp) / con.area)


class RelUpperZoneArea(parametertools.Parameter):
    """Relative area of all |FIELD|, |FOREST|, and |GLACIER| zones [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, 1.0)

    CONTROLPARAMETERS = (
        hland_control.ZoneArea,
        hland_control.ZoneType,
        hland_control.Area,
    )

    def update(self):
        """Update |RelUpperZoneArea| based on |Area|, |ZoneArea|, and |ZoneType|.

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> nmbzones(5)
        >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, SEALED)
        >>> area(100.0)
        >>> zonearea(10.0, 20.0, 30.0, 15.0, 25.0)
        >>> derived.relupperzonearea.update()
        >>> derived.relupperzonearea
        relupperzonearea(0.6)
        """
        con = self.subpars.pars.control
        temp = con.zonearea.values.copy()
        temp[con.zonetype.values == ILAKE] = 0.0
        temp[con.zonetype.values == SEALED] = 0.0
        self(numpy.sum(temp) / con.area)


class RelLowerZoneArea(parametertools.Parameter):
    """Relative area of all |FIELD|, |FOREST|, |GLACIER|, and |ILAKE| zones [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, 1.0)

    CONTROLPARAMETERS = (
        hland_control.ZoneArea,
        hland_control.ZoneType,
        hland_control.Area,
    )

    def update(self):
        """Update |RelLowerZoneArea| based on |Area|, |ZoneArea|, and |ZoneType|.

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> nmbzones(5)
        >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, SEALED)
        >>> area(100.0)
        >>> zonearea(10.0, 20.0, 30.0, 15.0, 25.0)
        >>> derived.rellowerzonearea.update()
        >>> derived.rellowerzonearea
        rellowerzonearea(0.75)
        """
        con = self.subpars.pars.control
        temp = con.zonearea.values.copy()
        temp[con.zonetype.values == SEALED] = 0.0
        self(numpy.sum(temp) / con.area)


class RelZoneAreas(hland_parameters.ParameterComplete):
    """Relative area of all zones [-]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, 1.0)
    strict_valuehandling: bool = False

    CONTROLPARAMETERS = (
        hland_control.ZoneArea,
        hland_control.ZoneType,
    )

    def update(self) -> None:
        """Update the relative area based on the parameter |ZoneArea|.

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> nmbzones(5)
        >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, SEALED)
        >>> zonearea(10.0, 40.0, 20.0, 25.0, 5.0)
        >>> derived.relzoneareas.update()
        >>> derived.relzoneareas
        relzoneareas(field=0.1, forest=0.4, glacier=0.2, ilake=0.25,
                     sealed=0.05)
        """
        zonearea = self.subpars.pars.control.zonearea.values
        self.values = zonearea / numpy.sum(zonearea)


class TTM(hland_parameters.ParameterUpperZone):
    """Threshold temperature for snow melting and refreezing [°C]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)

    CONTROLPARAMETERS = (
        hland_control.TT,
        hland_control.DTTM,
    )

    def update(self):
        """Update |TTM| based on :math:`TTM = TT+DTTM`.

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> nmbzones(1)
        >>> zonetype(FIELD)
        >>> tt(1.0)
        >>> dttm(-2.0)
        >>> derived.ttm.update()
        >>> derived.ttm
        ttm(-1.0)
        """
        con = self.subpars.pars.control
        self(con.tt + con.dttm)


class DT(parametertools.Parameter):
    """Relative time step length for the upper zone layer calculations [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, 1.0)

    CONTROLPARAMETERS = (hland_control.RecStep,)

    def update(self):
        """Update |DT| based on :math:`DT = \\frac{1}{RecStep}`.

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> simulationstep("12h")
        >>> recstep(2.0)
        >>> derived.dt.update()
        >>> derived.dt
        dt(1.0)
        >>> recstep(10.0)
        >>> derived.dt.update()
        >>> derived.dt
        dt(0.2)

        Note that the value assigned to parameter |RecStep| depends on the current
        parameter step size (one day).  Due to the current simulation step size (one
        hour), the applied |RecStep| value is five:

        >>> recstep.value
        5
        """
        self(1 / self.subpars.pars.control.recstep)


class W0(parametertools.Parameter):
    """Weight for calculating surface runoff [-]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, 1.0)

    CONTROLPARAMETERS = (hland_control.K0,)

    def update(self):
        """Update |W0| based on :math:`W0 = e^{-1/K0}`.

        >>> from hydpy.models.hland import *
        >>> simulationstep("1h")
        >>> parameterstep("1d")
        >>> nmbzones(5)
        >>> k0(0.0, 0.05, 0.5, 5.0, inf)
        >>> from hydpy import round_
        >>> round_(k0.values)
        0.0, 1.2, 12.0, 120.0, inf
        >>> derived.w0.update()
        >>> derived.w0
        w0(0.0, 0.434598, 0.920044, 0.991701, 1.0)
        """
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", _ZERO_DIVISION_MESSAGE)
            self.values = numpy.exp(-1.0 / self.subpars.pars.control.k0.values)


class W1(parametertools.Parameter):
    """Weight for calculating interflow [-]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, 1.0)

    CONTROLPARAMETERS = (hland_control.K1,)

    def update(self):
        """Update |W1| based on :math:`W1 = e^{-1/K1}`.

        >>> from hydpy.models.hland import *
        >>> simulationstep("1h")
        >>> parameterstep("1d")
        >>> nmbzones(4)
        >>> k1(0.05, 0.5, 5.0, inf)
        >>> from hydpy import round_
        >>> round_(k1.values)
        1.442695, 12.0, 120.0, inf
        >>> derived.w1.update()
        >>> derived.w1
        w1(0.5, 0.920044, 0.991701, 1.0)
        """
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", _ZERO_DIVISION_MESSAGE)
            self.values = numpy.exp(-1.0 / self.subpars.pars.control.k1.values)


class W2(parametertools.Parameter):
    """Weight for calculating the quick response base flow [-]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, 1.0)

    CONTROLPARAMETERS = (hland_control.K2,)

    def update(self):
        """Update |W2| based on :math:`W2 = e^{-1/K2}`.

        >>> from hydpy.models.hland import *
        >>> simulationstep("1h")
        >>> parameterstep("1d")
        >>> nmbzones(4)
        >>> k2(0.05, 0.5, 5.0, inf)
        >>> from hydpy import round_
        >>> round_(k2.values)
        1.442695, 12.0, 120.0, inf
        >>> derived.w2.update()
        >>> derived.w2
        w2(0.5, 0.920044, 0.991701, 1.0)
        """
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", _ZERO_DIVISION_MESSAGE)
            self.values = numpy.exp(-1.0 / self.subpars.pars.control.k2.values)


class W3(parametertools.Parameter):
    """Weight for calculating the response of the first-order groundwater reservoir
    [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, 1.0)

    CONTROLPARAMETERS = (hland_control.K3,)

    def update(self):
        """Update |W3| based on :math:`W3 = e^{-1/K3}`.

        >>> from hydpy.models.hland import *
        >>> simulationstep("1h")
        >>> parameterstep("1d")
        >>> k3(5.0)
        >>> from hydpy import round_
        >>> round_(k3.value)
        120.0
        >>> derived.w3.update()
        >>> derived.w3
        w3(0.991701)
        """
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", _ZERO_DIVISION_MESSAGE)
            self.values = numpy.exp(-1.0 / self.subpars.pars.control.k3.value)


class K4(parametertools.Parameter):
    """Storage time for very delayed baseflow [T]."""

    NDIM, TYPE, TIME, SPAN = 0, float, False, (0.0, None)

    def update(self):
        """Update |hland_derived.K4| based on :math:`K4 = K3/9`.

        >>> from hydpy.models.hland import *
        >>> simulationstep("1h")
        >>> parameterstep("1d")
        >>> k3(1.0)
        >>> from hydpy import round_
        >>> round_(k3.value)
        24.0
        >>> derived.k4.update()
        >>> derived.k4
        k4(9.0)
        >>> round_(derived.k4.value)
        216.0
        """
        self.values = 9.0 * self.subpars.pars.control.k3.value


class W4(parametertools.Parameter):
    """Weight for calculating the response of the second-order groundwater reservoir
    [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, 1.0)

    DERIVEDPARAMETERS = (K4,)

    def update(self):
        """Update |W4| based on :math:`W4 = e^{-1/K4}`.

        >>> from hydpy.models.hland import *
        >>> simulationstep("1h")
        >>> parameterstep("1d")
        >>> derived.k4(5.0)
        >>> from hydpy import round_
        >>> round_(derived.k4.value)
        120.0
        >>> derived.w4.update()
        >>> derived.w4
        w4(0.991701)
        """
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", _ZERO_DIVISION_MESSAGE)
            self.values = numpy.exp(-1.0 / self.subpars.k4.value)


class UH(parametertools.Parameter):
    """Unit hydrograph ordinates based on an isosceles triangle [-]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, 1.0)
    strict_valuehandling: bool = False

    CONTROLPARAMETERS = (hland_control.MaxBaz,)

    def update(self):
        """Update |UH| based on |MaxBaz|.

        .. note::

            This method also updates the shape of log sequence |QUH|.

        |MaxBaz| determines the endpoint of the triangle.  A value of |MaxBaz| being
        not larger than the simulation step size is identical with applying no unit
        hydrograph at all:

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> simulationstep("12h")
        >>> maxbaz(0.0)
        >>> derived.uh.update()
        >>> logs.quh.shape
        (1,)
        >>> derived.uh
        uh(1.0)

        Note that, due to the given difference of the parameter and the simulation step
        size, the largest assigned value resulting in an "inactive" unit hydrograph is
        1/2:

        >>> maxbaz(0.5)
        >>> derived.uh.update()
        >>> logs.quh.shape
        (1,)
        >>> derived.uh
        uh(1.0)

        When the value of |MaxBaz| is twice the simulation step size, both unit
        hydrograph ordinates must be 1/2 due to the symmetry of the triangle:

        >>> maxbaz(1.0)
        >>> derived.uh.update()
        >>> logs.quh.shape
        (2,)
        >>> derived.uh
        uh(0.5)
        >>> derived.uh.values
        array([0.5, 0.5])

        A |MaxBaz| value three times the simulation step size results in the ordinate
        values 2/9, 5/9, and 2/9:

        >>> maxbaz(1.5)
        >>> derived.uh.update()
        >>> logs.quh.shape
        (3,)
        >>> derived.uh
        uh(0.222222, 0.555556, 0.222222)

        When the end of the triangle lies in the middle of the fourth interval, the
        resulting fractions are:

        >>> maxbaz(1.75)
        >>> derived.uh.update()
        >>> logs.quh.shape
        (4,)
        >>> derived.uh
        uh(0.163265, 0.469388, 0.326531, 0.040816)
        """
        maxbaz = self.subpars.pars.control.maxbaz.value
        quh = self.subpars.pars.model.sequences.logs.quh
        # Determine UH parameters...
        if maxbaz <= 1.0:
            # ...when MaxBaz smaller than or equal to the simulation time step.
            self.shape = 1
            self(1.0)
            quh.shape = 1
        else:
            # ...when MaxBaz is greater than the simulation time step.
            # Define some shortcuts for the following calculations.
            full = maxbaz
            # Now comes a terrible trick due to rounding problems coming from
            # the conversation of the SMHI parameter set to the HydPy
            # parameter set.  Time to get rid of it...
            if (full % 1.0) < 1e-4:
                full //= 1.0
            full_f = int(numpy.floor(full))
            full_c = int(numpy.ceil(full))
            half = full / 2.0
            half_f = int(numpy.floor(half))
            half_c = int(numpy.ceil(half))
            full_2 = full ** 2.0
            # Calculate the triangle ordinate(s)...
            self.shape = full_c
            uh = self.values
            quh.shape = full_c
            # ...of the rising limb.
            points = numpy.arange(1, half_f + 1)
            uh[:half_f] = (2.0 * points - 1.0) / (2.0 * full_2)
            # ...around the peak (if it exists).
            if numpy.mod(half, 1.0) != 0.0:
                uh[half_f] = (half_c - half) / full + (
                    2 * half ** 2.0 - half_f ** 2.0 - half_c ** 2.0
                ) / (2.0 * full_2)
            # ...of the falling limb (eventually except the last one).
            points = numpy.arange(half_c + 1.0, full_f + 1.0)
            uh[half_c:full_f] = 1.0 / full - (2.0 * points - 1.0) / (2.0 * full_2)
            # ...at the end (if not already done).
            if numpy.mod(full, 1.0) != 0.0:
                uh[full_f] = (full - full_f) / full - (full_2 - full_f ** 2.0) / (
                    2.0 * full_2
                )
            # Normalize the ordinates.
            self(uh / numpy.sum(uh))


class KSC(parametertools.Parameter):
    """Coefficient of the individual storages of the linear storage cascade [1/T]."""

    NDIM, TYPE, TIME, SPAN = 0, float, True, (0.0, None)

    CONTROLPARAMETERS = (
        hland_control.MaxBaz,
        hland_control.NmbStorages,
    )

    def update(self):
        """Update |KSC| based on :math:`KSC = \\frac{2 \\cdot NmbStorages}{MaxBaz}`.

        >>> from hydpy.models.hland import *
        >>> simulationstep('12h')
        >>> parameterstep('1d')
        >>> maxbaz(8.0)
        >>> nmbstorages(2.0)
        >>> derived.ksc.update()
        >>> derived.ksc
        ksc(0.5)

        >>> maxbaz(0.0)
        >>> nmbstorages(2.0)
        >>> derived.ksc.update()
        >>> derived.ksc
        ksc(inf)
        """
        control = self.subpars.pars.control
        if control.maxbaz.value <= 0.0:
            self.value = numpy.inf
        else:
            self.value = 2.0 * control.nmbstorages.value / control.maxbaz.value


class QFactor(parametertools.Parameter):
    """Factor for converting mm/stepsize to m³/s."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)

    CONTROLPARAMETERS = (hland_control.Area,)

    def update(self):
        """Update |QFactor| based on |Area| and the current simulation step size.

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> simulationstep("12h")
        >>> area(50.0)
        >>> derived.qfactor.update()
        >>> derived.qfactor
        qfactor(1.157407)
        """
        self(
            self.subpars.pars.control.area
            * 1000.0
            / hydpy.pub.options.simulationstep.seconds
        )
