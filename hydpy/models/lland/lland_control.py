# -*- coding: utf-8 -*-
"""
.. _`LARSIM`: http://www.larsim.de/en/the-model/
"""
# import...
# ...from standard library
from __future__ import annotations
import warnings

# ...from site-packages
import numpy

# ...from HydPy
import hydpy
from hydpy.core import exceptiontools
from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.core import sequencetools
from hydpy.core import timetools
from hydpy.core.typingtools import *

# ...from lland
from hydpy.models.lland.lland_constants import CONSTANTS as CONSTANTS_
from hydpy.models.lland import lland_parameters


# spatial information


class FT(parametertools.Parameter):
    """Teileinzugsgebietsfläche (subbasin area) [km²]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (1e-10, None)


class NHRU(parametertools.Parameter):
    """Anzahl der Hydrotope (number of hydrological response units) [-].

    Note that |NHRU| determines the length of most 1-dimensional HydPy-L-Land
    parameters and sequences as well the shape of 2-dimensional log sequences with a
    predefined length of one axis (see |WEvI|).  This requires that the value of the
    respective |NHRU| instance is set before any of the values of these 1-dimensional
    parameters or sequences are set.  Changing the value of the |NHRU| instance
    necessitates setting their values again:

    Examples:

        >>> from hydpy.models.lland import *
        >>> parameterstep("1d")
        >>> nhru(5)
        >>> control.kg.shape
        (5,)
        >>> control.kapgrenz.shape
        (5, 2)
        >>> fluxes.tkor.shape
        (5,)
        >>> logs.wevi.shape
        (1, 5)
        >>> control.wg2z.shape
        (12,)
    """

    NDIM, TYPE, TIME, SPAN = 0, int, None, (1, None)

    def __call__(self, *args, **kwargs) -> None:
        super().__call__(*args, **kwargs)

        skippars = (parametertools.MonthParameter, parametertools.MOYParameter)
        for subpars in self.subpars.pars.model.parameters:
            for par in subpars:
                if (par.NDIM == 1) and not isinstance(par, skippars):
                    par.shape = self.value
        self.subpars.kapgrenz.shape = self.value, 2

        skipseqs = (sequencetools.LogSequences, sequencetools.LinkSequences)
        sequences = self.subpars.pars.model.sequences
        for subseqs in sequences:
            if not isinstance(subseqs, skipseqs):
                for seq in subseqs:
                    if seq.NDIM == 1:
                        seq.shape = self.value
        if hasattr(sequences.logs, "wevi"):
            sequences.logs.wevi.shape = self.value


class Lnk(parametertools.NameParameter):
    """Landnutzungsklasse (land use class) [-].

    For increasing legibility, the HydPy-L-Land constants are used for string
    representions of |Lnk| objects:

    >>> from hydpy.models.lland import *
    >>> parameterstep("1d")
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

    constants = CONSTANTS_


class FHRU(lland_parameters.ParameterComplete):
    """Flächenanteile der Hydrotope (area percentages of the respective HRUs) [-]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, 1.0)


# input correction


class KG(lland_parameters.ParameterComplete):
    """Niederschlagskorrekturfaktor (adjustment factor for precipitation)
    [-]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)
    INIT = 1.0


class KT(lland_parameters.ParameterComplete):
    """Temperaturkorrektursummand (adjustment summand for air temperature)
    [°C]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)
    INIT = 0.0


# energy adjustment


class P1Strahl(parametertools.Parameter):
    """Konstante der Globalstrahlungsreduktion für Wald (constant for
    reducing the global radiation in forests) [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, 1.0)
    INIT = 0.5


class P2Strahl(parametertools.Parameter):
    """Faktor der Globalstrahlungsreduktion für Wald (factor for
    reducing the global radiation in forests) [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, 1.0)
    INIT = 1.0 / 35.0


class Albedo0Snow(parametertools.Parameter):
    """Albedo von Neuschnee (albedo of fresh snow) [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, 1.0)
    INIT = 0.8


class SnowAgingFactor(parametertools.Parameter):
    """Wichtungsfaktor für die Sensitivität der Albedo für die Alterung des
    Schnees (weighting factor of albedo sensitivity for snow aging) [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, 1.0)
    INIT = 0.35


class Turb0(parametertools.Parameter):
    """Parameter des Übergangskoeffizienten des turbulenten Wärmestroms
    (parameter of transition coefficient for turbulent heat flux)
    [W/m²/K].

    Parameter |Turb0| corresponds to the LARSIM parameter `A0`.
    """

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 2.0


class Turb1(parametertools.Parameter):
    """Parameter des Übergangskoeffizienten des turbulenten Wärmestroms
    (parameter of transition coefficient for turbulent heat flux)
    [J/m³/K].

    Parameter |Turb0| corresponds to the LARSIM parameter `A1`.
    """

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 2.0


# wind speed adjustment


class MeasuringHeightWindSpeed(parametertools.Parameter):
    """The height above ground of the wind speed measurements [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0, None)
    INIT = 10.0


class P1Wind(parametertools.Parameter):
    """Konstante der Windgeschwindigkeitsreduktion für Wald (constant for
    reducing the wind speed in forests) [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, 1.0)
    INIT = 0.6


class P2Wind(parametertools.Parameter):
    """Faktor der Windgeschwindigkeitsreduktion für Wald (factor for
    reducing the wind speed in forests) [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, 1.0)
    INIT = 1.0 / 70.0


# interception


class LAI(lland_parameters.LanduseMonthParameter):
    """Blattflächenindex (leaf area index) [-]."""

    NDIM, TYPE, TIME, SPAN = 2, float, None, (0.0, None)
    INIT = 5.0


class HInz(parametertools.Parameter):
    """Interzeptionskapazität bezogen auf die Blattoberfläche (interception
    capacity normalized to the leaf surface area) [mm]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 0.2


# snow interception


class P1SIMax(parametertools.Parameter):
    """Konstante zur Berechnung der maximalen Schneeinterzeptionskapazität basierend
    auf dem Blattflächenindex (constant for calculating the maximum snow interception
    capacity based on the leaf area index) [mm]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 8.0


class P2SIMax(parametertools.Parameter):
    """Faktor zur Berechnung der maximalen Schneeinterzeptionskapazität basierend
    auf dem Blattflächenindex (factor for calculating the maximum snow interception
    capacity based on the leaf area index) [mm]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 1.5


class P1SIRate(parametertools.Parameter):
    """Konstante zur Berechnung des Verhältnisses von Schneeinerzeptionsrate und
    Niederschlagsintensität basierend auf dem Blattflächenindex (constant for
    calculating the ratio of the snow interception rate and the precipitation
    intensity based on the leaf area index) [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, 1.0)
    INIT = 0.2


class P2SIRate(parametertools.Parameter):
    """Faktor zur Berechnung des Verhältnisses von Schneeinerzeptionsrate und
    Niederschlagsintensität basierend auf dem Blattflächenindex (factor for
    calculating the ratio of the snow interception rate and precipitation intensity
    based on the leaf area index) [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, 1.0)
    INIT = 0.02


class P3SIRate(parametertools.Parameter):
    """Faktor zur Berechnung des Verhältnisses von Schneeinerzeptionsrate und
    Niederschlagsintensität basierend auf der bereits interzipierten Schneemenge
    (factor for calculating the ratio of the snow interception rate and precipitation
    intensity based on the amount of already intercepted snow) [1/mm]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, 0.05)
    INIT = 0.003


# snow


class TRefT(lland_parameters.ParameterLand):
    """Lufttemperaturgrenzwert des Grad-Tag-Verfahrens (air temperature
    threshold of the degree-day method) [°C]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)
    INIT = 0.0


class TRefN(lland_parameters.ParameterLand):
    """Niederschlagstemperaturgrenzwert des zur Berechnung des Wärmeeintrags
    durch Regen (precipitation temperature threshold to calculate heat flux
    caused by liquid precipitation on snow) [°C]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)
    INIT = 0.0


class TGr(lland_parameters.ParameterLand):
    """Temperaturgrenzwert flüssiger/fester Niederschlag (threshold
    temperature liquid/frozen precipitation) [°C]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)
    INIT = 0.0


class TSp(lland_parameters.ParameterLand):
    """Temperaturspanne flüssiger/fester Niederschlag (temperature range
    with mixed precipitation) [°C]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)
    INIT = 0.0


class GTF(lland_parameters.ParameterLand):
    """Grad-Tag-Faktor (factor of the degree-day method) [mm/°C/T]."""

    NDIM, TYPE, TIME, SPAN = 1, float, True, (0.0, None)
    INIT = 3.0


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
        ValueError: For parameter `pwmax` of element `?` neither \
a positional nor a keyword argument is given.
    """

    NDIM, TYPE, TIME, SPAN = 1, float, None, (1.0, None)
    INIT = 1.4278333871488538

    def __call__(self, *args, **kwargs) -> None:
        """The prefered way to pass values to |PWMax| instances within parameter
        control files.
        """
        rhot0 = float(kwargs.pop("rhot0", numpy.nan))
        rhodkrit = float(kwargs.pop("rhodkrit", numpy.nan))
        missing = int(numpy.isnan(rhot0)) + int(numpy.isnan(rhodkrit))
        try:
            super().__call__(*args, **kwargs)
            return
        except TypeError:
            pass
        except BaseException as exc:
            if missing == 2:
                raise exc
        if not missing:
            self(1.474 * rhodkrit / (rhot0 + 0.474 * rhodkrit))
        elif missing == 1:
            raise ValueError(
                "For the calculating parameter `pwmax`, both keyword "
                "arguments `rhot0` and `rhodkrit` are required."
            )
        else:
            raise ValueError(
                "Parameter `pwmax` can be set by directly passing a "
                "single value or a list of values, by assigning single "
                "values to landuse keywords, or by calculating a value "
                "based on the keyword arguments `rhot0` and `rhodkrit`."
            )


class RefreezeFlag(parametertools.Parameter):
    """Flag um wiedergefrieren zu aktivieren (flag to activate refreezing)
    [-]."""

    NDIM, TYPE, TIME, SPAN = 0, int, None, (False, True)
    INIT = 0


class KTSchnee(parametertools.Parameter):
    """Effektive Wärmeleitfähigkeit der obersten Schneeschicht (effective
    thermal conductivity of the top snow layer) [W/m²/K].

    Note that, at least for application model |lland_v3|, it is fine to
    set the value of parameter |KTSchnee| to |numpy.inf| to disable the
    explicite modelling of the top snow layer.  As a result, the top
    layer does not dampen the effects of atmospheric influences like
    radiative heating.  Another aspect is that the snow surface temperature
    does not need to be determined iteratively, as it is always identical
    with the the snow bulk temperature, which decreases computation times.
    """

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, numpy.inf)
    INIT = 5.0


class WG2Z(parametertools.MonthParameter):
    """Bodenwärmestrom in der Tiefe 2z (soil heat flux at depth 2z)
    [W/m²]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)
    INIT = 0.0


# evapotranspiration


class WfEvI(lland_parameters.ParameterComplete):
    """Zeitlicher Wichtungsfaktor der Interzeptionsverdunstung (temporal weighting
    factor for interception evaporation)."""

    NDIM, TYPE, TIME, SPAN = 1, float, True, (0.0, 1.0)
    INIT = 0.0


# soil properties


class WMax(lland_parameters.ParameterSoil):
    """Maximaler Bodenwasserspeicher  (maximum soil water storage) [mm]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)
    INIT = 100.0

    # defined at the bottom of the file:
    CONTROLPARAMETERS: ClassVar[tuple[type[PWP], type[FK]]]

    def trim(self, lower=None, upper=None):
        """Trim values in accordance with :math:`PWP \\leq FK \\leq WMax`.

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(3)
        >>> lnk(ACKER)

        >>> pwp(20.0)
        >>> wmax(10.0, 50.0, 90.0)
        >>> wmax
        wmax(20.0, 50.0, 90.0)

        >>> fk.values = 60.0
        >>> wmax.trim()
        >>> wmax
        wmax(60.0, 60.0, 90.0)
        """
        if lower is None:
            lower = exceptiontools.getattr_(self.subpars.fk, "value", None)
            if lower is None:
                lower = exceptiontools.getattr_(self.subpars.pwp, "value", None)
        super().trim(lower, upper)


class FK(lland_parameters.ParameterSoilThreshold):
    """Feldkapazität / Mindestbodenfeuchte für die Interflowentstehung (field
    capacity / threshold value of soil moisture for interflow generation) [mm].

    Note that one can define the values of parameter |FK| via the
    keyword argument `relative`, as explained in the documentation
    on class |ParameterSoilThreshold|.
    """

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)
    INIT = 0.0

    # defined at the bottom of the file:
    CONTROLPARAMETERS: ClassVar[tuple[type[PWP], type[WMax]]]

    def trim(self, lower=None, upper=None):
        """Trim upper values in accordance with :math:`PWP \\leq FK \\leq WMax`.

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(3)
        >>> lnk(ACKER)
        >>> pwp(20.0)
        >>> wmax(80.0)
        >>> fk(10.0, 50.0, 90.0)
        >>> fk
        fk(20.0, 50.0, 80.0)
        """
        if lower is None:
            lower = exceptiontools.getattr_(self.subpars.pwp, "value", None)
        if upper is None:
            upper = exceptiontools.getattr_(self.subpars.wmax, "value", None)
        super().trim(lower, upper)


class PWP(lland_parameters.ParameterSoilThreshold):
    """Permanenter Welkepunkt / Mindestbodenfeuchte für die
    Basisabflussentstehung (permanent wilting point threshold value of soil
    moisture for base flow generation) [mm].

    Note that one can define the values of parameter |PWP| via the
    keyword argument `relative`, as explained in the documentation
    on class |ParameterSoilThreshold|.
    """

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)
    INIT = 0.0

    CONTROLPARAMETERS = (WMax, FK)

    def trim(self, lower=None, upper=None):
        """Trim values in accordance with :math:`PWP \\leq FK \\leq WMax`.

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> nhru(3)
        >>> lnk(ACKER)
        >>> wmax(100.0)
        >>> pwp(-10.0, 50.0, 110.0)
        >>> pwp
        pwp(0.0, 50.0, 100.0)

        >>> fk.values = 80.0
        >>> pwp.trim()
        >>> pwp
        pwp(0.0, 50.0, 80.0)
        """
        if upper is None:
            upper = exceptiontools.getattr_(self.subpars.fk, "value", None)
            if upper is None:
                upper = exceptiontools.getattr_(self.subpars.wmax, "value", None)
        super().trim(lower, upper)


# runoff generation


class BSf(lland_parameters.ParameterSoil):
    """Bodenfeuchte-Sättigungsfläche-Parameter (shape parameter for the
    relation between the avarage soil moisture and the relative saturated
    area of a subbasin) [-]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)
    INIT = 0.4


class FVF(parametertools.Parameter):
    """Frostversiegelungsfaktor zur Ermittelung des Frostversiegelungsgrades
    (frost sealing factor for determination of the degree of frost sealing
    FVG) [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 0.5


class BSFF(parametertools.Parameter):
    """Exponent zur Ermittelung des Frostversieglungsgrades (frost sealing
    exponent for determination of degree of frost sealing FVG) [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 2.0


class DMin(lland_parameters.ParameterSoil):
    """Drainageindex des mittleren Bodenspeichers (flux rate for
    releasing interflow from the middle soil compartment) [mm/T].

    In addition to the |ParameterSoil| `__call__` method, it is
    possible to set the value of parameter |DMin| in accordance
    to the keyword argument `r_dmin` due to compatibility reasons
    with the original LARSIM implementation:

        :math:`Dmin = 0.001008 \\cdot hours \\cdot r_dmin`

    Example:

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2000-01-02", "1d"
        >>> from hydpy.models.lland import *
        >>> parameterstep("1h")
        >>> nhru(1)
        >>> lnk(ACKER)
        >>> dmin(r_dmin=10.0)
        >>> dmin
        dmin(0.01008)
        >>> dmin.values
        array([0.24192])

        A wrong keyword results in the right answer:

        >>> dmin(rdmin=10.0)
        Traceback (most recent call last):
        ...
        TypeError: While trying to set the values of parameter `dmin` of \
element `?` based on keyword arguments `rdmin`, the following error occurred: \
Keyword `rdmin` is not among the available model constants.

    .. testsetup::

        >>> del pub.timegrids
    """

    NDIM, TYPE, TIME, SPAN = 1, float, True, (0.0, None)
    INIT = 0.0

    def __call__(self, *args, **kwargs) -> None:
        """The prefered way to pass values to |DMin| instances
        within parameter control files.
        """
        try:
            lland_parameters.ParameterSoil.__call__(self, *args, **kwargs)
        except TypeError:
            if (r := kwargs.get("r_dmin")) is not None:
                hours = hydpy.pub.timegrids.init.stepsize.hours
                self.value = 0.001008 * hours * numpy.array(r)
                self.trim()
            else:
                objecttools.augment_excmessage()

    def trim(self, lower=None, upper=None):
        """Trim upper values in accordance with :math:`DMin \\leq DMax`.

        >>> from hydpy.models.lland import *
        >>> parameterstep("1d")
        >>> simulationstep("12h")
        >>> nhru(5)
        >>> lnk(ACKER)
        >>> dmax.values = 2.0
        >>> dmin(-2.0, 0.0, 2.0, 4.0, 6.0)
        >>> dmin
        dmin(0.0, 0.0, 2.0, 4.0, 4.0)
        """
        if upper is None:
            upper = exceptiontools.getattr_(self.subpars.dmax, "value", None)
        super().trim(lower, upper)


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

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2000-01-02", "1d"
        >>> from hydpy.models.lland import *
        >>> parameterstep("1h")
        >>> nhru(1)
        >>> lnk(ACKER)
        >>> dmax(r_dmax=10.0)
        >>> dmax
        dmax(1.008)
        >>> dmax.values
        array([24.192])

        A wrong keyword results in the right answer:

        >>> dmax(rdmax=10.0)
        Traceback (most recent call last):
        ...
        TypeError: While trying to set the values of parameter `dmax` of \
element `?` based on keyword arguments `rdmax`, the following error occurred: \
Keyword `rdmax` is not among the available model constants.

    .. testsetup::

        >>> del pub.timegrids
    """

    NDIM, TYPE, TIME, SPAN = 1, float, True, (None, None)
    INIT = 1.0

    def __call__(self, *args, **kwargs) -> None:
        """The prefered way to pass values to |DMax| instances
        within parameter control files.
        """
        try:
            lland_parameters.ParameterSoil.__call__(self, *args, **kwargs)
        except TypeError:
            if (r := kwargs.get("r_dmax")) is not None:
                self.value = (
                    0.1008 * hydpy.pub.timegrids.init.stepsize.hours * numpy.array(r)
                )
                self.trim()
            else:
                objecttools.augment_excmessage()

    def trim(self, lower=None, upper=None):
        """Trim upper values in accordance with :math:`DMax \\geq DMin`.

        >>> from hydpy.models.lland import *
        >>> parameterstep("1d")
        >>> simulationstep("12h")
        >>> nhru(3)
        >>> lnk(ACKER)
        >>> dmin.values = 2.0
        >>> dmax(2.0, 4.0, 6.0)
        >>> dmax
        dmax(4.0, 4.0, 6.0)
        """
        if lower is None:
            lower = exceptiontools.getattr_(self.subpars.dmin, "value", None)
        super().trim(lower, upper)


class Beta(lland_parameters.ParameterSoil):
    """Drainageindex des tiefen Bodenspeichers (storage coefficient for
    releasing base flow from the lower soil compartment) [1/T]."""

    NDIM, TYPE, TIME, SPAN = 1, float, True, (0.0, None)
    INIT = 0.01


class FBeta(lland_parameters.ParameterSoil):
    """Faktor zur Erhöhung der Perkolation im Grobporenbereich (factor for
    increasing percolation under wet conditions) [-]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (1.0, None)
    INIT = 1.0


class KapMax(lland_parameters.ParameterSoil):
    """Maximale kapillare Aufstiegsrate (maximum capillary rise) [mm/T]."""

    NDIM, TYPE, TIME, SPAN = 1, float, True, (0.0, None)
    INIT = 0.0


class KapGrenz(parametertools.Parameter):
    """Grenzwerte für den kapillaren Aufstieg (threshold values related
    to the capillary rise) [mm].

    Parameter |KapGrenz| actually consists of two types of parameter values.
    Both are thresholds and related to the soil water content.  If the
    actual soil water content is smaller than or equal to the first threshold,
    capillary rise reaches its maximum value.   If the actual water content
    is larger than or equal to the second threshold, there is no capillary
    rise at all.  In between, the soil water content and the capillary rise
    are inversely related (linear interpolation).

    In the following example, the we set the lower threshold of all three
    hydrological response units to 10 mm and the upper one to 40 mm:

    >>> from hydpy.models.lland import *
    >>> parameterstep("1d")
    >>> simulationstep ("12h")
    >>> nhru(3)
    >>> kapgrenz(10.0, 40.0)
    >>> kapgrenz
    kapgrenz([[10.0, 40.0],
              [10.0, 40.0],
              [10.0, 40.0]])

    The next example shows how assign different threshold pairs to each
    response unit:

    >>> kapgrenz([10.0, 40.0], [20., 60.0], [30., 80.0])
    >>> kapgrenz
    kapgrenz([[10.0, 40.0],
              [20.0, 60.0],
              [30.0, 80.0]])

    It works equally well to pass a complete matrix, of course:

    >>> kapgrenz([[10.0, 40.0],
    ...           [20.0, 60.0],
    ...           [30.0, 80.0]])
    >>> kapgrenz
    kapgrenz([[10.0, 40.0],
              [20.0, 60.0],
              [30.0, 80.0]])

    It is also fine to pass a single value, in case you prefer a sharp
    transition between zero and maximum capillary rise:

    >>> kapgrenz(30.0)
    >>> kapgrenz
    kapgrenz(30.0)

    For convenience and better compatibility with the original `LARSIM`_
    model, we provide the keyword argument `option`.  Simply pass an option
    name and then parameter |KapGrenz| itself calculates suitable threshold
    values based on soil properties.

    The first possible string is `FK`.  When passing this string, the current
    value of parameter |FK| serves both as the lower and the upper threshold,
    which is in agreement with the `LARSIM`_ option `KAPILLARER AUFSTIEG`:

    >>> fk(60.0, 120.0, 180.0)
    >>> kapgrenz(option="FK")
    >>> kapgrenz
    kapgrenz([[60.0, 60.0],
              [120.0, 120.0],
              [180.0, 180.0]])

    The second possible string is `0_WMax/10`, which corresponds to the
    LARSIM option `KOPPELUNG BODEN/GRUNDWASSER`, where the lower and upper
    threshold are zero and 10 % of the current value of parameter |WMax|,
    respectively:

    >>> wmax(100.0, 150.0, 200.0)
    >>> kapgrenz(option="0_WMax/10")
    >>> kapgrenz
    kapgrenz([[0.0, 10.0],
              [0.0, 15.0],
              [0.0, 20.0]])

    The third possible string is `FK/2_FK` where the lower and the upper
    threshold are 50 % and 100 % of the value of parameter |FK|, which does
    not correspond to any available `LARSIM`_ option:

    >>> kapgrenz(option="FK/2_FK")
    >>> kapgrenz
    kapgrenz([[30.0, 60.0],
              [60.0, 120.0],
              [90.0, 180.0]])

    Wrong keyword arguments result in errors like the following:


    >>> kapgrenz(option1="FK", option2="0_WMax/10")
    Traceback (most recent call last):
    ...
    ValueError: Parameter `kapgrenz` of element `?` does not accept multiple \
keyword arguments, but the following are given: option1 and option2

    >>> kapgrenz(option1="FK")
    Traceback (most recent call last):
    ...
    ValueError: Besides the standard keyword arguments, parameter `kapgrenz` \
of element `?` does only support the keyword argument `option`, but `option1` \
is given.

    >>> kapgrenz(option="NFk")
    Traceback (most recent call last):
    ...
    ValueError: Parameter `kapgrenz` of element `?` supports the options \
`FK`, `0_WMax/10`, and `FK/2_FK`, but `NFk` is given.
    """

    CONTROLPARAMETERS = (WMax, FK)
    NDIM, TYPE, TIME, SPAN = 2, float, None, (None, None)
    INIT = 0.0

    def __call__(self, *args, **kwargs) -> None:
        try:
            super().__call__(*args, **kwargs)
        except NotImplementedError:
            if len(kwargs) > 1:
                raise ValueError(
                    f"Parameter {objecttools.elementphrase(self)} does not "
                    f"accept multiple keyword arguments, but the following "
                    f"are given: {objecttools.enumeration(kwargs.keys())}"
                ) from None
            if "option" not in kwargs:
                raise ValueError(
                    f"Besides the standard keyword arguments, parameter "
                    f"{objecttools.elementphrase(self)} does only support "
                    f"the keyword argument `option`, but `{tuple(kwargs)[0]}` "
                    f"is given."
                ) from None
            con = self.subpars
            self.values = 0.0
            if kwargs["option"] == "FK/2_FK":
                self.values[:, 0] = 0.5 * con.fk  # type: ignore[index]
                self.values[:, 1] = con.fk  # type: ignore[index]
            elif kwargs["option"] == "0_WMax/10":
                self.values[:, 0] = 0.0  # type: ignore[index]
                self.values[:, 1] = 0.1 * con.wmax  # type: ignore[index]
            elif kwargs["option"] == "FK":
                self.values[:, 0] = con.fk  # type: ignore[index]
                self.values[:, 1] = con.fk  # type: ignore[index]
            else:
                raise ValueError(
                    f"Parameter {objecttools.elementphrase(self)} supports "
                    f"the options `FK`, `0_WMax/10`, and `FK/2_FK`, but "
                    f"`{kwargs['option']}` is given."
                ) from None


class RBeta(parametertools.Parameter):
    """Boolscher Parameter der steuert, ob the Perkolation unterhalb der
    Feldkapazität auf Null reduziert wird (flag to indicate if seepage is
    reduced to zero below field capacity) [-]."""

    NDIM, TYPE, TIME, SPAN = 0, bool, None, (False, True)
    INIT = False


class VolBMax(parametertools.Parameter):
    """Maximaler Inhalt des Gebietsspeichers für Basisabfluss (highest possible base
    flow storage) [mm]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = numpy.inf


class GSBMax(parametertools.Parameter):
    """Faktor zur Anpassung von |VolBMax| (factor for adjusting |VolBMax|) [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 1.0


class GSBGrad1(parametertools.Parameter):
    """Höchste Volumenzunahme des Gebietsspeichers für Basisabfluss ohne Begrenzung
    des Zuflusses (highest possible baseflow storage increase without inflow
    reductions) [mm/T]."""

    NDIM, TYPE, TIME, SPAN = 0, float, True, (None, None)
    INIT = numpy.inf

    def trim(self, lower=None, upper=None):
        r"""Trim upper values in accordance with :math:`GSBGrad1 \leq GSBGrad2`.

        >>> from hydpy.models.lland import *
        >>> simulationstep("1h")
        >>> parameterstep("1d")
        >>> gsbgrad2(1.0)
        >>> gsbgrad1(0.0)
        >>> gsbgrad1
        gsbgrad1(0.0)
        >>> gsbgrad1(1.0)
        >>> gsbgrad1
        gsbgrad1(1.0)
        >>> gsbgrad1(2.0)
        >>> gsbgrad1
        gsbgrad1(1.0)
        """
        if upper is None:
            upper = exceptiontools.getattr_(self.subpars.gsbgrad2, "value", None)
        super().trim(lower, upper)


class GSBGrad2(parametertools.Parameter):
    """Volumenzunahme des Gebietsspeichers für Basisabfluss, oberhalb der jeglicher
    Zufluss ausgeschlossen ist (highest possible baseflow storage increase) [mm/T]."""

    NDIM, TYPE, TIME, SPAN = 0, float, True, (None, None)
    INIT = numpy.inf

    def trim(self, lower=None, upper=None):
        r"""Trim upper values in accordance with :math:`GSBGrad1 \leq GSBGrad2`.

        >>> from hydpy.models.lland import *
        >>> simulationstep("1h")
        >>> parameterstep("1d")
        >>> gsbgrad1(1.0)
        >>> gsbgrad2(2.0)
        >>> gsbgrad2
        gsbgrad2(2.0)
        >>> gsbgrad2(1.0)
        >>> gsbgrad2
        gsbgrad2(1.0)
        >>> gsbgrad2(0.0)
        >>> gsbgrad2
        gsbgrad2(1.0)
        """
        if lower is None:
            lower = exceptiontools.getattr_(self.subpars.gsbgrad1, "value", None)
        super().trim(lower, upper)


# runoff concentration


class A1(parametertools.Parameter):
    """Parameter für die kontinuierliche Aufteilung der
    Direktabflusskomponenten (threshold value for the continuous seperation
    of direct runoff in a slow and a fast component) [mm/T]
    """

    NDIM, TYPE, TIME, SPAN = 0, float, True, (0.0, None)
    INIT = numpy.inf


class A2(parametertools.Parameter):
    """Parameter für die diskontinuierliche Aufteilung der
    Direktabflusskomponenten (threshold value for the discontinuous seperation
    of direct runoff in a slow and a fast component) [mm/T]
    """

    NDIM, TYPE, TIME, SPAN = 0, float, True, (0.0, None)
    INIT = 0.0


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
        >>> parameterstep("1d")
        >>> simulationstep("12h")
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
element `?` has been set to an unrealistic value of 0.000134 hours.

        Additionally, exceptions for missing (or wrong) keywords are
        implemented

        >>> tind(tal=5.0, hot=210.0)
        Traceback (most recent call last):
        ...
        ValueError: For the alternative calculation of parameter `tind`, \
values for all three keyword keyword arguments `tal`, `hot`, and `hut` \
must be given.

    """

    NDIM, TYPE, TIME, SPAN = 0, float, False, (0.0, None)
    INIT = 1.0

    def __call__(self, *args, **kwargs) -> None:
        try:
            super().__call__(*args, **kwargs)
        except NotImplementedError:
            try:
                tal = float(kwargs["tal"])
                hot = float(kwargs["hot"])
                hut = float(kwargs["hut"])
            except KeyError:
                raise ValueError(
                    "For the alternative calculation of parameter `tind`, "
                    "values for all three keyword keyword arguments `tal`, "
                    "`hot`, and `hut` must be given."
                ) from None
            if (tal <= 0.0) or (hot <= hut):
                raise ValueError(
                    f"For the alternative calculation of parameter `tind`, "
                    f"the value assigned to keyword argument `tal` must be "
                    f"greater then zero and the one of `hot` must be greater "
                    f"than the one of `hut`.  However, for element "
                    f"{objecttools.devicename(self)}, the values `{tal}`, "
                    f"`{hot}` and `{hut}` were given respectively."
                ) from None
            self.value = (0.868 * tal**3 / (hot - hut)) ** 0.385
            if (self > 1000.0) or (self < 0.001):
                warnings.warn(
                    f"Due to the given values for the keyword arguments "
                    f"`tal` ({tal}), `hot` ({hot}) and `hut` ({hut}), "
                    f"parameter `tind` of element "
                    f"`{objecttools.devicename(self)}` has been set to an "
                    f"unrealistic value of {objecttools.repr_(self.value)} "
                    f"hours."
                )
            self.value *= timetools.Period("1h") / hydpy.pub.options.simulationstep


class EQB(parametertools.Parameter):
    """Kalibrierfaktor für die Basisabflusskonzentration (factor for adjusting
    the concentration time of baseflow). [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 5000.0


class EQI1(parametertools.Parameter):
    """Kalibrierfaktor für die "untere" Zwischenabflusskonzentration
    (factor for adjusting the concentration time of the first interflow
    component) [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 2000.0

    def trim(self, lower=None, upper=None):
        """Trim upper values in accordance with :math:`EQI2 \\leq EQI1`.

        >>> from hydpy.models.lland import *
        >>> parameterstep("1d")
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
        """
        if lower is None:
            lower = exceptiontools.getattr_(self.subpars.eqi2, "value", None)
        super().trim(lower, upper)


class EQI2(parametertools.Parameter):
    """Kalibrierfaktor für die "obere" Zwischenabflusskonzentration
    (factor for adjusting the concentration time of the second interflow
    component) [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 1000.0

    def trim(self, lower=None, upper=None):
        """Trim upper values in accordance with :math:`EQI2 \\leq EQI1`.

        >>> from hydpy.models.lland import *
        >>> parameterstep("1d")
        >>> eqi1.value = 3.0
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
        if upper is None:
            upper = exceptiontools.getattr_(self.subpars.eqi1, "value", None)
        super().trim(lower, upper)


class EQD1(parametertools.Parameter):
    """Kalibrierfaktor für die langsamere Direktabflusskonzentration (factor
    for adjusting the concentration time of the slower component of direct
    runoff). [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 100.0

    def trim(self, lower=None, upper=None):
        """Trim upper values in accordance with :math:`EQD2 \\leq EQD1`.

        >>> from hydpy.models.lland import *
        >>> parameterstep("1d")
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
        """
        if lower is None:
            lower = exceptiontools.getattr_(self.subpars.eqd2, "value", None)
        super().trim(lower, upper)


class EQD2(parametertools.Parameter):
    """Kalibrierfaktor für die schnellere Direktabflusskonzentration (factor
    for adjusting the concentration time of the faster component of direct
    runoff). [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)
    INIT = 50.0

    def trim(self, lower=None, upper=None):
        """Trim upper values in accordance with :math:`EQD2 \\leq EQD1`.

        >>> from hydpy.models.lland import *
        >>> parameterstep("1d")
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
            upper = exceptiontools.getattr_(self.subpars.eqd1, "value", None)
        super().trim(lower, upper)


class NegQ(parametertools.Parameter):
    """Option: sind negative Abflüsse erlaubt (flag that indicated whether
    negative discharge values are allowed or not) [-]."""

    NDIM, TYPE, TIME, SPAN = 0, bool, None, (0.0, None)
    INIT = False


WMax.CONTROLPARAMETERS = (PWP, FK)
FK.CONTROLPARAMETERS = (PWP, WMax)
