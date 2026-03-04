# pylint: disable=missing-module-docstring

# imports...
# ...from HydPy
from hydpy.core import modeltools
from hydpy.cythons import modelutils
from hydpy.cythons import smoothutils
from hydpy.models.manager import manager_control
from hydpy.models.manager import manager_derived
from hydpy.models.manager import manager_factors
from hydpy.models.manager import manager_fluxes
from hydpy.models.manager import manager_logs
from hydpy.models.manager import manager_receivers
from hydpy.models.manager import manager_senders


class Pick_LoggedDischarge_V1(modeltools.Method):
    """Pick and memorise the target node's current discharge value.

    Example:

        >>> from hydpy.models.manager import *
        >>> parameterstep()
        >>> derived.memorylength(3)
        >>> receivers.q = 3.0
        >>> logs.loggeddischarge = 2.0, 4.0, 6.0
        >>> model.pick_loggeddischarge_v1()
        >>> logs.loggeddischarge
        loggeddischarge(3.0, 2.0, 4.0)
    """

    DERIVEDPARAMETERS = (manager_derived.MemoryLength,)
    REQUIREDSEQUENCES = (manager_receivers.Q,)
    RESULTSEQUENCES = (manager_logs.LoggedDischarge,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        der = model.parameters.derived.fastaccess
        log = model.sequences.logs.fastaccess
        rec = model.sequences.receivers.fastaccess

        for i in range(der.memorylength - 1, 0, -1):
            log.loggeddischarge[i] = log.loggeddischarge[i - 1]
        log.loggeddischarge[0] = rec.q


class Pick_LoggedWaterVolume_V1(modeltools.Method):
    """Pick and memorise the water volume of all sources.

    Example:

        >>> from hydpy.models.manager import *
        >>> parameterstep()
        >>> sources("a", "b", "c")
        >>> receivers.watervolume.shape = 3
        >>> receivers.watervolume = 1.0, 3.0, 2.0
        >>> model.pick_loggedwatervolume_v1()
        >>> logs.loggedwatervolume
        loggedwatervolume(a=1.0, b=3.0, c=2.0)
    """

    CONTROLPARAMETERS = (manager_control.Sources,)
    REQUIREDSEQUENCES = (manager_receivers.WaterVolume,)
    RESULTSEQUENCES = (manager_logs.LoggedWaterVolume,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        log = model.sequences.logs.fastaccess
        rec = model.sequences.receivers.fastaccess
        for i in range(con.sources):
            log.loggedwatervolume[i] = rec.watervolume[i]


class Calc_FreeDischarge_V1(modeltools.Method):
    r"""Extrapolate the "free discharge" that might occur without requesting additional
    water releases.

    Basic equation:
       .. math::
        F = max \left
        (min \left(f(1), \, \min_{i=2}^W \big(f(1) + f(i) / i\big) \right), \, 0 \right)
        \\
        f(i) = Q_i - R_{i+D}

        \\ \\
        F = FreeDischarge \\
        Q = LoggedDischarge \\
        R = LoggedRequest \\
        W = TimeWindow \\
        D = TimeDelay

    Examples:

        >>> from hydpy.models.manager import *
        >>> parameterstep()
        >>> timedelay(1)
        >>> timewindow(1)
        >>> derived.memorylength.update()

        >>> logs.loggeddischarge(3.0, nan)
        >>> logs.loggedrequest(nan, 1.0)
        >>> model.calc_freedischarge_v1()
        >>> fluxes.freedischarge
        freedischarge(2.0)

        >>> timewindow(3)
        >>> derived.memorylength.update()
        >>> logs.loggeddischarge(2.0, 3.0, 4.0, nan)
        >>> logs.loggedrequest(nan, 0.0, 1.0, 2.0)
        >>> model.calc_freedischarge_v1()
        >>> fluxes.freedischarge
        freedischarge(2.0)

        >>> logs.loggeddischarge[1] = 4.0
        >>> model.calc_freedischarge_v1()
        >>> fluxes.freedischarge
        freedischarge(1.0)

        >>> logs.loggeddischarge[1:3] = 3.0, 6.0
        >>> model.calc_freedischarge_v1()
        >>> fluxes.freedischarge
        freedischarge(1.0)

        >>> logs.loggeddischarge[2] = 10.0
        >>> model.calc_freedischarge_v1()
        >>> fluxes.freedischarge
        freedischarge(0.0)
    """

    CONTROLPARAMETERS = (manager_control.TimeDelay, manager_control.TimeWindow)
    REQUIREDSEQUENCES = (manager_logs.LoggedDischarge, manager_logs.LoggedRequest)
    RESULTSEQUENCES = (manager_fluxes.FreeDischarge,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        log = model.sequences.logs.fastaccess
        flu = model.sequences.fluxes.fastaccess

        flu.freedischarge = log.loggeddischarge[0] - log.loggedrequest[con.timedelay]
        q_min: float = modelutils.inf
        for i in range(1, con.timewindow):
            q_old: float = log.loggeddischarge[i] - log.loggedrequest[i + con.timedelay]
            q_min = min(q_min, flu.freedischarge + (flu.freedischarge - q_old) / i)
        flu.freedischarge = max(min(flu.freedischarge, q_min), 0.0)


class Calc_DemandTarget_V1(modeltools.Method):
    r"""Estimate the demand for additional water releases.

    Basic equation:
       .. math::
        D = m(T - F, \, 0, \, S)
        \\ \\
        D = Demand \\
        F = FreeDischarge \\
        T = DischargeThreshold \\
        S = DischargeSmoothPar \\
        m = smooth\_max1

    Used auxiliary method:
      |smooth_max1|

    Examples:

        >>> from hydpy.models.manager import *
        >>> parameterstep()
        >>> dischargethreshold(4.0)
        >>> from hydpy import UnitTest
        >>> test = UnitTest(
        ...     model,
        ...     model.calc_demandtarget_v1,
        ...     last_example=9,
        ...     parseqs=(fluxes.freedischarge, fluxes.demandtarget),
        ... )
        >>> test.nexts.freedischarge = range(9)

        >>> dischargetolerance(0.0)
        >>> derived.dischargesmoothpar.update()
        >>> test()
        | ex. | freedischarge | demandtarget |
        --------------------------------------
        |   1 |           0.0 |          4.0 |
        |   2 |           1.0 |          3.0 |
        |   3 |           2.0 |          2.0 |
        |   4 |           3.0 |          1.0 |
        |   5 |           4.0 |          0.0 |
        |   6 |           5.0 |          0.0 |
        |   7 |           6.0 |          0.0 |
        |   8 |           7.0 |          0.0 |
        |   9 |           8.0 |          0.0 |

        >>> dischargetolerance(1.0)
        >>> derived.dischargesmoothpar.update()
        >>> test()
        | ex. | freedischarge | demandtarget |
        --------------------------------------
        |   1 |           0.0 |          4.0 |
        |   2 |           1.0 |     3.000012 |
        |   3 |           2.0 |     2.000349 |
        |   4 |           3.0 |         1.01 |
        |   5 |           4.0 |     0.205524 |
        |   6 |           5.0 |         0.01 |
        |   7 |           6.0 |     0.000349 |
        |   8 |           7.0 |     0.000012 |
        |   9 |           8.0 |          0.0 |
    """

    CONTROLPARAMETERS = (manager_control.DischargeThreshold,)
    DERIVEDPARAMETERS = (manager_derived.DischargeSmoothPar,)
    REQUIREDSEQUENCES = (manager_fluxes.FreeDischarge,)
    RESULTSEQUENCES = (manager_fluxes.DemandTarget,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess

        flu.demandtarget = smoothutils.smooth_max1(
            con.dischargethreshold - flu.freedischarge, 0.0, der.dischargesmoothpar
        )


class Calc_Alertness_V1(modeltools.Method):
    r"""Determine the current need for low water control.

    Basic equation:
       .. math::
        A = l(T - F, \, 0, S)
        \\ \\
        A = Alertness \\
        F = FreeDischarge \\
        T = DischargeThreshold \\
        S = DischargeSmoothPar \\
        l = smooth\_logistic1

    Used auxiliary method:
      |smooth_logistic1|

    Examples:

        >>> from hydpy.models.manager import *
        >>> parameterstep()
        >>> dischargethreshold(4.0)
        >>> from hydpy import UnitTest
        >>> test = UnitTest(
        ...     model,
        ...     model.calc_alertness_v1,
        ...     last_example=9,
        ...     parseqs=(fluxes.freedischarge, factors.alertness),
        ... )
        >>> test.nexts.freedischarge = range(9)

        >>> dischargetolerance(0.0)
        >>> derived.dischargesmoothpar.update()
        >>> test()
        | ex. | freedischarge | alertness |
        -----------------------------------
        |   1 |           0.0 |       1.0 |
        |   2 |           1.0 |       1.0 |
        |   3 |           2.0 |       1.0 |
        |   4 |           3.0 |       1.0 |
        |   5 |           4.0 |       0.5 |
        |   6 |           5.0 |       0.0 |
        |   7 |           6.0 |       0.0 |
        |   8 |           7.0 |       0.0 |
        |   9 |           8.0 |       0.0 |

        >>> dischargetolerance(1.0)
        >>> derived.dischargesmoothpar.update()
        >>> test()
        | ex. | freedischarge | alertness |
        -----------------------------------
        |   1 |           0.0 |  0.999999 |
        |   2 |           1.0 |   0.99996 |
        |   3 |           2.0 |  0.998825 |
        |   4 |           3.0 |  0.966837 |
        |   5 |           4.0 |       0.5 |
        |   6 |           5.0 |  0.033163 |
        |   7 |           6.0 |  0.001175 |
        |   8 |           7.0 |   0.00004 |
        |   9 |           8.0 |  0.000001 |
    """

    CONTROLPARAMETERS = (manager_control.DischargeThreshold,)
    DERIVEDPARAMETERS = (manager_derived.DischargeSmoothPar,)
    REQUIREDSEQUENCES = (manager_fluxes.FreeDischarge,)
    RESULTSEQUENCES = (manager_factors.Alertness,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess

        fac.alertness = smoothutils.smooth_logistic1(
            con.dischargethreshold - flu.freedischarge, der.dischargesmoothpar
        )


class Calc_DemandSources_V1(modeltools.Method):
    r"""Calculate the water demand of all sources.

    Basic equation:
       .. math::
        D = \begin{cases}
        L \cdot 10^6/s \cdot m(T - V, \, 0, \, S)  &|\  A
        \\
        0  &|\  \overline{A}
        \end{cases}
        \\ \\
        A = Active \\
        s = Seconds \\
        D = DemandSources \\
        L = Alertness \\
        V = LoggedWaterVolume \\
        S = VolumeSmoothPar \\
        m = smooth\_max1

    Example:

        >>> from hydpy.models.manager import *
        >>> parameterstep()
        >>> derived.seconds(10**6 / 2.0)
        >>> sources("a", "b", "c", "d", "e", "f", "g", "h", "i", "j")
        >>> volumethreshold(5.0)
        >>> volumetolerance(0.0)
        >>> active(True, True, True, True, True, True, True, True, True, False)
        >>> derived.memorylength(1)
        >>> derived.volumesmoothpar.update()
        >>> logs.loggedwatervolume = 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 5.0
        >>> factors.alertness = 0.5
        >>> model.calc_demandsources_v1()
        >>> fluxes.demandsources
        demandsources(a=4.0, b=3.0, c=2.0, d=1.0, e=0.0, f=0.0, g=0.0, h=0.0,
                      i=0.0, j=0.0)
        >>> volumetolerance(1.0)
        >>> derived.volumesmoothpar.update()
        >>> model.calc_demandsources_v1()
        >>> fluxes.demandsources
        demandsources(a=4.0, b=3.000012, c=2.000349, d=1.01, e=0.205524,
                      f=0.01, g=0.000349, h=0.000012, i=0.0, j=0.0)
    """

    CONTROLPARAMETERS = (
        manager_control.Sources,
        manager_control.Active,
        manager_control.VolumeThreshold,
    )
    DERIVEDPARAMETERS = (manager_derived.Seconds, manager_derived.VolumeSmoothPar)
    REQUIREDSEQUENCES = (manager_factors.Alertness, manager_logs.LoggedWaterVolume)
    RESULTSEQUENCES = (manager_fluxes.DemandSources,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess

        v2q: float = 1e6 / der.seconds
        for i in range(con.sources):
            if con.active[i]:
                flu.demandsources[i] = (
                    fac.alertness
                    * v2q
                    * smoothutils.smooth_max1(
                        con.volumethreshold[i] - log.loggedwatervolume[i],
                        0.0,
                        der.volumesmoothpar[i],
                    )
                )
            else:
                flu.demandsources[i] = 0.0


class Calc_PossibleRelease_V1(modeltools.Method):
    r"""Calculate the possible additional release of all sources.

    Basic equation:
       .. math::
        P = \begin{cases}
        10^6/s \cdot min(max(L - V, \, 0), \, R)  &|\  A
        \\
        0  &|\  \overline{A}
        \end{cases}
        \\ \\
        A = Active \\
        s = Seconds \\
        P = PossibleRelease \\
        L = LoggedWaterVolume \\
        V = VolumeMin \\
        R = ReleaseMax

    Example:

        >>> from hydpy.models.manager import *
        >>> parameterstep()
        >>> sources("a", "b", "c", "d", "e")
        >>> volumethreshold(3.0, 3.0, 6.0, 3.0, 3.0)
        >>> releasemax(6.0, 6.0, 6.0, 3.0, 6.0)
        >>> active(True, True, True, True, False)
        >>> derived.seconds(10**6 / 2.0)
        >>> derived.memorylength(1)
        >>> logs.loggedwatervolume = 4.0, 5.0, 5.0, 5.0, 5.0
        >>> model.calc_possiblerelease_v1()
        >>> fluxes.possiblerelease
        possiblerelease(a=2.0, b=4.0, c=0.0, d=3.0, e=0.0)
    """

    CONTROLPARAMETERS = (
        manager_control.Sources,
        manager_control.Active,
        manager_control.VolumeThreshold,
        manager_control.ReleaseMax,
    )
    DERIVEDPARAMETERS = (manager_derived.Seconds,)
    REQUIREDSEQUENCES = (manager_logs.LoggedWaterVolume,)
    RESULTSEQUENCES = (manager_fluxes.PossibleRelease,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess

        v2q: float = 1e6 / der.seconds
        for i in range(con.sources):
            if con.active[i]:
                flu.possiblerelease[i] = min(
                    v2q * max(log.loggedwatervolume[i] - con.volumethreshold[i], 0.0),
                    con.releasemax[i],
                )
            else:
                flu.possiblerelease[i] = 0.0


class Calc_Request_V1(modeltools.Method):
    """Calculate the additional release request for all sources.

    Examples:

        As shown by the following example, the general principle of method
        |Calc_Request_V1| is to distribute the target node's demand proportionally to
        the directly neighbouring sources' possible release.  The determined requests
        serve as the relevant sources' demands.  |Calc_Request_V1| then distributes
        these sources' demands as requests to the following upstream sources, using the
        same rule.  It repeats this behaviour often enough to reach even the most
        upstream sources.

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2001-01-01", "1d"
        >>> from hydpy.models.manager import *
        >>> parameterstep()
        >>> commission("2000-01-01")
        >>> sources("d_1", "d_1a", "d_2", "d_2a", "d_2b", "d_2b1")
        >>> derived.adjacency([[True, False, False, False, False, False, False],
        ...                    [False, True, False, False, False, False, False],
        ...                    [True, False, False, False, False, False, False],
        ...                    [False, False, False, True, False, False, False],
        ...                    [False, False, False, True, False, False, False],
        ...                    [False, False, False, False, False, True, False]])
        >>> derived.order.update()
        >>> fluxes.demandtarget = 0.0
        >>> fluxes.demandsources = 0.0
        >>> fluxes.possiblerelease = 6.0
        >>> model.calc_request_v1()
        >>> fluxes.request
        request(d_1=0.0, d_1a=0.0, d_2=0.0, d_2a=0.0, d_2b=0.0, d_2b1=0.0)

        >>> fluxes.demandtarget = 10.0
        >>> model.calc_request_v1()
        >>> fluxes.request
        request(d_1=5.0, d_1a=5.0, d_2=5.0, d_2a=2.5, d_2b=2.5, d_2b1=2.5)

        >>> fluxes.possiblerelease[0] = 9.0
        >>> model.calc_request_v1()
        >>> fluxes.request
        request(d_1=6.0, d_1a=6.0, d_2=4.0, d_2a=2.0, d_2b=2.0, d_2b1=2.0)

        >>> fluxes.possiblerelease = 4.0
        >>> model.calc_request_v1()
        >>> fluxes.request
        request(d_1=4.0, d_1a=4.0, d_2=4.0, d_2a=2.0, d_2b=2.0, d_2b1=2.0)

        >>> fluxes.possiblerelease[0] = 0.0
        >>> model.calc_request_v1()
        >>> fluxes.request
        request(d_1=0.0, d_1a=0.0, d_2=4.0, d_2a=2.0, d_2b=2.0, d_2b1=2.0)

        >>> fluxes.possiblerelease[-3] = 1.0
        >>> model.calc_request_v1()
        >>> fluxes.request
        request(d_1=0.0, d_1a=0.0, d_2=4.0, d_2a=0.8, d_2b=3.2, d_2b1=3.2)

        If a source has its own demand, |Calc_Request_V1| adds it to the request to the
        source's upstream neighbours, from which it may be forwarded as described:

        >>> fluxes.demandtarget = 1.0
        >>> fluxes.demandsources[2] = 3.0
        >>> model.calc_request_v1()
        >>> fluxes.request
        request(d_1=0.0, d_1a=0.0, d_2=1.0, d_2a=0.8, d_2b=3.2, d_2b1=3.2)

        Before the commission date, |Calc_Request_V1| sets all requests to zero:

        >>> commission("2000-01-02")
        >>> model.calc_request_v1()
        >>> fluxes.request
        request(d_1=0.0, d_1a=0.0, d_2=0.0, d_2a=0.0, d_2b=0.0, d_2b1=0.0)
    """

    CONTROLPARAMETERS = (manager_control.Commission, manager_control.Sources)
    DERIVEDPARAMETERS = (manager_derived.Adjacency, manager_derived.Order)
    REQUIREDSEQUENCES = (
        manager_fluxes.DemandTarget,
        manager_fluxes.DemandSources,
        manager_fluxes.PossibleRelease,
    )
    RESULTSEQUENCES = (manager_fluxes.Request,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess

        if model.idx_sim < con.commission:

            for i in range(con.sources):
                flu.request[i] = 0.0

        else:

            available: float = 0.0
            for i in range(con.sources):
                if der.adjacency[i, 0]:
                    available += flu.possiblerelease[i]
            f: float = 0.0 if available <= 0 else min(flu.demandtarget / available, 1.0)
            for i in range(con.sources):
                if der.adjacency[i, 0]:
                    flu.request[i] = f * flu.possiblerelease[i]

            for jj in range(con.sources):
                j = der.order[jj]
                demand: float = flu.request[j] + flu.demandsources[j]
                if demand <= 0.0:
                    f = 0.0
                else:
                    available = 0.0
                    for i in range(con.sources):
                        if der.adjacency[i, j + 1]:
                            available += flu.possiblerelease[i]
                    f = 0.0 if available <= 0.0 else min(demand / available, 1.0)
                for i in range(con.sources):
                    if der.adjacency[i, j + 1]:
                        flu.request[i] = f * flu.possiblerelease[i]


class Update_LoggedRequest_V1(modeltools.Method):
    """Sum and memorise the requests to all source elements that are direct neighbours
    to the target node.

    Example:

        >>> from hydpy.models.manager import *
        >>> parameterstep()
        >>> sources("a", "b", "c", "d")
        >>> derived.memorylength(3)
        >>> derived.adjacency([[True, False, False, False, False],
        ...                    [False, True, False, False, False],
        ...                    [True, False, False, False, False],
        ...                    [False, False, True, False, False]])
        >>> fluxes.request = 1.0, nan, 2.0, nan
        >>> logs.loggedrequest = 2.0, 4.0, 6.0
        >>> model.update_loggedrequest_v1()
        >>> logs.loggedrequest
        loggedrequest(3.0, 2.0, 4.0)
    """

    CONTROLPARAMETERS = (manager_control.Sources,)
    DERIVEDPARAMETERS = (manager_derived.MemoryLength, manager_derived.Adjacency)
    REQUIREDSEQUENCES = (manager_fluxes.Request,)
    UPDATEDSEQUENCES = (manager_logs.LoggedRequest,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess

        for i in range(der.memorylength - 1, 0, -1):
            log.loggedrequest[i] = log.loggedrequest[i - 1]

        log.loggedrequest[0] = 0.0
        for i in range(con.sources):
            if der.adjacency[i, 0]:
                log.loggedrequest[0] += flu.request[i]


class Pass_Request_V1(modeltools.Method):
    """Pass the additional water release requests to the relevant sender sequences.

    Example:

        >>> from hydpy.models.manager import *
        >>> parameterstep()
        >>> sources("a", "b", "c")
        >>> fluxes.request = 3.0, 1.0, 2.0
        >>> senders.request.shape = 3
        >>> model.pass_request_v1()
        >>> senders.request
        request(3.0, 1.0, 2.0)
    """

    CONTROLPARAMETERS = (manager_control.Sources,)
    REQUIREDSEQUENCES = (manager_fluxes.Request,)
    RESULTSEQUENCES = (manager_senders.Request,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sen = model.sequences.senders.fastaccess
        for i in range(con.sources):
            sen.request[i] = flu.request[i]


class Model(modeltools.AdHocModel):
    """|manager.DOCNAME.complete|"""

    DOCNAME = modeltools.DocName(
        short="Manager-LWC", description="low water control management model"
    )
    __HYDPY_ROOTMODEL__ = True

    INLET_METHODS = ()
    OBSERVER_METHODS = ()
    RECEIVER_METHODS = (Pick_LoggedDischarge_V1, Pick_LoggedWaterVolume_V1)
    RUN_METHODS = (
        Calc_FreeDischarge_V1,
        Calc_DemandTarget_V1,
        Calc_Alertness_V1,
        Calc_DemandSources_V1,
        Calc_PossibleRelease_V1,
        Calc_Request_V1,
        Update_LoggedRequest_V1,
    )
    ADD_METHODS = ()
    OUTLET_METHODS = ()
    SENDER_METHODS = (Pass_Request_V1,)
    SUBMODELINTERFACES = ()
    SUBMODELS = ()
