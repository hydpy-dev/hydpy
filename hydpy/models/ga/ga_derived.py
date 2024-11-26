# pylint: disable=missing-module-docstring

# import...
# ...from site-packages
import numpy

# ...from HydPy
from hydpy.core import parametertools
from hydpy.models.ga import ga_control


class NmbSubsteps(parametertools.Parameter):
    """The number of numerical substeps in each simulation step [-]."""

    NDIM, TYPE, TIME, SPAN = 0, int, None, (1, numpy.inf)

    CONTROLPARAMETERS = (ga_control.DT,)

    def update(self) -> None:
        """Calculate the number of substeps based on :math:`NmbSubsteps = 1 / DT`.

        >>> from hydpy.models.ga import *
        >>> simulationstep("1h")
        >>> parameterstep("1h")
        >>> dt(0.5)
        >>> derived.nmbsubsteps.update()
        >>> derived.nmbsubsteps
        nmbsubsteps(2)
        """
        self.value = int(round(1.0 / self.subpars.pars.control.dt.value))


class SoilAreaFraction(parametertools.Parameter):
    """The area fraction of each soil compartment [-]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, 1.0)

    CONTROLPARAMETERS = (ga_control.SoilArea,)

    def update(self) -> None:
        r"""Calculate the fractions based on
        :math:`SoilAreaFraction_i = SoilArea_i / \Sigma SoilArea`.

        >>> from hydpy.models.ga import *
        >>> parameterstep()
        >>> nmbsoils(5)
        >>> soilarea(10.0, 40.0, 20.0, 25.0, 5.0)
        >>> derived.soilareafraction.update()
        >>> derived.soilareafraction
        soilareafraction(0.1, 0.4, 0.2, 0.25, 0.05)
        """
        soilarea = self.subpars.pars.control.soilarea.values
        self.values = soilarea / numpy.sum(soilarea)


class EffectiveCapillarySuction(parametertools.Parameter):
    """The effective capillary suction according to the Brooks-Corey soil moisture
    characteristic model :cite:p:`ref-Brooks1966` [mm]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)

    CONTROLPARAMETERS = (ga_control.PoreSizeDistribution, ga_control.AirEntryPotential)

    def update(self) -> None:
        r"""Calculate the effective capillary suction based on the current values of
        |AirEntryPotential| and |PoreSizeDistribution|.

        The used equation follows equation 13 of :cite:t:`ref-Lai2015` if setting the
        initial equal to the residual water content:

          :math:`EffectiveCapillarySuction = AirEntryPotential \cdot
          \frac{3 \cdot PoreSizeDistribution + 2}{3 \cdot PoreSizeDistribution + 1}`
        """
        control = self.subpars.pars.control
        psd = control.poresizedistribution.values
        aep = control.airentrypotential.values
        self.values = aep * (3.0 * psd + 2.0) / (3.0 * psd + 1.0)
