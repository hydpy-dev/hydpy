# -*- coding: utf-8 -*-

# import...
# ...standard library
from __future__ import division, print_function
# ...third party
import numpy
# ...HydPy specific
from hydpy.core import parametertools
# ...model specific
from hydpy.models.hland.hland_constants import FIELD, FOREST, ILAKE, GLACIER
from hydpy.models.hland.hland_constants import CONSTANTS


class MultiParameter(parametertools.ZipParameter):
    """Base class for handling parameters of the HydPy-H-Land model
    (potentially) handling multiple values.

    Due to inheriting from |ZipParameter|, additional keyword zipping
    functionality is offered.  The optional `kwargs` are checked for
    the keywords `field`, `forest`, `glacier`, `ilake,` and `default`.
    If available, the respective values are used to define the values
    of those 1-dimensional arrays, whose entries are related to the
    different zone types. Also the method
    |parametertools.MultiParameter.compress_repr| tries to find compressed
    string representations based on the mentioned zone types.

    Examples:

        Prepare a |hland_parameters.MultiParameter| instance:

        >>> from hydpy.models.hland.hland_parameters import MultiParameter
        >>> from hydpy.models.hland import *
        >>> parameterstep('1d')
        >>> mp = MultiParameter()
        >>> mp.DIM, mp.TYPE, mp.TIME = 1, float, None
        >>> mp.subpars = control

        Usually, one would indirectly define its shape through parameter
        |NmbZones|:

        >>> mp.shape
        Traceback (most recent call last):
        ...
        RuntimeError: Shape information for parameter `multiparameter` can \
only be retrieved after it has been defined.  You can do this manually, \
but usually it is done automatically by defining the value of \
parameter `nmbzones` first in each parameter control file.

        But here it is set manually to the value 5 for representing
        five different zone types:

        >>> zonetype.shape = 5
        >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, FIELD)
        >>> mp.shape = 5

        Assign values to all four zone types explicitly:

        >>> mp(field=2., forest=1., glacier=4., ilake=3.)
        >>> mp
        multiparameter(field=2.0, forest=1.0, glacier=4.0, ilake=3.0)
        >>> mp.values
        array([ 2.,  1.,  4.,  3.,  2.])

        Specify a default value for all zone types not included in the
        keyword list:

        >>> mp(field=2., forest=1., default=9.)
        >>> mp
        multiparameter(field=2.0, forest=1.0, glacier=9.0, ilake=9.0)
        >>> mp.values
        array([ 2.,  1.,  9.,  9.,  2.])

        If no default value is given, numpys `nan` is applied:

        >>> mp(field=2., forest=1.)
        >>> mp
        multiparameter(field=2.0, forest=1.0, glacier=nan, ilake=nan)
        >>> mp.values
        array([  2.,   1.,  nan,  nan,   2.])

        Of course, the usual value assignments remain unaffected:

        >>> mp.values = 5.
        >>> mp
        multiparameter(5.0)
        >>> mp.values
        array([ 5.,  5.,  5.,  5.,  5.])

        >>> mp.values = 5., 4., 3., 2., 1.
        >>> mp
        multiparameter(5.0, 4.0, 3.0, 2.0, 1.0)
        >>> mp.values
        array([ 5.,  4.,  3.,  2.,  1.])

    Another feature of |hland_parameters.MultiParameter| is that it
    relates the |property| |parametertools.MultiParameter.verifymask|
    to the defined zone types.  This requires the definition of the
    class attribute |hland_parameters.MultiParameter.REQUIRED_VALUES|
    for |hland_parameters.MultiParameter| subclasses.

    Examples:

        When values for all zone types are required, all entries of the
        verification mask are `True`:

        >>> mp.REQUIRED_VALUES = (FIELD, FOREST, GLACIER, ILAKE)
        >>> mp.verifymask
        array([ True,  True,  True,  True,  True], dtype=bool)

        When values for field and forest zones are required only, the
        entries related to glacier and ilake zones are `False`:

        >>> mp.REQUIRED_VALUES = (FIELD, FOREST)
        >>> mp.verifymask
        array([ True,  True, False, False,  True], dtype=bool)

    """
    REQUIRED_VALUES = (FIELD, FOREST, GLACIER, ILAKE)
    MODEL_CONSTANTS = CONSTANTS

    @property
    def refparameter(self):
        """Alias for the associated instance of |ZoneType|.
        """
        return self.subpars.pars.control.zonetype

    @property
    def shapeparameter(self):
        """Alias for the associated instance of |NmbZones|.
        """
        return self.subpars.pars.control.nmbzones


class MultiParameterSoil(MultiParameter):
    """Base class for handling parameters of the hland model (potentially)
    handling multiple values relevant for `soil zones` (and interception).
    """
    REQUIRED_VALUES = (FIELD, FOREST)


class MultiParameterLand(MultiParameter):
    """Base class for handling parameters of the hland model (potentially)
    handling multiple values relevant for all `land zones`.
    """
    REQUIRED_VALUES = (FIELD, FOREST, GLACIER)


class MultiParameterLake(MultiParameter):
    """Base class for handling parameters of the hland model (potentially)
    handling multiple values relevant for `lake zones` only.
    """
    REQUIRED_VALUES = (ILAKE,)


class MultiParameterGlacier(MultiParameter):
    """Base class for handling parameters of the hland model (potentially)
    handling multiple values relevant for `glacier zones` only.
    """
    REQUIRED_VALUES = (GLACIER,)


class MultiParameterNoGlacier(MultiParameter):
    """Base class for handling parameters of the hland model (potentially)
    handling multiple values relevant for `glacier free zones` only.
    """
    REQUIRED_VALUES = (FIELD, FOREST, ILAKE)


class Parameters(parametertools.Parameters):
    """All parameters of the hland model."""

    def update(self):
        """Determine the values of the parameters handled by
        |DerivedParameters| based on the values of the parameters
        handled by |ControlParameters|.  The results of the different
        methods are not interdependent, meaning their order could be changed.
        """
        self.calc_relzonearea()
        self.calc_landzonearea()
        self.calc_soilarea()
        self.calc_ttm()
        self.calc_dt()
        self.calc_nmbuh_uh()
        self.calc_qfactor()

    def calc_relzonearea(self):
        """Calculate the relative areas of all zones within the subbasin.

        Required control parameters:
          |ZoneArea|

        Calculated derived parameters:
          |RelZoneArea|

        Examples:

            With one single zone, its relative area is one by definition:

            >>> from hydpy.models.hland import *
            >>> parameterstep('1d')
            >>> nmbzones(1)
            >>> zonearea(1111.)
            >>> model.parameters.calc_relzonearea()
            >>> derived.relzonearea
            relzonearea(1.0)

            An example for three zones of different sizes:

            >>> nmbzones(3)
            >>> zonearea(1., 3., 2.)
            >>> model.parameters.calc_relzonearea()
            >>> derived.relzonearea
            relzonearea(0.166667, 0.5, 0.333333)

        """
        con = self.control
        der = self.derived
        der.relzonearea(con.zonearea/sum(con.zonearea))

    def calc_landzonearea(self):
        """Calculate the fraction of the summed area of all "land zones"
        (of type FIELD, FOREST, or ILAKE) and the total subbasin area, and
        calculate the fractions of all "land zones" and the total "land area"
        of the subbasin.

        Required control parameters:
          |Area|
          |ZoneArea|
          |ZoneType|

        Calculated derived parameters:
          |RelLandArea|
          |RelLandZoneArea|

        Examples:

            With all zones being "land zones", the relative land area is
            one by definition and the relative "land zone" areas are in
            accordance with the original zone areas:

            >>> from hydpy.models.hland import *
            >>> parameterstep('1d')
            >>> nmbzones(3)
            >>> zonetype(FIELD, FOREST, GLACIER)
            >>> area(100.)
            >>> zonearea(25., 25., 50.)
            >>> model.parameters.calc_landzonearea()
            >>> derived.rellandarea
            rellandarea(1.0)
            >>> derived.rellandzonearea
            rellandzonearea(field=0.25, forest=0.25, glacier=0.5)

            With one zone being a lake zone, the relative "land area" is
            decreased and the relative "land zone" areas are increased ---
            except the one related to the internal lake, which is set to zero:

            >>> zonetype(FIELD, FOREST, ILAKE)
            >>> model.parameters.calc_landzonearea()
            >>> derived.rellandarea
            rellandarea(0.5)
            >>> derived.rellandzonearea
            rellandzonearea(field=0.5, forest=0.5, ilake=0.0)

            With all zones being lake zones, all relative areas are zero:

            >>> zonetype(ILAKE, ILAKE, ILAKE)
            >>> model.parameters.calc_landzonearea()
            >>> derived.rellandarea
            rellandarea(0.0)
            >>> derived.rellandzonearea
            rellandzonearea(0.0)

        """
        con = self.control
        der = self.derived
        landzonearea = con.zonearea.values.copy()
        landzonearea[con.zonetype.values == ILAKE] = 0.
        landarea = numpy.sum(landzonearea)
        if landarea > 0.:
            der.rellandzonearea(landzonearea/landarea)
        else:
            der.rellandzonearea(0.)
        der.rellandarea(landarea/con.area)

    def calc_soilarea(self):
        """Calculate the fraction of the summed area of all "soil zones"
        (of type FIELD or FOREST) and the total subbasin area, and
        calculate the fractions of all "soil zones" and the total "soil area"
        of the subbasin.

        Required control parameters:
          |Area|
          |ZoneArea|
          |ZoneType|

        Calculated derived parameters:
          |RelSoilArea|
          |RelSoilZoneArea|

        Examples:

            With all zones being "soil zones", the relative land area is
            one by definition and the relative "soil zone" areas are in
            accordance with the original zone areas:

            >>> from hydpy.models.hland import *
            >>> parameterstep('1d')
            >>> nmbzones(4)
            >>> zonetype(FIELD, FOREST, FIELD, FOREST)
            >>> area(100.)
            >>> zonearea(25., 25., 25., 25.)
            >>> model.parameters.calc_soilarea()
            >>> derived.relsoilarea
            relsoilarea(1.0)
            >>> derived.relsoilzonearea
            relsoilzonearea(0.25)

            With one zone being a lake zone one one zone being a glacier
            zone, the relative "soil area" is decreased and the relative
            "soil zone" areas are increased --- except the ones related to
            the internal lake and the glacier, which are set to zero:

            >>> zonetype(FIELD, FOREST, GLACIER, ILAKE)
            >>> model.parameters.calc_soilarea()
            >>> derived.relsoilarea
            relsoilarea(0.5)
            >>> derived.relsoilzonearea
            relsoilzonearea(field=0.5, forest=0.5, glacier=0.0, ilake=0.0)

            With all zones being lake or glacier zones, all relative areas
            are zero:

            >>> zonetype(GLACIER, GLACIER, ILAKE, ILAKE)
            >>> model.parameters.calc_soilarea()
            >>> derived.relsoilarea
            relsoilarea(0.0)
            >>> derived.relsoilzonearea
            relsoilzonearea(0.0)

        """
        con = self.control
        der = self.derived
        soilzonearea = con.zonearea.values.copy()
        soilzonearea[con.zonetype.values == GLACIER] = 0.
        soilzonearea[con.zonetype.values == ILAKE] = 0.
        soilarea = numpy.sum(soilzonearea)
        if soilarea > 0.:
            der.relsoilzonearea(soilzonearea/soilarea)
        else:
            der.relsoilzonearea(0.)
        der.relsoilarea(soilarea/con.area)

    def calc_ttm(self):
        """Calculate the threshold temperature for melting and refreezing.

        Required control parameters:
          |TT|
          |DTTM|

        Calculated derived parameter:
          |TTM|

        Basic equation:
          :math:`TTM = TT+DTTM`

        Example:

            >>> from hydpy.models.hland import *
            >>> parameterstep('1d')
            >>> nmbzones(1)
            >>> tt(1.)
            >>> dttm(-2.)
            >>> model.parameters.calc_ttm()
            >>> derived.ttm
            ttm(-1.0)
        """
        con = self.control
        der = self.derived
        der.ttm(con.tt+con.dttm)

    def calc_dt(self):
        """Determine the relative time step size for solving the upper
        zone layer routine.

        Required control parameter:
          |RecStep|

        Calculated derived parameter:
          |DT|

        Basic equation:
          :math:`DT = \\frac{1}{RecStep}`

        Examples:

            >>> from hydpy.models.hland import *
            >>> parameterstep('1d')
            >>> simulationstep('12h')
            >>> recstep(2.)
            >>> model.parameters.calc_dt()
            >>> derived.dt
            dt(1.0)
            >>> recstep(10.)
            >>> model.parameters.calc_dt()
            >>> derived.dt
            dt(0.2)

            Note that the value assigned to recstep is related to the given
            parameter step size of one day.  The actually applied recstep of
            the last example is:

            >>> recstep.value
            5

        """
        con = self.control
        der = self.derived
        der.dt(1./con.recstep)

    def calc_qfactor(self):
        """Determine the factor for converting values of |QT| [mm/T] to
        values of |Q| [m³/s].

        Required control parameter:
          |Area|

        Calculated derived parameter:
          |QFactor|

        Example:

            >>> from hydpy.models.hland import *
            >>> parameterstep('1d')
            >>> simulationstep('12h')
            >>> area(50.)
            >>> model.parameters.calc_qfactor()
            >>> derived.qfactor
            qfactor(1.157407)

        """
        con = self.control
        der = self.derived
        der.qfactor(con.area*1000./der.qfactor.simulationstep.seconds)

    def calc_nmbuh_uh(self):
        """Calculate the ordinates of the triangle unit hydrograph.

        Note that also the shape of sequence |QUH| is defined in accordance
        with NmbUH.

        Required control parameter:
          |MaxBaz|

        Calculated derived parameters:
          NmbUH
          UH

        Prepared log sequence:
          |QUH|

        Examples:

            MaxBaz determines the end point of the triangle.  A value of
            MaxBaz being not larger than the simulation step size is
            identical with applying no unit hydrograph at all:

            >>> from hydpy.models.hland import *
            >>> parameterstep('1d')
            >>> simulationstep('12h')
            >>> maxbaz(0.)
            >>> model.parameters.calc_nmbuh_uh()
            >>> derived.nmbuh
            nmbuh(1)
            >>> logs.quh.shape
            (1,)
            >>> derived.uh
            uh(1.0)

            Note that, due to difference of the parameter and the simulation
            step size in the given example, the largest assignement resulting
            in a `inactive` unit hydrograph is 1/2:

            >>> maxbaz(0.5)
            >>> model.parameters.calc_nmbuh_uh()
            >>> derived.nmbuh
            nmbuh(1)
            >>> logs.quh.shape
            (1,)
            >>> derived.uh
            uh(1.0)

            When MaxBaz is in accordance with two simulation steps, both
            unit hydrograph ordinats must be 1/2, due to symmetry of the
            triangle:

            >>> maxbaz(1.)
            >>> model.parameters.calc_nmbuh_uh()
            >>> derived.nmbuh
            nmbuh(2)
            >>> logs.quh.shape
            (2,)
            >>> derived.uh
            uh(0.5)

            A MaxBaz value in accordance with three simulation steps results
            --- when expressed as fractions --- in the ordinate values 2/9,
            5/9, and 2/9:

            >>> maxbaz(1.5)
            >>> model.parameters.calc_nmbuh_uh()
            >>> derived.nmbuh
            nmbuh(3)
            >>> logs.quh.shape
            (3,)
            >>> derived.uh
            uh(0.222222, 0.555556, 0.222222)

            And a final example, where the end of the triangle lies within
            a simulation step, resulting in the fractions 8/49, 23/49, 16/49,
            and 2/49:

            >>> maxbaz(1.75)
            >>> model.parameters.calc_nmbuh_uh()
            >>> derived.nmbuh
            nmbuh(4)
            >>> logs.quh.shape
            (4,)
            >>> derived.uh
            uh(0.163265, 0.469388, 0.326531, 0.040816)

        """
        con = self.control
        der = self.derived
        log = self.model.sequences.logs
        # Determine UH parameters...
        if con.maxbaz <= 1.:
            # ...when MaxBaz smaller than or equal to the simulation time step.
            der.nmbuh = 1
            der.uh.shape = 1
            der.uh(1.)
            log.quh.shape = 1
        else:
            # ...when MaxBaz is greater than the simulation time step.
            # Define some shortcuts for the following calculations.
            full = con.maxbaz.value
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
            der.nmbuh(full_c)
            der.uh.shape = full_c
            log.quh.shape = full_c
            # ...of the rising limb.
            points = numpy.arange(1, half_f+1)
            der.uh[:half_f] = (2.*points-1.)/(2.*full_2)
            # ...around the peak (if it exists).
            if numpy.mod(half, 1.) != 0.:
                der.uh[half_f] = \
                    ((half_c-half)/full +
                     (2*half**2.-half_f**2.-half_c**2.)/(2.*full_2))
            # ...of the falling limb (eventually except the last one).
            points = numpy.arange(half_c+1., full_f+1.)
            der.uh[half_c:full_f] = 1./full-(2.*points-1.)/(2.*full_2)
            # ...at the end (if not already done).
            if numpy.mod(full, 1.) != 0.:
                der.uh[full_f] = ((full-full_f)/full -
                                  (full_2-full_f**2.)/(2.*full_2))
            # Normalize the ordinates.
            der.uh(der.uh/numpy.sum(der.uh))
