# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
import warnings
# ...from site-packages
import numpy
# ...from HydPy
from hydpy.core import abctools
from hydpy.core import parametertools
from hydpy.core import objecttools
from hydpy.core import timetools
# ...from lland
from hydpy.models.lland import lland_constants
from hydpy.models.lland import lland_parameters


class FT(parametertools.Parameter):
    """Teileinzugsgebietsfläche (subbasin area) [km²]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (1e-10, None)


class NHRU(parametertools.Parameter):
    """Anzahl der Hydrotope (number of hydrological response units) [-].

    Note that |NHRU| determines the length of most 1-dimensional HydPy-L-Land
    parameters and sequences as well the shape of 2-dimensional log sequences
    with a predefined length of one axis (see |WET0|).  This required that
    the value of the respective |NHRU| instance is set before any of the
    values of these 1-dimensional parameters or sequences are set.  Changing
    the value of the |NHRU| instance necessitates setting their values again.

    Examples:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(5)
        >>> control.kg.shape
        (5,)
        >>> fluxes.tkor.shape
        (5,)
        >>> logs.wet0.shape
        (1, 5)
    """
    NDIM, TYPE, TIME, SPAN = 0, int, None, (1, None)

    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)
        for subpars in self.subpars.pars.model.parameters:
            for par in subpars:
                if par.NDIM == 1:
                    par.shape = self.value
        for subseqs in self.subpars.pars.model.sequences:
            for seq in subseqs:
                if (((seq.NDIM == 1) and (seq.name != 'moy')) or
                        ((seq.NDIM == 2) and
                         isinstance(seq, abctools.LogSequenceABC))):
                    seq.shape = self.value


class FHRU(lland_parameters.ParameterComplete):
    """Flächenanteile der Hydrotope (area percentages of the respective
    HRUs) [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., 1.)


class Lnk(parametertools.NameParameter):
    """Landnutzungsklasse (land use class) [-].

    For increasing legibility, the HydPy-L-Land constants are used for
    string representions of |Lnk| objects:

    >>> from hydpy.models.lland import *
    >>> parameterstep('1d')
    >>> lnk
    lnk(?)
    >>> nhru(4)
    >>> lnk(ACKER, ACKER, WASSER, MISCHW)
    >>> lnk.values
    array([ 4,  4, 16, 15])
    >>> lnk
    lnk(ACKER, ACKER, WASSER, MISCHW)
    >>> lnk(ACKER)
    >>> lnk
    lnk(ACKER)
    """
    NDIM, TYPE, TIME = 1, int, None
    SPAN = (min(lland_constants.CONSTANTS.values()),
            max(lland_constants.CONSTANTS.values()))
    CONSTANTS = lland_constants.CONSTANTS


class HNN(lland_parameters.ParameterComplete):
    """Höhe über Normal-Null (height above sea level) [m]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)


class KG(lland_parameters.ParameterComplete):
    """Niederschlagskorrekturfaktor (adjustment factor for precipitation)
    [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)
    INIT = 1.


class KT(lland_parameters.ParameterComplete):
    """Temperaturkorrektursummand (adjustment summand for air temperature)
    [°C]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)
    INIT = 0.


class KE(lland_parameters.ParameterComplete):
    """Grasreferenzverdunstungskorrekturfaktor (adjustment factor for
    reference evapotranspiration) [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)
    INIT = 1.


class KF(lland_parameters.ParameterComplete):
    """Küstenfaktor ("coast factor" of Turc-Wendling's evaporation equation
    [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (.6, 1.)
    INIT = 1.


class WfET0(lland_parameters.ParameterComplete):
    """Zeitlicher Wichtungsfaktor der Grasreferenzverdunsung (temporal
    weighting factor for reference evapotranspiration)."""
    NDIM, TYPE, TIME, SPAN = 1, float, True, (0., 1.)


class FLn(lland_parameters.LanduseMonthParameter):
    """Landnutzungsabhängiger Verdunstungsfaktor (factor for adjusting
    reference evapotranspiration to different land use classes) [-]."""
    NDIM, TYPE, TIME, SPAN = 2, float, None, (0., None)
    INIT = 1.


class HInz(parametertools.Parameter):
    """Interzeptionskapazität bezogen auf die Blattoberfläche (interception
    capacity normalized to the leaf surface area) [mm]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)
    INIT = .2


class LAI(lland_parameters.LanduseMonthParameter):
    """Blattflächenindex (leaf area index) [-]."""
    NDIM, TYPE, TIME, SPAN = 2, float, None, (0., None)
    INIT = 5.


class TRefT(lland_parameters.ParameterLand):
    """Lufttemperaturgrenzwert des grundlegenden Grad-Tag-Verfahrens
    (air temperature threshold of the degree-day method) [°C]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)
    INIT = 0.


class TRefN(lland_parameters.ParameterLand):
    """Niederschlagstemperaturgrenzwert des erweiterten Grad-Tag-Verfahrens
    (precipitation temperature threshold of the degree-day method) [°C]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)
    INIT = 0.


class TGr(lland_parameters.ParameterLand):
    """Temperaturgrenzwert flüssiger/fester Niederschlag (threshold
    temperature liquid/frozen precipitation) [°C]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)
    INIT = 0.


class TSp(lland_parameters.ParameterLand):
    """Temperaturspanne flüssiger/fester Niederschlag (temperature range
    with mixed precipitation) [°C]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)
    INIT = 0.


class GTF(lland_parameters.ParameterLand):
    """Grad-Tag-Faktor (factor of the degree-day method) [mm/°C/T]."""
    NDIM, TYPE, TIME, SPAN = 1, float, True, (0., None)
    INIT = 3.


class RSchmelz(parametertools.Parameter):
    """Spezifische Schmelzwärme von Wasser (specific melt heat of water)
    [J/g]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)
    INIT = 334.


class CPWasser(parametertools.Parameter):
    """Spezifische Wärmekapazität von Wasser (specific heat capacity of water)
    [J/g]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)
    INIT = 4.1868


class PWMax(lland_parameters.ParameterLand):
    """Maximalverhältnis Gesamt- zu Trockenschnee (maximum ratio of the
    total and the frozen water equivalent stored in the snow cover) [-].

    In addition to the |parametertools| call method, it
    is possible to set the value of parameter |PWMax| in accordance to
    the keyword arguments `rhot0` and `rhodkrit`.

    Basic Equation:
        :math:`PWMax = \\frac{1.474 \\cdot rhodkrit}
        {rhot0 + 0.474 \\cdot rhodkrit}`

    Example:

        Using the common values for both `rhot0` and `rhodkrit`...

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(1)
        >>> lnk(ACKER)
        >>> pwmax(rhot0=0.2345, rhodkrit=0.42)

        ...results in:

        >>> pwmax
        pwmax(1.427833)

        This is also the default value of |PWMax|, meaning the relative
        portion of liquid water in the snow cover cannot exceed 30 %.

        Additional error messages try to clarify how to pass parameters:

        >>> pwmax(rhot0=0.2345)
        Traceback (most recent call last):
        ...
        ValueError: For the calculating parameter `pwmax`, both keyword \
arguments `rhot0` and `rhodkrit` are required.

        >>> pwmax(rho_t_0=0.2345)
        Traceback (most recent call last):
        ...
        ValueError: Parameter `pwmax` can be set by directly passing a \
single value or a list of values, by assigning single values to landuse \
keywords, or by calculating a value based on the keyword arguments \
`rhot0` and `rhodkrit`.

        Passing landuse specific parameter values is also supported
        (but not in combination with `rhot0` and `rhodkrit`):

        >>> pwmax(acker=2.0, vers=3.0)
        >>> pwmax
        pwmax(2.0)

        The "normal" input error management still works:

        >>> pwmax()
        Traceback (most recent call last):
        ...
        ValueError: For parameter pwmax of element ? neither a positional \
nor a keyword argument is given.
    """
    NDIM, TYPE, TIME, SPAN = 1, float, None, (1., None)
    INIT = 1.4278333871488538

    def __call__(self, *args, **kwargs):
        """The prefered way to pass values to |PWMax| instances
        within parameter control files.
        """
        rhot0 = float(kwargs.pop('rhot0', numpy.nan))
        rhodkrit = float(kwargs.pop('rhodkrit', numpy.nan))
        missing = int(numpy.isnan(rhot0)) + int(numpy.isnan(rhodkrit))
        try:
            lland_parameters.ParameterLand.__call__(self, *args, **kwargs)
            return
        except NotImplementedError:
            pass
        except BaseException as exc:
            if missing == 2:
                raise exc
        if not missing:
            self(1.474*rhodkrit/(rhot0+0.474*rhodkrit))
        elif missing == 1:
            raise ValueError(
                'For the calculating parameter `pwmax`, both keyword '
                'arguments `rhot0` and `rhodkrit` are required.')
        else:
            raise ValueError(
                'Parameter `pwmax` can be set by directly passing a '
                'single value or a list of values, by assigning single '
                'values to landuse keywords, or by calculating a value '
                'based on the keyword arguments `rhot0` and `rhodkrit`.')


class GrasRef_R(parametertools.Parameter):
    """Bodenfeuchte-Verdunstung-Parameter (soil moisture-dependent
    evaporation factor) [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)
    INIT = 5.


class NFk(lland_parameters.ParameterSoil):
    """Nutzbare Feldkapazität (usable field capacity) [mm]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)
    INIT = 100.


class RelWZ(lland_parameters.ParameterSoil):
    """Relative Mindestbodenfeuchte für die Interflowentstehung (threshold
       value of relative soil moisture for interflow generation) [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, 1.)
    INIT = .8

    def trim(self, lower=None, upper=None):
        """Trim upper values in accordance with :math:`RelWB \\leq RelWZ`.

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(3)
        >>> lnk(ACKER)
        >>> relwb.values = 0.5
        >>> relwz(0.2, 0.5, 0.8)
        >>> relwz
        relwz(0.5, 0.5, 0.8)
        """
        if lower is None:
            lower = getattr(self.subpars.relwb, 'value', None)
        lland_parameters.ParameterSoil.trim(self, lower, upper)


class RelWB(lland_parameters.ParameterSoil):
    """Relative Mindestbodenfeuchte für die Basisabflussentstehung (threshold
       value of relative soil moisture for base flow generation) [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)
    INIT = .05

    def trim(self, lower=None, upper=None):
        """Trim upper values in accordance with :math:`RelWB \\leq RelWZ`.

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> nhru(3)
        >>> lnk(ACKER)
        >>> relwz.values = 0.5
        >>> relwb(0.2, 0.5, 0.8)
        >>> relwb
        relwb(0.2, 0.5, 0.5)
        """
        if upper is None:
            upper = getattr(self.subpars.relwz, 'value', None)
        lland_parameters.ParameterSoil.trim(self, lower, upper)


class Beta(lland_parameters.ParameterSoil):
    """Drainageindex des tiefen Bodenspeichers (storage coefficient for
    releasing base flow from the lower soil compartment) [1/T]."""
    NDIM, TYPE, TIME, SPAN = 1, float, True, (0., None)
    INIT = .01


class FBeta(lland_parameters.ParameterSoil):
    """Faktor zur Erhöhung der Perkolation im Grobporenbereich (factor for
    increasing percolation under wet conditions) [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (1., None)
    INIT = 1.


class DMin(lland_parameters.ParameterSoil):
    """Drainageindex des mittleren Bodenspeichers (flux rate for
    releasing interflow from the middle soil compartment) [mm/T].

    In addition to the |ParameterSoil| `__call__` method, it is
    possible to set the value of parameter |DMin| in accordance
    to the keyword argument `r_dmin` due to compatibility reasons
    with the original LARSIM implemetation.

    Basic Equation:
        :math:`Dmin = 0.024192 \\cdot r_dmin`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> simulationstep('12h')
        >>> nhru(1)
        >>> lnk(ACKER)
        >>> dmax(10.0) # to prevent trimming of dmin, see below
        >>> dmin(r_dmin=10.0)
        >>> dmin
        dmin(0.24192)

        Note the additional dependence of the parameter value on the
        relation between the `parameterstep` and the actual `simulationstep`:

        >>> dmin.values
        array([ 0.12096])

        A wrong keyword results in the right answer:

        >>> dmin(rdmin=10.0)
        Traceback (most recent call last):
        ...
        NotImplementedError: While trying to set the values of parameter \
`dmin` of element `?` based on keyword arguments, the following error \
occurred: Key `rdmin` is not an available model constant.

    """
    NDIM, TYPE, TIME, SPAN = 1, float, True, (0., None)
    INIT = 0.

    def __call__(self, *args, **kwargs):
        """The prefered way to pass values to |DMin| instances
        within parameter control files.
        """
        try:
            lland_parameters.ParameterSoil.__call__(self, *args, **kwargs)
        except NotImplementedError:
            args = kwargs.get('r_dmin')
            if args is not None:
                self.values = 0.024192*self.apply_timefactor(numpy.array(args))
                self.trim()
            else:
                objecttools.augment_excmessage()

    def trim(self, lower=None, upper=None):
        """Trim upper values in accordance with :math:`DMin \\leq DMax`.

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> simulationstep('12h')
        >>> nhru(5)
        >>> lnk(ACKER)
        >>> dmax.values = 2.0
        >>> dmin(-2.0, 0.0, 2.0, 4.0, 6.0)
        >>> dmin
        dmin(0.0, 0.0, 2.0, 4.0, 4.0)
        """
        if upper is None:
            upper = getattr(self.subpars.dmax, 'value', None)
        lland_parameters.ParameterSoil.trim(self, lower, upper)


class DMax(lland_parameters.ParameterSoil):
    """Drainageindex des oberen Bodenspeichers (additional flux rate for
    releasing interflow from the upper soil compartment) [mm/T].

    In addition to the |ParameterSoil| `__call__` method, it is
    possible to set the value of parameter |DMax| in accordance
    to the keyword argument `r_dmax` due to compatibility reasons
    with the original LARSIM implemetation.

    Basic Equation:
        :math:`Dmax = 2.4192 \\cdot r_dmax`

    Example:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> simulationstep('12h')
        >>> nhru(1)
        >>> lnk(ACKER)
        >>> dmin(0.0) # to prevent trimming of dmax, see below
        >>> dmax(r_dmax=10.0)
        >>> dmax
        dmax(24.192)

        Note the additional dependence of the parameter value on the
        relation between the `parameterstep` and the actual `simulationstep`:

        >>> dmax.values
        array([ 12.096])

        A wrong keyword results in the right answer:

        >>> dmax(rdmax=10.0)
        Traceback (most recent call last):
        ...
        NotImplementedError: While trying to set the values of parameter \
`dmax` of element `?` based on keyword arguments, the following error \
occurred: Key `rdmax` is not an available model constant.
    """
    NDIM, TYPE, TIME, SPAN = 1, float, True, (None, None)
    INIT = 1.

    def __call__(self, *args, **kwargs):
        """The prefered way to pass values to |DMax| instances
        within parameter control files.
        """
        try:
            lland_parameters.ParameterSoil.__call__(self, *args, **kwargs)
        except NotImplementedError:
            args = kwargs.get('r_dmax')
            if args is not None:
                self.values = 2.4192*self.apply_timefactor(numpy.array(args))
                self.trim()
            else:
                objecttools.augment_excmessage()

    def trim(self, lower=None, upper=None):
        """Trim upper values in accordance with :math:`DMax \\geq DMin`.

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> simulationstep('12h')
        >>> nhru(3)
        >>> lnk(ACKER)
        >>> dmin.values = 2.0
        >>> dmax(2.0, 4.0, 6.0)
        >>> dmax
        dmax(4.0, 4.0, 6.0)
        """
        if lower is None:
            lower = getattr(self.subpars.dmin, 'value', None)
        lland_parameters.ParameterSoil.trim(self, lower, upper)


class BSf(lland_parameters.ParameterSoil):
    """Bodenfeuchte-Sättigungsfläche-Parameter (shape parameter for the
    relation between the avarage soil moisture and the relative saturated
    area of a subbasin) [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)
    INIT = .4


class A1(parametertools.Parameter):
    """Parameter für die kontinuierliche Aufteilung der
    Direktabflusskomponenten (threshold value for the continuous seperation
    of direct runoff in a slow and a fast component) [mm/d]
    """
    NDIM, TYPE, TIME, SPAN = 0, float, True, (0., None)
    INIT = numpy.inf


class A2(parametertools.Parameter):
    """Parameter für die diskontinuierliche Aufteilung der
    Direktabflusskomponenten (threshold value for the discontinuous seperation
    of direct runoff in a slow and a fast component) [mm/d]
    """
    NDIM, TYPE, TIME, SPAN = 0, float, True, (0., None)
    INIT = 0.


class TInd(parametertools.Parameter):
    """Fließzeitindex (factor related to the time of concentration) [T].

    In addition to the |Parameter| call method, it
    is possible to set the value of parameter |TInd| in accordance to
    the keyword arguments `tal` (talweg, [km]), `hot` (higher reference
    altitude, [m]), and `hut` (lower reference altitude, [m]).  This is
    supposed to decrease the time of runoff concentration in small and/or
    steep catchments.  Note that |TInd| does not only affect direct
    runoff, but interflow and base flow as well.  Hence it seems advisable
    to use this regionalization strategy with caution.

    Basic Equation:
        :math:`TInd[h] = (0.868 \\cdot \\frac{Tal^3}{HOT-HUT})^{0.385}`

    Examples:

        Using typical values:

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> simulationstep('12h')
        >>> tind(tal=5.0, hot=210.0, hut=200.0)
        >>> tind
        tind(0.104335)

        Note that this result is related to the selected parameter step size
        of one day.  The value related to the selected simulation step size
        of 12 hours is:

        >>> from hydpy import round_
        >>> round_(tind.value)
        0.20867

        Unplausible input values lead to the following exceptions:

        >>> tind(tal=5.0, hot=200.0, hut=200.0)
        Traceback (most recent call last):
        ...
        ValueError: For the alternative calculation of parameter `tind`, \
the value assigned to keyword argument `tal` must be greater then zero and \
the one of `hot` must be greater than the one of `hut`.  However, for \
element ?, the values `5.0`, `200.0` and `200.0` were given respectively.

        >>> tind(tal=0.0, hot=210.0, hut=200.0)
        Traceback (most recent call last):
        ...
        ValueError: For the alternative calculation of parameter `tind`, \
the value assigned to keyword argument `tal` must be greater then zero and \
the one of `hot` must be greater than the one of `hut`.  However, for \
element ?, the values `0.0`, `210.0` and `200.0` were given respectively.

        However, it is hard to define exact bounds for the value of
        |TInd| itself.  Whenever it is below 0.001 or above 1000 days,
        the following warning is given:

        >>> tind(tal=0.001, hot=210.0, hut=200.0)
        Traceback (most recent call last):
        ...
        UserWarning: Due to the given values for the keyword arguments \
`tal` (0.001), `hot` (210.0) and `hut` (200.0), parameter `tind` of \
element `?` has been set to an unrealistic value of `0.000134 hours`.

        Additionally, exceptions for missing (or wrong) keywords are
        implemented

        >>> tind(tal=5.0, hot=210.0)
        Traceback (most recent call last):
        ...
        ValueError: For the alternative calculation of parameter `tind`, \
values for all three keyword keyword arguments `tal`, `hot`, and `hut` \
must be given.

    """
    NDIM, TYPE, TIME, SPAN = 0, float, False, (0., None)
    INIT = 1.

    def __call__(self, *args, **kwargs):
        """The prefered way to pass values to |TInd| instances
        within parameter control files.
        """
        try:
            super().__call__(*args, **kwargs)
        except NotImplementedError:
            try:
                tal = float(kwargs['tal'])
                hot = float(kwargs['hot'])
                hut = float(kwargs['hut'])
            except KeyError:
                raise ValueError(
                    'For the alternative calculation of parameter `tind`, '
                    'values for all three keyword keyword arguments `tal`, '
                    '`hot`, and `hut` must be given.')
            if (tal <= 0.) or (hot <= hut):
                raise ValueError(
                    'For the alternative calculation of parameter '
                    '`tind`, the value assigned to keyword argument '
                    '`tal` must be greater then zero and the one of '
                    '`hot` must be greater than the one of `hut`.  '
                    'However, for element %s, the values `%s`, `%s` '
                    'and `%s` were given respectively.'
                    % (objecttools.devicename(self), tal, hot, hut))
            self.value = (.868*tal**3/(hot-hut))**.385
            if (self > 1000.) or (self < .001):
                warnings.warn(
                    'Due to the given values for the keyword arguments '
                    '`tal` (%s), `hot` (%s) and `hut` (%s), parameter '
                    '`tind` of element `%s` has been set to an '
                    'unrealistic value of `%s hours`.'
                    % (tal, hot, hut, objecttools.devicename(self),
                       objecttools.repr_(self.value)))
            self.value *= timetools.Period('1h')/self.simulationstep


class EQB(parametertools.Parameter):
    """Kalibrierfaktor für die Basisabflusskonzentration (factor for adjusting
    the concentration time of baseflow). [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)
    INIT = 5000.

    def trim(self, lower=None, upper=None):
        """Trim upper values in accordance with :math:`EQI1 \\leq EQB`.

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> eqi1.value = 2.0
        >>> eqb(1.0)
        >>> eqb
        eqb(2.0)
        >>> eqb(2.0)
        >>> eqb
        eqb(2.0)
        >>> eqb(3.0)
        >>> eqb
        eqb(3.0)
        """
        if lower is None:
            lower = getattr(self.subpars.eqi1, 'value', None)
        super().trim(lower, upper)


class EQI1(parametertools.Parameter):
    """Kalibrierfaktor für die "untere" Zwischenabflusskonzentration
    (factor for adjusting the concentration time of the first interflow
    component) [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)
    INIT = 2000.

    def trim(self, lower=None, upper=None):
        """Trim upper values in accordance with
        :math:`EQI2 \\leq EQI1 \\leq EQB`.

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> eqb.value = 3.0
        >>> eqi2.value = 1.0
        >>> eqi1(0.0)
        >>> eqi1
        eqi1(1.0)
        >>> eqi1(1.0)
        >>> eqi1
        eqi1(1.0)
        >>> eqi1(2.0)
        >>> eqi1
        eqi1(2.0)
        >>> eqi1(3.0)
        >>> eqi1
        eqi1(3.0)
        >>> eqi1(4.0)
        >>> eqi1
        eqi1(3.0)
        """
        if lower is None:
            lower = getattr(self.subpars.eqi2, 'value', None)
        if upper is None:
            upper = getattr(self.subpars.eqb, 'value', None)
        super().trim(lower, upper)


class EQI2(parametertools.Parameter):
    """Kalibrierfaktor für die "obere" Zwischenabflusskonzentration
    (factor for adjusting the concentration time of the second interflow
    component) [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)
    INIT = 1000.

    def trim(self, lower=None, upper=None):
        """Trim upper values in accordance with
        :math:`EQD \\leq EQI2 \\leq EQI1`.

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> eqi1.value = 3.0
        >>> eqd1.value = 1.0
        >>> eqi2(0.0)
        >>> eqi2
        eqi2(1.0)
        >>> eqi2(1.0)
        >>> eqi2
        eqi2(1.0)
        >>> eqi2(2.0)
        >>> eqi2
        eqi2(2.0)
        >>> eqi2(3.0)
        >>> eqi2
        eqi2(3.0)
        >>> eqi2(4.0)
        >>> eqi2
        eqi2(3.0)
        """
        if lower is None:
            lower = getattr(self.subpars.eqd1, 'value', None)
        if upper is None:
            upper = getattr(self.subpars.eqi1, 'value', None)
        super().trim(lower, upper)


class EQD1(parametertools.Parameter):
    """Kalibrierfaktor für die langsamere Direktabflusskonzentration (factor
    for adjusting the concentration time of the slower component of direct
    runoff). [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)
    INIT = 100.

    def trim(self, lower=None, upper=None):
        """Trim upper values in accordance with
        :math:`EQD2 \\leq EQD1 \\leq EQI2`.

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> eqi2.value = 3.0
        >>> eqd2.value = 1.0
        >>> eqd1(0.0)
        >>> eqd1
        eqd1(1.0)
        >>> eqd1(1.0)
        >>> eqd1
        eqd1(1.0)
        >>> eqd1(2.0)
        >>> eqd1
        eqd1(2.0)
        >>> eqd1(3.0)
        >>> eqd1
        eqd1(3.0)
        >>> eqd1(4.0)
        >>> eqd1
        eqd1(3.0)
        """
        if lower is None:
            lower = getattr(self.subpars.eqd2, 'value', None)
        if upper is None:
            upper = getattr(self.subpars.eqi2, 'value', None)
        super().trim(lower, upper)


class EQD2(parametertools.Parameter):
    """Kalibrierfaktor für die schnellere Direktabflusskonzentration (factor
    for adjusting the concentration time of the faster component of direct
    runoff). [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)
    INIT = 50.

    def trim(self, lower=None, upper=None):
        """Trim upper values in accordance with
        :math:`EQD2 \\leq EQD1`.

        >>> from hydpy.models.lland import *
        >>> parameterstep('1d')
        >>> eqd1.value = 3.0
        >>> eqd2(2.0)
        >>> eqd2
        eqd2(2.0)
        >>> eqd2(3.0)
        >>> eqd2
        eqd2(3.0)
        >>> eqd2(4.0)
        >>> eqd2
        eqd2(3.0)
        """
        if upper is None:
            upper = getattr(self.subpars.eqd1, 'value', None)
        super().trim(lower, upper)


class NegQ(parametertools.Parameter):
    """Option: sind negative Abflüsse erlaubt (flag that indicated wether
    negative discharge values are allowed or not) [-]."""
    NDIM, TYPE, TIME, SPAN = 0, bool, None, (0., None)
    INIT = False


class ControlParameters(parametertools.SubParameters):
    """Control parameters of HydPy-L-Land, directly defined by the user."""
    CLASSES = (FT,
               NHRU,
               Lnk,
               FHRU,
               HNN,
               KG,
               KT,
               KE,
               KF,
               WfET0,
               FLn,
               HInz,
               LAI,
               TRefT,
               TRefN,
               TGr,
               TSp,
               GTF,
               RSchmelz,
               CPWasser,
               PWMax,
               GrasRef_R,
               NFk,
               RelWZ,
               RelWB,
               Beta,
               FBeta,
               DMax,
               DMin,
               BSf,
               A1,
               A2,
               TInd,
               EQB,
               EQI1,
               EQI2,
               EQD1,
               EQD2,
               NegQ)
