# pylint: disable=missing-module-docstring

# imports...
# ...from HydPy
from hydpy.core import modeltools
from hydpy.models.manage import manage_control
from hydpy.models.manage import manage_derived
from hydpy.models.manage import manage_receivers
from hydpy.models.manage import manage_logs
from hydpy.models.manage import manage_fluxes
from hydpy.models.manage import manage_senders


class Pick_LoggedDischarge_V1(modeltools.Method):
    """ToDo"""

    REQUIREDSEQUENCES = (manage_receivers.Q,)
    RESULTSEQUENCES = (manage_logs.LoggedDischarge,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        log = model.sequences.logs.fastaccess
        rec = model.sequences.receivers.fastaccess
        log.loggeddischarge = rec.q


class Pick_LoggedWaterVolume_V1(modeltools.Method):
    """ToDo"""

    CONTROLPARAMETERS = (manage_control.NmbSources,)
    REQUIREDSEQUENCES = (manage_receivers.WaterVolume,)
    RESULTSEQUENCES = (manage_logs.LoggedWaterVolume,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        log = model.sequences.logs.fastaccess
        rec = model.sequences.receivers.fastaccess
        for i in range(con.nmbsources):
            log.loggedwatervolume[i] = rec.watervolume[i]


class Calc_Demand_V1(modeltools.Method):
    """ToDo"""

    CONTROLPARAMETERS = (manage_control.DischargeMin, manage_control.DischargeMax)
    REQUIREDSEQUENCES = (manage_logs.LoggedDischarge,)
    RESULTSEQUENCES = (manage_fluxes.Demand,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess

        q: float = log.loggeddischarge
        q0: float = con.dischargemin
        q1: float = con.dischargemax
        if q1 > q0:
            flu.demand = q0 * min(max(1.0 - (q - q0) / (q1 - q0), 0.0), 1.0)
        elif q < q0:
            flu.demand = q0
        else:
            flu.demand = 0.0



class Calc_Request_V1(modeltools.Method):
    """ToDo"""

    CONTROLPARAMETERS = (
        manage_control.NmbSources,
        manage_control.Active,
        manage_control.VolumeMin,
        manage_control.VolumeMax,
        manage_control.ReleaseMax,
    )
    DERIVEDPARAMETERS = (
        manage_derived.Adjacency,  # ToDo: remove
        manage_derived.Seconds,
        manage_derived.NmbActiveSources,
    )
    REQUIREDSEQUENCES = (manage_fluxes.Demand, manage_receivers.WaterVolume)
    RESULTSEQUENCES = (manage_fluxes.Request,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        rec = model.sequences.receivers.fastaccess
        flu = model.sequences.fluxes.fastaccess

        if flu.demand <= 0.0:

            for i in range(con.nmbsources):
                flu.request[i] = 0.0

        else:

            v2q: float = 1e6 / der.seconds
            available: float = 0.0
            for i in range(con.nmbsources):
                if con.active[i] and der.adjacency[i, 0]:
                    available += min(
                        v2q * max(rec.watervolume[i] - con.volumemin[i], 0.0),
                        con.releasemax[i],
                    )
            if available <= 0.0:
                factor: float = 0.0
            else:
                factor = min(flu.demand / available, 1.0)
            for i in range(con.nmbsources):
                if der.adjacency[i, 0]:
                    if con.active[i]:
                        flu.request[i] = factor * min(
                            v2q * max(rec.watervolume[i] - con.volumemin[i], 0.0),
                            con.releasemax[i],
                        )
                    else:
                        flu.request[i] = 0.0

            for j in range(con.nmbsources):
                if con.active[j]:
                    demand: float = v2q * max(
                        con.volumemax[j] - rec.watervolume[j], 0.0
                    )
                else:
                    demand = 0.0
                if demand > 0.0:
                    available = 0.0
                    for i in range(con.nmbsources):
                        if con.active[i] and der.adjacency[i, j + 1]:
                            available += min(
                                v2q * max(rec.watervolume[i] - con.volumemin[i], 0.0),
                                con.releasemax[i],
                            )
                    if available <= 0.0:
                        factor = 0.0
                    else:
                        factor = min(demand / available, 1.0)
                else:
                    factor = 0.0
                for i in range(con.nmbsources):
                    if der.adjacency[i, j + 1]:
                        if con.active[i]:
                            flu.request[i] = factor * (
                                min(
                                    v2q
                                    * max(rec.watervolume[i] - con.volumemin[i], 0.0),
                                    con.releasemax[i],
                                )
                            )
                        else:
                            flu.request[i] = 0.0


class Pass_Request_V1(modeltools.Method):
    """ToDo"""

    CONTROLPARAMETERS = (manage_control.NmbSources,)
    REQUIREDSEQUENCES = (manage_fluxes.Request,)
    RESULTSEQUENCES = (manage_senders.Request,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sen = model.sequences.senders.fastaccess
        for i in range(con.nmbsources):
            sen.request[i] = flu.request[i]


class Model(modeltools.AdHocModel):
    DOCNAME = modeltools.DocName(
        short="Manage-LWC", description="low water control management model"
    )
    __HYDPY_ROOTMODEL__ = True

    INLET_METHODS = ()
    OBSERVER_METHODS = ()
    RECEIVER_METHODS = (Pick_LoggedDischarge_V1, Pick_LoggedWaterVolume_V1)
    RUN_METHODS = (Calc_Demand_V1, Calc_Request_V1)
    ADD_METHODS = ()
    OUTLET_METHODS = ()
    SENDER_METHODS = (Pass_Request_V1,)
    SUBMODELINTERFACES = ()
    SUBMODELS = ()
