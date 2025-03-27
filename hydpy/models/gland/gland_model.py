# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import importtools
from hydpy.core import modeltools
from hydpy.core.typingtools import *
from hydpy.cythons import modelutils
from hydpy.interfaces import petinterfaces
from hydpy.interfaces import rconcinterfaces

# ...from gland
from hydpy.models.gland import gland_control
from hydpy.models.gland import gland_derived
from hydpy.models.gland import gland_inputs
from hydpy.models.gland import gland_fluxes
from hydpy.models.gland import gland_states
from hydpy.models.gland import gland_outlets


class Calc_E_PETModel_V1(modeltools.Method):
    """Let a submodel that conforms to the |PETModel_V1| interface calculate the
    potential evapotranspiration.

    Example:

        We use |evap_ret_tw2002| as an example:

        >>> from hydpy.models.gland_gr4 import *
        >>> parameterstep()
        >>> from hydpy import prepare_model
        >>> area(50.0)
        >>> with model.add_petmodel_v1("evap_ret_tw2002"):
        ...     hrualtitude(200.0)
        ...     coastfactor(0.6)
        ...     evapotranspirationfactor(1.1)
        ...     with model.add_radiationmodel_v2("meteo_glob_io"):
        ...         inputs.globalradiation = 200.0
        ...     with model.add_tempmodel_v2("meteo_temp_io"):
        ...         temperatureaddend(1.0)
        ...         inputs.temperature = 14.0
        >>> model.calc_e_v1()
        >>> fluxes.e
        e(3.07171)
    """

    RESULTSEQUENCES = (gland_fluxes.E,)

    @staticmethod
    def __call__(model: modeltools.Model, submodel: petinterfaces.PETModel_V1) -> None:
        flu = model.sequences.fluxes.fastaccess
        submodel.determine_potentialevapotranspiration()
        flu.e = submodel.get_potentialevapotranspiration(0)


class Calc_E_V1(modeltools.Method):
    """Let a submodel that conforms to the |PETModel_V1| interface calculate the
    potential evapotranspiration."""

    SUBMODELINTERFACES = (petinterfaces.PETModel_V1,)
    SUBMETHODS = (Calc_E_PETModel_V1,)
    RESULTSEQUENCES = (gland_fluxes.E,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        if model.petmodel_typeid == 1:
            model.calc_e_petmodel_v1(cast(petinterfaces.PETModel_V1, model.petmodel))


class Calc_EI_V1(modeltools.Method):
    r"""Calculate the actual evaporation from the interception store.

    Basic equation:

      :math:`EI = min(E, \, I + P)`

    Examples:

        >>> from hydpy.models.gland import *
        >>> parameterstep()

        >>> inputs.p = 1.0
        >>> fluxes.e = 0.5
        >>> states.i = 0.0
        >>> model.calc_ei_v1()
        >>> fluxes.ei
        ei(0.5)

        >>> inputs.p = 0.5
        >>> fluxes.e = 1.0
        >>> states.i = 0.2
        >>> model.calc_ei_v1()
        >>> fluxes.ei
        ei(0.7)
    """

    REQUIREDSEQUENCES = (gland_inputs.P, gland_fluxes.E, gland_states.I)
    RESULTSEQUENCES = (gland_fluxes.EI,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        flu.ei = min(flu.e, sta.i + inp.p)


class Calc_PN_V1(modeltools.Method):
    r"""Calculate the net precipitation by considering all interception losses.

    Basic equation:

      :math:`PN = max(P - (IMax - I) - EI, \, 0)`

    Examples:
        >>> from hydpy.models.gland import *
        >>> parameterstep()
        >>> control.imax(10.0)
        >>> inputs.p = 1.0
        >>> states.i = 5.0
        >>> fluxes.ei = 2.0
        >>> model.calc_pn_v1()
        >>> fluxes.pn
        pn(0.0)

        >>> inputs.p = 8.0
        >>> model.calc_pn_v1()
        >>> fluxes.pn
        pn(1.0)
    """

    CONTROLPARAMETERS = (gland_control.IMax,)
    REQUIREDSEQUENCES = (gland_inputs.P, gland_fluxes.EI, gland_states.I)
    RESULTSEQUENCES = (gland_fluxes.PN,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        flu.pn = max(inp.p - (con.imax - sta.i) - flu.ei, 0.0)


class Calc_EN_V1(modeltools.Method):
    r"""Calculate the net evapotranspiration capacity by considering interception
    evaporation.

    Basic equation:

      :math:`EN = max(E - EI, \, 0.0)`

    Examples:

        >>> from hydpy.models.gland import *
        >>> parameterstep()

        >>> fluxes.e = 1.0
        >>> fluxes.ei = 2.0
        >>> model.calc_en_v1()
        >>> fluxes.en
        en(0.0)

        >>> fluxes.e = 3.0
        >>> model.calc_en_v1()
        >>> fluxes.en
        en(1.0)
    """

    REQUIREDSEQUENCES = (gland_fluxes.E, gland_fluxes.EI)
    RESULTSEQUENCES = (gland_fluxes.EN,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.en = max(flu.e - flu.ei, 0.0)


class Update_I_V1(modeltools.Method):
    """Update the interception store based on precipitation, net precipitation, and
    interception evaporation.

    Basic equation:

      :math:`I_{new} = I_{old} + P - PN - EI`

    Example:

        >>> from hydpy.models.gland import *
        >>> parameterstep("1d")
        >>> states.i = 10.0
        >>> inputs.p = 5.0
        >>> fluxes.ei = 4.0
        >>> fluxes.pn = 3.0
        >>> model.update_i_v1()
        >>> states.i
        i(8.0)
    """

    REQUIREDSEQUENCES = (gland_inputs.P, gland_fluxes.PN, gland_fluxes.EI)
    UPDATEDSEQUENCES = (gland_states.I,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        sta.i += inp.p - flu.ei - flu.pn


class Calc_PS_V1(modeltools.Method):
    r"""Calculate the part of net precipitation filling the production store.

    Basic equation:

      :math:`PS = \frac{
      X1 \cdot \left( 1 - \left( \frac{S}{X1} \right)^2 \right)
      \cdot tanh \left( \frac{PN}{X1} \right)}
      {1 + \frac{S}{X1} \cdot tanh \left( \frac{PN}{X1} \right)}`

    Examples:

        If the production store is full, no more precipitation can enter it:

        >>> from hydpy.models.gland import *
        >>> from hydpy import pub
        >>> parameterstep()
        >>> x1(300.0)
        >>> states.s = 300.0
        >>> fluxes.pn = 50.0
        >>> model.calc_ps_v1()
        >>> fluxes.ps
        ps(0.0)

        If the production store is empty, nearly all net precipitation enters it:

        >>> states.s = 0.0
        >>> model.calc_ps_v1()
        >>> fluxes.ps
        ps(49.542124)

        If net precipitation is zero, there can be no inflow into the production store:

        >>> fluxes.pn = 0.0
        >>> model.calc_ps_v1()
        >>> fluxes.ps
        ps(0.0)
    """

    CONTROLPARAMETERS = (gland_control.X1,)
    REQUIREDSEQUENCES = (gland_fluxes.PN, gland_states.S)
    RESULTSEQUENCES = (gland_fluxes.PS,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess

        flu.ps = (
            con.x1
            * (1.0 - (sta.s / con.x1) ** 2.0)
            * modelutils.tanh(flu.pn / con.x1)
            / (1.0 + sta.s / con.x1 * modelutils.tanh(flu.pn / con.x1))
        )


class Calc_ES_V1(modeltools.Method):
    r"""Calculate the actual evapotranspiration from the production store.

    Basic equation:

      .. math ::
        Es = \frac{S \cdot (2 - r) \cdot t}{1 + (1 - r) \cdot t} \\
        t = tanh \left( EN / X1 \right) \\
        r = S / X1

    Examples:

        If the production store is nearly full, actual and potential evapotranspiration
        are almost equal:

        >>> from hydpy.models.gland import *
        >>> parameterstep()
        >>> x1(300.0)
        >>> states.s = 270.0
        >>> fluxes.en = 2.0
        >>> model.calc_es_v1()
        >>> fluxes.es
        es(1.978652)

        If the production store is nearly empty, actual evapotranspiration is almost
        zero:

        >>> states.s = 10.0
        >>> model.calc_es_v1()
        >>> fluxes.es
        es(0.13027)
    """

    CONTROLPARAMETERS = (gland_control.X1,)
    REQUIREDSEQUENCES = (gland_fluxes.EN, gland_states.S)
    RESULTSEQUENCES = (gland_fluxes.ES,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess

        rs: float = sta.s / con.x1
        re: float = flu.en / con.x1
        tre: float = modelutils.tanh(re)  # equals (exp(2 * re) - 1) / (exp(2 * re) + 1)
        flu.es = (sta.s * (2.0 - rs) * tre) / (1.0 + (1.0 - rs) * tre)


class Update_S_V1(modeltools.Method):
    """Update the production store by adding precipitation and evapotranspiration.

    Basic equation:

      :math:`S_{new} = S_{old} + PS - ES`

    Examples:

        >>> from hydpy.models.gland import *
        >>> parameterstep()
        >>> x1(300.0)
        >>> fluxes.ps = 10.0
        >>> fluxes.es = 3.0
        >>> states.s = 270.0
        >>> model.update_s_v1()
        >>> states.s
        s(277.0)
    """

    REQUIREDSEQUENCES = (gland_fluxes.PS, gland_fluxes.ES)
    UPDATEDSEQUENCES = (gland_states.S,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        sta.s += flu.ps - flu.es


class Calc_Perc_V1(modeltools.Method):
    r"""Calculate the percolation from the production store.

    Basic equation:

      :math:`Perc = S \cdot \left(
      1 - \left(1 + \left(\frac{S}{Beta \cdot X1} \right)^4 \right)^{-1/4} \right)`

    Examples:

        >>> from hydpy.models.gland import *
        >>> simulationstep("1d")
        >>> parameterstep()
        >>> derived.beta.update()

        >>> x1(300.0)
        >>> states.s = 268.0
        >>> model.calc_perc_v1()
        >>> fluxes.perc
        perc(1.639555)

        >>> states.s = 50.0
        >>> model.calc_perc_v1()
        >>> fluxes.perc
        perc(0.000376)
    """

    CONTROLPARAMETERS = (gland_control.X1,)
    DERIVEDPARAMETERS = (gland_derived.Beta,)
    UPDATEDSEQUENCES = (gland_states.S,)
    RESULTSEQUENCES = (gland_fluxes.Perc,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        flu.perc = sta.s * (1.0 - (1.0 + (sta.s / con.x1 / der.beta) ** 4.0) ** -0.25)


class Update_S_V2(modeltools.Method):
    """Update the production store by subtracting percolation.

    Basic equation:

      :math:`S_{new} = S_{old} - Perc`

    Examples:

        >>> from hydpy.models.gland import *
        >>> parameterstep()
        >>> fluxes.perc = 2.0
        >>> states.s = 20.0
        >>> model.update_s_v2()
        >>> states.s
        s(18.0)
    """

    REQUIREDSEQUENCES = (gland_fluxes.Perc,)
    UPDATEDSEQUENCES = (gland_states.S,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        sta.s -= flu.perc


class Calc_AE_V1(modeltools.Method):
    """Calculate the total actual evapotranspiration.

    Basic equation:

      :math:`AE = EI + ES`

    Examples:

        >>> from hydpy.models.gland import *
        >>> parameterstep()
        >>> fluxes.ei = 2.0
        >>> fluxes.es = 1.0
        >>> model.calc_ae_v1()
        >>> fluxes.ae
        ae(3.0)
    """

    REQUIREDSEQUENCES = (gland_fluxes.EI, gland_fluxes.ES)
    RESULTSEQUENCES = (gland_fluxes.AE,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.ae = flu.ei + flu.es


class Calc_Pr_V1(modeltools.Method):
    """Calculate the total inflow into the runoff concentration module.

    Basic equation:

      :math:`PR = Perc + (PN - PS)`

    Example:

        >>> from hydpy.models.gland import *
        >>> parameterstep()
        >>> fluxes.perc = 1.0
        >>> fluxes.pn = 5.0
        >>> fluxes.ps = 2.0
        >>> model.calc_pr_v1()
        >>> fluxes.pr
        pr(4.0)
    """

    REQUIREDSEQUENCES = (gland_fluxes.PS, gland_fluxes.PN, gland_fluxes.Perc)
    RESULTSEQUENCES = (gland_fluxes.PR,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.pr = flu.perc + flu.pn - flu.ps


class Calc_PR1_PR9_V1(modeltools.Method):
    r"""Split |PR| into |PR1| and |PR9|.

    Basic equations:

      :math:`PR9 = 0.9 \cdot PR`

      :math:`PR1 = 0.1 \cdot PR`

    Examples:

        >>> from hydpy.models.gland import *
        >>> parameterstep()
        >>> fluxes.pr = 10.0
        >>> model.calc_pr1_pr9_v1()
        >>> fluxes.pr9
        pr9(9.0)
        >>> fluxes.pr1
        pr1(1.0)
    """

    REQUIREDSEQUENCES = (gland_fluxes.PR,)
    RESULTSEQUENCES = (gland_fluxes.PR9, gland_fluxes.PR1)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.pr9 = 0.9 * flu.pr
        flu.pr1 = 0.1 * flu.pr


class Calc_Q_RConcModel_V1(modeltools.Method):
    """Let a submodel that follows the |RConcModel_V1| submodel interface perform
    runoff concentration."""

    @staticmethod
    def __call__(
        model: modeltools.Model, submodel: rconcinterfaces.RConcModel_V1, inflow: float
    ) -> float:
        submodel.set_inflow(inflow)
        submodel.determine_outflow()
        return submodel.get_outflow()


class Calc_Q9_V1(modeltools.Method):
    """Transform |PR9| into |Q9|.

    Examples:

        Without a `rconcmodel_routingstore` submodel, |Calc_Q9_V1| directs |PR9|
        instantaneously to |Q9|:

        >>> from hydpy.models.gland_gr4 import *
        >>> simulationstep("1d")
        >>> parameterstep("1d")
        >>> fluxes.pr9 = 1.0
        >>> model.calc_q9_v1()
        >>> fluxes.q9
        q9(1.0)

        For a GR-compatible calculation of runoff concentration, you can select the
        Unit Hydrograph submodel |rconc_uh| and configure its ordinates via the
        `gr_uh1` option:

        >>> with model.add_rconcmodel_routingstore_v1("rconc_uh"):
        ...     uh("gr_uh1", x4=3.0)
        ...     logs.quh = 1.0, 3.0, 0.0
        >>> fluxes.pr9 = 2.0
        >>> model.calc_q9_v1()
        >>> fluxes.q9
        q9(1.1283)
    """

    SUBMODELINTERFACES = (rconcinterfaces.RConcModel_V1,)
    SUBMETHODS = (Calc_Q_RConcModel_V1,)
    REQUIREDSEQUENCES = (gland_fluxes.PR9,)
    RESULTSEQUENCES = (gland_fluxes.Q9,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        if model.rconcmodel_routingstore is None:
            flu.q9 = flu.pr9
        elif model.rconcmodel_routingstore_typeid == 1:
            flu.q9 = model.calc_q_rconcmodel_v1(
                cast(rconcinterfaces.RConcModel_V1, model.rconcmodel_routingstore),
                flu.pr9,
            )


class Calc_Q1_V1(modeltools.Method):
    """Transform |PR1| into |Q1|.

    Examples:

        Without a `rconcmodel_directflow` submodel, |Calc_Q1_V1| directs |PR1|
        instantaneously to |Q1|:

        >>> from hydpy.models.gland_gr4 import *
        >>> simulationstep("1d")
        >>> parameterstep("1d")
        >>> fluxes.pr1 = 1.0
        >>> model.calc_q1_v1()
        >>> fluxes.q1
        q1(1.0)

        For a GR-compatible calculation of runoff concentration, you can select the
        Unit Hydrograph submodel |rconc_uh| and configure its ordinates via the
        `gr_uh2` option:

        >>> with model.add_rconcmodel_directflow_v1("rconc_uh"):
        ...     uh("gr_uh2", x4=1.5)
        ...     logs.quh = 1.0, 3.0, 0.0
        >>> fluxes.pr1 = 2.0
        >>> model.calc_q1_v1()
        >>> fluxes.q1
        q1(1.362887)
    """

    SUBMODELINTERFACES = (rconcinterfaces.RConcModel_V1,)
    SUBMETHODS = (Calc_Q_RConcModel_V1,)
    REQUIREDSEQUENCES = (gland_fluxes.PR1,)
    RESULTSEQUENCES = (gland_fluxes.Q1,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        if model.rconcmodel_directflow is None:
            flu.q1 = flu.pr1
        elif model.rconcmodel_directflow_typeid == 1:
            flu.q1 = model.calc_q_rconcmodel_v1(
                cast(rconcinterfaces.RConcModel_V1, model.rconcmodel_directflow),
                flu.pr1,
            )


class Calc_Q10_V1(modeltools.Method):
    """Transform |PR| into |Q10|.

    Examples:

        Without a `rconcmodel` submodel, |Calc_Q10_V1| directs |PR| instantaneously to
        |Q10|:

        >>> from hydpy.models.gland_gr5 import *
        >>> simulationstep("1d")
        >>> parameterstep("1d")
        >>> fluxes.pr = 1.0
        >>> model.calc_q10_v1()
        >>> fluxes.q10
        q10(1.0)

        For a GR-compatible calculation of runoff concentration, you can select the
        Unit Hydrograph submodel |rconc_uh| and configure its ordinates via the
        `gr_uh2` option:

        >>> with model.add_rconcmodel_v1("rconc_uh"):
        ...     uh("gr_uh2", x4=1.5)
        ...     logs.quh = 1.0, 3.0, 0.0
        >>> fluxes.pr = 2.0
        >>> model.calc_q10_v1()
        >>> fluxes.q10
        q10(1.362887)
    """

    SUBMODELINTERFACES = (rconcinterfaces.RConcModel_V1,)
    SUBMETHODS = (Calc_Q_RConcModel_V1,)
    REQUIREDSEQUENCES = (gland_fluxes.PR,)
    RESULTSEQUENCES = (gland_fluxes.Q10,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        if model.rconcmodel is None:
            flu.q10 = flu.pr
        elif model.rconcmodel_typeid == 1:
            flu.q10 = model.calc_q_rconcmodel_v1(
                cast(rconcinterfaces.RConcModel_V1, model.rconcmodel), flu.pr
            )


class Calc_Q1_Q9_V2(modeltools.Method):
    r"""Calculate |Q1| and |Q9| by splitting |Q10|.

    Basic equations:

      :math:`Q9 = 0.9 \cdot Q10`

      :math:`Q1 = 0.1 \cdot Q10`

    Example:

        >>> from hydpy.models.gland import *
        >>> parameterstep()
        >>> fluxes.q10 = 10.0
        >>> model.calc_q1_q9_v2()
        >>> fluxes.q1
        q1(1.0)
        >>> fluxes.q9
        q9(9.0)
    """

    REQUIREDSEQUENCES = (gland_fluxes.Q10,)
    RESULTSEQUENCES = (gland_fluxes.Q1, gland_fluxes.Q9)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.q1 = 0.1 * flu.q10
        flu.q9 = 0.9 * flu.q10


class Calc_FR_V1(modeltools.Method):
    r"""Calculate the groundwater exchange affecting the routing store according to
    GR4.

    Basic equation:

      :math:`FR = X2 \cdot \left( \frac{R}{X3} \right)^{7/2}`

    Examples:

        If the routing store is nearly full, groundwater exchange is high and close to
        |X3|:

        >>> from hydpy.models.gland import *
        >>> from hydpy import pub
        >>> simulationstep("1d")
        >>> parameterstep("1d")
        >>> x2(1.02)
        >>> x3(100.0)
        >>> states.r = 95.0
        >>> model.calc_fr_v1()
        >>> fluxes.fr
        fr(0.852379)

        If the routing store is almost empty, groundwater exchange is low and near
        zero:

        >>> states.r = 5.0
        >>> model.calc_fr_v1()
        >>> fluxes.fr
        fr(0.000029)
    """

    CONTROLPARAMETERS = (gland_control.X2, gland_control.X3)
    REQUIREDSEQUENCES = (gland_states.R,)
    RESULTSEQUENCES = (gland_fluxes.FR,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        flu.fr = con.x2 * (sta.r / con.x3) ** 3.5


class Calc_FR_V2(modeltools.Method):
    r"""Calculate the groundwater exchange affecting the routing store according to
    GR5 and GR6.

    Basic equation:

      :math:`FR = X2 \cdot \left( \frac{R}{X3} - X5 \right)`

    Example:

        >>> from hydpy.models.gland import *
        >>> simulationstep("1d")
        >>> parameterstep("1d")
        >>> x2(-0.163)
        >>> x3(100.0)
        >>> x5(0.104)
        >>> states.r = 95.0
        >>> model.calc_fr_v2()
        >>> fluxes.fr
        fr(-0.137898)
    """

    CONTROLPARAMETERS = (gland_control.X2, gland_control.X3, gland_control.X5)
    UPDATEDSEQUENCES = (gland_states.R,)
    RESULTSEQUENCES = (gland_fluxes.FR,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        flu.fr = con.x2 * (sta.r / con.x3 - con.x5)


class Update_R_V1(modeltools.Method):
    """Update the level of the non-linear routing store by adding its inflows according
    to GR4 and GR5.

    Basic equation:

      :math:`R_{new} = R_{old} + Q9 + FR`

    Examples:

        >>> from hydpy.models.gland import *
        >>> parameterstep()

        In case of sufficient content of the routing store, the basic equation applies
        without modification:

        >>> states.r = 4.0
        >>> fluxes.q9 = 1.0
        >>> fluxes.fr = -2.0
        >>> model.update_r_v1()
        >>> states.r
        r(3.0)
        >>> fluxes.fr
        fr(-2.0)

        For insufficient content, groundwater loss (negative groundwater exchange)
        becomes restricted:

        >>> fluxes.fr = -5.0
        >>> model.update_r_v1()
        >>> states.r
        r(0.0)
        >>> fluxes.fr
        fr(-4.0)
    """

    REQUIREDSEQUENCES = (gland_fluxes.Q9, gland_fluxes.FR)
    UPDATEDSEQUENCES = (gland_states.R,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        sta.r += flu.q9 + flu.fr
        if sta.r < 0.0:
            flu.fr -= sta.r
            sta.r = 0.0


class Update_R_V2(modeltools.Method):
    r"""Update the level of the non-linear routing store by adding its inflows
    according to GR6.

    Basic equation:

      :math:`R_{new} = R_{old} + 0.6 \cdot Q9 + FR`

    Examples:

        >>> from hydpy.models.gland import *
        >>> from hydpy import pub
        >>> parameterstep()

        In case of sufficient content of the routing store, the basic equation applies
        without modification:

        >>> states.r = 4.0
        >>> fluxes.q9 = 1.0 / 0.6
        >>> fluxes.fr = -2.0
        >>> model.update_r_v2()
        >>> states.r
        r(3.0)
        >>> fluxes.fr
        fr(-2.0)

        For insufficient content, groundwater loss (negative groundwater exchange)
        becomes restricted:

        >>> fluxes.fr = -5.0
        >>> model.update_r_v2()
        >>> states.r
        r(0.0)
        >>> fluxes.fr
        fr(-4.0)
    """

    REQUIREDSEQUENCES = (gland_fluxes.Q9, gland_fluxes.FR)
    UPDATEDSEQUENCES = (gland_states.R,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        sta.r += 0.6 * flu.q9 + flu.fr
        if sta.r < 0.0:
            flu.fr -= sta.r
            sta.r = 0.0


class Calc_QR_V1(modeltools.Method):
    r"""Calculate the outflow of the routing store.

    Basic equation:

      :math:`QR = R \cdot \left( 1 - \left[1 + \left( \frac{R}{X3} \right)^{4}
      \right]^{-1/4} \right)`

    Example:

        >>> from hydpy.models.gland import *
        >>> from hydpy import pub
        >>> parameterstep("1d")
        >>> simulationstep("1d")
        >>> x3(100.0)
        >>> states.r = 115.852379
        >>> model.calc_qr_v1()
        >>> fluxes.qr
        qr(26.30361)
    """

    CONTROLPARAMETERS = (gland_control.X3,)
    REQUIREDSEQUENCES = (gland_states.R,)
    RESULTSEQUENCES = (gland_fluxes.QR,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        flu.qr = sta.r * (1.0 - (1.0 + (sta.r / con.x3) ** 4.0) ** -0.25)


class Update_R_V3(modeltools.Method):
    """Update the non-linear routing store by subtracting its outflow.

    Basic equation:

      :math:`R_{new} = R_{old} - QR`

    Example:

        >>> from hydpy.models.gland import *
        >>> parameterstep()
        >>> fluxes.qr = 2.0
        >>> states.r = 20.0
        >>> model.update_r_v3()
        >>> states.r
        r(18.0)
    """

    REQUIREDSEQUENCES = (gland_fluxes.QR,)
    UPDATEDSEQUENCES = (gland_states.R,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        sta.r -= flu.qr


class Calc_FR2_V1(modeltools.Method):
    r"""Calculate the groundwater exchange affecting the exponential routing store.

    Basic equation:

      :math:`FR2 = FR`

    Examples:

        >>> from hydpy.models.gland import *
        >>> parameterstep()
        >>> fluxes.fr = -0.5
        >>> model.calc_fr2_v1()
        >>> fluxes.fr2
        fr2(-0.5)
    """

    REQUIREDSEQUENCES = (gland_fluxes.FR,)
    RESULTSEQUENCES = (gland_fluxes.FR2,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.fr2 = flu.fr


class Update_R2_V1(modeltools.Method):
    r"""Update the exponential routing store by adding its inflows.

    Basic equation:

      :math:`R2_{new} = R2_{new} + 0.4 \cdot Q9 + FR2`

    Examples:

        >>> from hydpy.models.gland import *
        >>> parameterstep()
        >>> fluxes.q9 = 10.0
        >>> fluxes.fr2 = -0.5
        >>> states.r2 = 40.0
        >>> model.update_r2_v1()
        >>> states.r2
        r2(43.5)
    """

    REQUIREDSEQUENCES = (gland_fluxes.Q9, gland_fluxes.FR2)
    UPDATEDSEQUENCES = (gland_states.R2,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        sta.r2 += 0.4 * flu.q9 + flu.fr2


class Calc_QR2_R2_V1(modeltools.Method):
    r"""Calculate the outflow of the exponential routing store and update its content.

    Basic equations:

      .. math::
        QR = \begin{cases}
        X6 \cdot exp(ar) &|\ ar < -7
        \\
        X6 \cdot log(exp(ar) + 1) &|\ -7 \leq ar \leq 7
        \\
        R2 + X6 / exp(ar) &|\ ar > 7
        \end{cases}
        \\
        ar = min(max(R2 / X6, \, -33), \, 33)

    Examples:

        >>> from hydpy.models.gland import *
        >>> parameterstep()
        >>> x6(4.5)

        For large negative exponential store levels, its outflow is almost zero:

        >>> states.r2 = -50.0
        >>> model.calc_qr2_r2_v1()
        >>> fluxes.qr2
        qr2(0.000067)
        >>> states.r2
        r2(-50.000067)

        For exponential store levels around zero, there is a significant outflow:

        >>> states.r2 = 0.0
        >>> model.calc_qr2_r2_v1()
        >>> fluxes.qr2
        qr2(3.119162)
        >>> states.r2
        r2(-3.119162)

        For large positive exponential store levels, its outflow is highest:

        >>> states.r2 = 40.0
        >>> model.calc_qr2_r2_v1()
        >>> fluxes.qr2
        qr2(40.000621)
        >>> states.r2
        r2(-0.000621)
    """

    CONTROLPARAMETERS = (gland_control.X6,)
    UPDATEDSEQUENCES = (gland_states.R2,)
    RESULTSEQUENCES = (gland_fluxes.QR2,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess

        ar: float = min(max(sta.r2 / con.x6, -33.0), 33.0)

        if ar < -7.0:
            flu.qr2 = con.x6 * modelutils.exp(ar)
        elif ar <= 7.0:
            flu.qr2 = con.x6 * modelutils.log(modelutils.exp(ar) + 1.0)
        else:
            flu.qr2 = sta.r2 + con.x6 / modelutils.exp(ar)

        sta.r2 -= flu.qr2


class Calc_FD_V1(modeltools.Method):
    r"""Calculate the groundwater exchange affecting the direct runoff.

    Basic equation:

      .. math::
        FD = \begin{cases}
        - Q1 &|\ (Q1 + FR) \leq 0
        \\
        FR &|\ (Q1 + FR) > 0
        \end{cases}

    Examples:

        >>> from hydpy.models.gland import *
        >>> parameterstep()

        >>> fluxes.q1 = 10.0
        >>> fluxes.fr = -0.5
        >>> model.calc_fd_v1()
        >>> fluxes.fd
        fd(-0.5)

        >>> fluxes.q1 = 1.0
        >>> fluxes.fr = -1.5
        >>> model.calc_fd_v1()
        >>> fluxes.fd
        fd(-1.0)
    """

    REQUIREDSEQUENCES = (gland_fluxes.Q1, gland_fluxes.FR)
    RESULTSEQUENCES = (gland_fluxes.FD,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        if (flu.q1 + flu.fr) <= 0.0:
            flu.fd = -flu.q1
        else:
            flu.fd = flu.fr


class Calc_QD_V1(modeltools.Method):
    r"""Calculate the direct runoff.

    Basic equation:

      :math:`QD = max(Q1 + FD, \, 0)`

    Examples:

        >>> from hydpy.models.gland import *
        >>> parameterstep()
        >>> fluxes.q1 = 2.0

        >>> fluxes.fd = -1.0
        >>> model.calc_qd_v1()
        >>> fluxes.qd
        qd(1.0)

        >>> fluxes.fd = -3.0
        >>> model.calc_qd_v1()
        >>> fluxes.qd
        qd(0.0)
    """

    REQUIREDSEQUENCES = (gland_fluxes.Q1, gland_fluxes.FD)
    RESULTSEQUENCES = (gland_fluxes.QD,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.qd = max(flu.q1 + flu.fd, 0.0)


class Calc_QH_V1(modeltools.Method):
    """Calculate the total runoff according to GR4 and GR5.

    Basic equation:

      :math:`QH = QR + QD`

    Example:

        >>> from hydpy.models.gland import *
        >>> parameterstep()
        >>> fluxes.qr = 2.0
        >>> fluxes.qd = 1.0
        >>> model.calc_qh_v1()
        >>> fluxes.qh
        qh(3.0)
    """

    REQUIREDSEQUENCES = (gland_fluxes.QR, gland_fluxes.QD)
    RESULTSEQUENCES = (gland_fluxes.QH,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.qh = flu.qr + flu.qd


class Calc_QH_V2(modeltools.Method):
    """Calculate the total runoff according to GR6.

    Basic equation:

      :math:`QH = QR + QR2 + QD`

    Example:

        >>> from hydpy.models.gland import *
        >>> parameterstep()
        >>> fluxes.qr = 1.0
        >>> fluxes.qr2 = 2.0
        >>> fluxes.qd = 3.0
        >>> model.calc_qh_v2()
        >>> fluxes.qh
        qh(6.0)
    """

    REQUIREDSEQUENCES = (gland_fluxes.QR, gland_fluxes.QR2, gland_fluxes.QD)
    RESULTSEQUENCES = (gland_fluxes.QH,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.qh = flu.qr + flu.qr2 + flu.qd


class Calc_QV_V1(modeltools.Method):
    r"""Calculate total discharge in m³/s.

    Basic equation:

      :math:`QV = QFactor \cdot QH`

    Example:

        >>> from hydpy.models.gland import *
        >>> parameterstep()
        >>> derived.qfactor(2.0)
        >>> fluxes.qh = 3.0
        >>> model.calc_qv_v1()
        >>> fluxes.qv
        qv(6.0)
    """

    DERIVEDPARAMETERS = (gland_derived.QFactor,)
    REQUIREDSEQUENCES = (gland_fluxes.QH,)
    RESULTSEQUENCES = (gland_fluxes.QV,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.qv = flu.qh * der.qfactor


class Pass_Q_V1(modeltools.Method):
    """Update the outlet link sequence.

    Basic equation:

      :math:`Q = QV`

    Example:

        >>> from hydpy.models.gland import *
        >>> parameterstep()
        >>> fluxes.qv = 2.0
        >>> model.pass_q_v1()
        >>> outlets.q
        q(2.0)
    """

    REQUIREDSEQUENCES = (gland_fluxes.QV,)
    RESULTSEQUENCES = (gland_outlets.Q,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        out = model.sequences.outlets.fastaccess
        out.q = flu.qv


class Model(modeltools.AdHocModel):
    """|gland.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(short="G")
    __HYDPY_ROOTMODEL__ = None

    INLET_METHODS = (Calc_E_V1,)
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        Calc_EI_V1,
        Calc_PN_V1,
        Calc_EN_V1,
        Update_I_V1,
        Calc_PS_V1,
        Calc_ES_V1,
        Update_S_V1,
        Calc_Perc_V1,
        Update_S_V2,
        Calc_AE_V1,
        Calc_Pr_V1,
        Calc_PR1_PR9_V1,
        Calc_Q9_V1,
        Calc_Q1_V1,
        Calc_Q10_V1,
        Calc_Q1_Q9_V2,
        Calc_FR_V1,
        Calc_FR_V2,
        Update_R_V1,
        Update_R_V3,
        Update_R_V2,
        Calc_QR_V1,
        Update_R_V3,
        Calc_FR2_V1,
        Update_R2_V1,
        Calc_QR2_R2_V1,
        Update_R_V2,
        Calc_FD_V1,
        Calc_QD_V1,
        Calc_QH_V1,
        Calc_QH_V2,
        Calc_QV_V1,
    )
    ADD_METHODS = (Calc_E_PETModel_V1, Calc_Q_RConcModel_V1)
    OUTLET_METHODS = (Pass_Q_V1,)
    SENDER_METHODS = ()
    SUBMODELINTERFACES = (petinterfaces.PETModel_V1, rconcinterfaces.RConcModel_V1)
    SUBMODELS = ()

    petmodel = modeltools.SubmodelProperty(petinterfaces.PETModel_V1)
    petmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    petmodel_typeid = modeltools.SubmodelTypeIDProperty()

    rconcmodel = modeltools.SubmodelProperty(rconcinterfaces.RConcModel_V1)
    rconcmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    rconcmodel_typeid = modeltools.SubmodelTypeIDProperty()

    rconcmodel_directflow = modeltools.SubmodelProperty(rconcinterfaces.RConcModel_V1)
    rconcmodel_directflow_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    rconcmodel_directflow_typeid = modeltools.SubmodelTypeIDProperty()

    rconcmodel_routingstore = modeltools.SubmodelProperty(rconcinterfaces.RConcModel_V1)
    rconcmodel_routingstore_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    rconcmodel_routingstore_typeid = modeltools.SubmodelTypeIDProperty()


class Main_PETModel_V1(modeltools.AdHocModel):
    """Base class for |gland.DOCNAME.long| models that use submodels that comply with
    the |PETModel_V1| interface."""

    petmodel: modeltools.SubmodelProperty
    petmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    petmodel_typeid = modeltools.SubmodelTypeIDProperty()

    @importtools.prepare_submodel(
        "petmodel",
        petinterfaces.PETModel_V1,
        petinterfaces.PETModel_V1.prepare_nmbzones,
        petinterfaces.PETModel_V1.prepare_subareas,
    )
    def add_petmodel_v1(
        self,
        petmodel: petinterfaces.PETModel_V1,
        /,
        *,
        refresh: bool,  # pylint: disable=unused-argument
    ) -> None:
        """Initialise the given `petmodel` that follows the |PETModel_V1| interface.

        >>> from hydpy.models.gland_gr4 import *
        >>> parameterstep()
        >>> area(5.0)
        >>> with model.add_petmodel_v1("evap_ret_tw2002"):
        ...     nmbhru
        ...     hruarea
        ...     evapotranspirationfactor(1.5)
        nmbhru(1)
        hruarea(5.0)

        >>> etf = model.petmodel.parameters.control.evapotranspirationfactor
        >>> etf
        evapotranspirationfactor(1.5)
        """
        control = self.parameters.control
        petmodel.prepare_nmbzones(1)
        petmodel.prepare_subareas(control.area.value)


class Main_RConcModel_V1(modeltools.AdHocModel):
    """Base class for |gland.DOCNAME.long| models that use a single submodel that
    complies with the |RConcModel_V1| interface."""

    rconcmodel: modeltools.SubmodelProperty
    rconcmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    rconcmodel_typeid = modeltools.SubmodelTypeIDProperty()

    @importtools.prepare_submodel("rconcmodel", rconcinterfaces.RConcModel_V1)
    def add_rconcmodel_v1(
        self, rconcmodel: rconcinterfaces.RConcModel_V1, /, *, refresh: bool
    ) -> None:
        """Initialise the given submodel that follows the |RConcModel_V1| interface and
        is responsible for calculating runoff concentration.

        >>> from hydpy.models.gland_gr5 import *
        >>> simulationstep("1d")
        >>> parameterstep("1d")
        >>> with model.add_rconcmodel_v1("rconc_uh"):
        ...     uh("gr_uh2", x4=3.0)
        >>> model.rconcmodel.parameters.control.uh
        uh("gr_uh2", x4=3.0)
        """

    def _get_rconcmodel_waterbalance(
        self, initial_conditions: ConditionsModel
    ) -> float:
        """Get the water balance of the single runoff concentration submodel if
        used."""
        if self.rconcmodel:
            return self.rconcmodel.get_waterbalance(
                initial_conditions["model.rconcmodel"]
            )
        return 0.0


class Main_RConcModel_V2(modeltools.AdHocModel):
    """Base class for |gland.DOCNAME.long| models that use two submodels that comply
    with the |RConcModel_V1| interface."""

    rconcmodel_routingstore: modeltools.SubmodelProperty
    rconcmodel_routingstore_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    rconcmodel_routingstore_typeid = modeltools.SubmodelTypeIDProperty()

    rconcmodel_directflow: modeltools.SubmodelProperty
    rconcmodel_directflow_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    rconcmodel_directflow_typeid = modeltools.SubmodelTypeIDProperty()

    @importtools.prepare_submodel(
        "rconcmodel_routingstore", rconcinterfaces.RConcModel_V1
    )
    def add_rconcmodel_routingstore_v1(
        self, rconcmodel: rconcinterfaces.RConcModel_V1, /, *, refresh: bool
    ) -> None:
        """Initialise the given submodel that follows the |RConcModel_V1| interface and
        is responsible for calculating the runoff concentration related to the routing
        store.

        >>> from hydpy.models.gland_gr4 import *
        >>> simulationstep("1d")
        >>> parameterstep("1d")
        >>> with model.add_rconcmodel_routingstore_v1("rconc_uh"):
        ...     uh("gr_uh1", x4=2.0)
        >>> model.rconcmodel_routingstore.parameters.control.uh
        uh("gr_uh1", x4=2.0)
        """

    @importtools.prepare_submodel(
        "rconcmodel_directflow", rconcinterfaces.RConcModel_V1
    )
    def add_rconcmodel_directflow_v1(
        self, rconcmodel: rconcinterfaces.RConcModel_V1, /, *, refresh: bool
    ) -> None:
        """Initialise the given submodel that follows the |RConcModel_V1| interface and
        is responsible for calculating the runoff concentration related to the direct
        runoff.

        >>> from hydpy.models.gland_gr4 import *
        >>> simulationstep("1d")
        >>> parameterstep("1d")
        >>> with model.add_rconcmodel_directflow_v1("rconc_uh"):
        ...     uh("gr_uh2", x4=3.0)
        >>> model.rconcmodel_directflow.parameters.control.uh
        uh("gr_uh2", x4=3.0)
        """

    def _get_rconcmodel_waterbalance_routingstore(
        self, initial_conditions: ConditionsModel
    ) -> float:
        r"""Get the water balance of the routing store runoff concentration submodel if
        used."""
        if self.rconcmodel_routingstore:
            return self.rconcmodel_routingstore.get_waterbalance(
                initial_conditions["model.rconcmodel_routingstore"]
            )
        return 0.0

    def _get_rconcmodel_waterbalance_directflow(
        self, initial_conditions: ConditionsModel
    ) -> float:
        r"""Get the water balance of the direct flow runoff concentration submodel if
        used."""
        if self.rconcmodel_directflow:
            return self.rconcmodel_directflow.get_waterbalance(
                initial_conditions["model.rconcmodel_directflow"]
            )
        return 0.0
