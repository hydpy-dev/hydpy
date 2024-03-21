# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from site-packages
import numpy

# ...from HydPy
import hydpy
from hydpy.core import exceptiontools
from hydpy.core import objecttools
from hydpy.core import parametertools

# ...from evap
from hydpy.models.evap import evap_parameters
from hydpy.models.evap import evap_control
from hydpy.models.evap import evap_fixed
from hydpy.models.evap import evap_logs


class MOY(parametertools.MOYParameter):
    """References the "global" month of the year index array [-]."""


class HRUAreaFraction(parametertools.Parameter):
    """The area fraction of each hydrological response unit [-]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, 1.0)

    CONTROLPARAMETERS = (evap_control.HRUArea,)

    def update(self) -> None:
        r"""Calculate the fractions based on
        :math:`HRUAreaFraction_i = HRUArea_i / \Sigma HRUArea`.

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(5)
        >>> hruarea(10.0, 40.0, 20.0, 25.0, 5.0)
        >>> derived.hruareafraction.update()
        >>> derived.hruareafraction
        hruareafraction(0.1, 0.4, 0.2, 0.25, 0.05)
        """
        hruarea = self.subpars.pars.control.hruarea.values
        self.values = hruarea / numpy.sum(hruarea)


class Altitude(parametertools.Parameter):
    """Average (reference) subbasin altitude [100m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)

    CONTROLPARAMETERS = (evap_control.HRUArea, evap_control.HRUAltitude)

    def update(self) -> None:
        """Average the individual hydrological response units' altitudes.

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(3)
        >>> hruarea(5.0, 3.0, 2.0)
        >>> hrualtitude(1.0, 3.0, 8.0)
        >>> derived.altitude.update()
        >>> derived.altitude
        altitude(3.0)
        """
        control = self.subpars.pars.control
        self.value = numpy.dot(
            control.hruarea.values, control.hrualtitude.values
        ) / numpy.sum(control.hruarea.values)


class Seconds(parametertools.SecondsParameter):
    """The length of the actual simulation step size in seconds [h]."""


class Hours(parametertools.HoursParameter):
    """The length of the actual simulation step size in hours [h]."""


class Days(parametertools.DaysParameter):
    """The length of the actual simulation step size in days [d]."""


class NmbLogEntries(parametertools.Parameter):
    """The number of log entries required for a memory duration of 24 hours [-]."""

    NDIM, TYPE, TIME, SPAN = 0, int, None, (1, None)

    def update(self):
        """Calculate the number of entries and adjust the shape of all relevant log
        sequences.

        The aimed memory duration is one day.  Hence, the number of required log
        entries depends on the simulation step size:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2000-01-02", "8h"
        >>> nmbhru(2)
        >>> derived.nmblogentries.update()
        >>> derived.nmblogentries
        nmblogentries(3)
        >>> logs.loggedglobalradiation
        loggedglobalradiation(nan, nan, nan)

        For 1-dimensional logged properties, there is a second axis whose size depends
        on the selected number of hydrological response units:

        >>> logs.loggedairtemperature
        loggedairtemperature([[nan, nan],
                              [nan, nan],
                              [nan, nan]])

        >>> logs.loggedpotentialevapotranspiration
        loggedpotentialevapotranspiration(nan, nan, nan)

        To prevent losing information, updating parameter |NmbLogEntries| resets the
        shape of the relevant log sequences only when necessary:

        >>> logs.loggedglobalradiation = 1.0
        >>> logs.loggedairtemperature = 2.0
        >>> logs.loggedpotentialevapotranspiration = 3.0
        >>> derived.nmblogentries.update()
        >>> logs.loggedglobalradiation
        loggedglobalradiation(1.0, 1.0, 1.0)
        >>> logs.loggedairtemperature
        loggedairtemperature([[2.0, 2.0],
                              [2.0, 2.0],
                              [2.0, 2.0]])
        >>> logs.loggedpotentialevapotranspiration
        loggedpotentialevapotranspiration(3.0, 3.0, 3.0)

        There is an explicit check for inappropriate simulation step sizes:

        >>> pub.timegrids = "2000-01-01 00:00", "2000-01-01 10:00", "5h"
        >>> derived.nmblogentries.update()
        Traceback (most recent call last):
        ...
        ValueError: The value of parameter `nmblogentries` of element `?` cannot be \
determined for a the current simulation step size.  The fraction of the memory period \
(1d) and the simulation step size (5h) leaves a remainder.
        """
        nmb = "1d" / hydpy.pub.timegrids.stepsize
        if nmb % 1:
            raise ValueError(
                f"The value of parameter {objecttools.elementphrase(self)} cannot be "
                f"determined for a the current simulation step size.  The fraction of "
                f"the memory period (1d) and the simulation step size "
                f"({hydpy.pub.timegrids.stepsize}) leaves a remainder."
            )
        self(nmb)
        pars = self.subpars.pars
        for seq in pars.model.sequences.logs:
            if isinstance(seq, evap_logs.LoggedPotentialEvapotranspiration):
                new_shape = self.value
                old_shape = exceptiontools.getattr_(seq, "shape", (None, None))[1]
            else:
                if seq.NDIM == 1:
                    new_shape = (self.value,)
                elif seq.NDIM == 2:
                    new_shape = self.value, pars.control.nmbhru.value
                old_shape = exceptiontools.getattr_(seq, "shape", (None,))
            if new_shape != old_shape:
                seq.shape = new_shape


class RoughnessLength(
    evap_parameters.LandMonthParameter
):  # ToDo: not directy required, remove?
    """Roughness length [m]."""

    TYPE, TIME, SPAN = float, None, (0.0, None)

    CONTROLPARAMETERS = (evap_control.CropHeight,)

    def update(self):
        r"""Calculate the roughness length based on
        :math:`max(0.13 \cdot CropHeight, \ 0.00013)`.

        The original equation seems to go back to Montheith.  We added the minimum
        value of 0.13 mm to cope with water areas and bare soils (to avoid zero
        roughness lengths):

        ToDo: Add a reference.

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(3)
        >>> cropheight(
        ...     ANY=[0.0, 0.001, 0.01, 0.1, 1.0, 2.0, 3.0, 4.0, 5.0, 10.0, 15.0, 20.0])
        >>> derived.roughnesslength.update()
        >>> derived.roughnesslength
        roughnesslength(ANY=[0.00013, 0.00013, 0.0013, 0.013, 0.13, 0.26, 0.39,
                             0.52, 0.65, 1.3, 1.95, 2.6])
        """
        cropheight = self.subpars.pars.control.cropheight.values
        self.values = numpy.clip(0.13 * cropheight, 0.00013, None)


class AerodynamicResistanceFactor(evap_parameters.LandMonthParameter):
    """Factor for calculating aerodynamic resistance [-]."""

    TYPE, TIME, SPAN = float, None, (0.0, None)

    CONTROLPARAMETERS = (evap_control.CropHeight,)
    DERIVEDPARAMETERS = (RoughnessLength,)
    FIXEDPARAMETERS = (evap_fixed.AerodynamicResistanceFactorMinimum,)

    def update(self):
        r"""Calculate the factor for calculating aerodynamic resistance based on the
        :math:`max \big( ln(2 / z_0) \cdot ln(10 / z_0) / 0.41^2, \ \tau \big)` with
        :math:`z_0` being the |RoughnessLength| :cite:p:`ref-Löpmeier2014` and
        :math:`\tau` the "alternative value" suggested by :cite:t:`ref-Thompson1981`
        and also used by :cite:t:`ref-LARSIM`.


        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> derived.roughnesslength(
        ...     ANY=[0.00013, 0.00013, 0.0013, 0.013, 0.13, 0.26, 0.39, 0.52, 0.65,
        ...          1.3, 1.95, 2.6])
        >>> derived.aerodynamicresistancefactor.update()
        >>> derived.aerodynamicresistancefactor
        aerodynamicresistancefactor(ANY=[752.975177, 752.975177, 476.301466,
                                         262.708041, 112.194903, 94.0, 94.0, 94.0,
                                         94.0, 94.0, 94.0, 94.0])
        """
        pars = self.subpars.pars
        z0 = pars.derived.roughnesslength.values
        min_ = pars.fixed.aerodynamicresistancefactorminimum.value
        self.values = numpy.clip(
            numpy.log(10.0 / z0) * numpy.log(10.0 / z0) / 0.41**2, min_, None
        )
