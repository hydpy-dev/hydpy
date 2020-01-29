# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# imports...
# ...from HydPy
from hydpy.core import modeltools
from hydpy.cythons.autogen import smoothutils
from hydpy.models.dam import dam_control
from hydpy.models.dam import dam_derived
from hydpy.models.dam import dam_solver
from hydpy.models.dam import dam_fluxes
from hydpy.models.dam import dam_states
from hydpy.models.dam import dam_logs
from hydpy.models.dam import dam_aides
from hydpy.models.dam import dam_inlets
from hydpy.models.dam import dam_receivers
from hydpy.models.dam import dam_outlets
from hydpy.models.dam import dam_senders


class Pic_Inflow_V1(modeltools.Method):
    """Update the inlet link sequence.

    Basic equation:
      :math:`Inflow = Q`
    """
    REQUIREDSEQUENCES = (
        dam_inlets.Q,
    )
    RESULTSEQUENCES = (
        dam_fluxes.Inflow,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        inl = model.sequences.inlets.fastaccess
        flu.inflow = inl.q[0]


class Pic_Inflow_V2(modeltools.Method):
    """Update the inlet link sequences.

    Basic equation:
      :math:`Inflow = Q + S + R`
    """
    REQUIREDSEQUENCES = (
        dam_inlets.Q,
        dam_inlets.S,
        dam_inlets.R,
    )
    RESULTSEQUENCES = (
        dam_fluxes.Inflow,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        inl = model.sequences.inlets.fastaccess
        flu.inflow = inl.q[0]+inl.s[0]+inl.r[0]


class Pic_TotalRemoteDischarge_V1(modeltools.Method):
    """Update the receiver link sequence.

    Basic equation:
      :math:`TotalRemoteDischarge = Q`
    """
    REQUIREDSEQUENCES = (
        dam_receivers.Q,
    )
    RESULTSEQUENCES = (
        dam_fluxes.TotalRemoteDischarge,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        rec = model.sequences.receivers.fastaccess
        flu.totalremotedischarge = rec.q[0]


class Pic_LoggedRequiredRemoteRelease_V1(modeltools.Method):
    """Update the receiver link sequence.

    Basic equation:
      :math:`LoggedRequiredRemoteRelease = D`
    """
    REQUIREDSEQUENCES = (
        dam_receivers.D,
    )
    RESULTSEQUENCES = (
        dam_logs.LoggedRequiredRemoteRelease,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        log = model.sequences.logs.fastaccess
        rec = model.sequences.receivers.fastaccess
        log.loggedrequiredremoterelease[0] = rec.d[0]


class Pic_LoggedRequiredRemoteRelease_V2(modeltools.Method):
    """Update the receiver link sequence.

    Basic equation:
      :math:`LoggedRequiredRemoteRelease = S`
    """
    REQUIREDSEQUENCES = (
        dam_receivers.S,
    )
    RESULTSEQUENCES = (
        dam_logs.LoggedRequiredRemoteRelease,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        log = model.sequences.logs.fastaccess
        rec = model.sequences.receivers.fastaccess
        log.loggedrequiredremoterelease[0] = rec.s[0]


class Pic_LoggedAllowedRemoteRelieve_V1(modeltools.Method):
    """Update the receiver link sequence.

    Basic equation:
      :math:`LoggedAllowedRemoteRelieve = R`
    """
    REQUIREDSEQUENCES = (
        dam_receivers.R,
    )
    RESULTSEQUENCES = (
        dam_logs.LoggedAllowedRemoteRelieve,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        log = model.sequences.logs.fastaccess
        rec = model.sequences.receivers.fastaccess
        log.loggedallowedremoterelieve[0] = rec.r[0]


class Update_LoggedTotalRemoteDischarge_V1(modeltools.Method):
    """Log a new entry of discharge at a cross section far downstream.

    Example:

        The following example shows that, with each new method call, the
        three memorized values are successively moved to the right and the
        respective new value is stored on the bare left position:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> nmblogentries(3)
        >>> logs.loggedtotalremotedischarge = 0.0
        >>> from hydpy import UnitTest
        >>> test = UnitTest(model, model.update_loggedtotalremotedischarge_v1,
        ...                 last_example=4,
        ...                 parseqs=(fluxes.totalremotedischarge,
        ...                          logs.loggedtotalremotedischarge))
        >>> test.nexts.totalremotedischarge = [1., 3., 2., 4]
        >>> del test.inits.loggedtotalremotedischarge
        >>> test()
        | ex. | totalremotedischarge |           loggedtotalremotedischarge |
        ---------------------------------------------------------------------
        |   1 |                  1.0 | 1.0  0.0                         0.0 |
        |   2 |                  3.0 | 3.0  1.0                         0.0 |
        |   3 |                  2.0 | 2.0  3.0                         1.0 |
        |   4 |                  4.0 | 4.0  2.0                         3.0 |
    """
    CONTROLPARAMETERS = (
        dam_control.NmbLogEntries,
    )
    REQUIREDSEQUENCES = (
        dam_fluxes.TotalRemoteDischarge,
    )
    UPDATEDSEQUENCES = (
        dam_logs.LoggedTotalRemoteDischarge,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        for idx in range(con.nmblogentries-1, 0, -1):
            log.loggedtotalremotedischarge[idx] = \
                                    log.loggedtotalremotedischarge[idx-1]
        log.loggedtotalremotedischarge[0] = flu.totalremotedischarge


class Calc_WaterLevel_V1(modeltools.Method):
    """Determine the water level based on an artificial neural network
    describing the relationship between water level and water stage.

    Example:

        Prepare a dam model:

        >>> from hydpy.models.dam import *
        >>> parameterstep()

        Prepare a very simple relationship based on one single neuron:

        >>> watervolume2waterlevel(
        ...         nmb_inputs=1, nmb_neurons=(1,), nmb_outputs=1,
        ...         weights_input=0.5, weights_output=1.0,
        ...         intercepts_hidden=0.0, intercepts_output=-0.5)

        At least in the water volume range used in the following examples,
        the shape of the relationship looks acceptable:

        >>> from hydpy import UnitTest
        >>> test = UnitTest(
        ...     model, model.calc_waterlevel_v1,
        ...     last_example=10,
        ...     parseqs=(states.watervolume, aides.waterlevel))
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

        For more realistic approximations of measured relationships between
        water level and volume, larger neural networks are required.
    """
    CONTROLPARAMETERS = (
        dam_control.WaterVolume2WaterLevel,
    )
    REQUIREDSEQUENCES = (
        dam_states.WaterVolume,
    )
    RESULTSEQUENCES = (
        dam_aides.WaterLevel,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        new = model.sequences.states.fastaccess_new
        aid = model.sequences.aides.fastaccess
        con.watervolume2waterlevel.inputs[0] = new.watervolume
        con.watervolume2waterlevel.process_actual_input()
        aid.waterlevel = con.watervolume2waterlevel.outputs[0]


class Calc_AllowedRemoteRelieve_V2(modeltools.Method):
    """Calculate the allowed maximum relieve another location
    is allowed to discharge into the dam.

    Used auxiliary method:
      |smooth_logistic1|

    Basic equation:
      :math:`ActualRemoteRelieve = HighestRemoteRelieve \\cdot
      smooth_{logistic1}(WaterLevelRelieveThreshold-WaterLevel,
      WaterLevelRelieveSmoothPar)`

    Examples:

        All control parameters that are involved in the calculation of
        |AllowedRemoteRelieve| are derived from |SeasonalParameter|.
        This allows to simulate seasonal dam control schemes.
        To show how this works, we first define a short simulation
        time period of only two days:

        >>> from hydpy import pub
        >>> pub.timegrids = '2001.03.30', '2001.04.03', '1d'

        Now we prepare the dam model and define two different control
        schemes for the hydrological summer (April to October) and
        winter month (November to May)

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> highestremoterelieve(_11_1_12=1.0, _03_31_12=1.0,
        ...                      _04_1_12=2.0, _10_31_12=2.0)
        >>> waterlevelrelievethreshold(_11_1_12=3.0, _03_31_12=2.0,
        ...                            _04_1_12=4.0, _10_31_12=4.0)
        >>> waterlevelrelievetolerance(_11_1_12=0.0, _03_31_12=0.0,
        ...                            _04_1_12=1.0, _10_31_12=1.0)
        >>> derived.waterlevelrelievesmoothpar.update()
        >>> derived.toy.update()

        The following test function is supposed to calculate
        |AllowedRemoteRelieve| for values of |WaterLevel| ranging
        from 0 and 8 m:

        >>> from hydpy import UnitTest
        >>> test = UnitTest(model,
        ...                 model.calc_allowedremoterelieve_v2,
        ...                 last_example=9,
        ...                 parseqs=(aides.waterlevel,
        ...                          fluxes.allowedremoterelieve))
        >>> test.nexts.waterlevel = range(9)

        On March 30 (which is the last day of the winter month and the
        first day of the simulation period), the value of
        |WaterLevelRelieveSmoothPar| is zero.  Hence, |AllowedRemoteRelieve|
        drops abruptly from 1 m³/s (the value of |HighestRemoteRelieve|) to
        0 m³/s, as soon as |WaterLevel| reaches 3 m (the value
        of |WaterLevelRelieveThreshold|):

        >>> model.idx_sim = pub.timegrids.init['2001.03.30']
        >>> test(first_example=2, last_example=6)
        | ex. | waterlevel | allowedremoterelieve |
        -------------------------------------------
        |   3 |        1.0 |                  1.0 |
        |   4 |        2.0 |                  1.0 |
        |   5 |        3.0 |                  0.0 |
        |   6 |        4.0 |                  0.0 |

        On April 1 (which is the first day of the sommer month and the
        last day of the simulation period), all parameter values are
        increased.  The value of parameter |WaterLevelRelieveSmoothPar|
        is 1 m.  Hence, loosely speaking, |AllowedRemoteRelieve| approaches
        the "discontinuous extremes (2 m³/s -- which is the value of
        |HighestRemoteRelieve| -- and 0 m³/s) to 99 % within a span of
        2 m³/s around the original threshold value of 4 m³/s defined by
        |WaterLevelRelieveThreshold|:

        >>> model.idx_sim = pub.timegrids.init['2001.04.01']
        >>> test()
        | ex. | waterlevel | allowedremoterelieve |
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
    """
    CONTROLPARAMETERS = (
        dam_control.HighestRemoteRelieve,
        dam_control.WaterLevelRelieveThreshold,
    )
    DERIVEDPARAMETERS = (
        dam_derived.TOY,
        dam_derived.WaterLevelRelieveSmoothPar,
    )
    REQUIREDSEQUENCES = (
        dam_aides.WaterLevel,
    )
    RESULTSEQUENCES = (
        dam_fluxes.AllowedRemoteRelieve,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        aid = model.sequences.aides.fastaccess
        toy = der.toy[model.idx_sim]
        flu.allowedremoterelieve = (
            con.highestremoterelieve[toy] *
            smoothutils.smooth_logistic1(
                con.waterlevelrelievethreshold[toy]-aid.waterlevel,
                der.waterlevelrelievesmoothpar[toy]))


class Calc_RequiredRemoteSupply_V1(modeltools.Method):
    """Calculate the required maximum supply from another location
    that can be discharged into the dam.

    Used auxiliary method:
      |smooth_logistic1|

    Basic equation:
      :math:`RequiredRemoteSupply = HighestRemoteSupply \\cdot
      smooth_{logistic1}(WaterLevelSupplyThreshold-WaterLevel,
      WaterLevelSupplySmoothPar)`

    Examples:

        Method |Calc_RequiredRemoteSupply_V1| is functionally identical
        with method |Calc_AllowedRemoteRelieve_V2|.  Hence the following
        examples serve for testing purposes only (see the documentation
        on function |Calc_AllowedRemoteRelieve_V2| for more detailed
        information):

        >>> from hydpy import pub
        >>> pub.timegrids = '2001.03.30', '2001.04.03', '1d'
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
        ...                 parseqs=(aides.waterlevel,
        ...                          fluxes.requiredremotesupply))
        >>> test.nexts.waterlevel = range(9)
        >>> model.idx_sim = pub.timegrids.init['2001.03.30']
        >>> test(first_example=2, last_example=6)
        | ex. | waterlevel | requiredremotesupply |
        -------------------------------------------
        |   3 |        1.0 |                  1.0 |
        |   4 |        2.0 |                  1.0 |
        |   5 |        3.0 |                  0.0 |
        |   6 |        4.0 |                  0.0 |
        >>> model.idx_sim = pub.timegrids.init['2001.04.01']
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
    """
    CONTROLPARAMETERS = (
        dam_control.HighestRemoteSupply,
        dam_control.WaterLevelSupplyThreshold,
    )
    DERIVEDPARAMETERS = (
        dam_derived.TOY,
        dam_derived.WaterLevelSupplySmoothPar,
    )
    REQUIREDSEQUENCES = (
        dam_aides.WaterLevel,
    )
    RESULTSEQUENCES = (
        dam_fluxes.RequiredRemoteSupply,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        aid = model.sequences.aides.fastaccess
        toy = der.toy[model.idx_sim]
        flu.requiredremotesupply = (
            con.highestremotesupply[toy] *
            smoothutils.smooth_logistic1(
                con.waterlevelsupplythreshold[toy]-aid.waterlevel,
                der.waterlevelsupplysmoothpar[toy]))


class Calc_NaturalRemoteDischarge_V1(modeltools.Method):
    """Try to estimate the natural discharge of a cross section far downstream
    based on the last few simulation steps.

    Basic equation:
      :math:`RemoteDemand =
      max(\\frac{\\Sigma(LoggedTotalRemoteDischarge - LoggedOutflow)}
      {NmbLogEntries}), 0)`

    Examples:

        Usually, the mean total remote flow should be larger than the mean
        dam outflows.  Then the estimated natural remote discharge is simply
        the difference of both mean values:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> nmblogentries(3)
        >>> logs.loggedtotalremotedischarge(2.5, 2.0, 1.5)
        >>> logs.loggedoutflow(2.0, 1.0, 0.0)
        >>> model.calc_naturalremotedischarge_v1()
        >>> fluxes.naturalremotedischarge
        naturalremotedischarge(1.0)

        Due to the wave travel times, the difference between remote discharge
        and dam outflow mights sometimes be negative.  To avoid negative
        estimates of natural discharge, it its value is set to zero in
        such cases:

        >>> logs.loggedoutflow(4.0, 3.0, 5.0)
        >>> model.calc_naturalremotedischarge_v1()
        >>> fluxes.naturalremotedischarge
        naturalremotedischarge(0.0)
    """
    CONTROLPARAMETERS = (
        dam_control.NmbLogEntries,
    )
    REQUIREDSEQUENCES = (
        dam_logs.LoggedTotalRemoteDischarge,
        dam_logs.LoggedOutflow,
    )
    RESULTSEQUENCES = (
        dam_fluxes.NaturalRemoteDischarge,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        flu.naturalremotedischarge = 0.
        for idx in range(con.nmblogentries):
            flu.naturalremotedischarge += (
                log.loggedtotalremotedischarge[idx] - log.loggedoutflow[idx])
        if flu.naturalremotedischarge > 0.:
            flu.naturalremotedischarge /= con.nmblogentries
        else:
            flu.naturalremotedischarge = 0.


class Calc_RemoteDemand_V1(modeltools.Method):
    """Estimate the discharge demand of a cross section far downstream.

    Basic equation:
      :math:`RemoteDemand =
      max(RemoteDischargeMinimum - NaturalRemoteDischarge, 0`

    Examples:

        Low water elevation is often restricted to specific month of the year.
        Sometimes the pursued lowest discharge value varies over the year
        to allow for a low flow variability that is in some agreement with
        the natural flow regime.  The HydPy-Dam model supports such
        variations.  Hence we define a short simulation time period first.
        This enables us to show how the related parameters values can be
        defined and how the calculation of the `remote` water demand
        throughout the year actually works:

        >>> from hydpy import pub
        >>> pub.timegrids = '2001.03.30', '2001.04.03', '1d'

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

        >>> model.idx_sim = pub.timegrids.init['2001.04.01']
        >>> test()
        | ex. | naturalremotedischarge | remotedemand |
        -----------------------------------------------
        |   1 |                    0.0 |          2.0 |
        |   2 |                    1.0 |          1.0 |
        |   3 |                    2.0 |          0.0 |
        |   4 |                    3.0 |          0.0 |

        On May 31, the required discharge is 0 m³/s:

        >>> model.idx_sim = pub.timegrids.init['2001.03.31']
        >>> test()
        | ex. | naturalremotedischarge | remotedemand |
        -----------------------------------------------
        |   1 |                    0.0 |          0.0 |
        |   2 |                    1.0 |          0.0 |
        |   3 |                    2.0 |          0.0 |
        |   4 |                    3.0 |          0.0 |
    """
    CONTROLPARAMETERS = (
        dam_control.RemoteDischargeMinimum,
    )
    DERIVEDPARAMETERS = (
        dam_derived.TOY,
    )
    REQUIREDSEQUENCES = (
        dam_fluxes.NaturalRemoteDischarge,
    )
    RESULTSEQUENCES = (
        dam_fluxes.RemoteDemand,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.remotedemand = max(
            con.remotedischargeminimum[der.toy[model.idx_sim]] -
            flu.naturalremotedischarge, 0.)


class Calc_RemoteFailure_V1(modeltools.Method):
    """Estimate the shortfall of actual discharge under the required discharge
    of a cross section far downstream.

    Basic equation:
      :math:`RemoteFailure =
      \\frac{\\Sigma(LoggedTotalRemoteDischarge)}{NmbLogEntries} -
      RemoteDischargeMinimum`

    Examples:

        As explained in the documentation on method |Calc_RemoteDemand_V1|,
        we have to define a simulation period first:

        >>> from hydpy import pub
        >>> pub.timegrids = '2001.03.30', '2001.04.03', '1d'

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

        >>> model.idx_sim = pub.timegrids.init['2001.04.01']
        >>> model.calc_remotefailure_v1()
        >>> fluxes.remotefailure
        remotefailure(1.0)

        Instead for May 31 there would have been an excess of 1 m³/s, which
        is interpreted to be a "negative failure":

        >>> model.idx_sim = pub.timegrids.init['2001.03.31']
        >>> model.calc_remotefailure_v1()
        >>> fluxes.remotefailure
        remotefailure(-1.0)
    """
    CONTROLPARAMETERS = (
        dam_control.NmbLogEntries,
        dam_control.RemoteDischargeMinimum,
    )
    DERIVEDPARAMETERS = (
        dam_derived.TOY,
    )
    REQUIREDSEQUENCES = (
        dam_logs.LoggedTotalRemoteDischarge,
    )
    RESULTSEQUENCES = (
        dam_fluxes.RemoteFailure,
    )
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
    """Guess the required release necessary to not fall below the threshold
    value at a cross section far downstream with a certain level of certainty.

    Used auxiliary method:
      |smooth_logistic1|

    Basic equation:
      :math:`RequiredRemoteRelease = RemoteDemand + RemoteDischargeSafety
      \\cdot smooth_{logistic1}(RemoteFailure, RemoteDischargeSmoothPar)`

    Examples:

        As in the examples above, define a short simulation time period first:

        >>> from hydpy import pub
        >>> pub.timegrids = '2001.03.30', '2001.04.03', '1d'

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

        >>> model.idx_sim = pub.timegrids.init['2001.03.31']
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

        >>> model.idx_sim = pub.timegrids.init['2001.04.01']
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

    """
    CONTROLPARAMETERS = (
        dam_control.RemoteDischargeSafety,
    )
    DERIVEDPARAMETERS = (
        dam_derived.TOY,
        dam_derived.RemoteDischargeSmoothPar,
    )
    REQUIREDSEQUENCES = (
        dam_fluxes.RemoteDemand,
        dam_fluxes.RemoteFailure,
    )
    RESULTSEQUENCES = (
        dam_fluxes.RequiredRemoteRelease,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.requiredremoterelease = (
            flu.remotedemand+con.remotedischargesafety[der.toy[model.idx_sim]] *
            smoothutils.smooth_logistic1(
                flu.remotefailure,
                der.remotedischargesmoothpar[der.toy[model.idx_sim]]))


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
    REQUIREDSEQUENCES = (
        dam_logs.LoggedRequiredRemoteRelease,
    )
    RESULTSEQUENCES = (
        dam_fluxes.RequiredRemoteRelease,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        flu.requiredremoterelease = log.loggedrequiredremoterelease[0]


class Calc_AllowedRemoteRelieve_V1(modeltools.Method):
    """Get the allowed remote relieve of the last simulation step.

    Basic equation:
      :math:`AllowedRemoteRelieve = LoggedAllowedRemoteRelieve`

    Example:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> logs.loggedallowedremoterelieve = 2.0
        >>> model.calc_allowedremoterelieve_v1()
        >>> fluxes.allowedremoterelieve
        allowedremoterelieve(2.0)
    """
    REQUIREDSEQUENCES = (
        dam_logs.LoggedAllowedRemoteRelieve,
    )
    RESULTSEQUENCES = (
        dam_fluxes.AllowedRemoteRelieve,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        flu.allowedremoterelieve = log.loggedallowedremoterelieve[0]


class Calc_RequiredRelease_V1(modeltools.Method):
    """Calculate the total water release (immediately and far downstream)
    required for reducing drought events.

    Used auxiliary method:
      |smooth_logistic2|

    Basic equation:
      :math:`RequiredRelease = RequiredRemoteRelease
      \\cdot smooth_{logistic2}(
      RequiredRemoteRelease-NearDischargeMinimumThreshold,
      NearDischargeMinimumSmoothPar2)`

    Examples:

        As in the examples above, define a short simulation time period first:

        >>> from hydpy import pub
        >>> pub.timegrids = '2001.03.30', '2001.04.03', '1d'

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

        >>> model.idx_sim = pub.timegrids.init['2001.03.31']
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

        >>> model.idx_sim = pub.timegrids.init['2001.04.01']
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

    """
    CONTROLPARAMETERS = (
        dam_control.NearDischargeMinimumThreshold,
    )
    DERIVEDPARAMETERS = (
        dam_derived.TOY,
        dam_derived.NearDischargeMinimumSmoothPar2,
    )
    REQUIREDSEQUENCES = (
        dam_fluxes.RequiredRemoteRelease,
    )
    RESULTSEQUENCES = (
        dam_fluxes.RequiredRelease,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.requiredrelease = con.neardischargeminimumthreshold[
            der.toy[model.idx_sim]]
        flu.requiredrelease = (
            flu.requiredrelease +
            smoothutils.smooth_logistic2(
                flu.requiredremoterelease-flu.requiredrelease,
                der.neardischargeminimumsmoothpar2[
                    der.toy[model.idx_sim]]))


class Calc_RequiredRelease_V2(modeltools.Method):
    """Calculate the water release (immediately downstream) required for
    reducing drought events.

    Basic equation:
      :math:`RequiredRelease = NearDischargeMinimumThreshold`

    Examples:

        As in the examples above, define a short simulation time period first:

        >>> from hydpy import pub
        >>> pub.timegrids = '2001.03.30', '2001.04.03', '1d'

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

        >>> model.idx_sim = pub.timegrids.init['2001.03.31']
        >>> model.calc_requiredrelease_v2()
        >>> fluxes.requiredrelease
        requiredrelease(0.0)
        >>> model.idx_sim = pub.timegrids.init['2001.04.01']
        >>> model.calc_requiredrelease_v2()
        >>> fluxes.requiredrelease
        requiredrelease(4.0)
    """
    CONTROLPARAMETERS = (
        dam_control.NearDischargeMinimumThreshold,
    )
    DERIVEDPARAMETERS = (
        dam_derived.TOY,
    )
    RESULTSEQUENCES = (
        dam_fluxes.RequiredRelease,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.requiredrelease = con.neardischargeminimumthreshold[
            der.toy[model.idx_sim]]


class Calc_PossibleRemoteRelieve_V1(modeltools.Method):
    """Calculate the highest possible water release that can be routed to
    a remote location based on an artificial neural network describing the
    relationship between possible release and water stage.

    Example:

        For simplicity, the example of method |Calc_FloodDischarge_V1|
        is reused.  See the documentation on the mentioned method for
        further information:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> waterlevel2possibleremoterelieve(
        ...     nmb_inputs=1,
        ...     nmb_neurons=(2,),
        ...     nmb_outputs=1,
        ...     weights_input=[[50., 4]],
        ...     weights_output=[[2.], [30]],
        ...     intercepts_hidden=[[-13000, -1046]],
        ...     intercepts_output=[0.])
        >>> from hydpy import UnitTest
        >>> test = UnitTest(
        ...     model, model.calc_possibleremoterelieve_v1,
        ...     last_example=21,
        ...     parseqs=(aides.waterlevel, fluxes.possibleremoterelieve))
        >>> test.nexts.waterlevel = numpy.arange(257, 261.1, 0.2)
        >>> test()
        | ex. | waterlevel | possibleremoterelieve |
        --------------------------------------------
        |   1 |      257.0 |                   0.0 |
        |   2 |      257.2 |              0.000001 |
        |   3 |      257.4 |              0.000002 |
        |   4 |      257.6 |              0.000005 |
        |   5 |      257.8 |              0.000011 |
        |   6 |      258.0 |              0.000025 |
        |   7 |      258.2 |              0.000056 |
        |   8 |      258.4 |              0.000124 |
        |   9 |      258.6 |              0.000275 |
        |  10 |      258.8 |              0.000612 |
        |  11 |      259.0 |              0.001362 |
        |  12 |      259.2 |              0.003031 |
        |  13 |      259.4 |              0.006745 |
        |  14 |      259.6 |              0.015006 |
        |  15 |      259.8 |              0.033467 |
        |  16 |      260.0 |              1.074179 |
        |  17 |      260.2 |              2.164498 |
        |  18 |      260.4 |              2.363853 |
        |  19 |      260.6 |               2.79791 |
        |  20 |      260.8 |              3.719725 |
        |  21 |      261.0 |              5.576088 |
    """
    CONTROLPARAMETERS = (
        dam_control.WaterLevel2PossibleRemoteRelieve,
    )
    REQUIREDSEQUENCES = (
        dam_aides.WaterLevel,
    )
    RESULTSEQUENCES = (
        dam_fluxes.PossibleRemoteRelieve,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        aid = model.sequences.aides.fastaccess
        con.waterlevel2possibleremoterelieve.inputs[0] = aid.waterlevel
        con.waterlevel2possibleremoterelieve.process_actual_input()
        flu.possibleremoterelieve = \
            con.waterlevel2possibleremoterelieve.outputs[0]


class Calc_ActualRemoteRelieve_V1(modeltools.Method):
    """Calculate the actual amount of water released to a remote location
    to relieve the dam during high flow conditions.

    Basic equation - discontinous:
      :math:`ActualRemoteRelease = min(PossibleRemoteRelease,
      AllowedRemoteRelease)`

    Used auxiliary methods:
      |smooth_min1|
      |smooth_max1|

    Basic equation - continous:
      :math:`ActualRemoteRelease = smooth_min1(PossibleRemoteRelease,
      AllowedRemoteRelease, RemoteRelieveTolerance)`


    Note that the given continous basic equation is a simplification of
    the complete algorithm to calculate |ActualRemoteRelieve|, which also
    makes use of |smooth_max1| to prevent from gaining negative values
    in a smooth manner.


    Examples:

        Prepare a dam model:

        >>> from hydpy.models.dam import *
        >>> parameterstep()

        Prepare a test function object that performs seven examples with
        |PossibleRemoteRelieve| ranging from -1 to 5 m³/s:

        >>> from hydpy import UnitTest
        >>> test = UnitTest(model, model.calc_actualremoterelieve_v1,
        ...                 last_example=7,
        ...                 parseqs=(fluxes.possibleremoterelieve,
        ...                          fluxes.actualremoterelieve))
        >>> test.nexts.possibleremoterelieve = range(-1, 6)

        We begin with a |AllowedRemoteRelieve| value of 3 m³/s:

        >>> fluxes.allowedremoterelieve = 3.0

        Through setting the value of |RemoteRelieveTolerance| to the
        lowest possible value, there is no smoothing.  Instead, the
        relationship between |ActualRemoteRelieve| and |PossibleRemoteRelieve|
        follows the simple discontinous minimum function:

        >>> remoterelievetolerance(0.0)
        >>> test()
        | ex. | possibleremoterelieve | actualremoterelieve |
        -----------------------------------------------------
        |   1 |                  -1.0 |                 0.0 |
        |   2 |                   0.0 |                 0.0 |
        |   3 |                   1.0 |                 1.0 |
        |   4 |                   2.0 |                 2.0 |
        |   5 |                   3.0 |                 3.0 |
        |   6 |                   4.0 |                 3.0 |
        |   7 |                   5.0 |                 3.0 |

        Increasing the value of parameter |RemoteRelieveTolerance| to a
        sensible value results in a moderate smoothing:

        >>> remoterelievetolerance(0.2)
        >>> test()
        | ex. | possibleremoterelieve | actualremoterelieve |
        -----------------------------------------------------
        |   1 |                  -1.0 |                 0.0 |
        |   2 |                   0.0 |                 0.0 |
        |   3 |                   1.0 |            0.970639 |
        |   4 |                   2.0 |             1.89588 |
        |   5 |                   3.0 |            2.584112 |
        |   6 |                   4.0 |            2.896195 |
        |   7 |                   5.0 |            2.978969 |

        Even when setting a very large smoothing parameter value, the actual
        remote relieve does not fall below 0 m³/s:

        >>> remoterelievetolerance(1.0)
        >>> test()
        | ex. | possibleremoterelieve | actualremoterelieve |
        -----------------------------------------------------
        |   1 |                  -1.0 |                 0.0 |
        |   2 |                   0.0 |                 0.0 |
        |   3 |                   1.0 |            0.306192 |
        |   4 |                   2.0 |            0.634882 |
        |   5 |                   3.0 |            1.037708 |
        |   6 |                   4.0 |            1.436494 |
        |   7 |                   5.0 |            1.788158 |

        Now we repeat the last example with a allowed remote relieve of
        only 0.03 m³/s instead of 3 m³/s:

        >>> fluxes.allowedremoterelieve = 0.03
        >>> test()
        | ex. | possibleremoterelieve | actualremoterelieve |
        -----------------------------------------------------
        |   1 |                  -1.0 |                 0.0 |
        |   2 |                   0.0 |                 0.0 |
        |   3 |                   1.0 |                0.03 |
        |   4 |                   2.0 |                0.03 |
        |   5 |                   3.0 |                0.03 |
        |   6 |                   4.0 |                0.03 |
        |   7 |                   5.0 |                0.03 |

        The result above is as expected, but the smooth part of the
        relationship is not resolved.  By increasing the resolution we
        see a relationship that corresponds to the one shown above
        for an allowed relieve of 3 m³/s.  This points out, that the
        degree of smoothing is releative to the allowed relieve:

        >>> import numpy
        >>> test.nexts.possibleremoterelieve = numpy.arange(-0.01, 0.06, 0.01)
        >>> test()
        | ex. | possibleremoterelieve | actualremoterelieve |
        -----------------------------------------------------
        |   1 |                 -0.01 |                 0.0 |
        |   2 |                   0.0 |                 0.0 |
        |   3 |                  0.01 |            0.003062 |
        |   4 |                  0.02 |            0.006349 |
        |   5 |                  0.03 |            0.010377 |
        |   6 |                  0.04 |            0.014365 |
        |   7 |                  0.05 |            0.017882 |

        One can reperform the shown experiments with an even higher
        resolution to see that the relationship between
        |ActualRemoteRelieve| and |PossibleRemoteRelieve| is
        (at least in most cases) in fact very smooth.  But a more analytical
        approach would possibly be favourable regarding the smoothness in
        some edge cases and computational efficiency.
    """
    CONTROLPARAMETERS = (
        dam_control.RemoteRelieveTolerance,
    )
    REQUIREDSEQUENCES = (
        dam_fluxes.AllowedRemoteRelieve,
        dam_fluxes.PossibleRemoteRelieve,
    )
    RESULTSEQUENCES = (
        dam_fluxes.ActualRemoteRelieve,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        d_smoothpar = con.remoterelievetolerance*flu.allowedremoterelieve
        flu.actualremoterelieve = smoothutils.smooth_min1(
            flu.possibleremoterelieve, flu.allowedremoterelieve, d_smoothpar)
        for dummy in range(5):
            d_smoothpar /= 5.
            flu.actualremoterelieve = smoothutils.smooth_max1(
                flu.actualremoterelieve, 0., d_smoothpar)
            d_smoothpar /= 5.
            flu.actualremoterelieve = smoothutils.smooth_min1(
                flu.actualremoterelieve, flu.possibleremoterelieve, d_smoothpar)
        flu.actualremoterelieve = min(flu.actualremoterelieve,
                                      flu.possibleremoterelieve)
        flu.actualremoterelieve = min(flu.actualremoterelieve,
                                      flu.allowedremoterelieve)
        flu.actualremoterelieve = max(flu.actualremoterelieve, 0.)


class Calc_TargetedRelease_V1(modeltools.Method):
    """Calculate the targeted water release for reducing drought events,
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
      w \\cdot RequiredRelease + (1-w) \\cdot Inflow`

      :math:`w = smooth_{logistic1}(
      Inflow-NearDischargeMinimumThreshold, NearDischargeMinimumSmoothPar1)`

    Examples:

        As in the examples above, define a short simulation time period first:

        >>> from hydpy import pub
        >>> pub.timegrids = '2001.03.30', '2001.04.03', '1d'

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

        >>> model.idx_sim = pub.timegrids.init['2001.03.31']
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

        >>> model.idx_sim = pub.timegrids.init['2001.04.01']
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

        >>> model.idx_sim = pub.timegrids.init['2001.03.31']
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

        >>> model.idx_sim = pub.timegrids.init['2001.04.01']
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
        >>> model.idx_sim = pub.timegrids.init['2001.03.31']
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
        >>> model.idx_sim = pub.timegrids.init['2001.04.01']
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
    """
    CONTROLPARAMETERS = (
        dam_control.RestrictTargetedRelease,
        dam_control.NearDischargeMinimumThreshold,
    )
    DERIVEDPARAMETERS = (
        dam_derived.NearDischargeMinimumSmoothPar1,
        dam_derived.TOY,
    )
    REQUIREDSEQUENCES = (
        dam_fluxes.Inflow,
        dam_fluxes.RequiredRelease,
    )
    RESULTSEQUENCES = (
        dam_fluxes.TargetedRelease,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        if con.restricttargetedrelease:
            flu.targetedrelease = smoothutils.smooth_logistic1(
                flu.inflow-con.neardischargeminimumthreshold[
                    der.toy[model.idx_sim]],
                der.neardischargeminimumsmoothpar1[der.toy[model.idx_sim]])
            flu.targetedrelease = (flu.targetedrelease * flu.requiredrelease +
                                   (1.-flu.targetedrelease) * flu.inflow)
        else:
            flu.targetedrelease = flu.requiredrelease


class Calc_ActualRelease_V1(modeltools.Method):
    """Calculate the actual water release that can be supplied by the
    dam considering the targeted release and the given water level.

    Used auxiliary method:
      |smooth_logistic1|

    Basic equation:
      :math:`ActualRelease = TargetedRelease \\cdot
      smooth_{logistic1}(WaterLevelMinimumThreshold-WaterLevel,
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
        ...                 parseqs=(aides.waterlevel,
        ...                          fluxes.actualrelease))
        >>> test.nexts.waterlevel = range(-1, 6)

        .. _dam_calc_actualrelease_v1_ex01:

        **Example 1**

        Firstly, we define a sharp minimum water level of 0 m:

        >>> waterlevelminimumthreshold(0.)
        >>> waterlevelminimumtolerance(0.)
        >>> derived.waterlevelminimumsmoothpar.update()

        The following test results show that the water releae is reduced
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

        >>> waterlevelminimumthreshold(4.)
        >>> waterlevelminimumtolerance(1.)
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

        >>> waterlevelminimumthreshold(1.)
        >>> waterlevelminimumtolerance(2.)
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
    CONTROLPARAMETERS = (
        dam_control.WaterLevelMinimumThreshold,
    )
    DERIVEDPARAMETERS = (
        dam_derived.WaterLevelMinimumSmoothPar,
    )
    REQUIREDSEQUENCES = (
        dam_fluxes.TargetedRelease,
        dam_aides.WaterLevel,
    )
    RESULTSEQUENCES = (
        dam_fluxes.ActualRelease,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        aid = model.sequences.aides.fastaccess
        flu.actualrelease = (flu.targetedrelease *
                             smoothutils.smooth_logistic1(
                                 aid.waterlevel-con.waterlevelminimumthreshold,
                                 der.waterlevelminimumsmoothpar))


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
    REQUIREDSEQUENCES = (
        dam_fluxes.ActualRelease,
        dam_fluxes.RequiredRemoteRelease,
    )
    RESULTSEQUENCES = (
        dam_fluxes.MissingRemoteRelease,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.missingremoterelease = max(
            flu.requiredremoterelease-flu.actualrelease, 0.)


class Calc_ActualRemoteRelease_V1(modeltools.Method):
    """Calculate the actual remote water release that can be supplied by the
    dam considering the required remote release and the given water level.

    Used auxiliary method:
      |smooth_logistic1|

    Basic equation:
      :math:`ActualRemoteRelease = RequiredRemoteRelease \\cdot
      smooth_{logistic1}(WaterLevelMinimumRemoteThreshold-WaterLevel,
      WaterLevelMinimumRemoteSmoothPar)`

    Examples:

        Note that method |Calc_ActualRemoteRelease_V1| is functionally
        identical with method |Calc_ActualRelease_V1|.  This is why we
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
        ...                 parseqs=(aides.waterlevel,
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
    CONTROLPARAMETERS = (
        dam_control.WaterLevelMinimumRemoteThreshold,
    )
    DERIVEDPARAMETERS = (
        dam_derived.WaterLevelMinimumRemoteSmoothPar,
    )
    REQUIREDSEQUENCES = (
        dam_fluxes.RequiredRemoteRelease,
        dam_aides.WaterLevel,
    )
    RESULTSEQUENCES = (
        dam_fluxes.ActualRemoteRelease,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        aid = model.sequences.aides.fastaccess
        flu.actualremoterelease = (
            flu.requiredremoterelease *
            smoothutils.smooth_logistic1(
                aid.waterlevel-con.waterlevelminimumremotethreshold,
                der.waterlevelminimumremotesmoothpar))


class Update_ActualRemoteRelieve_V1(modeltools.Method):
    """Constrain the actual relieve discharge to a remote location.

    Used auxiliary methods:
      |smooth_min1|
      |smooth_max1|

    Basic equation - discontinous:
      :math:`ActualRemoteRelieve = min(ActualRemoteRelease,
      HighestRemoteDischarge)`

    Basic equation - continous:
      :math:`ActualRemoteRelieve = smooth_min1(ActualRemoteRelieve,
      HighestRemoteDischarge, HighestRemoteSmoothPar)`

    Note that the given continous basic equation is a simplification of
    the complete algorithm to update |ActualRemoteRelieve|, which also
    makes use of |smooth_max1| to prevent from gaining negative values
    in a smooth manner.

    Examples:

        Prepare a dam model:

        >>> from hydpy.models.dam import *
        >>> parameterstep()

        Prepare a test function object that performs eight examples with
        |ActualRemoteRelieve| ranging from 0 to 8 m³/s and a fixed
        initial value of parameter |HighestRemoteDischarge| of 4 m³/s:

        >>> highestremotedischarge(4.0)
        >>> from hydpy import UnitTest
        >>> test = UnitTest(model,
        ...                 model.update_actualremoterelieve_v1,
        ...                 last_example=8,
        ...                 parseqs=(fluxes.actualremoterelieve,))
        >>> test.nexts.actualremoterelieve = range(8)

        Through setting the value of |HighestRemoteTolerance| to the
        lowest possible value, there is no smoothing.  Instead, the
        shown relationship agrees with a combination of the discontinuous
        minimum and maximum function:

        >>> highestremotetolerance(0.0)
        >>> derived.highestremotesmoothpar.update()
        >>> test()
        | ex. | actualremoterelieve |
        -----------------------------
        |   1 |                 0.0 |
        |   2 |                 1.0 |
        |   3 |                 2.0 |
        |   4 |                 3.0 |
        |   5 |                 4.0 |
        |   6 |                 4.0 |
        |   7 |                 4.0 |
        |   8 |                 4.0 |

        Setting a sensible |HighestRemoteTolerance| value results in
        a moderate smoothing:

        >>> highestremotetolerance(0.1)
        >>> derived.highestremotesmoothpar.update()
        >>> test()
        | ex. | actualremoterelieve |
        -----------------------------
        |   1 |                 0.0 |
        |   2 |            0.999999 |
        |   3 |             1.99995 |
        |   4 |            2.996577 |
        |   5 |            3.836069 |
        |   6 |            3.991578 |
        |   7 |            3.993418 |
        |   8 |            3.993442 |

        Method |Update_ActualRemoteRelieve_V1| is defined in a similar
        way as method |Calc_ActualRemoteRelieve_V1|.  Please read the
        documentation on |Calc_ActualRemoteRelieve_V1| for further
        information.
    """
    CONTROLPARAMETERS = (
        dam_control.HighestRemoteDischarge,
    )
    DERIVEDPARAMETERS = (
        dam_derived.HighestRemoteSmoothPar,
    )
    UPDATEDSEQUENCES = (
        dam_fluxes.ActualRemoteRelieve,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        d_smooth = der.highestremotesmoothpar
        d_highest = con.highestremotedischarge
        d_value = smoothutils.smooth_min1(
            flu.actualremoterelieve, d_highest, d_smooth)
        for dummy in range(5):
            d_smooth /= 5.
            d_value = smoothutils.smooth_max1(
                d_value, 0., d_smooth)
            d_smooth /= 5.
            d_value = smoothutils.smooth_min1(
                d_value, d_highest, d_smooth)
        d_value = min(d_value, flu.actualremoterelieve)
        d_value = min(d_value, d_highest)
        flu.actualremoterelieve = max(d_value, 0.)


class Update_ActualRemoteRelease_V1(modeltools.Method):
    """Constrain the actual release (supply discharge) to a remote location.

    Used auxiliary methods:
      |smooth_min1|
      |smooth_max1|

    Basic equation - discontinous:
      :math:`ActualRemoteRelease = min(ActualRemoteRelease,
      HighestRemoteDischarge-ActualRemoteRelieve)`

    Basic equation - continous:
      :math:`ActualRemoteRelease = smooth_min1(ActualRemoteRelease,
      HighestRemoteDischarge-ActualRemoteRelieve, HighestRemoteSmoothPar)`

    Note that the given continous basic equation is a simplification of
    the complete algorithm to update |ActualRemoteRelease|, which also
    makes use of |smooth_max1| to prevent from gaining negative values
    in a smooth manner.

    Examples:

        Prepare a dam model:

        >>> from hydpy.models.dam import *
        >>> parameterstep()

        Prepare a test function object that performs eight examples with
        |ActualRemoteRelieve| ranging from 0 to 8 m³/s and a fixed initial
        value of parameter |ActualRemoteRelease| of 2 m³/s:

        >>> from hydpy import UnitTest
        >>> test = UnitTest(model,
        ...                 model.update_actualremoterelease_v1,
        ...                 last_example=8,
        ...                 parseqs=(fluxes.actualremoterelieve,
        ...                          fluxes.actualremoterelease))
        >>> test.nexts.actualremoterelieve = range(8)
        >>> test.inits.actualremoterelease = 2.0

        Through setting the value of |HighestRemoteTolerance| to the
        lowest possible value, there is no smoothing.  Instead, the
        shown relationship agrees with a combination of the discontinuous
        minimum and maximum function:

        >>> highestremotedischarge(6.0)
        >>> highestremotetolerance(0.0)
        >>> derived.highestremotesmoothpar.update()
        >>> test()
        | ex. | actualremoterelieve | actualremoterelease |
        ---------------------------------------------------
        |   1 |                 0.0 |                 2.0 |
        |   2 |                 1.0 |                 2.0 |
        |   3 |                 2.0 |                 2.0 |
        |   4 |                 3.0 |                 2.0 |
        |   5 |                 4.0 |                 2.0 |
        |   6 |                 5.0 |                 1.0 |
        |   7 |                 6.0 |                 0.0 |
        |   8 |                 7.0 |                 0.0 |

        Setting a sensible |HighestRemoteTolerance| value results in
        a moderate smoothing.  But note that this is only true for
        the minimum function (restricting the larger
        |ActualRemoteRelease| values).  Instead of smoothing the
        maximum function as well, |ActualRemoteRelease| is exactly
        0 m³/s for a |ActualRemoteRelieve| value of 6 m³/s (within
        the shown precision). The remaining discontinuity does not
        pose a problem, as long |ActualRemoteRelieve| does not exceed
        the value of |HighestRemoteDischarge|.  (Application models
        using method |Update_ActualRemoteRelease_V1| should generally
        enforce this restriction). In case of exceedance, extended
        computation times might occur:

        >>> highestremotetolerance(0.1)
        >>> derived.highestremotesmoothpar.update()
        >>> test()
        | ex. | actualremoterelieve | actualremoterelease |
        ---------------------------------------------------
        |   1 |                 0.0 |            1.999996 |
        |   2 |                 1.0 |            1.999925 |
        |   3 |                 2.0 |            1.998739 |
        |   4 |                 3.0 |            1.979438 |
        |   5 |                 4.0 |            1.754104 |
        |   6 |                 5.0 |            0.976445 |
        |   7 |                 6.0 |                 0.0 |
        |   8 |                 7.0 |                 0.0 |

        Method |Update_ActualRemoteRelease_V1| is defined in a similar
        way as method |Calc_ActualRemoteRelieve_V1|.  Please read the
        documentation on |Calc_ActualRemoteRelieve_V1| for further
        information.
    """
    CONTROLPARAMETERS = (
        dam_control.HighestRemoteDischarge,
    )
    DERIVEDPARAMETERS = (
        dam_derived.HighestRemoteSmoothPar,
    )
    REQUIREDSEQUENCES = (
        dam_fluxes.ActualRemoteRelieve,
    )
    UPDATEDSEQUENCES = (
        dam_fluxes.ActualRemoteRelease,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        d_smooth = der.highestremotesmoothpar
        d_highest = con.highestremotedischarge-flu.actualremoterelieve
        d_value = smoothutils.smooth_min1(
            flu.actualremoterelease, d_highest, d_smooth)
        for dummy in range(5):
            d_smooth /= 5.
            d_value = smoothutils.smooth_max1(
                d_value, 0., d_smooth)
            d_smooth /= 5.
            d_value = smoothutils.smooth_min1(
                d_value, d_highest, d_smooth)
        d_value = min(d_value, flu.actualremoterelease)
        d_value = min(d_value, d_highest)
        flu.actualremoterelease = max(d_value, 0.)


class Calc_FloodDischarge_V1(modeltools.Method):
    """Calculate the discharge during and after a flood event based on an
    |anntools.SeasonalANN| describing the relationship(s) between discharge
    and water stage.

    Example:

        The control parameter |WaterLevel2FloodDischarge| is derived from
        |SeasonalParameter|.  This allows to simulate different seasonal
        dam control schemes.  To show that the seasonal selection mechanism
        is implemented properly, we define a short simulation period of
        three days:

        >>> from hydpy import pub
        >>> pub.timegrids = '2001.01.01', '2001.01.04', '1d'

        Now we prepare a dam model and define two different relationships
        between water level and flood discharge.  The first relatively
        simple relationship (for January, 2) is based on two neurons
        contained in a single hidden layer and is used in the following
        example.  The second neural network (for January, 3) is not
        applied at all, which is why we do not need to assign any parameter
        values to it:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> waterlevel2flooddischarge(
        ...     _01_02_12 = ann(nmb_inputs=1,
        ...                     nmb_neurons=(2,),
        ...                     nmb_outputs=1,
        ...                     weights_input=[[50., 4]],
        ...                     weights_output=[[2.], [30]],
        ...                     intercepts_hidden=[[-13000, -1046]],
        ...                     intercepts_output=[0.]),
        ...     _01_03_12 = ann(nmb_inputs=1,
        ...                     nmb_neurons=(2,),
        ...                     nmb_outputs=1))
        >>> derived.toy.update()
        >>> model.idx_sim = pub.timegrids.sim['2001.01.02']

        The following example shows two distinct effects of both neurons
        in the first network.  One neuron describes a relatively sharp
        increase between 259.8 and 260.2 meters from about 0 to 2 m³/s.
        This could describe a release of water through a bottom outlet
        controlled by a valve.  The add something like an exponential
        increase between 260 and 261 meters, which could describe the
        uncontrolled flow over a spillway:

        >>> from hydpy import UnitTest
        >>> test = UnitTest(model,
        ...                 model.calc_flooddischarge_v1,
        ...                 last_example=21,
        ...                 parseqs=(aides.waterlevel,
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
    """
    CONTROLPARAMETERS = (
        dam_control.WaterLevel2FloodDischarge,
    )
    DERIVEDPARAMETERS = (
        dam_derived.TOY,
    )
    REQUIREDSEQUENCES = (
        dam_aides.WaterLevel,
    )
    RESULTSEQUENCES = (
        dam_fluxes.FloodDischarge,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        aid = model.sequences.aides.fastaccess
        con.waterlevel2flooddischarge.inputs[0] = aid.waterlevel
        con.waterlevel2flooddischarge.process_actual_input(
            der.toy[model.idx_sim])
        flu.flooddischarge = con.waterlevel2flooddischarge.outputs[0]


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
    REQUIREDSEQUENCES = (
        dam_fluxes.ActualRelease,
        dam_fluxes.FloodDischarge,
    )
    RESULTSEQUENCES = (
        dam_fluxes.Outflow,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.outflow = max(flu.actualrelease + flu.flooddischarge, 0.)


class Update_WaterVolume_V1(modeltools.Method):
    """Update the actual water volume.

    Basic equation:
      :math:`\\frac{d}{dt}WaterVolume = 1e-6 \\cdot (Inflow-Outflow)`

    Example:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> derived.seconds = 2e6
        >>> states.watervolume.old = 5.0
        >>> fluxes.inflow = 2.0
        >>> fluxes.outflow = 3.0
        >>> model.update_watervolume_v1()
        >>> states.watervolume
        watervolume(3.0)
    """
    DERIVEDPARAMETERS = (
        dam_derived.Seconds,
    )
    REQUIREDSEQUENCES = (
        dam_fluxes.Inflow,
        dam_fluxes.Outflow,
    )
    UPDATEDSEQUENCES = (
        dam_states.WaterVolume,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        new.watervolume = (old.watervolume +
                           der.seconds*(flu.inflow-flu.outflow)/1e6)


class Update_WaterVolume_V2(modeltools.Method):
    """Update the actual water volume.

    Basic equation:
      :math:`\\frac{d}{dt}WaterVolume = 10^{-6}
      \\cdot (Inflow-Outflow-ActualRemoteRelease)`

    Example:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> derived.seconds = 2e6
        >>> states.watervolume.old = 5.0
        >>> fluxes.inflow = 2.0
        >>> fluxes.outflow = 3.0
        >>> fluxes.actualremoterelease = 1.0
        >>> model.update_watervolume_v2()
        >>> states.watervolume
        watervolume(1.0)
    """
    DERIVEDPARAMETERS = (
        dam_derived.Seconds,
    )
    REQUIREDSEQUENCES = (
        dam_fluxes.Inflow,
        dam_fluxes.Outflow,
        dam_fluxes.ActualRemoteRelease,
    )
    UPDATEDSEQUENCES = (
        dam_states.WaterVolume,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        new.watervolume = (
            old.watervolume +
            der.seconds*(flu.inflow-flu.outflow-flu.actualremoterelease)/1e6)


class Update_WaterVolume_V3(modeltools.Method):
    """Update the actual water volume.

    Basic equation:
      :math:`\\frac{d}{dt}WaterVolume = 10^{-6}
      \\cdot (Inflow-Outflow-ActualRemoteRelease-ActualRemoteRelieve)`

    Example:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> derived.seconds = 2e6
        >>> states.watervolume.old = 5.0
        >>> fluxes.inflow = 2.0
        >>> fluxes.outflow = 3.0
        >>> fluxes.actualremoterelease = 1.0
        >>> fluxes.actualremoterelieve = 0.5
        >>> model.update_watervolume_v3()
        >>> states.watervolume
        watervolume(0.0)
    """
    DERIVEDPARAMETERS = (
        dam_derived.Seconds,
    )
    REQUIREDSEQUENCES = (
        dam_fluxes.Inflow,
        dam_fluxes.Outflow,
        dam_fluxes.ActualRemoteRelease,
        dam_fluxes.ActualRemoteRelieve,
    )
    UPDATEDSEQUENCES = (
        dam_states.WaterVolume,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        new.watervolume = (
            old.watervolume +
            der.seconds*(flu.inflow -
                         flu.outflow -
                         flu.actualremoterelease -
                         flu.actualremoterelieve)/1e6)


class Pass_Outflow_V1(modeltools.Method):
    """Update the outlet link sequence |dam_outlets.Q|.

    Basic equation:
      :math:`Q = Outflow`
    """
    REQUIREDSEQUENCES = (
        dam_fluxes.Outflow,
    )
    RESULTSEQUENCES = (
        dam_outlets.Q,
    )
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
    REQUIREDSEQUENCES = (
        dam_fluxes.ActualRemoteRelease,
    )
    RESULTSEQUENCES = (
        dam_outlets.S,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        out = model.sequences.outlets.fastaccess
        out.s[0] += flu.actualremoterelease


class Pass_ActualRemoteRelieve_V1(modeltools.Method):
    """Update the outlet link sequence |dam_outlets.R|.

    Basic equation:
      :math:`R = ActualRemoteRelieve`
    """
    REQUIREDSEQUENCES = (
        dam_fluxes.ActualRemoteRelieve,
    )
    RESULTSEQUENCES = (
        dam_outlets.R,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        out = model.sequences.outlets.fastaccess
        out.r[0] += flu.actualremoterelieve


class Pass_MissingRemoteRelease_V1(modeltools.Method):
    """Update the outlet link sequence |dam_senders.D|.

    Basic equation:
      :math:`D = MissingRemoteRelease`
    """
    REQUIREDSEQUENCES = (
        dam_fluxes.MissingRemoteRelease,
    )
    RESULTSEQUENCES = (
        dam_senders.D,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        sen = model.sequences.senders.fastaccess
        sen.d[0] += flu.missingremoterelease


class Pass_AllowedRemoteRelieve_V1(modeltools.Method):
    """Update the outlet link sequence |dam_outlets.R|.

    Basic equation:
      :math:`R = AllowedRemoteRelieve`
    """
    REQUIREDSEQUENCES = (
        dam_fluxes.AllowedRemoteRelieve,
    )
    RESULTSEQUENCES = (
        dam_senders.R,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        sen = model.sequences.senders.fastaccess
        sen.r[0] += flu.allowedremoterelieve


class Pass_RequiredRemoteSupply_V1(modeltools.Method):
    """Update the outlet link sequence |dam_outlets.S|.

    Basic equation:
      :math:`S = RequiredRemoteSupply`
    """
    REQUIREDSEQUENCES = (
        dam_fluxes.RequiredRemoteSupply,
    )
    RESULTSEQUENCES = (
        dam_senders.S,
    )
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
    CONTROLPARAMETERS = (
        dam_control.NmbLogEntries,
    )
    REQUIREDSEQUENCES = (
        dam_fluxes.Outflow,
    )
    UPDATEDSEQUENCES = (
        dam_logs.LoggedOutflow,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        for idx in range(con.nmblogentries-1, 0, -1):
            log.loggedoutflow[idx] = log.loggedoutflow[idx-1]
        log.loggedoutflow[0] = flu.outflow


class Model(modeltools.ELSModel):
    """Dam base model."""
    SOLVERPARAMETERS = (
        dam_solver.AbsErrorMax,
        dam_solver.RelErrorMax,
        dam_solver.RelDTMin,
        dam_solver.RelDTMax,
    )
    SOLVERSEQUENCES = ()
    INLET_METHODS = (
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
        Pic_LoggedRequiredRemoteRelease_V1,
        Pic_LoggedRequiredRemoteRelease_V2,
        Calc_RequiredRemoteRelease_V2,
        Pic_LoggedAllowedRemoteRelieve_V1,
        Calc_AllowedRemoteRelieve_V1,
    )
    PART_ODE_METHODS = (
        Pic_Inflow_V1,
        Calc_WaterLevel_V1,
        Calc_ActualRelease_V1,
        Calc_PossibleRemoteRelieve_V1,
        Calc_ActualRemoteRelieve_V1,
        Calc_ActualRemoteRelease_V1,
        Update_ActualRemoteRelieve_V1,
        Update_ActualRemoteRelease_V1,
        Calc_FloodDischarge_V1,
        Calc_Outflow_V1,
    )
    FULL_ODE_METHODS = (
        Update_WaterVolume_V1,
        Update_WaterVolume_V2,
        Update_WaterVolume_V3,
    )
    OUTLET_METHODS = (
        Pass_Outflow_V1,
        Update_LoggedOutflow_V1,
        Pass_ActualRemoteRelease_V1,
        Pass_ActualRemoteRelieve_V1,
    )
    SENDER_METHODS = (
        Calc_MissingRemoteRelease_V1,
        Pass_MissingRemoteRelease_V1,
        Calc_AllowedRemoteRelieve_V2,
        Pass_AllowedRemoteRelieve_V1,
        Calc_RequiredRemoteSupply_V1,
        Pass_RequiredRemoteSupply_V1,
    )
