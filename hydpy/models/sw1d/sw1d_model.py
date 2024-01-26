# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import modeltools
from hydpy.core.typingtools import *
from hydpy.cythons import modelutils
from hydpy.cythons import smoothutils
from hydpy.interfaces import channelinterfaces
from hydpy.models.sw1d import sw1d_control
from hydpy.models.sw1d import sw1d_derived
from hydpy.models.sw1d import sw1d_fixed
from hydpy.models.sw1d import sw1d_inlets
from hydpy.models.sw1d import sw1d_outlets
from hydpy.models.sw1d import sw1d_factors
from hydpy.models.sw1d import sw1d_fluxes
from hydpy.models.sw1d import sw1d_states
from hydpy.models.sw1d import sw1d_receivers
from hydpy.models.sw1d import sw1d_senders


# pick data from and pass data to link sequences


class Pick_Inflow_V1(modeltools.Method):
    """Pick the longitudinal inflow from an arbitrary number of inlet sequences."""

    REQUIREDSEQUENCES = (sw1d_inlets.LongQ,)
    RESULTSEQUENCES = (sw1d_fluxes.Inflow,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        inl = model.sequences.inlets.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.inflow = 0.0
        for i in range(inl.len_longq):
            flu.inflow += inl.longq[i][0]


class Pick_Outflow_V1(modeltools.Method):
    """Pick the longitudinal outflow from an arbitrary number of outlet sequences."""

    REQUIREDSEQUENCES = (sw1d_outlets.LongQ,)
    RESULTSEQUENCES = (sw1d_fluxes.Outflow,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        out = model.sequences.outlets.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.outflow = 0.0
        for i in range(out.len_longq):
            flu.outflow += out.longq[i][0]


class Pick_LateralFlow_V1(modeltools.Method):
    """Pick the lateral inflow from an arbitrary number of inlet sequences."""

    REQUIREDSEQUENCES = (sw1d_inlets.LatQ,)
    RESULTSEQUENCES = (sw1d_fluxes.LateralFlow,)

    @staticmethod
    def __call__(model: modeltools.SegmentModel) -> None:
        inl = model.sequences.inlets.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.lateralflow = 0.0
        for i in range(inl.len_latq):
            flu.lateralflow += inl.latq[i][0]


class Pick_WaterLevelDownstream_V1(modeltools.Method):
    """Pick the water level downstream from a receiver sequence."""

    REQUIREDSEQUENCES = (sw1d_receivers.WaterLevel,)
    RESULTSEQUENCES = (sw1d_factors.WaterLevelDownstream,)

    @staticmethod
    def __call__(model: modeltools.SegmentModel) -> None:
        fac = model.sequences.factors.fastaccess
        rec = model.sequences.receivers.fastaccess
        fac.waterleveldownstream = rec.waterlevel[0]


class Pass_Discharge_V1(modeltools.Method):
    """Pass the calculated average discharge of the current simulation step to an
    arbitrary number of inlet or outlet sequences.

    Basic equation:
      :math:`QLong = DischargeVolume / Seconds`

    In contrast to typical methods for passing data to nodes, |Pass_Discharge_V1| not
    only passes data to outlet sequences but also to inlet sequences.  This
    functionality addresses the rare but allowed setting of a discharge calculating
    routing model lying at the inlet position of a subchannel, which is necessary for
    modelling branches.

    Examples:

        Without any node connection, |Pass_Discharge_V1| does nothing:

        >>> from hydpy import Element, Nodes, prepare_model
        >>> e1 = Element("e1")
        >>> e1.model = prepare_model("sw1d_lias")
        >>> e1.model.pass_discharge_v1()

        If any connections exist, |Pass_Discharge_V1| updates all corresponding
        sequences with the same average discharge value:

        >>> ni, no1, no2 = Nodes("ni", "no1", "no2", defaultvariable="LongQ")
        >>> ni.sequences.sim = 1.0
        >>> no1.sequences.sim = 2.0
        >>> no2.sequences.sim = 3.0
        >>> e2 = Element("e2", inlets=ni, outlets=(no1, no2))
        >>> e2.model = prepare_model("sw1d_lias")
        >>> e2.model.parameters.derived.seconds(60.0)
        >>> e2.model.sequences.fluxes.dischargevolume = 120.0
        >>> e2.model.pass_discharge_v1()
        >>> ni.sequences.sim
        sim(3.0)
        >>> no1.sequences.sim
        sim(4.0)
        >>> no2.sequences.sim
        sim(5.0)

        .. testsetup::

            >>> from hydpy import Node
            >>> Node.clear_all()
            >>> Element.clear_all()
    """

    DERIVEDPARAMETERS = (sw1d_derived.Seconds,)
    REQUIREDSEQUENCES = (sw1d_fluxes.DischargeVolume,)
    RESULTSEQUENCES = (sw1d_inlets.LongQ, sw1d_outlets.LongQ)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        inl = model.sequences.inlets.fastaccess
        out = model.sequences.outlets.fastaccess
        flu = model.sequences.fluxes.fastaccess
        discharge: float = flu.dischargevolume / der.seconds
        for i in range(inl.len_longq):
            inl.longq[i][0] += discharge
        for i in range(out.len_longq):
            out.longq[i][0] += discharge


class Pass_WaterLevel_V1(modeltools.Method):
    """Pass the calculated water level to an arbitrary number of sender sequences."""

    REQUIREDSEQUENCES = (sw1d_factors.WaterLevel,)
    RESULTSEQUENCES = (sw1d_senders.WaterLevel,)

    @staticmethod
    def __call__(model: modeltools.SegmentModel) -> None:
        fac = model.sequences.factors.fastaccess
        sen = model.sequences.senders.fastaccess
        for i in range(sen.len_waterlevel):
            sen.waterlevel[i][0] = fac.waterlevel


# calculation methods


class Trigger_Preprocessing_V1(modeltools.Method):
    """Order all submodels following the |StorageModel_V1|, |RoutingModel_V1|,
    |RoutingModel_V2|, or |RoutingModel_V3| interface to prepare all invariant data for
    a new internal simulation step.

    Example:

        >>> from hydpy import Element, Node, prepare_model
        >>> nlong = Node("nlong", variable="LongQ")
        >>> nlat = Node("nlat", variable="LatQ")
        >>> e = Element("e", inlets=(nlong, nlat))
        >>> channel = prepare_model("sw1d_channel")
        >>> channel.parameters.control.nmbsegments(1)
        >>> with channel.add_routingmodel_v1("sw1d_q_in", position=0, update=False):
        ...     pass
        >>> with channel.add_storagemodel_v1("sw1d_storage", position=0, update=False):
        ...     pass
        >>> e.model = channel
        >>> nlong.sequences.sim = 1.0
        >>> nlat.sequences.sim = 2.0
        >>> channel.trigger_preprocessing_v1()
        >>> channel.routingmodels[0].sequences.fluxes.inflow
        inflow(1.0)
        >>> channel.storagemodels[0].sequences.fluxes.lateralflow
        lateralflow(2.0)

        .. testsetup::

            >>> Node.clear_all()
            >>> Element.clear_all()
    """

    SUBMODELINTERFACES = (
        channelinterfaces.RoutingModel_V1,
        channelinterfaces.RoutingModel_V2,
        channelinterfaces.RoutingModel_V3,
        channelinterfaces.StorageModel_V1,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        for i in range(model.routingmodels.number):
            if model.routingmodels.typeids[i] in (1, 2, 3):
                cast(
                    Union[
                        channelinterfaces.RoutingModel_V1,
                        channelinterfaces.RoutingModel_V2,
                        channelinterfaces.RoutingModel_V3,
                    ],
                    model.routingmodels.submodels[i],
                ).perform_preprocessing()
        for i in range(model.storagemodels.number):
            if model.storagemodels.typeids[i] == 1:
                cast(
                    channelinterfaces.StorageModel_V1, model.storagemodels.submodels[i]
                ).perform_preprocessing()


class Trigger_Postprocessing_V1(modeltools.Method):
    """Order all submodels following the |StorageModel_V1|, |RoutingModel_V1|,
    |RoutingModel_V2|, or |RoutingModel_V3| interface to execute all tasks relevant at
    the end of each external simulation step.

    Example:

        >>> from hydpy import Element, Node, prepare_model
        >>> nw = Node("nw", variable="WaterLevel")
        >>> e = Element("e", senders=nw)
        >>> channel = prepare_model("sw1d_channel")
        >>> channel.parameters.control.nmbsegments(1)
        >>> with channel.add_routingmodel_v1("sw1d_q_in", position=0, update=False):
        ...     derived.seconds(60.0)
        ...     fluxes.inflow = 2.0
        >>> with channel.add_storagemodel_v1("sw1d_storage", position=0, update=False):
        ...     factors.waterlevel = 2.0
        >>> e.model = channel
        >>> channel.trigger_postprocessing_v1()
        >>> channel.routingmodels[0].sequences.fluxes.dischargevolume
        dischargevolume(120.0)
        >>> nw.sequences.sim
        sim(2.0)

        .. testsetup::

            >>> Node.clear_all()
            >>> Element.clear_all()
    """

    SUBMODELINTERFACES = (
        channelinterfaces.RoutingModel_V1,
        channelinterfaces.RoutingModel_V2,
        channelinterfaces.RoutingModel_V3,
        channelinterfaces.StorageModel_V1,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        for i in range(model.routingmodels.number):
            if model.routingmodels.typeids[i] in (1, 2, 3):
                cast(
                    Union[
                        channelinterfaces.RoutingModel_V1,
                        channelinterfaces.RoutingModel_V2,
                        channelinterfaces.RoutingModel_V3,
                    ],
                    model.routingmodels.submodels[i],
                ).perform_postprocessing()
        for i in range(model.storagemodels.number):
            if model.storagemodels.typeids[i] == 1:
                cast(
                    channelinterfaces.StorageModel_V1, model.storagemodels.submodels[i]
                ).perform_postprocessing()


class Calc_MaxTimeStep_V1(modeltools.Method):
    r"""Estimate the highest possible computation time step for which we can expect
    stability for a central LIAS-like routing model.

    Basic equation :cite:p:`ref-Bates2010`:
      :math:`MaxTimeStep = TimeStepFactor \cdot
      \frac{1000 \cdot LengthMin}{GravitationalAcceleration \cdot WaterDepth}`

    Examples:

        >>> from hydpy.models.sw1d import *
        >>> parameterstep()
        >>> timestepfactor(0.5)
        >>> derived.lengthmin(2.0)
        >>> factors.waterdepth = 4.0
        >>> model.calc_maxtimestep_v1()
        >>> factors.maxtimestep
        maxtimestep(159.637714)

        |Calc_MaxTimeStep_V1| handles the case of zero water depth by setting the
        maximum time step to infinity:

        >>> factors.waterdepth = 0.0
        >>> model.calc_maxtimestep_v1()
        >>> factors.maxtimestep
        maxtimestep(inf)
    """

    CONTROLPARAMETERS = (sw1d_control.TimeStepFactor,)
    DERIVEDPARAMETERS = (sw1d_derived.LengthMin,)
    FIXEDPARAMETERS = (sw1d_fixed.GravitationalAcceleration,)
    REQUIREDSEQUENCES = (sw1d_factors.WaterDepth,)
    RESULTSEQUENCES = (sw1d_factors.MaxTimeStep,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fix = model.parameters.fixed.fastaccess
        fac = model.sequences.factors.fastaccess
        if fac.waterdepth > 0.0:
            fac.maxtimestep = (con.timestepfactor * 1000.0 * der.lengthmin) / (
                fix.gravitationalacceleration * fac.waterdepth
            ) ** 0.5
        else:
            fac.maxtimestep = modelutils.inf


class Calc_MaxTimeStep_V2(modeltools.Method):
    r"""Estimate the highest possible computation time step for which we can expect
    stability for an inflow-providing routing model.

    Basic equation:
      :math:`MaxTimeStep = TimeStepFactor \cdot
      \frac{1000 \cdot LengthDownstream}{5 / 3 \cdot |Inflow| \cdot WettedArea}`

    Examples:

        >>> from hydpy.models.sw1d import *
        >>> parameterstep()
        >>> timestepfactor(0.5)
        >>> lengthdownstream(2.0)
        >>> factors.wettedarea = 5.0
        >>> fluxes.inflow = 6.0
        >>> model.calc_maxtimestep_v2()
        >>> factors.maxtimestep
        maxtimestep(500.0)

        For zero inflow values, the computation time step needs no restriction:

        >>> fluxes.inflow = 0.0
        >>> model.calc_maxtimestep_v2()
        >>> factors.maxtimestep
        maxtimestep(inf)

        To prevent zero division, |Calc_MaxTimeStep_V2| also sets the maximum time step
        to infinity if there is no wetted area:

        >>> fluxes.inflow = 6.0
        >>> factors.wettedarea = 0.0
        >>> model.calc_maxtimestep_v2()
        >>> factors.maxtimestep
        maxtimestep(inf)
    """

    CONTROLPARAMETERS = (sw1d_control.LengthDownstream, sw1d_control.TimeStepFactor)
    REQUIREDSEQUENCES = (sw1d_fluxes.Inflow, sw1d_factors.WettedArea)
    RESULTSEQUENCES = (sw1d_factors.MaxTimeStep,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        if (flu.inflow != 0.0) and (fac.wettedarea > 0.0):
            cel: float = modelutils.fabs(5.0 / 3.0 * flu.inflow / fac.wettedarea)
            fac.maxtimestep = con.timestepfactor * 1000.0 * con.lengthdownstream / cel
        else:
            fac.maxtimestep = modelutils.inf


class Calc_MaxTimeStep_V3(modeltools.Method):
    r"""Estimate the highest possible computation time step for which we can expect
    stability for a weir-like routing model.

    Basic equation:
      .. math::
        MaxTimeStep = f \cdot \frac{1000 \cdot l}{c\cdot \sqrt{2 \cdot g \cdot h}}
        \\ \\
        f = TimeStepFactor \\
        l = LengthDownstream \\
        c = FlowCoefficient \\
        g = GravitationalAcceleration \\
        h = WaterLevel - CrestHeight

    Examples:

        >>> from hydpy.models.sw1d import *
        >>> parameterstep()
        >>> crestheight(5.0)
        >>> flowcoefficient(0.6)
        >>> timestepfactor(0.5)
        >>> lengthupstream(2.0)
        >>> factors.waterlevel = 7.0
        >>> model.calc_maxtimestep_v3()
        >>> factors.maxtimestep
        maxtimestep(266.062857)

        For water levels equal to or below the crest height, the flow over the weir is
        zero and thus cannot cause instability.  Hence, |Calc_MaxTimeStep_V3| sets
        |MaxTimeStep| to infinity in such cases:

        >>> factors.waterlevel = 5.0
        >>> model.calc_maxtimestep_v3()
        >>> factors.maxtimestep
        maxtimestep(inf)
        >>> factors.waterlevel = 3.0
        >>> model.calc_maxtimestep_v3()
        >>> factors.maxtimestep
        maxtimestep(inf)
    """

    CONTROLPARAMETERS = (
        sw1d_control.LengthUpstream,
        sw1d_control.TimeStepFactor,
        sw1d_control.FlowCoefficient,
        sw1d_control.CrestHeight,
    )
    FIXEDPARAMETERS = (sw1d_fixed.GravitationalAcceleration,)
    REQUIREDSEQUENCES = (sw1d_factors.WaterLevel,)
    RESULTSEQUENCES = (sw1d_factors.MaxTimeStep,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fix = model.parameters.fixed.fastaccess
        fac = model.sequences.factors.fastaccess
        h: float = fac.waterlevel - con.crestheight
        if h > 0.0:
            c: float = con.flowcoefficient
            g: float = fix.gravitationalacceleration
            cel: float = c * (2.0 * g * h) ** 0.5
            fac.maxtimestep = con.timestepfactor * 1000.0 * con.lengthupstream / cel
        else:
            fac.maxtimestep = modelutils.inf


class Calc_MaxTimeStep_V4(modeltools.Method):
    r"""Estimate the highest possible computation time step for which we can expect
    stability for an outflow-providing routing model.

    Basic equation:
      :math:`MaxTimeStep = TimeStepFactor \cdot
      \frac{1000 \cdot LengthUpstream}{5 / 3 \cdot |Outflow| \cdot WettedArea}`

    Examples:

        >>> from hydpy.models.sw1d import *
        >>> parameterstep()
        >>> timestepfactor(0.5)
        >>> lengthupstream(2.0)
        >>> factors.wettedarea = 5.0
        >>> fluxes.outflow = 6.0
        >>> model.calc_maxtimestep_v4()
        >>> factors.maxtimestep
        maxtimestep(500.0)

        For zero outflow values, the computation time step needs no restriction:

        >>> fluxes.outflow = 0.0
        >>> model.calc_maxtimestep_v4()
        >>> factors.maxtimestep
        maxtimestep(inf)

        To prevent zero division, |Calc_MaxTimeStep_V4| also sets the maximum time step
        to infinity if there is no wetted area:

        >>> fluxes.outflow = 6.0
        >>> factors.wettedarea = 0.0
        >>> model.calc_maxtimestep_v4()
        >>> factors.maxtimestep
        maxtimestep(inf)
    """

    CONTROLPARAMETERS = (sw1d_control.LengthUpstream, sw1d_control.TimeStepFactor)
    REQUIREDSEQUENCES = (sw1d_fluxes.Outflow, sw1d_factors.WettedArea)
    RESULTSEQUENCES = (sw1d_factors.MaxTimeStep,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        if (flu.outflow != 0.0) and (fac.wettedarea > 0.0):
            cel: float = modelutils.fabs(5.0 / 3.0 * flu.outflow / fac.wettedarea)
            fac.maxtimestep = con.timestepfactor * 1000.0 * con.lengthupstream / cel
        else:
            fac.maxtimestep = modelutils.inf


class Calc_MaxTimeStep_V5(modeltools.Method):
    r"""Estimate the highest possible computation time step for which we can expect
    stability for a gate-like routing model.

    Basic equation:
      .. math::
        MaxTimeStep = f \cdot \frac{1000 \cdot l}{c \cdot \big( min (h, \ l) - b \big)
        \cdot \sqrt{2 \cdot g  \cdot (l_u - l_d)}}
        \\ \\
        f = TimeStepFactor \\
        c = FlowCoefficient \\
        h = GateHeight \\
        l = WaterLevel \\
        l_u = WaterLevelUpstream \\
        l_d = WaterLevelDownstream\\
        b = BottomLevel \\
        g = GravitationalAcceleration

    Examples:

        The following examples all correspond to selected ones of |Calc_Discharge_V3|.

        The case of a submerged gate and downstream flow:

        >>> from hydpy.models.sw1d import *
        >>> parameterstep()
        >>> bottomlevel(4.0)
        >>> gateheight(6.0)
        >>> flowcoefficient(0.6)
        >>> lengthupstream(4.0)
        >>> timestepfactor(0.5)
        >>> factors.waterlevel = 8.0
        >>> factors.waterlevelupstream = 9.0
        >>> factors.waterleveldownstream = 7.0
        >>> model.calc_maxtimestep_v5()
        >>> factors.maxtimestep
        maxtimestep(266.062857)

        The case of a non-submerged gate and upstream flow:

        >>> gateheight(8.0)
        >>> factors.waterlevelupstream = 7.0
        >>> factors.waterleveldownstream = 9.0
        >>> model.calc_maxtimestep_v5()
        >>> factors.maxtimestep
        maxtimestep(133.031429)

        The case of a negative effective gate opening with zero discharge:

        >>> gateheight(0.0)
        >>> factors.waterlevelupstream = 7.0
        >>> factors.waterleveldownstream = 9.0
        >>> model.calc_maxtimestep_v5()
        >>> factors.maxtimestep
        maxtimestep(inf)

        The case of a controlled gate opening:

        >>> def sluice(model) -> None:
        ...     con = model.parameters.control.fastaccess
        ...     fac = model.sequences.factors.fastaccess
        ...     if fac.waterlevelupstream < fac.waterleveldownstream:
        ...         con.gateheight = 4.0
        ...     else:
        ...         con.gateheight = 10.0
        >>> gateheight(callback=sluice)
        >>> factors.waterlevelupstream = 9.0
        >>> factors.waterleveldownstream = 7.0
        >>> model.calc_maxtimestep_v5()
        >>> factors.maxtimestep
        maxtimestep(133.031429)
        >>> factors.waterlevelupstream = 7.0
        >>> factors.waterleveldownstream = 9.0
        >>> model.calc_maxtimestep_v5()
        >>> factors.maxtimestep
        maxtimestep(inf)
    """

    CONTROLPARAMETERS = (
        sw1d_control.LengthUpstream,
        sw1d_control.BottomLevel,
        sw1d_control.GateHeight,
        sw1d_control.FlowCoefficient,
        sw1d_control.TimeStepFactor,
    )
    FIXEDPARAMETERS = (sw1d_fixed.GravitationalAcceleration,)
    REQUIREDSEQUENCES = (
        sw1d_factors.WaterLevel,
        sw1d_factors.WaterLevelUpstream,
        sw1d_factors.WaterLevelDownstream,
    )
    RESULTSEQUENCES = (sw1d_factors.MaxTimeStep,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fix = model.parameters.fixed.fastaccess
        fac = model.sequences.factors.fastaccess
        con.gateheight_callback(model)
        h: float = min(con.gateheight, fac.waterlevel) - con.bottomlevel
        if h > 0.0:
            c: float = con.flowcoefficient
            g: float = fix.gravitationalacceleration
            lu: float = fac.waterlevelupstream
            ld: float = fac.waterleveldownstream
            cel: float = c * h * (2.0 * g * modelutils.fabs(lu - ld)) ** 0.5
            fac.maxtimestep = con.timestepfactor * 1000.0 * con.lengthupstream / cel
        else:
            fac.maxtimestep = modelutils.inf


class Calc_MaxTimeSteps_V1(modeltools.Method):
    """Order all submodels that follow the |RoutingModel_V1|, |RoutingModel_V2|, or
    |RoutingModel_V3| interface to estimate the highest possible computation time step.

    Example:

        >>> from hydpy.models.sw1d_channel import *
        >>> parameterstep()
        >>> nmbsegments(2)
        >>> with model.add_storagemodel_v1("sw1d_storage", position=0, update=False):
        ...     factors.waterlevel = 6.0
        >>> with model.add_routingmodel_v2("sw1d_lias", position=1, update=False):
        ...     timestepfactor(0.5)
        ...     bottomlevel(1.0)
        ...     derived.weightupstream(0.5)
        ...     derived.lengthmin(2.0)
        ...     factors.waterdepth = 4.0
        >>> with model.add_storagemodel_v1("sw1d_storage", position=1, update=False):
        ...     factors.waterlevel = 4.0
        >>> model.calc_maxtimesteps_v1()
        >>> model.routingmodels[1].sequences.factors.maxtimestep
        maxtimestep(159.637714)
    """

    SUBMODELINTERFACES = (
        channelinterfaces.RoutingModel_V1,
        channelinterfaces.RoutingModel_V2,
        channelinterfaces.RoutingModel_V3,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        for i in range(model.routingmodels.number):
            if model.routingmodels.typeids[i] in (1, 2, 3):
                cast(
                    Union[
                        channelinterfaces.RoutingModel_V1,
                        channelinterfaces.RoutingModel_V2,
                        channelinterfaces.RoutingModel_V3,
                    ],
                    model.routingmodels.submodels[i],
                ).determine_maxtimestep()


class Calc_TimeStep_V1(modeltools.Method):
    r"""Determine the computation time step for which we can expect stability for a
    complete channel network.

    Examples:

        Usually, |Calc_TimeStep_V1| takes the minimum of the individual routing models'
        |MaxTimeStep| estimates:

        >>> from hydpy.models.sw1d_channel import *
        >>> parameterstep()
        >>> nmbsegments(2)
        >>> with model.add_routingmodel_v2("sw1d_lias", position=0, update=False):
        ...     factors.maxtimestep = 6.0
        >>> with model.add_routingmodel_v2("sw1d_lias", position=1, update=False):
        ...     factors.maxtimestep = 7.0
        >>> model.timeleft = 7.0
        >>> model.calc_timestep_v1()
        >>> factors.timestep
        timestep(6.0)
        >>> from hydpy import round_
        >>> round_(model.timeleft)
        1.0

        When appropriate, the `timeleft` argument synchronises the end of the next
        internal computation step with the end of the current external simulation step:

        >>> model.timeleft = 5.0
        >>> model.calc_timestep_v1()
        >>> factors.timestep
        timestep(5.0)
        >>> round_(model.timeleft)
        0.0
    """

    SUBMODELINTERFACES = (
        channelinterfaces.RoutingModel_V1,
        channelinterfaces.RoutingModel_V2,
        channelinterfaces.RoutingModel_V3,
    )
    RESULTSEQUENCES = (sw1d_factors.TimeStep,)

    @staticmethod
    def __call__(model: modeltools.SubstepModel) -> None:
        fac = model.sequences.factors.fastaccess

        fac.timestep = modelutils.inf
        for i in range(model.routingmodels.number):
            if model.routingmodels.typeids[i] in (1, 2, 3):
                timestep: float = cast(
                    Union[
                        channelinterfaces.RoutingModel_V1,
                        channelinterfaces.RoutingModel_V2,
                        channelinterfaces.RoutingModel_V3,
                    ],
                    model.routingmodels.submodels[i],
                ).get_maxtimestep()
                if timestep < fac.timestep:
                    fac.timestep = timestep
        if fac.timestep < model.timeleft:
            model.timeleft -= fac.timestep
        else:
            fac.timestep = model.timeleft
            model.timeleft = 0.0


class Send_TimeStep_V1(modeltools.Method):
    """Send the actual computation time step to all submodels following the
    |StorageModel_V1|, |RoutingModel_V1|, |RoutingModel_V2|, or |RoutingModel_V3|
    interface.

    Example:

        >>> from hydpy.models.sw1d_channel import *
        >>> parameterstep()
        >>> nmbsegments(1)
        >>> with model.add_routingmodel_v2("sw1d_lias", position=0, update=False):
        ...     factors.maxtimestep = 6.0
        >>> with model.add_storagemodel_v1("sw1d_storage", position=0, update=False):
        ...     factors.maxtimestep = 6.0
        >>> factors.timestep = 5.0
        >>> model.send_timestep_v1()
        >>> model.routingmodels[0].sequences.factors.timestep
        timestep(5.0)
        >>> model.storagemodels[0].sequences.factors.timestep
        timestep(5.0)
    """

    SUBMODELINTERFACES = (
        channelinterfaces.RoutingModel_V1,
        channelinterfaces.RoutingModel_V2,
        channelinterfaces.RoutingModel_V3,
        channelinterfaces.StorageModel_V1,
    )
    REQUIREDSEQUENCES = (sw1d_factors.TimeStep,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        fac = model.sequences.factors.fastaccess

        for i in range(model.routingmodels.number):
            if model.routingmodels.typeids[i] in (1, 2, 3):
                cast(
                    Union[
                        channelinterfaces.RoutingModel_V1,
                        channelinterfaces.RoutingModel_V2,
                        channelinterfaces.RoutingModel_V3,
                    ],
                    model.routingmodels.submodels[i],
                ).set_timestep(fac.timestep)
        for i in range(model.storagemodels.number):
            if model.storagemodels.typeids[i] == 1:
                cast(
                    channelinterfaces.StorageModel_V1, model.storagemodels.submodels[i]
                ).set_timestep(fac.timestep)


class Calc_WaterLevelUpstream_V1(modeltools.Method):
    """Query the water level from an upstream submodel that follows the
    |StorageModel_V1| interface.

    Example:

        >>> from hydpy import prepare_model
        >>> main, sub = prepare_model("sw1d"), prepare_model("sw1d_storage")
        >>> sub.sequences.factors.waterlevel = 2.0
        >>> main.storagemodelupstream = sub
        >>> main.storagemodelupstream_typeid = 1
        >>> main.calc_waterlevelupstream_v1()
        >>> main.sequences.factors.waterlevelupstream
        waterlevelupstream(2.0)
    """

    SUBMODELINTERFACES = (channelinterfaces.StorageModel_V1,)
    RESULTSEQUENCES = (sw1d_factors.WaterLevelUpstream,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        fac = model.sequences.factors.fastaccess
        if model.storagemodelupstream_typeid == 1:
            fac.waterlevelupstream = cast(
                channelinterfaces.StorageModel_V1, model.storagemodelupstream
            ).get_waterlevel()


class Calc_WaterLevelDownstream_V1(modeltools.Method):
    """Query the water level from a downstream submodel that follows the
    |StorageModel_V1| interface.

    Example:

        >>> from hydpy import prepare_model
        >>> main, sub = prepare_model("sw1d"), prepare_model("sw1d_storage")
        >>> sub.sequences.factors.waterlevel = 2.0
        >>> main.storagemodeldownstream = sub
        >>> main.storagemodeldownstream_typeid = 1
        >>> main.calc_waterleveldownstream_v1()
        >>> main.sequences.factors.waterleveldownstream
        waterleveldownstream(2.0)
    """

    SUBMODELINTERFACES = (channelinterfaces.StorageModel_V1,)
    RESULTSEQUENCES = (sw1d_factors.WaterLevelDownstream,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        fac = model.sequences.factors.fastaccess
        if model.storagemodeldownstream_typeid == 1:
            fac.waterleveldownstream = cast(
                channelinterfaces.StorageModel_V1, model.storagemodeldownstream
            ).get_waterlevel()


class Calc_WaterVolumeUpstream_V1(modeltools.Method):
    """Query the water volume from an upstream submodel that follows the
    |StorageModel_V1| interface.

    Example:

        >>> from hydpy import prepare_model
        >>> main, sub = prepare_model("sw1d"), prepare_model("sw1d_storage")
        >>> sub.sequences.states.watervolume = 2.0
        >>> main.storagemodelupstream = sub
        >>> main.storagemodelupstream_typeid = 1
        >>> main.calc_watervolumeupstream_v1()
        >>> main.sequences.factors.watervolumeupstream
        watervolumeupstream(2.0)
    """

    SUBMODELINTERFACES = (channelinterfaces.StorageModel_V1,)
    RESULTSEQUENCES = (sw1d_factors.WaterVolumeUpstream,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        fac = model.sequences.factors.fastaccess
        if model.storagemodelupstream_typeid == 1:
            fac.watervolumeupstream = cast(
                channelinterfaces.StorageModel_V1, model.storagemodelupstream
            ).get_watervolume()


class Calc_WaterVolumeDownstream_V1(modeltools.Method):
    """Query the water volume from a downstream submodel that follows the
    |StorageModel_V1| interface.

    Example:

        >>> from hydpy import prepare_model
        >>> main, sub = prepare_model("sw1d"), prepare_model("sw1d_storage")
        >>> sub.sequences.states.watervolume = 2.0
        >>> main.storagemodeldownstream = sub
        >>> main.storagemodeldownstream_typeid = 1
        >>> main.calc_watervolumedownstream_v1()
        >>> main.sequences.factors.watervolumedownstream
        watervolumedownstream(2.0)
    """

    SUBMODELINTERFACES = (channelinterfaces.StorageModel_V1,)
    RESULTSEQUENCES = (sw1d_factors.WaterVolumeDownstream,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        fac = model.sequences.factors.fastaccess
        if model.storagemodeldownstream_typeid == 1:
            fac.watervolumedownstream = cast(
                channelinterfaces.StorageModel_V1, model.storagemodeldownstream
            ).get_watervolume()


class Calc_WaterLevel_V1(modeltools.Method):
    r"""Calculate the water level based on the water depth.

    Basic equation:
      :math:`WaterLevel = BottomLevel + WaterDepth`

    Example:

        >>> from hydpy.models.sw1d import *
        >>> parameterstep()
        >>> bottomlevel(3.0)
        >>> factors.waterdepth = 2.0
        >>> model.calc_waterlevel_v1()
        >>> factors.waterlevel
        waterlevel(5.0)
    """

    CONTROLPARAMETERS = (sw1d_control.BottomLevel,)
    REQUIREDSEQUENCES = (sw1d_factors.WaterDepth,)
    RESULTSEQUENCES = (sw1d_factors.WaterLevel,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        fac.waterlevel = con.bottomlevel + fac.waterdepth


class Calc_WaterLevel_V2(modeltools.Method):
    r"""Interpolate the water level based on the water levels of the adjacent channel
    segments.

    Basic equation:
      .. math::
        WaterLevel =
        \omega \cdot WaterLevelUpstream + (1 - \omega) \cdot WaterLevelDownstream
        \\ \\
        \omega = WeightUpstream

    Example:

        >>> from hydpy.models.sw1d import *
        >>> parameterstep()
        >>> derived.weightupstream(0.8)
        >>> factors.waterlevelupstream = 3.0
        >>> factors.waterleveldownstream = 1.0
        >>> model.calc_waterlevel_v2()
        >>> factors.waterlevel
        waterlevel(2.6)
    """

    DERIVEDPARAMETERS = (sw1d_derived.WeightUpstream,)
    REQUIREDSEQUENCES = (
        sw1d_factors.WaterLevelUpstream,
        sw1d_factors.WaterLevelDownstream,
    )
    RESULTSEQUENCES = (sw1d_factors.WaterLevel,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        w: float = der.weightupstream
        fac.waterlevel = (
            w * fac.waterlevelupstream + (1.0 - w) * fac.waterleveldownstream
        )


class Calc_WaterLevel_V3(modeltools.Method):
    r"""Take the water level from the downstream channel segment.

    Basic equation:
      :math:`WaterLevel = WaterLevelDownstream`

    Example:

        >>> from hydpy.models.sw1d import *
        >>> parameterstep()
        >>> factors.waterleveldownstream = 3.0
        >>> model.calc_waterlevel_v3()
        >>> factors.waterlevel
        waterlevel(3.0)
    """

    REQUIREDSEQUENCES = (sw1d_factors.WaterLevelDownstream,)
    RESULTSEQUENCES = (sw1d_factors.WaterLevel,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        fac = model.sequences.factors.fastaccess
        fac.waterlevel = fac.waterleveldownstream


class Calc_WaterLevel_V4(modeltools.Method):
    r"""Take the water level from the upstream channel segment.

    Basic equation:
      :math:`WaterLevel = WaterLevelUpstream`

    Example:

        >>> from hydpy.models.sw1d import *
        >>> parameterstep()
        >>> factors.waterlevelupstream = 3.0
        >>> model.calc_waterlevel_v4()
        >>> factors.waterlevel
        waterlevel(3.0)
    """

    REQUIREDSEQUENCES = (sw1d_factors.WaterLevelUpstream,)
    RESULTSEQUENCES = (sw1d_factors.WaterLevel,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        fac = model.sequences.factors.fastaccess
        fac.waterlevel = fac.waterlevelupstream


class Calc_WaterLevel_V5(modeltools.Method):
    """Average the upstream and the downstream water level.

    Basic equation:
      :math:`WaterLevel = (WaterLevelUpstream + WaterLevelUpstream) / 2`

    Example:

        >>> from hydpy.models.sw1d import *
        >>> parameterstep()
        >>> factors.waterlevelupstream = 3.0
        >>> factors.waterleveldownstream = 1.0
        >>> model.calc_waterlevel_v5()
        >>> factors.waterlevel
        waterlevel(2.0)
    """

    REQUIREDSEQUENCES = (
        sw1d_factors.WaterLevelUpstream,
        sw1d_factors.WaterLevelDownstream,
    )
    RESULTSEQUENCES = (sw1d_factors.WaterLevel,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        fac = model.sequences.factors.fastaccess
        fac.waterlevel = (fac.waterlevelupstream + fac.waterleveldownstream) / 2.0


class Calc_WaterDepth_V1(modeltools.Method):
    r"""Calculate the water depth assuming a symmetric trapezoidal channel profile.

    Basic equation:
      .. math::
        WaterDepth = \begin{cases}
        a / w &|\ s = 0
        \\
        \left( \sqrt{4 \cdot s \cdot a + w^2} - w \right) / (2 \cdot s) &|\ s > 0
        \end{cases}
        \\ \\
        a = WaterVolume / Length \\
        w = BottomWidth \\
        s = SideSlope

    Examples:

        The first example deals with a rectangular profile:

        >>> from hydpy.models.sw1d import *
        >>> parameterstep()
        >>> length(2.0)
        >>> bottomwidth(3.0)
        >>> sideslope(0.0)
        >>> states.watervolume = 1.0
        >>> model.calc_waterdepth_v1()
        >>> factors.waterdepth
        waterdepth(0.166667)

        The second example deals with a triangular profile:

        >>> bottomwidth(0.0)
        >>> sideslope(2.0)
        >>> states.watervolume = 2.0
        >>> model.calc_waterdepth_v1()
        >>> factors.waterdepth
        waterdepth(0.707107)

        The third example combines the two profiles defined above into a trapezoidal
        profile:

        >>> bottomwidth(3.0)
        >>> sideslope(2.0)
        >>> states.watervolume = 3.0
        >>> model.calc_waterdepth_v1()
        >>> factors.waterdepth
        waterdepth(0.395644)

        The third example shows that zero water volume results in zero water depth:

        >>> bottomwidth(3.0)
        >>> sideslope(2.0)
        >>> states.watervolume = 0.0
        >>> model.calc_waterdepth_v1()
        >>> factors.waterdepth
        waterdepth(0.0)

        The fourth example deals with a quasi-rectangular profile with nearly zero
        side slopes.  Method |Calc_WaterDepth_V1| handles side slopes smaller than
        1e-10 as zero to circumvent errors due to the limited precision of floating
        point numbers:

        >>> sideslope(1e-20)
        >>> states.watervolume = 1.0
        >>> model.calc_waterdepth_v1()
        >>> factors.waterdepth
        waterdepth(0.166667)
    """

    CONTROLPARAMETERS = (
        sw1d_control.Length,
        sw1d_control.BottomWidth,
        sw1d_control.SideSlope,
    )
    REQUIREDSEQUENCES = (sw1d_states.WaterVolume,)
    RESULTSEQUENCES = (sw1d_factors.WaterDepth,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        sta = model.sequences.states.fastaccess
        if sta.watervolume > 0.0:
            a: float = sta.watervolume / con.length
            w: float = con.bottomwidth
            s: float = con.sideslope
            if s < 1e-10:
                fac.waterdepth = a / w
            else:
                fac.waterdepth = ((4.0 * s * a + w**2) ** 0.5 - w) / (2.0 * s)
        else:
            fac.waterdepth = 0.0


class Calc_WaterDepth_V2(modeltools.Method):
    r"""Calculate the water depth based on the water level.

    Basic equation:
      :math:`WaterDepth = max(WaterLevel - BottomLevel, \ 0)`

    Examples:

        >>> from hydpy.models.sw1d import *
        >>> parameterstep()
        >>> bottomlevel(3.0)
        >>> factors.waterlevel = 5.0
        >>> model.calc_waterdepth_v2()
        >>> factors.waterdepth
        waterdepth(2.0)

        >>> factors.waterlevel = 2.0
        >>> model.calc_waterdepth_v2()
        >>> factors.waterdepth
        waterdepth(0.0)
    """

    CONTROLPARAMETERS = (sw1d_control.BottomLevel,)
    REQUIREDSEQUENCES = (sw1d_factors.WaterLevel,)
    RESULTSEQUENCES = (sw1d_factors.WaterDepth,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        fac.waterdepth = max(fac.waterlevel - con.bottomlevel, 0.0)


class Calc_WettedArea_V1(modeltools.Method):
    r"""Calculate the wetted area in a symmetric trapezoidal profile.

    Basic equation:
      :math:`WettedArea = WaterDepth \cdot (BottomWidth + SideSlope \cdot WaterDepth)`

    Examples:

        The first example deals with a rectangular profile:

        >>> from hydpy.models.sw1d import *
        >>> parameterstep()
        >>> factors.waterdepth = 3.0
        >>> bottomwidth(2.0)
        >>> sideslope(0.0)
        >>> model.calc_wettedarea_v1()
        >>> factors.wettedarea
        wettedarea(6.0)

        The second example deals with a triangular profile:

        >>> bottomwidth(0.0)
        >>> sideslope(2.0)
        >>> model.calc_wettedarea_v1()
        >>> factors.wettedarea
        wettedarea(18.0)

        The third example combines the two profiles defined above into a trapezoidal
        profile:

        >>> bottomwidth(2.0)
        >>> sideslope(2.0)
        >>> model.calc_wettedarea_v1()
        >>> factors.wettedarea
        wettedarea(24.0)
    """

    CONTROLPARAMETERS = (sw1d_control.BottomWidth, sw1d_control.SideSlope)
    REQUIREDSEQUENCES = (sw1d_factors.WaterDepth,)
    RESULTSEQUENCES = (sw1d_factors.WettedArea,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        fac.wettedarea = fac.waterdepth * (
            con.bottomwidth + con.sideslope * fac.waterdepth
        )


class Calc_WettedPerimeter_V1(modeltools.Method):
    r"""Calculate the wetted perimeter in a trapezoidal profile.

    Basic equation:
      :math:`WettedPerimeter =
      BottomWidth + 2 \cdot WaterDepth \cdot \sqrt{1 + SideSlope^2}`

    Examples:

        The first example deals with a rectangular profile:

        >>> from hydpy.models.sw1d import *
        >>> parameterstep()
        >>> factors.waterdepth = 3.0
        >>> bottomwidth(2.0)
        >>> sideslope(0.0)
        >>> model.calc_wettedperimeter_v1()
        >>> factors.wettedperimeter
        wettedperimeter(8.0)

        The second example deals with a triangular profile:

        >>> bottomwidth(0.0)
        >>> sideslope(2.0)
        >>> model.calc_wettedperimeter_v1()
        >>> factors.wettedperimeter
        wettedperimeter(13.416408)

        The third example combines the two profiles defined above into a trapezoidal
        profile:

        >>> bottomwidth(2.0)
        >>> sideslope(2.0)
        >>> model.calc_wettedperimeter_v1()
        >>> factors.wettedperimeter
        wettedperimeter(15.416408)
    """

    CONTROLPARAMETERS = (sw1d_control.BottomWidth, sw1d_control.SideSlope)
    REQUIREDSEQUENCES = (sw1d_factors.WaterDepth,)
    RESULTSEQUENCES = (sw1d_factors.WettedPerimeter,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        fac.wettedperimeter = con.bottomwidth + (
            2.0 * fac.waterdepth * (1.0 + con.sideslope**2.0) ** 0.5
        )


class Calc_DischargeUpstream_V1(modeltools.Method):
    """Sum the (partial) discharge of all upstream routing submodels following the
    |RoutingModel_V1| or |RoutingModel_V2| interface.

    Examples:

        If there is no upstream model, |DischargeUpstream| is zero:

        >>> from hydpy import prepare_model
        >>> c2 = prepare_model("sw1d_channel")
        >>> c2.parameters.control.nmbsegments(1)
        >>> with c2.add_storagemodel_v1("sw1d_storage", position=0, update=False):
        ...     pass
        >>> with c2.add_routingmodel_v2("sw1d_lias", position=1, update=False) as r2:
        ...     states.discharge = 5.0
        >>> r2.calc_dischargeupstream_v1()
        >>> r2.sequences.fluxes.dischargeupstream
        dischargeupstream(0.0)

        Otherwise, |Calc_DischargeUpstream_V1| totals the individual (partial)
        discharge values:

        >>> from hydpy import Element, Node
        >>> n012 = Node("n012", variable="LongQ")
        >>> e2 = Element("e2", inlets=n012)
        >>> e2.model = c2
        >>> e0, e1 = Element("e0", outlets=n012), Element("e1", outlets=n012)
        >>> for element, discharge in ((e0, 1.0), (e1, 3.0)):
        ...     c = prepare_model("sw1d_channel")
        ...     element.model = c
        ...     c.parameters.control.nmbsegments(1)
        ...     with c.add_storagemodel_v1("sw1d_storage", position=0, update=False):
        ...         pass
        ...     with c.add_routingmodel_v2("sw1d_lias", position=1, update=False):
        ...         states.discharge = discharge
        >>> network = c2.couple_models(nodes=(n012,), elements=(e0, e1, e2))
        >>> r2.calc_dischargeupstream_v1()
        >>> r2.sequences.fluxes.dischargeupstream
        dischargeupstream(4.0)

        .. testsetup::

            >>> Node.clear_all()
            >>> Element.clear_all()
    """

    SUBMODELINTERFACES = (
        channelinterfaces.RoutingModel_V1,
        channelinterfaces.RoutingModel_V2,
    )
    REQUIREDSEQUENCES = (sw1d_states.Discharge,)
    RESULTSEQUENCES = (sw1d_fluxes.DischargeUpstream,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess

        flu.dischargeupstream = 0.0
        for i in range(model.routingmodelsupstream.number):
            if model.routingmodelsupstream.typeids[i] in (1, 2):
                flu.dischargeupstream += cast(
                    Union[
                        channelinterfaces.RoutingModel_V1,
                        channelinterfaces.RoutingModel_V2,
                    ],
                    model.routingmodelsupstream.submodels[i],
                ).get_partialdischargeupstream(sta.discharge)


class Calc_DischargeDownstream_V1(modeltools.Method):
    """Sum the (partial) discharge of all downstream routing submodels following the
    |RoutingModel_V2| or |RoutingModel_V3| interface.

    Examples:

        If there is no downstream model, |DischargeDownstream| is zero:

        >>> from hydpy import prepare_model
        >>> c0 = prepare_model("sw1d_channel")
        >>> c0.parameters.control.nmbsegments(1)
        >>> with c0.add_routingmodel_v2("sw1d_lias", position=0, update=False) as r0:
        ...     states.discharge = 5.0
        >>> with c0.add_storagemodel_v1("sw1d_storage", position=0, update=False):
        ...     pass
        >>> r0.calc_dischargedownstream_v1()
        >>> r0.sequences.fluxes.dischargedownstream
        dischargedownstream(0.0)

        Otherwise, |Calc_DischargeDownstream_V1| totals the individual (partial)
        discharge values:

        >>> from hydpy import Element, Node
        >>> n012 = Node("n012", variable="LongQ")
        >>> e0 = Element("e0", outlets=n012)
        >>> e0.model = c0
        >>> e1, e2 = Element("e1", inlets=n012), Element("e2", inlets=n012)
        >>> for element, discharge in ((e1, 1.0), (e2, 3.0)):
        ...     c = prepare_model("sw1d_channel")
        ...     element.model = c
        ...     c.parameters.control.nmbsegments(1)
        ...     with c.add_routingmodel_v2("sw1d_lias", position=0, update=False):
        ...         states.discharge = discharge
        ...     with c.add_storagemodel_v1("sw1d_storage", position=0, update=False):
        ...         pass
        >>> network = c0.couple_models(nodes=(n012,), elements=(e0, e1, e2))
        >>> r0.calc_dischargedownstream_v1()
        >>> r0.sequences.fluxes.dischargedownstream
        dischargedownstream(4.0)

        .. testsetup::

            >>> Node.clear_all()
            >>> Element.clear_all()
    """

    SUBMODELINTERFACES = (
        channelinterfaces.RoutingModel_V2,
        channelinterfaces.RoutingModel_V3,
    )
    REQUIREDSEQUENCES = (sw1d_states.Discharge,)
    RESULTSEQUENCES = (sw1d_fluxes.DischargeDownstream,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess

        flu.dischargedownstream = 0.0
        for i in range(model.routingmodelsdownstream.number):
            if model.routingmodelsdownstream.typeids[i] in (2, 3):
                flu.dischargedownstream += cast(
                    Union[
                        channelinterfaces.RoutingModel_V2,
                        channelinterfaces.RoutingModel_V3,
                    ],
                    model.routingmodelsdownstream.submodels[i],
                ).get_partialdischargedownstream(sta.discharge)


class Calc_Discharge_V1(modeltools.Method):
    r"""Calculate the discharge according to :cite:t:`ref-Bates2010` and
    :cite:t:`ref-Almeida2012`.

    Basic equation :cite:p:`ref-Almeida2012`:
      .. math::
        Q_{i-1/2}^{n+1} = \frac{\left[ (1-\theta) \cdot Q_{i-1/2}^n +
        \frac{\theta}{2} \cdot \left( Q_{i-3/2}^n + Q_{i+1/2}^n\right) \right] +
        g \cdot A_f \cdot \Delta t^n \cdot (y_{i-1}^n - y_i^n) / \Delta x}
        {1 + g \cdot \Delta t \cdot k_{st}^{-2} \cdot \left| Q_{i-1/2}^n \right|
        \cdot {P_f^n}^{\frac{4}{3}} \cdot {A_f^n}^{-\frac{7}{3}}}
        \\ \\
        Q = Discharge \\
        \theta = DiffusionFactor \\
        g = GravitationalAcceleration \\
        A_f = WettedArea \\
        \Delta t = TimeStep \\
        \Delta x = Length \\
        y = WaterLevel \\
        k_{st} = StricklerCoefficient \\
        P_f = WettedPerimeter

    Examples:

        The following channel configuration corresponds to a rectangular profile and
        a water surface slope of one meter per kilometre:

        >>> from hydpy.models.sw1d import *
        >>> parameterstep()
        >>> diffusionfactor(0.2)
        >>> stricklercoefficient(50.0)
        >>> derived.lengthmean(2.0)
        >>> factors.timestep = 100.0
        >>> factors.wettedarea = 6.0
        >>> factors.wettedperimeter = 8.0
        >>> factors.waterlevelupstream = 5.0
        >>> factors.waterleveldownstream = 3.0

        According to the Manning-Strickler equation, this configuration corresponds to
        a discharge of about 8 m³/s:

        >>> dh = factors.waterlevelupstream - factors.waterleveldownstream
        >>> i = dh/ (1000.0 * derived.lengthmean)
        >>> r = factors.wettedarea / factors.wettedperimeter
        >>> v = stricklercoefficient * r**(2.0/3.0) * i**0.5
        >>> q = factors.wettedarea * v
        >>> from hydpy import round_
        >>> round_(q)
        7.831208

        If we use this value as the "old" discharge, relevant for the local inertial
        term, |Calc_Discharge_V1| calculates the same value as the "new" discharge,
        demonstrating its agreement with Manning-Stricker for stationary conditions:

        >>> fluxes.dischargeupstream = q
        >>> fluxes.dischargedownstream = q
        >>> states.discharge = q
        >>> model.calc_discharge_v1()
        >>> states.discharge
        discharge(7.831208)

        Reversing the surface water slope and the "old" discharge reverses the "new"
        discharge:

        >>> factors.waterlevelupstream = -5.0
        >>> factors.waterleveldownstream = -3.0
        >>> fluxes.dischargeupstream = -q
        >>> fluxes.dischargedownstream = -q
        >>> states.discharge = -q
        >>> model.calc_discharge_v1()
        >>> states.discharge
        discharge(-7.831208)

        With zero initial discharge, the estimated discharge becomes smaller:

        >>> factors.waterlevelupstream = 5.0
        >>> factors.waterleveldownstream = 3.0
        >>> fluxes.dischargeupstream = 0.0
        >>> fluxes.dischargedownstream = 0.0
        >>> states.discharge = 0.0
        >>> model.calc_discharge_v1()
        >>> states.discharge
        discharge(5.886)

        For differences between the initial discharge at the upstream, the actual, and
        the downstream position, the extension introduced by :cite:t:`ref-Almeida2012`
        to increase computational stability via numerical diffusion becomes relevant:

        >>> states.discharge = q
        >>> model.calc_discharge_v1()
        >>> states.discharge
        discharge(6.937035)

        |Calc_Discharge_V1| sets the discharge directly to zero for zero wetted
        cross-section areas to prevent zero division errors:

        >>> factors.wettedarea = 0.0
        >>> model.calc_discharge_v1()
        >>> states.discharge
        discharge(0.0)
    """

    CONTROLPARAMETERS = (
        sw1d_control.DiffusionFactor,
        sw1d_control.StricklerCoefficient,
    )
    DERIVEDPARAMETERS = (sw1d_derived.LengthMean,)
    FIXEDPARAMETERS = (sw1d_fixed.GravitationalAcceleration,)
    REQUIREDSEQUENCES = (
        sw1d_factors.TimeStep,
        sw1d_factors.WettedArea,
        sw1d_factors.WettedPerimeter,
        sw1d_factors.WaterLevelUpstream,
        sw1d_factors.WaterLevelDownstream,
        sw1d_fluxes.DischargeUpstream,
        sw1d_fluxes.DischargeDownstream,
    )
    UPDATEDSEQUENCES = (sw1d_states.Discharge,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fix = model.parameters.fixed.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess

        if fac.wettedarea > 0.0:
            w: float = con.diffusionfactor  # * fac.timestep / der.seconds
            nominator1: float = (1.0 - w) * sta.discharge + w / 2.0 * (
                flu.dischargeupstream + flu.dischargedownstream
            )
            nominator2: float = (
                fix.gravitationalacceleration
                * fac.wettedarea
                * fac.timestep
                * (fac.waterlevelupstream - fac.waterleveldownstream)
                / (1000.0 * der.lengthmean)
            )
            denominator: float = 1.0 + (
                fix.gravitationalacceleration
                * fac.timestep
                / con.stricklercoefficient**2.0
                * modelutils.fabs(sta.discharge)
                * fac.wettedperimeter ** (4.0 / 3.0)
                / fac.wettedarea ** (7.0 / 3.0)
            )
            sta.discharge = (nominator1 + nominator2) / denominator
        else:
            sta.discharge = 0.0


class Calc_Discharge_V2(modeltools.Method):
    r"""Calculate the free weir flow after Poleni.

    Basic equation:
      .. math::
        Q = w \cdot 2 / 3 \cdot c \cdot  \sqrt{2 \cdot g} \cdot h^{3/2}
        \\ \\
        w = CrestWidth \\
        c = FlowCoefficient \\
        g = GravitationalAcceleration \\
        h = max(WaterLevel - CrestHeight, \ 0)

    Examples:

        >>> from hydpy.models.sw1d import *
        >>> parameterstep()
        >>> crestwidth(10.0)
        >>> crestheight(5.0)
        >>> flowcoefficient(0.6)
        >>> factors.waterlevel = 7.0
        >>> model.calc_discharge_v2()
        >>> states.discharge
        discharge(50.113471)

        >>> factors.waterlevel = 4.0
        >>> model.calc_discharge_v2()
        >>> states.discharge
        discharge(0.0)

        >>> factors.waterlevel = 5.0
        >>> model.calc_discharge_v2()
        >>> states.discharge
        discharge(0.0)
    """

    CONTROLPARAMETERS = (
        sw1d_control.CrestHeight,
        sw1d_control.CrestWidth,
        sw1d_control.FlowCoefficient,
    )
    FIXEDPARAMETERS = (sw1d_fixed.GravitationalAcceleration,)
    REQUIREDSEQUENCES = (sw1d_factors.WaterLevel,)
    UPDATEDSEQUENCES = (sw1d_states.Discharge,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fix = model.parameters.fixed.fastaccess
        fac = model.sequences.factors.fastaccess
        sta = model.sequences.states.fastaccess
        h: float = fac.waterlevel - con.crestheight
        if h > 0.0:
            w: float = con.crestwidth
            c: float = con.flowcoefficient
            g: float = fix.gravitationalacceleration
            sta.discharge = w * 2.0 / 3.0 * c * (2.0 * g) ** 0.5 * h ** (3.0 / 2.0)
        else:
            sta.discharge = 0.0


class Calc_Discharge_V3(modeltools.Method):
    r"""Calculate the flow under a gate.

    Basic equation:
      .. math::
        Q = d \cdot w \cdot c \cdot \big( min (h, \ l) - b \big)
        \cdot \sqrt{2 \cdot g  \cdot (l_u - l_d)}
        \\ \\
        d = f_{filter\_norm}(l_u, \ l_d, \ DampingRadius) \\
        w = GateWidth \\
        c = FlowCoefficient \\
        h = GateHeight \\
        l = WaterLevel \\
        l_u = WaterLevelUpstream \\
        l_d = WaterLevelDownstream\\
        b = BottomLevel \\
        g = GravitationalAcceleration

    Examples:

        The first two examples deal with flow under a submerged gate:

        >>> from hydpy.models.sw1d import *
        >>> parameterstep()
        >>> bottomlevel(4.0)
        >>> gateheight(6.0)
        >>> gatewidth(3.0)
        >>> flowcoefficient(0.6)
        >>> dampingradius(0.0)
        >>> factors.waterlevel = 8.0
        >>> factors.waterlevelupstream = 9.0
        >>> factors.waterleveldownstream = 7.0
        >>> model.calc_discharge_v3()
        >>> states.discharge
        discharge(22.551062)
        >>> factors.waterlevelupstream = 7.0
        >>> factors.waterleveldownstream = 9.0
        >>> model.calc_discharge_v3()
        >>> states.discharge
        discharge(-22.551062)

        The next two examples deal with a gate submerge "on one side":

        >>> gateheight(8.0)
        >>> factors.waterlevelupstream = 9.0
        >>> factors.waterleveldownstream = 7.0
        >>> model.calc_discharge_v3()
        >>> states.discharge
        discharge(45.102124)
        >>> factors.waterlevelupstream = 7.0
        >>> factors.waterleveldownstream = 9.0
        >>> model.calc_discharge_v3()
        >>> states.discharge
        discharge(-45.102124)

        For non-submerged gates, the water level becomes the effective gate opening:

        >>> gateheight(10.0)
        >>> factors.waterlevelupstream = 9.0
        >>> factors.waterleveldownstream = 7.0
        >>> model.calc_discharge_v3()
        >>> states.discharge
        discharge(45.102124)
        >>> factors.waterlevelupstream = 7.0
        >>> factors.waterleveldownstream = 9.0
        >>> model.calc_discharge_v3()
        >>> states.discharge
        discharge(-45.102124)

        Negative effective gate openings result in zero discharge values:

        >>> gateheight(0.0)
        >>> factors.waterlevelupstream = 9.0
        >>> factors.waterleveldownstream = 7.0
        >>> model.calc_discharge_v3()
        >>> states.discharge
        discharge(0.0)
        >>> factors.waterlevelupstream = 7.0
        >>> factors.waterleveldownstream = 9.0
        >>> model.calc_discharge_v3()
        >>> states.discharge
        discharge(0.0)

        According to the given base equation, the change in flow rate with respect to
        changes in the water level gradient is highest for little water level
        gradients.  For nearly zero gradients, these changes are so extreme that
        numerically solving this ordinary differential equation in combination with the
        ones of other routing models may introduce considerable artificial
        oscillations.

        In the following example, a water level gradient of 1 mm corresponds to a
        discharge of only 0.3 m³/s, but also to a discharge increase of nearly
        1600 m³/s per meter rise of the upstream water level:

        >>> gateheight(10.0)
        >>> factors.waterlevelupstream = 8.0001
        >>> factors.waterleveldownstream = 8.0
        >>> model.calc_discharge_v3()
        >>> states.discharge
        discharge(0.31892)
        >>> from hydpy import NumericalDifferentiator, round_
        >>> numdiff = NumericalDifferentiator(
        ...     xsequence=factors.waterlevelupstream,
        ...     ysequences=[states.discharge],
        ...     methods=[model.calc_discharge_v3])
        >>> numdiff()
        d_discharge/d_waterlevelupstream: 1594.591021

        Principally, one could reduce the resulting oscillations by decreasing the
        internal calculation step size.  However, this alone sometimes results in
        unacceptable increases in computation time.  Hence, we suggest using the
        |DampingRadius| parameter to prevent such oscillations.  Setting it, for
        example, to 1 mm reduces the change in discharge to 40 m³/s per meter:

        >>> dampingradius(0.001)
        >>> numdiff()
        d_discharge/d_waterlevelupstream: 39.685825

        Be careful not to set larger values than necessary, as this stabilisation trick
        does not only reduce the discharge derivative but also the discharge itself:

        >>> model.calc_discharge_v3()
        >>> states.discharge
        discharge(0.001591)

        All of the above examples deal with fixed gate openings.  However, in reality,
        gates are often controlled, so their opening degree depends on other
        properties.  Therefore, parameter |GateHeight| alternatively accepts a callback
        function for adjusting its values based on the current model state.  One can,
        for example, define a "sluice" function that prevents any flow for reversed
        water level gradients:

        >>> def sluice(model) -> None:
        ...     con = model.parameters.control.fastaccess
        ...     fac = model.sequences.factors.fastaccess
        ...     if fac.waterlevelupstream < fac.waterleveldownstream:
        ...         con.gateheight = 4.0
        ...     else:
        ...         con.gateheight = 10.0
        >>> ();gateheight(callback=sluice);()  # doctest: +ELLIPSIS
        (...)

        Method |Calc_Discharge_V3| applies this callback function before performing its
        further calculations.  Hence, the following results agree with the
        "non-submerged gates" example for a positive water level gradient and the
        "negative effective gate opening" example for a negative one:

        >>> factors.waterlevelupstream = 9.0
        >>> factors.waterleveldownstream = 7.0
        >>> model.calc_discharge_v3()
        >>> states.discharge
        discharge(45.102124)
        >>> factors.waterlevelupstream = 7.0
        >>> factors.waterleveldownstream = 9.0
        >>> model.calc_discharge_v3()
        >>> states.discharge
        discharge(0.0)
    """

    CONTROLPARAMETERS = (
        sw1d_control.BottomLevel,
        sw1d_control.GateWidth,
        sw1d_control.GateHeight,
        sw1d_control.FlowCoefficient,
        sw1d_control.DampingRadius,
    )
    FIXEDPARAMETERS = (sw1d_fixed.GravitationalAcceleration,)
    REQUIREDSEQUENCES = (
        sw1d_factors.WaterLevel,
        sw1d_factors.WaterLevelUpstream,
        sw1d_factors.WaterLevelDownstream,
    )
    UPDATEDSEQUENCES = (sw1d_states.Discharge,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fix = model.parameters.fixed.fastaccess
        fac = model.sequences.factors.fastaccess
        sta = model.sequences.states.fastaccess

        con.gateheight_callback(model)
        h: float = min(con.gateheight, fac.waterlevel) - con.bottomlevel
        if h > 0.0:
            w: float = con.gatewidth
            c: float = con.flowcoefficient
            g: float = fix.gravitationalacceleration
            lu: float = fac.waterlevelupstream
            ld: float = fac.waterleveldownstream
            if ld < lu:
                sta.discharge = w * c * h * (2.0 * g * (lu - ld)) ** 0.5
            else:
                sta.discharge = -w * c * h * (2.0 * g * (ld - lu)) ** 0.5
            sta.discharge *= 1.0 - smoothutils.filter_norm(lu, ld, con.dampingradius)
        else:
            sta.discharge = 0.0


class Update_Discharge_V1(modeltools.Method):
    r"""Reduce the already calculated discharge due to limited water availability in
    one of the adjacent channel segments.

    Basic equations:
      .. math::
        Q_{new} = \begin{cases}
        max(Q_{old}, \ 1000 \cdot max(V_u, \ 0) / \Delta  &|\  Q_{old} > 0 \\
        min(Q_{old}, \ -1000 \cdot max(V_d, \ 0) / \Delta  &|\  Q_{old} < 0
        \end{cases} \\
        \\ \\
        Q = Discharge \\
        V_u = WaterVolumeUpstream \\
        V_d = WaterVolumeDownstream \\
        \Delta = TimeStep

    Examples:

        >>> from hydpy.models.sw1d import *
        >>> parameterstep()
        >>> factors.timestep = 100.0
        >>> factors.watervolumeupstream = 0.1
        >>> factors.watervolumedownstream = 0.2

        |Update_Discharge_V1| must consider the upstream segment's water volume for
        positive discharge values:

        >>> states.discharge = 1.0
        >>> model.update_discharge_v1()
        >>> states.discharge
        discharge(1.0)
        >>> states.discharge = 2.0
        >>> model.update_discharge_v1()
        >>> states.discharge
        discharge(1.0)

        Instead, it must consider the downstream segment's water volume for negative
        discharge values:

        >>> states.discharge = -2.0
        >>> model.update_discharge_v1()
        >>> states.discharge
        discharge(-2.0)
        >>> states.discharge = -3.0
        >>> model.update_discharge_v1()
        >>> states.discharge
        discharge(-2.0)
    """

    REQUIREDSEQUENCES = (
        sw1d_factors.TimeStep,
        sw1d_factors.WaterVolumeUpstream,
        sw1d_factors.WaterVolumeDownstream,
    )
    UPDATEDSEQUENCES = (sw1d_states.Discharge,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        fac = model.sequences.factors.fastaccess
        sta = model.sequences.states.fastaccess
        if sta.discharge > 0.0:
            q_max: float = 1000.0 * max(fac.watervolumeupstream, 0.0) / fac.timestep
            sta.discharge = min(sta.discharge, q_max)
        elif sta.discharge < 0.0:
            q_min: float = -1000.0 * max(fac.watervolumedownstream, 0.0) / fac.timestep
            sta.discharge = max(sta.discharge, q_min)


class Update_Discharge_V2(modeltools.Method):
    r"""Suppress upstream flow if the downstream water level exceeds the upstream one.

    Basic equations:
      .. math::
        Q_{new} = \begin{cases}
        Q_{old} &|\  0 \leq Q_{old} \ \lor  \ h_d \leq h_u  \ \lor \ h_u \leq t_1 \\
        Q_{old} \cdot \left( 1 - \frac{h_u - t_1}{t_2 - t_1} \right)
         &|\  Q_{old} < 0 \ \land  \ h_u < h_d \ \ \land \ t_1 < h_u < t_2 \\
        0 &|\  Q_{old} < 0 \ \land  \ h_u < h_d \ \ \land \ t_2 \leq h_u
        \end{cases} \\
        \\
        Q = Discharge \\
        h_u = WaterLevelUpstream \\
        h_d = WaterLevelDownstream \\
        t_1 = TargetWaterLevel1 \\
        t_2 = TargetWaterLevel2

    Examples:

        We use the same unmodified discharge of -1 m³/s in most examples:

        >>> from hydpy.models.sw1d import *
        >>> parameterstep()
        >>> states.discharge = -1.0

        At first, we set |TargetWaterLevel1| and |TargetWaterLevel2| to the same value
        of 2 m:

        >>> targetwaterlevel1(2.0)
        >>> targetwaterlevel2(2.0)

        We prepare a |UnitTest| object demonstrating |Update_Discharge_V2| for multiple
        upstream and downstream water levels:

        >>> from hydpy import UnitTest
        >>> test = UnitTest(
        ...     model, model.update_discharge_v2,
        ...     last_example=7,
        ...     parseqs=(factors.waterlevelupstream, factors.waterleveldownstream,
        ...              states.discharge))

        |Update_Discharge_V2| does never modify the original discharge value as long as
        the downstream water level does not exceed the upstream one:

        >>> test.nexts.waterlevelupstream = 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0
        >>> test.nexts.waterleveldownstream = 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0
        >>> test()
        | ex. | waterlevelupstream | waterleveldownstream | discharge |
        ---------------------------------------------------------------
        |   1 |                1.0 |                  1.0 |      -1.0 |
        |   2 |                2.0 |                  2.0 |      -1.0 |
        |   3 |                3.0 |                  3.0 |      -1.0 |
        |   4 |                4.0 |                  4.0 |      -1.0 |
        |   5 |                5.0 |                  5.0 |      -1.0 |
        |   6 |                6.0 |                  6.0 |      -1.0 |
        |   7 |                7.0 |                  7.0 |      -1.0 |

        After raising the downstream water level, |Update_Discharge_V2| sets the
        upstream flow to zero as soon as the upper water level exceeds the given lower
        and upper threshold values:

        >>> test.nexts.waterleveldownstream = 7 * [8.0]
        >>> test()
        | ex. | waterlevelupstream | waterleveldownstream | discharge |
        ---------------------------------------------------------------
        |   1 |                1.0 |                  8.0 |      -1.0 |
        |   2 |                2.0 |                  8.0 |      -1.0 |
        |   3 |                3.0 |                  8.0 |       0.0 |
        |   4 |                4.0 |                  8.0 |       0.0 |
        |   5 |                5.0 |                  8.0 |       0.0 |
        |   6 |                6.0 |                  8.0 |       0.0 |
        |   7 |                7.0 |                  8.0 |       0.0 |

        Setting |TargetWaterLevel1| and |TargetWaterLevel2| to the same value might
        result in situations with frequent "on-off switching" with eventually adverse
        effects on computational efficiency or simulation accuracy.  After setting
        |TargetWaterLevel2| to 5 m, we see that |Update_Discharge_V2| reduces the
        original upstream flow more smoothly via linear interpolation:

        >>> targetwaterlevel2(6.0)
        >>> test()
        | ex. | waterlevelupstream | waterleveldownstream | discharge |
        ---------------------------------------------------------------
        |   1 |                1.0 |                  8.0 |      -1.0 |
        |   2 |                2.0 |                  8.0 |      -1.0 |
        |   3 |                3.0 |                  8.0 |     -0.75 |
        |   4 |                4.0 |                  8.0 |      -0.5 |
        |   5 |                5.0 |                  8.0 |     -0.25 |
        |   6 |                6.0 |                  8.0 |       0.0 |
        |   7 |                7.0 |                  8.0 |       0.0 |

        The discussed reductions do not apply to downstream flows:

        >>> test.inits.discharge = 1.0
        >>> test()
        | ex. | waterlevelupstream | waterleveldownstream | discharge |
        ---------------------------------------------------------------
        |   1 |                1.0 |                  8.0 |       1.0 |
        |   2 |                2.0 |                  8.0 |       1.0 |
        |   3 |                3.0 |                  8.0 |       1.0 |
        |   4 |                4.0 |                  8.0 |       1.0 |
        |   5 |                5.0 |                  8.0 |       1.0 |
        |   6 |                6.0 |                  8.0 |       1.0 |
        |   7 |                7.0 |                  8.0 |       1.0 |
    """

    CONTROLPARAMETERS = (sw1d_control.TargetWaterLevel1, sw1d_control.TargetWaterLevel2)
    REQUIREDSEQUENCES = (
        sw1d_factors.WaterLevelUpstream,
        sw1d_factors.WaterLevelDownstream,
    )
    UPDATEDSEQUENCES = (sw1d_states.Discharge,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        sta = model.sequences.states.fastaccess

        if sta.discharge < 0.0:
            hu: float = fac.waterlevelupstream
            hd: float = fac.waterleveldownstream
            t1: float = con.targetwaterlevel1
            t2: float = con.targetwaterlevel2
            if t1 < hu < hd:
                if hu < t2:
                    sta.discharge *= 1 - (hu - t1) / (t2 - t1)
                else:
                    sta.discharge = 0.0


class Reset_DischargeVolume_V1(modeltools.Method):
    """Reset the discharge volume to zero (at the beginning of an external simulation
    step).

    Example:

        >>> from hydpy.models.sw1d import *
        >>> parameterstep()
        >>> fluxes.dischargevolume = 1.0
        >>> model.reset_dischargevolume_v1()
        >>> fluxes.dischargevolume
        dischargevolume(0.0)
    """

    RESULTSEQUENCES = (sw1d_fluxes.DischargeVolume,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.dischargevolume = 0.0


class Update_DischargeVolume_V1(modeltools.Method):
    r"""Update the total discharge volume of the current external simulation step.

    Basic equation:
      :math:`DischargeVolume_{new} = DischargeVolume_{old} + TimeStep \cdot Discharge`

    Example:

        >>> from hydpy.models.sw1d import *
        >>> parameterstep()
        >>> fluxes.dischargevolume = 6.0
        >>> factors.timestep = 60.0
        >>> states.discharge = 0.2
        >>> model.update_dischargevolume_v1()
        >>> fluxes.dischargevolume
        dischargevolume(18.0)
    """

    REQUIREDSEQUENCES = (sw1d_factors.TimeStep, sw1d_states.Discharge)
    UPDATEDSEQUENCES = (sw1d_fluxes.DischargeVolume,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        flu.dischargevolume += fac.timestep * sta.discharge


class Calc_DischargeVolume_V1(modeltools.Method):
    r"""Calculate the total discharge volume of a complete external simulation step at
    once.

    Basic equation:
      :math:`DischargeVolume = Seconds \cdot Inflow`

    Example:

        >>> from hydpy.models.sw1d import *
        >>> parameterstep()
        >>> derived.seconds(60.0)
        >>> fluxes.inflow = 2.0
        >>> model.calc_dischargevolume_v1()
        >>> fluxes.dischargevolume
        dischargevolume(120.0)
    """

    DERIVEDPARAMETERS = (sw1d_derived.Seconds,)
    REQUIREDSEQUENCES = (sw1d_fluxes.Inflow,)
    UPDATEDSEQUENCES = (sw1d_fluxes.DischargeVolume,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.dischargevolume = der.seconds * flu.inflow


class Calc_DischargeVolume_V2(modeltools.Method):
    r"""Calculate the total discharge volume of a complete external simulation step at
    once.

    Basic equation:
      :math:`DischargeVolume = Seconds \cdot Outflow`

    Example:

        >>> from hydpy.models.sw1d import *
        >>> parameterstep()
        >>> derived.seconds(60.0)
        >>> fluxes.outflow = 2.0
        >>> model.calc_dischargevolume_v2()
        >>> fluxes.dischargevolume
        dischargevolume(120.0)
    """

    DERIVEDPARAMETERS = (sw1d_derived.Seconds,)
    REQUIREDSEQUENCES = (sw1d_fluxes.Outflow,)
    UPDATEDSEQUENCES = (sw1d_fluxes.DischargeVolume,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.dischargevolume = der.seconds * flu.outflow


class Calc_Discharges_V1(modeltools.Method):
    """Let a network model order all routing submodels following the |RoutingModel_V1|,
    |RoutingModel_V2|, or |RoutingModel_V3| interface to determine their individual
    discharge values.

    Example:

        >>> from hydpy.models.sw1d_channel import *
        >>> parameterstep()
        >>> nmbsegments(2)
        >>> with model.add_routingmodel_v2("sw1d_lias", position=1, update=False) as r:
        ...     diffusionfactor(0.2)
        ...     stricklercoefficient(50.0)
        ...     derived.lengthmean(2.0)
        ...     factors.timestep = 100.0
        ...     factors.wettedarea = 6.0
        ...     factors.wettedperimeter = 8.0
        ...     factors.waterlevelupstream = 5.0
        ...     factors.waterleveldownstream = 3.0
        ...     states.discharge = 7.831208
        ...     fluxes.dischargeupstream = 7.831208
        ...     fluxes.dischargedownstream = 7.831208
        >>> model.calc_discharges_v1()
        >>> r.sequences.states.discharge
        discharge(7.831208)
    """

    SUBMODELINTERFACES = (
        channelinterfaces.RoutingModel_V1,
        channelinterfaces.RoutingModel_V2,
        channelinterfaces.RoutingModel_V3,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        for i in range(model.routingmodels.number):
            if model.routingmodels.typeids[i] in (1, 2, 3):
                cast(
                    Union[
                        channelinterfaces.RoutingModel_V1,
                        channelinterfaces.RoutingModel_V2,
                        channelinterfaces.RoutingModel_V3,
                    ],
                    model.routingmodels.submodels[i],
                ).determine_discharge()


class Calc_Discharges_V2(modeltools.Method):
    """Query the discharge volume of the complete external simulation step from all
    submodels following the |RoutingModel_V1|, |RoutingModel_V2|, or |RoutingModel_V3|
    interface and calculate the corresponding average discharges.

    Basic equation:
      :math:`Discharges_i = DischargeVolume / Seconds`

    Examples:

        >>> from hydpy.models.sw1d_channel import *
        >>> parameterstep()
        >>> nmbsegments(2)
        >>> derived.seconds(60.0)
        >>> with model.add_routingmodel_v2("sw1d_lias", position=1, update=False):
        ...     fluxes.dischargevolume = 120.0
        >>> model.calc_discharges_v2()
        >>> fluxes.discharges
        discharges(0.0, 2.0, 0.0)
    """

    SUBMODELINTERFACES = (
        channelinterfaces.RoutingModel_V1,
        channelinterfaces.RoutingModel_V2,
        channelinterfaces.RoutingModel_V3,
    )
    DERIVEDPARAMETERS = (sw1d_derived.Seconds,)
    RESULTSEQUENCES = (sw1d_fluxes.Discharges,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess

        for i in range(model.routingmodels.number):
            if model.routingmodels.typeids[i] in (1, 2, 3):
                flu.discharges[i] = (
                    cast(
                        Union[
                            channelinterfaces.RoutingModel_V1,
                            channelinterfaces.RoutingModel_V2,
                            channelinterfaces.RoutingModel_V3,
                        ],
                        model.routingmodels.submodels[i],
                    ).get_dischargevolume()
                    / der.seconds
                )
            else:
                flu.discharges[i] = 0.0


class Calc_NetInflow_V1(modeltools.Method):
    """Calculate the net flow into a channel segment.

    Examples:

        Without adjacent routing models, net inflow equals lateral inflow:

        >>> from hydpy import Element, Node, prepare_model
        >>> c = prepare_model("sw1d_channel")
        >>> c.parameters.control.nmbsegments(1)
        >>> with c.add_storagemodel_v1("sw1d_storage", position=0, update=False) as s:
        ...     factors.timestep = 100.0
        ...     fluxes.lateralflow = 1.0
        >>> s.calc_netinflow_v1()
        >>> s.sequences.fluxes.netinflow
        netinflow(0.1)

        With adjacent routing models, |Calc_NetInflow_V1| adds the discharge from the
        upper one and subtracts the discharge from the lower one:

        >>> n01, n12 = Node("n01", variable="LongQ"), Node("n12", variable="LongQ")
        >>> e1 = Element("e1", inlets=n01, outlets=n12)
        >>> e1.model = c
        >>> e0a, e0b = Element("e0a", outlets=n01), Element("e0b", outlets=n01)
        >>> e2a, e2b = Element("e2a", inlets=n12), Element("e2b", inlets=n12)
        >>> for element, position, discharge in ((e0a, 1, 1.0), (e0b, 1, 2.0),
        ...                                      (e2a, 0, 2.0), (e2b, 0, 3.0)):
        ...     c = prepare_model("sw1d_channel")
        ...     element.model = c
        ...     c.parameters.control.nmbsegments(1)
        ...     with c.add_routingmodel_v2(
        ...             "sw1d_lias", position=position, update=False):
        ...         states.discharge = discharge
        ...     with c.add_storagemodel_v1("sw1d_storage", position=0, update=False):
        ...         pass
        >>> network = c.couple_models(
        ...     nodes=(n01, n12), elements=(e0a, e0b, e1, e2a, e2b))
        >>> s.calc_netinflow_v1()
        >>> s.sequences.fluxes.netinflow
        netinflow(-0.1)

        .. testsetup::

            >>> Node.clear_all()
            >>> Element.clear_all()
    """

    SUBMODELINTERFACES = (
        channelinterfaces.RoutingModel_V1,
        channelinterfaces.RoutingModel_V2,
        channelinterfaces.StorageModel_V1,
    )
    REQUIREDSEQUENCES = (sw1d_factors.TimeStep, sw1d_fluxes.LateralFlow)
    RESULTSEQUENCES = (sw1d_fluxes.NetInflow,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.netinflow = flu.lateralflow
        for i in range(model.routingmodelsupstream.number):
            if model.routingmodelsupstream.typeids[i] in (1, 2):
                flu.netinflow += cast(
                    Union[
                        channelinterfaces.RoutingModel_V1,
                        channelinterfaces.RoutingModel_V2,
                    ],
                    model.routingmodelsupstream.submodels[i],
                ).get_discharge()
        for i in range(model.routingmodelsdownstream.number):
            if model.routingmodelsdownstream.typeids[i] in (2, 3):
                flu.netinflow -= cast(
                    Union[
                        channelinterfaces.RoutingModel_V2,
                        channelinterfaces.RoutingModel_V3,
                    ],
                    model.routingmodelsdownstream.submodels[i],
                ).get_discharge()
        flu.netinflow *= fac.timestep / 1e3


class Update_WaterVolume_V1(modeltools.Method):
    """Update the current water content of a channel segment.

    Example:

        >>> from hydpy.models.sw1d import *
        >>> parameterstep()
        >>> states.watervolume = 2.0
        >>> fluxes.netinflow = 1.0
        >>> model.update_watervolume_v1()
        >>> states.watervolume
        watervolume(3.0)
    """

    REQUIREDSEQUENCES = (sw1d_fluxes.NetInflow,)
    UPDATEDSEQUENCES = (sw1d_states.WaterVolume,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        sta.watervolume += flu.netinflow


class Update_Storages_V1(modeltools.Method):
    """Let a network model order all storage submodels to update their storage contents
    and their dependent factors.

    Example:

        >>> from hydpy.models.sw1d_channel import *
        >>> parameterstep()
        >>> nmbsegments(1)
        >>> with model.add_routingmodel_v2("sw1d_lias", position=0, update=False):
        ...     states.discharge = 50.0
        >>> with model.add_storagemodel_v1("sw1d_storage", position=0, update=False):
        ...     length(2.0)
        ...     bottomwidth(3.0)
        ...     sideslope(0.0)
        ...     bottomlevel(10.0)
        ...     states.watervolume = 2.0
        ...     factors.timestep = 100.0
        ...     fluxes.lateralflow = 1.0
        >>> with model.add_routingmodel_v2("sw1d_lias", position=1, update=False):
        ...     states.discharge = 60.0
        >>> model.update_storages()
        >>> model.storagemodels[0].sequences.states.watervolume
        watervolume(1.1)
    """

    SUBMODELINTERFACES = (channelinterfaces.StorageModel_V1,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        for i in range(model.storagemodels.number):
            if model.storagemodels.typeids[i] == 1:
                cast(
                    channelinterfaces.StorageModel_V1, model.storagemodels.submodels[i]
                ).update_storage()


class Query_WaterLevels_V1(modeltools.Method):
    """Query the water levels from all submodels following the |StorageModel_V1|
    interface.

    Example:

        >>> from hydpy.models.sw1d_channel import *
        >>> parameterstep()
        >>> nmbsegments(2)
        >>> with model.add_storagemodel_v1("sw1d_storage", position=0, update=False):
        ...     factors.waterlevel = 1.0
        >>> with model.add_storagemodel_v1("sw1d_storage", position=1, update=False):
        ...     factors.waterlevel = -1.0
        >>> model.query_waterlevels_v1()
        >>> factors.waterlevels
        waterlevels(1.0, -1.0)
    """

    SUBMODELINTERFACES = (channelinterfaces.StorageModel_V1,)
    RESULTSEQUENCES = (sw1d_factors.WaterLevels,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        fac = model.sequences.factors.fastaccess

        for i in range(model.storagemodels.number):
            if model.storagemodels.typeids[i] == 1:
                fac.waterlevels[i] = cast(
                    channelinterfaces.StorageModel_V1, model.storagemodels.submodels[i]
                ).get_waterlevel()


# interface methods


class Perform_Preprocessing_V1(modeltools.AutoMethod):
    """Routing model interface method for preprocessing data that is invariant within
    each external simulation step."""

    SUBMETHODS = (Pick_Inflow_V1,)
    REQUIREDSEQUENCES = (sw1d_inlets.LongQ,)
    RESULTSEQUENCES = (sw1d_fluxes.Inflow,)


class Perform_Preprocessing_V2(modeltools.AutoMethod):
    """Routing model interface method for preprocessing data that is invariant within
    each external simulation step."""

    SUBMETHODS = (Reset_DischargeVolume_V1,)
    RESULTSEQUENCES = (sw1d_fluxes.DischargeVolume,)


class Perform_Preprocessing_V3(modeltools.AutoMethod):
    """Storage model interface method for preprocessing data that is invariant within
    each external simulation step."""

    SUBMETHODS = (Pick_LateralFlow_V1, Calc_WaterDepth_V1, Calc_WaterLevel_V1)
    CONTROLPARAMETERS = (
        sw1d_control.Length,
        sw1d_control.BottomLevel,
        sw1d_control.BottomWidth,
        sw1d_control.SideSlope,
    )
    REQUIREDSEQUENCES = (sw1d_inlets.LatQ, sw1d_states.WaterVolume)
    RESULTSEQUENCES = (
        sw1d_factors.WaterDepth,
        sw1d_factors.WaterLevel,
        sw1d_fluxes.LateralFlow,
    )


class Perform_Preprocessing_V4(modeltools.AutoMethod):
    """Routing model interface method for preprocessing data that is invariant within
    each external simulation step."""

    SUBMETHODS = (Pick_Outflow_V1,)
    REQUIREDSEQUENCES = (sw1d_outlets.LongQ,)
    RESULTSEQUENCES = (sw1d_fluxes.Outflow,)


class Perform_Preprocessing_V5(modeltools.AutoMethod):
    """Routing model interface method for preprocessing data that is invariant within
    each external simulation step."""

    SUBMETHODS = (Pick_WaterLevelDownstream_V1, Reset_DischargeVolume_V1)
    REQUIREDSEQUENCES = (sw1d_receivers.WaterLevel,)
    RESULTSEQUENCES = (sw1d_factors.WaterLevelDownstream, sw1d_fluxes.DischargeVolume)


class Perform_Postprocessing_V1(modeltools.AutoMethod):
    """Routing model interface method for executing all tasks necessary at the end of
    each external simulation step."""

    SUBMETHODS = (Calc_DischargeVolume_V1,)
    DERIVEDPARAMETERS = (sw1d_derived.Seconds,)
    REQUIREDSEQUENCES = (sw1d_fluxes.Inflow,)
    UPDATEDSEQUENCES = (sw1d_fluxes.DischargeVolume,)


class Perform_Postprocessing_V2(modeltools.AutoMethod):
    """Routing model interface method for executing all tasks necessary at the end of
    each external simulation step."""

    SUBMETHODS = (Pass_Discharge_V1,)
    DERIVEDPARAMETERS = (sw1d_derived.Seconds,)
    REQUIREDSEQUENCES = (sw1d_fluxes.DischargeVolume,)
    RESULTSEQUENCES = (sw1d_inlets.LongQ, sw1d_outlets.LongQ)


class Perform_Postprocessing_V3(modeltools.AutoMethod):
    """Storage model interface method for executing all tasks necessary at the end of
    each external simulation step."""

    SUBMETHODS = (Pass_WaterLevel_V1,)
    REQUIREDSEQUENCES = (sw1d_factors.WaterLevel,)
    RESULTSEQUENCES = (sw1d_senders.WaterLevel,)


class Perform_Postprocessing_V4(modeltools.AutoMethod):
    """Routing model interface method for executing all tasks necessary at the end of
    each external simulation step."""

    SUBMETHODS = (Calc_DischargeVolume_V2,)
    DERIVEDPARAMETERS = (sw1d_derived.Seconds,)
    REQUIREDSEQUENCES = (sw1d_fluxes.Outflow,)
    UPDATEDSEQUENCES = (sw1d_fluxes.DischargeVolume,)


class Determine_MaxTimeStep_V1(modeltools.AutoMethod):
    """Interface method for determining the highest possible computation time step at a
    central location."""

    SUBMETHODS = (
        Calc_WaterLevelUpstream_V1,
        Calc_WaterLevelDownstream_V1,
        Calc_WaterLevel_V2,
        Calc_WaterDepth_V2,
        Calc_WettedArea_V1,
        Calc_WettedPerimeter_V1,
        Calc_DischargeUpstream_V1,
        Calc_DischargeDownstream_V1,
        Calc_MaxTimeStep_V1,
    )
    CONTROLPARAMETERS = (
        sw1d_control.BottomLevel,
        sw1d_control.BottomWidth,
        sw1d_control.SideSlope,
        sw1d_control.TimeStepFactor,
    )
    DERIVEDPARAMETERS = (sw1d_derived.WeightUpstream, sw1d_derived.LengthMin)
    FIXEDPARAMETERS = (sw1d_fixed.GravitationalAcceleration,)
    REQUIREDSEQUENCES = (sw1d_states.Discharge,)
    RESULTSEQUENCES = (
        sw1d_factors.WaterLevelUpstream,
        sw1d_factors.WaterLevelDownstream,
        sw1d_factors.WaterLevel,
        sw1d_factors.WaterDepth,
        sw1d_factors.WettedArea,
        sw1d_factors.WettedPerimeter,
        sw1d_factors.MaxTimeStep,
        sw1d_fluxes.DischargeUpstream,
        sw1d_fluxes.DischargeDownstream,
    )


class Determine_MaxTimeStep_V2(modeltools.AutoMethod):
    """Interface method for determining the highest possible computation time step at
    an inflow location."""

    SUBMETHODS = (
        Calc_WaterLevelDownstream_V1,
        Calc_WaterLevel_V3,
        Calc_WaterDepth_V2,
        Calc_WettedArea_V1,
        Calc_MaxTimeStep_V2,
    )
    CONTROLPARAMETERS = (
        sw1d_control.BottomLevel,
        sw1d_control.BottomWidth,
        sw1d_control.SideSlope,
        sw1d_control.LengthDownstream,
        sw1d_control.TimeStepFactor,
    )
    REQUIREDSEQUENCES = (sw1d_fluxes.Inflow,)
    RESULTSEQUENCES = (
        sw1d_factors.WaterLevelDownstream,
        sw1d_factors.WaterLevel,
        sw1d_factors.WaterDepth,
        sw1d_factors.WettedArea,
        sw1d_factors.MaxTimeStep,
    )


class Determine_MaxTimeStep_V3(modeltools.AutoMethod):
    """Interface method for determining the highest possible computation time step at
    an outflow weir."""

    SUBMETHODS = (Calc_WaterLevelUpstream_V1, Calc_WaterLevel_V4, Calc_MaxTimeStep_V3)
    CONTROLPARAMETERS = (
        sw1d_control.CrestHeight,
        sw1d_control.FlowCoefficient,
        sw1d_control.TimeStepFactor,
        sw1d_control.LengthUpstream,
    )
    FIXEDPARAMETERS = (sw1d_fixed.GravitationalAcceleration,)
    RESULTSEQUENCES = (
        sw1d_factors.WaterLevelUpstream,
        sw1d_factors.WaterLevel,
        sw1d_factors.MaxTimeStep,
    )


class Determine_MaxTimeStep_V4(modeltools.AutoMethod):
    """Interface method for determining the highest possible computation time step at
    an outflow location."""

    SUBMETHODS = (
        Calc_WaterLevelUpstream_V1,
        Calc_WaterLevel_V4,
        Calc_WaterDepth_V2,
        Calc_WettedArea_V1,
        Calc_MaxTimeStep_V4,
    )
    CONTROLPARAMETERS = (
        sw1d_control.BottomLevel,
        sw1d_control.BottomWidth,
        sw1d_control.SideSlope,
        sw1d_control.LengthUpstream,
        sw1d_control.TimeStepFactor,
    )
    REQUIREDSEQUENCES = (sw1d_fluxes.Outflow,)
    RESULTSEQUENCES = (
        sw1d_factors.WaterLevelUpstream,
        sw1d_factors.WaterLevel,
        sw1d_factors.WaterDepth,
        sw1d_factors.WettedArea,
        sw1d_factors.MaxTimeStep,
    )


class Determine_MaxTimeStep_V5(modeltools.AutoMethod):
    """Interface method for determining the highest possible computation time step at
    an outflow gate."""

    SUBMETHODS = (Calc_WaterLevelUpstream_V1, Calc_WaterLevel_V5, Calc_MaxTimeStep_V5)
    CONTROLPARAMETERS = (
        sw1d_control.BottomLevel,
        sw1d_control.GateHeight,
        sw1d_control.FlowCoefficient,
        sw1d_control.LengthUpstream,
        sw1d_control.TimeStepFactor,
    )
    FIXEDPARAMETERS = (sw1d_fixed.GravitationalAcceleration,)
    REQUIREDSEQUENCES = (sw1d_factors.WaterLevelDownstream,)
    RESULTSEQUENCES = (
        sw1d_factors.WaterLevelUpstream,
        sw1d_factors.WaterLevel,
        sw1d_factors.MaxTimeStep,
    )


class Determine_Discharge_V1(modeltools.AutoMethod):
    """Interface method for determining the discharge at a central location."""

    SUBMETHODS = (
        Calc_WaterVolumeUpstream_V1,
        Calc_WaterVolumeDownstream_V1,
        Calc_Discharge_V1,
        Update_Discharge_V1,
        Update_DischargeVolume_V1,
    )
    CONTROLPARAMETERS = (
        sw1d_control.StricklerCoefficient,
        sw1d_control.DiffusionFactor,
    )
    DERIVEDPARAMETERS = (sw1d_derived.LengthMean,)
    FIXEDPARAMETERS = (sw1d_fixed.GravitationalAcceleration,)
    REQUIREDSEQUENCES = (
        sw1d_factors.WaterLevelUpstream,
        sw1d_factors.WaterLevelDownstream,
        sw1d_factors.WettedArea,
        sw1d_factors.WettedPerimeter,
        sw1d_fluxes.DischargeUpstream,
        sw1d_fluxes.DischargeDownstream,
        sw1d_factors.TimeStep,
    )
    RESULTSEQUENCES = (
        sw1d_factors.WaterVolumeUpstream,
        sw1d_factors.WaterVolumeDownstream,
    )
    UPDATEDSEQUENCES = (sw1d_states.Discharge, sw1d_fluxes.DischargeVolume)


class Determine_Discharge_V2(modeltools.Method):
    """Interface method for determining the discharge at an inflow location."""

    REQUIREDSEQUENCES = (sw1d_fluxes.Inflow,)
    UPDATEDSEQUENCES = (sw1d_states.Discharge,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        sta.discharge = flu.inflow


class Determine_Discharge_V3(modeltools.AutoMethod):
    """Interface method for determining the discharge at an outflow weir."""

    SUBMETHODS = (Calc_Discharge_V2, Update_DischargeVolume_V1)
    CONTROLPARAMETERS = (
        sw1d_control.CrestHeight,
        sw1d_control.CrestWidth,
        sw1d_control.FlowCoefficient,
    )
    FIXEDPARAMETERS = (sw1d_fixed.GravitationalAcceleration,)
    REQUIREDSEQUENCES = (sw1d_factors.WaterLevel, sw1d_factors.TimeStep)
    UPDATEDSEQUENCES = (sw1d_states.Discharge, sw1d_fluxes.DischargeVolume)


class Determine_Discharge_V4(modeltools.Method):
    """Interface method for determining the discharge at an outflow location."""

    REQUIREDSEQUENCES = (sw1d_fluxes.Outflow,)
    UPDATEDSEQUENCES = (sw1d_states.Discharge,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        sta.discharge = flu.outflow


class Determine_Discharge_V5(modeltools.AutoMethod):
    """Interface method for determining the sluice-modified discharge at a central
    location considering."""

    SUBMETHODS = (
        Calc_WaterVolumeUpstream_V1,
        Calc_WaterVolumeDownstream_V1,
        Calc_Discharge_V1,
        Update_Discharge_V1,
        Update_Discharge_V2,
        Update_DischargeVolume_V1,
    )
    CONTROLPARAMETERS = (
        sw1d_control.StricklerCoefficient,
        sw1d_control.DiffusionFactor,
        sw1d_control.TargetWaterLevel1,
        sw1d_control.TargetWaterLevel2,
    )
    DERIVEDPARAMETERS = (sw1d_derived.LengthMean,)
    FIXEDPARAMETERS = (sw1d_fixed.GravitationalAcceleration,)
    REQUIREDSEQUENCES = (
        sw1d_factors.WaterLevelUpstream,
        sw1d_factors.WaterLevelDownstream,
        sw1d_factors.WettedArea,
        sw1d_factors.WettedPerimeter,
        sw1d_fluxes.DischargeUpstream,
        sw1d_fluxes.DischargeDownstream,
        sw1d_factors.TimeStep,
    )
    RESULTSEQUENCES = (
        sw1d_factors.WaterVolumeUpstream,
        sw1d_factors.WaterVolumeDownstream,
    )
    UPDATEDSEQUENCES = (sw1d_states.Discharge, sw1d_fluxes.DischargeVolume)


class Determine_Discharge_V6(modeltools.AutoMethod):
    """Interface method for determining the discharge at an outflow gate."""

    SUBMETHODS = (Calc_Discharge_V3, Update_DischargeVolume_V1)
    CONTROLPARAMETERS = (
        sw1d_control.BottomLevel,
        sw1d_control.GateHeight,
        sw1d_control.GateWidth,
        sw1d_control.FlowCoefficient,
        sw1d_control.DampingRadius,
    )
    FIXEDPARAMETERS = (sw1d_fixed.GravitationalAcceleration,)
    REQUIREDSEQUENCES = (
        sw1d_factors.WaterLevel,
        sw1d_factors.WaterLevelUpstream,
        sw1d_factors.WaterLevelDownstream,
        sw1d_factors.TimeStep,
    )
    UPDATEDSEQUENCES = (sw1d_states.Discharge, sw1d_fluxes.DischargeVolume)


class Get_WaterVolume_V1(modeltools.Method):
    """Interface method for querying the water volume in 1000 m³."""

    REQUIREDSEQUENCES = (sw1d_states.WaterVolume,)

    @staticmethod
    def __call__(model: modeltools.Model) -> float:
        sta = model.sequences.states.fastaccess
        return sta.watervolume


class Get_WaterLevel_V1(modeltools.Method):
    """Interface method for querying the water level in m."""

    REQUIREDSEQUENCES = (sw1d_factors.WaterLevel,)

    @staticmethod
    def __call__(model: modeltools.Model) -> float:
        fac = model.sequences.factors.fastaccess
        return fac.waterlevel


class Get_Discharge_V1(modeltools.Method):
    """Interface method for querying the discharge in m³/s."""

    REQUIREDSEQUENCES = (sw1d_states.Discharge,)

    @staticmethod
    def __call__(model: modeltools.Model) -> float:
        sta = model.sequences.states.fastaccess
        return sta.discharge


class Get_DischargeVolume_V1(modeltools.Method):
    """Interface method for querying the discharge in m³."""

    REQUIREDSEQUENCES = (sw1d_fluxes.DischargeVolume,)

    @staticmethod
    def __call__(model: modeltools.Model) -> float:
        flu = model.sequences.fluxes.fastaccess
        return flu.dischargevolume


class Get_MaxTimeStep_V1(modeltools.Method):
    """Interface method for querying the highest possible computation time step in
    s."""

    REQUIREDSEQUENCES = (sw1d_factors.MaxTimeStep,)

    @staticmethod
    def __call__(model: modeltools.Model) -> float:
        fac = model.sequences.factors.fastaccess
        return fac.maxtimestep


class Set_TimeStep_V1(modeltools.Method):
    """Interface method for setting the actual computation time step in s."""

    RESULTSEQUENCES = (sw1d_factors.TimeStep,)

    @staticmethod
    def __call__(model: modeltools.Model, timestep: float) -> None:
        fac = model.sequences.factors.fastaccess
        fac.timestep = timestep


class Get_PartialDischargeUpstream_V1(modeltools.Method):
    r"""Return a partial discharge estimate suitable for a downstream model.

    Basic equation:
      :math:`PartialDischargeUpstream = Discharge_{server} \cdot
      \frac{|Discharge_{client}|}{\Sigma_{i=1}^{n_{downstream}} |Discharge_i|}`

    Examples:

        If the client model (which is currently asking for the partial discharge) is
        the only downstream model, |Get_PartialDischargeUpstream_V1| returns the total
        discharge without modification:

        >>> from hydpy import Element, Node, prepare_model, round_
        >>> n01 = Node("n01", variable="LongQ")
        >>> e0 = Element("e0", outlets=n01)
        >>> e1a = Element("e1a", inlets=n01)

        >>> c0 = prepare_model("sw1d_channel")
        >>> e0.model = c0
        >>> c0.parameters.control.nmbsegments(1)
        >>> with c0.add_routingmodel_v2("sw1d_lias", position=0, update=False) as r0:
        ...     states.discharge = 5.0
        >>> with c0.add_storagemodel_v1("sw1d_storage", position=0, update=False):
        ...     pass

        >>> c1a = prepare_model("sw1d_channel")
        >>> e1a.model = c1a
        >>> c1a.parameters.control.nmbsegments(1)
        >>> with c1a.add_routingmodel_v2("sw1d_lias", position=0, update=False) as r1a:
        ...     states.discharge = 3.0
        >>> with c1a.add_storagemodel_v1("sw1d_storage", position=0, update=False):
        ...     pass
        >>> network = c0.couple_models(nodes=[n01], elements=[e0, e1a])
        >>> round_(r0.get_partialdischargeupstream_v1(3.0))
        5.0

        For multiple downstream models, it returns the discharge portion that it
        attributes to the current client model:

        >>> e1b = Element("e1b", inlets=n01)
        >>> c1b = prepare_model("sw1d_channel")
        >>> e1b.model = c1b
        >>> c1b.parameters.control.nmbsegments(1)
        >>> with c1b.add_routingmodel_v2("sw1d_lias", position=0, update=False) as r1b:
        ...     states.discharge = 1.0
        >>> with c1b.add_storagemodel_v1("sw1d_storage", position=0, update=False):
        ...     pass
        >>> network = c0.couple_models(nodes=[n01], elements=[e0, e1a, e1b])
        >>> round_(r0.get_partialdischargeupstream_v1(3.0))
        3.75
        >>> round_(r0.get_partialdischargeupstream_v1(1.0))
        1.25

        To prevent zero divisions, |Get_PartialDischargeUpstream_V1| returns zero if
        all downstream models' (total) discharge is also zero:

        >>> r1a.sequences.states.discharge = 0.0
        >>> r1b.sequences.states.discharge = 0.0
        >>> round_(r0.get_partialdischargeupstream_v1(0.0))
        0.0

        .. testsetup::

            >>> Node.clear_all()
            >>> Element.clear_all()
    """

    SUBMODELINTERFACES = (
        channelinterfaces.RoutingModel_V2,
        channelinterfaces.RoutingModel_V3,
    )
    REQUIREDSEQUENCES = (sw1d_states.Discharge,)

    @staticmethod
    def __call__(model: modeltools.Model, clientdischarge: float) -> float:
        sta = model.sequences.states.fastaccess

        dischargedownstream: float = 0.0
        for i in range(model.routingmodelsdownstream.number):
            if model.routingmodelsdownstream.typeids[i] in (2, 3):
                dischargedownstream += modelutils.fabs(
                    cast(
                        Union[
                            channelinterfaces.RoutingModel_V2,
                            channelinterfaces.RoutingModel_V3,
                        ],
                        model.routingmodelsdownstream.submodels[i],
                    ).get_discharge()
                )
        if dischargedownstream == 0.0:
            return 0.0
        return modelutils.fabs(sta.discharge) * clientdischarge / dischargedownstream


class Get_PartialDischargeDownstream_V1(modeltools.Method):
    r"""Return a partial discharge estimate suitable for an upstream model.

    Basic equation:
      :math:`PartialDischargeDownstream = Discharge_{server} \cdot
      \frac{|Discharge_{client}|}{\Sigma_{i=1}^{n_{upstream}} |Discharge_i|}`

    Examples:

        If the client model (which is currently asking for the partial discharge) is
        the only upstream model, |Get_PartialDischargeDownstream_V1| returns the total
        discharge without modification:

        >>> from hydpy import Element, Node, prepare_model, round_
        >>> n01 = Node("n01", variable="LongQ")
        >>> e1 = Element("e1", inlets=n01)
        >>> e0a = Element("e0a", outlets=n01)

        >>> c1 = prepare_model("sw1d_channel")
        >>> e1.model = c1
        >>> c1.parameters.control.nmbsegments(1)
        >>> with c1.add_storagemodel_v1("sw1d_storage", position=0, update=False):
        ...     pass
        >>> with c1.add_routingmodel_v2("sw1d_lias", position=1, update=False) as r1:
        ...     states.discharge = 5.0

        >>> c0a = prepare_model("sw1d_channel")
        >>> e0a.model = c0a
        >>> c0a.parameters.control.nmbsegments(1)
        >>> with c0a.add_storagemodel_v1("sw1d_storage", position=0, update=False):
        ...     pass
        >>> with c0a.add_routingmodel_v2("sw1d_lias", position=1, update=False) as r0a:
        ...     states.discharge = 3.0
        >>> network = c1.couple_models(nodes=[n01], elements=[e1, e0a])
        >>> round_(r1.get_partialdischargedownstream_v1(3.0))
        5.0

        For multiple upstream models, it returns the discharge portion that it
        attributes to the current client model:

        >>> e0b = Element("e0b", outlets=n01)
        >>> c0b = prepare_model("sw1d_channel")
        >>> e0b.model = c0b
        >>> c0b.parameters.control.nmbsegments(1)
        >>> with c0b.add_storagemodel_v1("sw1d_storage", position=0, update=False):
        ...     pass
        >>> with c0b.add_routingmodel_v2("sw1d_lias", position=1, update=False) as r0b:
        ...     states.discharge = 1.0
        >>> network = c1.couple_models(nodes=[n01], elements=[e1, e0a, e0b])
        >>> round_(r1.get_partialdischargedownstream_v1(3.0))
        3.75
        >>> round_(r1.get_partialdischargedownstream_v1(1.0))
        1.25

        To prevent zero divisions, |Get_PartialDischargeDownstream_V1| returns zero if
        all upstream models' (total) discharge is also zero:

        >>> r0a.sequences.states.discharge = 0.0
        >>> r0b.sequences.states.discharge = 0.0
        >>> round_(r1.get_partialdischargedownstream_v1(0.0))
        0.0

        .. testsetup::

            >>> Node.clear_all()
            >>> Element.clear_all()
    """

    SUBMODELINTERFACES = (
        channelinterfaces.RoutingModel_V1,
        channelinterfaces.RoutingModel_V2,
    )
    REQUIREDSEQUENCES = (sw1d_states.Discharge,)

    @staticmethod
    def __call__(model: modeltools.Model, clientdischarge: float) -> float:
        sta = model.sequences.states.fastaccess

        dischargeupstream: float = 0.0
        for i in range(model.routingmodelsupstream.number):
            if model.routingmodelsupstream.typeids[i] in (1, 2):
                dischargeupstream += modelutils.fabs(
                    cast(
                        Union[
                            channelinterfaces.RoutingModel_V1,
                            channelinterfaces.RoutingModel_V2,
                        ],
                        model.routingmodelsupstream.submodels[i],
                    ).get_discharge()
                )
        if dischargeupstream == 0.0:
            return 0.0
        return modelutils.fabs(sta.discharge) * clientdischarge / dischargeupstream


class Update_Storage_V1(modeltools.AutoMethod):
    """Interface method for updating the storage water content."""

    SUBMETHODS = (
        Calc_NetInflow_V1,
        Update_WaterVolume_V1,
        Calc_WaterDepth_V1,
        Calc_WaterLevel_V1,
    )
    CONTROLPARAMETERS = (
        sw1d_control.Length,
        sw1d_control.BottomLevel,
        sw1d_control.BottomWidth,
        sw1d_control.SideSlope,
    )
    REQUIREDSEQUENCES = (sw1d_factors.TimeStep, sw1d_fluxes.LateralFlow)
    RESULTSEQUENCES = (
        sw1d_fluxes.NetInflow,
        sw1d_factors.WaterDepth,
        sw1d_factors.WaterLevel,
    )
    UPDATEDSEQUENCES = (sw1d_states.WaterVolume,)


class Model(modeltools.SubstepModel):
    """The HydPy-SW-1D model."""

    INLET_METHODS = (
        Pick_Inflow_V1,
        Pick_Outflow_V1,
        Pick_LateralFlow_V1,
        Pick_WaterLevelDownstream_V1,
        Trigger_Preprocessing_V1,
    )
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        Calc_MaxTimeSteps_V1,
        Calc_TimeStep_V1,
        Send_TimeStep_V1,
        Calc_Discharges_V1,
        Update_Storages_V1,
        Query_WaterLevels_V1,
    )
    INTERFACE_METHODS = (
        Perform_Preprocessing_V1,
        Perform_Preprocessing_V2,
        Perform_Preprocessing_V3,
        Perform_Preprocessing_V4,
        Perform_Preprocessing_V5,
        Perform_Postprocessing_V1,
        Perform_Postprocessing_V2,
        Perform_Postprocessing_V3,
        Perform_Postprocessing_V4,
        Determine_MaxTimeStep_V1,
        Determine_MaxTimeStep_V2,
        Determine_MaxTimeStep_V3,
        Determine_MaxTimeStep_V4,
        Determine_MaxTimeStep_V5,
        Determine_Discharge_V1,
        Determine_Discharge_V2,
        Determine_Discharge_V3,
        Determine_Discharge_V4,
        Determine_Discharge_V5,
        Determine_Discharge_V6,
        Get_WaterVolume_V1,
        Get_WaterLevel_V1,
        Get_Discharge_V1,
        Get_DischargeVolume_V1,
        Get_MaxTimeStep_V1,
        Set_TimeStep_V1,
        Get_PartialDischargeUpstream_V1,
        Get_PartialDischargeDownstream_V1,
        Update_Storage_V1,
    )
    ADD_METHODS = (
        Calc_MaxTimeStep_V1,
        Calc_MaxTimeStep_V2,
        Calc_MaxTimeStep_V3,
        Calc_MaxTimeStep_V4,
        Calc_MaxTimeStep_V5,
        Calc_WaterVolumeUpstream_V1,
        Calc_WaterVolumeDownstream_V1,
        Calc_WaterLevelUpstream_V1,
        Calc_WaterLevelDownstream_V1,
        Calc_WaterLevel_V1,
        Calc_WaterLevel_V2,
        Calc_WaterLevel_V3,
        Calc_WaterLevel_V4,
        Calc_WaterLevel_V5,
        Calc_WaterDepth_V1,
        Calc_WaterDepth_V2,
        Calc_WettedArea_V1,
        Calc_WettedPerimeter_V1,
        Calc_DischargeUpstream_V1,
        Calc_DischargeDownstream_V1,
        Calc_Discharge_V1,
        Calc_Discharge_V2,
        Calc_Discharge_V3,
        Update_Discharge_V1,
        Update_Discharge_V2,
        Reset_DischargeVolume_V1,
        Update_DischargeVolume_V1,
        Calc_DischargeVolume_V1,
        Calc_DischargeVolume_V2,
        Calc_NetInflow_V1,
        Update_WaterVolume_V1,
    )
    OUTLET_METHODS = (
        Pass_Discharge_V1,
        Pass_WaterLevel_V1,
        Trigger_Postprocessing_V1,
        Calc_Discharges_V2,
    )
    SENDER_METHODS = ()
    SUBMODELINTERFACES = (
        channelinterfaces.ChannelModel_V1,
        channelinterfaces.StorageModel_V1,
        channelinterfaces.RoutingModel_V1,
        channelinterfaces.RoutingModel_V2,
        channelinterfaces.RoutingModel_V3,
    )
    SUBMODELS = ()

    channelmodels = modeltools.SubmodelsProperty(channelinterfaces.ChannelModel_V1)
    storagemodels = modeltools.SubmodelsProperty(channelinterfaces.StorageModel_V1)
    routingmodels = modeltools.SubmodelsProperty(channelinterfaces.RoutingModel_V1)

    storagemodelupstream = modeltools.SubmodelProperty(
        channelinterfaces.StorageModel_V1
    )
    storagemodelupstream_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    storagemodelupstream_typeid = modeltools.SubmodelTypeIDProperty()

    storagemodeldownstream = modeltools.SubmodelProperty(
        channelinterfaces.StorageModel_V1
    )
    storagemodeldownstream_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    storagemodeldownstream_typeid = modeltools.SubmodelTypeIDProperty()

    routingmodelsupstream = modeltools.SubmodelsProperty(
        channelinterfaces.RoutingModel_V1,
        channelinterfaces.RoutingModel_V2,
        channelinterfaces.RoutingModel_V3,
        sidemodels=True,
    )
    routingmodelsdownstream = modeltools.SubmodelsProperty(
        channelinterfaces.RoutingModel_V2,
        channelinterfaces.RoutingModel_V3,
        channelinterfaces.RoutingModel_V3,
        sidemodels=True,
    )
