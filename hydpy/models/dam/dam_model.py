# -*- coding: utf-8 -*-

# imports...
# ...standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import modeltools
from hydpy.cythons import modelutils


def pic_inflow_v1(self):
    """Update the inlet link sequence."""
    flu = self.sequences.fluxes.fastaccess
    inl = self.sequences.inlets.fastaccess
    flu.inflow = inl.q[0]


def pic_totalremotedischarge_v1(self):
    """Update the receiver link sequence.

    !!! This method needs revision. !!!
    """
    flu = self.sequences.fluxes.fastaccess
    log = self.sequences.logs.fastaccess
    flu.totalremotedischarge = log.loggedtotalremotedischarge[0]


def update_loggedtotalremotedischarge_v1(self):
    """Log a new entry of discharge at a cross section far downstream.

    !!! This method needs revision. !!!

    Required control parameter:
      :class:`~hydpy.models.dam.dam_derived.NmbLogEntries`

    Required receiver sequence:
      :class:`~hydpy.models.dam.dam_receivers.Q`

    Calculated flux sequence:
      :class:`~hydpy.models.dam.dam_logs.LoggedTotalRemoteDischarge`

    Example:

        The following example shows that, with each new method call, the
        three memorized values are successively moved to the right and the
        respective new value is stored on the bare left position:

        !!! The following test is outdated !!!

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> nmblogentries(3)
        >>> from hydpy.core.testtools import UnitTest
        >>> test = UnitTest(model, model.update_loggedtotalremotedischarge_v1,
        ...                 last_example=4)
        >>> test.nexts.totalremotedischarge = [1., 3., 2., 4]
        >>> # test()

        | ex. | totalremotedischarge |           loggedtotalremotedischarge |
        ---------------------------------------------------------------------
        |   1 |                  1.0 | 1.0  nan                         nan |
        |   2 |                  3.0 | 3.0  1.0                         nan |
        |   3 |                  2.0 | 2.0  3.0                         1.0 |
        |   4 |                  4.0 | 4.0  2.0                         3.0 |
    """
    con = self.parameters.control.fastaccess
    log = self.sequences.logs.fastaccess
    rec = self.sequences.receivers.fastaccess
    for idx in range(con.nmblogentries-1, 0, -1):
        log.loggedtotalremotedischarge[idx] = \
                                log.loggedtotalremotedischarge[idx-1]
    log.loggedtotalremotedischarge[0] = rec.q[0]


def calc_waterlevel_v1(self):
    """Determine the water level based on an artificial neural network
    describing the relationship between water level and water stage.

    Required control parameter:
      :class:`~hydpy.models.dam.dam_derived.WaterVolume2WaterLevel`

    Required state sequence:
      :class:`~hydpy.models.dam.dam_states.WaterVolume`

    Calculated aide sequence:
      :class:`~hydpy.models.dam.dam_aides.WaterLevel`

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

        >>> from hydpy.core.testtools import UnitTest
        >>> test = UnitTest(model, model.calc_waterlevel_v1, last_example=10)
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
    con = self.parameters.control.fastaccess
    new = self.sequences.states.fastaccess_new
    aid = self.sequences.aides.fastaccess
    con.watervolume2waterlevel.inputs[0] = new.watervolume
    con.watervolume2waterlevel.process_actual_input()
    aid.waterlevel = con.watervolume2waterlevel.outputs[0]


def calc_naturalremotedischarge_v1(self):
    """Try to estimate the natural discharge of a cross section far downstream
    based on the last few simulation steps.

    Required control parameter:
      :class:`~hydpy.models.dam.dam_derived.NmbLogEntries`

    Required log sequences:
      :class:`~hydpy.models.dam.dam_logs.LoggedTotalRemoteDischarge`
      :class:`~hydpy.models.dam.dam_logs.LoggedOutflow`

    Calculated flux sequence:
      :class:`~hydpy.models.dam.dam_fluxes.NaturalRemoteDischarge`

    Basic equation:
      :math:`RemoteDemand =
      max(\\frac{\\Sigma(LoggedTotalRemoteDischarge - LoggedOutflow)}
      {NmbLogEntries}), 0)`

    Examples:

        Usually, the mean total remote flow should be larger than the mean
        dam outflows.  Then the estimated natural remote discharge is simply
        the difference of both mean values::

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
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    log = self.sequences.logs.fastaccess
    flu.naturalremotedischarge = 0.
    for idx in range(con.nmblogentries):
        flu.naturalremotedischarge += (
                log.loggedtotalremotedischarge[idx] - log.loggedoutflow[idx])
    if flu.naturalremotedischarge > 0.:
        flu.naturalremotedischarge /= con.nmblogentries
    else:
        flu.naturalremotedischarge = 0.


def calc_remotedemand_v1(self):
    """Estimate the discharge demand of a cross section far downstream.

    Required control parameter:
      :class:`~hydpy.models.dam.dam_derived.RemoteDischargeMinimum`

    Required derived parameters:
      :class:`~hydpy.models.dam.dam_derived.TOY`

    Required flux sequence:
      :class:`~hydpy.models.dam.dam_fluxes.NaturalRemoteDischage`

    Calculated flux sequence:
      :class:`~hydpy.models.dam.dam_fluxes.RemoteDemand`

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
        >>> from hydpy.core.timetools import Timegrids, Timegrid
        >>> pub.timegrids = Timegrids(Timegrid('2001.03.30',
        ...                                    '2001.04.03',
        ...                                    '1d'))

        Prepare the dam model:

        >>> from hydpy.models.dam import *
        >>> parameterstep()

        Assume the required discharge at a gauge downstream beeing 2 m³/s
        in the hydrological summer half-year (April to October).  In the
        winter month (November to May), there is no such requirement:

        >>> remotedischargeminimum(_11_1_12=0.0, _03_31_12=0.0,
        ...                        _04_1_12=2.0, _10_31_12=2.0)
        >>> derived.toy.update()

        Prepare a test function, that calculates the remote discharge demand
        based on the parameter values defined above and for natural remote
        discharge values ranging between 0 and 3 m³/s:

        >>> from hydpy.core.testtools import UnitTest
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
    con = self.parameters.control.fastaccess
    der = self.parameters.derived.fastaccess
    flu = self.sequences.fluxes.fastaccess
    flu.remotedemand = max(con.remotedischargeminimum[der.toy[self.idx_sim]] -
                           flu.naturalremotedischarge, 0.)


def calc_remotefailure_v1(self):
    """Estimate the shortfall of actual discharge under the required discharge
    of a cross section far downstream.

    Required control parameters:
      :class:`~hydpy.models.dam.dam_derived.NmbLogEntries`
      :class:`~hydpy.models.dam.dam_derived.RemoteDischargeMinimum`

    Required derived parameters:
      :class:`~hydpy.models.dam.dam_derived.TOY`

    Required log sequence:
      :class:`~hydpy.models.dam.dam_logs.LoggedTotalRemoteDischarge`

    Calculated flux sequence:
      :class:`~hydpy.models.dam.dam_fluxes.RemoteFailure`

    Basic equation:
      :math:`RemoteFailure =
      \\frac{\\Sigma(LoggedTotalRemoteDischarge)}{NmbLogEntries} -
      RemoteDischargeMinimum`

    Examples:

        As explained in the documentation on method
        :func:`calc_remotedemand_v1`, we have to define a
        simulation period first:

        >>> from hydpy import pub
        >>> from hydpy.core.timetools import Timegrids, Timegrid
        >>> pub.timegrids = Timegrids(Timegrid('2001.03.30',
        ...                                    '2001.04.03',
        ...                                    '1d'))

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
    con = self.parameters.control.fastaccess
    der = self.parameters.derived.fastaccess
    flu = self.sequences.fluxes.fastaccess
    log = self.sequences.logs.fastaccess
    flu.remotefailure = 0
    for idx in range(con.nmblogentries):
        flu.remotefailure -= log.loggedtotalremotedischarge[idx]
    flu.remotefailure /= con.nmblogentries
    flu.remotefailure += con.remotedischargeminimum[der.toy[self.idx_sim]]


def calc_requiredremoterelease_v1(self):
    """Guess the required release necessary to not fall below the threshold
    value at a cross section far downstream with a certain level of certainty.

    Required control parameter:
      :class:`~hydpy.models.dam.dam_control.RemoteDischargeSafety`

    Required derived parameters:
      :class:`~hydpy.models.dam.dam_derived.RemoteDischargeSmoothPar`
      :class:`~hydpy.models.dam.dam_derived.TOY`

    Required flux sequence:
      :class:`~hydpy.models.dam.dam_fluxes.RemoteDemand`
      :class:`~hydpy.models.dam.dam_fluxes.RemoteFailure`

    Calculated flux sequence:
      :class:`~hydpy.models.dam.dam_fluxes.RequiredRelease`

    Basic equation:
      :math:`RequiredRemoteRelease = RemoteDemand + RemoteDischargeSafety
      \\cdot smooth\_logistic1(RemoteFailure, RemoteDischargeSmoothPar)`

    Used auxiliary method:
      :func:`~hydpy.cythons.smoothutils.smooth_logistic1`.

    Examples:

        As in the examples above, define a short simulation time period first:

        >>> from hydpy import pub
        >>> from hydpy.core.timetools import Timegrids, Timegrid
        >>> pub.timegrids = Timegrids(Timegrid('2001.03.30',
        ...                                    '2001.04.03',
        ...                                    '1d'))

        Prepare the dam model:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> derived.toy.update()

        Define a savety factor of 0.5 m³/s for the summer months and
        no savety factor at all for the winter months:

        >>> remotedischargesavety(_11_1_12=0.0, _03_31_12=0.0,
        ...                       _04_1_12=1.0, _10_31_12=1.0)
        >>> derived.remotedischargesmoothpar.update()

        Assume the actual demand at the cross section downsstream has actually
        been estimated to be 2 m³/s:

        >>> fluxes.remotedemand = 2.0

        Prepare a test function, that calculates the required discharge
        based on the parameter values defined above and for a "remote
        failure" values ranging between -4 and 4 m³/s:

        >>> from hydpy.core.testtools import UnitTest
        >>> test = UnitTest(model, model.calc_requiredremoterelease_v1,
        ...                 last_example=9,
        ...                 parseqs=(fluxes.remotefailure,
        ...                          fluxes.requiredremoterelease))
        >>> test.nexts.remotefailure = range(-4, 5)

        On May 31, the savety factor is 0 m³/s.  Hence no discharge is
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

        On April 1, the savety factor is 1 m³/s.  If the remote failure was
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
    con = self.parameters.control.fastaccess
    der = self.parameters.derived.fastaccess
    flu = self.sequences.fluxes.fastaccess
    flu.requiredremoterelease = (
            flu.remotedemand+con.remotedischargesavety[der.toy[self.idx_sim]] *
            modelutils.smooth_logistic1(
                    flu.remotefailure,
                    der.remotedischargesmoothpar[der.toy[self.idx_sim]]))


def calc_requiredrelease_v1(self):
    """Calculate the total water release required for reducing drought events.

    Required control parameter:
      :class:`~hydpy.models.dam.dam_control.NearDischargeMinimumThreshold`

    Required derived parameters:
      :class:`~hydpy.models.dam.dam_derived.NearDischargeMinimumSmoothPar2`
      :class:`~hydpy.models.dam.dam_derived.TOY`

    Required flux sequence:
      :class:`~hydpy.models.dam.dam_fluxes.RequiredRemoteRelease`

    Calculated flux sequence:
      :class:`~hydpy.models.dam.dam_fluxes.RequiredRelease`

    Basic equation:
      :math:`RequiredRelease = RequiredRemoteRelease
      \\cdot smooth\_logistic2(
      RequiredRemoteRelease-NearDischargeMinimumThreshold,
      NearDischargeMinimumSmoothPar2)`

    Used auxiliary method:
      :func:`~hydpy.cythons.smoothutils.smooth_logistic2`.

    Examples:

        As in the examples above, define a short simulation time period first:

        >>> from hydpy import pub
        >>> from hydpy.core.timetools import Timegrids, Timegrid
        >>> pub.timegrids = Timegrids(Timegrid('2001.03.30',
        ...                                    '2001.04.03',
        ...                                    '1d'))

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

        >>> from hydpy.core.testtools import UnitTest
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
    con = self.parameters.control.fastaccess
    der = self.parameters.derived.fastaccess
    flu = self.sequences.fluxes.fastaccess
    flu.requiredrelease = con.neardischargeminimumthreshold[
                                                    der.toy[self.idx_sim]]
    flu.requiredrelease = (flu.requiredrelease +
                           modelutils.smooth_logistic2(
                               flu.requiredremoterelease-flu.requiredrelease,
                               der.neardischargeminimumsmoothpar2[
                                                    der.toy[self.idx_sim]]))


def calc_targetedrelease_v1(self):
    """Calculate the targeted water release for reducing drought events,
    taking into account both the required water release and the actual
    inflow into the dam.

    Some dams are supposed to maintain a certain degree of low flow
    variability downstream.  Method
    :func:`~hydpy.models.dam.dam_model.calc_targetedrelease_v1` simulates
    this by (approximately) passing inflow as outflow whenever inflow
    is below the value of the threshold parameter
    :class:`~hydpy.models.dam.dam_control.NearDischargeMinimumThreshold`.

    Required control parameter:
      :class:`~hydpy.models.dam.dam_control.NearDischargeMinimumThreshold`

    Required derived parameters:
      :class:`~hydpy.models.dam.dam_derived.NearDischargeMinimumSmoothPar1`
      :class:`~hydpy.models.dam.dam_derived.TOY`

    Required flux sequence:
      :class:`~hydpy.models.dam.dam_fluxes.RequiredRelease`

    Calculated flux sequence:
      :class:`~hydpy.models.dam.dam_fluxes.TargetedRelease`

    Used auxiliary method:
      :func:`~hydpy.cythons.smoothutils.smooth_logistic1`

    Basic equation:
      :math:`TargetedRelease =
      w \\cdot RequiredRelease + (1-w) \\cdot Inflow`

      :math:`w = smooth\\_logistic1(
      Inflow-NearDischargeMinimumThreshold, NearDischargeMinimumSmoothPar)`

    Examples:

        As in the examples above, define a short simulation time period first:

        >>> from hydpy import pub
        >>> from hydpy.core.timetools import Timegrids, Timegrid
        >>> pub.timegrids = Timegrids(Timegrid('2001.03.30',
        ...                                    '2001.04.03',
        ...                                    '1d'))

        Prepare the dam model:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> derived.toy.update()

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

        >>> from hydpy.core.testtools import UnitTest
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
    """
    con = self.parameters.control.fastaccess
    der = self.parameters.derived.fastaccess
    flu = self.sequences.fluxes.fastaccess
    flu.targetedrelease = modelutils.smooth_logistic1(
            flu.inflow-con.neardischargeminimumthreshold[
                                                der.toy[self.idx_sim]],
            der.neardischargeminimumsmoothpar1[der.toy[self.idx_sim]])
    flu.targetedrelease = (flu.targetedrelease * flu.requiredrelease +
                           (1.-flu.targetedrelease) * flu.inflow)


def calc_actualrelease_v1(self):
    """Calculate the actual water release that can be supplied by the
    dam considering the targeted release and the given water level.

    Required control parameter:
      :class:`~hydpy.models.dam.dam_control.WaterLevelMinimumThreshold`

    Required derived parameters:
      :class:`~hydpy.models.dam.dam_derived.WaterLevelMinimumSmoothPar`

    Required flux sequence:
      :class:`~hydpy.models.dam.dam_fluxes.TargetedRelease`

    Required aide sequence:
      :class:`~hydpy.models.dam.dam_aides.WaterLevel`

    Calculated flux sequence:
      :class:`~hydpy.models.dam.dam_fluxes.ActualRelease`

    Basic equation:
      :math:`ActualRelease = TargetedRelease \\cdot
      smooth\_logistic1(WaterLevelMinimumThreshold-WaterLevel,
      WaterLevelMinimumSmoothPar)`

    Used auxiliary method:
      :func:`~hydpy.cythons.smoothutils.smooth_logistic1`.

    Examples:

        Prepare the dam model:

        >>> from hydpy.models.dam import *
        >>> parameterstep()

        Assume the required release has previously been estimated
        to be 2 m³/s:

        >>> fluxes.targetedrelease = 2.0

        Prepare a test function, that calculates the targeted water release
        for water levels ranging between -1 and 5 m:

        >>> from hydpy.core.testtools import UnitTest
        >>> test = UnitTest(model, model.calc_actualrelease_v1,
        ...                 last_example=7,
        ...                 parseqs=(aides.waterlevel,
        ...                          fluxes.actualrelease))
        >>> test.nexts.waterlevel = range(-1, 6)

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
    con = self.parameters.control.fastaccess
    der = self.parameters.derived.fastaccess
    flu = self.sequences.fluxes.fastaccess
    aid = self.sequences.aides.fastaccess
    flu.actualrelease = (flu.targetedrelease *
                         modelutils.smooth_logistic1(
                                 aid.waterlevel-con.waterlevelminimumthreshold,
                                 der.waterlevelminimumsmoothpar))


def calc_flooddischarge_v1(self):
    """Calculate the discharge during and after a flood event based on an
    artificial neural network describing the relationship between discharge
    and water stage.

    Required control parameter:
      :class:`~hydpy.models.dam.dam_control.WaterLevel2FloodDischarge`

    Required aide sequence:
      :class:`~hydpy.models.dam.dam_aides.WaterLevel`

    Calculated flux sequence:
      :class:`~hydpy.models.dam.dam_fluxes.FloodDischarge`

    Example:

        Prepare a dam model:

        >>> from hydpy.models.dam import *
        >>> parameterstep()

        Prepare a relatively simple relationship based on two neuron
        contained in a single hidden layer:

        >>> waterlevel2flooddischarge(nmb_inputs=1,
        ...                           nmb_neurons=(2,),
        ...                           nmb_outputs=1,
        ...                           weights_input=[[50., 4]],
        ...                           weights_output=[[2.], [30]],
        ...                           intercepts_hidden=[[-13000, -1046]],
        ...                           intercepts_output=[0.])

        The following example shows two distinct effects of both neurons.
        One neuron describes a relatively sharp increase between 259.8
        and 260.2 meters from about 0 to 2 m³/s.  This could describe
        a release of water through a bottom outlet controlled by a valve.
        The add something like an exponential increase between 260 and
        261 meters, which could describe the uncontrolled flow over a
        spillway:

        >>> from hydpy.core.testtools import UnitTest
        >>> test = UnitTest(model, model.calc_flooddischarge_v1,
        ...                 last_example=21)
        >>> test.nexts.waterlevel = numpy.arange(257, 261.1, 0.2)
        >>> test()
        | ex. | flooddischarge | waterlevel |
        -------------------------------------
        |   1 |            0.0 |      257.0 |
        |   2 |       0.000001 |      257.2 |
        |   3 |       0.000002 |      257.4 |
        |   4 |       0.000005 |      257.6 |
        |   5 |       0.000011 |      257.8 |
        |   6 |       0.000025 |      258.0 |
        |   7 |       0.000056 |      258.2 |
        |   8 |       0.000124 |      258.4 |
        |   9 |       0.000275 |      258.6 |
        |  10 |       0.000612 |      258.8 |
        |  11 |       0.001362 |      259.0 |
        |  12 |       0.003031 |      259.2 |
        |  13 |       0.006745 |      259.4 |
        |  14 |       0.015006 |      259.6 |
        |  15 |       0.033467 |      259.8 |
        |  16 |       1.074179 |      260.0 |
        |  17 |       2.164498 |      260.2 |
        |  18 |       2.363853 |      260.4 |
        |  19 |        2.79791 |      260.6 |
        |  20 |       3.719725 |      260.8 |
        |  21 |       5.576088 |      261.0 |

    """
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    aid = self.sequences.aides.fastaccess
    con.waterlevel2flooddischarge.inputs[0] = aid.waterlevel
    con.waterlevel2flooddischarge.process_actual_input()
    flu.flooddischarge = con.waterlevel2flooddischarge.outputs[0]


def calc_outflow_v1(self):
    """Calculate the total outflow of the dam.
`
    Required flux sequences:
      :class:`~hydpy.models.dam.dam_fluxes.ActualRelease`
      :class:`~hydpy.models.dam.dam_fluxes.FloodDischarge`

    Calculated flux sequence:
      :class:`~hydpy.models.dam.dam_fluxes.Outflow`

    Basic equation:
      :math:`Outflow = ActualRelease + FloodDischarge`

    Example:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> fluxes.actualrelease = 2.0
        >>> fluxes.flooddischarge = 3.0
        >>> model.calc_outflow_v1()
        >>> fluxes.outflow
        outflow(5.0)
    """
    flu = self.sequences.fluxes.fastaccess
    flu.outflow = flu.actualrelease + flu.flooddischarge


def update_watervolume_v1(self):
    """Update the actual water volume.

    Required derived parameter:
      :class:`~hydpy.models.dam.dam_derived.Seconds`

    Required flux sequences:
      :class:`~hydpy.models.dam.dam_fluxes.Inflow`
      :class:`~hydpy.models.dam.dam_fluxes.Outflow`

    Updated state sequence:
      :class:`~hydpy.models.dam.dam_states.WaterVolume`

    Basic equation:
      :math:`\\frac{d}{dt}WaterVolume = Inflow - Outflow`

    Example:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> states.watervolume.old = 5.0
        >>> fluxes.inflow = 2.0
        >>> fluxes.outflow = 3.0
        >>> model.update_watervolume_v1()
        >>> states.watervolume
        watervolume(4.0)
    """
    der = self.parameters.derived.fastaccess
    flu = self.sequences.fluxes.fastaccess
    old = self.sequences.states.fastaccess_old
    new = self.sequences.states.fastaccess_new
    new.watervolume = old.watervolume + der.seconds*(flu.inflow-flu.outflow)


def pass_outflow_v1(self):
    """Update the outlet link sequence."""
    flu = self.sequences.fluxes.fastaccess
    out = self.sequences.outlets.fastaccess
    out.q[0] += flu.outflow


def update_loggedoutflow_v1(self):
    """Log a new entry of discharge at a cross section far downstream.

    Required control parameter:
      :class:`~hydpy.models.dam.dam_derived.NmbLogEntries`

    Required flux sequence:
      :class:`~hydpy.models.dam.dam_fluxes.Outflow`

    Calculated flux sequence:
      :class:`~hydpy.models.dam.dam_logs.LoggedOutflow`

    Example:

        The following example shows that, with each new method call, the
        three memorized values are successively moved to the right and the
        respective new value is stored on the bare left position:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> nmblogentries(3)
        >>> from hydpy.core.testtools import UnitTest
        >>> test = UnitTest(model, model.update_loggedoutflow_v1,
        ...                 last_example=4)
        >>> test.nexts.outflow = [1., 3., 2., 4]
        >>> test()
        | ex. | outflow |           loggedoutflow |
        -------------------------------------------
        |   1 |     1.0 | 1.0  nan            nan |
        |   2 |     3.0 | 3.0  1.0            nan |
        |   3 |     2.0 | 2.0  3.0            1.0 |
        |   4 |     4.0 | 4.0  2.0            3.0 |
    """
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    log = self.sequences.logs.fastaccess
    for idx in range(con.nmblogentries-1, 0, -1):
        log.loggedoutflow[idx] = log.loggedoutflow[idx-1]
    log.loggedoutflow[0] = flu.outflow


class Model(modeltools.ModelELS):
    """Dam base model."""

    _INLET_METHODS = (pic_inflow_v1,
                      pic_totalremotedischarge_v1,
                      calc_naturalremotedischarge_v1,
                      calc_remotedemand_v1,
                      calc_remotefailure_v1,
                      calc_requiredremoterelease_v1,
                      calc_requiredrelease_v1,
                      calc_targetedrelease_v1)
    _RECEIVER_METHODS = (update_loggedtotalremotedischarge_v1,)
    _PART_ODE_METHODS = (pic_inflow_v1,
                         calc_waterlevel_v1,
                         calc_actualrelease_v1,
                         calc_flooddischarge_v1,
                         calc_outflow_v1)
    _FULL_ODE_METHODS = (update_watervolume_v1,)
    _OUTLET_METHODS = (pass_outflow_v1,
                       update_loggedoutflow_v1)
