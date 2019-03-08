# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from site-packages
import numpy
# ...from HydPy
from hydpy.core import parametertools
# ...from hland
from hydpy.models.hland import hland_parameters
from hydpy.models.hland.hland_constants import ILAKE, GLACIER


class RelSoilArea(parametertools.Parameter):
    """Relative area of all |FIELD| and |FOREST| zones [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., 1.)

    def update(self):
        """Update |RelSoilArea| based on |Area|, |ZoneArea|, and |ZoneType|.

        >>> from hydpy.models.hland import *
        >>> parameterstep('1d')
        >>> nmbzones(4)
        >>> zonetype(FIELD, FOREST, GLACIER, ILAKE)
        >>> area(100.0)
        >>> zonearea(10.0, 20.0, 30.0, 40.0)
        >>> derived.relsoilarea.update()
        >>> derived.relsoilarea
        relsoilarea(0.3)
        """
        con = self.subpars.pars.control
        temp = con.zonearea.values.copy()
        temp[con.zonetype.values == GLACIER] = 0.
        temp[con.zonetype.values == ILAKE] = 0.
        self(numpy.sum(temp)/con.area)


class RelLandArea(parametertools.Parameter):
    """Relative area of all |FIELD|, |FOREST|, and |GLACIER| zones [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., 1.)

    def update(self):
        """Update |RelLandArea| based on |Area|, |ZoneArea|, and |ZoneType|.

        >>> from hydpy.models.hland import *
        >>> parameterstep('1d')
        >>> nmbzones(4)
        >>> zonetype(FIELD, FOREST, GLACIER, ILAKE)
        >>> area(100.0)
        >>> zonearea(10.0, 20.0, 30.0, 40.0)
        >>> derived.rellandarea.update()
        >>> derived.rellandarea
        rellandarea(0.6)
        """
        con = self.subpars.pars.control
        temp = con.zonearea.values.copy()
        temp[con.zonetype.values == ILAKE] = 0.
        self(numpy.sum(temp)/con.area)


class RelZoneArea(hland_parameters.ParameterComplete,
                  parametertools.RelSubweightsMixin):
    """Relative zone area of all zone types [-].

    >>> from hydpy.models.hland import *
    >>> parameterstep('1d')
    >>> nmbzones(4)
    >>> zonetype(FIELD, FOREST, GLACIER, ILAKE)
    >>> zonearea(10.0, 40.0, 20.0, 30.0)
    >>> derived.relzonearea.update()
    >>> derived.relzonearea
    relzonearea(field=0.1, forest=0.4, glacier=0.2, ilake=0.3)
    """
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., 1.)
    strict_valuehandling = False


class RelSoilZoneArea(hland_parameters.ParameterSoil,
                      parametertools.RelSubweightsMixin):
    """Relative zone area of all |FIELD| and |FOREST| zones [-].

    >>> from hydpy.models.hland import *
    >>> parameterstep('1d')
    >>> nmbzones(4)
    >>> zonetype(FIELD, FOREST, GLACIER, ILAKE)
    >>> zonearea(10.0, 40.0, 20.0, 30.0)
    >>> derived.relsoilzonearea.update()
    >>> derived.relsoilzonearea
    relsoilzonearea(field=0.2, forest=0.8)
    """
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., 1.)
    strict_valuehandling = False


class RelLandZoneArea(hland_parameters.ParameterLand,
                      parametertools.RelSubweightsMixin):
    """Relative zone area of all |FIELD|, |FOREST|, and |GLACIER| zones [-].

    >>> from hydpy.models.hland import *
    >>> parameterstep('1d')
    >>> nmbzones(4)
    >>> zonetype(FIELD, FOREST, GLACIER, ILAKE)
    >>> zonearea(10.0, 40.0, 20.0, 30.0)
    >>> derived.rellandzonearea.update()
    >>> derived.rellandzonearea
    rellandzonearea(field=0.142857, forest=0.571429, glacier=0.285714)
    """
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., 1.)
    strict_valuehandling = False


class TTM(hland_parameters.ParameterLand):
    """Threshold temperature for snow melting and refreezing [°C]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)

    def update(self):
        """Update |TTM| based on :math:`TTM = TT+DTTM`.

        >>> from hydpy.models.hland import *
        >>> parameterstep('1d')
        >>> nmbzones(1)
        >>> zonetype(FIELD)
        >>> tt(1.0)
        >>> dttm(-2.0)
        >>> derived.ttm.update()
        >>> derived.ttm
        ttm(-1.0)
        """
        con = self.subpars.pars.control
        self(con.tt+con.dttm)


class DT(parametertools.Parameter):
    """Relative time step length for the upper zone layer calculations [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., 1.)

    def update(self):
        """Update |DT| based on :math:`DT = \\frac{1}{RecStep}`.

        >>> from hydpy.models.hland import *
        >>> parameterstep('1d')
        >>> simulationstep('12h')
        >>> recstep(2.0)
        >>> derived.dt.update()
        >>> derived.dt
        dt(1.0)
        >>> recstep(10.0)
        >>> derived.dt.update()
        >>> derived.dt
        dt(0.2)

        Note that the value assigned to recstep is related to the given
        parameter step size of one day.  The actually applied recstep of
        the last example is:

        >>> recstep.value
        5
        """
        self(1/self.subpars.pars.control.recstep)


class UH(parametertools.Parameter):
    """Unit hydrograph ordinates based on a isosceles triangle [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., 1.)
    strict_valuehandling = False

    def update(self):
        """Update |UH| based on |MaxBaz|.

        .. note::

            This method also updates the shape of log sequence |QUH|.

        |MaxBaz| determines the end point of the triangle.  A value of
        |MaxBaz| being not larger than the simulation step size is
        identical with applying no unit hydrograph at all:

        >>> from hydpy.models.hland import *
        >>> parameterstep('1d')
        >>> simulationstep('12h')
        >>> maxbaz(0.0)
        >>> derived.uh.update()
        >>> logs.quh.shape
        (1,)
        >>> derived.uh
        uh(1.0)

        Note that, due to difference of the parameter and the simulation
        step size in the given example, the largest assignment resulting
        in a `inactive` unit hydrograph is 1/2:

        >>> maxbaz(0.5)
        >>> derived.uh.update()
        >>> logs.quh.shape
        (1,)
        >>> derived.uh
        uh(1.0)

        When |MaxBaz| is in accordance with two simulation steps, both
        unit hydrograph ordinats must be 1/2 due to symmetry of the
        triangle:

        >>> maxbaz(1.0)
        >>> derived.uh.update()
        >>> logs.quh.shape
        (2,)
        >>> derived.uh
        uh(0.5)
        >>> derived.uh.values
        array([ 0.5,  0.5])

        A |MaxBaz| value in accordance with three simulation steps results
        in the ordinate values 2/9, 5/9, and 2/9:

        >>> maxbaz(1.5)
        >>> derived.uh.update()
        >>> logs.quh.shape
        (3,)
        >>> derived.uh
        uh(0.222222, 0.555556, 0.222222)

        And a final example, where the end of the triangle lies within
        a simulation step, resulting in the fractions 8/49, 23/49, 16/49,
        and 2/49:

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
        if maxbaz <= 1.:
            # ...when MaxBaz smaller than or equal to the simulation time step.
            self.shape = 1
            self(1.)
            quh.shape = 1
        else:
            # ...when MaxBaz is greater than the simulation time step.
            # Define some shortcuts for the following calculations.
            full = maxbaz
            # Now comes a terrible trick due to rounding problems coming from
            # the conversation of the SMHI parameter set to the HydPy
            # parameter set.  Time to get rid of it...
            if (full % 1.) < 1e-4:
                full //= 1.
            full_f = int(numpy.floor(full))
            full_c = int(numpy.ceil(full))
            half = full/2.
            half_f = int(numpy.floor(half))
            half_c = int(numpy.ceil(half))
            full_2 = full**2.
            # Calculate the triangle ordinate(s)...
            self.shape = full_c
            uh = self.values
            quh.shape = full_c
            # ...of the rising limb.
            points = numpy.arange(1, half_f+1)
            uh[:half_f] = (2.*points-1.)/(2.*full_2)
            # ...around the peak (if it exists).
            if numpy.mod(half, 1.) != 0.:
                uh[half_f] = (
                    (half_c-half)/full +
                    (2*half**2.-half_f**2.-half_c**2.)/(2.*full_2))
            # ...of the falling limb (eventually except the last one).
            points = numpy.arange(half_c+1., full_f+1.)
            uh[half_c:full_f] = 1./full-(2.*points-1.)/(2.*full_2)
            # ...at the end (if not already done).
            if numpy.mod(full, 1.) != 0.:
                uh[full_f] = (
                    (full-full_f)/full-(full_2-full_f**2.)/(2.*full_2))
            # Normalize the ordinates.
            self(uh/numpy.sum(uh))


class QFactor(parametertools.Parameter):
    """Factor for converting mm/stepsize to m³/s."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

    def update(self):
        """Update |QFactor| based on |Area| and the current simulation
        step size.

        >>> from hydpy.models.hland import *
        >>> parameterstep('1d')
        >>> simulationstep('12h')
        >>> area(50.0)
        >>> derived.qfactor.update()
        >>> derived.qfactor
        qfactor(1.157407)
        """
        self(self.subpars.pars.control.area*1000. /
             self.subpars.qfactor.simulationstep.seconds)


class DerivedParameters(parametertools.SubParameters):
    """Derived parameters of HydPy-H-Land, indirectly defined by the user."""
    CLASSES = (RelZoneArea,
               RelSoilArea,
               RelSoilZoneArea,
               RelLandZoneArea,
               RelLandArea,
               TTM,
               DT,
               UH,
               QFactor)
