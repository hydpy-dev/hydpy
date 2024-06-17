# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# imports...
# ...from HydPy
from hydpy.core import importtools
from hydpy.core import modeltools
from hydpy.cythons import modelutils
from hydpy.cythons import smoothutils
from hydpy.interfaces import petinterfaces
from hydpy.interfaces import precipinterfaces
from hydpy.models.dam import dam_control
from hydpy.models.dam import dam_derived
from hydpy.models.dam import dam_solver
from hydpy.models.dam import dam_factors
from hydpy.models.dam import dam_fluxes
from hydpy.models.dam import dam_states
from hydpy.models.dam import dam_logs
from hydpy.models.dam import dam_aides
from hydpy.models.dam import dam_inlets
from hydpy.models.dam import dam_receivers
from hydpy.models.dam import dam_outlets
from hydpy.models.dam import dam_senders
from hydpy.core.typingtools import *


class Calc_Precipitation_V1(modeltools.Method):
    """If available, let a submodel that complies with the |PrecipModel_V2| interface
    determine precipitation.

    Examples:

        We use |dam_v001| as an example:

        >>> from hydpy.models.dam_v001 import *
        >>> parameterstep()

        Without a submodel, |Calc_Precipitation_V1| generally sets precipitation to
        zero:

        >>> model.calc_precipitation_v1()
        >>> fluxes.precipitation
        precipitation(0.0)

        Otherwise, it triggers the determination and queries the resulting value from
        the available submodel:

        >>> surfacearea(2.0)
        >>> with model.add_precipmodel_v2("meteo_precip_io"):
        ...     precipitationfactor(1.1)
        ...     inputs.precipitation = 3.0
        >>> model.calc_precipitation_v1()
        >>> fluxes.precipitation
        precipitation(3.3)
    """

    RESULTSEQUENCES = (dam_fluxes.Precipitation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess

        if model.precipmodel is None:
            flu.precipitation = 0.0
        elif model.precipmodel_typeid == 2:
            cast(
                precipinterfaces.PrecipModel_V2, model.precipmodel
            ).determine_precipitation()
            flu.precipitation = cast(
                precipinterfaces.PrecipModel_V2, model.precipmodel
            ).get_precipitation(0)


class Calc_AdjustedPrecipitation_V1(modeltools.Method):
    r"""Adjust the given precipitation.

    Basic equation:
      :math:`AdjustedPrecipitation =
      InputFactor \cdot CorrectionPrecipitation \cdot Precipitation`

    Example:

        >>> from hydpy.models.dam import *
        >>> simulationstep("1h")
        >>> parameterstep()
        >>> surfacearea(36.0)
        >>> correctionprecipitation(1.25)
        >>> derived.seconds.update()
        >>> derived.inputfactor.update()
        >>> fluxes.precipitation = 2.0
        >>> model.calc_adjustedprecipitation_v1()
        >>> fluxes.adjustedprecipitation
        adjustedprecipitation(25.0)
    """

    CONTROLPARAMETERS = (dam_control.CorrectionPrecipitation,)
    DERIVEDPARAMETERS = (dam_derived.InputFactor,)
    REQUIREDSEQUENCES = (dam_fluxes.Precipitation,)
    RESULTSEQUENCES = (dam_fluxes.AdjustedPrecipitation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.adjustedprecipitation = (
            der.inputfactor * con.correctionprecipitation * flu.precipitation
        )


class Calc_PotentialEvaporation_V1(modeltools.Method):
    """If available, let a submodel that complies with the |PETModel_V1| interface
    determine potential evaporation.

    Examples:

        We use |dam_v001| as an example:

        >>> from hydpy.models.dam_v001 import *
        >>> parameterstep()

        Without a submodel, |Calc_PotentialEvaporation_V1| generally sets potential
        evaporation to zero:

        >>> model.calc_potentialevaporation_v1()
        >>> fluxes.potentialevaporation
        potentialevaporation(0.0)

        Otherwise, it triggers the determination and queries the resulting value from
        the available submodel:

        >>> surfacearea(2.0)
        >>> with model.add_pemodel_v1("evap_ret_io"):
        ...     evapotranspirationfactor(1.1)
        ...     inputs.referenceevapotranspiration = 3.0
        >>> model.calc_potentialevaporation_v1()
        >>> fluxes.potentialevaporation
        potentialevaporation(3.3)
    """

    RESULTSEQUENCES = (dam_fluxes.PotentialEvaporation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess

        if model.pemodel is None:
            flu.potentialevaporation = 0.0
        elif model.pemodel_typeid == 1:
            cast(
                petinterfaces.PETModel_V1, model.pemodel
            ).determine_potentialevapotranspiration()
            flu.potentialevaporation = cast(
                petinterfaces.PETModel_V1, model.pemodel
            ).get_potentialevapotranspiration(0)


class Calc_AdjustedEvaporation_V1(modeltools.Method):
    r"""Adjust the given potential evaporation.

    Basic equation:
      :math:`AdjustedEvaporation = WeightEvaporation \cdot InputFactor \cdot
      CorrectionEvaporation \cdot PotentialEvaporation
      + (1 - WeightEvaporation) \cdot LoggedAdjustedEvaporation`

    Examples:

        Besides transforming units (mm/T to m³/s), method |Calc_AdjustedEvaporation_V1|
        modifies the given potential evaporation values in two ways.  First, it
        increases or reduces its general level via parameter |CorrectionEvaporation|
        and, second, it delays and damps its variability via parameter
        |WeightEvaporation|.  We begin with the first functionality by setting the
        correction factor to 1.25 and the weighting factor to 1.0:

        >>> from hydpy.models.dam import *
        >>> simulationstep("1h")
        >>> parameterstep("1h")
        >>> surfacearea(36.0)
        >>> correctionevaporation(1.25)
        >>> weightevaporation(1.0)
        >>> derived.seconds.update()
        >>> derived.inputfactor.update()
        >>> fluxes.potentialevaporation = 2.0
        >>> logs.loggedadjustedevaporation = 20.0
        >>> model.calc_adjustedevaporation_v1()
        >>> fluxes.adjustedevaporation
        adjustedevaporation(25.0)

        Note that method |Calc_AdjustedEvaporation_V1| also updates the log sequence
        |LoggedAdjustedEvaporation| with the same value as flux sequence
        |AdjustedEvaporation|:

        >>> logs.loggedadjustedevaporation
        loggedadjustedevaporation(25.0)

        Setting the weighting factor to a value smaller one activates the damping-delay
        mechanism.  A value of 0.6 implies a weighting of 60 % of the "new" evaporation
        value (here: 2.0 mm/h or 25 m³/s) and of 40 % of the "old" evaporation value
        (here: 1.6 mm/h or 20 m³/s):

        >>> weightevaporation(0.6)
        >>> logs.loggedadjustedevaporation = 20.0
        >>> model.calc_adjustedevaporation_v1()
        >>> fluxes.adjustedevaporation
        adjustedevaporation(23.0)
        >>> logs.loggedadjustedevaporation
        loggedadjustedevaporation(23.0)
    """

    CONTROLPARAMETERS = (
        dam_control.CorrectionEvaporation,
        dam_control.WeightEvaporation,
    )
    DERIVEDPARAMETERS = (dam_derived.InputFactor,)
    REQUIREDSEQUENCES = (dam_fluxes.PotentialEvaporation,)
    UPDATEDSEQUENCES = (dam_logs.LoggedAdjustedEvaporation,)
    RESULTSEQUENCES = (dam_fluxes.AdjustedEvaporation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        d_weight = con.weightevaporation
        d_new = der.inputfactor * con.correctionevaporation * flu.potentialevaporation
        d_old = log.loggedadjustedevaporation[0]
        flu.adjustedevaporation = d_weight * d_new + (1.0 - d_weight) * d_old
        log.loggedadjustedevaporation[0] = flu.adjustedevaporation


class Calc_ActualEvaporation_V1(modeltools.Method):
    r"""Calculate the actual evaporation.

    Basic equation:
      :math:`ActualEvaporation = AdjustedEvaporation \cdot
      smooth_{logistic1}(ThresholdEvaporation - WaterLevel, SmoothParEvaporation)`

    Used auxiliary method:
      |smooth_logistic1|

    Examples:

        First, we prepare a |UnitTest| object to illustrate the relationship between
        the water level and actual evaporation for different settings:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> fluxes.adjustedevaporation = 2.0
        >>> from hydpy import UnitTest
        >>> test = UnitTest(model, model.calc_actualevaporation_v1,
        ...                 last_example=10,
        ...                 parseqs=(factors.waterlevel,
        ...                          fluxes.actualevaporation))
        >>> test.nexts.waterlevel = [value / 1000.0 for value in range(-1, 9)]

        The most intuitive way to configure method |Calc_ActualEvaporation_V1| is to
        set |WaterLevelMinimumThreshold| and |WaterLevelMinimumTolerance| to zero.
        Then, there is a sharp transition between zero and potential evaporation around
        a water level of 0 m:

        >>> thresholdevaporation(0.0)
        >>> toleranceevaporation(0.0)
        >>> derived.smoothparevaporation.update()

        >>> test()
        | ex. | waterlevel | actualevaporation |
        ----------------------------------------
        |   1 |     -0.001 |               0.0 |
        |   2 |        0.0 |               1.0 |
        |   3 |      0.001 |               2.0 |
        |   4 |      0.002 |               2.0 |
        |   5 |      0.003 |               2.0 |
        |   6 |      0.004 |               2.0 |
        |   7 |      0.005 |               2.0 |
        |   8 |      0.006 |               2.0 |
        |   9 |      0.007 |               2.0 |
        |  10 |      0.008 |               2.0 |

        For numerical efficiency (and more natural transitions), it is  preferable to
        set |WaterLevelMinimumTolerance| to a value larger than zero.  Here, we set it
        to 1 mm and adjust |WaterLevelMinimumThreshold| so that the actual evaporation
        values are (at least for the shown precision) zero below a water level of 0 mm:

        >>> thresholdevaporation(0.004)
        >>> toleranceevaporation(0.001)
        >>> derived.smoothparevaporation.update()
        >>> test()
        | ex. | waterlevel | actualevaporation |
        ----------------------------------------
        |   1 |     -0.001 |               0.0 |
        |   2 |        0.0 |               0.0 |
        |   3 |      0.001 |          0.000002 |
        |   4 |      0.002 |          0.000204 |
        |   5 |      0.003 |              0.02 |
        |   6 |      0.004 |               1.0 |
        |   7 |      0.005 |              1.98 |
        |   8 |      0.006 |          1.999796 |
        |   9 |      0.007 |          1.999998 |
        |  10 |      0.008 |               2.0 |
    """

    CONTROLPARAMETERS = (dam_control.ThresholdEvaporation,)
    DERIVEDPARAMETERS = (dam_derived.SmoothParEvaporation,)
    REQUIREDSEQUENCES = (dam_fluxes.AdjustedEvaporation, dam_factors.WaterLevel)
    RESULTSEQUENCES = (dam_fluxes.ActualEvaporation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.actualevaporation = flu.adjustedevaporation * smoothutils.smooth_logistic1(
            fac.waterlevel - con.thresholdevaporation, der.smoothparevaporation
        )


class Pic_Inflow_V1(modeltools.Method):
    """Update the inlet sequence |Inflow|.

    Basic equation:
      :math:`Inflow = \\sum Q`
    """

    REQUIREDSEQUENCES = (dam_inlets.Q,)
    RESULTSEQUENCES = (dam_fluxes.Inflow,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        inl = model.sequences.inlets.fastaccess
        flu.inflow = 0.0
        for idx in range(inl.len_q):
            flu.inflow += inl.q[idx][0]


class Pic_Inflow_V2(modeltools.Method):
    """Update the inlet sequence |Inflow|.

    Basic equation:
      :math:`Inflow = S + R + \\sum Q`
    """

    REQUIREDSEQUENCES = (dam_inlets.Q, dam_inlets.S, dam_inlets.R)
    RESULTSEQUENCES = (dam_fluxes.Inflow,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        inl = model.sequences.inlets.fastaccess
        flu.inflow = inl.s[0] + inl.r[0]
        for idx in range(inl.len_q):
            flu.inflow += inl.q[idx][0]


class Pic_TotalRemoteDischarge_V1(modeltools.Method):
    """Update the receiver sequence |TotalRemoteDischarge|.

    Basic equation:
      :math:`TotalRemoteDischarge = Q`
    """

    REQUIREDSEQUENCES = (dam_receivers.Q,)
    RESULTSEQUENCES = (dam_fluxes.TotalRemoteDischarge,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        rec = model.sequences.receivers.fastaccess
        flu.totalremotedischarge = rec.q[0]


class Pick_LoggedOuterWaterLevel_V1(modeltools.Method):
    """Update the receiver sequence |LoggedOuterWaterLevel|.

    Basic equation:
      :math:`LoggedOuterWaterLevel = OWL`
    """

    REQUIREDSEQUENCES = (dam_receivers.OWL,)
    RESULTSEQUENCES = (dam_logs.LoggedOuterWaterLevel,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        log = model.sequences.logs.fastaccess
        rec = model.sequences.receivers.fastaccess
        log.loggedouterwaterlevel[0] = rec.owl[0]


class Pick_LoggedRemoteWaterLevel_V1(modeltools.Method):
    """Update the receiver sequence |LoggedRemoteWaterLevel|.

    Basic equation:
      :math:`LoggedRemoteWaterLevel = RWL`
    """

    REQUIREDSEQUENCES = (dam_receivers.RWL,)
    RESULTSEQUENCES = (dam_logs.LoggedRemoteWaterLevel,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        log = model.sequences.logs.fastaccess
        rec = model.sequences.receivers.fastaccess
        log.loggedremotewaterlevel[0] = rec.rwl[0]


class Pic_LoggedRequiredRemoteRelease_V1(modeltools.Method):
    """Update the receiver sequence |LoggedRequiredRemoteRelease|.

    Basic equation:
      :math:`LoggedRequiredRemoteRelease = D`
    """

    REQUIREDSEQUENCES = (dam_receivers.D,)
    RESULTSEQUENCES = (dam_logs.LoggedRequiredRemoteRelease,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        log = model.sequences.logs.fastaccess
        rec = model.sequences.receivers.fastaccess
        log.loggedrequiredremoterelease[0] = rec.d[0]


class Pic_LoggedRequiredRemoteRelease_V2(modeltools.Method):
    """Update the receiver sequence |LoggedRequiredRemoteRelease|.

    Basic equation:
      :math:`LoggedRequiredRemoteRelease = S`
    """

    REQUIREDSEQUENCES = (dam_receivers.S,)
    RESULTSEQUENCES = (dam_logs.LoggedRequiredRemoteRelease,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        log = model.sequences.logs.fastaccess
        rec = model.sequences.receivers.fastaccess
        log.loggedrequiredremoterelease[0] = rec.s[0]


class Pic_Exchange_V1(modeltools.Method):
    r"""Update the inlet sequence |Exchange|.

    Basic equation:
      :math:`Exchange = \sum E_{inlets}`
    """

    REQUIREDSEQUENCES = (dam_inlets.E,)
    RESULTSEQUENCES = (dam_fluxes.Exchange,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        inl = model.sequences.inlets.fastaccess
        flu.exchange = 0.0
        for idx in range(inl.len_e):
            flu.exchange += inl.e[idx][0]


class Pic_LoggedAllowedRemoteRelief_V1(modeltools.Method):
    """Update the receiver sequence |LoggedAllowedRemoteRelief|.

    Basic equation:
      :math:`LoggedAllowedRemoteRelief = R`
    """

    REQUIREDSEQUENCES = (dam_receivers.R,)
    RESULTSEQUENCES = (dam_logs.LoggedAllowedRemoteRelief,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        log = model.sequences.logs.fastaccess
        rec = model.sequences.receivers.fastaccess
        log.loggedallowedremoterelief[0] = rec.r[0]


class Update_LoggedTotalRemoteDischarge_V1(modeltools.Method):
    """Log a new entry of the discharge at a cross-section far downstream.

    Example:

        The following example shows that method |Update_LoggedTotalRemoteDischarge_V1|
        moves the three memorised values successively to the right and stores the
        respective new value on the bare left position:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> nmblogentries(3)
        >>> logs.loggedtotalremotedischarge = 0.0
        >>> from hydpy import UnitTest
        >>> test = UnitTest(model, model.update_loggedtotalremotedischarge_v1,
        ...                 last_example=4,
        ...                 parseqs=(fluxes.totalremotedischarge,
        ...                          logs.loggedtotalremotedischarge))
        >>> test.nexts.totalremotedischarge = [1.0, 3.0, 2.0, 4.0]
        >>> del test.inits.loggedtotalremotedischarge
        >>> test()
        | ex. | totalremotedischarge |           loggedtotalremotedischarge |
        ---------------------------------------------------------------------
        |   1 |                  1.0 | 1.0  0.0                         0.0 |
        |   2 |                  3.0 | 3.0  1.0                         0.0 |
        |   3 |                  2.0 | 2.0  3.0                         1.0 |
        |   4 |                  4.0 | 4.0  2.0                         3.0 |
    """

    CONTROLPARAMETERS = (dam_control.NmbLogEntries,)
    REQUIREDSEQUENCES = (dam_fluxes.TotalRemoteDischarge,)
    UPDATEDSEQUENCES = (dam_logs.LoggedTotalRemoteDischarge,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        for i in range(con.nmblogentries - 1, 0, -1):
            log.loggedtotalremotedischarge[i] = log.loggedtotalremotedischarge[i - 1]
        log.loggedtotalremotedischarge[0] = flu.totalremotedischarge


class Calc_WaterLevel_V1(modeltools.Method):
    """Determine the water level based on an interpolation approach approximating the
    relationship between water volume and water level.

    Example:

        We prepare a straightforward relationship based on a single neuron in the
        hidden layer:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> watervolume2waterlevel(
        ...     ANN(nmb_inputs=1, nmb_neurons=(1,), nmb_outputs=1,
        ...         weights_input=0.5, weights_output=1.0,
        ...         intercepts_hidden=0.0, intercepts_output=-0.5))

        At least in the water volume range used in the following examples, the shape of
        the relationship looks acceptable:

        >>> from hydpy import UnitTest
        >>> test = UnitTest(
        ...     model, model.calc_waterlevel_v1,
        ...     last_example=10,
        ...     parseqs=(states.watervolume, factors.waterlevel))
        >>> test.nexts.watervolume = range(10)
        >>> test()
        | ex. | watervolume | waterlevel |
        ----------------------------------
        |   1 |         0.0 |        0.0 |
        |   2 |         1.0 |   0.122459 |
        |   3 |         2.0 |   0.231059 |
        |   4 |         3.0 |   0.317574 |
        |   5 |         4.0 |   0.380797 |
        |   6 |         5.0 |   0.424142 |
        |   7 |         6.0 |   0.452574 |
        |   8 |         7.0 |   0.470688 |
        |   9 |         8.0 |   0.482014 |
        |  10 |         9.0 |   0.489013 |

        Larger neural networks or piecewise polynomials allow for more realistic
        approximations of measured relationships between water volume and water level.
    """

    CONTROLPARAMETERS = (dam_control.WaterVolume2WaterLevel,)
    REQUIREDSEQUENCES = (dam_states.WaterVolume,)
    RESULTSEQUENCES = (dam_factors.WaterLevel,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        new = model.sequences.states.fastaccess_new
        fac = model.sequences.factors.fastaccess
        con.watervolume2waterlevel.inputs[0] = new.watervolume
        con.watervolume2waterlevel.calculate_values()
        fac.waterlevel = con.watervolume2waterlevel.outputs[0]


class Calc_OuterWaterLevel_V1(modeltools.Method):
    """Get the water level directly below the dam of the last simulation step.

    Basic equation:
      :math:`OuterWaterLevel = LoggedOuterWaterLevel`

    Example:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> logs.loggedouterwaterlevel = 2.0
        >>> model.calc_outerwaterlevel_v1()
        >>> factors.outerwaterlevel
        outerwaterlevel(2.0)
    """

    REQUIREDSEQUENCES = (dam_logs.LoggedOuterWaterLevel,)
    RESULTSEQUENCES = (dam_factors.OuterWaterLevel,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        fac = model.sequences.factors.fastaccess
        log = model.sequences.logs.fastaccess
        fac.outerwaterlevel = log.loggedouterwaterlevel[0]


class Calc_RemoteWaterLevel_V1(modeltools.Method):
    """Get the water level at a remote location of the last simulation step.

    Basic equation:
      :math:`RemoteWaterLevel = LoggedRemoteWaterLevel`

    Example:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> logs.loggedremotewaterlevel = 2.0
        >>> model.calc_remotewaterlevel_v1()
        >>> factors.remotewaterlevel
        remotewaterlevel(2.0)
    """

    REQUIREDSEQUENCES = (dam_logs.LoggedRemoteWaterLevel,)
    RESULTSEQUENCES = (dam_factors.RemoteWaterLevel,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        fac = model.sequences.factors.fastaccess
        log = model.sequences.logs.fastaccess
        fac.remotewaterlevel = log.loggedremotewaterlevel[0]


class Calc_WaterLevelDifference_V1(modeltools.Method):
    """Calculate the difference between the inner and the outer water level.

    Example:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> factors.waterlevel = 5.0
        >>> factors.outerwaterlevel = 3.0
        >>> model.calc_waterleveldifference_v1()
        >>> factors.waterleveldifference
        waterleveldifference(2.0)
    """

    REQUIREDSEQUENCES = (dam_factors.WaterLevel, dam_factors.OuterWaterLevel)
    RESULTSEQUENCES = (dam_factors.WaterLevelDifference,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        fac = model.sequences.factors.fastaccess
        fac.waterleveldifference = fac.waterlevel - fac.outerwaterlevel


class Calc_EffectiveWaterLevelDifference_V1(modeltools.Method):
    r"""Calculate the "effective" difference between the inner and the outer water level
    above a threshold level.

    Basic equation:
      .. math::
        EffectiveWaterLevelDifference = h_1 - h_2
        \\ \\
        h_1 = f_{smooth \, max1}(WaterLevel, \, CrestLevelThreshold, \,
        CrestLevelSmoothPar)
        \\ \\
        h_2 = f_{smooth \, max2}(OuterWaterLevel, \, CrestLevelThreshold, \,
        CrestLevelSmoothPar)

    Used auxiliary method:
      |smooth_max1|

    Examples:

        We prepare a |UnitTest| object to illustrate how the effective water level
        difference depends on the inner and the outer water level:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> from hydpy import UnitTest
        >>> test = UnitTest(model, model.calc_effectivewaterleveldifference_v1,
        ...                 last_example=21,
        ...                 parseqs=(factors.waterlevel,
        ...                          factors.outerwaterlevel,
        ...                          factors.effectivewaterleveldifference))
        >>> test.nexts.waterlevel = numpy.linspace(3.15, 3.35, 21)
        >>> test.nexts.outerwaterlevel = numpy.linspace(3.05, 3.25, 21)

        When setting |CrestLevelTolerance| to zero, |EffectiveWaterLevelDifference| is
        identical to the water level difference above the weir's crest:

        >>> crestlevel(3.2)
        >>> crestleveltolerance(0.0)
        >>> derived.crestlevelsmoothpar.update()
        >>> test()
        | ex. | waterlevel | outerwaterlevel | effectivewaterleveldifference |
        ----------------------------------------------------------------------
        |   1 |       3.15 |            3.05 |                           0.0 |
        |   2 |       3.16 |            3.06 |                           0.0 |
        |   3 |       3.17 |            3.07 |                           0.0 |
        |   4 |       3.18 |            3.08 |                           0.0 |
        |   5 |       3.19 |            3.09 |                           0.0 |
        |   6 |        3.2 |             3.1 |                           0.0 |
        |   7 |       3.21 |            3.11 |                          0.01 |
        |   8 |       3.22 |            3.12 |                          0.02 |
        |   9 |       3.23 |            3.13 |                          0.03 |
        |  10 |       3.24 |            3.14 |                          0.04 |
        |  11 |       3.25 |            3.15 |                          0.05 |
        |  12 |       3.26 |            3.16 |                          0.06 |
        |  13 |       3.27 |            3.17 |                          0.07 |
        |  14 |       3.28 |            3.18 |                          0.08 |
        |  15 |       3.29 |            3.19 |                          0.09 |
        |  16 |        3.3 |             3.2 |                           0.1 |
        |  17 |       3.31 |            3.21 |                           0.1 |
        |  18 |       3.32 |            3.22 |                           0.1 |
        |  19 |       3.33 |            3.23 |                           0.1 |
        |  20 |       3.34 |            3.24 |                           0.1 |
        |  21 |       3.35 |            3.25 |                           0.1 |

        For more natural transitions (and also for computational efficiency), it is
        preferable to define a tolerance value larger than zero.  We set
        |CrestLevelTolerance| to 10 mm:

        >>> crestleveltolerance(0.01)
        >>> derived.crestlevelsmoothpar.update()
        >>> test()
        | ex. | waterlevel | outerwaterlevel | effectivewaterleveldifference |
        ----------------------------------------------------------------------
        |   1 |       3.15 |            3.05 |                      0.001779 |
        |   2 |       3.16 |            3.06 |                      0.002805 |
        |   3 |       3.17 |            3.07 |                      0.004364 |
        |   4 |       3.18 |            3.08 |                      0.006658 |
        |   5 |       3.19 |            3.09 |                      0.009896 |
        |   6 |        3.2 |             3.1 |                      0.014236 |
        |   7 |       3.21 |            3.11 |                      0.019728 |
        |   8 |       3.22 |            3.12 |                      0.026285 |
        |   9 |       3.23 |            3.13 |                      0.033701 |
        |  10 |       3.24 |            3.14 |                      0.041703 |
        |  11 |       3.25 |            3.15 |                          0.05 |
        |  12 |       3.26 |            3.16 |                      0.058297 |
        |  13 |       3.27 |            3.17 |                      0.066299 |
        |  14 |       3.28 |            3.18 |                      0.073715 |
        |  15 |       3.29 |            3.19 |                      0.080272 |
        |  16 |        3.3 |             3.2 |                      0.085764 |
        |  17 |       3.31 |            3.21 |                      0.090104 |
        |  18 |       3.32 |            3.22 |                      0.093342 |
        |  19 |       3.33 |            3.23 |                      0.095636 |
        |  20 |       3.34 |            3.24 |                      0.097195 |
        |  21 |       3.35 |            3.25 |                      0.098221 |

        Swapping the inner and outer water levels changes only the calculated
        difference's signs:

        >>> test.nexts.waterlevel, test.nexts.outerwaterlevel = (
        ...     test.nexts.outerwaterlevel, test.nexts.waterlevel)
        >>> test()
        | ex. | waterlevel | outerwaterlevel | effectivewaterleveldifference |
        ----------------------------------------------------------------------
        |   1 |       3.05 |            3.15 |                     -0.001779 |
        |   2 |       3.06 |            3.16 |                     -0.002805 |
        |   3 |       3.07 |            3.17 |                     -0.004364 |
        |   4 |       3.08 |            3.18 |                     -0.006658 |
        |   5 |       3.09 |            3.19 |                     -0.009896 |
        |   6 |        3.1 |             3.2 |                     -0.014236 |
        |   7 |       3.11 |            3.21 |                     -0.019728 |
        |   8 |       3.12 |            3.22 |                     -0.026285 |
        |   9 |       3.13 |            3.23 |                     -0.033701 |
        |  10 |       3.14 |            3.24 |                     -0.041703 |
        |  11 |       3.15 |            3.25 |                         -0.05 |
        |  12 |       3.16 |            3.26 |                     -0.058297 |
        |  13 |       3.17 |            3.27 |                     -0.066299 |
        |  14 |       3.18 |            3.28 |                     -0.073715 |
        |  15 |       3.19 |            3.29 |                     -0.080272 |
        |  16 |        3.2 |             3.3 |                     -0.085764 |
        |  17 |       3.21 |            3.31 |                     -0.090104 |
        |  18 |       3.22 |            3.32 |                     -0.093342 |
        |  19 |       3.23 |            3.33 |                     -0.095636 |
        |  20 |       3.24 |            3.34 |                     -0.097195 |
        |  21 |       3.25 |            3.35 |                     -0.098221 |
    """

    CONTROLPARAMETERS = (dam_control.CrestLevel,)
    DERIVEDPARAMETERS = (dam_derived.CrestLevelSmoothPar,)
    REQUIREDSEQUENCES = (dam_factors.WaterLevel, dam_factors.OuterWaterLevel)
    RESULTSEQUENCES = (dam_factors.EffectiveWaterLevelDifference,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        hi: float = smoothutils.smooth_max1(
            fac.waterlevel, con.crestlevel, der.crestlevelsmoothpar
        )
        ho: float = smoothutils.smooth_max1(
            fac.outerwaterlevel, con.crestlevel, der.crestlevelsmoothpar
        )
        fac.effectivewaterleveldifference = hi - ho


class Calc_SurfaceArea_V1(modeltools.Method):
    r"""Determine the surface area based on an interpolation approach approximating the
    relationship between the water level and the surface area.

    Basic equation:
      :math:`SurfaceArea = \frac{dWaterVolume}{WaterLevel}`

    Example:

        Method |Calc_SurfaceArea_V1| relies on the identical neural network as method
        |Calc_WaterLevel_V1|.  Therefore, we reuse the same network configuration:

        >>> from hydpy.models.dam import *
        >>> parameterstep()

        >>> watervolume2waterlevel(
        ...     ANN(nmb_inputs=1, nmb_neurons=(1,), nmb_outputs=1,
        ...         weights_input=0.5, weights_output=1.0,
        ...         intercepts_hidden=0.0, intercepts_output=-0.5))

        >>> from hydpy import UnitTest
        >>> test = UnitTest(
        ...     model, model.calc_surfacearea_v1,
        ...     last_example=10,
        ...     parseqs=(states.watervolume, aides.surfacearea))
        >>> test.nexts.watervolume = range(10)
        >>> test()
        | ex. | watervolume | surfacearea |
        -----------------------------------
        |   1 |         0.0 |         8.0 |
        |   2 |         1.0 |    8.510504 |
        |   3 |         2.0 |   10.172323 |
        |   4 |         3.0 |   13.409638 |
        |   5 |         4.0 |   19.048783 |
        |   6 |         5.0 |   28.529158 |
        |   7 |         6.0 |   44.270648 |
        |   8 |         7.0 |   70.291299 |
        |   9 |         8.0 |  113.232931 |
        |  10 |         9.0 |  184.056481 |

        We apply the class |NumericalDifferentiator| to validate the calculated surface
        area corresponding to a water volume of 9 million m³:

        >>> from hydpy import NumericalDifferentiator, round_
        >>> numdiff = NumericalDifferentiator(
        ...     xsequence=states.watervolume,
        ...     ysequences=[factors.waterlevel],
        ...     methods=[model.calc_waterlevel_v1])
        >>> numdiff()
        d_waterlevel/d_watervolume: 0.005433

        Calculating the inverse of the above result (:math:`dV/dh` instead of
        :math:`dh/dV`) gives the surface area tabulated above:

        >>> round_(1.0/0.005433115, decimals=5)
        184.05648
    """

    CONTROLPARAMETERS = (dam_control.WaterVolume2WaterLevel,)
    REQUIREDSEQUENCES = (dam_states.WaterVolume,)
    RESULTSEQUENCES = (dam_aides.SurfaceArea,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        new = model.sequences.states.fastaccess_new
        aid = model.sequences.aides.fastaccess
        con.watervolume2waterlevel.inputs[0] = new.watervolume
        con.watervolume2waterlevel.calculate_values()
        con.watervolume2waterlevel.calculate_derivatives(0)
        aid.surfacearea = 1.0 / con.watervolume2waterlevel.output_derivatives[0]


class Calc_AllowedRemoteRelief_V2(modeltools.Method):
    r"""Calculate the allowed maximum relief that another location is allowed to
    discharge into the dam.

    Used auxiliary method:
      |smooth_logistic1|

    Basic equation:
      :math:`ActualRemoteRelief = HighestRemoteRelief \cdot
      smooth_{logistic1}(WaterLevelReliefThreshold-WaterLevel,
      WaterLevelReliefSmoothPar)`

    Examples:

        All control parameters involved in the calculation of |AllowedRemoteRelief| are
        subclasses of |SeasonalParameter|.  This design allows simulating seasonal dam
        control schemes.  To show how this works, we first define a short simulation
        period of two days:

        >>> from hydpy import pub
        >>> pub.timegrids = "2001.03.30", "2001.04.03", "1d"

        We prepare the dam model and define two different control schemes for the
        hydrological summer (April to October) and winter month (November to May):

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> highestremoterelief(_11_1_12=1.0, _03_31_12=1.0,
        ...                     _04_1_12=2.0, _10_31_12=2.0)
        >>> waterlevelreliefthreshold(_11_1_12=3.0, _03_31_12=2.0,
        ...                           _04_1_12=4.0, _10_31_12=4.0)
        >>> waterlevelrelieftolerance(_11_1_12=0.0, _03_31_12=0.0,
        ...                           _04_1_12=1.0, _10_31_12=1.0)
        >>> derived.waterlevelreliefsmoothpar.update()
        >>> derived.toy.update()

        The following test function calculates |AllowedRemoteRelief| water levels
        ranging from 0.0 and 8.0 meters:

        >>> from hydpy import UnitTest
        >>> test = UnitTest(model,
        ...                 model.calc_allowedremoterelief_v2,
        ...                 last_example=9,
        ...                 parseqs=(factors.waterlevel,
        ...                          fluxes.allowedremoterelief))
        >>> test.nexts.waterlevel = range(9)

        On March 30 (which is the last day of the winter month and the first day of the
        simulation period), the value of |WaterLevelReliefSmoothPar| is zero.  Hence,
        |AllowedRemoteRelief| drops abruptly from 1 m³/s (defined by
        |HighestRemoteRelief|) to 0 m³/s as soon as |WaterLevel| reaches 3 m (defined
        by of |WaterLevelReliefThreshold|):

        >>> model.idx_sim = pub.timegrids.init["2001.03.30"]
        >>> test(first_example=2, last_example=6)
        | ex. | waterlevel | allowedremoterelief |
        ------------------------------------------
        |   3 |        1.0 |                 1.0 |
        |   4 |        2.0 |                 1.0 |
        |   5 |        3.0 |                 0.0 |
        |   6 |        4.0 |                 0.0 |

        April 1 (the first day of the summer and the last day of the simulation period)
        comes with increased parameter values.  The value of parameter
        |WaterLevelReliefSmoothPar| is 1 m.  Hence, loosely speaking,
        |AllowedRemoteRelief| approaches the "discontinuous extremes (2 m³/s -- defined
        by |HighestRemoteRelief| -- and 0 m³/s) to 99 % within a span of 2 m³/s around
        the original threshold value of 4 m³/s defined by |WaterLevelReliefThreshold|:

        >>> model.idx_sim = pub.timegrids.init["2001.04.01"]
        >>> test()
        | ex. | waterlevel | allowedremoterelief |
        ------------------------------------------
        |   1 |        0.0 |                 2.0 |
        |   2 |        1.0 |            1.999998 |
        |   3 |        2.0 |            1.999796 |
        |   4 |        3.0 |                1.98 |
        |   5 |        4.0 |                 1.0 |
        |   6 |        5.0 |                0.02 |
        |   7 |        6.0 |            0.000204 |
        |   8 |        7.0 |            0.000002 |
        |   9 |        8.0 |                 0.0 |

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (
        dam_control.HighestRemoteRelief,
        dam_control.WaterLevelReliefThreshold,
    )
    DERIVEDPARAMETERS = (dam_derived.TOY, dam_derived.WaterLevelReliefSmoothPar)
    REQUIREDSEQUENCES = (dam_factors.WaterLevel,)
    RESULTSEQUENCES = (dam_fluxes.AllowedRemoteRelief,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        toy = der.toy[model.idx_sim]
        flu.allowedremoterelief = (
            smoothutils.smooth_logistic1(
                con.waterlevelreliefthreshold[toy] - fac.waterlevel,
                der.waterlevelreliefsmoothpar[toy],
            )
            * con.highestremoterelief[toy]
        )


class Calc_RequiredRemoteSupply_V1(modeltools.Method):
    r"""Calculate the supply required from another location.

    Used auxiliary method:
      |smooth_logistic1|

    Basic equation:
      :math:`RequiredRemoteSupply = HighestRemoteSupply \cdot
      smooth_{logistic1}(WaterLevelSupplyThreshold-WaterLevel,
      WaterLevelSupplySmoothPar)`

    Examples:

        Method |Calc_RequiredRemoteSupply_V1| is functionally identical with method
        |Calc_AllowedRemoteRelief_V2|.  Hence, the following examples serve for testing
        purposes only (see the documentation on function |Calc_AllowedRemoteRelief_V2|
        for more detailed information):

        >>> from hydpy import pub
        >>> pub.timegrids = "2001.03.30", "2001.04.03", "1d"
        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> highestremotesupply(_11_1_12=1.0, _03_31_12=1.0,
        ...                     _04_1_12=2.0, _10_31_12=2.0)
        >>> waterlevelsupplythreshold(_11_1_12=3.0, _03_31_12=2.0,
        ...                           _04_1_12=4.0, _10_31_12=4.0)
        >>> waterlevelsupplytolerance(_11_1_12=0.0, _03_31_12=0.0,
        ...                           _04_1_12=1.0, _10_31_12=1.0)
        >>> derived.waterlevelsupplysmoothpar.update()
        >>> derived.toy.update()
        >>> from hydpy import UnitTest
        >>> test = UnitTest(model,
        ...                 model.calc_requiredremotesupply_v1,
        ...                 last_example=9,
        ...                 parseqs=(factors.waterlevel,
        ...                          fluxes.requiredremotesupply))
        >>> test.nexts.waterlevel = range(9)
        >>> model.idx_sim = pub.timegrids.init["2001.03.30"]
        >>> test(first_example=2, last_example=6)
        | ex. | waterlevel | requiredremotesupply |
        -------------------------------------------
        |   3 |        1.0 |                  1.0 |
        |   4 |        2.0 |                  1.0 |
        |   5 |        3.0 |                  0.0 |
        |   6 |        4.0 |                  0.0 |
        >>> model.idx_sim = pub.timegrids.init["2001.04.01"]
        >>> test()
        | ex. | waterlevel | requiredremotesupply |
        -------------------------------------------
        |   1 |        0.0 |                  2.0 |
        |   2 |        1.0 |             1.999998 |
        |   3 |        2.0 |             1.999796 |
        |   4 |        3.0 |                 1.98 |
        |   5 |        4.0 |                  1.0 |
        |   6 |        5.0 |                 0.02 |
        |   7 |        6.0 |             0.000204 |
        |   8 |        7.0 |             0.000002 |
        |   9 |        8.0 |                  0.0 |

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (
        dam_control.HighestRemoteSupply,
        dam_control.WaterLevelSupplyThreshold,
    )
    DERIVEDPARAMETERS = (dam_derived.TOY, dam_derived.WaterLevelSupplySmoothPar)
    REQUIREDSEQUENCES = (dam_factors.WaterLevel,)
    RESULTSEQUENCES = (dam_fluxes.RequiredRemoteSupply,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        toy = der.toy[model.idx_sim]
        flu.requiredremotesupply = (
            smoothutils.smooth_logistic1(
                con.waterlevelsupplythreshold[toy] - fac.waterlevel,
                der.waterlevelsupplysmoothpar[toy],
            )
            * con.highestremotesupply[toy]
        )


class Calc_NaturalRemoteDischarge_V1(modeltools.Method):
    r"""Estimate the natural discharge of a cross-section far downstream based on the
    last few simulation steps.

    Basic equation:
      :math:`RemoteDemand =
      max(\frac{\Sigma(LoggedTotalRemoteDischarge - LoggedOutflow)}{NmbLogEntries}), 0)`

    Examples:

        Usually, the mean total remote flow should be larger than the mean
        dam outflow.  Then, the estimated natural remote discharge is simply
        the difference between both averages:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> nmblogentries(3)
        >>> logs.loggedtotalremotedischarge(2.5, 2.0, 1.5)
        >>> logs.loggedoutflow(2.0, 1.0, 0.0)
        >>> model.calc_naturalremotedischarge_v1()
        >>> fluxes.naturalremotedischarge
        naturalremotedischarge(1.0)

        Due to the wave travel times, the difference between remote discharge and dam
        outflow might sometimes be negative.  To avoid negative estimates of natural
        discharge, |Calc_NaturalRemoteDischarge_V1| sets its value to zero in such
        cases:

        >>> logs.loggedoutflow(4.0, 3.0, 5.0)
        >>> model.calc_naturalremotedischarge_v1()
        >>> fluxes.naturalremotedischarge
        naturalremotedischarge(0.0)
    """

    CONTROLPARAMETERS = (dam_control.NmbLogEntries,)
    REQUIREDSEQUENCES = (dam_logs.LoggedTotalRemoteDischarge, dam_logs.LoggedOutflow)
    RESULTSEQUENCES = (dam_fluxes.NaturalRemoteDischarge,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        flu.naturalremotedischarge = 0.0
        for idx in range(con.nmblogentries):
            flu.naturalremotedischarge += (
                log.loggedtotalremotedischarge[idx] - log.loggedoutflow[idx]
            )
        if flu.naturalremotedischarge > 0.0:
            flu.naturalremotedischarge /= con.nmblogentries
        else:
            flu.naturalremotedischarge = 0.0


class Calc_RemoteDemand_V1(modeltools.Method):
    """Estimate the discharge demand of a cross-section far downstream.

    Basic equation:
      :math:`RemoteDemand = max(RemoteDischargeMinimum - NaturalRemoteDischarge, 0)`

    Examples:

        Low water elevation is often restricted to specific months of the year.
        Sometimes the pursued lowest discharge value varies over the year to allow for
        a low flow variability in some agreement with the natural flow regime.  The
        |dam.DOCNAME.long| model supports such variations.  Hence we define a short
        simulation period first, allowing us to show how we can define the
        corresponding parameter values and how calculating the `remote` water demand
        throughout the year works:

        >>> from hydpy import pub
        >>> pub.timegrids = "2001.03.30", "2001.04.03", "1d"

        Prepare the dam model:

        >>> from hydpy.models.dam import *
        >>> parameterstep()

        Assume the required discharge at a gauge downstream being 2 m³/s
        in the hydrological summer half-year (April to October).  In the
        winter month (November to May), there is no such requirement:

        >>> remotedischargeminimum(_11_1_12=0.0, _03_31_12=0.0,
        ...                        _04_1_12=2.0, _10_31_12=2.0)
        >>> derived.toy.update()

        Prepare a test function, that calculates the remote discharge demand
        based on the parameter values defined above and for natural remote
        discharge values ranging between 0 and 3 m³/s:

        >>> from hydpy import UnitTest
        >>> test = UnitTest(model, model.calc_remotedemand_v1, last_example=4,
        ...                 parseqs=(fluxes.naturalremotedischarge,
        ...                          fluxes.remotedemand))
        >>> test.nexts.naturalremotedischarge = range(4)

        On April 1, the required discharge is 2 m³/s:

        >>> model.idx_sim = pub.timegrids.init["2001.04.01"]
        >>> test()
        | ex. | naturalremotedischarge | remotedemand |
        -----------------------------------------------
        |   1 |                    0.0 |          2.0 |
        |   2 |                    1.0 |          1.0 |
        |   3 |                    2.0 |          0.0 |
        |   4 |                    3.0 |          0.0 |

        On May 31, the required discharge is 0 m³/s:

        >>> model.idx_sim = pub.timegrids.init["2001.03.31"]
        >>> test()
        | ex. | naturalremotedischarge | remotedemand |
        -----------------------------------------------
        |   1 |                    0.0 |          0.0 |
        |   2 |                    1.0 |          0.0 |
        |   3 |                    2.0 |          0.0 |
        |   4 |                    3.0 |          0.0 |

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (dam_control.RemoteDischargeMinimum,)
    DERIVEDPARAMETERS = (dam_derived.TOY,)
    REQUIREDSEQUENCES = (dam_fluxes.NaturalRemoteDischarge,)
    RESULTSEQUENCES = (dam_fluxes.RemoteDemand,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        d_rdm = con.remotedischargeminimum[der.toy[model.idx_sim]]
        flu.remotedemand = max(d_rdm - flu.naturalremotedischarge, 0.0)


class Calc_RemoteFailure_V1(modeltools.Method):
    r"""Estimate the shortfall of actual discharge under the required discharge
    of a cross section far downstream.

    Basic equation:
      :math:`RemoteFailure =
      \frac{\Sigma(LoggedTotalRemoteDischarge)}{NmbLogEntries} -
      RemoteDischargeMinimum`

    Examples:

        As explained in the documentation on method |Calc_RemoteDemand_V1|,
        we have to define a simulation period first:

        >>> from hydpy import pub
        >>> pub.timegrids = "2001.03.30", "2001.04.03", "1d"

        Now we prepare a dam model with log sequences memorizing three values:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> nmblogentries(3)

        Again, the required discharge is 2 m³/s in summer and 0 m³/s in winter:

        >>> remotedischargeminimum(_11_1_12=0.0, _03_31_12=0.0,
        ...                        _04_1_12=2.0, _10_31_12=2.0)
        >>> derived.toy.update()

        Let it be supposed that the actual discharge at the remote
        cross section droped from 2 m³/s to 0  m³/s over the last three days:

        >>> logs.loggedtotalremotedischarge(0.0, 1.0, 2.0)

        This means that for the April 1 there would have been an averaged
        shortfall of 1 m³/s:

        >>> model.idx_sim = pub.timegrids.init["2001.04.01"]
        >>> model.calc_remotefailure_v1()
        >>> fluxes.remotefailure
        remotefailure(1.0)

        Instead for May 31 there would have been an excess of 1 m³/s, which
        is interpreted to be a "negative failure":

        >>> model.idx_sim = pub.timegrids.init["2001.03.31"]
        >>> model.calc_remotefailure_v1()
        >>> fluxes.remotefailure
        remotefailure(-1.0)

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (dam_control.NmbLogEntries, dam_control.RemoteDischargeMinimum)
    DERIVEDPARAMETERS = (dam_derived.TOY,)
    REQUIREDSEQUENCES = (dam_logs.LoggedTotalRemoteDischarge,)
    RESULTSEQUENCES = (dam_fluxes.RemoteFailure,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        flu.remotefailure = 0
        for idx in range(con.nmblogentries):
            flu.remotefailure -= log.loggedtotalremotedischarge[idx]
        flu.remotefailure /= con.nmblogentries
        flu.remotefailure += con.remotedischargeminimum[der.toy[model.idx_sim]]


class Calc_RequiredRemoteRelease_V1(modeltools.Method):
    r"""Guess the required release necessary to not fall below the threshold
    value at a cross section far downstream with a certain level of certainty.

    Used auxiliary method:
      |smooth_logistic1|

    Basic equation:
      :math:`RequiredRemoteRelease = RemoteDemand + RemoteDischargeSafety
      \cdot smooth_{logistic1}(RemoteFailure, RemoteDischargeSmoothPar)`

    Examples:

        As in the examples above, define a short simulation time period first:

        >>> from hydpy import pub
        >>> pub.timegrids = "2001.03.30", "2001.04.03", "1d"

        Prepare the dam model:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> derived.toy.update()

        Define a safety factor of 0.5 m³/s for the summer months and
        no safety factor at all for the winter months:

        >>> remotedischargesafety(_11_1_12=0.0, _03_31_12=0.0,
        ...                       _04_1_12=1.0, _10_31_12=1.0)
        >>> derived.remotedischargesmoothpar.update()

        Assume the actual demand at the cross section downsstream has actually
        been estimated to be 2 m³/s:

        >>> fluxes.remotedemand = 2.0

        Prepare a test function, that calculates the required discharge
        based on the parameter values defined above and for a "remote
        failure" values ranging between -4 and 4 m³/s:

        >>> from hydpy import UnitTest
        >>> test = UnitTest(model, model.calc_requiredremoterelease_v1,
        ...                 last_example=9,
        ...                 parseqs=(fluxes.remotefailure,
        ...                          fluxes.requiredremoterelease))
        >>> test.nexts.remotefailure = range(-4, 5)

        On May 31, the safety factor is 0 m³/s.  Hence no discharge is
        added to the estimated remote demand of 2 m³/s:

        >>> model.idx_sim = pub.timegrids.init["2001.03.31"]
        >>> test()
        | ex. | remotefailure | requiredremoterelease |
        -----------------------------------------------
        |   1 |          -4.0 |                   2.0 |
        |   2 |          -3.0 |                   2.0 |
        |   3 |          -2.0 |                   2.0 |
        |   4 |          -1.0 |                   2.0 |
        |   5 |           0.0 |                   2.0 |
        |   6 |           1.0 |                   2.0 |
        |   7 |           2.0 |                   2.0 |
        |   8 |           3.0 |                   2.0 |
        |   9 |           4.0 |                   2.0 |

        On April 1, the safety factor is 1 m³/s.  If the remote failure was
        exactly zero in the past, meaning the control of the dam was perfect,
        only 0.5 m³/s are added to the estimated remote demand of 2 m³/s.
        If the actual recharge did actually fall below the threshold value,
        up to 1 m³/s is added. If the the actual discharge exceeded the
        threshold value by 2 or 3 m³/s, virtually nothing is added:

        >>> model.idx_sim = pub.timegrids.init["2001.04.01"]
        >>> test()
        | ex. | remotefailure | requiredremoterelease |
        -----------------------------------------------
        |   1 |          -4.0 |                   2.0 |
        |   2 |          -3.0 |              2.000001 |
        |   3 |          -2.0 |              2.000102 |
        |   4 |          -1.0 |                  2.01 |
        |   5 |           0.0 |                   2.5 |
        |   6 |           1.0 |                  2.99 |
        |   7 |           2.0 |              2.999898 |
        |   8 |           3.0 |              2.999999 |
        |   9 |           4.0 |                   3.0 |

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (dam_control.RemoteDischargeSafety,)
    DERIVEDPARAMETERS = (dam_derived.TOY, dam_derived.RemoteDischargeSmoothPar)
    REQUIREDSEQUENCES = (dam_fluxes.RemoteDemand, dam_fluxes.RemoteFailure)
    RESULTSEQUENCES = (dam_fluxes.RequiredRemoteRelease,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.requiredremoterelease = flu.remotedemand + (
            smoothutils.smooth_logistic1(
                flu.remotefailure, der.remotedischargesmoothpar[der.toy[model.idx_sim]]
            )
            * con.remotedischargesafety[der.toy[model.idx_sim]]
        )


class Calc_RequiredRemoteRelease_V2(modeltools.Method):
    """Get the required remote release of the last simulation step.

    Basic equation:
      :math:`RequiredRemoteRelease = LoggedRequiredRemoteRelease`

    Example:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> logs.loggedrequiredremoterelease = 3.0
        >>> model.calc_requiredremoterelease_v2()
        >>> fluxes.requiredremoterelease
        requiredremoterelease(3.0)
    """

    REQUIREDSEQUENCES = (dam_logs.LoggedRequiredRemoteRelease,)
    RESULTSEQUENCES = (dam_fluxes.RequiredRemoteRelease,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        flu.requiredremoterelease = log.loggedrequiredremoterelease[0]


class Calc_AllowedRemoteRelief_V1(modeltools.Method):
    """Get the allowed remote relief of the last simulation step.

    Basic equation:
      :math:`AllowedRemoteRelief = LoggedAllowedRemoteRelief`

    Example:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> logs.loggedallowedremoterelief = 2.0
        >>> model.calc_allowedremoterelief_v1()
        >>> fluxes.allowedremoterelief
        allowedremoterelief(2.0)
    """

    REQUIREDSEQUENCES = (dam_logs.LoggedAllowedRemoteRelief,)
    RESULTSEQUENCES = (dam_fluxes.AllowedRemoteRelief,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        flu.allowedremoterelief = log.loggedallowedremoterelief[0]


class Calc_RequiredRelease_V1(modeltools.Method):
    r"""Calculate the total water release (immediately and far downstream)
    required for reducing drought events.

    Used auxiliary method:
      |smooth_logistic2|

    Basic equation:
      :math:`RequiredRelease = RequiredRemoteRelease
      \cdot smooth_{logistic2}(
      RequiredRemoteRelease-NearDischargeMinimumThreshold,
      NearDischargeMinimumSmoothPar2)`

    Examples:

        As in the examples above, define a short simulation time period first:

        >>> from hydpy import pub
        >>> pub.timegrids = "2001.03.30", "2001.04.03", "1d"

        Prepare the dam model:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> derived.toy.update()

        Define a minimum discharge value for a cross section immediately
        downstream of 4 m³/s for the summer months and of 0 m³/s for the
        winter months:

        >>> neardischargeminimumthreshold(_11_1_12=0.0, _03_31_12=0.0,
        ...                               _04_1_12=4.0, _10_31_12=4.0)

        Also define related tolerance values that are 1 m³/s in summer and
        0 m³/s in winter:

        >>> neardischargeminimumtolerance(_11_1_12=0.0, _03_31_12=0.0,
        ...                               _04_1_12=1.0, _10_31_12=1.0)
        >>> derived.neardischargeminimumsmoothpar2.update()

        Prepare a test function, that calculates the required total discharge
        based on the parameter values defined above and for a required value
        for a cross section far downstream ranging from 0 m³/s to 8 m³/s:

        >>> from hydpy import UnitTest
        >>> test = UnitTest(model, model.calc_requiredrelease_v1,
        ...                 last_example=9,
        ...                 parseqs=(fluxes.requiredremoterelease,
        ...                          fluxes.requiredrelease))
        >>> test.nexts.requiredremoterelease = range(9)

        On May 31, both the threshold and the tolerance value are 0 m³/s.
        Hence the required total and the required remote release are equal:

        >>> model.idx_sim = pub.timegrids.init["2001.03.31"]
        >>> test()
        | ex. | requiredremoterelease | requiredrelease |
        -------------------------------------------------
        |   1 |                   0.0 |             0.0 |
        |   2 |                   1.0 |             1.0 |
        |   3 |                   2.0 |             2.0 |
        |   4 |                   3.0 |             3.0 |
        |   5 |                   4.0 |             4.0 |
        |   6 |                   5.0 |             5.0 |
        |   7 |                   6.0 |             6.0 |
        |   8 |                   7.0 |             7.0 |
        |   9 |                   8.0 |             8.0 |

        On April 1, the threshold value is 4 m³/s and the tolerance value
        is 1 m³/s.  For low values of the required remote release, the
        required total release approximates the threshold value. For large
        values, it approximates the required remote release itself.  Around
        the threshold value, due to the tolerance value of 1 m³/s, the
        required total release is a little larger than both the treshold
        value and the required remote release value:

        >>> model.idx_sim = pub.timegrids.init["2001.04.01"]
        >>> test()
        | ex. | requiredremoterelease | requiredrelease |
        -------------------------------------------------
        |   1 |                   0.0 |             4.0 |
        |   2 |                   1.0 |        4.000012 |
        |   3 |                   2.0 |        4.000349 |
        |   4 |                   3.0 |            4.01 |
        |   5 |                   4.0 |        4.205524 |
        |   6 |                   5.0 |            5.01 |
        |   7 |                   6.0 |        6.000349 |
        |   8 |                   7.0 |        7.000012 |
        |   9 |                   8.0 |             8.0 |

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (dam_control.NearDischargeMinimumThreshold,)
    DERIVEDPARAMETERS = (dam_derived.TOY, dam_derived.NearDischargeMinimumSmoothPar2)
    REQUIREDSEQUENCES = (dam_fluxes.RequiredRemoteRelease,)
    RESULTSEQUENCES = (dam_fluxes.RequiredRelease,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.requiredrelease = con.neardischargeminimumthreshold[der.toy[model.idx_sim]]
        flu.requiredrelease = flu.requiredrelease + smoothutils.smooth_logistic2(
            flu.requiredremoterelease - flu.requiredrelease,
            der.neardischargeminimumsmoothpar2[der.toy[model.idx_sim]],
        )


class Calc_RequiredRelease_V2(modeltools.Method):
    """Calculate the water release (immediately downstream) required for
    reducing drought events.

    Basic equation:
      :math:`RequiredRelease = NearDischargeMinimumThreshold`

    Examples:

        As in the examples above, define a short simulation time period first:

        >>> from hydpy import pub
        >>> pub.timegrids = "2001.03.30", "2001.04.03", "1d"

        Prepare the dam model:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> derived.toy.update()

        Define a minimum discharge value for a cross section immediately
        downstream of 4 m³/s for the summer months and of 0 m³/s for the
        winter months:

        >>> neardischargeminimumthreshold(_11_1_12=0.0, _03_31_12=0.0,
        ...                               _04_1_12=4.0, _10_31_12=4.0)


        As to be expected, the calculated required release is 0.0 m³/s
        on May 31 and 4.0 m³/s on April 1:

        >>> model.idx_sim = pub.timegrids.init["2001.03.31"]
        >>> model.calc_requiredrelease_v2()
        >>> fluxes.requiredrelease
        requiredrelease(0.0)
        >>> model.idx_sim = pub.timegrids.init["2001.04.01"]
        >>> model.calc_requiredrelease_v2()
        >>> fluxes.requiredrelease
        requiredrelease(4.0)

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (dam_control.NearDischargeMinimumThreshold,)
    DERIVEDPARAMETERS = (dam_derived.TOY,)
    RESULTSEQUENCES = (dam_fluxes.RequiredRelease,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.requiredrelease = con.neardischargeminimumthreshold[der.toy[model.idx_sim]]


class Calc_PossibleRemoteRelief_V1(modeltools.Method):
    """Calculate the highest possible water release that can be routed to a remote
    location based on an interpolation approach approximating the relationship between
    possible release and water stage.

    Example:

        For simplicity, the example of method |Calc_FloodDischarge_V1| is reused.  See
        the documentation on the mentioned method for further information:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> waterlevel2possibleremoterelief(
        ...     ANN(nmb_inputs=1,
        ...         nmb_neurons=(2,),
        ...         nmb_outputs=1,
        ...         weights_input=[[50.0, 4]],
        ...         weights_output=[[2.0], [30]],
        ...         intercepts_hidden=[[-13000, -1046]],
        ...         intercepts_output=[0.0]))
        >>> from hydpy import UnitTest
        >>> test = UnitTest(
        ...     model, model.calc_possibleremoterelief_v1,
        ...     last_example=21,
        ...     parseqs=(factors.waterlevel, fluxes.possibleremoterelief))
        >>> test.nexts.waterlevel = numpy.arange(257, 261.1, 0.2)
        >>> test()
        | ex. | waterlevel | possibleremoterelief |
        -------------------------------------------
        |   1 |      257.0 |                  0.0 |
        |   2 |      257.2 |             0.000001 |
        |   3 |      257.4 |             0.000002 |
        |   4 |      257.6 |             0.000005 |
        |   5 |      257.8 |             0.000011 |
        |   6 |      258.0 |             0.000025 |
        |   7 |      258.2 |             0.000056 |
        |   8 |      258.4 |             0.000124 |
        |   9 |      258.6 |             0.000275 |
        |  10 |      258.8 |             0.000612 |
        |  11 |      259.0 |             0.001362 |
        |  12 |      259.2 |             0.003031 |
        |  13 |      259.4 |             0.006745 |
        |  14 |      259.6 |             0.015006 |
        |  15 |      259.8 |             0.033467 |
        |  16 |      260.0 |             1.074179 |
        |  17 |      260.2 |             2.164498 |
        |  18 |      260.4 |             2.363853 |
        |  19 |      260.6 |              2.79791 |
        |  20 |      260.8 |             3.719725 |
        |  21 |      261.0 |             5.576088 |
    """

    CONTROLPARAMETERS = (dam_control.WaterLevel2PossibleRemoteRelief,)
    REQUIREDSEQUENCES = (dam_factors.WaterLevel,)
    RESULTSEQUENCES = (dam_fluxes.PossibleRemoteRelief,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        fac = model.sequences.factors.fastaccess
        con.waterlevel2possibleremoterelief.inputs[0] = fac.waterlevel
        con.waterlevel2possibleremoterelief.calculate_values()
        flu.possibleremoterelief = con.waterlevel2possibleremoterelief.outputs[0]


class Fix_Min1_V1(modeltools.Method):
    """Apply function |smooth_min1| without risking negative results.

    Used auxiliary methods:
      |smooth_min1|
      |smooth_max1|

    When applying function |smooth_min1| straight-forward
    (:math:`result = smooth_min1(input, threshold, smoothpar`),
    it likely results in slightly negative `result` values for a positive
    `threshold` value and an `input` value of zero.  Some methods of the
    |dam| models rely on |smooth_min1| but should never return negative
    values.  Therefore, methods |Fix_Min1_V1| modifies |smooth_min1| for
    such cases.

    Method both supports "absolute" (where the smoothing parameter value
    is taken as is) and "relative" smoothers (where the actual smoothing
    parameter value depends on the current threshold value).  Please see
    the detailed documentation on methods |Calc_ActualRemoteRelief_V1|
    (implementing a "relative" smoother approach), which explains the
    strategy behind method |Fix_Min1_V1| in depths.  The documentation
    on method |Update_ActualRemoteRelief_V1| provides test calculation
    results for the "aboslute" smoother approach.
    """

    @staticmethod
    def __call__(
        model: modeltools.Model,
        input_: float,
        threshold: float,
        smoothpar: float,
        relative: bool,
    ) -> float:
        if relative:
            smoothpar *= threshold
        d_result = smoothutils.smooth_min1(input_, threshold, smoothpar)
        for _ in range(5):
            smoothpar /= 5.0
            d_result = smoothutils.smooth_max1(d_result, 0.0, smoothpar)
            smoothpar /= 5.0
            if relative:
                d_result = smoothutils.smooth_min1(d_result, input_, smoothpar)
            else:
                d_result = smoothutils.smooth_min1(d_result, threshold, smoothpar)
        return max(min(d_result, input_, threshold), 0.0)


class Calc_ActualRemoteRelief_V1(modeltools.Method):
    """Calculate the actual amount of water released to a remote location
    to relieve the dam during high flow conditions.

    Basic equation - discontinous:
      :math:`ActualRemoteRelease =
      min(PossibleRemoteRelease, AllowedRemoteRelease)`

    Used additional method:
      |Fix_Min1_V1|

    Basic equation - continous:
      :math:`ActualRemoteRelease = smooth_min1(PossibleRemoteRelease,
      AllowedRemoteRelease, RemoteReliefTolerance)`

    Note that the given continous basic equation is a simplification of
    the complete algorithm to calculate |ActualRemoteRelief|, which also
    makes use of |smooth_max1| to prevent from gaining negative values
    in a smooth manner.

    Examples:

        Prepare a dam model:

        >>> from hydpy.models.dam import *
        >>> parameterstep()

        Prepare a test function object that performs seven examples with
        |PossibleRemoteRelief| ranging from -1 to 5 m³/s:

        >>> from hydpy import UnitTest
        >>> test = UnitTest(model, model.calc_actualremoterelief_v1,
        ...                 last_example=7,
        ...                 parseqs=(fluxes.possibleremoterelief,
        ...                          fluxes.actualremoterelief))
        >>> test.nexts.possibleremoterelief = range(-1, 6)

        We begin with a |AllowedRemoteRelief| value of 3 m³/s:

        >>> fluxes.allowedremoterelief = 3.0

        Through setting the value of |RemoteReliefTolerance| to the
        lowest possible value, there is no smoothing.  Instead, the
        relationship between |ActualRemoteRelief| and |PossibleRemoteRelief|
        follows the simple discontinous minimum function:

        >>> remoterelieftolerance(0.0)
        >>> test()
        | ex. | possibleremoterelief | actualremoterelief |
        ---------------------------------------------------
        |   1 |                 -1.0 |                0.0 |
        |   2 |                  0.0 |                0.0 |
        |   3 |                  1.0 |                1.0 |
        |   4 |                  2.0 |                2.0 |
        |   5 |                  3.0 |                3.0 |
        |   6 |                  4.0 |                3.0 |
        |   7 |                  5.0 |                3.0 |

        Increasing the value of parameter |RemoteReliefTolerance| to a
        sensible value results in a moderate smoothing:

        >>> remoterelieftolerance(0.2)
        >>> test()
        | ex. | possibleremoterelief | actualremoterelief |
        ---------------------------------------------------
        |   1 |                 -1.0 |                0.0 |
        |   2 |                  0.0 |                0.0 |
        |   3 |                  1.0 |           0.970639 |
        |   4 |                  2.0 |            1.89588 |
        |   5 |                  3.0 |           2.584112 |
        |   6 |                  4.0 |           2.896195 |
        |   7 |                  5.0 |           2.978969 |

        Even when setting a very large smoothing parameter value, the actual
        remote relief does not fall below 0 m³/s:

        >>> remoterelieftolerance(1.0)
        >>> test()
        | ex. | possibleremoterelief | actualremoterelief |
        ---------------------------------------------------
        |   1 |                 -1.0 |                0.0 |
        |   2 |                  0.0 |                0.0 |
        |   3 |                  1.0 |           0.306192 |
        |   4 |                  2.0 |           0.634882 |
        |   5 |                  3.0 |           1.037708 |
        |   6 |                  4.0 |           1.436494 |
        |   7 |                  5.0 |           1.788158 |

        Now we repeat the last example with an allowed remote relief of
        only 0.03 m³/s instead of 3 m³/s:

        >>> fluxes.allowedremoterelief = 0.03
        >>> test()
        | ex. | possibleremoterelief | actualremoterelief |
        ---------------------------------------------------
        |   1 |                 -1.0 |                0.0 |
        |   2 |                  0.0 |                0.0 |
        |   3 |                  1.0 |               0.03 |
        |   4 |                  2.0 |               0.03 |
        |   5 |                  3.0 |               0.03 |
        |   6 |                  4.0 |               0.03 |
        |   7 |                  5.0 |               0.03 |

        The result above is as expected, but the smooth part of the
        relationship is not resolved.  By increasing the resolution we
        see a relationship that corresponds to the one shown above
        for an allowed relief of 3 m³/s.  This points out, that the
        degree of smoothing is releative to the allowed relief:

        >>> import numpy
        >>> test.nexts.possibleremoterelief = numpy.arange(-0.01, 0.06, 0.01)
        >>> test()
        | ex. | possibleremoterelief | actualremoterelief |
        ---------------------------------------------------
        |   1 |                -0.01 |                0.0 |
        |   2 |                  0.0 |                0.0 |
        |   3 |                 0.01 |           0.003062 |
        |   4 |                 0.02 |           0.006349 |
        |   5 |                 0.03 |           0.010377 |
        |   6 |                 0.04 |           0.014365 |
        |   7 |                 0.05 |           0.017882 |

        One can reperform the shown experiments with an even higher
        resolution to see that the relationship between
        |ActualRemoteRelief| and |PossibleRemoteRelief| is
        (at least in most cases) in fact very smooth.  But a more analytical
        approach would possibly be favourable regarding the smoothness in
        some edge cases and computational efficiency.
    """

    CONTROLPARAMETERS = (dam_control.RemoteReliefTolerance,)
    REQUIREDSEQUENCES = (
        dam_fluxes.AllowedRemoteRelief,
        dam_fluxes.PossibleRemoteRelief,
    )
    RESULTSEQUENCES = (dam_fluxes.ActualRemoteRelief,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.actualremoterelief = model.fix_min1_v1(
            flu.possibleremoterelief,
            flu.allowedremoterelief,
            con.remoterelieftolerance,
            True,
        )


class Calc_TargetedRelease_V1(modeltools.Method):
    r"""Calculate the targeted water release for reducing drought events,
    taking into account both the required water release and the actual
    inflow into the dam.

    Some dams are supposed to maintain a certain degree of low flow
    variability downstream.  In case parameter |RestrictTargetedRelease|
    is set to `True`, method |Calc_TargetedRelease_V1| simulates
    this by (approximately) passing inflow as outflow whenever inflow
    is below the value of the threshold parameter
    |NearDischargeMinimumThreshold|. If parameter |RestrictTargetedRelease|
    is set to `False`, does nothing except assigning the value of sequence
    |RequiredRelease| to sequence |TargetedRelease|.

    Used auxiliary method:
      |smooth_logistic1|

    Basic equation:
      :math:`TargetedRelease =
      w \cdot RequiredRelease + (1-w) \cdot Inflow`

      :math:`w = smooth_{logistic1}(
      Inflow-NearDischargeMinimumThreshold, NearDischargeMinimumSmoothPar1)`

    Examples:

        As in the examples above, define a short simulation time period first:

        >>> from hydpy import pub
        >>> pub.timegrids = "2001.03.30", "2001.04.03", "1d"

        Prepare the dam model:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> derived.toy.update()

        We start with enabling |RestrictTargetedRelease|:

        >>> restricttargetedrelease(True)

        Define a minimum discharge value for a cross section immediately
        downstream of 6 m³/s for the summer months and of 4 m³/s for the
        winter months:

        >>> neardischargeminimumthreshold(_11_1_12=6.0, _03_31_12=6.0,
        ...                               _04_1_12=4.0, _10_31_12=4.0)

        Also define related tolerance values that are 1 m³/s in summer and
        0 m³/s in winter:

        >>> neardischargeminimumtolerance(_11_1_12=0.0, _03_31_12=0.0,
        ...                               _04_1_12=2.0, _10_31_12=2.0)
        >>> derived.neardischargeminimumsmoothpar1.update()

        Prepare a test function that calculates the targeted water release
        based on the parameter values defined above and for inflows into
        the dam ranging from 0 m³/s to 10 m³/s:

        >>> from hydpy import UnitTest
        >>> test = UnitTest(model, model.calc_targetedrelease_v1,
        ...                 last_example=21,
        ...                 parseqs=(fluxes.inflow,
        ...                          fluxes.targetedrelease))
        >>> test.nexts.inflow = numpy.arange(0.0, 10.5, .5)

        Firstly, assume the required release of water for reducing droughts
        has already been determined to be 10 m³/s:

        >>> fluxes.requiredrelease = 10.

        On May 31, the tolerance value is 0 m³/s.  Hence the targeted
        release jumps from the inflow value to the required release
        when exceeding the threshold value of 6 m³/s:

        >>> model.idx_sim = pub.timegrids.init["2001.03.31"]
        >>> test()
        | ex. | inflow | targetedrelease |
        ----------------------------------
        |   1 |    0.0 |             0.0 |
        |   2 |    0.5 |             0.5 |
        |   3 |    1.0 |             1.0 |
        |   4 |    1.5 |             1.5 |
        |   5 |    2.0 |             2.0 |
        |   6 |    2.5 |             2.5 |
        |   7 |    3.0 |             3.0 |
        |   8 |    3.5 |             3.5 |
        |   9 |    4.0 |             4.0 |
        |  10 |    4.5 |             4.5 |
        |  11 |    5.0 |             5.0 |
        |  12 |    5.5 |             5.5 |
        |  13 |    6.0 |             8.0 |
        |  14 |    6.5 |            10.0 |
        |  15 |    7.0 |            10.0 |
        |  16 |    7.5 |            10.0 |
        |  17 |    8.0 |            10.0 |
        |  18 |    8.5 |            10.0 |
        |  19 |    9.0 |            10.0 |
        |  20 |    9.5 |            10.0 |
        |  21 |   10.0 |            10.0 |

        On April 1, the threshold value is 4 m³/s and the tolerance value
        is 2 m³/s.  Hence there is a smooth transition for inflows ranging
        between 2 m³/s and 6 m³/s:

        >>> model.idx_sim = pub.timegrids.init["2001.04.01"]
        >>> test()
        | ex. | inflow | targetedrelease |
        ----------------------------------
        |   1 |    0.0 |         0.00102 |
        |   2 |    0.5 |        0.503056 |
        |   3 |    1.0 |        1.009127 |
        |   4 |    1.5 |        1.527132 |
        |   5 |    2.0 |            2.08 |
        |   6 |    2.5 |        2.731586 |
        |   7 |    3.0 |        3.639277 |
        |   8 |    3.5 |        5.064628 |
        |   9 |    4.0 |             7.0 |
        |  10 |    4.5 |        8.676084 |
        |  11 |    5.0 |        9.543374 |
        |  12 |    5.5 |        9.861048 |
        |  13 |    6.0 |            9.96 |
        |  14 |    6.5 |        9.988828 |
        |  15 |    7.0 |        9.996958 |
        |  16 |    7.5 |        9.999196 |
        |  17 |    8.0 |        9.999796 |
        |  18 |    8.5 |        9.999951 |
        |  19 |    9.0 |         9.99999 |
        |  20 |    9.5 |        9.999998 |
        |  21 |   10.0 |            10.0 |


        An required release substantially below the threshold value is
        a rather unlikely scenario, but is at least instructive regarding
        the functioning of the method (when plotting the results
        graphically...):

        >>> fluxes.requiredrelease = 2.

        On May 31, the relationship between targeted release and inflow
        is again highly discontinous:

        >>> model.idx_sim = pub.timegrids.init["2001.03.31"]
        >>> test()
        | ex. | inflow | targetedrelease |
        ----------------------------------
        |   1 |    0.0 |             0.0 |
        |   2 |    0.5 |             0.5 |
        |   3 |    1.0 |             1.0 |
        |   4 |    1.5 |             1.5 |
        |   5 |    2.0 |             2.0 |
        |   6 |    2.5 |             2.5 |
        |   7 |    3.0 |             3.0 |
        |   8 |    3.5 |             3.5 |
        |   9 |    4.0 |             4.0 |
        |  10 |    4.5 |             4.5 |
        |  11 |    5.0 |             5.0 |
        |  12 |    5.5 |             5.5 |
        |  13 |    6.0 |             4.0 |
        |  14 |    6.5 |             2.0 |
        |  15 |    7.0 |             2.0 |
        |  16 |    7.5 |             2.0 |
        |  17 |    8.0 |             2.0 |
        |  18 |    8.5 |             2.0 |
        |  19 |    9.0 |             2.0 |
        |  20 |    9.5 |             2.0 |
        |  21 |   10.0 |             2.0 |

        And on April 1, it is again absolutely smooth:

        >>> model.idx_sim = pub.timegrids.init["2001.04.01"]
        >>> test()
        | ex. | inflow | targetedrelease |
        ----------------------------------
        |   1 |    0.0 |        0.000204 |
        |   2 |    0.5 |        0.500483 |
        |   3 |    1.0 |        1.001014 |
        |   4 |    1.5 |        1.501596 |
        |   5 |    2.0 |             2.0 |
        |   6 |    2.5 |        2.484561 |
        |   7 |    3.0 |        2.908675 |
        |   8 |    3.5 |        3.138932 |
        |   9 |    4.0 |             3.0 |
        |  10 |    4.5 |         2.60178 |
        |  11 |    5.0 |        2.273976 |
        |  12 |    5.5 |        2.108074 |
        |  13 |    6.0 |            2.04 |
        |  14 |    6.5 |        2.014364 |
        |  15 |    7.0 |        2.005071 |
        |  16 |    7.5 |         2.00177 |
        |  17 |    8.0 |        2.000612 |
        |  18 |    8.5 |         2.00021 |
        |  19 |    9.0 |        2.000072 |
        |  20 |    9.5 |        2.000024 |
        |  21 |   10.0 |        2.000008 |

        For required releases equal with the threshold value, there is
        generally no jump in the relationship.  But on May 31, there
        remains a discontinuity in the first derivative:

        >>> fluxes.requiredrelease = 6.
        >>> model.idx_sim = pub.timegrids.init["2001.03.31"]
        >>> test()
        | ex. | inflow | targetedrelease |
        ----------------------------------
        |   1 |    0.0 |             0.0 |
        |   2 |    0.5 |             0.5 |
        |   3 |    1.0 |             1.0 |
        |   4 |    1.5 |             1.5 |
        |   5 |    2.0 |             2.0 |
        |   6 |    2.5 |             2.5 |
        |   7 |    3.0 |             3.0 |
        |   8 |    3.5 |             3.5 |
        |   9 |    4.0 |             4.0 |
        |  10 |    4.5 |             4.5 |
        |  11 |    5.0 |             5.0 |
        |  12 |    5.5 |             5.5 |
        |  13 |    6.0 |             6.0 |
        |  14 |    6.5 |             6.0 |
        |  15 |    7.0 |             6.0 |
        |  16 |    7.5 |             6.0 |
        |  17 |    8.0 |             6.0 |
        |  18 |    8.5 |             6.0 |
        |  19 |    9.0 |             6.0 |
        |  20 |    9.5 |             6.0 |
        |  21 |   10.0 |             6.0 |

        On April 1, this second order discontinuity is smoothed with
        the help of a little hump around the threshold:

        >>> fluxes.requiredrelease = 4.
        >>> model.idx_sim = pub.timegrids.init["2001.04.01"]
        >>> test()
        | ex. | inflow | targetedrelease |
        ----------------------------------
        |   1 |    0.0 |        0.000408 |
        |   2 |    0.5 |        0.501126 |
        |   3 |    1.0 |        1.003042 |
        |   4 |    1.5 |         1.50798 |
        |   5 |    2.0 |            2.02 |
        |   6 |    2.5 |        2.546317 |
        |   7 |    3.0 |        3.091325 |
        |   8 |    3.5 |        3.620356 |
        |   9 |    4.0 |             4.0 |
        |  10 |    4.5 |        4.120356 |
        |  11 |    5.0 |        4.091325 |
        |  12 |    5.5 |        4.046317 |
        |  13 |    6.0 |            4.02 |
        |  14 |    6.5 |         4.00798 |
        |  15 |    7.0 |        4.003042 |
        |  16 |    7.5 |        4.001126 |
        |  17 |    8.0 |        4.000408 |
        |  18 |    8.5 |        4.000146 |
        |  19 |    9.0 |        4.000051 |
        |  20 |    9.5 |        4.000018 |
        |  21 |   10.0 |        4.000006 |

        Repeating the above example with the |RestrictTargetedRelease| flag
        disabled results in identical values for sequences |RequiredRelease|
        and |TargetedRelease|:

        >>> restricttargetedrelease(False)
        >>> test()
        | ex. | inflow | targetedrelease |
        ----------------------------------
        |   1 |    0.0 |             4.0 |
        |   2 |    0.5 |             4.0 |
        |   3 |    1.0 |             4.0 |
        |   4 |    1.5 |             4.0 |
        |   5 |    2.0 |             4.0 |
        |   6 |    2.5 |             4.0 |
        |   7 |    3.0 |             4.0 |
        |   8 |    3.5 |             4.0 |
        |   9 |    4.0 |             4.0 |
        |  10 |    4.5 |             4.0 |
        |  11 |    5.0 |             4.0 |
        |  12 |    5.5 |             4.0 |
        |  13 |    6.0 |             4.0 |
        |  14 |    6.5 |             4.0 |
        |  15 |    7.0 |             4.0 |
        |  16 |    7.5 |             4.0 |
        |  17 |    8.0 |             4.0 |
        |  18 |    8.5 |             4.0 |
        |  19 |    9.0 |             4.0 |
        |  20 |    9.5 |             4.0 |
        |  21 |   10.0 |             4.0 |

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (
        dam_control.RestrictTargetedRelease,
        dam_control.NearDischargeMinimumThreshold,
    )
    DERIVEDPARAMETERS = (dam_derived.NearDischargeMinimumSmoothPar1, dam_derived.TOY)
    REQUIREDSEQUENCES = (dam_fluxes.Inflow, dam_fluxes.RequiredRelease)
    RESULTSEQUENCES = (dam_fluxes.TargetedRelease,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        if con.restricttargetedrelease:
            flu.targetedrelease = smoothutils.smooth_logistic1(
                flu.inflow - con.neardischargeminimumthreshold[der.toy[model.idx_sim]],
                der.neardischargeminimumsmoothpar1[der.toy[model.idx_sim]],
            )
            flu.targetedrelease = (
                flu.targetedrelease * flu.requiredrelease
                + (1.0 - flu.targetedrelease) * flu.inflow
            )
        else:
            flu.targetedrelease = flu.requiredrelease


class Calc_ActualRelease_V1(modeltools.Method):
    r"""Calculate the actual water release that can be supplied by the
    dam considering the targeted release and the given water level.

    Used auxiliary method:
      |smooth_logistic1|

    Basic equation:
      :math:`ActualRelease = TargetedRelease \cdot
      smooth_{logistic1}(WaterLevelMinimumThreshold - WaterLevel,
      WaterLevelMinimumSmoothPar)`

    Examples:

        Prepare the dam model:

        >>> from hydpy.models.dam import *
        >>> parameterstep()

        Assume the required release has previously been estimated
        to be 2 m³/s:

        >>> fluxes.targetedrelease = 2.0

        Prepare a test function, that calculates the targeted water release
        for water levels ranging between -1 and 5 m:

        >>> from hydpy import UnitTest
        >>> test = UnitTest(model, model.calc_actualrelease_v1,
        ...                 last_example=7,
        ...                 parseqs=(factors.waterlevel,
        ...                          fluxes.actualrelease))
        >>> test.nexts.waterlevel = range(-1, 6)

        .. _dam_calc_actualrelease_v1_ex01:

        **Example 1**

        Firstly, we define a sharp minimum water level tolerance of 0 m:

        >>> waterlevelminimumthreshold(0.0)
        >>> waterlevelminimumtolerance(0.0)
        >>> derived.waterlevelminimumsmoothpar.update()

        The following test results show that the water release is reduced
        to 0 m³/s for water levels (even slightly) lower than 0 m and is
        identical with the required value of 2 m³/s (even slighlty) above 0 m:

        >>> test()
        | ex. | waterlevel | actualrelease |
        ------------------------------------
        |   1 |       -1.0 |           0.0 |
        |   2 |        0.0 |           1.0 |
        |   3 |        1.0 |           2.0 |
        |   4 |        2.0 |           2.0 |
        |   5 |        3.0 |           2.0 |
        |   6 |        4.0 |           2.0 |
        |   7 |        5.0 |           2.0 |


        One may have noted that in the above example the calculated water
        release is 1 m³/s (which is exactly the half of the targeted release)
        at a water level of 1 m.  This looks suspiciously lake a flaw but
        is not of any importance considering the fact, that numerical
        integration algorithms will approximate the analytical solution
        of a complete emptying of a dam emtying (which is a water level
        of 0 m), only with a certain accuracy.

        .. _dam_calc_actualrelease_v1_ex02:

        **Example 2**

        Nonetheless, it can (besides some other possible advantages)
        dramatically increase the speed of numerical integration algorithms
        to define a smooth transition area instead of sharp threshold value,
        like in the following example:

        >>> waterlevelminimumthreshold(4.0)
        >>> waterlevelminimumtolerance(1.0)
        >>> derived.waterlevelminimumsmoothpar.update()

        Now, 98 % of the variation of the total range from 0 m³/s to 2 m³/s
        occurs between a water level of 3 m and 5 m:

        >>> test()
        | ex. | waterlevel | actualrelease |
        ------------------------------------
        |   1 |       -1.0 |           0.0 |
        |   2 |        0.0 |           0.0 |
        |   3 |        1.0 |      0.000002 |
        |   4 |        2.0 |      0.000204 |
        |   5 |        3.0 |          0.02 |
        |   6 |        4.0 |           1.0 |
        |   7 |        5.0 |          1.98 |

        .. _dam_calc_actualrelease_v1_ex03:

        **Example 3**

        Note that it is possible to set both parameters in a manner that
        might result in negative water stages beyond numerical inaccuracy:

        >>> waterlevelminimumthreshold(1.0)
        >>> waterlevelminimumtolerance(2.0)
        >>> derived.waterlevelminimumsmoothpar.update()

        Here, the actual water release is 0.18 m³/s for a water level
        of 0 m.  Hence water stages in the range of 0 m to -1 m or
        even -2 m might occur during the simulation of long drought events:

        >>> test()
        | ex. | waterlevel | actualrelease |
        ------------------------------------
        |   1 |       -1.0 |          0.02 |
        |   2 |        0.0 |       0.18265 |
        |   3 |        1.0 |           1.0 |
        |   4 |        2.0 |       1.81735 |
        |   5 |        3.0 |          1.98 |
        |   6 |        4.0 |      1.997972 |
        |   7 |        5.0 |      1.999796 |

    """

    CONTROLPARAMETERS = (dam_control.WaterLevelMinimumThreshold,)
    DERIVEDPARAMETERS = (dam_derived.WaterLevelMinimumSmoothPar,)
    REQUIREDSEQUENCES = (dam_fluxes.TargetedRelease, dam_factors.WaterLevel)
    RESULTSEQUENCES = (dam_fluxes.ActualRelease,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.actualrelease = flu.targetedrelease * smoothutils.smooth_logistic1(
            fac.waterlevel - con.waterlevelminimumthreshold,
            der.waterlevelminimumsmoothpar,
        )


class Calc_ActualRelease_V2(modeltools.Method):
    r"""Calculate the actual water release in aggrement with the allowed
    release not causing harm downstream and the actual water volume.

    Used auxiliary method:
      |smooth_logistic1|

    Basic equation:
      :math:`ActualRelease = AllowedRelease \cdot
      smooth_{logistic1}(WaterLevel, WaterLevelMinimumSmoothPar)`

    Examples:

        We assume a short simulation period spanning the last and first
        two days of March and April, respectively:

        >>> from hydpy import pub
        >>> pub.timegrids = "2001-03-30", "2001-04-03", "1d"

        We prepare the dam model and set the allowed release to 2 m³/s and
        to 4 m³/s for March and February, respectively, and set the water
        level threshold to 0.5 m:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> allowedrelease(_11_1_12=2.0, _03_31_12=2.0,
        ...                _04_1_12=4.0, _10_31_12=4.0)
        >>> waterlevelminimumthreshold(0.5)
        >>> derived.toy.update()

        Next, wrepare a test function, that calculates the actual water release
        for water levels ranging between 0.1 and 0.9 m:

        >>> from hydpy import UnitTest
        >>> test = UnitTest(model, model.calc_actualrelease_v2,
        ...                 last_example=9,
        ...                 parseqs=(factors.waterlevel,
        ...                          fluxes.actualrelease))
        >>> test.nexts.waterlevel = 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9

        First, we define a sharp minimum water level tolerance of 0 m,
        resulting in a sharp transition from 0 to 2 m³/s around the a
        water level threshold of 0.5 m, shown for the 31st March:

        >>> model.idx_sim = pub.timegrids.init["2001-03-31"]
        >>> waterlevelminimumtolerance(0.0)
        >>> derived.waterlevelminimumsmoothpar.update()
        >>> test()
        | ex. | waterlevel | actualrelease |
        ------------------------------------
        |   1 |        0.1 |           0.0 |
        |   2 |        0.2 |           0.0 |
        |   3 |        0.3 |           0.0 |
        |   4 |        0.4 |           0.0 |
        |   5 |        0.5 |           1.0 |
        |   6 |        0.6 |           2.0 |
        |   7 |        0.7 |           2.0 |
        |   8 |        0.8 |           2.0 |
        |   9 |        0.9 |           2.0 |

        Second, we define a numerically more sensible tolerance value
        of 0.1 m, causing 98 % of the variation of the actual release
        to occur between water levels of 0.4 m and 0.6 m, shown for
        the 1th April:

        >>> model.idx_sim = pub.timegrids.init["2001-04-01"]
        >>> waterlevelminimumtolerance(0.1)
        >>> derived.waterlevelminimumsmoothpar.update()
        >>> test()
        | ex. | waterlevel | actualrelease |
        ------------------------------------
        |   1 |        0.1 |           0.0 |
        |   2 |        0.2 |      0.000004 |
        |   3 |        0.3 |      0.000408 |
        |   4 |        0.4 |          0.04 |
        |   5 |        0.5 |           2.0 |
        |   6 |        0.6 |          3.96 |
        |   7 |        0.7 |      3.999592 |
        |   8 |        0.8 |      3.999996 |
        |   9 |        0.9 |           4.0 |

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (
        dam_control.AllowedRelease,
        dam_control.WaterLevelMinimumThreshold,
    )
    DERIVEDPARAMETERS = (dam_derived.TOY, dam_derived.WaterLevelMinimumSmoothPar)
    REQUIREDSEQUENCES = (dam_factors.WaterLevel,)
    RESULTSEQUENCES = (dam_fluxes.ActualRelease,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.actualrelease = con.allowedrelease[
            der.toy[model.idx_sim]
        ] * smoothutils.smooth_logistic1(
            fac.waterlevel - con.waterlevelminimumthreshold,
            der.waterlevelminimumsmoothpar,
        )


class Calc_ActualRelease_V3(modeltools.Method):
    """Calculate an actual water release that tries to change the water
    storage into the direction of the actual target volume without
    violating the required minimum and the allowed maximum flow.

    Used auxiliary methods:
      |smooth_logistic1|
      |smooth_logistic2|
      |smooth_min1|
      |smooth_max1|

    Examples:

        Method |Calc_ActualRelease_V3| is quite complex.  As it is the key component of
        application model |dam_lreservoir|, we advise to read its documentation
        including some introductory examples first, and to inspect the following
        detailled examples afterwards, which hopefully cover all of the mentioned
        corner cases.

        >>> from hydpy import pub
        >>> pub.timegrids = "2001-03-30", "2001-04-03", "1d"

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> targetvolume(_11_1_12=5.0, _03_31_12=5.0,
        ...              _04_1_12=0.0, _10_31_12=0.0)
        >>> neardischargeminimumthreshold(_11_1_12=3.0, _03_31_12=3.0,
        ...                               _04_1_12=0.0, _10_31_12=0.0)
        >>> watervolumeminimumthreshold(0.0)
        >>> derived.toy.update()

        >>> from hydpy import UnitTest
        >>> test = UnitTest(model, model.calc_actualrelease_v3,
        ...                 last_example=31,
        ...                 parseqs=(states.watervolume,
        ...                          fluxes.actualrelease))
        >>> import numpy
        >>> test.nexts.watervolume = numpy.arange(3.5, 6.6, 0.1)

        >>> model.idx_sim = pub.timegrids.init["2001-03-31"]
        >>> aides.alloweddischarge = 6.0

        >>> def set_tolerances(value):
        ...     volumetolerance(value)
        ...     dischargetolerance(value)
        ...     derived.volumesmoothparlog1.update()
        ...     derived.volumesmoothparlog2.update()
        ...     derived.dischargesmoothpar.update()

        >>> def apply_targetrange(flag):
        ...     if flag:
        ...         targetrangeabsolute(0.1)
        ...         targetrangerelative(0.2)
        ...     else:
        ...         targetrangeabsolute(0.0)
        ...         targetrangerelative(0.0)

        Standard case, without smoothing, without interpolation:

        >>> fluxes.inflow = 4.0
        >>> set_tolerances(0.0)
        >>> apply_targetrange(False)
        >>> test()
        | ex. | watervolume | actualrelease |
        -------------------------------------
        |   1 |         3.5 |           3.0 |
        |   2 |         3.6 |           3.0 |
        |   3 |         3.7 |           3.0 |
        |   4 |         3.8 |           3.0 |
        |   5 |         3.9 |           3.0 |
        |   6 |         4.0 |           3.0 |
        |   7 |         4.1 |           3.0 |
        |   8 |         4.2 |           3.0 |
        |   9 |         4.3 |           3.0 |
        |  10 |         4.4 |           3.0 |
        |  11 |         4.5 |           3.0 |
        |  12 |         4.6 |           3.0 |
        |  13 |         4.7 |           3.0 |
        |  14 |         4.8 |           3.0 |
        |  15 |         4.9 |           3.0 |
        |  16 |         5.0 |           4.0 |
        |  17 |         5.1 |           6.0 |
        |  18 |         5.2 |           6.0 |
        |  19 |         5.3 |           6.0 |
        |  20 |         5.4 |           6.0 |
        |  21 |         5.5 |           6.0 |
        |  22 |         5.6 |           6.0 |
        |  23 |         5.7 |           6.0 |
        |  24 |         5.8 |           6.0 |
        |  25 |         5.9 |           6.0 |
        |  26 |         6.0 |           6.0 |
        |  27 |         6.1 |           6.0 |
        |  28 |         6.2 |           6.0 |
        |  29 |         6.3 |           6.0 |
        |  30 |         6.4 |           6.0 |
        |  31 |         6.5 |           6.0 |

        Standard case, without smoothing, with interpolation:

        >>> fluxes.inflow = 4.0
        >>> set_tolerances(0.0)
        >>> apply_targetrange(True)
        >>> test()
        | ex. | watervolume | actualrelease |
        -------------------------------------
        |   1 |         3.5 |           3.0 |
        |   2 |         3.6 |           3.0 |
        |   3 |         3.7 |           3.0 |
        |   4 |         3.8 |           3.0 |
        |   5 |         3.9 |           3.0 |
        |   6 |         4.0 |           3.0 |
        |   7 |         4.1 |           3.1 |
        |   8 |         4.2 |           3.2 |
        |   9 |         4.3 |           3.3 |
        |  10 |         4.4 |           3.4 |
        |  11 |         4.5 |           3.5 |
        |  12 |         4.6 |           3.6 |
        |  13 |         4.7 |           3.7 |
        |  14 |         4.8 |           3.8 |
        |  15 |         4.9 |           3.9 |
        |  16 |         5.0 |           4.0 |
        |  17 |         5.1 |           4.2 |
        |  18 |         5.2 |           4.4 |
        |  19 |         5.3 |           4.6 |
        |  20 |         5.4 |           4.8 |
        |  21 |         5.5 |           5.0 |
        |  22 |         5.6 |           5.2 |
        |  23 |         5.7 |           5.4 |
        |  24 |         5.8 |           5.6 |
        |  25 |         5.9 |           5.8 |
        |  26 |         6.0 |           6.0 |
        |  27 |         6.1 |           6.0 |
        |  28 |         6.2 |           6.0 |
        |  29 |         6.3 |           6.0 |
        |  30 |         6.4 |           6.0 |
        |  31 |         6.5 |           6.0 |

        Standard case, moderate smoothing, without interpolation:

        >>> fluxes.inflow = 4.0
        >>> set_tolerances(0.1)
        >>> apply_targetrange(False)
        >>> test()
        | ex. | watervolume | actualrelease |
        -------------------------------------
        |   1 |         3.5 |           3.0 |
        |   2 |         3.6 |           3.0 |
        |   3 |         3.7 |           3.0 |
        |   4 |         3.8 |           3.0 |
        |   5 |         3.9 |           3.0 |
        |   6 |         4.0 |           3.0 |
        |   7 |         4.1 |           3.0 |
        |   8 |         4.2 |           3.0 |
        |   9 |         4.3 |           3.0 |
        |  10 |         4.4 |           3.0 |
        |  11 |         4.5 |           3.0 |
        |  12 |         4.6 |           3.0 |
        |  13 |         4.7 |      3.000001 |
        |  14 |         4.8 |      3.000102 |
        |  15 |         4.9 |          3.01 |
        |  16 |         5.0 |           4.0 |
        |  17 |         5.1 |          5.98 |
        |  18 |         5.2 |      5.999796 |
        |  19 |         5.3 |      5.999998 |
        |  20 |         5.4 |           6.0 |
        |  21 |         5.5 |           6.0 |
        |  22 |         5.6 |           6.0 |
        |  23 |         5.7 |           6.0 |
        |  24 |         5.8 |           6.0 |
        |  25 |         5.9 |           6.0 |
        |  26 |         6.0 |           6.0 |
        |  27 |         6.1 |           6.0 |
        |  28 |         6.2 |           6.0 |
        |  29 |         6.3 |           6.0 |
        |  30 |         6.4 |           6.0 |
        |  31 |         6.5 |           6.0 |


        Standard case, moderate smoothing, with interpolation:

        >>> fluxes.inflow = 4.0
        >>> set_tolerances(0.1)
        >>> apply_targetrange(True)
        >>> test()
        | ex. | watervolume | actualrelease |
        -------------------------------------
        |   1 |         3.5 |      3.000013 |
        |   2 |         3.6 |      3.000068 |
        |   3 |         3.7 |      3.000369 |
        |   4 |         3.8 |      3.001974 |
        |   5 |         3.9 |          3.01 |
        |   6 |         4.0 |      3.040983 |
        |   7 |         4.1 |          3.11 |
        |   8 |         4.2 |      3.201974 |
        |   9 |         4.3 |      3.300369 |
        |  10 |         4.4 |      3.400067 |
        |  11 |         4.5 |           3.5 |
        |  12 |         4.6 |      3.599933 |
        |  13 |         4.7 |      3.699632 |
        |  14 |         4.8 |      3.798047 |
        |  15 |         4.9 |        3.8913 |
        |  16 |         5.0 |           4.0 |
        |  17 |         5.1 |        4.2177 |
        |  18 |         5.2 |      4.403907 |
        |  19 |         5.3 |      4.600737 |
        |  20 |         5.4 |      4.800134 |
        |  21 |         5.5 |           5.0 |
        |  22 |         5.6 |      5.199866 |
        |  23 |         5.7 |      5.399263 |
        |  24 |         5.8 |      5.596051 |
        |  25 |         5.9 |          5.78 |
        |  26 |         6.0 |      5.918035 |
        |  27 |         6.1 |          5.98 |
        |  28 |         6.2 |      5.996051 |
        |  29 |         6.3 |      5.999262 |
        |  30 |         6.4 |      5.999864 |
        |  31 |         6.5 |      5.999975 |

        Inflow smaller than minimum release, without smoothing, without interpolation:

        >>> fluxes.inflow = 2.0
        >>> set_tolerances(0.0)
        >>> apply_targetrange(False)
        >>> test()
        | ex. | watervolume | actualrelease |
        -------------------------------------
        |   1 |         3.5 |           3.0 |
        |   2 |         3.6 |           3.0 |
        |   3 |         3.7 |           3.0 |
        |   4 |         3.8 |           3.0 |
        |   5 |         3.9 |           3.0 |
        |   6 |         4.0 |           3.0 |
        |   7 |         4.1 |           3.0 |
        |   8 |         4.2 |           3.0 |
        |   9 |         4.3 |           3.0 |
        |  10 |         4.4 |           3.0 |
        |  11 |         4.5 |           3.0 |
        |  12 |         4.6 |           3.0 |
        |  13 |         4.7 |           3.0 |
        |  14 |         4.8 |           3.0 |
        |  15 |         4.9 |           3.0 |
        |  16 |         5.0 |           3.0 |
        |  17 |         5.1 |           6.0 |
        |  18 |         5.2 |           6.0 |
        |  19 |         5.3 |           6.0 |
        |  20 |         5.4 |           6.0 |
        |  21 |         5.5 |           6.0 |
        |  22 |         5.6 |           6.0 |
        |  23 |         5.7 |           6.0 |
        |  24 |         5.8 |           6.0 |
        |  25 |         5.9 |           6.0 |
        |  26 |         6.0 |           6.0 |
        |  27 |         6.1 |           6.0 |
        |  28 |         6.2 |           6.0 |
        |  29 |         6.3 |           6.0 |
        |  30 |         6.4 |           6.0 |
        |  31 |         6.5 |           6.0 |

        Inflow smaller than minimum release, without smoothing, with interpolation:

        >>> fluxes.inflow = 2.0
        >>> set_tolerances(0.0)
        >>> apply_targetrange(True)
        >>> fluxes.inflow = 2.0
        >>> test()
        | ex. | watervolume | actualrelease |
        -------------------------------------
        |   1 |         3.5 |           3.0 |
        |   2 |         3.6 |           3.0 |
        |   3 |         3.7 |           3.0 |
        |   4 |         3.8 |           3.0 |
        |   5 |         3.9 |           3.0 |
        |   6 |         4.0 |           3.0 |
        |   7 |         4.1 |           3.0 |
        |   8 |         4.2 |           3.0 |
        |   9 |         4.3 |           3.0 |
        |  10 |         4.4 |           3.0 |
        |  11 |         4.5 |           3.0 |
        |  12 |         4.6 |           3.0 |
        |  13 |         4.7 |           3.0 |
        |  14 |         4.8 |           3.0 |
        |  15 |         4.9 |           3.0 |
        |  16 |         5.0 |           3.0 |
        |  17 |         5.1 |           3.3 |
        |  18 |         5.2 |           3.6 |
        |  19 |         5.3 |           3.9 |
        |  20 |         5.4 |           4.2 |
        |  21 |         5.5 |           4.5 |
        |  22 |         5.6 |           4.8 |
        |  23 |         5.7 |           5.1 |
        |  24 |         5.8 |           5.4 |
        |  25 |         5.9 |           5.7 |
        |  26 |         6.0 |           6.0 |
        |  27 |         6.1 |           6.0 |
        |  28 |         6.2 |           6.0 |
        |  29 |         6.3 |           6.0 |
        |  30 |         6.4 |           6.0 |
        |  31 |         6.5 |           6.0 |

        Inflow smaller than minimum release, moderate smoothing, without interpolation:

        >>> fluxes.inflow = 2.0
        >>> set_tolerances(0.1)
        >>> apply_targetrange(False)
        >>> test()
        | ex. | watervolume | actualrelease |
        -------------------------------------
        |   1 |         3.5 |           3.0 |
        |   2 |         3.6 |           3.0 |
        |   3 |         3.7 |           3.0 |
        |   4 |         3.8 |           3.0 |
        |   5 |         3.9 |           3.0 |
        |   6 |         4.0 |           3.0 |
        |   7 |         4.1 |           3.0 |
        |   8 |         4.2 |           3.0 |
        |   9 |         4.3 |           3.0 |
        |  10 |         4.4 |           3.0 |
        |  11 |         4.5 |           3.0 |
        |  12 |         4.6 |           3.0 |
        |  13 |         4.7 |           3.0 |
        |  14 |         4.8 |           3.0 |
        |  15 |         4.9 |           3.0 |
        |  16 |         5.0 |           3.0 |
        |  17 |         5.1 |          5.97 |
        |  18 |         5.2 |      5.999694 |
        |  19 |         5.3 |      5.999997 |
        |  20 |         5.4 |           6.0 |
        |  21 |         5.5 |           6.0 |
        |  22 |         5.6 |           6.0 |
        |  23 |         5.7 |           6.0 |
        |  24 |         5.8 |           6.0 |
        |  25 |         5.9 |           6.0 |
        |  26 |         6.0 |           6.0 |
        |  27 |         6.1 |           6.0 |
        |  28 |         6.2 |           6.0 |
        |  29 |         6.3 |           6.0 |
        |  30 |         6.4 |           6.0 |
        |  31 |         6.5 |           6.0 |

        Inflow smaller than minimum release, moderate smoothing, with interpolation:

        >>> fluxes.inflow = 2.0
        >>> set_tolerances(0.1)
        >>> apply_targetrange(True)
        >>> test()
        | ex. | watervolume | actualrelease |
        -------------------------------------
        |   1 |         3.5 |           3.0 |
        |   2 |         3.6 |           3.0 |
        |   3 |         3.7 |           3.0 |
        |   4 |         3.8 |           3.0 |
        |   5 |         3.9 |           3.0 |
        |   6 |         4.0 |           3.0 |
        |   7 |         4.1 |           3.0 |
        |   8 |         4.2 |           3.0 |
        |   9 |         4.3 |           3.0 |
        |  10 |         4.4 |           3.0 |
        |  11 |         4.5 |           3.0 |
        |  12 |         4.6 |           3.0 |
        |  13 |         4.7 |           3.0 |
        |  14 |         4.8 |      3.000001 |
        |  15 |         4.9 |        3.0003 |
        |  16 |         5.0 |           3.0 |
        |  17 |         5.1 |        3.3267 |
        |  18 |         5.2 |      3.605861 |
        |  19 |         5.3 |      3.901105 |
        |  20 |         5.4 |      4.200201 |
        |  21 |         5.5 |           4.5 |
        |  22 |         5.6 |      4.799799 |
        |  23 |         5.7 |      5.098894 |
        |  24 |         5.8 |      5.394077 |
        |  25 |         5.9 |          5.67 |
        |  26 |         6.0 |      5.877052 |
        |  27 |         6.1 |          5.97 |
        |  28 |         6.2 |      5.994077 |
        |  29 |         6.3 |      5.998894 |
        |  30 |         6.4 |      5.999796 |
        |  31 |         6.5 |      5.999962 |

        Inflow larger than maximum release, without smoothing, without interpolation:

        >>> fluxes.inflow = 7.0
        >>> set_tolerances(0.0)
        >>> apply_targetrange(False)
        >>> test()
        | ex. | watervolume | actualrelease |
        -------------------------------------
        |   1 |         3.5 |           3.0 |
        |   2 |         3.6 |           3.0 |
        |   3 |         3.7 |           3.0 |
        |   4 |         3.8 |           3.0 |
        |   5 |         3.9 |           3.0 |
        |   6 |         4.0 |           3.0 |
        |   7 |         4.1 |           3.0 |
        |   8 |         4.2 |           3.0 |
        |   9 |         4.3 |           3.0 |
        |  10 |         4.4 |           3.0 |
        |  11 |         4.5 |           3.0 |
        |  12 |         4.6 |           3.0 |
        |  13 |         4.7 |           3.0 |
        |  14 |         4.8 |           3.0 |
        |  15 |         4.9 |           3.0 |
        |  16 |         5.0 |           6.0 |
        |  17 |         5.1 |           6.0 |
        |  18 |         5.2 |           6.0 |
        |  19 |         5.3 |           6.0 |
        |  20 |         5.4 |           6.0 |
        |  21 |         5.5 |           6.0 |
        |  22 |         5.6 |           6.0 |
        |  23 |         5.7 |           6.0 |
        |  24 |         5.8 |           6.0 |
        |  25 |         5.9 |           6.0 |
        |  26 |         6.0 |           6.0 |
        |  27 |         6.1 |           6.0 |
        |  28 |         6.2 |           6.0 |
        |  29 |         6.3 |           6.0 |
        |  30 |         6.4 |           6.0 |
        |  31 |         6.5 |           6.0 |

        Inflow larger than maximum release, without smoothing, with interpolation:

        >>> fluxes.inflow = 7.0
        >>> set_tolerances(0.0)
        >>> apply_targetrange(True)
        >>> test()
        | ex. | watervolume | actualrelease |
        -------------------------------------
        |   1 |         3.5 |           3.0 |
        |   2 |         3.6 |           3.0 |
        |   3 |         3.7 |           3.0 |
        |   4 |         3.8 |           3.0 |
        |   5 |         3.9 |           3.0 |
        |   6 |         4.0 |           3.0 |
        |   7 |         4.1 |           3.3 |
        |   8 |         4.2 |           3.6 |
        |   9 |         4.3 |           3.9 |
        |  10 |         4.4 |           4.2 |
        |  11 |         4.5 |           4.5 |
        |  12 |         4.6 |           4.8 |
        |  13 |         4.7 |           5.1 |
        |  14 |         4.8 |           5.4 |
        |  15 |         4.9 |           5.7 |
        |  16 |         5.0 |           6.0 |
        |  17 |         5.1 |           6.0 |
        |  18 |         5.2 |           6.0 |
        |  19 |         5.3 |           6.0 |
        |  20 |         5.4 |           6.0 |
        |  21 |         5.5 |           6.0 |
        |  22 |         5.6 |           6.0 |
        |  23 |         5.7 |           6.0 |
        |  24 |         5.8 |           6.0 |
        |  25 |         5.9 |           6.0 |
        |  26 |         6.0 |           6.0 |
        |  27 |         6.1 |           6.0 |
        |  28 |         6.2 |           6.0 |
        |  29 |         6.3 |           6.0 |
        |  30 |         6.4 |           6.0 |
        |  31 |         6.5 |           6.0 |

        Inflow larger than maximum release, moderate smoothing, without interpolation:

        >>> fluxes.inflow = 7.0
        >>> apply_targetrange(False)
        >>> set_tolerances(0.1)
        >>> test()
        | ex. | watervolume | actualrelease |
        -------------------------------------
        |   1 |         3.5 |           3.0 |
        |   2 |         3.6 |           3.0 |
        |   3 |         3.7 |           3.0 |
        |   4 |         3.8 |           3.0 |
        |   5 |         3.9 |           3.0 |
        |   6 |         4.0 |           3.0 |
        |   7 |         4.1 |           3.0 |
        |   8 |         4.2 |           3.0 |
        |   9 |         4.3 |           3.0 |
        |  10 |         4.4 |           3.0 |
        |  11 |         4.5 |           3.0 |
        |  12 |         4.6 |           3.0 |
        |  13 |         4.7 |      3.000003 |
        |  14 |         4.8 |      3.000306 |
        |  15 |         4.9 |          3.03 |
        |  16 |         5.0 |           6.0 |
        |  17 |         5.1 |           6.0 |
        |  18 |         5.2 |           6.0 |
        |  19 |         5.3 |           6.0 |
        |  20 |         5.4 |           6.0 |
        |  21 |         5.5 |           6.0 |
        |  22 |         5.6 |           6.0 |
        |  23 |         5.7 |           6.0 |
        |  24 |         5.8 |           6.0 |
        |  25 |         5.9 |           6.0 |
        |  26 |         6.0 |           6.0 |
        |  27 |         6.1 |           6.0 |
        |  28 |         6.2 |           6.0 |
        |  29 |         6.3 |           6.0 |
        |  30 |         6.4 |           6.0 |
        |  31 |         6.5 |           6.0 |

        Inflow larger than maximum release, moderate smoothing, with interpolation:

        >>> fluxes.inflow = 7.0
        >>> apply_targetrange(True)
        >>> set_tolerances(0.1)
        >>> test()
        | ex. | watervolume | actualrelease |
        -------------------------------------
        |   1 |         3.5 |      3.000038 |
        |   2 |         3.6 |      3.000204 |
        |   3 |         3.7 |      3.001106 |
        |   4 |         3.8 |      3.005923 |
        |   5 |         3.9 |          3.03 |
        |   6 |         4.0 |      3.122948 |
        |   7 |         4.1 |          3.33 |
        |   8 |         4.2 |      3.605923 |
        |   9 |         4.3 |      3.901106 |
        |  10 |         4.4 |      4.200201 |
        |  11 |         4.5 |           4.5 |
        |  12 |         4.6 |      4.799799 |
        |  13 |         4.7 |      5.098895 |
        |  14 |         4.8 |      5.394139 |
        |  15 |         4.9 |        5.6733 |
        |  16 |         5.0 |           6.0 |
        |  17 |         5.1 |        5.9997 |
        |  18 |         5.2 |      5.999999 |
        |  19 |         5.3 |           6.0 |
        |  20 |         5.4 |           6.0 |
        |  21 |         5.5 |           6.0 |
        |  22 |         5.6 |           6.0 |
        |  23 |         5.7 |           6.0 |
        |  24 |         5.8 |           6.0 |
        |  25 |         5.9 |           6.0 |
        |  26 |         6.0 |           6.0 |
        |  27 |         6.1 |           6.0 |
        |  28 |         6.2 |           6.0 |
        |  29 |         6.3 |           6.0 |
        |  30 |         6.4 |           6.0 |
        |  31 |         6.5 |           6.0 |

        Maximum release smaller than minimum release, without smoothing, with
        interpolation:

        >>> aides.alloweddischarge = 1.0
        >>> set_tolerances(0.0)
        >>> apply_targetrange(True)
        >>> test()
        | ex. | watervolume | actualrelease |
        -------------------------------------
        |   1 |         3.5 |           3.0 |
        |   2 |         3.6 |           3.0 |
        |   3 |         3.7 |           3.0 |
        |   4 |         3.8 |           3.0 |
        |   5 |         3.9 |           3.0 |
        |   6 |         4.0 |           3.0 |
        |   7 |         4.1 |           3.0 |
        |   8 |         4.2 |           3.0 |
        |   9 |         4.3 |           3.0 |
        |  10 |         4.4 |           3.0 |
        |  11 |         4.5 |           3.0 |
        |  12 |         4.6 |           3.0 |
        |  13 |         4.7 |           3.0 |
        |  14 |         4.8 |           3.0 |
        |  15 |         4.9 |           3.0 |
        |  16 |         5.0 |           3.0 |
        |  17 |         5.1 |           3.0 |
        |  18 |         5.2 |           3.0 |
        |  19 |         5.3 |           3.0 |
        |  20 |         5.4 |           3.0 |
        |  21 |         5.5 |           3.0 |
        |  22 |         5.6 |           3.0 |
        |  23 |         5.7 |           3.0 |
        |  24 |         5.8 |           3.0 |
        |  25 |         5.9 |           3.0 |
        |  26 |         6.0 |           3.0 |
        |  27 |         6.1 |           3.0 |
        |  28 |         6.2 |           3.0 |
        |  29 |         6.3 |           3.0 |
        |  30 |         6.4 |           3.0 |
        |  31 |         6.5 |           3.0 |

        Maximum release smaller than minimum release, moderate smoothing, with
        interpolation:

        >>> aides.alloweddischarge = 1.0
        >>> set_tolerances(0.1)
        >>> apply_targetrange(True)
        >>> test()
        | ex. | watervolume | actualrelease |
        -------------------------------------
        |   1 |         3.5 |      3.000001 |
        |   2 |         3.6 |      3.000003 |
        |   3 |         3.7 |      3.000015 |
        |   4 |         3.8 |      3.000081 |
        |   5 |         3.9 |       3.00041 |
        |   6 |         4.0 |       3.00168 |
        |   7 |         4.1 |      3.004508 |
        |   8 |         4.2 |      3.008277 |
        |   9 |         4.3 |       3.01231 |
        |  10 |         4.4 |      3.016396 |
        |  11 |         4.5 |      3.020491 |
        |  12 |         4.6 |      3.024587 |
        |  13 |         4.7 |      3.028673 |
        |  14 |         4.8 |      3.032702 |
        |  15 |         4.9 |       3.03611 |
        |  16 |         5.0 |      3.040983 |
        |  17 |         5.1 |      3.000406 |
        |  18 |         5.2 |      3.000004 |
        |  19 |         5.3 |           3.0 |
        |  20 |         5.4 |           3.0 |
        |  21 |         5.5 |           3.0 |
        |  22 |         5.6 |           3.0 |
        |  23 |         5.7 |           3.0 |
        |  24 |         5.8 |           3.0 |
        |  25 |         5.9 |           3.0 |
        |  26 |         6.0 |           3.0 |
        |  27 |         6.1 |           3.0 |
        |  28 |         6.2 |           3.0 |
        |  29 |         6.3 |           3.0 |
        |  30 |         6.4 |           3.0 |
        |  31 |         6.5 |           3.0 |

        >>> from hydpy import UnitTest
        >>> test = UnitTest(model, model.calc_actualrelease_v3,
        ...                 last_example=21,
        ...                 parseqs=(states.watervolume,
        ...                          fluxes.actualrelease))
        >>> test.nexts.watervolume = numpy.arange(-0.5, 1.6, 0.1)
        >>> model.idx_sim = pub.timegrids.init["2001-04-01"]
        >>> fluxes.inflow = 0.0

        Zero values, without smoothing, with interpolation:

        >>> set_tolerances(0.0)
        >>> apply_targetrange(True)
        >>> test()
        | ex. | watervolume | actualrelease |
        -------------------------------------
        |   1 |        -0.5 |           0.0 |
        |   2 |        -0.4 |           0.0 |
        |   3 |        -0.3 |           0.0 |
        |   4 |        -0.2 |           0.0 |
        |   5 |        -0.1 |           0.0 |
        |   6 |         0.0 |           0.0 |
        |   7 |         0.1 |           1.0 |
        |   8 |         0.2 |           1.0 |
        |   9 |         0.3 |           1.0 |
        |  10 |         0.4 |           1.0 |
        |  11 |         0.5 |           1.0 |
        |  12 |         0.6 |           1.0 |
        |  13 |         0.7 |           1.0 |
        |  14 |         0.8 |           1.0 |
        |  15 |         0.9 |           1.0 |
        |  16 |         1.0 |           1.0 |
        |  17 |         1.1 |           1.0 |
        |  18 |         1.2 |           1.0 |
        |  19 |         1.3 |           1.0 |
        |  20 |         1.4 |           1.0 |
        |  21 |         1.5 |           1.0 |

        Zero values, moderate smoothing, with interpolation:

        >>> set_tolerances(0.1)
        >>> apply_targetrange(True)
        >>> test()
        | ex. | watervolume | actualrelease |
        -------------------------------------
        |   1 |        -0.5 |           0.0 |
        |   2 |        -0.4 |           0.0 |
        |   3 |        -0.3 |           0.0 |
        |   4 |        -0.2 |      0.000004 |
        |   5 |        -0.1 |       0.00042 |
        |   6 |         0.0 |      0.032478 |
        |   7 |         0.1 |      0.941985 |
        |   8 |         0.2 |        0.9998 |
        |   9 |         0.3 |      0.999998 |
        |  10 |         0.4 |           1.0 |
        |  11 |         0.5 |           1.0 |
        |  12 |         0.6 |           1.0 |
        |  13 |         0.7 |           1.0 |
        |  14 |         0.8 |           1.0 |
        |  15 |         0.9 |           1.0 |
        |  16 |         1.0 |           1.0 |
        |  17 |         1.1 |           1.0 |
        |  18 |         1.2 |           1.0 |
        |  19 |         1.3 |           1.0 |
        |  20 |         1.4 |           1.0 |
        |  21 |         1.5 |           1.0 |

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (
        dam_control.TargetVolume,
        dam_control.TargetRangeAbsolute,
        dam_control.TargetRangeRelative,
        dam_control.NearDischargeMinimumThreshold,
        dam_control.WaterVolumeMinimumThreshold,
    )
    DERIVEDPARAMETERS = (
        dam_derived.TOY,
        dam_derived.VolumeSmoothParLog1,
        dam_derived.VolumeSmoothParLog2,
        dam_derived.DischargeSmoothPar,
    )
    REQUIREDSEQUENCES = (
        dam_fluxes.Inflow,
        dam_states.WaterVolume,
        dam_aides.AllowedDischarge,
    )
    RESULTSEQUENCES = (dam_fluxes.ActualRelease,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        new = model.sequences.states.fastaccess_new
        aid = model.sequences.aides.fastaccess
        # some general preparations:
        idx_toy = der.toy[model.idx_sim]
        d_target = con.targetvolume[idx_toy]
        d_range = max(con.targetrangeabsolute, con.targetrangerelative * d_target)
        d_range = max(d_range, 1e-6)
        d_qmin = con.neardischargeminimumthreshold[idx_toy]
        d_qmax = smoothutils.smooth_max1(
            d_qmin, aid.alloweddischarge, der.dischargesmoothpar
        )
        # calculate the release for too-high water volumes:
        d_factor = smoothutils.smooth_logistic3(
            (new.watervolume - d_target + d_range) / d_range, der.volumesmoothparlog2
        )
        d_upperbound = smoothutils.smooth_min1(
            d_qmax, flu.inflow, der.dischargesmoothpar
        )
        d_release1 = (1.0 - d_factor) * d_qmin + d_factor * smoothutils.smooth_max1(
            d_qmin, d_upperbound, der.dischargesmoothpar
        )
        # calculate the release for too-low water volumes:
        d_factor = smoothutils.smooth_logistic3(
            (d_target + d_range - new.watervolume) / d_range, der.volumesmoothparlog2
        )
        d_neutral = smoothutils.smooth_max1(d_qmin, flu.inflow, der.dischargesmoothpar)
        d_release2 = (1.0 - d_factor) * d_qmax + d_factor * smoothutils.smooth_min1(
            d_qmax, d_neutral, der.dischargesmoothpar
        )
        # combine both releases smoothly:
        d_weight = smoothutils.smooth_logistic1(
            d_target - new.watervolume, der.volumesmoothparlog1
        )
        flu.actualrelease = d_weight * d_release1 + (1.0 - d_weight) * d_release2
        # the realease calculated so far may depend on the smoothing-degree,
        # even when the actual volume meets the target volume; the following
        # equations are supposed to correct this:
        if der.volumesmoothparlog1 > 0.0:
            d_weight = modelutils.exp(
                -(((new.watervolume - d_target) / der.volumesmoothparlog1) ** 2)
            )
        else:
            d_weight = 0.0
        d_neutral = smoothutils.smooth_max1(
            d_upperbound, d_qmin, der.dischargesmoothpar
        )
        flu.actualrelease = d_weight * d_neutral + (1.0 - d_weight) * flu.actualrelease
        # for good measure, prevent negative release and storage overdrying
        # explictly:
        flu.actualrelease = smoothutils.smooth_max1(
            flu.actualrelease, 0.0, der.dischargesmoothpar
        )
        flu.actualrelease *= smoothutils.smooth_logistic1(
            new.watervolume - con.watervolumeminimumthreshold[idx_toy],
            der.volumesmoothparlog1,
        )


class Calc_MissingRemoteRelease_V1(modeltools.Method):
    """Calculate the portion of the required remote demand that could not
    be met by the actual discharge release.

    Basic equation:
      :math:`MissingRemoteRelease = max(
      RequiredRemoteRelease-ActualRelease, 0)`

    Example:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> fluxes.requiredremoterelease = 2.0
        >>> fluxes.actualrelease = 1.0
        >>> model.calc_missingremoterelease_v1()
        >>> fluxes.missingremoterelease
        missingremoterelease(1.0)
        >>> fluxes.actualrelease = 3.0
        >>> model.calc_missingremoterelease_v1()
        >>> fluxes.missingremoterelease
        missingremoterelease(0.0)
    """

    REQUIREDSEQUENCES = (dam_fluxes.ActualRelease, dam_fluxes.RequiredRemoteRelease)
    RESULTSEQUENCES = (dam_fluxes.MissingRemoteRelease,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.missingremoterelease = max(
            flu.requiredremoterelease - flu.actualrelease, 0.0
        )


class Calc_ActualRemoteRelease_V1(modeltools.Method):
    r"""Calculate the actual remote water release that can be supplied by the
    dam considering the required remote release and the given water level.

    Used auxiliary method:
      |smooth_logistic1|

    Basic equation:
      :math:`ActualRemoteRelease = RequiredRemoteRelease \cdot
      smooth_{logistic1}(WaterLevelMinimumRemoteThreshold-WaterLevel,
      WaterLevelMinimumRemoteSmoothPar)`

    Examples:

        Note that method |Calc_ActualRemoteRelease_V1| is functionally
        identical to method |Calc_ActualRelease_V1|.  This is why we
        omit to explain the following examples, as they are just repetitions
        of the ones of method |Calc_ActualRemoteRelease_V1| with partly
        different variable names.  Please follow the links to read the
        corresponding explanations.

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> fluxes.requiredremoterelease = 2.0
        >>> from hydpy import UnitTest
        >>> test = UnitTest(model, model.calc_actualremoterelease_v1,
        ...                 last_example=7,
        ...                 parseqs=(factors.waterlevel,
        ...                          fluxes.actualremoterelease))
        >>> test.nexts.waterlevel = range(-1, 6)

        :ref:`Recalculation of example 1 <dam_calc_actualrelease_v1_ex01>`

        >>> waterlevelminimumremotethreshold(0.)
        >>> waterlevelminimumremotetolerance(0.)
        >>> derived.waterlevelminimumremotesmoothpar.update()
        >>> test()
        | ex. | waterlevel | actualremoterelease |
        ------------------------------------------
        |   1 |       -1.0 |                 0.0 |
        |   2 |        0.0 |                 1.0 |
        |   3 |        1.0 |                 2.0 |
        |   4 |        2.0 |                 2.0 |
        |   5 |        3.0 |                 2.0 |
        |   6 |        4.0 |                 2.0 |
        |   7 |        5.0 |                 2.0 |


        :ref:`Recalculation of example 2 <dam_calc_actualrelease_v1_ex02>`

        >>> waterlevelminimumremotethreshold(4.)
        >>> waterlevelminimumremotetolerance(1.)
        >>> derived.waterlevelminimumremotesmoothpar.update()
        >>> test()
        | ex. | waterlevel | actualremoterelease |
        ------------------------------------------
        |   1 |       -1.0 |                 0.0 |
        |   2 |        0.0 |                 0.0 |
        |   3 |        1.0 |            0.000002 |
        |   4 |        2.0 |            0.000204 |
        |   5 |        3.0 |                0.02 |
        |   6 |        4.0 |                 1.0 |
        |   7 |        5.0 |                1.98 |

        :ref:`Recalculation of example 3 <dam_calc_actualrelease_v1_ex03>`

        >>> waterlevelminimumremotethreshold(1.)
        >>> waterlevelminimumremotetolerance(2.)
        >>> derived.waterlevelminimumremotesmoothpar.update()
        >>> test()
        | ex. | waterlevel | actualremoterelease |
        ------------------------------------------
        |   1 |       -1.0 |                0.02 |
        |   2 |        0.0 |             0.18265 |
        |   3 |        1.0 |                 1.0 |
        |   4 |        2.0 |             1.81735 |
        |   5 |        3.0 |                1.98 |
        |   6 |        4.0 |            1.997972 |
        |   7 |        5.0 |            1.999796 |
    """

    CONTROLPARAMETERS = (dam_control.WaterLevelMinimumRemoteThreshold,)
    DERIVEDPARAMETERS = (dam_derived.WaterLevelMinimumRemoteSmoothPar,)
    REQUIREDSEQUENCES = (dam_fluxes.RequiredRemoteRelease, dam_factors.WaterLevel)
    RESULTSEQUENCES = (dam_fluxes.ActualRemoteRelease,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.actualremoterelease = (
            flu.requiredremoterelease
            * smoothutils.smooth_logistic1(
                fac.waterlevel - con.waterlevelminimumremotethreshold,
                der.waterlevelminimumremotesmoothpar,
            )
        )


class Update_ActualRemoteRelief_V1(modeltools.Method):
    """Constrain the actual relief discharge to a remote location.

    Used additional method:
      |Fix_Min1_V1|

    Basic equation - discontinous:
      :math:`ActualRemoteRelief = min(ActualRemoteRelease,
      HighestRemoteDischarge)`

    Basic equation - continous:
      :math:`ActualRemoteRelief =
      smooth_min1(ActualRemoteRelief, HighestRemoteDischarge, HighestRemoteSmoothPar)`

    Examples:

        Prepare a dam model:

        >>> from hydpy.models.dam import *
        >>> parameterstep()

        Prepare a test function object that performs eight examples with
        |ActualRemoteRelief| ranging from 0 to 8 m³/s and a fixed
        initial value of parameter |HighestRemoteDischarge| of 4 m³/s:

        >>> highestremotedischarge(4.0)
        >>> from hydpy import UnitTest
        >>> test = UnitTest(model,
        ...                 model.update_actualremoterelief_v1,
        ...                 last_example=8,
        ...                 parseqs=(fluxes.actualremoterelief,))
        >>> test.nexts.actualremoterelief = range(8)

        Through setting the value of |HighestRemoteTolerance| to the
        lowest possible value, there is no smoothing.  Instead, the
        shown relationship agrees with a combination of the discontinuous
        minimum and maximum function:

        >>> highestremotetolerance(0.0)
        >>> derived.highestremotesmoothpar.update()
        >>> test()
        | ex. | actualremoterelief |
        ----------------------------
        |   1 |                0.0 |
        |   2 |                1.0 |
        |   3 |                2.0 |
        |   4 |                3.0 |
        |   5 |                4.0 |
        |   6 |                4.0 |
        |   7 |                4.0 |
        |   8 |                4.0 |

        Setting a sensible |HighestRemoteTolerance| value results in
        a moderate smoothing:

        >>> highestremotetolerance(0.1)
        >>> derived.highestremotesmoothpar.update()
        >>> test()
        | ex. | actualremoterelief |
        ----------------------------
        |   1 |                0.0 |
        |   2 |           0.999999 |
        |   3 |            1.99995 |
        |   4 |           2.996577 |
        |   5 |           3.836069 |
        |   6 |           3.991578 |
        |   7 |           3.993418 |
        |   8 |           3.993442 |
    """

    CONTROLPARAMETERS = (dam_control.HighestRemoteDischarge,)
    DERIVEDPARAMETERS = (dam_derived.HighestRemoteSmoothPar,)
    UPDATEDSEQUENCES = (dam_fluxes.ActualRemoteRelief,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.actualremoterelief = model.fix_min1_v1(
            flu.actualremoterelief,
            con.highestremotedischarge,
            der.highestremotesmoothpar,
            False,
        )


class Update_ActualRemoteRelease_V1(modeltools.Method):
    """Constrain the actual release (supply discharge) to a remote location.

    Used additional method:
      |Fix_Min1_V1|

    Basic equation - discontinous:
      :math:`ActualRemoteRelease =
      min(ActualRemoteRelease, HighestRemoteDischarge - ActualRemoteRelief)`

    Basic equation - continous:
      :math:`ActualRemoteRelease = smooth_min1(ActualRemoteRelease,
      HighestRemoteDischarge - ActualRemoteRelief, HighestRemoteSmoothPar)`

    Examples:

        Prepare a dam model:

        >>> from hydpy.models.dam import *
        >>> parameterstep()

        Prepare a test function object that performs eight examples with
        |ActualRemoteRelief| ranging from 0 to 8 m³/s and a fixed initial
        value of parameter |ActualRemoteRelease| of 2 m³/s:

        >>> from hydpy import UnitTest
        >>> test = UnitTest(model,
        ...                 model.update_actualremoterelease_v1,
        ...                 last_example=8,
        ...                 parseqs=(fluxes.actualremoterelief,
        ...                          fluxes.actualremoterelease))
        >>> test.nexts.actualremoterelief = range(8)
        >>> test.inits.actualremoterelease = 2.0

        Through setting the value of |HighestRemoteTolerance| to the
        lowest possible value, there is no smoothing.  Instead, the
        shown relationship agrees with a combination of the discontinuous
        minimum and maximum function:

        >>> highestremotedischarge(6.0)
        >>> highestremotetolerance(0.0)
        >>> derived.highestremotesmoothpar.update()
        >>> test()
        | ex. | actualremoterelief | actualremoterelease |
        --------------------------------------------------
        |   1 |                0.0 |                 2.0 |
        |   2 |                1.0 |                 2.0 |
        |   3 |                2.0 |                 2.0 |
        |   4 |                3.0 |                 2.0 |
        |   5 |                4.0 |                 2.0 |
        |   6 |                5.0 |                 1.0 |
        |   7 |                6.0 |                 0.0 |
        |   8 |                7.0 |                 0.0 |

        Setting a sensible |HighestRemoteTolerance| value results in
        a moderate smoothing.  But note that this is only true for
        the minimum function (restricting the larger
        |ActualRemoteRelease| values).  Instead of smoothing the
        maximum function as well, |ActualRemoteRelease| is exactly
        0 m³/s for a |ActualRemoteRelief| value of 6 m³/s (within
        the shown precision). The remaining discontinuity does not
        pose a problem, as long |ActualRemoteRelief| does not exceed
        the value of |HighestRemoteDischarge|.  (Application models
        using method |Update_ActualRemoteRelease_V1| should generally
        enforce this restriction). In case of exceedance, extended
        computation times might occur:

        >>> highestremotetolerance(0.1)
        >>> derived.highestremotesmoothpar.update()
        >>> test()
        | ex. | actualremoterelief | actualremoterelease |
        --------------------------------------------------
        |   1 |                0.0 |            1.999996 |
        |   2 |                1.0 |            1.999925 |
        |   3 |                2.0 |            1.998739 |
        |   4 |                3.0 |            1.979438 |
        |   5 |                4.0 |            1.754104 |
        |   6 |                5.0 |            0.976445 |
        |   7 |                6.0 |                 0.0 |
        |   8 |                7.0 |                 0.0 |
    """

    CONTROLPARAMETERS = (dam_control.HighestRemoteDischarge,)
    DERIVEDPARAMETERS = (dam_derived.HighestRemoteSmoothPar,)
    REQUIREDSEQUENCES = (dam_fluxes.ActualRemoteRelief,)
    UPDATEDSEQUENCES = (dam_fluxes.ActualRemoteRelease,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.actualremoterelease = model.fix_min1_v1(
            flu.actualremoterelease,
            con.highestremotedischarge - flu.actualremoterelief,
            der.highestremotesmoothpar,
            False,
        )


class Calc_FloodDischarge_V1(modeltools.Method):
    """Calculate the discharge during and after a flood event based on seasonally
    varying interpolation approaches approximating the relationship(s) between
    discharge and water stage.

    Example:

        The control parameter |WaterLevel2FloodDischarge| is derived from
        |SeasonalInterpolator|.  This allows to simulate different seasonal dam control
        schemes.  To show that the seasonal selection mechanism is implemented properly,
        we define a short simulation period of three days:

        >>> from hydpy import pub
        >>> pub.timegrids = "2001.01.01", "2001.01.04", "1d"

        Now we prepare a dam model and define two different relationships between water
        level and flood discharge using artificial neural networks as interpolators.
        The first relatively simple relationship (for January 2) is based on two
        neurons contained in a single hidden layer and is used in the following example.
        The second neural network (for January 3) is not applied at all, which is why
        we do not need to assign any parameter values to it:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> waterlevel2flooddischarge(
        ...     _01_02_12 = ANN(nmb_inputs=1,
        ...                     nmb_neurons=(2,),
        ...                     nmb_outputs=1,
        ...                     weights_input=[[50.0, 4]],
        ...                     weights_output=[[2.0], [30]],
        ...                     intercepts_hidden=[[-13000, -1046]],
        ...                     intercepts_output=[0.0]),
        ...     _01_03_12 = ANN(nmb_inputs=1,
        ...                     nmb_neurons=(2,),
        ...                     nmb_outputs=1))
        >>> derived.toy.update()
        >>> model.idx_sim = pub.timegrids.sim["2001.01.02"]

        The following example shows two distinct effects of both neurons in the first
        network.  One neuron describes a relatively sharp increase between 259.8 and
        260.2 meters from about 0 to 2 m³/s.  This could describe a release of water
        through a bottom outlet controlled by a valve.  The add something like an
        exponential increase between 260 and 261 meters, which could describe the
        uncontrolled flow over a spillway:

        >>> from hydpy import UnitTest
        >>> test = UnitTest(model,
        ...                 model.calc_flooddischarge_v1,
        ...                 last_example=21,
        ...                 parseqs=(factors.waterlevel,
        ...                          fluxes.flooddischarge))
        >>> test.nexts.waterlevel = numpy.arange(257, 261.1, 0.2)
        >>> test()
        | ex. | waterlevel | flooddischarge |
        -------------------------------------
        |   1 |      257.0 |            0.0 |
        |   2 |      257.2 |       0.000001 |
        |   3 |      257.4 |       0.000002 |
        |   4 |      257.6 |       0.000005 |
        |   5 |      257.8 |       0.000011 |
        |   6 |      258.0 |       0.000025 |
        |   7 |      258.2 |       0.000056 |
        |   8 |      258.4 |       0.000124 |
        |   9 |      258.6 |       0.000275 |
        |  10 |      258.8 |       0.000612 |
        |  11 |      259.0 |       0.001362 |
        |  12 |      259.2 |       0.003031 |
        |  13 |      259.4 |       0.006745 |
        |  14 |      259.6 |       0.015006 |
        |  15 |      259.8 |       0.033467 |
        |  16 |      260.0 |       1.074179 |
        |  17 |      260.2 |       2.164498 |
        |  18 |      260.4 |       2.363853 |
        |  19 |      260.6 |        2.79791 |
        |  20 |      260.8 |       3.719725 |
        |  21 |      261.0 |       5.576088 |

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (dam_control.WaterLevel2FloodDischarge,)
    DERIVEDPARAMETERS = (dam_derived.TOY,)
    REQUIREDSEQUENCES = (dam_factors.WaterLevel,)
    RESULTSEQUENCES = (dam_fluxes.FloodDischarge,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        con.waterlevel2flooddischarge.inputs[0] = fac.waterlevel
        con.waterlevel2flooddischarge.calculate_values(der.toy[model.idx_sim])
        flu.flooddischarge = con.waterlevel2flooddischarge.outputs[0]


class Calc_MaxForcedDischarge_V1(modeltools.Method):
    """Approximate the currently highest possible forced water release through
    structures as pumps based on seasonally varying interpolation approaches that take
    the water level difference as input.

    Examples:

        We consider a simulation period of five days:

        >>> from hydpy import pub
        >>> pub.timegrids = "2001-01-01", "2001-01-06", "1d"

        For the second day, the maximum possible discharge of 2 m³/s does not depend on
        the water level difference.  For the fourth day, it is -4 m³/s for negative and
        4 m³/s for positive water level differences:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> waterleveldifference2maxforceddischarge(
        ...     _01_02_12 = PPoly(Poly(x0=0.0, cs=[2.0])),
        ...     _01_04_12 = PPoly(Poly(x0=-2.0, cs=[-4.0]), Poly(x0=0.0, cs=[4.0]))
        ... )
        >>> derived.toy.update()

        All results are as expected:

        >>> model.idx_sim = pub.timegrids.sim["2001-01-02"]
        >>> factors.waterleveldifference = -1.0
        >>> model.calc_maxforceddischarge_v1()
        >>> fluxes.maxforceddischarge
        maxforceddischarge(2.0)

        >>> model.idx_sim = pub.timegrids.sim["2001-01-03"]
        >>> model.calc_maxforceddischarge_v1()
        >>> fluxes.maxforceddischarge
        maxforceddischarge(-1.0)

        >>> model.idx_sim = pub.timegrids.sim["2001-01-04"]
        >>> factors.waterleveldifference = 1.0
        >>> model.calc_maxforceddischarge_v1()
        >>> fluxes.maxforceddischarge
        maxforceddischarge(4.0)

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (dam_control.WaterLevelDifference2MaxForcedDischarge,)
    DERIVEDPARAMETERS = (dam_derived.TOY,)
    REQUIREDSEQUENCES = (dam_factors.WaterLevelDifference,)
    RESULTSEQUENCES = (dam_fluxes.MaxForcedDischarge,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        con.waterleveldifference2maxforceddischarge.inputs[0] = fac.waterleveldifference
        toy: int = der.toy[model.idx_sim]
        con.waterleveldifference2maxforceddischarge.calculate_values(toy)
        flu.maxforceddischarge = con.waterleveldifference2maxforceddischarge.outputs[0]


class Calc_MaxFreeDischarge_V1(modeltools.Method):
    """Approximate the currently highest possible free water release through structures
    as sluices based on seasonally varying interpolation approaches that take the water
    level difference as input.

    Examples:

        We consider a simulation period of five days:

        >>> from hydpy import pub
        >>> pub.timegrids = "2001-01-01", "2001-01-06", "1d"

        For the second day, the maximum possible discharge is 2 m³/s does not depend on
        the water level difference.  For the fourth day, it is -4 m³/s for negative and
        4 m³/s for positive water level differences:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> waterleveldifference2maxfreedischarge(
        ...     _01_02_12 = PPoly(Poly(x0=0.0, cs=[2.0])),
        ...     _01_04_12 = PPoly(Poly(x0=-2.0, cs=[-4.0]), Poly(x0=0.0, cs=[4.0]))
        ... )
        >>> derived.toy.update()

        All results are as expected:

        >>> model.idx_sim = pub.timegrids.sim["2001-01-02"]
        >>> factors.effectivewaterleveldifference = -1.0
        >>> model.calc_maxfreedischarge_v1()
        >>> fluxes.maxfreedischarge
        maxfreedischarge(2.0)

        >>> model.idx_sim = pub.timegrids.sim["2001-01-03"]
        >>> model.calc_maxfreedischarge_v1()
        >>> fluxes.maxfreedischarge
        maxfreedischarge(-1.0)

        >>> model.idx_sim = pub.timegrids.sim["2001-01-04"]
        >>> factors.effectivewaterleveldifference = 1.0
        >>> model.calc_maxfreedischarge_v1()
        >>> fluxes.maxfreedischarge
        maxfreedischarge(4.0)

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (dam_control.WaterLevelDifference2MaxFreeDischarge,)
    DERIVEDPARAMETERS = (dam_derived.TOY,)
    REQUIREDSEQUENCES = (dam_factors.EffectiveWaterLevelDifference,)
    RESULTSEQUENCES = (dam_fluxes.MaxFreeDischarge,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        con.waterleveldifference2maxfreedischarge.inputs[0] = (
            fac.effectivewaterleveldifference
        )
        toy: int = der.toy[model.idx_sim]
        con.waterleveldifference2maxfreedischarge.calculate_values(toy)
        flu.maxfreedischarge = con.waterleveldifference2maxfreedischarge.outputs[0]


class Calc_ForcedDischarge_V1(modeltools.Method):
    r"""Calculate the actual forced water release through structures as pumps to
    prevent a too-high inner water level if a maximum water level at a remote location
    is not violated.

    In the case of a negative value for |MaxForcedDischarge| (e.g. the simulation of
    irrigation processes), the inner water level will be kept higher than a minimum
    level if the remote water level is higher than |WaterLevelMaximumThreshold|.

    Basic equation:
      .. math::
        ForcedDischarge = \begin{cases}
            MaxForcedDischarge \cdot (1 - r_1) \cdot r_2, & | MaxForcedDischarge < 0 \\
            MaxForcedDischarge \cdot r_1 \cdot (1 - r_2), & | MaxForcedDischarge \geq 0
            \end{cases}
        \\ \\
        r_1 = f_{smooth \, logistic1}(WaterLevel -
        WaterLevelMaximumThreshold, \, WaterLevelMaximumSmoothPar) \\
        r_2 = f_{smooth \, logistic1}(RemoteWaterLevel -
        RemoteWaterLevelMaximumThreshold, \, RemoteWaterLevelMaximumSmoothPar)

    Used auxiliary method:
      |smooth_logistic1|

    Examples:

        First, we prepare a |UnitTest| object to illustrate how the actual forced
        discharge depends on the inner and the remote water level:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> fluxes.maxforceddischarge = 2.0
        >>> from hydpy import UnitTest
        >>> test = UnitTest(model, model.calc_forceddischarge_v1,
        ...                 last_example=21,
        ...                 parseqs=(factors.waterlevel,
        ...                          factors.remotewaterlevel,
        ...                          fluxes.forceddischarge))
        >>> test.nexts.waterlevel = numpy.linspace(2.95, 3.15, 21)
        >>> test.nexts.remotewaterlevel = numpy.linspace(4.85, 5.05, 21)

        When setting |WaterLevelMaximumTolerance| and
        |RemoteWaterLevelMaximumTolerance| to zero, there is a discontinuous increase
        from zero to |MaxForcedDischarge| around  |WaterLevelMaximumThreshold| and a
        discontinuous decrease back to zero around |RemoteWaterLevelMaximumThreshold|:

        >>> waterlevelmaximumthreshold(3.0)
        >>> waterlevelmaximumtolerance(0.0)
        >>> derived.waterlevelmaximumsmoothpar.update()
        >>> remotewaterlevelmaximumthreshold(5.0)
        >>> remotewaterlevelmaximumtolerance(0.0)
        >>> derived.remotewaterlevelmaximumsmoothpar.update()
        >>> test()
        | ex. | waterlevel | remotewaterlevel | forceddischarge |
        ---------------------------------------------------------
        |   1 |       2.95 |             4.85 |             0.0 |
        |   2 |       2.96 |             4.86 |             0.0 |
        |   3 |       2.97 |             4.87 |             0.0 |
        |   4 |       2.98 |             4.88 |             0.0 |
        |   5 |       2.99 |             4.89 |             0.0 |
        |   6 |        3.0 |              4.9 |             1.0 |
        |   7 |       3.01 |             4.91 |             2.0 |
        |   8 |       3.02 |             4.92 |             2.0 |
        |   9 |       3.03 |             4.93 |             2.0 |
        |  10 |       3.04 |             4.94 |             2.0 |
        |  11 |       3.05 |             4.95 |             2.0 |
        |  12 |       3.06 |             4.96 |             2.0 |
        |  13 |       3.07 |             4.97 |             2.0 |
        |  14 |       3.08 |             4.98 |             2.0 |
        |  15 |       3.09 |             4.99 |             2.0 |
        |  16 |        3.1 |              5.0 |             1.0 |
        |  17 |       3.11 |             5.01 |             0.0 |
        |  18 |       3.12 |             5.02 |             0.0 |
        |  19 |       3.13 |             5.03 |             0.0 |
        |  20 |       3.14 |             5.04 |             0.0 |
        |  21 |       3.15 |             5.05 |             0.0 |

        For more natural transitions (and in the case of |WaterLevelMaximumTolerance|,
        also for computational efficiency), it is preferable to define tolerance values
        larger than zero.  We set |WaterLevelMaximumTolerance| to 15 mm and
        |RemoteWaterLevelMaximumTolerance| to 10 mm:

        >>> waterlevelmaximumtolerance(0.015)
        >>> derived.waterlevelmaximumsmoothpar.update()
        >>> remotewaterlevelmaximumtolerance(0.01)
        >>> derived.remotewaterlevelmaximumsmoothpar.update()
        >>> test()
        | ex. | waterlevel | remotewaterlevel | forceddischarge |
        ---------------------------------------------------------
        |   1 |       2.95 |             4.85 |             0.0 |
        |   2 |       2.96 |             4.86 |         0.00001 |
        |   3 |       2.97 |             4.87 |        0.000204 |
        |   4 |       2.98 |             4.88 |        0.004357 |
        |   5 |       2.99 |             4.89 |        0.089284 |
        |   6 |        3.0 |              4.9 |             1.0 |
        |   7 |       3.01 |             4.91 |        1.910716 |
        |   8 |       3.02 |             4.92 |        1.995643 |
        |   9 |       3.03 |             4.93 |        1.999796 |
        |  10 |       3.04 |             4.94 |         1.99999 |
        |  11 |       3.05 |             4.95 |             2.0 |
        |  12 |       3.06 |             4.96 |             2.0 |
        |  13 |       3.07 |             4.97 |        1.999998 |
        |  14 |       3.08 |             4.98 |        1.999796 |
        |  15 |       3.09 |             4.99 |            1.98 |
        |  16 |        3.1 |              5.0 |             1.0 |
        |  17 |       3.11 |             5.01 |            0.02 |
        |  18 |       3.12 |             5.02 |        0.000204 |
        |  19 |       3.13 |             5.03 |        0.000002 |
        |  20 |       3.14 |             5.04 |             0.0 |
        |  21 |       3.15 |             5.05 |             0.0 |

        When |MaxForcedDischarge| is negative, the flow direction is reversed.
        Forced discharge will start when the |RemoteWaterLevelMaximumThreshold|
        is higher than 4.9 and drop to zero as soon as the
        |WaterLevelMaximumThreshold| is reached.

        >>> fluxes.maxforceddischarge = -2.0
        >>> waterlevelmaximumthreshold(3.1)
        >>> remotewaterlevelmaximumthreshold(4.9)
        >>> test()
        | ex. | waterlevel | remotewaterlevel | forceddischarge |
        ---------------------------------------------------------
        |   1 |       2.95 |             4.85 |             0.0 |
        |   2 |       2.96 |             4.86 |             0.0 |
        |   3 |       2.97 |             4.87 |       -0.000002 |
        |   4 |       2.98 |             4.88 |       -0.000204 |
        |   5 |       2.99 |             4.89 |           -0.02 |
        |   6 |        3.0 |              4.9 |            -1.0 |
        |   7 |       3.01 |             4.91 |           -1.98 |
        |   8 |       3.02 |             4.92 |       -1.999796 |
        |   9 |       3.03 |             4.93 |       -1.999998 |
        |  10 |       3.04 |             4.94 |            -2.0 |
        |  11 |       3.05 |             4.95 |            -2.0 |
        |  12 |       3.06 |             4.96 |        -1.99999 |
        |  13 |       3.07 |             4.97 |       -1.999796 |
        |  14 |       3.08 |             4.98 |       -1.995643 |
        |  15 |       3.09 |             4.99 |       -1.910716 |
        |  16 |        3.1 |              5.0 |            -1.0 |
        |  17 |       3.11 |             5.01 |       -0.089284 |
        |  18 |       3.12 |             5.02 |       -0.004357 |
        |  19 |       3.13 |             5.03 |       -0.000204 |
        |  20 |       3.14 |             5.04 |        -0.00001 |
        |  21 |       3.15 |             5.05 |             0.0 |
    """

    CONTROLPARAMETERS = (
        dam_control.WaterLevelMaximumThreshold,
        dam_control.RemoteWaterLevelMaximumThreshold,
    )
    DERIVEDPARAMETERS = (
        dam_derived.WaterLevelMaximumSmoothPar,
        dam_derived.RemoteWaterLevelMaximumSmoothPar,
    )
    REQUIREDSEQUENCES = (
        dam_factors.WaterLevel,
        dam_factors.RemoteWaterLevel,
        dam_fluxes.MaxForcedDischarge,
    )
    RESULTSEQUENCES = (dam_fluxes.ForcedDischarge,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        r1: float = smoothutils.smooth_logistic1(
            fac.waterlevel - con.waterlevelmaximumthreshold,
            der.waterlevelmaximumsmoothpar,
        )
        r2: float = smoothutils.smooth_logistic1(
            fac.remotewaterlevel - con.remotewaterlevelmaximumthreshold,
            der.remotewaterlevelmaximumsmoothpar,
        )
        if flu.maxforceddischarge >= 0.0:
            flu.forceddischarge = flu.maxforceddischarge * r1 * (1.0 - r2)
        else:
            flu.forceddischarge = flu.maxforceddischarge * (1.0 - r1) * r2


class Calc_FreeDischarge_V1(modeltools.Method):
    r"""Calculate the actual water flow through a hydraulic structure like a (flap)
    sluice that generally depends on the water level gradient but can be suppressed to
    stop releasing water if a maximum water level at a remote location is violated.

    Basic equation:
      .. math::
        FreeDischarge = \omega \cdot q_{trimmed} + (1 - \omega) \cdot MaxFreeDischarge
        \\ \\
        \omega = f_{smooth \, logistic1}(RemoteWaterLevelMaximumThreshold -
        RemoteWaterLevel, \, RemoteWaterLevelMaximumSmoothPar)
        \\ \\
        q_{trimmed} = -f_{smooth \, logistic2}(MaxFreeDischarge, \, DischargeSmoothPar)


    Used auxiliary methods:
      |smooth_logistic1| |smooth_logistic2|

    Examples:

        First, we prepare a |UnitTest| object to illustrate how the actual free
        discharge depends on the possible free discharge and the remote water level:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> fluxes.maxfreedischarge = 2.0
        >>> from hydpy import UnitTest
        >>> test = UnitTest(model, model.calc_freedischarge_v1,
        ...                 last_example=21,
        ...                 parseqs=(factors.remotewaterlevel,
        ...                          fluxes.maxfreedischarge,
        ...                          fluxes.freedischarge))

        We constantly decrease |MaxFreeDischarge| and increase |RemoteWaterLevel|
        between successive examples:

        >>> test.nexts.maxfreedischarge = numpy.linspace(0.15, -0.05, 21)
        >>> test.nexts.remotewaterlevel = numpy.linspace(4.95, 5.15, 21)

        In the first two experiments, the remote water level overshoots its threshold
        while the possible discharge is still positive:

        >>> remotewaterlevelmaximumthreshold(5.0)

        When setting |RemoteWaterLevelMaximumTolerance| and |DischargeTolerance| to
        zero, the actual discharge drops suddenly to zero when the remote water level
        reaches |RemoteWaterLevelMaximumThreshold| and stays there until the possible
        discharge becomes negative:

        >>> remotewaterlevelmaximumtolerance(0.0)
        >>> derived.remotewaterlevelmaximumsmoothpar.update()
        >>> dischargetolerance(0.0)
        >>> derived.dischargesmoothpar.update()
        >>> test()
        | ex. | remotewaterlevel | maxfreedischarge | freedischarge |
        -------------------------------------------------------------
        |   1 |             4.95 |             0.15 |          0.15 |
        |   2 |             4.96 |             0.14 |          0.14 |
        |   3 |             4.97 |             0.13 |          0.13 |
        |   4 |             4.98 |             0.12 |          0.12 |
        |   5 |             4.99 |             0.11 |          0.11 |
        |   6 |              5.0 |              0.1 |          0.05 |
        |   7 |             5.01 |             0.09 |           0.0 |
        |   8 |             5.02 |             0.08 |           0.0 |
        |   9 |             5.03 |             0.07 |           0.0 |
        |  10 |             5.04 |             0.06 |           0.0 |
        |  11 |             5.05 |             0.05 |           0.0 |
        |  12 |             5.06 |             0.04 |           0.0 |
        |  13 |             5.07 |             0.03 |           0.0 |
        |  14 |             5.08 |             0.02 |           0.0 |
        |  15 |             5.09 |             0.01 |           0.0 |
        |  16 |              5.1 |              0.0 |           0.0 |
        |  17 |             5.11 |            -0.01 |         -0.01 |
        |  18 |             5.12 |            -0.02 |         -0.02 |
        |  19 |             5.13 |            -0.03 |         -0.03 |
        |  20 |             5.14 |            -0.04 |         -0.04 |
        |  21 |             5.15 |            -0.05 |         -0.05 |

        For more natural transitions (and in the case of |DischargeTolerance|, also for
        computational efficiency), defining tolerance values larger than zero is
        preferable.  We set |RemoteWaterLevelMaximumTolerance| to 10 mm and
        |DischargeTolerance| to 0.01 m³/s:

        >>> remotewaterlevelmaximumtolerance(0.01)
        >>> derived.remotewaterlevelmaximumsmoothpar.update()
        >>> dischargetolerance(0.01)
        >>> derived.dischargesmoothpar.update()
        >>> test()
        | ex. | remotewaterlevel | maxfreedischarge | freedischarge |
        -------------------------------------------------------------
        |   1 |             4.95 |             0.15 |          0.15 |
        |   2 |             4.96 |             0.14 |          0.14 |
        |   3 |             4.97 |             0.13 |          0.13 |
        |   4 |             4.98 |             0.12 |      0.119988 |
        |   5 |             4.99 |             0.11 |      0.108899 |
        |   6 |              5.0 |              0.1 |      0.049916 |
        |   7 |             5.01 |             0.09 |      0.000631 |
        |   8 |             5.02 |             0.08 |     -0.000429 |
        |   9 |             5.03 |             0.07 |     -0.000704 |
        |  10 |             5.04 |             0.06 |     -0.001127 |
        |  11 |             5.05 |             0.05 |     -0.001794 |
        |  12 |             5.06 |             0.04 |      -0.00283 |
        |  13 |             5.07 |             0.03 |     -0.004404 |
        |  14 |             5.08 |             0.02 |     -0.006723 |
        |  15 |             5.09 |             0.01 |         -0.01 |
        |  16 |              5.1 |              0.0 |     -0.014404 |
        |  17 |             5.11 |            -0.01 |         -0.02 |
        |  18 |             5.12 |            -0.02 |     -0.026723 |
        |  19 |             5.13 |            -0.03 |     -0.034404 |
        |  20 |             5.14 |            -0.04 |      -0.04283 |
        |  21 |             5.15 |            -0.05 |     -0.051794 |

        In the following two experiments, we let |MaxFreeDischarge| reach 0 m³/s
        earlier and increase |RemoteWaterLevelMaximumThreshold| so that its violation
        occurs later:

        >>> test.nexts.maxfreedischarge = numpy.linspace(0.05, -0.15, 21)
        >>> remotewaterlevelmaximumthreshold(5.1)

        Without smoothing, free discharge now strictly follows potential discharge:

        >>> remotewaterlevelmaximumtolerance(0.0)
        >>> derived.remotewaterlevelmaximumsmoothpar.update()
        >>> dischargetolerance(0.0)
        >>> derived.dischargesmoothpar.update()
        >>> test()
        | ex. | remotewaterlevel | maxfreedischarge | freedischarge |
        -------------------------------------------------------------
        |   1 |             4.95 |             0.05 |          0.05 |
        |   2 |             4.96 |             0.04 |          0.04 |
        |   3 |             4.97 |             0.03 |          0.03 |
        |   4 |             4.98 |             0.02 |          0.02 |
        |   5 |             4.99 |             0.01 |          0.01 |
        |   6 |              5.0 |              0.0 |           0.0 |
        |   7 |             5.01 |            -0.01 |         -0.01 |
        |   8 |             5.02 |            -0.02 |         -0.02 |
        |   9 |             5.03 |            -0.03 |         -0.03 |
        |  10 |             5.04 |            -0.04 |         -0.04 |
        |  11 |             5.05 |            -0.05 |         -0.05 |
        |  12 |             5.06 |            -0.06 |         -0.06 |
        |  13 |             5.07 |            -0.07 |         -0.07 |
        |  14 |             5.08 |            -0.08 |         -0.08 |
        |  15 |             5.09 |            -0.09 |         -0.09 |
        |  16 |              5.1 |             -0.1 |          -0.1 |
        |  17 |             5.11 |            -0.11 |         -0.11 |
        |  18 |             5.12 |            -0.12 |         -0.12 |
        |  19 |             5.13 |            -0.13 |         -0.13 |
        |  20 |             5.14 |            -0.14 |         -0.14 |
        |  21 |             5.15 |            -0.15 |         -0.15 |

        With smoothing, there is a slight deviation between potential and actual
        discharge:

        ToDo: Is there a smoothing alternative that circumvents this deviation without
              complicating the calculation too much?  (low priority).

        >>> remotewaterlevelmaximumtolerance(0.01)
        >>> derived.remotewaterlevelmaximumsmoothpar.update()
        >>> dischargetolerance(0.01)
        >>> derived.dischargesmoothpar.update()
        >>> test()
        | ex. | remotewaterlevel | maxfreedischarge | freedischarge |
        -------------------------------------------------------------
        |   1 |             4.95 |             0.05 |          0.05 |
        |   2 |             4.96 |             0.04 |          0.04 |
        |   3 |             4.97 |             0.03 |          0.03 |
        |   4 |             4.98 |             0.02 |          0.02 |
        |   5 |             4.99 |             0.01 |          0.01 |
        |   6 |              5.0 |              0.0 |           0.0 |
        |   7 |             5.01 |            -0.01 |         -0.01 |
        |   8 |             5.02 |            -0.02 |         -0.02 |
        |   9 |             5.03 |            -0.03 |         -0.03 |
        |  10 |             5.04 |            -0.04 |         -0.04 |
        |  11 |             5.05 |            -0.05 |         -0.05 |
        |  12 |             5.06 |            -0.06 |         -0.06 |
        |  13 |             5.07 |            -0.07 |         -0.07 |
        |  14 |             5.08 |            -0.08 |         -0.08 |
        |  15 |             5.09 |            -0.09 |     -0.090003 |
        |  16 |              5.1 |             -0.1 |     -0.100084 |
        |  17 |             5.11 |            -0.11 |     -0.110103 |
        |  18 |             5.12 |            -0.12 |     -0.120064 |
        |  19 |             5.13 |            -0.13 |      -0.13004 |
        |  20 |             5.14 |            -0.14 |     -0.140025 |
        |  21 |             5.15 |            -0.15 |     -0.150015 |
    """

    CONTROLPARAMETERS = (dam_control.RemoteWaterLevelMaximumThreshold,)
    DERIVEDPARAMETERS = (
        dam_derived.RemoteWaterLevelMaximumSmoothPar,
        dam_derived.DischargeSmoothPar,
    )
    REQUIREDSEQUENCES = (dam_factors.RemoteWaterLevel, dam_fluxes.MaxFreeDischarge)
    RESULTSEQUENCES = (dam_fluxes.FreeDischarge,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        w: float = smoothutils.smooth_logistic1(
            fac.remotewaterlevel - con.remotewaterlevelmaximumthreshold,
            der.remotewaterlevelmaximumsmoothpar,
        )
        # pylint: disable=invalid-unary-operand-type
        q_trimmed: float = -smoothutils.smooth_logistic2(
            -flu.maxfreedischarge, der.dischargesmoothpar
        )
        flu.freedischarge = w * q_trimmed + (1.0 - w) * flu.maxfreedischarge


class Calc_Outflow_V1(modeltools.Method):
    """Calculate the total outflow of the dam.

    Note that the maximum function is used to prevent from negative outflow
    values, which could otherwise occur within the required level of
    numerical accuracy.

    Basic equation:
      :math:`Outflow = max(ActualRelease + FloodDischarge, 0.)`

    Example:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> fluxes.actualrelease = 2.0
        >>> fluxes.flooddischarge = 3.0
        >>> model.calc_outflow_v1()
        >>> fluxes.outflow
        outflow(5.0)
        >>> fluxes.flooddischarge = -3.0
        >>> model.calc_outflow_v1()
        >>> fluxes.outflow
        outflow(0.0)
    """

    REQUIREDSEQUENCES = (dam_fluxes.ActualRelease, dam_fluxes.FloodDischarge)
    RESULTSEQUENCES = (dam_fluxes.Outflow,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.outflow = max(flu.actualrelease + flu.flooddischarge, 0.0)


class Calc_AllowedDischarge_V1(modeltools.Method):
    r"""Calculate the maximum discharge not leading to exceedance of the
    allowed water level drop.

    Basic equation:
      :math:`Outflow = AllowedWaterLevelDrop \cdot SurfaceArea
      + Inflow + AdjustedPrecipitation - AdjustedEvaporation + Exchange`

    Example:

        >>> from hydpy.models.dam import *
        >>> parameterstep("1d")
        >>> simulationstep("1h")
        >>> allowedwaterleveldrop(0.1)
        >>> derived.seconds.update()
        >>> fluxes.adjustedprecipitation = 1.0
        >>> fluxes.inflow = 3.0
        >>> fluxes.actualevaporation = 2.0
        >>> fluxes.exchange = 4.0
        >>> aides.surfacearea = 0.864
        >>> model.calc_alloweddischarge_v1()
        >>> aides.alloweddischarge
        alloweddischarge(7.0)
    """

    CONTROLPARAMETERS = (dam_control.AllowedWaterLevelDrop,)
    DERIVEDPARAMETERS = (dam_derived.Seconds,)
    REQUIREDSEQUENCES = (
        dam_fluxes.AdjustedPrecipitation,
        dam_fluxes.ActualEvaporation,
        dam_fluxes.Inflow,
        dam_fluxes.Exchange,
        dam_aides.SurfaceArea,
    )
    RESULTSEQUENCES = (dam_aides.AllowedDischarge,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        aid = model.sequences.aides.fastaccess
        aid.alloweddischarge = (
            con.allowedwaterleveldrop / der.seconds * aid.surfacearea * 1e6
            + flu.adjustedprecipitation
            + flu.inflow
            - flu.actualevaporation
            + flu.exchange
        )


class Calc_AllowedDischarge_V2(modeltools.Method):
    r"""Calculate the maximum discharge not leading to exceedance of the
    allowed water level drop.

    Used additional methods:
      |smooth_min1|

    Basic (discontinuous) equation:
      :math:`Outflow = min(AllowedRelease,
      AllowedWaterLevelDrop \cdot SurfaceArea + Inflow`

    Example:

        >>> from hydpy import pub
        >>> pub.timegrids = "2001.03.30", "2001.04.03", "1h"

        >>> from hydpy.models.dam import *
        >>> parameterstep("1d")

        >>> allowedwaterleveldrop(0.1)
        >>> allowedrelease(_11_01_12=1.0, _03_31_12=1.0,
        ...                _04_01_00=3.0, _04_02_00=3.0,
        ...                _04_02_12=5.0, _10_31_12=5.0)

        >>> derived.seconds.update()
        >>> derived.toy.update()

        >>> aides.surfacearea = 0.864
        >>> from hydpy import UnitTest
        >>> test = UnitTest(model,
        ...                 model.calc_alloweddischarge_v2,
        ...                 last_example=7,
        ...                 parseqs=(fluxes.inflow,
        ...                          aides.alloweddischarge))
        >>> import numpy
        >>> test.nexts.inflow = 1.0, 1.5, 1.9, 2.0, 2.1, 2.5, 3.0

        >>> model.idx_sim = pub.timegrids.init["2001-04-01"]

        >>> dischargetolerance(0.0)
        >>> derived.dischargesmoothpar.update()
        >>> test()
        | ex. | inflow | alloweddischarge |
        -----------------------------------
        |   1 |    1.0 |              2.0 |
        |   2 |    1.5 |              2.5 |
        |   3 |    1.9 |              2.9 |
        |   4 |    2.0 |              3.0 |
        |   5 |    2.1 |              3.0 |
        |   6 |    2.5 |              3.0 |
        |   7 |    3.0 |              3.0 |

        >>> dischargetolerance(0.1)
        >>> derived.dischargesmoothpar.update()
        >>> test()
        | ex. | inflow | alloweddischarge |
        -----------------------------------
        |   1 |    1.0 |              2.0 |
        |   2 |    1.5 |         2.499987 |
        |   3 |    1.9 |             2.89 |
        |   4 |    2.0 |         2.959017 |
        |   5 |    2.1 |             2.99 |
        |   6 |    2.5 |         2.999987 |
        |   7 |    3.0 |              3.0 |

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (dam_control.AllowedRelease, dam_control.AllowedWaterLevelDrop)
    DERIVEDPARAMETERS = (
        dam_derived.TOY,
        dam_derived.Seconds,
        dam_derived.DischargeSmoothPar,
    )
    REQUIREDSEQUENCES = (dam_fluxes.Inflow, dam_aides.SurfaceArea)
    RESULTSEQUENCES = (dam_aides.AllowedDischarge,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        aid = model.sequences.aides.fastaccess
        aid.alloweddischarge = smoothutils.smooth_min1(
            con.allowedwaterleveldrop / der.seconds * aid.surfacearea * 1e6
            + flu.inflow,
            con.allowedrelease[der.toy[model.idx_sim]],
            der.dischargesmoothpar,
        )


class Calc_Outflow_V2(modeltools.Method):
    """Calculate the total outflow of the dam, taking the allowed water discharge into
    account.

    Used additional method:
      |Fix_Min1_V1|

    Basic (discontinuous) equation:
      :math:`Outflow = min(FloodDischarge, AllowedDischarge)`

    Examples:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> from hydpy import UnitTest
        >>> test = UnitTest(model,
        ...                 model.calc_outflow_v2,
        ...                 last_example=8,
        ...                 parseqs=(fluxes.flooddischarge,
        ...                          fluxes.outflow))
        >>> test.nexts.flooddischarge = range(8)

        >>> aides.alloweddischarge = 3.0

        >>> dischargetolerance(0.0)
        >>> derived.dischargesmoothpar.update()
        >>> test()
        | ex. | flooddischarge | outflow |
        ----------------------------------
        |   1 |            0.0 |     0.0 |
        |   2 |            1.0 |     1.0 |
        |   3 |            2.0 |     2.0 |
        |   4 |            3.0 |     3.0 |
        |   5 |            4.0 |     3.0 |
        |   6 |            5.0 |     3.0 |
        |   7 |            6.0 |     3.0 |
        |   8 |            7.0 |     3.0 |


        >>> dischargetolerance(1.0)
        >>> derived.dischargesmoothpar.update()
        >>> test()
        | ex. | flooddischarge |  outflow |
        -----------------------------------
        |   1 |            0.0 |      0.0 |
        |   2 |            1.0 | 0.999651 |
        |   3 |            2.0 |     1.99 |
        |   4 |            3.0 | 2.794476 |
        |   5 |            4.0 | 2.985755 |
        |   6 |            5.0 | 2.991603 |
        |   7 |            6.0 | 2.991773 |
        |   8 |            7.0 | 2.991779 |

        >>> aides.alloweddischarge = 0.0
        >>> test()
        | ex. | flooddischarge | outflow |
        ----------------------------------
        |   1 |            0.0 |     0.0 |
        |   2 |            1.0 |     0.0 |
        |   3 |            2.0 |     0.0 |
        |   4 |            3.0 |     0.0 |
        |   5 |            4.0 |     0.0 |
        |   6 |            5.0 |     0.0 |
        |   7 |            6.0 |     0.0 |
        |   8 |            7.0 |     0.0 |
    """

    DERIVEDPARAMETERS = (dam_derived.DischargeSmoothPar,)
    REQUIREDSEQUENCES = (dam_fluxes.FloodDischarge, dam_aides.AllowedDischarge)
    RESULTSEQUENCES = (dam_fluxes.Outflow,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        aid = model.sequences.aides.fastaccess
        flu.outflow = model.fix_min1_v1(
            flu.flooddischarge, aid.alloweddischarge, der.dischargesmoothpar, False
        )


class Calc_Outflow_V3(modeltools.Method):
    """Take the forced discharge as the only outflow.

    Basic equation:
      :math:`Outflow = ForcedDischaerge`

    Example:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> fluxes.forceddischarge = 2.0
        >>> model.calc_outflow_v3()
        >>> fluxes.outflow
        outflow(2.0)
    """

    REQUIREDSEQUENCES = (dam_fluxes.ForcedDischarge,)
    RESULTSEQUENCES = (dam_fluxes.Outflow,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.outflow = flu.forceddischarge


class Calc_Outflow_V4(modeltools.Method):
    """Take the free discharge as the only outflow.

    Basic equation:
      :math:`Outflow = FreeDischaerge`

    Example:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> fluxes.freedischarge = 2.0
        >>> model.calc_outflow_v4()
        >>> fluxes.outflow
        outflow(2.0)
    """

    REQUIREDSEQUENCES = (dam_fluxes.FreeDischarge,)
    RESULTSEQUENCES = (dam_fluxes.Outflow,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.outflow = flu.freedischarge


class Calc_Outflow_V5(modeltools.Method):
    """Calculate the total outflow as the sum of free and forced discharge.

    Basic equation:
      :math:`Outflow = FreeDischarge + ForcedDischarge`

    Example:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> fluxes.freedischarge = 2.0
        >>> fluxes.forceddischarge = 3.0
        >>> model.calc_outflow_v5()
        >>> fluxes.outflow
        outflow(5.0)
    """

    REQUIREDSEQUENCES = (dam_fluxes.FreeDischarge, dam_fluxes.ForcedDischarge)
    RESULTSEQUENCES = (dam_fluxes.Outflow,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.outflow = flu.freedischarge + flu.forceddischarge


class Update_WaterVolume_V1(modeltools.Method):
    r"""Update the actual water volume.

    Basic equation:
      :math:`\frac{d}{dt}WaterVolume =
      1e-6 \cdot (AdjustedPrecipitation - AdjustedEvaporation - Inflow - Outflow)`

    Example:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> derived.seconds = 2e6
        >>> states.watervolume.old = 5.0
        >>> fluxes.adjustedprecipitation = 1.0
        >>> fluxes.actualevaporation = 2.0
        >>> fluxes.inflow = 3.0
        >>> fluxes.outflow = 4.0
        >>> model.update_watervolume_v1()
        >>> states.watervolume
        watervolume(1.0)
    """

    DERIVEDPARAMETERS = (dam_derived.Seconds,)
    REQUIREDSEQUENCES = (
        dam_fluxes.AdjustedPrecipitation,
        dam_fluxes.ActualEvaporation,
        dam_fluxes.Inflow,
        dam_fluxes.Outflow,
    )
    UPDATEDSEQUENCES = (dam_states.WaterVolume,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        new.watervolume = old.watervolume + der.seconds / 1e6 * (
            flu.adjustedprecipitation - flu.actualevaporation + flu.inflow - flu.outflow
        )


class Update_WaterVolume_V2(modeltools.Method):
    r"""Update the actual water volume.

    Basic equation:
      :math:`\frac{d}{dt}WaterVolume = 10^{-6} \cdot (AdjustedPrecipitation -
      AdjustedEvaporation - Inflow - Outflow - ActualRemoteRelease)`

    Example:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> derived.seconds = 2e6
        >>> states.watervolume.old = 9.0
        >>> fluxes.adjustedprecipitation = 2.0
        >>> fluxes.actualevaporation = 1.0
        >>> fluxes.inflow = 4.0
        >>> fluxes.outflow = 3.0
        >>> fluxes.actualremoterelease = 6.0
        >>> model.update_watervolume_v2()
        >>> states.watervolume
        watervolume(1.0)
    """

    DERIVEDPARAMETERS = (dam_derived.Seconds,)
    REQUIREDSEQUENCES = (
        dam_fluxes.AdjustedPrecipitation,
        dam_fluxes.ActualEvaporation,
        dam_fluxes.Inflow,
        dam_fluxes.Outflow,
        dam_fluxes.ActualRemoteRelease,
    )
    UPDATEDSEQUENCES = (dam_states.WaterVolume,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        new.watervolume = old.watervolume + der.seconds / 1e6 * (
            flu.adjustedprecipitation
            - flu.actualevaporation
            + flu.inflow
            - flu.outflow
            - flu.actualremoterelease
        )


class Update_WaterVolume_V3(modeltools.Method):
    r"""Update the actual water volume.

    Basic equation:
      :math:`\frac{d}{dt}WaterVolume = 10^{-6} \cdot
      (AdjustedPrecipitation - AdjustedEvaporation + Inflow - Outflow -
      ActualRemoteRelease - ActualRemoteRelief)`

    Example:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> derived.seconds = 2e6
        >>> states.watervolume.old = 6.0
        >>> fluxes.adjustedprecipitation = 5.0
        >>> fluxes.actualevaporation = 4.0
        >>> fluxes.inflow = 2.0
        >>> fluxes.outflow = 3.0
        >>> fluxes.actualremoterelease = 1.0
        >>> fluxes.actualremoterelief = 0.5
        >>> model.update_watervolume_v3()
        >>> states.watervolume
        watervolume(3.0)
    """

    DERIVEDPARAMETERS = (dam_derived.Seconds,)
    REQUIREDSEQUENCES = (
        dam_fluxes.AdjustedPrecipitation,
        dam_fluxes.ActualEvaporation,
        dam_fluxes.Inflow,
        dam_fluxes.Outflow,
        dam_fluxes.ActualRemoteRelease,
        dam_fluxes.ActualRemoteRelief,
    )
    UPDATEDSEQUENCES = (dam_states.WaterVolume,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        new.watervolume = old.watervolume + (der.seconds / 1e6) * (
            flu.adjustedprecipitation
            - flu.actualevaporation
            + flu.inflow
            - flu.outflow
            - flu.actualremoterelease
            - flu.actualremoterelief
        )


class Update_WaterVolume_V4(modeltools.Method):
    r"""Update the actual water volume.

    Basic equation:
      :math:`\frac{d}{dt}WaterVolume = 1e-6 \cdot
      (AdjustedPrecipitation - AdjustedEvaporation - Inflow - Outflow + Exchange)`

    Example:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> derived.seconds = 2e6
        >>> states.watervolume.old = 5.0
        >>> fluxes.adjustedprecipitation = 1.0
        >>> fluxes.actualevaporation = 2.0
        >>> fluxes.inflow = 3.0
        >>> fluxes.outflow = 4.0
        >>> fluxes.exchange = 5.0
        >>> model.update_watervolume_v4()
        >>> states.watervolume
        watervolume(11.0)
    """

    DERIVEDPARAMETERS = (dam_derived.Seconds,)
    REQUIREDSEQUENCES = (
        dam_fluxes.AdjustedPrecipitation,
        dam_fluxes.ActualEvaporation,
        dam_fluxes.Inflow,
        dam_fluxes.Outflow,
        dam_fluxes.Exchange,
    )
    UPDATEDSEQUENCES = (dam_states.WaterVolume,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        new.watervolume = old.watervolume + der.seconds / 1e6 * (
            flu.adjustedprecipitation
            - flu.actualevaporation
            + flu.inflow
            - flu.outflow
            + flu.exchange
        )


class Pass_Outflow_V1(modeltools.Method):
    """Update the outlet link sequence |dam_outlets.Q|.

    Basic equation:
      :math:`Q = Outflow`
    """

    REQUIREDSEQUENCES = (dam_fluxes.Outflow,)
    RESULTSEQUENCES = (dam_outlets.Q,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        out = model.sequences.outlets.fastaccess
        out.q[0] += flu.outflow


class Pass_ActualRemoteRelease_V1(modeltools.Method):
    """Update the outlet link sequence |dam_outlets.S|.

    Basic equation:
      :math:`S = ActualRemoteRelease`
    """

    REQUIREDSEQUENCES = (dam_fluxes.ActualRemoteRelease,)
    RESULTSEQUENCES = (dam_outlets.S,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        out = model.sequences.outlets.fastaccess
        out.s[0] += flu.actualremoterelease


class Pass_ActualRemoteRelief_V1(modeltools.Method):
    """Update the outlet link sequence |dam_outlets.R|.

    Basic equation:
      :math:`R = ActualRemoteRelief`
    """

    REQUIREDSEQUENCES = (dam_fluxes.ActualRemoteRelief,)
    RESULTSEQUENCES = (dam_outlets.R,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        out = model.sequences.outlets.fastaccess
        out.r[0] += flu.actualremoterelief


class Pass_MissingRemoteRelease_V1(modeltools.Method):
    """Update the outlet link sequence |dam_senders.D|.

    Basic equation:
      :math:`D = MissingRemoteRelease`
    """

    REQUIREDSEQUENCES = (dam_fluxes.MissingRemoteRelease,)
    RESULTSEQUENCES = (dam_senders.D,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        sen = model.sequences.senders.fastaccess
        sen.d[0] += flu.missingremoterelease


class Pass_AllowedRemoteRelief_V1(modeltools.Method):
    """Update the outlet link sequence |dam_outlets.R|.

    Basic equation:
      :math:`R = AllowedRemoteRelief`
    """

    REQUIREDSEQUENCES = (dam_fluxes.AllowedRemoteRelief,)
    RESULTSEQUENCES = (dam_senders.R,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        sen = model.sequences.senders.fastaccess
        sen.r[0] += flu.allowedremoterelief


class Pass_RequiredRemoteSupply_V1(modeltools.Method):
    """Update the outlet link sequence |dam_outlets.S|.

    Basic equation:
      :math:`S = RequiredRemoteSupply`
    """

    REQUIREDSEQUENCES = (dam_fluxes.RequiredRemoteSupply,)
    RESULTSEQUENCES = (dam_senders.S,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        sen = model.sequences.senders.fastaccess
        sen.s[0] += flu.requiredremotesupply


class Update_LoggedOutflow_V1(modeltools.Method):
    """Log a new entry of discharge at a cross section far downstream.

    Example:

        The following example shows that, with each new method call, the
        three memorized values are successively moved to the right and the
        respective new value is stored on the bare left position:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> nmblogentries(3)
        >>> logs.loggedoutflow = 0.0
        >>> from hydpy import UnitTest
        >>> test = UnitTest(model,
        ...                 model.update_loggedoutflow_v1,
        ...                 last_example=4,
        ...                 parseqs=(fluxes.outflow,
        ...                          logs.loggedoutflow))
        >>> test.nexts.outflow = [1.0, 3.0, 2.0, 4.0]
        >>> del test.inits.loggedoutflow
        >>> test()
        | ex. | outflow |           loggedoutflow |
        -------------------------------------------
        |   1 |     1.0 | 1.0  0.0            0.0 |
        |   2 |     3.0 | 3.0  1.0            0.0 |
        |   3 |     2.0 | 2.0  3.0            1.0 |
        |   4 |     4.0 | 4.0  2.0            3.0 |
    """

    CONTROLPARAMETERS = (dam_control.NmbLogEntries,)
    REQUIREDSEQUENCES = (dam_fluxes.Outflow,)
    UPDATEDSEQUENCES = (dam_logs.LoggedOutflow,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        for idx in range(con.nmblogentries - 1, 0, -1):
            log.loggedoutflow[idx] = log.loggedoutflow[idx - 1]
        log.loggedoutflow[0] = flu.outflow


class Model(modeltools.ELSModel):
    """|dam.DOCNAME.complete|"""

    DOCNAME = modeltools.DocName(short="Dam")

    SOLVERPARAMETERS = (
        dam_solver.AbsErrorMax,
        dam_solver.RelErrorMax,
        dam_solver.RelDTMin,
        dam_solver.RelDTMax,
    )
    SOLVERSEQUENCES = ()
    INLET_METHODS = (
        Calc_Precipitation_V1,
        Calc_AdjustedPrecipitation_V1,
        Calc_PotentialEvaporation_V1,
        Calc_AdjustedEvaporation_V1,
        Calc_ActualEvaporation_V1,
        Pic_Inflow_V1,
        Pic_Inflow_V2,
        Calc_NaturalRemoteDischarge_V1,
        Calc_RemoteDemand_V1,
        Calc_RemoteFailure_V1,
        Calc_RequiredRemoteRelease_V1,
        Calc_RequiredRelease_V1,
        Calc_RequiredRelease_V2,
        Calc_TargetedRelease_V1,
    )
    RECEIVER_METHODS = (
        Pic_TotalRemoteDischarge_V1,
        Update_LoggedTotalRemoteDischarge_V1,
        Pick_LoggedOuterWaterLevel_V1,
        Pick_LoggedRemoteWaterLevel_V1,
        Pic_LoggedRequiredRemoteRelease_V1,
        Pic_LoggedRequiredRemoteRelease_V2,
        Calc_RequiredRemoteRelease_V2,
        Pic_LoggedAllowedRemoteRelief_V1,
        Calc_AllowedRemoteRelief_V1,
    )
    ADD_METHODS = (Fix_Min1_V1,)
    PART_ODE_METHODS = (
        Pic_Inflow_V1,
        Pic_Inflow_V2,
        Calc_WaterLevel_V1,
        Calc_OuterWaterLevel_V1,
        Calc_RemoteWaterLevel_V1,
        Calc_WaterLevelDifference_V1,
        Calc_EffectiveWaterLevelDifference_V1,
        Calc_SurfaceArea_V1,
        Calc_AllowedDischarge_V1,
        Calc_AllowedDischarge_V2,
        Calc_ActualRelease_V1,
        Calc_ActualRelease_V2,
        Calc_ActualRelease_V3,
        Calc_PossibleRemoteRelief_V1,
        Calc_ActualRemoteRelief_V1,
        Calc_ActualRemoteRelease_V1,
        Update_ActualRemoteRelief_V1,
        Update_ActualRemoteRelease_V1,
        Calc_FloodDischarge_V1,
        Calc_MaxForcedDischarge_V1,
        Calc_MaxFreeDischarge_V1,
        Calc_ForcedDischarge_V1,
        Calc_FreeDischarge_V1,
        Calc_Outflow_V1,
        Calc_Outflow_V2,
        Calc_Outflow_V3,
        Calc_Outflow_V4,
        Calc_Outflow_V5,
    )
    FULL_ODE_METHODS = (
        Update_WaterVolume_V1,
        Update_WaterVolume_V2,
        Update_WaterVolume_V3,
        Update_WaterVolume_V4,
    )
    OUTLET_METHODS = (
        Pass_Outflow_V1,
        Update_LoggedOutflow_V1,
        Pass_ActualRemoteRelease_V1,
        Pass_ActualRemoteRelief_V1,
    )
    SENDER_METHODS = (
        Calc_MissingRemoteRelease_V1,
        Pass_MissingRemoteRelease_V1,
        Calc_AllowedRemoteRelief_V2,
        Pass_AllowedRemoteRelief_V1,
        Calc_RequiredRemoteSupply_V1,
        Pass_RequiredRemoteSupply_V1,
    )
    SUBMODELINTERFACES = ()
    SUBMODELS = ()

    precipmodel = modeltools.SubmodelProperty(
        precipinterfaces.PrecipModel_V2, optional=True
    )
    precipmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    precipmodel_typeid = modeltools.SubmodelTypeIDProperty()

    pemodel = modeltools.SubmodelProperty(petinterfaces.PETModel_V1, optional=True)
    pemodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    pemodel_typeid = modeltools.SubmodelTypeIDProperty()


class Main_PrecipModel_V2(modeltools.ELSModel):
    """Base class for |dam.DOCNAME.long| models that use submodels that comply with the
    |PrecipModel_V2| interface."""

    precipmodel: modeltools.SubmodelProperty
    precipmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    precipmodel_typeid = modeltools.SubmodelTypeIDProperty()

    @importtools.prepare_submodel(
        "precipmodel",
        precipinterfaces.PrecipModel_V2,
        precipinterfaces.PrecipModel_V2.prepare_nmbzones,
        precipinterfaces.PrecipModel_V2.prepare_subareas,
    )
    def add_precipmodel_v2(
        self,
        precipmodel: precipinterfaces.PrecipModel_V2,
        /,
        *,
        refresh: bool,  # pylint: disable=unused-argument
    ) -> None:
        """Initialise the given `precipmodel` that follows the |PrecipModel_V2|
        interface.

        >>> from hydpy.models.dam_v001 import *
        >>> parameterstep()
        >>> surfacearea(2.0)
        >>> with model.add_precipmodel_v2("meteo_precip_io"):
        ...     nmbhru
        ...     hruarea
        ...     precipitationfactor(1.5)
        nmbhru(1)
        hruarea(2.0)
        >>> model.precipmodel.parameters.control.precipitationfactor
        precipitationfactor(1.5)
        """
        control = self.parameters.control
        precipmodel.prepare_nmbzones(1)
        precipmodel.prepare_subareas(control.surfacearea.value)


class Main_PEModel_V1(modeltools.ELSModel):
    """Base class for |dam.DOCNAME.long| models that use submodels that comply with the
    |PETModel_V1| interface."""

    pemodel: modeltools.SubmodelProperty
    pemodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    pemodel_typeid = modeltools.SubmodelTypeIDProperty()

    @importtools.prepare_submodel(
        "pemodel",
        petinterfaces.PETModel_V1,
        petinterfaces.PETModel_V1.prepare_nmbzones,
        petinterfaces.PETModel_V1.prepare_subareas,
    )
    def add_pemodel_v1(
        self,
        pemodel: petinterfaces.PETModel_V1,
        /,
        *,
        refresh: bool,  # pylint: disable=unused-argument
    ) -> None:
        """Initialise the given `pemodel` that follows the |PETModel_V1| interface.

        >>> from hydpy.models.dam_v001 import *
        >>> parameterstep()
        >>> surfacearea(2.0)
        >>> with model.add_pemodel_v1("evap_ret_tw2002"):
        ...     nmbhru
        ...     hruarea
        ...     evapotranspirationfactor(1.5)
        nmbhru(1)
        hruarea(2.0)

        >>> model.pemodel.parameters.control.evapotranspirationfactor
        evapotranspirationfactor(1.5)
        """
        control = self.parameters.control
        pemodel.prepare_nmbzones(1)
        pemodel.prepare_subareas(control.surfacearea.value)
