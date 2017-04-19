# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
import warnings
# ...from site-packages
import numpy
# ...HydPy specific
from hydpy.core import parametertools
from hydpy.core import objecttools
from hydpy.core import timetools
# ...model specific
from hydpy.models.lland import lland_constants
from hydpy.models.lland import lland_parameters

class FT(parametertools.SingleParameter):
    """Teileinzugsgebietsfläche (subbasin area) [km²]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (1e-10, None)

class NHRU(parametertools.SingleParameter):
    """Anzahl der Hydrotope (number of hydrological response units) [-].

    Note that :class:`NHRU` determines the length of most 1-dimensional
    HydPy-L-Land parameters and sequences.  This required that the value of
    the respective :class:`NHRU` instance is set before any of the values
    of these 1-dimensional parameters or sequences are set.  Changing the
    value of the :class:`NHRU` instance necessitates setting their values
    again.

    Examples:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(5)
        >>> control.kg.shape
        (5,)
        >>> fluxes.tkor.shape
        (5,)
    """
    NDIM, TYPE, TIME, SPAN = 0, int, None, (1, None)

    def __call__(self, *args, **kwargs):
        """The prefered way to pass a value to :class:`NHRU` instances
        within parameter control files.  Sets the shape of the associated
        1-dimensional parameter and sequence objects additionally.
        """
        parametertools.SingleParameter.__call__(self, *args, **kwargs)
        for (_name, subpars) in self.subpars.pars.model.parameters:
            for (name, par) in subpars:
                if par.NDIM == 1:
                    par.shape = self.value
        for (_name, subseqs) in self.subpars.pars.model.sequences:
            for (name, seq) in subseqs:
                if (seq.NDIM == 1) and (seq.name != 'moy'):
                    seq.shape = self.value

class FHRU(lland_parameters.MultiParameter):
    """Flächenanteile der Hydrotope (area percentages of the respective
    HRUs) [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., 1.)

class Lnk(lland_parameters.MultiParameter):
    """Landnutzungsklasse (land use class) [-].

    For increasing legibility, the HydPy-L-Land constants are used for string
    representions of :class:`Lnk` instances:

    >>> from hydpy.models.lland import *
    >>> parameterstep('1d')
    >>> nhru(4)
    >>> lnk(ACKER, ACKER, WASSER, MISCHW)
    >>> lnk.values
    array([ 4,  4, 16, 15])
    >>> lnk
    lnk(ACKER, ACKER, WASSER, MISCHW)
    """
    NDIM, TYPE, TIME = 1, int, None
    SPAN = (min(lland_constants.CONSTANTS.values()),
            max(lland_constants.CONSTANTS.values()))

    def compressrepr(self):
        """Returns a list which contains a string representation with land
        uses beeing defined by the constants
        :const:`~hydpy.models.lland.lland_constants.SIED_D`,
        :const:`~hydpy.models.lland.lland_constants.SIED_L`...
        """
        invmap = {value: key for key, value in
                  lland_constants.CONSTANTS.items()}
        return [', '.join(invmap.get(value, repr(value))
                          for value in self.values)]

class HNN(lland_parameters.MultiParameter):
    """Höhe über Normal-Null (height above sea level) [m]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)

class KG(lland_parameters.MultiParameter):
    """Niederschlagskorrekturfaktor (adjustment factor for precipitation)
    [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

class KT(lland_parameters.MultiParameter):
    """Temperaturkorrekturfaktor (adjustment factor for air temperature)
    [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)

class KE(lland_parameters.MultiParameter):
    """Grasreferenzverdunstungskorrekturfaktor (adjustment factor for
    reference evapotranspiration) [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, True, (0., None)

class KF(lland_parameters.MultiParameter):
    """Küstenfaktor ("coast factor" of Turc-Wendling's evaporation equation
    [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (.6, 1.)

class FLn(lland_parameters.LanduseMonthParameter):
    """Landnutzungsabhängiger Verdunstungsfaktor (factor for adjusting
    reference evapotranspiration to different land use classes) [-]."""
    NDIM, TYPE, TIME, SPAN = 2, float, None, (0., None)

class HInz(parametertools.SingleParameter):
    """Interzeptionskapazität bezogen auf die Blattoberfläche (interception
    capacity normalized to the leaf surface area) [mm]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

class LAI(lland_parameters.LanduseMonthParameter):
    """Blattflächenindex (leaf area index) [-]."""
    NDIM, TYPE, TIME, SPAN = 2, float, None, (0., None)

class TRefT(lland_parameters.MultiParameter):
    """Lufttemperaturgrenzwert des grundlegenden Grad-Tag-Verfahrens
    (air temperature threshold of the degree-day method) [°C]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)

class TRefN(lland_parameters.MultiParameter):
    """Niederschlagstemperaturgrenzwert des erweiterten Grad-Tag-Verfahrens
    (precipitation temperature threshold of the degree-day method) [°C]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)

class TGr(lland_parameters.MultiParameter):
    """Temperaturgrenzwert flüssiger/fester Niederschlag (threshold
    temperature liquid/frozen precipitation) [°C]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)

class GTF(lland_parameters.MultiParameter):
    """Grad-Tag-Faktor (factor of the degree-day method) [mm/°C/T]."""
    NDIM, TYPE, TIME, SPAN = 1, float, True, (0., None)

class RSchmelz(parametertools.SingleParameter):
    """Spezifische Schmelzwärme von Wasser (specific melt heat of water)
    [J/g]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)
    INIT = 334.

class CPWasser(parametertools.SingleParameter):
    """Spezifische Wärmekapazität von Wasser (specific heat capacity of water)
    [J/g]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)
    INIT = 4.1868

class PWMax(lland_parameters.MultiParameter):
    """Maximalverhältnis Gesamt- zu Trockenschnee (maximum ratio of the
    total and the frozen water equivalent stored in the snow cover) [-].

    In addition to the :class:`parametertools.SingleParameter` call method, it
    is possible to set the value of parameter :class:`PWMax` in accordance to
    the keyword arguments `rhot0` and `rhodkrit`.

    Basic Equation:
        :math:`PWMax = \\frac{1.474 \\cdot rhodkrit}
        {rhot0 + 0.474 \\cdot rhodkrit}`

    Example:
        Using the common values for both rhot0 and rhodkrit...

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(1)
        >>> lnk(ACKER)
        >>> pwmax(rhot0=0.2345, rhodkrit=0.42)

        ...leads to,...

        >>> pwmax
        pwmax(1.427833)

        This is also the default value of :class:`PWMax` and means that
        the proportion of the liquid water in the snow cover cannot go
        above 30%.
    """
    NDIM, TYPE, TIME, SPAN = 1, float, None, (1., None)

    def __call__(self, *args, **kwargs):
        """The prefered way to pass values to :class:`PWMax` instances
        within parameter control files.
        """
        try:
            lland_parameters.MultiParameter.__call__(self, *args, **kwargs)
        except NotImplementedError:
            counter = ('rhot0' in kwargs) + ('rhodkrit' in kwargs)
            if counter == 0:
                raise ValueError('For parameter `pwmax` a value can be set '
                                 'directly by passing a single value or '
                                 'indirectly by using the keyword arguments '
                                 '`rhot0` and `rhodkrit`.')
            elif counter == 1:
                raise ValueError('For the alternative calculation of '
                                 'parameter `pwmax`, values for both keyword '
                                 'keyword arguments `rhot0` and `rhodkrit` '
                                 'must be given.')
            else:
                rhot0 = float(kwargs['rhot0'])
                rhodkrit = float(kwargs['rhodkrit'])
                self(1.474*rhodkrit/(rhot0+0.474*rhodkrit))

class GrasRef_R(parametertools.SingleParameter):
    """Bodenfeuchte-Verdunstung-Parameter (soil moisture dependend
    evaporation factor) [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

class NFk(lland_parameters.MultiParameter):
    """Nutzbare Feldkapazität (usable field capacity) [mm]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

class RelWZ(lland_parameters.MultiParameter):
    """Relative Mindestbodenfeuchte für die Interflowentstehung (threshold
       value of relative soil moisture for interflow generation) [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, 1.)

    def trim(self, lower=None, upper=None):
        """Trim upper values in accordance with :math:`RelWB \\leq RelWZ`.

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> hru(3)
        >>> relwb.values = .5
        >>> relwz(0.2, .5, .8)
        >>> relwz
        relwz(0.5, 0.5, 0.8)
        """
        relwb = self.subpars.relwb.value
        if (lower is None) and (relwb is not None):
            lower = relwb
        lland_parameters.MultiParameter.trim(self, lower, upper)

class RelWB(lland_parameters.MultiParameter):
    """Relative Mindestbodenfeuchte für die Basisabflussentstehung (threshold
       value of relative soil moisture for base flow generation) [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

    def trim(self, lower=None, upper=None):
        """Trim upper values in accordance with :math:`RelWB \\leq RelWZ`.

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> hru(3)
        >>> relwz.values = .5
        >>> relwb(0.2, .5, .8)
        >>> relwb
        relwb(0.2, 0.5, 0.5)
        """
        relwz = self.subpars.relwz.value
        if (upper is None) and (relwz is not None):
            upper = relwz
        lland_parameters.MultiParameter.trim(self, lower, upper)

class Beta(lland_parameters.MultiParameter):
    """Drainageindex des tiefen Bodenspeichers (storage coefficient for
    releasing base flow from the lower soil compartment) [1/T]."""
    NDIM, TYPE, TIME, SPAN = 1, float, True, (0., None)

class DMin(lland_parameters.MultiParameter):
    """Drainageindex des mittleren Bodenspeichers (flux rate for
    releasing interflow from the middle soil compartment) [mm/T].

    In addition to the :class:`parametertools.MultiParameter` call method, it
    is possible to set the value of parameter :class:`DMin` in accordance to
    the keyword argument `r_dmin` due to compatibility reasons with the
    original LARSIM implemetation.

    Basic Equation:
        :math:`Dmin = 0.024192 \\cdot r_dmin`

    Example:
        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> simulationstep('12h')
        >>> nhru(1)
        >>> lnk(ACKER)
        >>> dmax(10.) # to prevent trimming of dmin, see below
        >>> dmin(r_dmin=10.)
        >>> dmin
        dmin(0.24192)

        Note the additional dependence of the parameter value on the
        relation between the `parameterstep` and the actual `simulationstep`:

        >>> dmin.values
        array([ 0.12096])
    """
    NDIM, TYPE, TIME, SPAN = 1, float, True, (0., None)

    def __call__(self, *args, **kwargs):
        """The prefered way to pass values to :class:`DMin` instances
        within parameter control files.
        """
        try:
            lland_parameters.MultiParameter.__call__(self, *args, **kwargs)
        except NotImplementedError:
            args = kwargs.get('r_dmin')
            if args is not None:
                self.values = 0.024192*self.applytimefactor(numpy.array(args))
                self.trim()
            else:
                objecttools.augmentexcmessage()

    def trim(self, lower=None, upper=None):
        """Trim upper values in accordance with :math:`DMin \\leq DMax`.

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> simulationstep('12h')
        >>> nhru(5)
        >>> dmax.values = 2.
        >>> dmin(-2., 0., 2., 4., 6.)
        >>> dmin
        dmin(0.0, 0.0, 2.0, 4.0, 4.0)
        """
        if upper is None:
            upper = self.subpars.dmax
        lland_parameters.MultiParameter.trim(self, lower, upper)

class DMax(lland_parameters.MultiParameter):
    """Drainageindex des oberen Bodenspeichers (additional flux rate for
    releasing interflow from the upper soil compartment) [mm/T].

    In addition to the :class:`parametertools.MultiParameter` call method, it
    is possible to set the value of parameter :class:`DMax` in accordance to
    the keyword argument `r_dmax` due to compatibility reasons with the
    original LARSIM implemetation.

    Basic Equation:
        :math:`Dmax = 2.4192 \\cdot r_dmax`

    Example:
        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> simulationstep('12h')
        >>> nhru(1)
        >>> lnk(ACKER)
        >>> dmin(0.) # to prevent trimming of dmax, see below
        >>> dmax(r_dmax=10.)
        >>> dmax
        dmax(24.192)

        Note the additional dependence of the parameter value on the
        relation between the `parameterstep` and the actual `simulationstep`:

        >>> dmax.values
        array([ 12.096])
    """
    NDIM, TYPE, TIME, SPAN = 1, float, True, (None, None)

    def __call__(self, *args, **kwargs):
        """The prefered way to pass values to :class:`DMin` instances
        within parameter control files.
        """
        try:
            lland_parameters.MultiParameter.__call__(self, *args, **kwargs)
        except NotImplementedError:
            args = kwargs.get('r_dmax')
            if args is not None:
                self.values = 2.4192*self.applytimefactor(numpy.array(args))
                self.trim()
            else:
                objecttools.augmentexcmessage()

    def trim(self, lower=None, upper=None):
        """Trim upper values in accordance with :math:`DMax \\geq DMin`.

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> simulationstep('12h')
        >>> nhru(3)
        >>> dmin.values = 2.
        >>> dmax(2., 4., 6.)
        >>> dmax
        dmax(4.0, 4.0, 6.0)
        """
        if lower is None:
            lower = self.subpars.dmin
        lland_parameters.MultiParameter.trim(self, lower, upper)

class BSf(lland_parameters.MultiParameter):
    """Bodenfeuchte-Sättigungsfläche-Parameter (shape parameter for the
    relation between the avarage soil moisture and the relative saturated
    area of a subbasin) [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

class TInd(parametertools.SingleParameter):
    """Fließzeitindex (factor related to the time of concentration) [T].

    In addition to the :class:`parametertools.SingleParameter` call method, it
    is possible to set the value of parameter :class:`TInd` in accordance to
    the keyword arguments `tal` (talweg, [km]), `hot` (higher reference
    altitude, [m]), and `hut` (lower reference altitude, [m]).  This is
    supposed to decrease the time of runoff concentration in small and/or
    steep catchments.  Note that :class:`TInd` does not only affect direct
    runoff, but interflow and base flow as well.  Hence it seems advisable
    to use this regionalization strategy with caution.

    Basic Equation:
        :math:`TInd[h] = (0.868 \\cdot \\frac{Tal^3}{HOT-HUT})^{0.385}`

    Examples:
        Using typical values:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> simulationstep('12h')
        >>> tind(tal=5., hot=210., hut=200.)
        >>> tind
        tind(0.104335)

        Note that this result is related to the selected parameter step size
        of one day.  The value related to the selected simulation step size
        of 12 hours is:

        >>> round(tind.value, 6)
        0.20867

        Unplausible input values lead to the following exception:
        >>> tind(tal=5., hot=200., hut=200.)
        Traceback (most recent call last):
        ...
        ValueError: For the alternative calculation of parameter `tind`, the value assigned to keyword argument `tal` must be greater then zero and the one of `hot` must be greater than the one of `hut`.  However, for element ?, the values `5.0`, `200.0` and `200.0` were given respectively.
        >>> tind(tal=0., hot=210., hut=200.)
        Traceback (most recent call last):
        ...
        ValueError: For the alternative calculation of parameter `tind`, the value assigned to keyword argument `tal` must be greater then zero and the one of `hot` must be greater than the one of `hut`.  However, for element ?, the values `0.0`, `210.0` and `200.0` were given respectively.

        However, it is hard to define exact bounds for the value of
        :class:`TInd` itself.  Whenever it is below 0.001 or above 1000 days,
        the following warning is given:

        >>> tind(tal=.001, hot=210., hut=200.)
        Traceback (most recent call last):
        ...
        UserWarning: Due to the given values for the keyword arguments `tal` (0.001), `hot` (210.0) and `hut` (200.0), parameter `tind` of element `?` has been set to an unrealistic value of `0.000134 hours`.
    """
    NDIM, TYPE, TIME, SPAN = 0, float, False, (0., None)

    def __call__(self, *args, **kwargs):
        """The prefered way to pass values to :class:`TInd` instances
        within parameter control files.
        """
        try:
            parametertools.SingleParameter.__call__(self, *args, **kwargs)
        except NotImplementedError:
            counter = ('tal' in kwargs) + ('hot' in kwargs) + ('hut' in kwargs)
            if counter == 0:
                raise ValueError('For parameter `tind` a value can be set '
                                 'directly by passing a single value or '
                                 'indirectly by using the keyword arguments '
                                 '`tal`, `hot`, and `hut`.')
            elif counter < 3:
                raise ValueError('For the alternative calculation of '
                                 'parameter `tind`, values for all three '
                                 'keyword keyword arguments `tal`, `hot`, '
                                 'and `hut` must be given.')
            else:
                tal = float(kwargs['tal'])
                hot = float(kwargs['hot'])
                hut = float(kwargs['hut'])
                if (tal <= 0.) or (hot <= hut):
                    raise ValueError('For the alternative calculation of '
                                     'parameter `tind`, the value assigned to '
                                     'keyword argument `tal` must be greater '
                                     'then zero and the one of `hot` must be '
                                     'greater than the one of `hut`.  '
                                     'However, for element %s, the values '
                                     '`%s`, `%s` and `%s` were given '
                                     'respectively.'
                                     % (objecttools.devicename(self),
                                        tal, hot, hut))
                self.value = (.868*tal**3/(hot-hut))**.385
                if (self > 1000.) or (self < .001):
                    warnings.warn('Due to the given values for the keyword '
                                  'arguments `tal` (%s), `hot` (%s) and `hut` '
                                  '(%s), parameter `tind` of element `%s` has '
                                  'been set to an unrealistic value of `%s '
                                  'hours`.' % (tal, hot, hut,
                                               objecttools.devicename(self),
                                               round(self.value, 6)))
                self.value *=  timetools.Period('1h')/self.simulationstep

class EQB(parametertools.SingleParameter):
    """Kalibrierfaktor für die Basisabflusskonzentration (factor for adjusting
    the concentration time of baseflow). [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

    def trim(self, lower=None, upper=None):
        """Trim upper values in accordance with :math:`EQI1 \\leq EQB`.

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> eqi1.value = 2.
        >>> eqb(1.)
        >>> eqb
        eqb(2.0)
        >>> eqb(2.)
        >>> eqb
        eqb(2.0)
        >>> eqb(3.)
        >>> eqb
        eqb(3.0)
        """
        if (lower is None) and not numpy.isnan(self.subpars.eqi1):
            lower = self.subpars.eqi1
        parametertools.SingleParameter.trim(self, lower, upper)


class EQI1(parametertools.SingleParameter):
    """Kalibrierfaktor für die "untere" Zwischenabflusskonzentration
    (factor for adjusting the concentration time of the first interflow
    component) [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

    def trim(self, lower=None, upper=None):
        """Trim upper values in accordance with
        :math:`EQI2 \\leq EQI1 \\leq EQB`.

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> eqb.value = 3.
        >>> eqi2.value = 1.
        >>> eqi1(0.)
        >>> eqi1
        eqi1(1.0)
        >>> eqi1(1.)
        >>> eqi1
        eqi1(1.0)
        >>> eqi1(2.)
        >>> eqi1
        eqi1(2.0)
        >>> eqi1(3.)
        >>> eqi1
        eqi1(3.0)
        >>> eqi1(4.)
        >>> eqi1
        eqi1(3.0)
        """
        if (lower is None) and not numpy.isnan(self.subpars.eqi2):
            lower = self.subpars.eqi2
        if (upper is None) and not numpy.isnan(self.subpars.eqb):
            upper = self.subpars.eqb
        parametertools.SingleParameter.trim(self, lower, upper)

class EQI2(parametertools.SingleParameter):
    """Kalibrierfaktor für die "obere" Zwischenabflusskonzentration
    (factor for adjusting the concentration time of the second interflow
    component) [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

    def trim(self, lower=None, upper=None):
        """Trim upper values in accordance with
        :math:`EQD \\leq EQI2 \\leq EQI1`.

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> eqi1.value = 3.
        >>> eqd.value = 1.
        >>> eqi2(0.)
        >>> eqi2
        eqi2(1.0)
        >>> eqi2(1.)
        >>> eqi2
        eqi2(1.0)
        >>> eqi2(2.)
        >>> eqi2
        eqi2(2.0)
        >>> eqi2(3.)
        >>> eqi2
        eqi2(3.0)
        >>> eqi2(4.)
        >>> eqi2
        eqi2(3.0)
        """
        if (lower is None) and not numpy.isnan(self.subpars.eqd):
            lower = self.subpars.eqd
        if (upper is None) and not numpy.isnan(self.subpars.eqi1):
            upper = self.subpars.eqi1
        parametertools.SingleParameter.trim(self, lower, upper)

class EQD(parametertools.SingleParameter):
    """Kalibrierfaktor für die Direktabflusskonzentration (factor for adjusting
    the concentration time of direct runoff). [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

    def trim(self, lower=None, upper=None):
        """Trim upper values in accordance with
        :math:`EQD \\leq EQI2`.

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> eqi2.value = 2.
        >>> eqd(1.)
        >>> eqd
        eqd(1.0)
        >>> eqd(2.)
        >>> eqd
        eqd(2.0)
        >>> eqd(3.)
        >>> eqd
        eqd(2.0)
        """
        if (upper is None) and not numpy.isnan(self.subpars.eqi2):
            upper = self.subpars.eqi2
        parametertools.SingleParameter.trim(self, lower, upper)

class ControlParameters(parametertools.SubParameters):
    """Control parameters of HydPy-L-Land, directly defined by the user."""
    _PARCLASSES = (FT, NHRU, FHRU, Lnk, HNN, KG, KT, KE, KF, FLn, HInz, LAI,
                   TRefT, TRefN, TGr, GTF, RSchmelz, CPWasser, PWMax,
                   GrasRef_R, NFk, RelWB, RelWZ, Beta, DMax, DMin, BSf,
                   TInd, EQB, EQI1, EQI2, EQD)
