# pylint: disable=missing-module-docstring

from hydpy.core import modeltools
from hydpy.models.tm import tm_control
from hydpy.models.tm import tm_derived
from hydpy.models.tm import tm_inputs
from hydpy.models.tm import tm_fluxes
from hydpy.models.tm import tm_states
from hydpy.models.tm import tm_outlets


class Calc_PNet_V1(modeltools.Method):
    r"""Calculate the net precipitation.

    Basic equation:
      :math:`PNet = Psi \cdot P`

    Example:

        >>> from hydpy.models.tm import *
        >>> parameterstep()
        >>> psi(0.8)
        >>> inputs.p = 2.0
        >>> model.calc_pnet_v1()
        >>> fluxes.pnet
        pnet(1.6)
    """

    CONTROLPARAMETERS = (tm_control.Psi,)
    REQUIREDSEQUENCES = (tm_inputs.P,)
    RESULTSEQUENCES = (tm_fluxes.PNet,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess

        flu.pnet = con.psi * inp.p


class Update_S_V1(modeltools.Method):
    r"""Add the net precipitation to the upper-layer storage.

    Basic equation:
      :math:`S_{new} = S_{old} + PNet`

    Example:

        >>> from hydpy.models.tm import *
        >>> parameterstep()
        >>> fluxes.pnet = 2.0
        >>> states.s = 3.0
        >>> model.update_s_v1()
        >>> states.s
        s(5.0)
    """

    REQUIREDSEQUENCES = (tm_fluxes.PNet,)
    UPDATEDSEQUENCES = (tm_states.S,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess

        sta.s += flu.pnet


class Calc_Perc_QI_S_V1(modeltools.Method):
    r"""Calculate percolation and interflow and update the upper-layer storage.

    Basic equations:
      .. math::
        Perc = KPerc \cdot S_{old} \\
        QI = KU \cdot S_{old} \\
        S_{new} = S_{old} - Perc - QI

    Examples:

        >>> from hydpy.models.tm import *
        >>> simulationstep("2h")
        >>> parameterstep("1h")

        Suitable storage coefficient values:

        >>> kperc(0.1)
        >>> ku(0.3)
        >>> states.s = 2.0
        >>> model.calc_perc_qi_s_v1()
        >>> fluxes.perc
        perc(0.4)
        >>> fluxes.qi
        qi(1.2)
        >>> states.s
        s(0.4)

        Too high storage coefficient values:

        >>> ku.value = 0.9
        >>> states.s = 2.0
        >>> model.calc_perc_qi_s_v1()
        >>> fluxes.perc
        perc(0.363636)
        >>> fluxes.qi
        qi(1.636364)
        >>> states.s
        s(0.0)
    """

    CONTROLPARAMETERS = (tm_control.KPerc, tm_control.KU)
    RESULTSEQUENCES = (tm_fluxes.Perc, tm_fluxes.QI)
    UPDATEDSEQUENCES = (tm_states.S,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess

        flu.perc = con.kperc * sta.s
        flu.qi = con.ku * sta.s
        ds: float = flu.perc + flu.qi
        if ds <= sta.s:
            sta.s -= ds
        else:
            f: float = sta.s / ds
            sta.s = 0.0
            flu.perc *= f
            flu.qi *= f


class Calc_QD_S_V1(modeltools.Method):
    r"""Calculate direct runoff and update the upper-layer storage.

    Basic equations:
      .. math::
        QD = max(S_{old} - SMax, \, 0) \\
        S_{new} = S_{old} - QD

    Examples:

        >>> from hydpy.models.tm import *
        >>> parameterstep()
        >>> smax(4.0)

        Storage capacity not exceeded:

        >>> states.s = 3.0
        >>> model.calc_qd_s_v1()
        >>> fluxes.qd
        qd(0.0)
        >>> states.s
        s(3.0)

        Storage capacity exceeded:

        >>> states.s = 6.0
        >>> model.calc_qd_s_v1()
        >>> fluxes.qd
        qd(2.0)
        >>> states.s
        s(4.0)
    """

    CONTROLPARAMETERS = (tm_control.SMax,)
    RESULTSEQUENCES = (tm_fluxes.QD,)
    UPDATEDSEQUENCES = (tm_states.S,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess

        if sta.s <= con.smax:
            flu.qd = 0.0
        else:
            flu.qd = sta.s - con.smax
            sta.s = con.smax


class Update_G_V1(modeltools.Method):
    r"""Add the percolation to the lower-layer storage.

    Basic equation:
      :math:`G_{new} = G_{old} + Perc`

    Example:

        >>> from hydpy.models.tm import *
        >>> parameterstep()
        >>> fluxes.perc = 2.0
        >>> states.g = 3.0
        >>> model.update_g_v1()
        >>> states.g
        g(5.0)
    """

    REQUIREDSEQUENCES = (tm_fluxes.Perc,)
    UPDATEDSEQUENCES = (tm_states.G,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess

        sta.g += flu.perc


class Calc_QB_G_V1(modeltools.Method):
    r"""Calculate the baseflow and update the lower-layer storage.

    Basic equations:
      .. math::
        QB = KL \cdot G_{old} \\
        G_{new} = G_{old} - QB

    Example:

        >>> from hydpy.models.tm import *
        >>> simulationstep("2h")
        >>> parameterstep("1h")
        >>> kl(0.3)
        >>> states.g = 2.0
        >>> model.calc_qb_g_v1()
        >>> fluxes.qb
        qb(1.2)
        >>> states.g
        g(0.8)
    """

    CONTROLPARAMETERS = (tm_control.KL,)
    RESULTSEQUENCES = (tm_fluxes.QB,)
    UPDATEDSEQUENCES = (tm_states.G,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess

        flu.qb = con.kl * sta.g
        sta.g -= flu.qb


class Calc_QT_V1(modeltools.Method):
    r"""Calculate the total runoff height.

    Basic equations:
      :math:`QT = QB + QI + QD`

    Example:

        >>> from hydpy.models.tm import *
        >>> parameterstep()
        >>> fluxes.qb = 1.0
        >>> fluxes.qi = 2.0
        >>> fluxes.qd = 3.0
        >>> model.calc_qt_v1()
        >>> fluxes.qt
        qt(6.0)
    """

    REQUIREDSEQUENCES = (tm_fluxes.QD, tm_fluxes.QI, tm_fluxes.QB)
    RESULTSEQUENCES = (tm_fluxes.QT,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        flu = model.sequences.fluxes.fastaccess

        flu.qt = flu.qb + flu.qi + flu.qd


class Pass_Q_V1(modeltools.Method):
    r"""Calculate the catchment's discharge.

    Basic equations:
      :math:`Q = QF \cdot QT`

    Example:

        >>> from hydpy.models.tm import *
        >>> parameterstep()
        >>> derived.qf(2.0)
        >>> fluxes.qt = 3.0
        >>> model.pass_q_v1()
        >>> outlets.q
        q(6.0)
    """

    DERIVEDPARAMETERS = (tm_derived.QF,)
    REQUIREDSEQUENCES = (tm_fluxes.QT,)
    RESULTSEQUENCES = (tm_outlets.Q,)

    @staticmethod
    def __call__(model: modeltools.Model, /) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        out = model.sequences.outlets.fastaccess

        out.q = der.qf * flu.qt


class Model(modeltools.AdHocModel):
    """|tm.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(short="TM")
    __HYDPY_ROOTMODEL__ = None

    INLET_METHODS = ()
    OBSERVER_METHODS = ()
    RECEIVER_METHODS = ()
    ADD_METHODS = ()
    RUN_METHODS = (
        Calc_PNet_V1,
        Update_S_V1,
        Calc_Perc_QI_S_V1,
        Calc_QD_S_V1,
        Update_G_V1,
        Calc_QB_G_V1,
        Calc_QT_V1,
    )
    OUTLET_METHODS = (Pass_Q_V1,)
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()
