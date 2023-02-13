# -*- coding: utf-8 -*-
"""
.. _`issue 89`: https://github.com/hydpy-dev/hydpy/issues/89
"""
# imports...
# ...from site-packages
import numpy

# ...from HydPy
from hydpy.core import importtools
from hydpy.core import modeltools
from hydpy.core.typingtools import *
from hydpy.cythons import modelutils
from hydpy.interfaces import soilinterfaces

# ...from hland
from hydpy.models.ga import ga_control
from hydpy.models.ga import ga_derived
from hydpy.models.ga import ga_inputs
from hydpy.models.ga import ga_fluxes
from hydpy.models.ga import ga_states
from hydpy.models.ga import ga_logs
from hydpy.models.ga import ga_aides


class Calc_SurfaceWaterSupply_V1(modeltools.Method):
    r"""Take rainfall as the possible supply for infiltration through the soil's
    surface.

    Basic equation:
      :math:`SurfaceWaterSupply = Rainfall`

    Example:

        >>> from hydpy.models.ga import *
        >>> parameterstep()
        >>> nmbsoils(2)
        >>> inputs.rainfall = 2.0
        >>> model.calc_surfacewatersupply_v1()
        >>> fluxes.surfacewatersupply
        surfacewatersupply(2.0, 2.0)
    """

    CONTROLPARAMETERS = (ga_control.NmbSoils,)
    REQUIREDSEQUENCES = (ga_inputs.Rainfall,)
    RESULTSEQUENCES = (ga_fluxes.SurfaceWaterSupply,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess

        for s in range(con.nmbsoils):
            flu.surfacewatersupply[s] = inp.rainfall


class Calc_SoilWaterSupply_V1(modeltools.Method):
    r"""Take capillary rise as the possible supply for water additions through the
    soil's bottom.

    Basic equation:
      :math:`SoilWaterSupply = CapillaryRise`

    Example:

        >>> from hydpy.models.ga import *
        >>> parameterstep()
        >>> nmbsoils(2)
        >>> inputs.capillaryrise = 2.0
        >>> model.calc_soilwatersupply_v1()
        >>> fluxes.soilwatersupply
        soilwatersupply(2.0, 2.0)
    """

    CONTROLPARAMETERS = (ga_control.NmbSoils,)
    REQUIREDSEQUENCES = (ga_inputs.CapillaryRise,)
    RESULTSEQUENCES = (ga_fluxes.SoilWaterSupply,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess

        for s in range(con.nmbsoils):
            flu.soilwatersupply[s] = inp.capillaryrise


class Calc_Demand_V1(modeltools.Method):
    r"""Take evaporation as the demand for extracting water from the soil's surface and
     body.

    Basic equation:
      :math:`Demand = Evaporation`

    Example:

        >>> from hydpy.models.ga import *
        >>> parameterstep()
        >>> nmbsoils(2)
        >>> inputs.evaporation = 2.0
        >>> model.calc_demand_v1()
        >>> fluxes.demand
        demand(2.0, 2.0)
    """

    CONTROLPARAMETERS = (ga_control.NmbSoils,)
    REQUIREDSEQUENCES = (ga_inputs.Evaporation,)
    RESULTSEQUENCES = (ga_fluxes.Demand,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess

        for s in range(con.nmbsoils):
            flu.demand[s] = inp.evaporation


class Return_RelativeMoisture_V1(modeltools.Method):
    r"""Calculate and return the relative soil water content for the given bin-soil
    combination.

    Basic equation (:cite:t:`ref-Lai2015`, equation 11):
      :math:`RelativeMoisture =
      \frac{FrontMoisture - ResidualMoisture}{SaturationMoisture - ResidualMoisture}`

    Method |Return_RelativeMoisture_V1| prevents returning values smaller than zero or
    larger than one that might arise due to violations of the residualor saturation
    water content.

    Examples:

        >>> from hydpy.models.ga import *
        >>> simulationstep("1h")
        >>> parameterstep("1h")
        >>> nmbsoils(2)
        >>> nmbbins(5)
        >>> residualmoisture(0.1, 0.2)
        >>> saturationmoisture(0.5, 0.8)
        >>> states.moisture = [[0.0, 0.0],
        ...                    [0.1, 0.2],
        ...                    [0.3, 0.65],
        ...                    [0.5, 0.8],
        ...                    [1.0, 1.0]]
        >>> from hydpy import round_
        >>> for soil in range(2):
        ...     for bin_ in range(5):
        ...         print(f"soil: {soil}, bin: {bin_} -> relativemoisture ", end="")
        ...         round_(model.return_relativemoisture_v1(bin_, soil))
        soil: 0, bin: 0 -> relativemoisture 0.0
        soil: 0, bin: 1 -> relativemoisture 0.0
        soil: 0, bin: 2 -> relativemoisture 0.5
        soil: 0, bin: 3 -> relativemoisture 1.0
        soil: 0, bin: 4 -> relativemoisture 1.0
        soil: 1, bin: 0 -> relativemoisture 0.0
        soil: 1, bin: 1 -> relativemoisture 0.0
        soil: 1, bin: 2 -> relativemoisture 0.75
        soil: 1, bin: 3 -> relativemoisture 1.0
        soil: 1, bin: 4 -> relativemoisture 1.0
    """

    CONTROLPARAMETERS = (
        ga_control.ResidualMoisture,
        ga_control.SaturationMoisture,
    )
    REQUIREDSEQUENCES = (ga_states.Moisture,)

    @staticmethod
    def __call__(model: modeltools.Model, b: int, s: int) -> float:
        con = model.parameters.control.fastaccess
        sta = model.sequences.states.fastaccess

        moisture: float = min(sta.moisture[b, s], con.saturationmoisture[s])
        moisture = max(moisture, con.residualmoisture[s])
        return (moisture - con.residualmoisture[s]) / (
            con.saturationmoisture[s] - con.residualmoisture[s]
        )


class Return_Conductivity_V1(modeltools.Method):
    r"""Based on the Brooks-Corey soil moisture characteristic model
    :cite:p:`ref-Brooks1966`, calculate and return the conductivity for the given
    bin-soil combination.

    Basic equation (:cite:t:`ref-Lai2015`, equation 11):
      :math:`Conductivity = SaturatedConductivity \cdot
      RelativeMoisture^{3 + 2 / PoreSizeDistribution}`

    Examples:

        >>> from hydpy.models.ga import *
        >>> simulationstep("1h")
        >>> parameterstep("1h")
        >>> nmbsoils(2)
        >>> nmbbins(3)
        >>> residualmoisture(0.1, 0.2)
        >>> saturationmoisture(0.5, 0.8)
        >>> poresizedistribution(0.3, 0.4)
        >>> saturatedconductivity(10.0, 20.0)
        >>> states.moisture = [[0.1, 0.0],
        ...                    [0.3, 0.5],
        ...                    [0.5, 1.0]]
        >>> from hydpy import round_
        >>> for soil in range(2):
        ...     for bin_ in range(3):
        ...         print(f"soil: {soil}, bin: {bin_} -> conductivity ", end="")
        ...         round_(model.return_conductivity_v1(bin_, soil))
        soil: 0, bin: 0 -> conductivity 0.0
        soil: 0, bin: 1 -> conductivity 0.012304
        soil: 0, bin: 2 -> conductivity 10.0
        soil: 1, bin: 0 -> conductivity 0.0
        soil: 1, bin: 1 -> conductivity 0.078125
        soil: 1, bin: 2 -> conductivity 20.0
    """

    SUBMETHODS = (Return_RelativeMoisture_V1,)
    CONTROLPARAMETERS = (
        ga_control.ResidualMoisture,
        ga_control.SaturationMoisture,
        ga_control.SaturatedConductivity,
        ga_control.PoreSizeDistribution,
    )
    REQUIREDSEQUENCES = (ga_states.Moisture,)

    @staticmethod
    def __call__(model: modeltools.Model, b: int, s: int) -> float:
        con = model.parameters.control.fastaccess

        return con.saturatedconductivity[s] * (
            model.return_relativemoisture_v1(b, s)
            ** (3.0 + 2.0 / con.poresizedistribution[s])
        )


class Return_CapillaryDrive_V1(modeltools.Method):
    r"""Based on the Brooks-Corey soil moisture characteristic model
    :cite:p:`ref-Brooks1966`, calculate and return the capillary drive between the
    water contents of the given bins for the defined soil.

    Basic equation (:cite:t:`ref-Lai2015`, equation 11):
      :math:`CapillaryDrive_{bin1,bin2} =
      \frac{AirEntryPotential}{3 \cdot PoreSizeDistribution + 1} \cdot
      \begin{cases}
      RelativeMoisture_{bin2}^{3 + 1 / PoreSizeDistribution} -
      RelativeMoisture_{bin1}^{3 + 1 / PoreSizeDistribution}
      &|\ Moisture_{bin2} < SaturationMoisture
      \\
      3 \cdot PoreSizeDistribution + 2 -
      RelativeMoisture_{bin1}^{3 + 1 / PoreSizeDistribution}
      &|\ Moisture_{bin2} = SaturationMoisture
      \end{cases}`

    Examples:

        >>> from hydpy.models.ga import *
        >>> simulationstep("1h")
        >>> parameterstep("1h")
        >>> nmbsoils(2)
        >>> nmbbins(3)
        >>> residualmoisture(0.1, 0.2)
        >>> saturationmoisture(0.5, 0.8)
        >>> airentrypotential(0.1, 0.2)
        >>> poresizedistribution(0.3, 0.4)
        >>> saturatedconductivity(10.0, 20.0)
        >>> states.moisture = [[0.1, 0.0],
        ...                    [0.3, 0.5],
        ...                    [0.5, 1.0]]
        >>> from hydpy import round_
        >>> for soil in range(2):
        ...     for bin_ in range(2):
        ...         print(f"soil: {soil}, bin: {bin_} -> capillarydrive ", end="")
        ...         round_(model.return_capillarydrive_v1(bin_, bin_ + 1, soil))
        soil: 0, bin: 0 -> capillarydrive 0.000653
        soil: 0, bin: 1 -> capillarydrive 0.151979
        soil: 1, bin: 0 -> capillarydrive 0.002009
        soil: 1, bin: 1 -> capillarydrive 0.2889
    """

    SUBMETHODS = (Return_RelativeMoisture_V1,)
    CONTROLPARAMETERS = (
        ga_control.ResidualMoisture,
        ga_control.SaturationMoisture,
        ga_control.AirEntryPotential,
        ga_control.PoreSizeDistribution,
    )
    REQUIREDSEQUENCES = (ga_states.Moisture,)

    @staticmethod
    def __call__(model: modeltools.Model, b1: int, b2: int, s: int) -> float:
        con = model.parameters.control.fastaccess
        sta = model.sequences.states.fastaccess

        exp: float = 1.0 / con.poresizedistribution[s] + 3.0
        if sta.moisture[b2, s] < con.saturationmoisture[s]:
            subtrahend: float = model.return_relativemoisture_v1(b2, s) ** exp
        else:
            subtrahend = 3.0 * con.poresizedistribution[s] + 2.0
        return (
            con.airentrypotential[s]
            * (subtrahend - model.return_relativemoisture_v1(b1, s) ** exp)
            / (3.0 * con.poresizedistribution[s] + 1.0)
        )


class Percolate_FilledBin_V1(modeltools.Method):
    r"""Calculate the percolation of water through the filled first bin due to
    gravitational forcing.

    Basic equation:
      :math:`Percolation = DT \cdot Conductivity`

    Example:

        For simplicity, we make each soil compartment's first (and only) bin saturated
        so that actual conductivity equals saturated conductivity:

        >>> from hydpy.models.ga import *
        >>> simulationstep("1h")
        >>> parameterstep("1h")
        >>> nmbsoils(3)
        >>> nmbbins(2)
        >>> dt(0.5)
        >>> soildepth(100.0, 200.0, 300.0)
        >>> residualmoisture(0.1)
        >>> saturationmoisture(0.5)
        >>> poresizedistribution(0.3)
        >>> saturatedconductivity(6.0, 8.0, 10.0)
        >>> states.moisture = 0.5
        >>> aides.actualsurfacewater = 2.0, 4.0, 6.0
        >>> fluxes.percolation = 1.0
        >>> for soil in range(3):
        ...     model.percolate_filledbin_v1(soil)
        >>> aides.actualsurfacewater
        actualsurfacewater(0.0, 0.0, 1.0)
        >>> fluxes.percolation
        percolation(3.0, 5.0, 6.0)

        By the way, |Percolate_FilledBin_V1| sets the first bin's front depth to the
        respective soil compartment's depth:

        >>> states.frontdepth
        frontdepth([[100.0, 200.0, 300.0],
                    [nan, nan, nan]])
    """

    SUBMETHODS = (
        Return_RelativeMoisture_V1,
        Return_Conductivity_V1,
    )
    CONTROLPARAMETERS = (
        ga_control.DT,
        ga_control.SoilDepth,
        ga_control.ResidualMoisture,
        ga_control.SaturationMoisture,
        ga_control.SaturatedConductivity,
        ga_control.PoreSizeDistribution,
    )
    REQUIREDSEQUENCES = (ga_states.Moisture,)
    UPDATEDSEQUENCES = (
        ga_states.FrontDepth,
        ga_aides.ActualSurfaceWater,
        ga_fluxes.Percolation,
    )

    @staticmethod
    def __call__(model: modeltools.Model, s: int) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess

        sta.frontdepth[0, s] = con.soildepth[s]
        potinfiltration: float = con.dt * model.return_conductivity_v1(0, s)
        if potinfiltration < aid.actualsurfacewater[s]:
            aid.actualsurfacewater[s] -= potinfiltration
            flu.percolation[s] += potinfiltration
        else:
            flu.percolation[s] += aid.actualsurfacewater[s]
            aid.actualsurfacewater[s] = 0.0


class Return_DryDepth_V1(modeltools.Method):
    r"""Calculate and return the "dry depth".

    Basic equations (:cite:t:`ref-Lai2015`, equation 7, modified, see `issue 89`_):
      :math:`
      \frac{\tau + \sqrt{\tau^2 + 4 \cdot \tau \cdot EffectiveCapillarySuction}}{2}`

      :math:`
      \tau = DT \cdot \frac{SaturatedConductivity}{SaturationMoisture - FrontMoisture}`

    Example:

        >>> from hydpy.models.ga import *
        >>> simulationstep("1h")
        >>> parameterstep("1h")
        >>> nmbsoils(3)
        >>> nmbbins(2)
        >>> dt(0.5)
        >>> residualmoisture(0.1, 0.2, 0.2)
        >>> saturationmoisture(0.5, 0.8, 0.8)
        >>> poresizedistribution(0.3, 0.4, 0.4)
        >>> saturatedconductivity(10.0, 20.0, 20.0)
        >>> airentrypotential(0.1, 0.2, 0.2)
        >>> derived.effectivecapillarysuction.update()
        >>> states.moisture = [[0.3, 0.5, 0.8], [nan, nan, nan]]
        >>> from hydpy import round_
        >>> for soil in range(3):
        ...     round_(model.return_drydepth_v1(soil))
        25.151711
        33.621747
        inf
    """

    CONTROLPARAMETERS = (
        ga_control.DT,
        ga_control.SaturationMoisture,
        ga_control.SaturatedConductivity,
    )
    DERIVEDPARAMETERS = (ga_derived.EffectiveCapillarySuction,)
    REQUIREDSEQUENCES = (ga_states.Moisture,)

    @staticmethod
    def __call__(model: modeltools.Model, s: int) -> float:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        sta = model.sequences.states.fastaccess

        if sta.moisture[0, s] < con.saturationmoisture[s]:
            tau: float = (
                con.dt
                * con.saturatedconductivity[s]
                / (con.saturationmoisture[s] - sta.moisture[0, s])
            )
            return 0.5 * (
                tau + (tau**2 + 4.0 * tau * der.effectivecapillarysuction[s]) ** 0.5
            )
        return modelutils.inf


class Return_LastActiveBin_V1(modeltools.Method):
    r"""Find the index of the last active bin (that either contains a wetting front or
    uniform moisture over the complete soil depth).

    Example:

        >>> from hydpy.models.ga import *
        >>> simulationstep("1h")
        >>> parameterstep("1h")
        >>> nmbsoils(3)
        >>> nmbbins(3)
        >>> states.moisture = [[0.1, 0.1, 0.1],
        ...                    [0.1, 0.5, 0.5],
        ...                    [0.1, 1.0, 0.1]]
        >>> for soil in range(3):
        ...     print(f"soil: {soil} -> bin: {model.return_lastactivebin_v1(soil)}")
        soil: 0 -> bin: 0
        soil: 1 -> bin: 2
        soil: 2 -> bin: 1
    """

    CONTROLPARAMETERS = (ga_control.NmbBins,)
    REQUIREDSEQUENCES = (ga_states.Moisture,)

    @staticmethod
    def __call__(model: modeltools.Model, s: int) -> int:
        con = model.parameters.control.fastaccess
        sta = model.sequences.states.fastaccess

        for b in range(con.nmbbins - 1, 0, -1):
            if sta.moisture[b, s] > sta.moisture[0, s]:
                return b
        return 0


class Active_Bin_V1(modeltools.Method):
    r"""Activate a bin to the right of the bin with the given index.

    We need to activate another bin if the current last bin's moisture decreases and
    rainfall intensity exceeds saturated conductivity.

    Basic equations (related to :cite:t:`ref-Lai2015`):
      :math:`MoistureChange_{bin+1} =
      \frac{ActualSurfaceWater - DT \cdot 2 \cdot Conductivity_{bin}}{DryDepth}`

      :math:`Moisture_{bin+1} = Moisture_{bin} + MoistureChange_{bin+1}`

      :math:`Infiltration_{bin+1} = DT \cdot SaturatedConductivity \cdot
      \left( \frac{EffectiveCapillarySuction}{DryDepth} + 1 \right)`

      :math:`FrontDepth_{bin+1} = \frac{Infiltration_{bin+1}}{MoistureChange_{bin+1}}`

    The calculation of infiltration and the new front depth follows equation 4 of
    :cite:t:`ref-Lai2015`, except for using :math:`Moisture_{bin}` instead of
    :math:`ResidualMoisture` and :math:`Moisture_{bin+1}` instead of
    :math:`SaturationMoisture`.  Regarding the moisture change, :cite:t:`ref-Lai2015`
    does not seem to mention the given basic equation explicitly.

    Examples:

        Method |Active_Bin_V1| is a little complicated, so we perform multiple test
        calculations considering different special cases.  We use the following setting
        for all these test calculations.

        >>> from hydpy.models.ga_garto import *
        >>> simulationstep("1h")
        >>> parameterstep("1h")
        >>> nmbsoils(1)
        >>> nmbbins(3)
        >>> dt(0.25)
        >>> sealed(False)
        >>> soilarea(1.0)
        >>> soildepth(1000.0)
        >>> residualmoisture(0.1)
        >>> saturationmoisture(0.5)
        >>> airentrypotential(0.1)
        >>> poresizedistribution(0.3)
        >>> saturatedconductivity(10.0)
        >>> derived.soilareafraction.update()
        >>> derived.effectivecapillarysuction.update()

        We define a test function that applies |Active_Bin_V1| for a definable initial
        surface water depth.  The function checks that the water volume remains
        unchanged, prints the moisture change, the resulting moisture state, and the
        depth of the new active front (as calculated by |Active_Bin_V1|), and
        additionally prints the related infiltration (which |Active_Bin_V1| does not
        calculate on its own):

        >>> from hydpy.core.objecttools import repr_, repr_values
        >>> def check(actualsurfacewater):
        ...     states.moisture = [[0.1], [0.3], [0.1]]
        ...     states.frontdepth = [[1000.0], [500.0], [0.0]]
        ...     logs.moisturechange = [[nan], [-inf], [nan]]
        ...     aides.actualsurfacewater = actualsurfacewater
        ...     old_volume = round(model.watercontent + aides.actualsurfacewater[0], 12)
        ...     model.active_bin_v1(1, 0)
        ...     new_volume = round(model.watercontent + aides.actualsurfacewater[0], 12)
        ...     assert old_volume == new_volume
        ...     infiltration = actualsurfacewater - aides.actualsurfacewater[0]
        ...     print(f"moisturechange: {repr_values(logs.moisturechange[:, 0])}")
        ...     print(f"moisture: {repr_values(states.moisture[:, 0])}")
        ...     print(f"infiltration: {repr_(infiltration)}")
        ...     print(f"frontdepth: {repr_values(states.frontdepth[:, 0])}")

        The first example deals with a moderate rainfall intensity (a relatively small
        surface water depth), where everything works as described by the basic
        equations defined above:

        >>> check(actualsurfacewater=1.0)
        moisturechange: nan, -inf, 0.155311
        moisture: 0.1, 0.3, 0.455311
        infiltration: 1.0
        frontdepth: 1000.0, 500.0, 6.438686

        For high rainfall intensities, the calculated moisture change could result in
        the actual moisture exceeding the saturation moisture.  In such cases,
        |Active_Bin_V1| corrects the moisture but leaves the moisture change as is:

        ToDo: clip the moisture change?

        >>> check(actualsurfacewater=5.0)
        moisturechange: nan, -inf, 0.780401
        moisture: 0.1, 0.3, 0.5
        infiltration: 2.55963
        frontdepth: 1000.0, 500.0, 12.798152

        A particularity of method |Active_Bin_V1| is to set the moisture change to its
        highest possible value if the original moisture change (following the basic
        equation) is negative.  Such situations can arise when the pre-existing active
        fronts have already infiltrated a significant amount of the rainfall available
        for the given numerical timestep:

        ToDo: set the moisture change to zero?

        >>> check(actualsurfacewater=0.001)
        moisturechange: nan, -inf, 0.2
        moisture: 0.1, 0.3, 0.5
        infiltration: 0.001
        frontdepth: 1000.0, 500.0, 0.005


        Even for zero remaining surface water, |Active_Bin_V1| activates a bin and sets
        its moisture value to the saturation value (without calculating any
        infiltration):

        >>> check(actualsurfacewater=0.0)
        moisturechange: nan, -inf, 0.2
        moisture: 0.1, 0.3, 0.5
        infiltration: 0.0
        frontdepth: 1000.0, 500.0, 0.0

        A very special case is when the initially calculated moisture change (following
        the basic equation) is zero.  Only then, |Active_Bin_V1| refrains from
        activating another bin:

        |Active_Bin_V1| checks if the initially calculated moisture change (following
        the basic equation) is zero.  Only then does it refrain from activating another
        bin:

        >>> actualsurfacewater=control.dt * 2.0 * model.return_conductivity_v1(1, 0)
        >>> check(actualsurfacewater=actualsurfacewater)
        moisturechange: nan, -inf, 0.0
        moisture: 0.1, 0.3, 0.1
        infiltration: 0.0
        frontdepth: 1000.0, 500.0, 0.0

        The following two examples illustrate highly deviating ways of front activation
        around the "zero moisture change" case (the second example also shows that
        infiltration becomes restricted when the front depth would otherwise overshoot
        the soil depth):

        >>> check(actualsurfacewater=actualsurfacewater-1e-5)
        moisturechange: nan, -inf, 0.2
        moisture: 0.1, 0.3, 0.5
        infiltration: 0.006142
        frontdepth: 1000.0, 500.0, 0.03071

        >>> check(actualsurfacewater=actualsurfacewater+1e-5)
        moisturechange: nan, -inf, 0.000002
        moisture: 0.1, 0.3, 0.300002
        infiltration: 0.001563
        frontdepth: 1000.0, 500.0, 1000.0
    """

    CONTROLPARAMETERS = (
        ga_control.DT,
        ga_control.SoilDepth,
        ga_control.SaturationMoisture,
        ga_control.SaturatedConductivity,
    )
    DERIVEDPARAMETERS = (ga_derived.EffectiveCapillarySuction,)
    UPDATEDSEQUENCES = (
        ga_states.Moisture,
        ga_states.FrontDepth,
        ga_logs.MoistureChange,
        ga_aides.ActualSurfaceWater,
    )

    @staticmethod
    def __call__(model: modeltools.Model, b: int, s: int) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        sta = model.sequences.states.fastaccess
        log = model.sequences.logs.fastaccess
        aid = model.sequences.aides.fastaccess

        drydepth: float = model.return_drydepth_v1(s)
        conductivity: float = model.return_conductivity_v1(b, s)
        log.moisturechange[b + 1, s] = (
            aid.actualsurfacewater[s] - con.dt * 2.0 * conductivity
        ) / drydepth
        if log.moisturechange[b + 1, s] < 0.0:
            log.moisturechange[b + 1, s] = (
                con.saturationmoisture[s] - sta.moisture[b, s]
            )
        if log.moisturechange[b + 1, s] > 0.0:
            sta.moisture[b + 1, s] = min(
                sta.moisture[b, s] + log.moisturechange[b + 1, s],
                con.saturationmoisture[s],
            )
            deltamoisture: float = sta.moisture[b + 1, s] - sta.moisture[b, s]
            potinfiltration: float = min(
                con.dt
                * con.saturatedconductivity[s]
                * (der.effectivecapillarysuction[s] / drydepth + 1.0),
                con.soildepth[s] * deltamoisture,
            )
            if aid.actualsurfacewater[s] > potinfiltration:
                sta.frontdepth[b + 1, s] = potinfiltration / deltamoisture
                aid.actualsurfacewater[s] -= potinfiltration
            else:
                sta.frontdepth[b + 1, s] = aid.actualsurfacewater[s] / deltamoisture
                aid.actualsurfacewater[s] = 0.0


class Shift_Front_V1(modeltools.Method):
    r"""Increase the selected bin's wetting front depth without modifying its relative
    moisture following a variation of the Talbot-Ogden equation
    :cite:p:`ref-Talbot2008`.

    Method |Shift_Front_V1| applies for active wetting front bins that are not the last
    active bin or that are saturated (|Moisture| equals |SaturationMoisture|).  The
    latter holds only for periods with rainfall intensity exceeding saturated
    conductivity.

    Basic equation (:cite:t:`ref-Lai2015`, equation 8, modified):
      :math:`FrontDepth_{bin, new} = FrontDepth_{bin, old} + DT \cdot
      \frac{Conductivity_{bin-1} - Conductivity_{bin}}
      {Moisture_{bin} - Moisture_{bin-1}} \cdot \left(1 +
      \frac{CapillaryDrive_{0, LastActiveBin} + InitialSurfaceWater}{FrontDepth_{bin}}
      \right)`

    Note the used equation deviates from equation 8 of :cite:t:`ref-Lai2015` in adding
    the initial surface water depth to the effective capillary drive, which increases
    infiltration.  Using |InitialSurfaceWater| instead of |ActualSurfaceWater| assures
    the bin processing order does not affect the individual infiltration rates.

    Examples:

        For comparison, we perform the following examples similar to those of method
        |Active_Bin_V1|.  The general setting is identical, except that we initialise
        one more bin:

        >>> from hydpy.models.ga_garto import *
        >>> simulationstep("1h")
        >>> parameterstep("1h")
        >>> nmbsoils(1)
        >>> nmbbins(4)
        >>> dt(0.25)
        >>> sealed(False)
        >>> soilarea(1.0)
        >>> soildepth(1000.0)
        >>> residualmoisture(0.1)
        >>> saturationmoisture(0.5)
        >>> airentrypotential(0.1)
        >>> poresizedistribution(0.3)
        >>> saturatedconductivity(10.0)
        >>> derived.soilareafraction.update()
        >>> derived.effectivecapillarysuction.update()

        The test function also behaves similarly but allows for more modifications
        of the initial states, supports selecting the considered bin, and applies
        |Shift_Front_V1| instead of |Active_Bin_V1|:

        >>> from hydpy.core.objecttools import repr_, repr_values
        >>> def check(
        ...         bin_, initialsurfacewater, actualsurfacewater, frontdepth, moisture
        ...     ):
        ...     states.moisture = [[m] for m in moisture]
        ...     states.frontdepth = [[fd] for fd in frontdepth]
        ...     logs.moisturechange = nan
        ...     aides.initialsurfacewater = initialsurfacewater
        ...     aides.actualsurfacewater = actualsurfacewater
        ...     old_volume = round(model.watercontent + aides.actualsurfacewater[0], 12)
        ...     model.shift_front_v1(bin_, 0)
        ...     new_volume = round(model.watercontent + aides.actualsurfacewater[0], 12)
        ...     assert old_volume == new_volume
        ...     infiltration = actualsurfacewater - aides.actualsurfacewater[0]
        ...     print(f"moisturechange: {repr_values(logs.moisturechange[:, 0])}")
        ...     print(f"moisture: {repr_values(states.moisture[:, 0])}")
        ...     print(f"infiltration: {repr_(infiltration)}")
        ...     print(f"frontdepth: {repr_values(states.frontdepth[:, 0])}")

        |Shift_Front_V1| is to be applied on non-last active wetting front bins and the
        last bin if it is saturated. We start with demonstrating its functionality for
        the latter case.

        The first example is standard so far that the given basic equation applies
        without additional restrictions and initial and actual surface water depths are
        identical.  2.75 mm of the available surface water infiltrate and shift the
        wetting front by about 13.75 mm:

        >>> check(bin_=2, initialsurfacewater=10.0, actualsurfacewater=10.0,
        ...       frontdepth=[1000.0, 500.0, 100.0, 0.0],
        ...       moisture=[0.1, 0.3, 0.5, 0.1])
        moisturechange: nan, nan, nan, nan
        moisture: 0.1, 0.3, 0.5, 0.1
        infiltration: 2.750428
        frontdepth: 1000.0, 500.0, 113.752138, 0.0

        Next, we decrease the amount of available surface water to 1 mm but let the
        initial surface water depth at 10 mm.  Thus, the potential infiltration stays
        as is, but the actual infiltration reduces to 1 mm (and the front shift to
        5 mm):

        >>> check(bin_=2, initialsurfacewater=10.0, actualsurfacewater=1.0,
        ...       frontdepth=[1000.0, 500.0, 100.0, 0.0],
        ...       moisture=[0.1, 0.3, 0.5, 0.1])
        moisturechange: nan, nan, nan, nan
        moisture: 0.1, 0.3, 0.5, 0.1
        infiltration: 1.0
        frontdepth: 1000.0, 500.0, 105.0, 0.0

        For small or zero initial front depths, |Shift_Front_V1| uses the method
        |Return_DryDepth_V1| to advance the front instead of the basic equation:

        >>> from hydpy import round_
        >>> round_(model.return_drydepth_v1(0))
        6.399076
        >>> check(bin_=2, initialsurfacewater=10.0, actualsurfacewater=10.0,
        ...       frontdepth=[1000.0, 500.0, 0.0, 0.0],
        ...       moisture=[0.1, 0.3, 0.5, 0.1])
        moisturechange: nan, nan, nan, nan
        moisture: 0.1, 0.3, 0.5, 0.1
        infiltration: 1.279815
        frontdepth: 1000.0, 500.0, 6.399076, 0.0

        |Shift_Front_V1| prevents a wetting front from overshooting the soil depth but
        not the depth of other fronts:

        >>> check(bin_=2, initialsurfacewater=10.0, actualsurfacewater=10.0,
        ...       frontdepth=[1000.0, 999.0, 998.0, 0.0],
        ...       moisture=[0.1, 0.3, 0.5, 0.1])
        moisturechange: nan, nan, nan, nan
        moisture: 0.1, 0.3, 0.5, 0.1
        infiltration: 0.4
        frontdepth: 1000.0, 999.0, 1000.0, 0.0

        In principle, |Shift_Front_V1| works for the active, non-last bins as described
        above:

        >>> check(bin_=1, initialsurfacewater=10.0, actualsurfacewater=1.0,
        ...       frontdepth=[1000.0, 300.0, 200.0, 100.0],
        ...       moisture=[0.2, 0.3, 0.4, 0.5])
        moisturechange: nan, nan, nan, nan
        moisture: 0.2, 0.3, 0.4, 0.5
        infiltration: 0.003176
        frontdepth: 1000.0, 300.031762, 200.0, 100.0

        However, for these bins, it also applies to rain-free periods.  Then, its front
        shifts as usual while keeping its relative moisture.  As the considered bin
        cannot (completely) take the corrensponding absolute moisture decrease from the
        surface, it takes water from the last active bin instead, decreasing its depth
        but not its relative moisture:

        >>> check(bin_=1, initialsurfacewater=0.0, actualsurfacewater=0.0,
        ...       frontdepth=[1000.0, 300.0, 200.0, 100.0],
        ...       moisture=[0.2, 0.3, 0.4, 0.5])
        moisturechange: nan, nan, nan, nan
        moisture: 0.2, 0.3, 0.4, 0.5
        infiltration: 0.0
        frontdepth: 1000.0, 300.030738, 200.0, 99.969262

        If the last active bin does not contain enough water, the second-last bin must
        help out:

        >>> check(bin_=1, initialsurfacewater=0.0, actualsurfacewater=0.0,
        ...       frontdepth=[1000.0, 300.0, 200.0, 0.01],
        ...       moisture=[0.2, 0.3, 0.4, 0.5])
        moisturechange: nan, nan, nan, 0.0
        moisture: 0.2, 0.3, 0.4, 0.2
        infiltration: 0.0
        frontdepth: 1000.0, 300.030738, 199.979262, 0.0

        If all bins that possess higher relative moisture than the considered bin do
        not contain enough water, the shift of the wetting front becomes restricted:

        >>> check(bin_=1, initialsurfacewater=0.0, actualsurfacewater=0.0,
        ...       frontdepth=[1000.0, 300.0, 0.02, 0.01],
        ...       moisture=[0.2, 0.3, 0.4, 0.5])
        moisturechange: nan, nan, 0.0, 0.0
        moisture: 0.2, 0.3, 0.2, 0.2
        infiltration: 0.0
        frontdepth: 1000.0, 300.03, 0.0, 0.0

        All examples above show that |Shift_Front_V1| never modifies |MoistureChange|,
        except when deactivating a bin.  Then, it sets the moisture change to zero.
    """

    SUBMETHODS = (
        Return_RelativeMoisture_V1,
        Return_LastActiveBin_V1,
        Return_DryDepth_V1,
        Return_Conductivity_V1,
        Return_CapillaryDrive_V1,
    )
    CONTROLPARAMETERS = (
        ga_control.DT,
        ga_control.NmbBins,
        ga_control.SoilDepth,
        ga_control.ResidualMoisture,
        ga_control.SaturationMoisture,
        ga_control.SaturatedConductivity,
        ga_control.AirEntryPotential,
        ga_control.PoreSizeDistribution,
    )
    DERIVEDPARAMETERS = (ga_derived.EffectiveCapillarySuction,)
    REQUIREDSEQUENCES = (ga_aides.InitialSurfaceWater,)
    UPDATEDSEQUENCES = (
        ga_states.Moisture,
        ga_states.FrontDepth,
        ga_logs.MoistureChange,
        ga_aides.ActualSurfaceWater,
    )

    @staticmethod
    def __call__(model: modeltools.Model, b: int, s: int) -> None:
        con = model.parameters.control.fastaccess
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess
        log = model.sequences.logs.fastaccess

        b_last = model.return_lastactivebin_v1(s)
        drydepth: float = model.return_drydepth_v1(s)
        if sta.frontdepth[b, s] < drydepth:
            frontshift: float = drydepth
        else:
            cond1: float = model.return_conductivity_v1(b - 1, s)
            cond2: float = model.return_conductivity_v1(b, s)
            drive: float = model.return_capillarydrive_v1(0, b_last, s)
            frontshift = (
                con.dt * (cond2 - cond1) / (sta.moisture[b, s] - sta.moisture[b - 1, s])
            ) * (1.0 + (drive + aid.initialsurfacewater[s]) / sta.frontdepth[b, s])
        frontshift = min(frontshift, con.soildepth[s] - sta.frontdepth[b, s])

        deltamoisture_b: float = sta.moisture[b, s] - sta.moisture[b - 1, s]
        required: float = frontshift * deltamoisture_b
        if required < aid.actualsurfacewater[s]:
            sta.frontdepth[b, s] += frontshift
            aid.actualsurfacewater[s] -= required
        else:
            required -= aid.actualsurfacewater[s]
            sta.frontdepth[b, s] += aid.actualsurfacewater[s] / deltamoisture_b
            aid.actualsurfacewater[s] = 0.0
            for b_last in range(b_last, b, -1):
                deltamoisture_bb: float = (
                    sta.moisture[b_last, s] - sta.moisture[b_last - 1, s]
                )
                available: float = deltamoisture_bb * sta.frontdepth[b_last, s]
                if available < required:
                    required -= available
                    sta.frontdepth[b, s] += available / deltamoisture_b
                    sta.frontdepth[b_last, s] = 0.0
                    sta.moisture[b_last, s] = sta.moisture[0, s]
                    log.moisturechange[b_last, s] = 0.0
                else:
                    sta.frontdepth[b_last, s] -= required / deltamoisture_bb
                    sta.frontdepth[b, s] += required / deltamoisture_b
                    break


class Redistribute_Front_V1(modeltools.Method):
    r"""Modify the selected bin's wetting front depth and relative moisture content
    based on a Green & Ampt redistribution equation.

    |Redistribute_Front_V1| applies for the last active wetting front bin when rainfall
    intensity does not exceed saturated conductivity.

    Basic equations (:cite:t:`ref-Lai2015`, equation 6)
      :math:`p = \cases{1.7 &| ActualSurfaceWater = 0 \\ 1.0 &| ActualSurfaceWater > 0}`

      :math:`MoistureChange_{bin} = \frac{1}{FrontDepth_{bin}} \cdot
      \left( ActualSurfaceWater - DT \cdot \left( Conductivity_{bin} -
      \frac{p \cdot SaturatedConductivity \cdot CapillaryDrive_{bin-1,bin}}
      {FrontDepth_{bin}} \right) \right)`

      :math:`Moisture_{bin,old} = Moisture_{bin,new} + MoistureChange_{bin}`

      :math:`Infiltration_{bin} = DT \cdot SaturatedConductivity \cdot
      \left( 1 + \frac{EffectiveCapillarySuction}{FrontDepth_{bin}} \right)`

      :math:`FrontDepth_{bin,new} = \frac{Infiltration_{bin} +
      FrontDepth_{bin,old} \cdot (Moisture_{bin,old} - Moisture_{bin-1})}
      {Moisture_{bin,new} - Moisture_{bin-1}}`

    :cite:t:`ref-Lai2015` define only the calculation of the moisture change
    explicitly.  The infiltration calculation and the corresponding shift of the
    wetting front depth rest on the GARTO source code provided by the authors.  One
    might have expected to use :math:`Conductivity_{bin}` and
    :math:`CapillaryDrive_{bin-1,bin}` instead of :math:`SaturatedConductivity` and
    :math:`EffectiveCapillarySuction`.  There is a remark of the authors (possibly
    concerning the :math:`CapillaryDrive_{bin-1,bin}` vs
    :math:`EffectiveCapillarySuction` issue only) that oscillations in infiltration
    rates might show up otherwise.  Maybe we can discuss this with the authors or
    investigate ourselves in more detail later.

    If the bin's initial front depth is zero, the basic equations for calculating
    moisture change and infiltration become obsolete.  |Redistribute_Front_V1| then
    proceeds as follows:

      :math:`MoistureChange_{bin} =
      (ActualSurfaceWater - DT \cdot  Conductivity_{bin-1}) / DryDepth`

      :math:`Infiltration_{bin} = DT \cdot SaturatedConductivity \cdot
      \left( 1 + \frac{EffectiveCapillarySuction}{DryDepth} \right)`


    Examples:

        For comparison, we perform the following examples similar to those of method
        |Shift_Front_V1|.  The general setting is identical:

        >>> from hydpy.models.ga_garto import *
        >>> simulationstep("1h")
        >>> parameterstep("1h")
        >>> nmbsoils(1)
        >>> nmbbins(4)
        >>> dt(0.25)
        >>> sealed(False)
        >>> soilarea(1.0)
        >>> soildepth(1000.0)
        >>> residualmoisture(0.1)
        >>> saturationmoisture(0.5)
        >>> airentrypotential(0.1)
        >>> poresizedistribution(0.3)
        >>> saturatedconductivity(10.0)
        >>> derived.soilareafraction.update()
        >>> derived.effectivecapillarysuction.update()

        The test function behaves similarly.  However it neglects the initial surface
        water depth, which is not a relevant input to |Redistribute_Front_V1|, and
        considers percolation, which |Redistribute_Front_V1| might update when
        deactivating surface wetting fronts:

        >>> from hydpy.core.objecttools import repr_, repr_values
        >>> def check(bin_, actualsurfacewater, frontdepth, moisture):
        ...     states.moisture = [[m] for m in moisture]
        ...     states.frontdepth = [[fd] for fd in frontdepth]
        ...     logs.moisturechange = nan
        ...     aides.actualsurfacewater = actualsurfacewater
        ...     fluxes.percolation[0] = 0.0
        ...     old_volume = round(model.watercontent + aides.actualsurfacewater[0], 12)
        ...     model.redistribute_front_v1(bin_, 0)
        ...     new_volume = round(model.watercontent + aides.actualsurfacewater[0], 12)
        ...     assert old_volume == new_volume + fluxes.percolation[0]
        ...     infiltration = actualsurfacewater - aides.actualsurfacewater[0]
        ...     print(f"moisturechange: {repr_values(logs.moisturechange[:, 0])}")
        ...     print(f"moisture: {repr_values(states.moisture[:, 0])}")
        ...     print(f"infiltration: {repr_(infiltration)}")
        ...     print(f"percolation: {repr_(fluxes.percolation[0])}")
        ...     print(f"frontdepth: {repr_values(states.frontdepth[:, 0])}")

        In the first example, the given basic equations apply without modifications.
        Due to missing surface water, relative moisture decreases.  Consequently, the
        front's depth increases to keep the bin's total water volume:

        >>> check(bin_=2, actualsurfacewater=0.0,
        ...       frontdepth=[1000.0, 500.0, 100.0, 0.0],
        ...       moisture=[0.1, 0.3, 0.4, 0.1])
        moisturechange: nan, nan, -0.001553, nan
        moisture: 0.1, 0.3, 0.398447, 0.1
        infiltration: 0.0
        percolation: 0.0
        frontdepth: 1000.0, 500.0, 101.57736, 0.0

        With enough available surface water, the bin's relative soil moisture
        increases.  In the following example, this moisture increase outweighs the
        actual infiltration.  So the front depth must must decrease to keep the
        absolute water volume.

        >>> check(bin_=2, actualsurfacewater=5.0,
        ...       frontdepth=[1000.0, 500.0, 100.0, 0.0],
        ...       moisture=[0.1, 0.3, 0.4, 0.1])
        moisturechange: nan, nan, 0.048449, nan
        moisture: 0.1, 0.3, 0.448449, 0.1
        infiltration: 2.503816
        percolation: 0.0
        frontdepth: 1000.0, 500.0, 84.229985, 0.0

        For zero initial front depth, |Redistribute_Front_V1| prefers the alternative
        equations for calculating moisture change and infiltration defined above:

        >>> check(bin_=2, actualsurfacewater=0.5,
        ...       frontdepth=[1000.0, 500.0, 0.0, 0.0],
        ...       moisture=[0.1, 0.3, 0.4, 0.1])
        moisturechange: nan, nan, 0.077656, nan
        moisture: 0.1, 0.3, 0.477656, 0.1
        infiltration: 0.5
        percolation: 0.0
        frontdepth: 1000.0, 500.0, 2.814434, 0.0

        |Redistribute_Front_V1| ensures the updated moisture content does not exceed
        the saturation content, even if the calculated moisture change suggests so:

        ToDo: clip moisture change?

        >>> check(bin_=2, actualsurfacewater=20.0,
        ...       frontdepth=[1000.0, 500.0, 100.0, 0.0],
        ...       moisture=[0.1, 0.3, 0.4, 0.1])
        moisturechange: nan, nan, 0.198449, nan
        moisture: 0.1, 0.3, 0.5, 0.1
        infiltration: 2.503816
        percolation: 0.0
        frontdepth: 1000.0, 500.0, 62.519079, 0.0

        A moisture decrease that would result in falling below the moisture value of
        the left neighbour bin causes the deactivation of the affected bin.  If the
        left neighbour contains an active wetting front, |Redistribute_Front_V1| adds
        the remaining soil water and infiltration to this bin by increasing its front
        depth:

        ToDo: What if the front depth of the left neigbour bin exceeds soil depth
              afterwards?

        >>> check(bin_=2, actualsurfacewater=0.001,
        ...       frontdepth=[1000.0, 500.0, 100.0, 0.0],
        ...       moisture=[0.1, 0.3, 0.30001, 0.1])
        moisturechange: nan, nan, 0.0, nan
        moisture: 0.1, 0.3, 0.1, 0.1
        infiltration: 0.001
        percolation: 0.0
        frontdepth: 1000.0, 500.01, 0.0, 0.0

        If the left neighbour is the first, completely "filled" bin, the remaining soil
        water and infiltration increase its moisture content:

        >>> soildepth(500.0)
        >>> check(bin_=1, actualsurfacewater=0.001,
        ...       frontdepth=[500.0, 100.0, 0.0, 0.0],
        ...       moisture=[0.3, 0.30001, 0.1, 0.1])
        moisturechange: nan, 0.0, nan, nan
        moisture: 0.300004, 0.300004, 0.300004, 0.300004
        infiltration: 0.001
        percolation: 0.0
        frontdepth: 500.0, 0.0, 0.0, 0.0

        ToDo: In the original GARTO code, the remaining soil water and infiltration
              become percolation.  However, when evaporation interferes with the
              original equations, this simplification can result in percolation rates
              larger than saturated conductivity.  We observed this in the
              :ref:`ga_garto_24h_1000mm_evap_continuous` example, where percolation was
              20 mm/h (the rainfall rate) in the 21st hour despite a saturated
              conductivity of 13.2 mm/h.  For our assumption, the percolation rate is
              12.8 mm/h.  Nevertheless, we should keep this deviation from the original
              implementation in mind for a while;  in case it brings unexpected side
              effects in future applications.
    """

    SUBMETHODS = (
        Return_RelativeMoisture_V1,
        Return_DryDepth_V1,
        Return_Conductivity_V1,
        Return_CapillaryDrive_V1,
    )
    CONTROLPARAMETERS = (
        ga_control.NmbBins,
        ga_control.DT,
        ga_control.SoilDepth,
        ga_control.ResidualMoisture,
        ga_control.SaturationMoisture,
        ga_control.SaturatedConductivity,
        ga_control.AirEntryPotential,
        ga_control.PoreSizeDistribution,
    )
    DERIVEDPARAMETERS = (ga_derived.EffectiveCapillarySuction,)
    UPDATEDSEQUENCES = (
        ga_states.Moisture,
        ga_states.FrontDepth,
        ga_logs.MoistureChange,
        ga_aides.ActualSurfaceWater,
    )

    @staticmethod
    def __call__(model: modeltools.Model, b: int, s: int) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess
        log = model.sequences.logs.fastaccess

        if sta.frontdepth[b, s] > 0.0:
            conductivity: float = model.return_conductivity_v1(b, s)
            capillarydrive: float = model.return_capillarydrive_v1(b - 1, b, s)
            factor: float = 1.0 if aid.actualsurfacewater[s] > 0.0 else 1.7
            log.moisturechange[b, s] = (con.dt / sta.frontdepth[b, s]) * (
                max(aid.actualsurfacewater[s], 0.0) / con.dt
                - conductivity
                - (factor * con.saturatedconductivity[s] * capillarydrive)
                / sta.frontdepth[b, s]
            )
            potinfiltration: float = (
                con.dt
                * con.saturatedconductivity[s]
                * (1.0 + der.effectivecapillarysuction[s] / sta.frontdepth[b, s])
            )
        else:
            drydepth: float = model.return_drydepth_v1(s)
            conductivity = model.return_conductivity_v1(b - 1, s)
            log.moisturechange[b, s] = (
                aid.actualsurfacewater[s] - con.dt * conductivity
            ) / drydepth
            potinfiltration = (
                con.dt
                * con.saturatedconductivity[s]
                * (1.0 + der.effectivecapillarysuction[s] / drydepth)
            )

        initialcontent: float = sta.frontdepth[b, s] * (
            sta.moisture[b, s] - sta.moisture[b - 1, s]
        )

        sta.moisture[b, s] += log.moisturechange[b, s]
        sta.moisture[b, s] = min(sta.moisture[b, s], con.saturationmoisture[s])
        sta.moisture[b, s] = max(sta.moisture[b, s], sta.moisture[b - 1, s])

        if aid.actualsurfacewater[s] > potinfiltration:
            volume: float = potinfiltration + initialcontent
            aid.actualsurfacewater[s] -= potinfiltration
        else:
            volume = aid.actualsurfacewater[s] + initialcontent
            aid.actualsurfacewater[s] = 0.0

        if sta.moisture[b, s] > sta.moisture[b - 1, s]:
            sta.frontdepth[b, s] = volume / (
                sta.moisture[b, s] - sta.moisture[b - 1, s]
            )
        else:
            if b > 1:
                sta.frontdepth[b - 1, s] += volume / (
                    sta.moisture[b - 1, s] - sta.moisture[b - 2, s]
                )
                sta.moisture[b, s] = sta.moisture[0, s]
            elif b == 1:
                sta.moisture[0, s] += volume / con.soildepth[s]
                for bb in range(1, con.nmbbins):
                    sta.moisture[bb, s] = sta.moisture[0, s]
            sta.frontdepth[b, s] = 0.0
            log.moisturechange[b, s] = 0.0


class Infiltrate_WettingFrontBins_V1(modeltools.Method):
    r"""Process infiltration into the wetting front bins.

    |Infiltrate_WettingFrontBins_V1| does not perform any calculations itself but
    selects the proper submethods to do so.  It either does nothing (if the filled bin
    is saturated) or calls |Redistribute_Front_V1|, |Shift_Front_V1|, or
    |Active_Bin_V1| (primarily depending on the initial surface water depth and the
    current moisture contents).

    |Infiltrate_WettingFrontBins_V1| is specifically designed for |ga_garto|.

    Examples:

        Instead of triggering actual calculations, we try to show how
        |Infiltrate_WettingFrontBins_V1| selects the mentioned methods based on mocking
        them.  Therefore, we must import the model in pure Python mode:

        >>> from hydpy.core.importtools import reverse_model_wildcard_import
        >>> reverse_model_wildcard_import()
        >>> from hydpy import pub, print_values
        >>> with pub.options.usecython(False):
        ...     from hydpy.models.ga import *
        ...     simulationstep("1h")
        ...     parameterstep("1h")

        We define only those parameters required for selecting the proper methods:

        >>> nmbsoils(1)
        >>> nmbbins(5)
        >>> dt(0.25)
        >>> saturationmoisture(0.6)
        >>> saturatedconductivity(10.0)

        The following test function prepares the initial surface water depth, the
        (current) relative moisture, and the (previous) moisture change.  Afterwards,
        it replaces the mentioned methods with mocks, invokes
        |Infiltrate_WettingFrontBins_V1|, and prints the passed arguments of all mock
        calls:

        >>> from unittest.mock import patch
        >>> def check(initialsurfacewater, moisture, moisturechange):
        ...     states.moisture = [[m] for m in moisture]
        ...     logs.moisturechange = [[mc] for mc in moisturechange]
        ...     aides.initialsurfacewater = initialsurfacewater
        ...     with patch.object(
        ...         model, "redistribute_front_v1"
        ...     ) as redistribute_front_v1, patch.object(
        ...         model, "shift_front_v1"
        ...     ) as shift_front_v1, patch.object(
        ...         model, "active_bin_v1"
        ...     ) as active_bin_v1:
        ...         model.infiltrate_wettingfrontbins_v1(0)
        ...     for mock in (shift_front_v1, redistribute_front_v1, active_bin_v1):
        ...         if mock.called:
        ...             print(mock._extract_mock_name(), end=": ")
        ...             print_values([str(call)[4:] for call in mock.mock_calls])

        If the first (filled) bin is saturated, |Infiltrate_WettingFrontBins_V1| does
        nothing:

        >>> check(initialsurfacewater=20.0,
        ...       moisture=[0.6, 0.6, 0.6, 0.6, 0.6],
        ...       moisturechange=[0.0, 0.0, 0.0, 0.0, 0.0])

        If a wetting front bin is saturated, |Infiltrate_WettingFrontBins_V1| calls
        either |Shift_Front_V1| or |Redistribute_Front_V1|, depending on whether
        the surface water depth (rainfall intensity) exceeds saturated conductivity or
        not:

        >>> check(initialsurfacewater=20.0,
        ...       moisture=[0.1, 0.6, 0.6, 0.6, 0.6],
        ...       moisturechange=[0.0, 0.0, 0.0, 0.0, 0.0])
        shift_front_v1: (1, 0)

        >>> check(initialsurfacewater=2.0,
        ...       moisture=[0.1, 0.6, 0.6, 0.6, 0.6],
        ...       moisturechange=[0.0, 0.0, 0.0, 0.0, 0.0])
        redistribute_front_v1: (1, 0)

        If all bins are active, |Infiltrate_WettingFrontBins_V1| calls |Shift_Front_V1|
        for all bins except for the last one, for which it calls
        |Redistribute_Front_V1|:

        >>> check(initialsurfacewater=2.0,
        ...       moisture=[0.1, 0.2, 0.3, 0.4, 0.5],
        ...       moisturechange=[0.0, 0.0, 0.0, 0.0, 0.0])
        shift_front_v1: (1, 0), (2, 0), (3, 0)
        redistribute_front_v1: (4, 0)

        If there is at least one inactivated bin and the last active bin is not
        saturated, |Infiltrate_WettingFrontBins_V1| either calls |Active_Bin_V1| to
        activate a new bin right to it or calls |Redistribute_Front_V1|, depending on
        whether rainfall intensity exceeds saturated conductivity and the active bin's
        relative moisture decreased previously or not:

        >>> check(initialsurfacewater=20.0,
        ...       moisture=[0.1, 0.2, 0.3, 0.4, 0.1],
        ...       moisturechange=[0.0, 0.0, 0.0, -1.0, 0.0])
        shift_front_v1: (1, 0), (2, 0)
        active_bin_v1: (3, 0)

        >>> check(initialsurfacewater=2.0,
        ...       moisture=[0.1, 0.2, 0.3, 0.4, 0.1],
        ...       moisturechange=[0.0, 0.0, 0.0, -1.0, 0.0])
        shift_front_v1: (1, 0), (2, 0)
        redistribute_front_v1: (3, 0)

        >>> check(initialsurfacewater=20.0,
        ...       moisture=[0.1, 0.2, 0.3, 0.4, 0.1],
        ...       moisturechange=[0.0, 0.0, 0.0, 0.0, 0.0])
        shift_front_v1: (1, 0), (2, 0)
        redistribute_front_v1: (3, 0)

        >>> check(initialsurfacewater=2.0,
        ...       moisture=[0.1, 0.2, 0.3, 0.4, 0.1],
        ...       moisturechange=[0.0, 0.0, 0.0, 0.0, 0.0])
        shift_front_v1: (1, 0), (2, 0)
        redistribute_front_v1: (3, 0)

        >>> reverse_model_wildcard_import()
    """

    SUBMETHODS = (
        Return_RelativeMoisture_V1,
        Return_DryDepth_V1,
        Return_Conductivity_V1,
        Return_CapillaryDrive_V1,
        Active_Bin_V1,
        Shift_Front_V1,
        Redistribute_Front_V1,
    )
    CONTROLPARAMETERS = (
        ga_control.NmbBins,
        ga_control.DT,
        ga_control.SoilDepth,
        ga_control.ResidualMoisture,
        ga_control.SaturationMoisture,
        ga_control.SaturatedConductivity,
        ga_control.AirEntryPotential,
        ga_control.PoreSizeDistribution,
    )
    DERIVEDPARAMETERS = (ga_derived.EffectiveCapillarySuction,)
    REQUIREDSEQUENCES = (ga_aides.InitialSurfaceWater,)
    UPDATEDSEQUENCES = (
        ga_states.Moisture,
        ga_states.FrontDepth,
        ga_logs.MoistureChange,
        ga_aides.ActualSurfaceWater,
    )

    @staticmethod
    def __call__(model: modeltools.Model, s: int) -> None:
        con = model.parameters.control.fastaccess
        sta = model.sequences.states.fastaccess
        log = model.sequences.logs.fastaccess
        aid = model.sequences.aides.fastaccess
        for b in range(1, con.nmbbins):
            if sta.moisture[0, s] >= con.saturationmoisture[s]:
                break
            if sta.moisture[b, s] >= con.saturationmoisture[s]:
                if aid.initialsurfacewater[s] < con.dt * con.saturatedconductivity[s]:
                    model.redistribute_front_v1(b, s)
                else:
                    model.shift_front_v1(b, s)
                break
            if b == con.nmbbins - 1:
                model.redistribute_front_v1(b, s)
                break
            if sta.moisture[0, s] < sta.moisture[b, s] < sta.moisture[b + 1, s]:
                log.moisturechange[b, s] = 0.0
                model.shift_front_v1(b, s)
            elif (
                (aid.initialsurfacewater[s] > con.dt * con.saturatedconductivity[s])
                and (log.moisturechange[b, s] < 0.0)
                and (sta.moisture[b, s] > sta.moisture[0, s])
            ):
                model.active_bin_v1(b, s)
                break
            else:
                model.redistribute_front_v1(b, s)
                break


class Merge_FrontDepthOvershootings_V1(modeltools.Method):
    r"""Merge those neighbour bins where the wetting front's depth of the right
    neighbour exceeds the wetting front's depth of the left neighbour.

    Examples:

        For comparison, we perform the following examples similar to those of method
        |Active_Bin_V1|.  However, in contrast to |Active_Bin_V1|,
        |Merge_FrontDepthOvershootings_V1| only needs to know the number of available
        bins and their current states only, making the general set-up much shorter:

        >>> from hydpy.models.ga_garto import *
        >>> parameterstep()
        >>> nmbsoils(1)
        >>> nmbbins(5)
        >>> sealed(False)
        >>> soilarea(1.0)
        >>> soildepth(1000.0)
        >>> derived.soilareafraction.update()

        Instead of accepting different values for the actual surface water depth, the
        test function here allows defining the respective front's depth, moisture and
        moisture change:

        >>> from hydpy.core.objecttools import repr_, repr_values
        >>> def check(frontdepth, moisture, moisturechange):
        ...     states.frontdepth = [[fd] for fd in frontdepth]
        ...     states.moisture = [[m] for m in moisture]
        ...     logs.moisturechange = [[mc] for mc in moisturechange]
        ...     old_volume = round(model.watercontent, 12)
        ...     model.merge_frontdepthovershootings_v1(0)
        ...     new_volume = round(model.watercontent, 12)
        ...     assert old_volume == new_volume
        ...     print(f"frontdepth: {repr_values(states.frontdepth[:, 0])}")
        ...     print(f"moisture: {repr_values(states.moisture[:, 0])}")
        ...     print(f"moisturechange: {repr_values(logs.moisturechange[:, 0])}")

        Nothing happens as long as all bins have smaller front depths than their left
        neighbours.  Note that |Merge_FrontDepthOvershootings_V1| also becomes active
        only if relative moisture increases from left to right.  Hence, in the
        following example, there is no merging of the two inactive bins, which (as
        usual) both have zero front depths:

        >>> check(frontdepth=[1000.0, 500.0, 100.0, 0.0, 0.0],
        ...       moisture=[0.1, 0.3, 0.5, 0.1, 0.1],
        ...       moisturechange=[0.2, 0.4, 0.6, 0.0, 0.0])
        frontdepth: 1000.0, 500.0, 100.0, 0.0, 0.0
        moisture: 0.1, 0.3, 0.5, 0.1, 0.1
        moisturechange: 0.2, 0.4, 0.6, 0.0, 0.0

        For equal depths, |Merge_FrontDepthOvershootings_V1| deactivates the left
        neighbour bin and sets the moisture change of the left neighbour to zero:

        >>> check(frontdepth=[1000.0, 500.0, 500.0, 0.0, 0.0],
        ...       moisture=[0.1, 0.3, 0.5, 0.1, 0.1],
        ...       moisturechange=[0.2, 0.4, 0.6, 0.0, 0.0])
        frontdepth: 1000.0, 500.0, 0.0, 0.0, 0.0
        moisture: 0.1, 0.5, 0.1, 0.1, 0.1
        moisturechange: 0.2, 0.0, 0.0, 0.0, 0.0

        In case of an overshooting, |Merge_FrontDepthOvershootings_V1| must add the
        (additional) water content of the (deactivated) right neighbour to the
        (preserved) left neighbour:

        >>> check(frontdepth=[1000.0, 500.0, 600.0, 0.0, 0.0],
        ...       moisture=[0.1, 0.3, 0.5, 0.1, 0.1],
        ...       moisturechange=[0.2, 0.4, 0.6, 0.0, 0.0])
        frontdepth: 1000.0, 550.0, 0.0, 0.0, 0.0
        moisture: 0.1, 0.5, 0.1, 0.1, 0.1
        moisturechange: 0.2, 0.0, 0.0, 0.0, 0.0

        All right neighbours of a deactivated bin move (at least) one place to the
        left:

        >>> check(frontdepth=[1000.0, 500.0, 600.0, 400.0, 0.0],
        ...       moisture=[0.1, 0.2, 0.3, 0.4, 0.1],
        ...       moisturechange=[0.2, 0.4, 0.6, 0.8, 0.0])
        frontdepth: 1000.0, 550.0, 400.0, 0.0, 0.0
        moisture: 0.1, 0.3, 0.4, 0.1, 0.1
        moisturechange: 0.2, 0.0, 0.8, 0.0, 0.0

        If the last bin is active, it gets properly deactivated:

        >>> check(frontdepth=[1000.0, 500.0, 600.0, 400.0, 300.0],
        ...       moisture=[0.1, 0.2, 0.3, 0.4, 0.5],
        ...       moisturechange=[0.2, 0.4, 0.6, 0.8, 1.0])
        frontdepth: 1000.0, 550.0, 400.0, 300.0, 0.0
        moisture: 0.1, 0.3, 0.4, 0.5, 0.1
        moisturechange: 0.2, 0.0, 0.8, 1.0, 0.0

        The two last examples demonstrate that the underlying algorithm works stably in
        case multiple mergings are necessary:

        >>> check(frontdepth=[1000.0, 500.0, 600.0, 700.0, 0.0],
        ...       moisture=[0.1, 0.2, 0.3, 0.4, 0.1],
        ...       moisturechange=[0.2, 0.4, 0.6, 0.8, 0.0])
        frontdepth: 1000.0, 600.0, 0.0, 0.0, 0.0
        moisture: 0.1, 0.4, 0.1, 0.1, 0.1
        moisturechange: 0.2, 0.0, 0.0, 0.0, 0.0

        >>> check(frontdepth=[1000.0, 500.0, 600.0, 400.0, 500.0],
        ...       moisture=[0.1, 0.2, 0.3, 0.4, 0.5],
        ...       moisturechange=[0.2, 0.4, 0.6, 0.8, 1.0])
        frontdepth: 1000.0, 550.0, 450.0, 0.0, 0.0
        moisture: 0.1, 0.3, 0.5, 0.1, 0.1
        moisturechange: 0.2, 0.0, 0.0, 0.0, 0.0
    """

    CONTROLPARAMETERS = (ga_control.NmbBins,)
    UPDATEDSEQUENCES = (
        ga_states.Moisture,
        ga_states.FrontDepth,
        ga_logs.MoistureChange,
    )

    @staticmethod
    def __call__(model: modeltools.Model, s: int) -> None:
        con = model.parameters.control.fastaccess
        sta = model.sequences.states.fastaccess
        log = model.sequences.logs.fastaccess
        b = con.nmbbins - 1
        while b > 1:
            if (sta.frontdepth[b, s] >= sta.frontdepth[b - 1, s]) and (
                sta.moisture[b, s] > sta.moisture[b - 1, s]
            ):
                content_thisbin: float = sta.frontdepth[b, s] * (
                    sta.moisture[b, s] - sta.moisture[b - 1, s]
                )
                content_lastbin: float = sta.frontdepth[b - 1, s] * (
                    sta.moisture[b - 1, s] - sta.moisture[b - 2, s]
                )
                sta.frontdepth[b - 1, s] = (content_thisbin + content_lastbin) / (
                    sta.moisture[b, s] - sta.moisture[b - 2, s]
                )
                sta.moisture[b - 1, s] = sta.moisture[b, s]
                sta.frontdepth[b, s] = 0.0
                sta.moisture[b, s] = sta.moisture[0, s]
                log.moisturechange[b - 1, s] = 0.0
                log.moisturechange[b, s] = 0.0
                for bb in range(b + 1, con.nmbbins):
                    if sta.moisture[bb, s] > sta.moisture[0, s]:
                        sta.moisture[bb - 1, s] = sta.moisture[bb, s]
                        sta.moisture[bb, s] = sta.moisture[0, s]
                        sta.frontdepth[bb - 1, s] = sta.frontdepth[bb, s]
                        sta.frontdepth[bb, s] = 0.0
                        log.moisturechange[bb - 1, s] = log.moisturechange[bb, s]
                        log.moisturechange[bb, s] = 0.0
                b += 1
            b -= 1


class Merge_SoilDepthOvershootings_V1(modeltools.Method):
    r"""Merge bins with wetting front depth larger than soil depth with their
    left neighbour bins and add their water excess to percolation.

    |Merge_SoilDepthOvershootings_V1| assumes proper sorting of wetting front depths
    (decreasing from left to right), as ensured by |Merge_FrontDepthOvershootings_V1|.

    Examples:

        For comparison, we perform the following examples similar to those of the
        related method |Merge_FrontDepthOvershootings_V1|.  The general setting is
        identical:

        >>> from hydpy.models.ga_garto import *
        >>> parameterstep()
        >>> nmbsoils(1)
        >>> nmbbins(5)
        >>> sealed(False)
        >>> soilarea(1.0)
        >>> soildepth(1000.0)
        >>> derived.soilareafraction.update()

        The test function is similar but must also consider percolation:

        >>> from hydpy.core.objecttools import repr_, repr_values
        >>> def check(frontdepth, moisture, moisturechange):
        ...     states.frontdepth = [[fd] for fd in frontdepth]
        ...     states.moisture = [[m] for m in moisture]
        ...     logs.moisturechange = [[mc] for mc in moisturechange]
        ...     fluxes.percolation = 0.0
        ...     old_volume = round(model.watercontent, 12)
        ...     model.merge_soildepthovershootings_v1(0)
        ...     new_volume = round(model.watercontent + fluxes.percolation[0], 12)
        ...     assert old_volume == new_volume
        ...     print(f"frontdepth: {repr_values(states.frontdepth[:, 0])}")
        ...     print(f"moisture: {repr_values(states.moisture[:, 0])}")
        ...     print(f"moisturechange: {repr_values(logs.moisturechange[:, 0])}")
        ...     print(f"percolation: {repr_(fluxes.percolation[0])}")

        Nothing happens as long as all bins have smaller front depths than their left
        neighbours.  Note that |Merge_SoilDepthOvershootings_V1| also becomes active
        only if relative moisture increases from left to right.  Hence, in the
        following example, there is no merging of the two inactive bins, which (as
        usual) both have zero front depths:

        >>> check(frontdepth=[1000.0, 900.0, 800.0, 0.0, 0.0],
        ...       moisture=[0.1, 0.2, 0.3, 0.1, 0.1],
        ...       moisturechange=[0.0, 1.0, 2.0, 0.0, 0.0])
        frontdepth: 1000.0, 900.0, 800.0, 0.0, 0.0
        moisture: 0.1, 0.2, 0.3, 0.1, 0.1
        moisturechange: 0.0, 1.0, 2.0, 0.0, 0.0
        percolation: 0.0

        If a single front's depth reaches the soil bottom exactly,
        |Merge_SoilDepthOvershootings_V1| deactivates the affected bin and takes its
        relative moisture value as the new initial moisture:

        >>> check(frontdepth=[1000.0, 1000.0, 0.0, 0.0, 0.0],
        ...       moisture=[0.1, 0.2, 0.1, 0.1, 0.1],
        ...       moisturechange=[0.0, 1.0, 0.0, 0.0, 0.0])
        frontdepth: 1000.0, 0.0, 0.0, 0.0, 0.0
        moisture: 0.2, 0.2, 0.2, 0.2, 0.2
        moisturechange: 0.0, 0.0, 0.0, 0.0, 0.0
        percolation: 0.0

        Parts of the front lying below the soil's bottom become percolation:

        >>> check(frontdepth=[1000.0, 1100.0, 0.0, 0.0, 0.0],
        ...       moisture=[0.1, 0.2, 0.1, 0.1, 0.1],
        ...       moisturechange=[0.0, 1.0, 0.0, 0.0, 0.0])
        frontdepth: 1000.0, 0.0, 0.0, 0.0, 0.0
        moisture: 0.2, 0.2, 0.2, 0.2, 0.2
        moisturechange: 0.0, 0.0, 0.0, 0.0, 0.0
        percolation: 10.0

        All remaining active wetting front bins move (at least) one place to the left:

        >>> check(frontdepth=[1000.0, 1100.0, 800.0, 700.0, 600.0],
        ...       moisture=[0.1, 0.2, 0.3, 0.4, 0.5],
        ...       moisturechange=[0.0, 1.0, 2.0, 3.0, 4.0])
        frontdepth: 1000.0, 800.0, 700.0, 600.0, 0.0
        moisture: 0.2, 0.3, 0.4, 0.5, 0.2
        moisturechange: 0.0, 2.0, 3.0, 4.0, 0.0
        percolation: 10.0

        The two last examples demonstrate that the underlying algorithm works stably in
        case multiple mergings are necessary:

        >>> check(frontdepth=[1000.0, 1200.0, 1100.0, 700.0, 0.0],
        ...       moisture=[0.1, 0.2, 0.3, 0.4, 0.1],
        ...       moisturechange=[0.0, 1.0, 2.0, 3.0, 0.0])
        frontdepth: 1000.0, 700.0, 0.0, 0.0, 0.0
        moisture: 0.3, 0.4, 0.3, 0.3, 0.3
        moisturechange: 0.0, 3.0, 0.0, 0.0, 0.0
        percolation: 30.0

        >>> check(frontdepth=[1000.0, 1200.0, 1200.0, 1100.0, 1100.0],
        ...       moisture=[0.1, 0.2, 0.3, 0.4, 0.5],
        ...       moisturechange=[0.0, 1.0, 2.0, 3.0, 4.0])
        frontdepth: 1000.0, 0.0, 0.0, 0.0, 0.0
        moisture: 0.5, 0.5, 0.5, 0.5, 0.5
        moisturechange: 0.0, 0.0, 0.0, 0.0, 0.0
        percolation: 60.0
    """

    CONTROLPARAMETERS = (
        ga_control.NmbBins,
        ga_control.SoilDepth,
    )
    UPDATEDSEQUENCES = (
        ga_states.FrontDepth,
        ga_states.Moisture,
        ga_logs.MoistureChange,
        ga_fluxes.Percolation,
    )

    @staticmethod
    def __call__(model: modeltools.Model, s: int) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        log = model.sequences.logs.fastaccess

        while (sta.frontdepth[1, s] >= con.soildepth[s]) and (
            sta.moisture[1, s] > sta.moisture[0, s]
        ):
            flu.percolation[s] += (sta.frontdepth[1, s] - con.soildepth[s]) * (
                sta.moisture[1, s] - sta.moisture[0, s]
            )
            sta.frontdepth[1, s] = 0.0
            log.moisturechange[1, s] = 0.0
            sta.moisture[0, s] = sta.moisture[1, s]
            for b in range(2, con.nmbbins):
                if sta.moisture[b, s] > sta.moisture[0, s]:
                    sta.frontdepth[b - 1, s] = sta.frontdepth[b, s]
                    log.moisturechange[b - 1, s] = log.moisturechange[b, s]
                    sta.moisture[b - 1, s] = sta.moisture[b, s]
                    sta.frontdepth[b, s] = 0.0
                    log.moisturechange[b, s] = 0.0
                sta.moisture[b, s] = sta.moisture[0, s]


class Water_AllBins_V1(modeltools.Method):
    r"""Water the soil's body by (potentially) adding water to all active bins.

    The soil water addition calculated by |Water_AllBins_V1| equals the defined soil
    water supply, except adding the complete supply would exceed the saturation water
    content.

    Note that the caller needs to pass the supply as a method parameter, which allows
    him to decide whether to add everything in one simulation step or multiple
    numerical substeps.

    Examples:

        We prepare a single shallow soil compartment divided into four bins:

        >>> from hydpy.models.ga_garto import *
        >>> simulationstep("1d")
        >>> parameterstep("1d")
        >>> nmbsoils(1)
        >>> nmbbins(4)
        >>> dt(0.5)
        >>> sealed(False)
        >>> soilarea(1.0)
        >>> soildepth(100.0)
        >>> saturationmoisture(0.5)
        >>> derived.soilareafraction.update()

        The following test function works similar to the one defined for demonstrating
        |Active_Bin_V1| but considers the soil water addition instead of infiltration:

        >>> from hydpy.core.objecttools import repr_, repr_values
        >>> def check(soilwatersupply, moisture, frontdepth):
        ...     fluxes.soilwatersupply[0] = soilwatersupply
        ...     states.moisture = [[m] for m in moisture]
        ...     states.frontdepth = [[fd] for fd in frontdepth]
        ...     logs.moisturechange = [[1.0], [2.0], [3.0], [4.0]]
        ...     fluxes.soilwateraddition[0] = 0.0
        ...     old_volume = round(model.watercontent, 12)
        ...     model.water_allbins_v1(0, soilwatersupply)
        ...     new_volume = round(model.watercontent, 12)
        ...     assert old_volume + fluxes.soilwateraddition[0] == new_volume
        ...     print(f"soilwatersupply: {repr_(fluxes.soilwatersupply[0])}")
        ...     print(f"moisture: {repr_values(states.moisture[:, 0])}")
        ...     print(f"frontdepth: {repr_values(states.frontdepth[:, 0])}")
        ...     print(f"moisturechange: {repr_values(logs.moisturechange[:, 0])}")
        ...     print(f"soilwateraddition: {repr_(fluxes.soilwateraddition[0])}")

        For zero soil water supply, |Water_AllBins_V1| does nothing:

        >>> check(soilwatersupply=0.0,
        ...       moisture=[0.1, 0.3, 0.1, 0.1],
        ...       frontdepth=[100.0, 50.0, 0.0, 0.0])
        soilwatersupply: 0.0
        moisture: 0.1, 0.3, 0.1, 0.1
        frontdepth: 100.0, 50.0, 0.0, 0.0
        moisturechange: 1.0, 2.0, 3.0, 4.0
        soilwateraddition: 0.0

        |Water_AllBins_V1| tries to add the supply to the dryest bin by increasing its
        relative moisture content:

        >>> check(soilwatersupply=5.0,
        ...       moisture=[0.1, 0.3, 0.1, 0.1],
        ...       frontdepth=[100.0, 50.0, 0.0, 0.0])
        soilwatersupply: 5.0
        moisture: 0.2, 0.3, 0.2, 0.2
        frontdepth: 100.0, 50.0, 0.0, 0.0
        moisturechange: 0.0, 2.0, 3.0, 4.0
        soilwateraddition: 5.0

        If a bin is not the last active bin, its highest possible moisture content is
        restricted by the relative moisture value of its right neighbour bin.  If two
        bins get the same moisture, one of them becomes obsolete, so we can remove it
        and shift all its right neighbours one place to the left:

        >>> check(soilwatersupply=10.0,
        ...       moisture=[0.1, 0.3, 0.1, 0.1],
        ...       frontdepth=[100.0, 50.0, 0.0, 0.0])
        soilwatersupply: 10.0
        moisture: 0.3, 0.3, 0.3, 0.3
        frontdepth: 100.0, 0.0, 0.0, 0.0
        moisturechange: 0.0, 3.0, 4.0, 0.0
        soilwateraddition: 10.0

        If the first bin cannot take enough water, |Water_AllBins_V1| updates the front
        depth and increases the water content of the second bin:

        >>> check(soilwatersupply=20.0,
        ...       moisture=[0.1, 0.3, 0.1, 0.1],
        ...       frontdepth=[100.0, 50.0, 0.0, 0.0])
        soilwatersupply: 20.0
        moisture: 0.4, 0.4, 0.4, 0.4
        frontdepth: 100.0, 0.0, 0.0, 0.0
        moisturechange: 0.0, 3.0, 4.0, 0.0
        soilwateraddition: 20.0

        However, no bin can possess relative moisture higher than indicated by
        saturation moisture:

        >>> check(soilwatersupply=40.0,
        ...       moisture=[0.1, 0.3, 0.1, 0.1],
        ...       frontdepth=[100.0, 50.0, 0.0, 0.0])
        soilwatersupply: 40.0
        moisture: 0.5, 0.5, 0.5, 0.5
        frontdepth: 100.0, 0.0, 0.0, 0.0
        moisturechange: 0.0, 3.0, 4.0, 0.0
        soilwateraddition: 30.0

        |Water_AllBins_V1| deactivates multiple bins when necessary:

        >>> check(soilwatersupply=40.0,
        ...       moisture=[0.1, 0.3, 0.5, 0.1],
        ...       frontdepth=[100.0, 50.0, 0.0, 0.0])
        soilwatersupply: 40.0
        moisture: 0.5, 0.5, 0.5, 0.5
        frontdepth: 100.0, 0.0, 0.0, 0.0
        moisturechange: 0.0, 4.0, 0.0, 0.0
        soilwateraddition: 30.0

        >>> check(soilwatersupply=10.0,
        ...       moisture=[0.1, 0.2, 0.3, 0.4],
        ...       frontdepth=[100.0, 75.0, 50.0, 25.0])
        soilwatersupply: 10.0
        moisture: 0.333333, 0.4, 0.333333, 0.333333
        frontdepth: 100.0, 25.0, 0.0, 0.0
        moisturechange: 0.0, 4.0, 0.0, 0.0
        soilwateraddition: 10.0

        >>> check(soilwatersupply=30.0,
        ...       moisture=[0.1, 0.2, 0.3, 0.4],
        ...       frontdepth=[100.0, 75.0, 50.0, 25.0])
        soilwatersupply: 30.0
        moisture: 0.5, 0.5, 0.5, 0.5
        frontdepth: 100.0, 0.0, 0.0, 0.0
        moisturechange: 0.0, 0.0, 0.0, 0.0
        soilwateraddition: 25.0

        The last two examples demonstrate, similar to the first example, that
        |Water_AllBins_V1| adjusts the relative moisture value of all non-active bins
        after increasing the moisture of the first bin:

        >>> check(soilwatersupply=10.0,
        ...       moisture=[0.1, 0.1, 0.1, 0.1],
        ...       frontdepth=[100.0, 0.0, 0.0, 0.0])
        soilwatersupply: 10.0
        moisture: 0.2, 0.2, 0.2, 0.2
        frontdepth: 100.0, 0.0, 0.0, 0.0
        moisturechange: 0.0, 2.0, 3.0, 4.0
        soilwateraddition: 10.0

        >>> check(soilwatersupply=50.0,
        ...       moisture=[0.1, 0.1, 0.1, 0.1],
        ...       frontdepth=[100.0, 0.0, 0.0, 0.0])
        soilwatersupply: 50.0
        moisture: 0.5, 0.5, 0.5, 0.5
        frontdepth: 100.0, 0.0, 0.0, 0.0
        moisturechange: 0.0, 2.0, 3.0, 4.0
        soilwateraddition: 40.0
    """

    CONTROLPARAMETERS = (
        ga_control.NmbBins,
        ga_control.SoilDepth,
        ga_control.SaturationMoisture,
    )
    UPDATEDSEQUENCES = (
        ga_states.Moisture,
        ga_states.FrontDepth,
        ga_logs.MoistureChange,
        ga_fluxes.SoilWaterAddition,
    )

    @staticmethod
    def __call__(model: modeltools.Model, s: int, supply: float) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        log = model.sequences.logs.fastaccess

        if supply <= 0.0:
            return

        rest: float = supply
        bl = model.return_lastactivebin_v1(s)
        for b in range(bl):
            freedepth: float = con.soildepth[s] - sta.frontdepth[b + 1, s]
            freecontent: float = freedepth * (
                sta.moisture[b + 1, s] - sta.moisture[b, s]
            )
            if rest <= freecontent:
                flu.soilwateraddition[s] += supply
                sta.moisture[b, s] += rest / freedepth
                rest = 0.0
                initmoisture: float = sta.moisture[b, s]
                break
            rest -= freecontent
            sta.frontdepth[b + 1, s] = con.soildepth[s]
            initmoisture = sta.moisture[b + 1, s]

        if rest > 0.0:
            freecontent = con.soildepth[s] * (
                con.saturationmoisture[s] - sta.moisture[bl, s]
            )
            if rest <= freecontent:
                flu.soilwateraddition[s] += supply
                sta.moisture[bl, s] += rest / con.soildepth[s]
            else:
                rest -= freecontent
                flu.soilwateraddition[s] += supply - rest
                sta.moisture[bl, s] = con.saturationmoisture[s]
            initmoisture = sta.moisture[bl, s]

        for b in range(con.nmbbins):
            if sta.moisture[b, s] <= initmoisture:
                sta.moisture[b, s] = initmoisture

        for b in range(bl):
            while (sta.moisture[b, s] == sta.moisture[b + 1, s]) and (
                sta.frontdepth[b + 1, s] > 0.0
            ):
                sta.frontdepth[b + 1] = sta.frontdepth[b]
                for bb in range(b, con.nmbbins - 1):
                    sta.moisture[bb, s] = sta.moisture[bb + 1, s]
                    sta.frontdepth[bb, s] = sta.frontdepth[bb + 1, s]
                    log.moisturechange[bb, s] = log.moisturechange[bb + 1, s]
                sta.moisture[con.nmbbins - 1, s] = sta.moisture[0, s]
                sta.frontdepth[con.nmbbins - 1, s] = 0.0
                log.moisturechange[con.nmbbins - 1, s] = 0.0
        log.moisturechange[0, s] = 0.0

        return


class Withdraw_AllBins_V1(modeltools.Method):
    r"""Take withdrawal from the available surface water and (potentially) from all
    active bins.

    The withdrawal calculated by |Withdraw_AllBins_V1| equals the defined demand,
    except no water exceeding the residual moisture is left.  Hence, for example,
    actual evaporation is more suitable for specifying the demand than potential
    evaporation.

    Note that the caller needs to pass the demand as a method parameter, which allows
    him to decide whether to subtract everything in one simulation step or multiple
    numerical substeps.

    Examples:

        We prepare a single shallow soil compartment divided into four bins:

        >>> from hydpy.models.ga_garto import *
        >>> simulationstep("1d")
        >>> parameterstep("1d")
        >>> nmbsoils(1)
        >>> nmbbins(4)
        >>> dt(0.5)
        >>> sealed(False)
        >>> soilarea(1.0)
        >>> soildepth(100.0)
        >>> residualmoisture(0.1)
        >>> derived.soilareafraction.update()

        The following test function works similar to the one defined for demonstrating
        |Active_Bin_V1| but considers the withdrawal instead of infiltration:

        >>> from hydpy.core.objecttools import repr_, repr_values
        >>> def check(demand, actualsurfacewater, frontdepth, moisture):
        ...     states.moisture = [[m] for m in moisture]
        ...     states.frontdepth = [[fd] for fd in frontdepth]
        ...     logs.moisturechange = nan
        ...     aides.actualsurfacewater = actualsurfacewater
        ...     fluxes.withdrawal[0] = 0.0
        ...     old_volume = round(model.watercontent + aides.actualsurfacewater[0], 12)
        ...     model.withdraw_allbins_v1(0, control.dt * demand)
        ...     new_volume = round(model.watercontent + aides.actualsurfacewater[0], 12)
        ...     assert old_volume == new_volume + fluxes.withdrawal[0]
        ...     print(f"withdrawal: {repr_(fluxes.withdrawal[0])}")
        ...     print(f"actualsurfacewater: {repr_(aides.actualsurfacewater[0])}")
        ...     print(f"moisture: {repr_values(states.moisture[:, 0])}")
        ...     print(f"frontdepth: {repr_values(states.frontdepth[:, 0])}")

        For zero demand, |Withdraw_AllBins_V1| does nothing:

        >>> check(demand=0.0, actualsurfacewater=20.0,
        ...       frontdepth=[100.0, 50.0, 0.0, 0.0],
        ...       moisture=[0.1, 0.3, 0.1, 0.1])
        withdrawal: 0.0
        actualsurfacewater: 20.0
        moisture: 0.1, 0.3, 0.1, 0.1
        frontdepth: 100.0, 50.0, 0.0, 0.0

        If possible, |Withdraw_AllBins_V1| withdraws only surface water:

        >>> check(demand=10.0, actualsurfacewater=20.0,
        ...       frontdepth=[100.0, 50.0, 0.0, 0.0],
        ...       moisture=[0.1, 0.3, 0.1, 0.1])
        withdrawal: 5.0
        actualsurfacewater: 15.0
        moisture: 0.1, 0.3, 0.1, 0.1
        frontdepth: 100.0, 50.0, 0.0, 0.0

        If no surface water is available, |Withdraw_AllBins_V1| tries to take all
        withdrawal from the wettest bin by reducing its relative moisture content:

        >>> check(demand=10.0, actualsurfacewater=0.0,
        ...       frontdepth=[100.0, 50.0, 0.0, 0.0],
        ...       moisture=[0.1, 0.3, 0.1, 0.1])
        withdrawal: 5.0
        actualsurfacewater: 0.0
        moisture: 0.1, 0.2, 0.1, 0.1
        frontdepth: 100.0, 50.0, 0.0, 0.0

        The following example shows that |Withdraw_AllBins_V1| still prefers surface
        water over soil water if the demand exceeds the available surface water:

        >>> check(demand=10.0, actualsurfacewater=2.5,
        ...       frontdepth=[100.0, 50.0, 0.0, 0.0],
        ...       moisture=[0.1, 0.3, 0.1, 0.1])
        withdrawal: 5.0
        actualsurfacewater: 0.0
        moisture: 0.1, 0.25, 0.1, 0.1
        frontdepth: 100.0, 50.0, 0.0, 0.0

        If the wettest bin does not contain enough water, |Withdraw_AllBins_V1|
        proceeds from right to left in taking the remaining demand:

        >>> check(demand=10.0, actualsurfacewater=0.0,
        ...       frontdepth=[100.0, 75.0, 50.0, 25.0],
        ...       moisture=[0.1, 0.2, 0.3, 0.4])
        withdrawal: 5.0
        actualsurfacewater: 0.0
        moisture: 0.1, 0.2, 0.25, 0.1
        frontdepth: 100.0, 75.0, 50.0, 0.0

        However, |Withdraw_AllBins_V1| never takes more water than indicated by soil's
        residual moisture:

        >>> check(demand=40.0, actualsurfacewater=0.0,
        ...       frontdepth=[100.0, 75.0, 50.0, 25.0],
        ...       moisture=[0.1, 0.2, 0.3, 0.4])
        withdrawal: 15.0
        actualsurfacewater: 0.0
        moisture: 0.1, 0.1, 0.1, 0.1
        frontdepth: 100.0, 0.0, 0.0, 0.0

        The last two examples show that |Withdraw_AllBins_V1| can also take water from
        the filled bin (if it is not already dry, as in the previous example):

        >>> check(demand=10.0, actualsurfacewater=0.0,
        ...       frontdepth=[100.0, 0.0, 0.0, 0.0],
        ...       moisture=[0.2, 0.2, 0.2, 0.2])
        withdrawal: 5.0
        actualsurfacewater: 0.0
        moisture: 0.15, 0.2, 0.2, 0.2
        frontdepth: 100.0, 0.0, 0.0, 0.0

        >>> check(demand=40.0, actualsurfacewater=0.0,
        ...       frontdepth=[100.0, 0.0, 0.0, 0.0],
        ...       moisture=[0.2, 0.2, 0.2, 0.2])
        withdrawal: 10.0
        actualsurfacewater: 0.0
        moisture: 0.1, 0.2, 0.2, 0.2
        frontdepth: 100.0, 0.0, 0.0, 0.0

        As the last examples show, |Withdraw_AllBins_V1| does not update the other
        bins' moisture after removing water from the filled bin, which is surprising
        but agrees with the author's GARTO source code and gave better results for
        shallow soils in some comparisons.
    """

    CONTROLPARAMETERS = (
        ga_control.NmbBins,
        ga_control.SoilDepth,
        ga_control.ResidualMoisture,
    )
    UPDATEDSEQUENCES = (
        ga_states.Moisture,
        ga_states.FrontDepth,
        ga_aides.ActualSurfaceWater,
        ga_fluxes.Withdrawal,
    )

    @staticmethod
    def __call__(model: modeltools.Model, s: int, demand: float) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess

        if demand <= 0.0:
            return

        if demand < aid.actualsurfacewater[s]:
            aid.actualsurfacewater[s] -= demand
            flu.withdrawal[s] += demand
            return
        demand -= aid.actualsurfacewater[s]
        flu.withdrawal[s] += aid.actualsurfacewater[s]
        aid.actualsurfacewater[s] = 0.0

        for b in range(con.nmbbins - 1, 0, -1):
            if sta.moisture[b, s] > sta.moisture[0, s]:
                available: float = sta.frontdepth[b, s] * (
                    sta.moisture[b, s] - sta.moisture[b - 1, s]
                )
                if demand <= available:
                    sta.moisture[b, s] -= demand / sta.frontdepth[b, s]
                    flu.withdrawal[s] += demand
                    return
                flu.withdrawal[s] += available
                demand -= available
                sta.moisture[b, s] = sta.moisture[0, s]
                sta.frontdepth[b, s] = 0.0

        if sta.moisture[0, s] <= con.residualmoisture[s]:
            return

        available = con.soildepth[s] * (sta.moisture[0, s] - con.residualmoisture[s])
        if demand <= available:
            sta.moisture[0, s] -= demand / con.soildepth[s]
            flu.withdrawal[s] += demand
        else:
            flu.withdrawal[s] += available
            sta.moisture[0, s] = con.residualmoisture[s]
        return


class Perform_GARTO_V1(modeltools.Method):
    r"""Perform the GARTO algorithm for the numerical substeps and aggregate their
    results.

    Method |Perform_GARTO_V1| executes its submethods |Percolate_FilledBin_V1|,
    |Infiltrate_WettingFrontBins_V1|, |Merge_FrontDepthOvershootings_V1|,
    |Merge_SoilDepthOvershootings_V1|, |Water_AllBins_V1|, and |Withdraw_AllBins_V1| in
    the order of mentioning on all non-sealed soil compartments.  Additionally, it
    converts surface water that cannot infiltrate (or evaporate) during a numerical
    substep immediately to surface runoff (no ponding).  So, it provides all core
    functionalities of application model |ga_garto|, and the explanations and test
    results for |ga_garto| essentially apply to |Perform_GARTO_V1|, too.
    """
    SUBMETHODS = (
        Return_LastActiveBin_V1,
        Return_Conductivity_V1,
        Return_DryDepth_V1,
        Return_CapillaryDrive_V1,
        Percolate_FilledBin_V1,
        Infiltrate_WettingFrontBins_V1,
        Merge_FrontDepthOvershootings_V1,
        Merge_SoilDepthOvershootings_V1,
        Water_AllBins_V1,
        Withdraw_AllBins_V1,
    )
    CONTROLPARAMETERS = (
        ga_control.NmbSoils,
        ga_control.NmbBins,
        ga_control.DT,
        ga_control.SoilDepth,
        ga_control.Sealed,
        ga_control.ResidualMoisture,
        ga_control.SaturationMoisture,
        ga_control.SaturatedConductivity,
        ga_control.AirEntryPotential,
        ga_control.PoreSizeDistribution,
    )
    DERIVEDPARAMETERS = (
        ga_derived.NmbSubsteps,
        ga_derived.EffectiveCapillarySuction,
    )
    REQUIREDSEQUENCES = (
        ga_fluxes.SurfaceWaterSupply,
        ga_fluxes.SoilWaterSupply,
        ga_fluxes.Demand,
    )
    UPDATEDSEQUENCES = (
        ga_aides.InitialSurfaceWater,
        ga_aides.ActualSurfaceWater,
        ga_states.Moisture,
        ga_states.FrontDepth,
        ga_logs.MoistureChange,
    )
    RESULTSEQUENCES = (
        ga_fluxes.Infiltration,
        ga_fluxes.Percolation,
        ga_fluxes.SoilWaterAddition,
        ga_fluxes.Withdrawal,
        ga_fluxes.SurfaceRunoff,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        aid = model.sequences.aides.fastaccess
        for s in range(con.nmbsoils):
            flu.percolation[s] = 0.0
            flu.infiltration[s] = 0.0
            flu.soilwateraddition[s] = 0.0
            if con.sealed[s]:
                if flu.demand[s] < flu.surfacewatersupply[s]:
                    flu.withdrawal[s] = flu.demand[s]
                    flu.surfacerunoff[s] = flu.surfacewatersupply[s] - flu.demand[s]
                else:
                    flu.withdrawal[s] = flu.surfacewatersupply[s]
                    flu.surfacerunoff[s] = 0.0
            else:
                aid.initialsurfacewater[s] = con.dt * flu.surfacewatersupply[s]
                flu.withdrawal[s] = 0.0
                flu.surfacerunoff[s] = 0.0
                for _ in range(der.nmbsubsteps):
                    aid.actualsurfacewater[s] = aid.initialsurfacewater[s]
                    model.percolate_filledbin_v1(s)
                    model.infiltrate_wettingfrontbins_v1(s)
                    flu.infiltration[s] += (
                        aid.initialsurfacewater[s] - aid.actualsurfacewater[s]
                    )
                    model.merge_frontdepthovershootings_v1(s)
                    model.merge_soildepthovershootings_v1(s)
                    model.water_allbins_v1(s, con.dt * flu.soilwatersupply[s])
                    model.withdraw_allbins_v1(s, con.dt * flu.demand[s])
                    flu.surfacerunoff[s] += aid.actualsurfacewater[s]


class Calc_TotalInfiltration_V1(modeltools.Method):
    r"""Calculate the average infiltration from all soil compartments.

    Basic equation:
      :math:`TotalInfiltration =
      \sum_{i=1}^{NmbSoils} SoilAreaFraction_i \cdot Infiltration_i`

    Example:

        >>> from hydpy.models.ga import *
        >>> parameterstep()
        >>> nmbsoils(2)
        >>> derived.soilareafraction(0.8, 0.2)
        >>> fluxes.infiltration = 1.0, 2.0
        >>> model.calc_totalinfiltration_v1()
        >>> fluxes.totalinfiltration
        totalinfiltration(1.2)
    """

    CONTROLPARAMETERS = (ga_control.NmbSoils,)
    DERIVEDPARAMETERS = (ga_derived.SoilAreaFraction,)
    REQUIREDSEQUENCES = (ga_fluxes.Infiltration,)
    RESULTSEQUENCES = (ga_fluxes.TotalInfiltration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess

        flu.totalinfiltration = 0.0
        for s in range(con.nmbsoils):
            flu.totalinfiltration += der.soilareafraction[s] * flu.infiltration[s]


class Calc_TotalPercolation_V1(modeltools.Method):
    r"""Calculate the average percolation from all soil compartments.

    Basic equation:
      :math:`TotalPercolation =
      \sum_{i=1}^{NmbSoils} SoilAreaFraction_i \cdot Percolation_i`

    Example:

        >>> from hydpy.models.ga import *
        >>> parameterstep()
        >>> nmbsoils(2)
        >>> derived.soilareafraction(0.8, 0.2)
        >>> fluxes.percolation = 1.0, 2.0
        >>> model.calc_totalpercolation_v1()
        >>> fluxes.totalpercolation
        totalpercolation(1.2)
    """

    CONTROLPARAMETERS = (ga_control.NmbSoils,)
    DERIVEDPARAMETERS = (ga_derived.SoilAreaFraction,)
    REQUIREDSEQUENCES = (ga_fluxes.Percolation,)
    RESULTSEQUENCES = (ga_fluxes.TotalPercolation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess

        flu.totalpercolation = 0.0
        for s in range(con.nmbsoils):
            flu.totalpercolation += der.soilareafraction[s] * flu.percolation[s]


class Calc_TotalSoilWaterAddition_V1(modeltools.Method):
    r"""Calculate the average soil water addition to all soil compartments.

    Basic equation:
      :math:`TotalSoilWaterAddition =
      \sum_{i=1}^{NmbSoils} SoilAreaFraction_i \cdot SoilWaterAddition_i`

    Example:

        >>> from hydpy.models.ga import *
        >>> parameterstep()
        >>> nmbsoils(2)
        >>> derived.soilareafraction(0.8, 0.2)
        >>> fluxes.soilwateraddition = 1.0, 2.0
        >>> model.calc_totalsoilwateraddition_v1()
        >>> fluxes.totalsoilwateraddition
        totalsoilwateraddition(1.2)
    """

    CONTROLPARAMETERS = (ga_control.NmbSoils,)
    DERIVEDPARAMETERS = (ga_derived.SoilAreaFraction,)
    REQUIREDSEQUENCES = (ga_fluxes.SoilWaterAddition,)
    RESULTSEQUENCES = (ga_fluxes.TotalSoilWaterAddition,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess

        flu.totalsoilwateraddition = 0.0
        for s in range(con.nmbsoils):
            flu.totalsoilwateraddition += (
                der.soilareafraction[s] * flu.soilwateraddition[s]
            )


class Calc_TotalWithdrawal_V1(modeltools.Method):
    r"""Calculate the average withdrawal from all soil compartments.

    Basic equation:
      :math:`TotalWithdrawal =
      \sum_{i=1}^{NmbSoils} SoilAreaFraction_i \cdot Withdrawal_i`

    Example:

        >>> from hydpy.models.ga import *
        >>> parameterstep()
        >>> nmbsoils(2)
        >>> derived.soilareafraction(0.8, 0.2)
        >>> fluxes.withdrawal = 1.0, 2.0
        >>> model.calc_totalwithdrawal_v1()
        >>> fluxes.totalwithdrawal
        totalwithdrawal(1.2)
    """

    CONTROLPARAMETERS = (ga_control.NmbSoils,)
    DERIVEDPARAMETERS = (ga_derived.SoilAreaFraction,)
    REQUIREDSEQUENCES = (ga_fluxes.Withdrawal,)
    RESULTSEQUENCES = (ga_fluxes.TotalWithdrawal,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess

        flu.totalwithdrawal = 0.0
        for s in range(con.nmbsoils):
            flu.totalwithdrawal += der.soilareafraction[s] * flu.withdrawal[s]


class Calc_TotalSurfaceRunoff_V1(modeltools.Method):
    r"""Calculate the average surface runoff from all soil compartments.

    Basic equation:
      :math:`TotalSurfaceRunoff =
      \sum_{i=1}^{NmbSoils} SoilAreaFraction_i \cdot SurfaceRunoff_i`

    Example:

        >>> from hydpy.models.ga import *
        >>> parameterstep()
        >>> nmbsoils(2)
        >>> derived.soilareafraction(0.8, 0.2)
        >>> fluxes.surfacerunoff = 1.0, 2.0
        >>> model.calc_totalsurfacerunoff_v1()
        >>> fluxes.totalsurfacerunoff
        totalsurfacerunoff(1.2)
    """

    CONTROLPARAMETERS = (ga_control.NmbSoils,)
    DERIVEDPARAMETERS = (ga_derived.SoilAreaFraction,)
    REQUIREDSEQUENCES = (ga_fluxes.SurfaceRunoff,)
    RESULTSEQUENCES = (ga_fluxes.TotalSurfaceRunoff,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess

        flu.totalsurfacerunoff = 0.0
        for s in range(con.nmbsoils):
            flu.totalsurfacerunoff += der.soilareafraction[s] * flu.surfacerunoff[s]


class Set_InitialSurfaceWater_V1(modeltools.Method):
    """Set the given initial surface water depth for the selected soil compartment.

    Example:

        Note that |Set_InitialSurfaceWater_V1| multiplies the given value with |DT| to
        adjust it to the numerical substep width:

        >>> from hydpy.models.ga import *
        >>> parameterstep()
        >>> nmbsoils(2)
        >>> dt.value = 0.5
        >>> model.set_initialsurfacewater_v1(0, 2.0)
        >>> model.set_initialsurfacewater_v1(1, 4.0)
        >>> aides.initialsurfacewater
        initialsurfacewater(1.0, 2.0)
    """

    CONTROLPARAMETERS = (ga_control.DT,)
    RESULTSEQUENCES = (ga_aides.InitialSurfaceWater,)

    @staticmethod
    def __call__(model: modeltools.Model, s: int, v: float) -> None:
        con = model.parameters.control.fastaccess
        aid = model.sequences.aides.fastaccess

        aid.initialsurfacewater[s] = con.dt * v


class Set_ActualSurfaceWater_V1(modeltools.Method):
    """Set the given actual surface water depth for the selected soil compartment.

    Example:

        Note that |Set_ActualSurfaceWater_V1| multiplies the given value with |DT| to
        adjust it to the numerical substep width:

        >>> from hydpy.models.ga import *
        >>> parameterstep()
        >>> nmbsoils(2)
        >>> dt.value = 0.5
        >>> model.set_actualsurfacewater_v1(0, 2.0)
        >>> model.set_actualsurfacewater_v1(1, 4.0)
        >>> aides.actualsurfacewater
        actualsurfacewater(1.0, 2.0)
    """

    CONTROLPARAMETERS = (ga_control.DT,)
    RESULTSEQUENCES = (ga_aides.ActualSurfaceWater,)

    @staticmethod
    def __call__(model: modeltools.Model, s: int, v: float) -> None:
        con = model.parameters.control.fastaccess
        aid = model.sequences.aides.fastaccess

        aid.actualsurfacewater[s] = con.dt * v


class Set_SoilWaterSupply_V1(modeltools.Method):
    """Set the (potential) water supply to the soil's body.

    Example:

        >>> from hydpy.models.ga import *
        >>> parameterstep()
        >>> nmbsoils(2)
        >>> model.set_soilwatersupply_v1(0, 2.0)
        >>> model.set_soilwatersupply_v1(1, 4.0)
        >>> fluxes.soilwatersupply
        soilwatersupply(2.0, 4.0)
    """

    RESULTSEQUENCES = (ga_fluxes.SoilWaterSupply,)

    @staticmethod
    def __call__(model: modeltools.Model, s: int, v: float) -> None:
        flu = model.sequences.fluxes.fastaccess

        flu.soilwatersupply[s] = v


class Set_SoilWaterDemand_V1(modeltools.Method):
    """Set the (potential) water withdrawal from the soil's surface and body.

    Example:

        >>> from hydpy.models.ga import *
        >>> parameterstep()
        >>> nmbsoils(2)
        >>> model.set_soilwaterdemand_v1(0, 2.0)
        >>> model.set_soilwaterdemand_v1(1, 4.0)
        >>> fluxes.demand
        demand(2.0, 4.0)
    """

    RESULTSEQUENCES = (ga_fluxes.Demand,)

    @staticmethod
    def __call__(model: modeltools.Model, s: int, v: float) -> None:
        flu = model.sequences.fluxes.fastaccess

        flu.demand[s] = v


class Execute_Infiltration_V1(modeltools.Method):
    """Calculate infiltration (and percolation).

    The interface method |Execute_Infiltration_V1| subsequently executes the GARTO
    methods |Percolate_FilledBin_V1|, |Infiltrate_WettingFrontBins_V1|,
    |Merge_FrontDepthOvershootings_V1|, and |Merge_SoilDepthOvershootings_V1| for all
    numerical substeps.
    """

    SUBMETHODS = (
        Return_LastActiveBin_V1,
        Return_Conductivity_V1,
        Return_DryDepth_V1,
        Return_CapillaryDrive_V1,
        Percolate_FilledBin_V1,
        Infiltrate_WettingFrontBins_V1,
        Merge_FrontDepthOvershootings_V1,
        Merge_SoilDepthOvershootings_V1,
    )
    CONTROLPARAMETERS = (
        ga_control.NmbBins,
        ga_control.DT,
        ga_control.SoilDepth,
        ga_control.ResidualMoisture,
        ga_control.SaturationMoisture,
        ga_control.SaturatedConductivity,
        ga_control.AirEntryPotential,
        ga_control.PoreSizeDistribution,
    )
    DERIVEDPARAMETERS = (
        ga_derived.NmbSubsteps,
        ga_derived.EffectiveCapillarySuction,
    )
    REQUIREDSEQUENCES = (ga_aides.InitialSurfaceWater,)
    UPDATEDSEQUENCES = (
        ga_aides.ActualSurfaceWater,
        ga_states.Moisture,
        ga_states.FrontDepth,
        ga_logs.MoistureChange,
    )
    RESULTSEQUENCES = (
        ga_fluxes.Infiltration,
        ga_fluxes.Percolation,
        ga_fluxes.SurfaceRunoff,
    )

    @staticmethod
    def __call__(model: modeltools.Model, s: int) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        aid = model.sequences.aides.fastaccess

        initialactualsurfacewater: float = aid.actualsurfacewater[s]
        flu.infiltration[s] = 0.0
        flu.percolation[s] = 0.0
        flu.surfacerunoff[s] = 0.0
        for _ in range(der.nmbsubsteps):
            aid.actualsurfacewater[s] = initialactualsurfacewater
            model.percolate_filledbin_v1(s)
            model.infiltrate_wettingfrontbins_v1(s)
            flu.infiltration[s] += initialactualsurfacewater - aid.actualsurfacewater[s]
            model.merge_frontdepthovershootings_v1(s)
            model.merge_soildepthovershootings_v1(s)
            flu.surfacerunoff[s] += aid.actualsurfacewater[s]
        aid.actualsurfacewater[s] = 0.0


class Add_SoilWater_V1(modeltools.Method):
    """Add the (direct) soil water supply to the soil's body.

    The interface method |Add_SoilWater_V1| only calls |Withdraw_AllBins_V1|.
    """

    SUBMETHODS = (Water_AllBins_V1,)
    CONTROLPARAMETERS = (
        ga_control.NmbBins,
        ga_control.SoilDepth,
        ga_control.SaturationMoisture,
    )
    REQUIREDSEQUENCES = (ga_fluxes.SoilWaterSupply,)
    UPDATEDSEQUENCES = (
        ga_states.FrontDepth,
        ga_states.Moisture,
        ga_logs.MoistureChange,
    )
    RESULTSEQUENCES = (ga_fluxes.SoilWaterAddition,)

    @staticmethod
    def __call__(model: modeltools.Model, s: int) -> None:
        flu = model.sequences.fluxes.fastaccess

        flu.soilwateraddition[s] = 0.0
        model.water_allbins_v1(s, flu.soilwatersupply[s])


class Remove_SoilWater_V1(modeltools.Method):
    """Remove the water demand from the soil's body and eventually from the soil's
    surface.

    The interface method |Remove_SoilWater_V1| only calls |Withdraw_AllBins_V1|.
    Hence, whether |Remove_SoilWater_V1| can remove surface water depends on the order
    the different interface methods are applied and is thus a decision of the calling
    model.
    """

    SUBMETHODS = (Withdraw_AllBins_V1,)
    CONTROLPARAMETERS = (
        ga_control.NmbBins,
        ga_control.SoilDepth,
        ga_control.ResidualMoisture,
    )
    REQUIREDSEQUENCES = (ga_fluxes.Demand,)
    UPDATEDSEQUENCES = (
        ga_aides.ActualSurfaceWater,
        ga_states.FrontDepth,
        ga_states.Moisture,
    )
    RESULTSEQUENCES = (ga_fluxes.Withdrawal,)

    @staticmethod
    def __call__(model: modeltools.Model, s: int) -> None:
        flu = model.sequences.fluxes.fastaccess
        aid = model.sequences.aides.fastaccess

        aid.actualsurfacewater[s] = 0.0
        flu.withdrawal[s] = 0.0
        model.withdraw_allbins_v1(s, flu.demand[s])


class Get_Infiltration_V1(modeltools.Method):
    """Get the current infiltration to the selected soil compartment.

    Example:

        >>> from hydpy.models.ga import *
        >>> parameterstep()
        >>> nmbsoils(2)
        >>> fluxes.infiltration = 2.0, 4.0
        >>> model.get_infiltration_v1(0)
        2.0
        >>> model.get_infiltration_v1(1)
        4.0
    """

    RESULTSEQUENCES = (ga_fluxes.Infiltration,)

    @staticmethod
    def __call__(model: modeltools.Model, s: int) -> float:
        flu = model.sequences.fluxes.fastaccess

        return flu.infiltration[s]


class Get_Percolation_V1(modeltools.Method):
    """Get the current percolation from the selected soil compartment.

    Example:

        >>> from hydpy.models.ga import *
        >>> parameterstep()
        >>> nmbsoils(2)
        >>> fluxes.percolation = 2.0, 4.0
        >>> model.get_percolation_v1(0)
        2.0
        >>> model.get_percolation_v1(1)
        4.0
    """

    RESULTSEQUENCES = (ga_fluxes.Percolation,)

    @staticmethod
    def __call__(model: modeltools.Model, s: int) -> float:
        flu = model.sequences.fluxes.fastaccess

        return flu.percolation[s]


class Get_SoilWaterAddition_V1(modeltools.Method):
    """Get the current soil water addition to the selected soil compartment.

    Example:

        >>> from hydpy.models.ga import *
        >>> parameterstep()
        >>> nmbsoils(2)
        >>> fluxes.soilwateraddition = 2.0, 4.0
        >>> model.get_soilwateraddition_v1(0)
        2.0
        >>> model.get_soilwateraddition_v1(1)
        4.0
    """

    RESULTSEQUENCES = (ga_fluxes.SoilWaterAddition,)

    @staticmethod
    def __call__(model: modeltools.Model, s: int) -> float:
        flu = model.sequences.fluxes.fastaccess

        return flu.soilwateraddition[s]


class Get_SoilWaterRemoval_V1(modeltools.Method):
    """Get the current soil (and surface water) withdrawal from the selected soil
    compartment.

    Example:

        >>> from hydpy.models.ga import *
        >>> parameterstep()
        >>> nmbsoils(2)
        >>> fluxes.withdrawal = 2.0, 4.0
        >>> model.get_soilwaterremoval_v1(0)
        2.0
        >>> model.get_soilwaterremoval_v1(1)
        4.0
    """

    RESULTSEQUENCES = (ga_fluxes.Withdrawal,)

    @staticmethod
    def __call__(model: modeltools.Model, s: int) -> float:
        flu = model.sequences.fluxes.fastaccess

        return flu.withdrawal[s]


class Get_SoilWaterContent_V1(modeltools.Method):
    r"""Get the current soil water content of the selected soil compartment.

    Basic equation:
      :math:`SoilWaterContent = Moisture_1 \cdot SoilDepth +
      \sum_{i=2}^{NmbBins} (Moisture_i - Moisture_{i-1}) \cdot FrontDepth_i`

    Example:

        >>> from hydpy.models.ga import *
        >>> parameterstep()
        >>> nmbsoils(3)
        >>> nmbbins(4)
        >>> sealed(False, False, True)
        >>> soilarea(1.0, 2.0, 3.0)
        >>> soildepth(100.0, 200, nan)
        >>> residualmoisture(0.1, 0.2, nan)
        >>> saturationmoisture(0.5, 0.8, nan)
        >>> states.moisture = [[0.3, 0.2, nan],
        ...                    [0.3, 0.3, nan],
        ...                    [0.3, 0.5, nan],
        ...                    [0.3, 0.8, nan]]
        >>> states.frontdepth = [[100.0, 200.0, nan],
        ...                      [0.0, 150.0, nan],
        ...                      [0.0, 100.0, nan],
        ...                      [0.0, 50.0, nan]]
        >>> from hydpy import round_
        >>> round_(model.get_soilwatercontent_v1(0))
        30.0
        >>> round_(model.get_soilwatercontent_v1(1))
        90.0
        >>> round_(model.get_soilwatercontent_v1(2))
        0.0
    """

    CONTROLPARAMETERS = (
        ga_control.NmbBins,
        ga_control.Sealed,
        ga_control.SoilDepth,
    )
    REQUIREDSEQUENCES = (
        ga_states.Moisture,
        ga_states.FrontDepth,
    )

    @staticmethod
    def __call__(model: modeltools.Model, s: int) -> float:
        con = model.parameters.control.fastaccess
        sta = model.sequences.states.fastaccess

        if con.sealed[s]:
            return 0.0
        wc: float = con.soildepth[s] * sta.moisture[0, s]
        for b in range(1, con.nmbbins):
            if sta.moisture[b, s] == sta.moisture[0, s]:
                break
            wc += sta.frontdepth[b, s] * (sta.moisture[b, s] - sta.moisture[b - 1, s])
        return wc


class Model(modeltools.AdHocModel):
    r"""The Green-Ampt base model."""

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        Calc_SurfaceWaterSupply_V1,
        Calc_SoilWaterSupply_V1,
        Calc_Demand_V1,
        Perform_GARTO_V1,
        Calc_TotalInfiltration_V1,
        Calc_TotalPercolation_V1,
        Calc_TotalSoilWaterAddition_V1,
        Calc_TotalWithdrawal_V1,
        Calc_TotalSurfaceRunoff_V1,
    )
    INTERFACE_METHODS = (
        Set_InitialSurfaceWater_V1,
        Set_ActualSurfaceWater_V1,
        Set_SoilWaterSupply_V1,
        Set_SoilWaterDemand_V1,
        Execute_Infiltration_V1,
        Add_SoilWater_V1,
        Remove_SoilWater_V1,
        Get_Infiltration_V1,
        Get_Percolation_V1,
        Get_SoilWaterAddition_V1,
        Get_SoilWaterRemoval_V1,
        Get_SoilWaterContent_V1,
    )
    ADD_METHODS = (
        Return_RelativeMoisture_V1,
        Return_Conductivity_V1,
        Return_CapillaryDrive_V1,
        Return_DryDepth_V1,
        Return_LastActiveBin_V1,
        Active_Bin_V1,
        Percolate_FilledBin_V1,
        Shift_Front_V1,
        Redistribute_Front_V1,
        Infiltrate_WettingFrontBins_V1,
        Merge_FrontDepthOvershootings_V1,
        Merge_SoilDepthOvershootings_V1,
        Water_AllBins_V1,
        Withdraw_AllBins_V1,
    )
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()


class MixinGARTO:
    """Mixin class for GARTO-like Green-Ampt models."""

    def check_waterbalance(
        self,
        initial_conditions: Dict[str, Dict[str, ArrayFloat]],
    ) -> float:
        r"""Determine the water balance error of the previous simulation run in mm.

        Method |MixinGARTO.check_waterbalance| calculates the balance error as follows:

        :math:`\sum_{t=t0}^{t1} \big(
        Rainfall_t - TotalPercolation_t  + TotalSoilWaterAddition_t - TotalWithdrawal_t
        - Percolation_t \big) +b\big( WaterVolume_{t0} - WaterVolume_{t1} \big)`

        The returned error should always be in scale with numerical precision so that
        it does not affect the simulation results in any relevant manner.

        Pick the required initial conditions before starting the simulation via
        property |Sequences.conditions|.  See the integration tests of the application
        model |ga_garto| for some examples.
        """
        inputs = self.sequences.inputs
        fluxes = self.sequences.fluxes
        old_watercontent = self._calc_watercontent(
            frontdepth=initial_conditions["states"]["frontdepth"],  # type: ignore[arg-type]  # pylint: disable=line-too-long
            moisture=initial_conditions["states"]["moisture"],  # type: ignore[arg-type]  # pylint: disable=line-too-long
        )
        return float(
            numpy.sum(inputs.rainfall.evalseries)
            + numpy.sum(fluxes.totalsoilwateraddition.evalseries)
            - numpy.sum(fluxes.totalpercolation.evalseries)
            - numpy.sum(fluxes.totalwithdrawal.evalseries)
            - numpy.sum(fluxes.totalsurfacerunoff.evalseries)
            + (old_watercontent - self.watercontent)
        )

    @property
    def watercontents(self) -> NDArrayFloat:
        """The unique water content of each soil compartment in mm.

        Property |MixinGARTO.watercontents| generally returns zero values for sealed
        soil compartments:

        >>> from hydpy.models.ga_garto import *
        >>> parameterstep()
        >>> nmbsoils(3)
        >>> nmbbins(4)
        >>> sealed(False, False, True)
        >>> soilarea(1.0, 2.0, 3.0)
        >>> soildepth(100.0, 200, nan)
        >>> residualmoisture(0.1, 0.2, nan)
        >>> saturationmoisture(0.5, 0.8, nan)
        >>> derived.soilareafraction.update()
        >>> states.moisture = [[0.3, 0.2, nan],
        ...                    [0.3, 0.3, nan],
        ...                    [0.3, 0.5, nan],
        ...                    [0.3, 0.8, nan]]
        >>> states.frontdepth = [[100.0, 200.0, nan],
        ...                      [0.0, 150.0, nan],
        ...                      [0.0, 100.0, nan],
        ...                      [0.0, 50.0, nan]]
        >>> from hydpy import print_values
        >>> print_values(model.watercontents)
        30.0, 90.0, 0.0
        """
        states = self.sequences.states
        return self._calc_watercontents(
            frontdepth=states.frontdepth.values, moisture=states.moisture.values
        )

    @property
    def watercontent(self) -> float:
        """The average water content of all soil compartments in mm.

        Property |MixinGARTO.watercontent| includes sealed soil compartments in the
        average, which is why the presence of sealing reduces the returned value:

        >>> from hydpy.models.ga_garto import *
        >>> parameterstep()
        >>> nmbsoils(3)
        >>> nmbbins(4)
        >>> sealed(False, False, True)
        >>> soilarea(1.0, 2.0, 3.0)
        >>> soildepth(100.0, 200, nan)
        >>> residualmoisture(0.1, 0.2, nan)
        >>> saturationmoisture(0.5, 0.8, nan)
        >>> derived.soilareafraction.update()
        >>> states.moisture = [[0.3, 0.2, nan],
        ...                    [0.3, 0.3, nan],
        ...                    [0.3, 0.5, nan],
        ...                    [0.3, 0.8, nan]]
        >>> states.frontdepth = [[100.0, 200.0, nan],
        ...                      [0.0, 150.0, nan],
        ...                      [0.0, 100.0, nan],
        ...                      [0.0, 50.0, nan]]
        >>> from hydpy import round_
        >>> round_(model.watercontent)
        35.0

        >>> soilarea(1.0, 2.0, 0.0)
        >>> derived.soilareafraction.update()
        >>> round_(model.watercontent)
        70.0
        """
        states = self.sequences.states
        return self._calc_watercontent(
            frontdepth=states.frontdepth.values, moisture=states.moisture.values
        )

    def _calc_watercontents(
        self, frontdepth: NDArrayFloat, moisture: NDArrayFloat
    ) -> NDArrayFloat:
        frontdepth = frontdepth.copy()
        frontdepth[0, :] = self.parameters.control.soildepth.values
        deltamoisture = numpy.diff(moisture, axis=0, prepend=0.0)
        deltamoisture = numpy.clip(deltamoisture, 0.0, numpy.inf)
        watercontents = numpy.sum(frontdepth * deltamoisture, axis=0)
        watercontents[self.parameters.control.sealed.values] = 0.0
        return watercontents

    def _calc_watercontent(
        self, frontdepth: NDArrayFloat, moisture: NDArrayFloat
    ) -> float:
        weights = self.parameters.derived.soilareafraction.values
        watercontents = self._calc_watercontents(
            frontdepth=frontdepth, moisture=moisture
        )
        return numpy.nansum(weights * watercontents)


class Base_SoilModel_V1(modeltools.AdHocModel, soilinterfaces.SoilModel_V1):
    """Base class for HydPy-GA models that comply with the |SoilModel_V1| submodel
    interface."""

    @importtools.define_targetparameter(ga_control.NmbSoils)
    def prepare_nmbzones(self, nmbzones: int) -> None:
        """Set the number of soil compartments.

        >>> from hydpy.models.ga_garto_submodel1 import *
        >>> parameterstep()
        >>> model.prepare_nmbzones(2)
        >>> nmbsoils
        nmbsoils(2)
        """
        self.parameters.control.nmbsoils(nmbzones)
