# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from standard library
import warnings

# ...from site-packages
import networkx
import numpy

# ...from HydPy
import hydpy
from hydpy.core import objecttools
from hydpy.core import parametertools

# ...from hland
from hydpy.models.hland import hland_parameters
from hydpy.models.hland import hland_control
from hydpy.models.hland.hland_constants import ILAKE, GLACIER, SEALED

_ZERO_DIVISION_MESSAGE = "divide by zero encountered in"


class DOY(parametertools.DOYParameter):
    """References the |Indexer.dayofyear| index array provided by the instance of
    class |Indexer| available in module |pub| [-]."""


class RelZoneAreas(hland_parameters.ParameterComplete):
    """Relative area of all zones [-]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, 1.0)
    strict_valuehandling: bool = False

    CONTROLPARAMETERS = (
        hland_control.ZoneArea,
        hland_control.ZoneType,
        hland_control.Psi,
    )

    def update(self) -> None:
        """Update the relative area based on the parameters |ZoneArea|, |ZoneType|,
        and |Psi|.

        In the simplest case, |RelZoneAreas| provides the fractions of the zone areas
        available via the control parameter |ZoneArea|:

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> area(100.0)
        >>> nmbzones(5)
        >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, SEALED)
        >>> zonearea(10.0, 40.0, 20.0, 25.0, 5.0)
        >>> psi(1.0)
        >>> derived.relzoneareas.update()
        >>> derived.relzoneareas
        relzoneareas(field=0.1, forest=0.4, glacier=0.2, ilake=0.25,
                     sealed=0.05)

        |hland| assumes complete sealing for zones classified as land-use type
        |SEALED|.  Hence, besides interception losses, their runoff coefficient is
        always one.  When deriving zone types from available land-use classifications,
        we are likely to identify zones as |SEALED| that actually have lower runoff
        coefficients due to incomplete sealing, infiltration of sealed surface runoff
        on adjacent unsealed areas, retention of surface runoff in sewage treatment
        plants, and many other issues.  Parameter |Psi| allows decreasing the effective
        relative area of zones of type |SEALED|. Method |RelZoneAreas.update| divides
        the remaining "uneffective" sealed area to all zones of different land-use
        types (proportionally to their sizes), except those of type |GLACIER|:

        >>> psi(0.6)
        >>> derived.relzoneareas.update()
        >>> derived.relzoneareas
        relzoneareas(field=0.102667, forest=0.410667, glacier=0.2,
                     ilake=0.256667, sealed=0.03)

        For subbasins without |SEALED| zones, the value of |Psi| is irrelevant:

        >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, ILAKE)
        >>> derived.relzoneareas.update()
        >>> derived.relzoneareas
        relzoneareas(0.1, 0.4, 0.2, 0.25, 0.05)

        The same holds for subbasins consisting only of |SEALED| and |GLACIER| zones:

        >>> zonetype(SEALED)
        >>> derived.relzoneareas.update()
        >>> derived.relzoneareas
        relzoneareas(0.1, 0.4, 0.2, 0.25, 0.05)
        >>> zonetype(GLACIER, GLACIER, SEALED, SEALED, SEALED)
        >>> derived.relzoneareas.update()
        >>> derived.relzoneareas
        relzoneareas(0.1, 0.4, 0.2, 0.25, 0.05)

        The last example demonstrates that the underlying algorithm also works when
        multiple |SEALED| or |GLACIER| zones are involved:

        >>> zonetype(FIELD, GLACIER, GLACIER, SEALED, SEALED)
        >>> derived.relzoneareas.update()
        >>> derived.relzoneareas
        relzoneareas(0.22, 0.4, 0.2, 0.15, 0.03)
        """
        control = self.subpars.pars.control
        zonearea = control.zonearea.values
        zonetype = control.zonetype.values
        psi = control.psi.value
        idxs_source = zonetype == SEALED
        idxs_sink = ~idxs_source * (zonetype != GLACIER)
        if (psi < 1.0) and numpy.any(idxs_source) and numpy.any(idxs_sink):
            adjusted_area = zonearea.copy()
            adjusted_area[idxs_source] *= psi
            delta = numpy.sum(zonearea) - numpy.sum(adjusted_area)
            weights = adjusted_area[idxs_sink] / numpy.sum(adjusted_area[idxs_sink])
            adjusted_area[idxs_sink] += weights * delta
            self.values = adjusted_area / numpy.sum(adjusted_area)
        else:
            self.values = zonearea / numpy.sum(zonearea)


class RelSoilArea(parametertools.Parameter):
    """Relative area of all |FIELD| and |FOREST| zones [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, 1.0)

    CONTROLPARAMETERS = (hland_control.ZoneType,)
    DERIVEDPARAMETERS = (RelZoneAreas,)

    def update(self):
        """Update |RelSoilArea| based on |RelZoneAreas| and |ZoneType|.

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> nmbzones(5)
        >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, SEALED)
        >>> derived.relzoneareas(0.1, 0.2, 0.15, 0.25, 0.3)
        >>> derived.relsoilarea.update()
        >>> derived.relsoilarea
        relsoilarea(0.3)
        """
        zonetype = self.subpars.pars.control.zonetype.values
        temp = self.subpars.relzoneareas.values.copy()
        temp[zonetype == GLACIER] = 0.0
        temp[zonetype == ILAKE] = 0.0
        temp[zonetype == SEALED] = 0.0
        self(numpy.sum(temp))


class RelLandArea(parametertools.Parameter):
    """Relative area of all |FIELD|, |FOREST|, |GLACIER|, and |SEALED| zones [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, 1.0)

    CONTROLPARAMETERS = (hland_control.ZoneType,)
    DERIVEDPARAMETERS = (RelZoneAreas,)

    def update(self):
        """Update |RelLandArea| based on |RelZoneAreas| and |ZoneType|.

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> nmbzones(5)
        >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, SEALED)
        >>> derived.relzoneareas(0.1, 0.2, 0.3, 0.15, 0.25)
        >>> derived.rellandarea.update()
        >>> derived.rellandarea
        rellandarea(0.85)
        """
        temp = self.subpars.relzoneareas.values.copy()
        temp[self.subpars.pars.control.zonetype.values == ILAKE] = 0.0
        self(numpy.sum(temp))


class RelUpperZoneArea(parametertools.Parameter):
    """Relative area of all |FIELD|, |FOREST|, and |GLACIER| zones [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, 1.0)

    CONTROLPARAMETERS = (hland_control.ZoneType,)
    DERIVEDPARAMETERS = (RelZoneAreas,)

    def update(self):
        """Update |RelUpperZoneArea| based on |RelZoneAreas| and |ZoneType|.

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> nmbzones(5)
        >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, SEALED)
        >>> derived.relzoneareas(0.1, 0.2, 0.3, 0.15, 0.25)
        >>> derived.relupperzonearea.update()
        >>> derived.relupperzonearea
        relupperzonearea(0.6)
        """
        zonetype = self.subpars.pars.control.zonetype.values
        temp = self.subpars.relzoneareas.values.copy()
        temp[zonetype == ILAKE] = 0.0
        temp[zonetype == SEALED] = 0.0
        self(numpy.sum(temp))


class RelLowerZoneArea(parametertools.Parameter):
    """Relative area of all |FIELD|, |FOREST|, |GLACIER|, and |ILAKE| zones [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, 1.0)

    CONTROLPARAMETERS = (hland_control.ZoneType,)
    DERIVEDPARAMETERS = (RelZoneAreas,)

    def update(self):
        """Update |RelLowerZoneArea| based on |RelZoneAreas| and |ZoneType|.

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> nmbzones(5)
        >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, SEALED)
        >>> derived.relzoneareas(0.1, 0.2, 0.3, 0.15, 0.25)
        >>> derived.rellowerzonearea.update()
        >>> derived.rellowerzonearea
        rellowerzonearea(0.75)
        """
        temp = self.subpars.relzoneareas.values.copy()
        temp[self.subpars.pars.control.zonetype.values == SEALED] = 0.0
        self(numpy.sum(temp))


class ZoneAreaRatios(parametertools.Parameter):
    """Ratios of all zone combinations [-]."""

    NDIM, TYPE, TIME, SPAN = 2, float, None, (0.0, None)

    DERIVEDPARAMETERS = (RelZoneAreas,)

    def update(self) -> None:
        """Update the zone area ratios based on the parameter |ZoneArea|.

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> nmbzones(3)
        >>> derived.relzoneareas(0.0625, 0.3125, 0.625)
        >>> derived.zonearearatios.update()
        >>> derived.zonearearatios
        zonearearatios([[1.0, 0.2, 0.1],
                        [5.0, 1.0, 0.5],
                        [10.0, 2.0, 1.0]])
        """
        relzoneareas = self.subpars.relzoneareas.values
        self.values = relzoneareas[:, numpy.newaxis] / relzoneareas


class IndicesZoneZ(parametertools.Parameter):
    """Indices of the zones sorted by altitude [-]."""

    NDIM, TYPE, TIME, SPAN = 1, int, None, (0, None)

    CONTROLPARAMETERS = (hland_control.ZoneZ,)

    def update(self) -> None:
        """Update the indices based on the order of the values of parameter |ZoneZ|.

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> nmbzones(5)
        >>> zonez(3.0, 4.0, 2.0, 5.0, 3.0)
        >>> derived.indiceszonez.update()
        >>> derived.indiceszonez
        indiceszonez(2, 0, 4, 1, 3)
        """
        self.values = numpy.argsort(self.subpars.pars.control.zonez.values)


class Z(parametertools.Parameter):
    """Average (reference) subbasin elevation [100m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)

    CONTROLPARAMETERS = (
        hland_control.Area,
        hland_control.ZoneArea,
        hland_control.ZoneZ,
    )

    def update(self) -> None:
        """Average the individual zone elevations.

        >>> from hydpy.models.hland import *
        >>> parameterstep()
        >>> nmbzones(3)
        >>> area(10.0)
        >>> zonearea(5.0, 3.0, 2.0)
        >>> zonez(1.0, 3.0, 8.0)
        >>> derived.z.update()
        >>> derived.z
        z(3.0)
        """
        control = self.subpars.pars.control
        self.value = (
            numpy.dot(control.zonearea.values, control.zonez.values)
            / control.area.value
        )


class SRedOrder(parametertools.Parameter):
    """Processing order for the snow redistribution routine [-]."""

    NDIM, TYPE, TIME, SPAN = 2, int, None, (0, None)

    CONTROLPARAMETERS = (hland_control.SRed,)

    def update(self) -> None:
        """Update the processing order based on the weighting factors defined by
        parameter |SRed|.

        An example for well-sorted data:

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> nmbzones(6)
        >>> zonetype(FIELD)
        >>> sred([[0.0, 0.2, 0.2, 0.2, 0.2, 0.2],
        ...       [0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
        ...       [0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
        ...       [0.0, 0.0, 0.0, 0.0, 0.5, 0.5],
        ...       [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ...       [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]])
        >>> derived.sredorder.update()
        >>> derived.sredorder
        sredorder([[0, 1],
                   [0, 2],
                   [0, 3],
                   [0, 4],
                   [0, 5],
                   [1, 2],
                   [2, 3],
                   [3, 4],
                   [3, 5]])

        An erroneous example, including a cycle:

        >>> sred([[0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
        ...       [0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
        ...       [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ...       [0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
        ...       [0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
        ...       [0.0, 0.4, 0.4, 0.2, 0.0, 0.0]])
        >>> derived.sredorder.update()
        Traceback (most recent call last):
        ...
        RuntimeError: The weighting factors of parameter `sred` of element `?` define \
at least one cycle: (1, 4), (4, 5), and (5, 1).

        A "no redistribution" example:

        >>> sred(0.0)
        >>> derived.sredorder.update()
        >>> derived.sredorder
        sredorder([[]])

        An example or unsorted data:

        >>> nmbzones(5)
        >>> zonetype(FIELD)
        >>> sred([[0.0, 0.5, 0.0, 0.5, 0.0],
        ...       [0.0, 0.0, 0.0, 0.0, 0.0],
        ...       [0.0, 0.0, 0.0, 0.0, 1.0],
        ...       [0.0, 0.0, 0.0, 0.0, 0.0],
        ...       [1.0, 0.0, 0.0, 0.0, 0.0]])
        >>> derived.sredorder.update()
        >>> derived.sredorder
        sredorder([[2, 4],
                   [4, 0],
                   [0, 1],
                   [0, 3]])
        """
        sred = self.subpars.pars.control.sred
        idxs, jdxs = numpy.nonzero(sred.values)
        self.shape = len(idxs), 2
        if len(idxs):
            dg = networkx.DiGraph(zip(idxs, jdxs))
            try:
                first_cycle = networkx.find_cycle(dg)
                raise RuntimeError(
                    f"The weighting factors of parameter "
                    f"{objecttools.elementphrase(sred)} define at least one cycle: "
                    f"{objecttools.enumeration(first_cycle)}."
                )
            except networkx.NetworkXNoCycle:
                self.values = tuple(networkx.topological_sort(networkx.line_graph(dg)))
        else:
            self.values = 0.0


class SRedEnd(parametertools.Parameter):
    """Flags that indicate the "dead ends" of snow redistribution within a subbasin."""

    NDIM, TYPE, TIME, SPAN = 1, int, None, (False, True)

    CONTROLPARAMETERS = (hland_control.NmbZones,)
    DERIVEDPARAMETERS = (SRedOrder,)

    def update(self) -> None:
        """Update the dead-end flags based on parameter |SRedOrder|.

        >>> from hydpy.models.hland_v1 import *
        >>> parameterstep("1d")
        >>> nmbzones(6)
        >>> derived.sredorder.shape = 9, 2
        >>> derived.sredorder([[0, 1],
        ...                    [0, 2],
        ...                    [1, 2],
        ...                    [0, 3],
        ...                    [2, 3],
        ...                    [0, 4],
        ...                    [3, 4],
        ...                    [0, 5],
        ...                    [3, 5]])
        >>> derived.sredend.update()
        >>> derived.sredend
        sredend(0, 0, 0, 0, 1, 1)
        """
        nmbzones = self.subpars.pars.control.nmbzones.value
        sredorder = self.subpars.sredorder.values
        self.values = ~numpy.isin(numpy.arange(nmbzones), sredorder[:, 0])


class SRedNumber(parametertools.Parameter):
    """The total number of snow redistribution paths [-]."""

    NDIM, TYPE, TIME, SPAN = 0, int, None, (0, None)

    CONTROLPARAMETERS = (hland_control.SRed,)
    DERIVEDPARAMETERS = (ZoneAreaRatios,)

    def update(self) -> None:
        """Update the number of redistribution paths based on the parameter |SRedOrder|.

        >>> from hydpy.models.hland import *
        >>> parameterstep("1d")
        >>> derived.sredorder.shape = 8, 3
        >>> derived.srednumber.update()
        >>> derived.srednumber
        srednumber(8)
        """
        self.value = self.subpars.sredorder.shape[0]


class TTM(hland_parameters.ParameterLand):
    """Threshold temperature for snow melting and refreezing [°C]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)

    CONTROLPARAMETERS = (hland_control.TT, hland_control.DTTM)

    def update(self):
        """Update |TTM| based on :math:`TTM = TT + DTTM`.

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
        self(1.0 / self.subpars.pars.control.recstep)


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
        r"""Update |hland_derived.K4| based on :math:`K4 = 9 \cdot K3`.

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

            This method also updates the shape of the log sequence |QUH|.

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
            full_2 = full**2.0
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
                    2 * half**2.0 - half_f**2.0 - half_c**2.0
                ) / (2.0 * full_2)
            # ...of the falling limb (eventually except the last one).
            points = numpy.arange(half_c + 1.0, full_f + 1.0)
            uh[half_c:full_f] = 1.0 / full - (2.0 * points - 1.0) / (2.0 * full_2)
            # ...at the end (if not already done).
            if numpy.mod(full, 1.0) != 0.0:
                uh[full_f] = (full - full_f) / full - (full_2 - full_f**2.0) / (
                    2.0 * full_2
                )
            # Normalize the ordinates.
            self(uh / numpy.sum(uh))


class KSC(parametertools.Parameter):
    """Coefficient of the individual storages of the linear storage cascade [1/T]."""

    NDIM, TYPE, TIME, SPAN = 0, float, True, (0.0, None)

    CONTROLPARAMETERS = (hland_control.MaxBaz, hland_control.NmbStorages)

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
