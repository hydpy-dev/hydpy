# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# imports...
# ...from HydPy
from hydpy.core import importtools
from hydpy.core import modeltools
from hydpy.core.typingtools import *
from hydpy.cythons import modelutils
from hydpy.interfaces import petinterfaces
from hydpy.interfaces import rconcinterfaces

# ...from gland
from hydpy.models.gland import gland_inputs
from hydpy.models.gland import gland_fluxes
from hydpy.models.gland import gland_control
from hydpy.models.gland import gland_states
from hydpy.models.gland import gland_outlets
from hydpy.models.gland import gland_derived


class Calc_E_PETModel_V1(modeltools.Method):
    """Let a submodel that conforms to the |PETModel_V1| interface calculate the
    potential evapotranspiration.

    Example:

        We use |evap_ret_tw2002| as an example:

        >>> from hydpy.models.gland_gr4 import *
        >>> parameterstep()
        >>> from hydpy import prepare_model
        >>> area(50.)
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
    r"""Calculate the actual evaporation rate from interception store. It is limited
    by the amount of water available and the potential evapotranspiration (|E|).

    Basic equations:

      :math:`EI = Min(E, I + P)`

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
        flu = model.sequences.fluxes.fastaccess
        inp = model.sequences.inputs.fastaccess
        sta = model.sequences.states.fastaccess
        flu.ei = min(flu.e, sta.i + inp.p)


class Calc_PN_V1(modeltools.Method):
    r"""Calculate the net precipitation by subtracting the intercepted water and the
    evaporated water from the input precipitation.

    Basic equations:

      :math:`PN = Max(0, P - (IMax - I) - EI)`

    Examples:
        >>> from hydpy.models.gland import *
        >>> parameterstep()
        >>> inputs.p = 1.0
        >>> control.imax = 10.0
        >>> states.i = 5.0
        >>> fluxes.ei = 2.0
        >>> model.calc_pn_v1()
        >>> fluxes.pn
        pn(0.0)

        >>> inputs.p = 5.0
        >>> control.imax = 10.0
        >>> states.i = 8.0
        >>> fluxes.ei = 2.0
        >>> model.calc_pn_v1()
        >>> fluxes.pn
        pn(1.0)
    """

    REQUIREDSEQUENCES = (gland_inputs.P, gland_fluxes.EI, gland_states.I)

    CONTROLPARAMETERS = (gland_control.IMax,)

    RESULTSEQUENCES = (gland_fluxes.PN,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        inp = model.sequences.inputs.fastaccess
        sta = model.sequences.states.fastaccess
        flu.pn = max(0.0, inp.p - (con.imax - sta.i) - flu.ei)


class Calc_EN_V1(modeltools.Method):
    r"""Calculate the net evaporation.

    Basic equations:

      :math:`En = Max(0, E - EI)`

    Examples:
        >>> from hydpy.models.gland import *
        >>> parameterstep()
        >>> fluxes.e = 1.0
        >>> fluxes.ei = 2.0
        >>> model.calc_en_v1()
        >>> fluxes.en
        en(0.0)

        >>> fluxes.e = 2.0
        >>> fluxes.ei = 1.0
        >>> model.calc_en_v1()
        >>> fluxes.en
        en(1.0)
    """

    REQUIREDSEQUENCES = (gland_fluxes.EI, gland_fluxes.E)

    RESULTSEQUENCES = (gland_fluxes.EN,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.en = max(0.0, flu.e - flu.ei)


class Update_I_V1(modeltools.Method):
    """Update the interception store based on net precipitation and evaporation from
    interception store.

    Basic equations:

      :math:`I_{new} = I_{old} - EI - PN`

    Examples:

        >>> from hydpy.models.gland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> states.i = 10.0
        >>> inputs.p = 5.0
        >>> fluxes.ei = 2.0
        >>> fluxes.pn = 5.
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
        sta.i = sta.i + inp.p - flu.ei - flu.pn


class Calc_PS_V1(modeltools.Method):
    r"""Calculate part of net rainfall |PN| filling the production store.

    Basic equation:

      :math:`PS = \frac{
      X1\left(1-\left(\frac{S}{X1}\right)^{2}\right ) \cdot
      tanh \left( \frac{PN }{X1} \right)}
      {1 + \frac{S}{X1}\cdot tanh \left( \frac{PN}{X1} \right)}`

    Examples:

        Production store is full, no more rain can enter the production store

        >>> from hydpy.models.gland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> x1(300)
        >>> states.s = 300
        >>> fluxes.pn = 50
        >>> model.calc_ps_v1()
        >>> fluxes.ps
        ps(0.0)

        Production store is empty, nearly all net rainfall fills the production store:

        >>> states.s = 0
        >>> model.calc_ps_v1()
        >>> fluxes.ps
        ps(49.542124)

        No net rainfall, no inflow to production store:

        >>> fluxes.pn = 0
        >>> model.calc_ps_v1()
        >>> fluxes.ps
        ps(0.0)
    """

    REQUIREDSEQUENCES = (gland_fluxes.PN, gland_states.S)
    CONTROLPARAMETERS = (gland_control.X1,)

    RESULTSEQUENCES = (gland_fluxes.PS,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        con = model.parameters.control.fastaccess

        flu.ps = (
            con.x1
            * (1.0 - (sta.s / con.x1) ** 2.0)
            * modelutils.tanh(flu.pn / con.x1)
            / (1.0 + sta.s / con.x1 * modelutils.tanh(flu.pn / con.x1))
        )


class Calc_ES_V1(modeltools.Method):
    r"""Calculate actual evaporation rate from production store.

    Basic equations:

      .. math ::
        ws = tanh\left(\frac{EN}{X1}\right), \quad sr = \frac{S}{X1} \\
        Es = \frac{S \cdot (2-sr) \cdot ws}{1+(1-sr) \cdot ws}

    Examples:

        Production store almost full, no rain: |ES| reaches almost |EN|:

        >>> from hydpy.models.gland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> x1(300.)
        >>> fluxes.en = 2.
        >>> states.s = 270.
        >>> model.calc_es_v1()
        >>> fluxes.es
        es(1.978652)

        Production store almost empty, no rain: |ES| reaches almost 0:

        >>> states.s = 10.
        >>> model.calc_es_v1()
        >>> fluxes.es
        es(0.13027)
    """

    REQUIREDSEQUENCES = (gland_fluxes.EN, gland_states.S)
    CONTROLPARAMETERS = (gland_control.X1,)

    RESULTSEQUENCES = (gland_fluxes.ES,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        con = model.parameters.control.fastaccess
        # fill level of production storage
        sr: float = sta.s / con.x1
        # relative part of net evapotranspiration to storage capacity
        ws: float = flu.en / con.x1
        tw: float = modelutils.tanh(ws)  # equals (exp(2*d_ws) - 1) / (exp(2*d_ws) + 1)
        flu.es = (sta.s * (2.0 - sr) * tw) / (1.0 + (1.0 - sr) * tw)


class Update_S_V1(modeltools.Method):
    """Update the production store based on filling and evaporation from production
    store.

    Basic equations:

      :math:`S_{new} = S_{old} - ES + PS`

    Examples:

        >>> from hydpy.models.gland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> x1(300.)
        >>> fluxes.ps = 10.
        >>> fluxes.es = 3.
        >>> states.s = 270.
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
        sta.s = sta.s - flu.es + flu.ps


class Calc_Perc_V1(modeltools.Method):
    r"""Calculate percolation from the production store. The percolation rate varies
    between 0 mm (empty storage) and 0.0095 mm |S| (completely filled storage).

    Basic equations:

      :math:`Perc = S \cdot \left(
      1 - \left(1 + \left(\frac{S}{Beta \cdot X1} \right)^4 \right)^{-1/4} \right)`

    Examples:

        >>> from hydpy.models.gland import *
        >>> simulationstep("1d")
        >>> parameterstep()

        Producion store is almost full:

        >>> x1(300.0)
        >>> derived.beta.update()
        >>> states.s = 268.0
        >>> model.calc_perc_v1()
        >>> fluxes.perc
        perc(1.639555)

        Producion store is almost empty:

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
        flu.perc = sta.s * (1.0 - (1.0 + (sta.s / con.x1 / der.beta) ** 4.0) ** (-0.25))


class Update_S_V2(modeltools.Method):
    """Update the production store according to percolation.

    Basic equations:

      :math:`S_{new} = S_{old} - Perc`

    Examples:

        >>> from hydpy.models.gland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> fluxes.perc = 1.6402
        >>> states.s = 268.021348
        >>> model.update_s_v2()
        >>> states.s
        s(266.381148)
    """

    REQUIREDSEQUENCES = (gland_fluxes.Perc,)

    UPDATEDSEQUENCES = (gland_states.S,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        sta.s = sta.s - flu.perc


class Calc_AE_V1(modeltools.Method):
    """Calculate actual evaporation |AE| (for output only).

    Basic equations:

      :math:`AE = EI + ES`

    Examples:

        >>> from hydpy.models.gland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> fluxes.ei = 8.
        >>> fluxes.es = 1.978652
        >>> model.calc_ae_v1()
        >>> fluxes.ae
        ae(9.978652)
    """

    REQUIREDSEQUENCES = (gland_fluxes.EI, gland_fluxes.ES)
    RESULTSEQUENCES = (gland_fluxes.AE,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.ae = flu.ei + flu.es


class Calc_Pr_V1(modeltools.Method):
    """Calculate total quantity |PR| of water reaching the routing functions.

    Basic equation:

      :math:`PR = Perc + (PN - PS)`

    Examples:

        Example production store almost full, no rain:

        >>> from hydpy.models.gland import *
        >>> parameterstep('1d')
        >>> fluxes.ps = 3.
        >>> fluxes.perc = 10.
        >>> fluxes.pn = 5.
        >>> model.calc_pr_v1()
        >>>
        >>> fluxes.pr
        pr(12.0)
    """

    REQUIREDSEQUENCES = (gland_fluxes.PS, gland_fluxes.PN, gland_fluxes.Perc)

    RESULTSEQUENCES = (gland_fluxes.PR,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.pr = flu.perc + flu.pn - flu.ps


class Calc_PR1_PR9_V1(modeltools.Method):
    r"""Splitting |PR| into |PR1| and |PR9|.

    Basic equations:

      :math:`PR9 = 0.9 \cdot PR`

      :math:`PR1 = PR - PR1`

    Examples:

        Example production store nearly full, no rain:

        >>> from hydpy.models.gland import *
        >>> parameterstep('1d')
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
        flu.pr1 = flu.pr - flu.pr9


class Calc_Q9_RConcModel_V1(modeltools.Method):
    """Let a submodel that follows the |RConcModel_V1| submodel interface calculate
    runoff concentration."""

    REQUIREDSEQUENCES = (gland_fluxes.PR9,)
    RESULTSEQUENCES = (gland_fluxes.Q9,)

    @staticmethod
    def __call__(
        model: modeltools.Model, submodel: rconcinterfaces.RConcModel_V1
    ) -> None:
        flu = model.sequences.fluxes.fastaccess
        submodel.set_inflow(flu.pr9)
        submodel.determine_outflow()
        flu.q9 = submodel.get_outflow()


class Calc_Q9_V1(modeltools.Method):
    """Calculate the runofff concentration with |PR9| as input.

    Examples:

        A model without a submodel for runoff concentration directs the input directly
        to the output:

        >>> from hydpy.models.gland_gr4 import *
        >>> simulationstep("1h")
        >>> parameterstep("1d")
        >>> fluxes.pr9 = 1.0
        >>> model.calc_q9_v1()
        >>> fluxes.q9
        q9(1.0)

        Prepare a submodel for a unit hydrograph with only three ordinates:

        >>> from hydpy.models.gland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> simulationstep('1d')
        >>> with model.add_rconcmodel_routingstore_v1("rconc_uh"):
        ...     uh("gr_uh1", x4=3)
        >>> from hydpy import round_
        >>> round_(model.rconcmodel_routingstore.parameters.control.uh.values)
        0.06415, 0.298737, 0.637113
        >>> model.rconcmodel_routingstore.sequences.logs.quh = 1.0, 3.0, 0.0

        Without new input, the actual output is simply the first value stored in the
        logging sequence and the values of the logging sequence are shifted to the left:

        >>> fluxes.pr9 = 0.0
        >>> model.calc_q9_v1()
        >>> fluxes.q9
        q9(1.0)
        >>> model.rconcmodel_routingstore.sequences.logs.quh
        quh(3.0, 0.0, 0.0)

        With an new input of 4 mm, the actual output consists of the first value
        stored in the logging sequence and the input value multiplied with the first
        unit hydrograph ordinate. The updated logging sequence values result from the
        multiplication of the input values and the remaining ordinates:

        >>> fluxes.pr9 = 3.6
        >>> model.calc_q9_v1()
        >>> fluxes.q9
        q9(3.23094)
        >>> model.rconcmodel_routingstore.sequences.logs.quh
        quh(1.075454, 2.293605, 0.0)

        In the next example we set the memory to zero (no input in the past),
        and apply a single input signal:

        >>> model.rconcmodel_routingstore.sequences.logs.quh = 0.0, 0.0, 0.0
        >>> fluxes.pr9 = 3.6
        >>> model.calc_q9_v1()
        >>> fluxes.q9
        q9(0.23094)
        >>> fluxes.pr9 = 0.0
        >>> model.calc_q9_v1()
        >>> fluxes.q9
        q9(1.075454)
        >>> model.calc_q9_v1()
        >>> fluxes.q9
        q9(2.293605)
        >>> model.calc_q9_v1()
        >>> fluxes.q9
        q9(0.0)

        A unit hydrograph with only one ordinate results in the direct routing of the
        input, remember, only 90% of pr enters UH:

        >>> with model.add_rconcmodel_routingstore_v1("rconc_uh"):
        ...     uh("gr_uh1", x4=0.8)
        >>> round_(model.rconcmodel_routingstore.parameters.control.uh.values)
        1.0
        >>> model.rconcmodel_routingstore.sequences.logs.quh = 0.0
        >>> fluxes.pr9 = 3.6
        >>> model.calc_q9_v1()
        >>> fluxes.q9
        q9(3.6)
    """

    SUBMODELINTERFACES = (rconcinterfaces.RConcModel_V1,)
    SUBMETHODS = (Calc_Q9_RConcModel_V1,)
    REQUIREDSEQUENCES = (gland_fluxes.PR9,)
    RESULTSEQUENCES = (gland_fluxes.Q9,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        if model.rconcmodel_routingstore is None:
            flu.q9 = flu.pr9
        elif model.rconcmodel_routingstore_typeid == 1:
            model.calc_q9_rconcmodel_v1(
                cast(rconcinterfaces.RConcModel_V1, model.rconcmodel_routingstore)
            )


class Calc_Q1_RConcModel_V1(modeltools.Method):
    """Let a submodel that follows the |RConcModel_V1| submodel interface calculate
    runoff concentration."""

    REQUIREDSEQUENCES = (gland_fluxes.PR1,)
    RESULTSEQUENCES = (gland_fluxes.Q1,)

    @staticmethod
    def __call__(
        model: modeltools.Model, submodel: rconcinterfaces.RConcModel_V1
    ) -> None:
        flu = model.sequences.fluxes.fastaccess
        submodel.set_inflow(flu.pr1)
        submodel.determine_outflow()
        flu.q1 = submodel.get_outflow()


class Calc_Q1_V1(modeltools.Method):
    """Calculate the runofff concentration with |PR1| as input.

    Examples:

        A model without a submodel for runoff concentration directs the input directly
        to the output:

        >>> from hydpy.models.gland_gr4 import *
        >>> simulationstep("1h")
        >>> parameterstep("1d")
        >>> fluxes.pr1 = 1.0
        >>> model.calc_q1_v1()
        >>> fluxes.q1
        q1(1.0)

        Prepare a submodel for a unit hydrograph with six ordinates:

        >>> from hydpy.models.gland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> simulationstep('1d')
        >>> with model.add_rconcmodel_directflow_v1("rconc_uh"):
        ...     uh("gr_uh2", x4=3)
        >>> from hydpy import round_
        >>> round_(model.rconcmodel_directflow.parameters.control.uh.values)
        0.032075, 0.149369, 0.318556, 0.318556, 0.149369, 0.032075
        >>> model.rconcmodel_directflow.sequences.logs.quh = (1.0, 3.0, 0.0, 2.0,
        ...                                                   1.0, 0.0)

        Without new input, the actual output is simply the first value stored in the
        logging sequence and the values of the logging sequence are shifted to the left:

        >>> fluxes.pr1 = 0.0
        >>> model.calc_q1_v1()
        >>> fluxes.q1
        q1(1.0)
        >>> model.rconcmodel_directflow.sequences.logs.quh
        quh(3.0, 0.0, 2.0, 1.0, 0.0, 0.0)

        With an new input of 4mm, the actual output consists of the first value
        stored in the logging sequence and the input value multiplied with the first
        unit hydrograph ordinate. The updated logging sequence values result from the
        multiplication of the input values and the remaining ordinates:

        >>> fluxes.pr1 = 0.4
        >>> model.calc_q1_v1()
        >>> fluxes.q1
        q1(3.01283)
        >>> model.rconcmodel_directflow.sequences.logs.quh
        quh(0.059747, 2.127423, 1.127423, 0.059747, 0.01283, 0.0)

        In the next example we set the memory to zero (no input in the past), and
        apply a single input signal:

        >>> model.rconcmodel_directflow.sequences.logs.quh = (0.0, 0.0, 0.0, 0.0,
        ...                                                   0.0, 0.0)
        >>> fluxes.pr1 = 0.4
        >>> model.calc_q1_v1()
        >>> fluxes.q1
        q1(0.01283)
        >>> fluxes.pr1 = 0.0
        >>> model.calc_q1_v1()
        >>> fluxes.q1
        q1(0.059747)
        >>> model.calc_q1_v1()
        >>> fluxes.q1
        q1(0.127423)
        >>> model.calc_q1_v1()
        >>> fluxes.q1
        q1(0.127423)
        >>> model.calc_q1_v1()
        >>> fluxes.q1
        q1(0.059747)
        >>> model.calc_q1_v1()
        >>> fluxes.q1
        q1(0.01283)
        >>> model.calc_q1_v1()
        >>> fluxes.q1
        q1(0.0)
    """

    SUBMODELINTERFACES = (rconcinterfaces.RConcModel_V1,)
    SUBMETHODS = (Calc_Q1_RConcModel_V1,)
    REQUIREDSEQUENCES = (gland_fluxes.PR1,)
    RESULTSEQUENCES = (gland_fluxes.Q1,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        if model.rconcmodel_directflow is None:
            flu.q1 = flu.pr1
        elif model.rconcmodel_directflow_typeid == 1:
            model.calc_q1_rconcmodel_v1(
                cast(rconcinterfaces.RConcModel_V1, model.rconcmodel_directflow)
            )


class Calc_Q10_RConcModel_V1(modeltools.Method):
    """Let a submodel that follows the |RConcModel_V1| submodel interface calculate
    runoff concentration."""

    REQUIREDSEQUENCES = (gland_fluxes.PR,)
    RESULTSEQUENCES = (gland_fluxes.Q10,)

    @staticmethod
    def __call__(
        model: modeltools.Model, submodel: rconcinterfaces.RConcModel_V1
    ) -> None:
        flu = model.sequences.fluxes.fastaccess
        submodel.set_inflow(flu.pr)
        submodel.determine_outflow()
        flu.q10 = submodel.get_outflow()


class Calc_Q10_V1(modeltools.Method):
    """Calculate the runoff concentration with |PR| as input.

    This version is used in the GR5 model with only one unit hydrograph. The input is
    100% of |PR|.

    Examples:

        A model without a submodel for runoff concentration directs the input directly
        to the output:

        >>> from hydpy.models.gland_gr5 import *
        >>> simulationstep("1h")
        >>> parameterstep("1d")
        >>> fluxes.pr = 1.0
        >>> model.calc_q10_v1()
        >>> fluxes.q10
        q10(1.0)

        Prepare a submodel for a unit hydrograph with six ordinates:

        >>> from hydpy.models.gland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> simulationstep('1d')
        >>> with model.add_rconcmodel_v1("rconc_uh"):
        ...     uh("gr_uh2", x4=3)
        >>> from hydpy import round_
        >>> round_(model.rconcmodel.parameters.control.uh.values)
        0.032075, 0.149369, 0.318556, 0.318556, 0.149369, 0.032075
        >>> model.rconcmodel.sequences.logs.quh = 3.0, 3.0, 0.0, 2.0, 4.0, 0.0

        Without new input, the actual output is simply the first value stored in the
        logging sequence and the values of the logging sequence are shifted to the left.

        >>> fluxes.pr = 0.0
        >>> model.calc_q10_v1()
        >>> fluxes.q10
        q10(3.0)
        >>> model.rconcmodel.sequences.logs.quh
        quh(3.0, 0.0, 2.0, 4.0, 0.0, 0.0)

        With an new input of 2mm, the actual output consists of the first value
        stored in the logging sequence and the input value multiplied with the first
        unit hydrograph ordinate. The updatedlogging sequence values result from the
        multiplication of the input values and the remaining ordinates:

        >>> fluxes.pr = 2.0
        >>> model.calc_q10_v1()
        >>> fluxes.q10
        q10(3.06415)
        >>> model.rconcmodel.sequences.logs.quh
        quh(0.298737, 2.637113, 4.637113, 0.298737, 0.06415, 0.0)
    """

    SUBMODELINTERFACES = (rconcinterfaces.RConcModel_V1,)
    SUBMETHODS = (Calc_Q10_RConcModel_V1,)
    REQUIREDSEQUENCES = (gland_fluxes.PR,)
    RESULTSEQUENCES = (gland_fluxes.Q10,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        if model.rconcmodel is None:
            flu.q10 = flu.pr
        elif model.rconcmodel_typeid == 1:
            model.calc_q10_rconcmodel_v1(
                cast(rconcinterfaces.RConcModel_V1, model.rconcmodel)
            )


class Calc_Q1_Q9_V2(modeltools.Method):
    r"""Calculate |Q1| and |Q9| by splittung |Q10|. This is the version for the GR5
    model.

    Basic equations:

      :math:`Q9 = 0.9 \cdot Q10`

      :math:`Q1 = Q10 - Q9`

    Example:

        >>> from hydpy.models.gland import *
        >>> parameterstep('1d')
        >>> simulationstep('1d')
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
    r"""Calculate the potential groundwater exchange term |FR| used in GR4.

    Basic equations:

      :math:`FR = X2 \cdot \left (\frac{R}{X3}\right )^{7/2}`

    Examples:

        Groundwater exchange is high when the routing storage is almost full (|R| close
        to |X3|):

        >>> from hydpy.models.gland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> x2(1.02)
        >>> x3(100.)
        >>> states.r = 95.
        >>> model.calc_fr_v1()
        >>> fluxes.fr
        fr(0.852379)

        Groundwater exchange is low when the routing storage is almost empty (|R|
        close to 0):

        >>> from hydpy.models.gland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> x2(1.02)
        >>> x3(100.)
        >>> states.r = 5.
        >>> model.calc_fr_v1()
        >>> fluxes.fr
        fr(0.000029)
    """

    CONTROLPARAMETERS = (gland_control.X2, gland_control.X3)

    UPDATEDSEQUENCES = (gland_states.R,)
    RESULTSEQUENCES = (gland_fluxes.FR,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        con = model.parameters.control.fastaccess
        flu.fr = con.x2 * (sta.r / con.x3) ** 3.5


class Calc_FR_V2(modeltools.Method):
    r"""Calculate he routing store groundwater exchange term |FR| used in GR5 and GR6.

    Basic equations:

      :math:`FR = X2 \cdot \left (\frac{R}{X3} - X5 \right )`

    Examples:

        >>> from hydpy.models.gland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> x2(-0.163)
        >>> x3(100.)
        >>> x5(0.104)
        >>> states.r = 95.
        >>> model.calc_fr_v2()
        >>> fluxes.fr
        fr(-0.137898)
    """

    CONTROLPARAMETERS = (gland_control.X2, gland_control.X3, gland_control.X5)

    UPDATEDSEQUENCES = (gland_states.R,)

    RESULTSEQUENCES = (gland_fluxes.FR,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        con = model.parameters.control.fastaccess
        flu.fr = con.x2 * (sta.r / con.x3 - con.x5)


class Update_R_V1(modeltools.Method):
    """Update level of the non-linear routing store |R| used in GR4 and GR5.

    Basic equations:

      :math:`R = R + Q9 + FR`

    Examples:

        >>> from hydpy.models.gland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> fluxes.q9 = 20.
        >>> fluxes.fr = -0.137898
        >>> states.r = 95.
        >>> model.update_r_v1()
        >>> states.r
        r(114.862102)
    """

    REQUIREDSEQUENCES = (gland_fluxes.Q9, gland_fluxes.FR)
    UPDATEDSEQUENCES = (gland_states.R,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        sta.r = max(0.0, sta.r + flu.q9 + flu.fr)


class Update_R_V2(modeltools.Method):
    r"""Update level of the non-linear routing store |R| used in GR6.

    Basic equations:

      :math:`R = max(0; R + 0.6 \cdot Q9 + F)`

    Examples:

        >>> from hydpy.models.gland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> fluxes.q9 = 20.
        >>> fluxes.fr = -0.137898
        >>> states.r = 95.
        >>> model.update_r_v2()
        >>> states.r
        r(106.862102)
    """

    REQUIREDSEQUENCES = (gland_fluxes.Q9, gland_fluxes.FR)
    UPDATEDSEQUENCES = (gland_states.R,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        sta.r = max(0.0, sta.r + 0.6 * flu.q9 + flu.fr)


class Calc_QR_V1(modeltools.Method):
    r"""Calculate the outflow |QR| of the reservoir.

    Basic equations:

      :math:`QR = R \cdot \left( 1 - \left[1 + \left( \frac{R}{X3} \right)^{4}
      \right]^{-1/4} \right)`

    Examples:

        >>> from hydpy.models.gland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> x3(100.)
        >>> states.r = 115.852379
        >>> model.calc_qr_v1()
        >>> fluxes.qr
        qr(26.30361)
    """

    CONTROLPARAMETERS = (gland_control.X3,)
    UPDATEDSEQUENCES = (gland_states.R,)
    RESULTSEQUENCES = (gland_fluxes.QR,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        con = model.parameters.control.fastaccess
        flu.qr = sta.r * (1 - (1 + (sta.r / con.x3) ** 4) ** (-0.25))


class Update_R_V3(modeltools.Method):
    """Update the non-linear routing store |R| according to its outflow.

    Basic equation:

      :math:`R = R - QR`

    Examples:

        >>> from hydpy.models.gland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> fluxes.qr = 26.30361
        >>> states.r = 115.852379
        >>> model.update_r_v3()
        >>> states.r
        r(89.548769)
    """

    REQUIREDSEQUENCES = (gland_fluxes.QR,)
    UPDATEDSEQUENCES = (gland_states.R,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        sta.r = sta.r - flu.qr


class Calc_FR2_V1(modeltools.Method):
    r"""Calculate groundwater exchange term of the exponential routing store.

    Basic equation:

      :math:`FR2 = FR`

    Examples:

        >>> from hydpy.models.gland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
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
    r"""Update the exponential Routing Store.

    Basic equation:

      :math:`R2 = R2 + 0.4 \cdot Q9 + FR2`

    Examples:

        >>> from hydpy.models.gland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> fluxes.q9 = 10.
        >>> fluxes.fr2 = -0.5
        >>> states.r2 = 40.
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
        sta.r2 = sta.r2 + 0.4 * flu.q9 + flu.fr2


class Calc_QR2_R2_V1(modeltools.Method):
    r"""Calculates the exponential routing store of the GR6 version.

    Basic equations:

      .. math::
        ar = Max(-33.0, Min(33.0, R2 / X6))
        \\
        QR = \begin{cases}
        X6 \cdot exp(ar) &|\ ar < -7
        \\
        X6 \cdot log(exp(ar)+1) &|\ -7 \leq ar \leq 7
        \\
        R2 + X6 / exp(ar) &|\ ar > 7
        \end{cases}

    Examples:

        >>> from hydpy.models.gland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> x6(4.5)
        >>> states.r2 = 40.
        >>> model.calc_qr2_r2_v1()
        >>> fluxes.qr2
        qr2(40.000621)
        >>> states.r2
        r2(-0.000621)

        There is an outflow even if the exponential storage is empty:

        >>> states.r2 = 0.
        >>> model.calc_qr2_r2_v1()
        >>> fluxes.qr2
        qr2(3.119162)
        >>> states.r2
        r2(-3.119162)

        For very small values of |R2|, |QR2| tends to 0:

        >>> states.r2 = -50.
        >>> model.calc_qr2_r2_v1()
        >>> fluxes.qr2
        qr2(0.000067)
        >>> states.r2
        r2(-50.000067)
    """

    CONTROLPARAMETERS = (gland_control.X6,)
    UPDATEDSEQUENCES = (gland_states.R2,)
    RESULTSEQUENCES = (gland_fluxes.QR2,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        con = model.parameters.control.fastaccess
        ar: float = max(-33.0, min(33.0, sta.r2 / con.x6))

        if ar > 7:
            flu.qr2 = sta.r2 + con.x6 / modelutils.exp(ar)
        elif ar < -7:
            flu.qr2 = con.x6 * modelutils.exp(ar)
        else:
            flu.qr2 = con.x6 * modelutils.log(modelutils.exp(ar) + 1.0)

        sta.r2 -= flu.qr2


class Calc_FD_V1(modeltools.Method):
    r"""Calculate groundwater exchange term with direct runoff.

    Basic equation:

      .. math::
        FD = \begin{cases}
        - Q1 &|\ (Q1 + FR) \leq 0
        \\
        FR &|\ (Q1 + FR) > 0
        \end{cases}

    Examples:

        >>> from hydpy.models.gland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> fluxes.q1 = 10.
        >>> fluxes.fr = -0.5
        >>> model.calc_fd_v1()
        >>> fluxes.fd
        fd(-0.5)

        >>> fluxes.q1 = 1.
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
        if (flu.q1 + flu.fr) > 0:
            flu.fd = flu.fr
        else:
            flu.fd = -flu.q1


class Calc_Qd_V1(modeltools.Method):
    """Calculate direct flow component.

    Basic equations:

      :math:`QD = max(0; Q1 + FD)`

    Examples:

        Positive groundwater exchange:

        >>> from hydpy.models.gland import *
        >>> parameterstep('1d')
        >>> fluxes.q1 = 20
        >>> fluxes.fd = 20
        >>> model.calc_qd_v1()
        >>> fluxes.qd
        qd(40.0)

        Negative groundwater exchange:

        >>> fluxes.fd = -10
        >>> model.calc_qd_v1()
        >>> fluxes.qd
        qd(10.0)

        Negative groundwater exchange exceeding outflow of unit hydrograph:
        >>> fluxes.fd = -30
        >>> model.calc_qd_v1()
        >>> fluxes.qd
        qd(0.0)
    """

    REQUIREDSEQUENCES = (gland_fluxes.Q1, gland_fluxes.FD)

    RESULTSEQUENCES = (gland_fluxes.QD,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.qd = max(0.0, flu.q1 + flu.fd)


class Calc_QH_V1(modeltools.Method):
    """Calculate total flow.

    Basic equations:

      :math:`QH = QR + QD`

    Example:

        >>> from hydpy.models.gland import *
        >>> parameterstep('1d')
        >>> fluxes.qr = 20
        >>> fluxes.qd = 10
        >>> model.calc_qh_v1()
        >>> fluxes.qh
        qh(30.0)
    """

    REQUIREDSEQUENCES = (gland_fluxes.QR, gland_fluxes.QD)

    RESULTSEQUENCES = (gland_fluxes.QH,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.qh = flu.qr + flu.qd


class Calc_QH_V2(modeltools.Method):
    """Calculate total flow (GR6 model version).

    Basic equations:

      :math:`QH = QR + QR2 + QD`

    Example:

        >>> from hydpy.models.gland import *
        >>> parameterstep('1d')
        >>> fluxes.qr = 20.
        >>> fluxes.qr2 = 10.
        >>> fluxes.qd = 10.
        >>> model.calc_qh_v2()
        >>> fluxes.qh
        qh(40.0)
    """

    REQUIREDSEQUENCES = (gland_fluxes.QR, gland_fluxes.QR2, gland_fluxes.QD)

    RESULTSEQUENCES = (gland_fluxes.QH,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.qh = flu.qr + flu.qr2 + flu.qd


class Calc_QV_V1(modeltools.Method):
    """Calculate total runoff in m³/s.

    Basic equations:

      :math:`QV = QFactor \\cdot QH`

    Example:

        >>> from hydpy.models.gland import *
        >>> parameterstep('1d')
        >>> fluxes.qh = 10.
        >>> derived.qfactor = 5.
        >>> model.calc_qv_v1()
        >>> fluxes.qv
        qv(50.0)
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
    r"""Update the outlet link sequence.

    Basic equation:
      :math:`Q = QV`
    """

    REQUIREDSEQUENCES = (gland_fluxes.QV,)
    RESULTSEQUENCES = (gland_outlets.Q,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        out = model.sequences.outlets.fastaccess
        out.q[0] += flu.qv


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
        Calc_Qd_V1,
        Calc_QH_V1,
        Calc_QH_V2,
        Calc_QV_V1,
    )
    ADD_METHODS = (
        Calc_E_PETModel_V1,
        Calc_Q1_RConcModel_V1,
        Calc_Q9_RConcModel_V1,
        Calc_Q10_RConcModel_V1,
    )
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
    """Base class for HydPy-W models that use submodels that comply with the
    |PETModel_V1| interface."""

    petmodel: modeltools.SubmodelProperty
    petmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    petmodel_typeid = modeltools.SubmodelTypeIDProperty()

    @importtools.prepare_submodel("petmodel", petinterfaces.PETModel_V1)
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
        >>> area(50.)
        >>> with model.add_petmodel_v1("evap_ret_tw2002"):
        ...     evapotranspirationfactor(1.5)

        >>> etf = model.petmodel.parameters.control.evapotranspirationfactor
        >>> etf
        evapotranspirationfactor(1.5)
        """
        control = self.parameters.control
        petmodel.prepare_nmbzones(1)
        petmodel.prepare_subareas(control.area.value)


class Main_RConcModel_V1(modeltools.AdHocModel):
    """Base class for HydPy-H models that use submodels that comply with the
    |RConcModel_V1| interface."""

    rconcmodel: modeltools.SubmodelProperty
    rconcmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    rconcmodel_typeid = modeltools.SubmodelTypeIDProperty()

    @importtools.prepare_submodel("rconcmodel", rconcinterfaces.RConcModel_V1)
    def add_rconcmodel_v1(
        self, rconcmodel: rconcinterfaces.RConcModel_V1, /, *, refresh: bool
    ) -> None:
        """Initialise the given submodel that follows the |RConcModel_V1| interface and
        is responsible for calculating the runoff concentration.

        >>> from hydpy.models.gland_gr5 import *
        >>> simulationstep("1d")
        >>> parameterstep("1d")
        >>> with model.add_rconcmodel_v1("rconc_uh"):
        ...     uh("gr_uh2", x4=3)
        >>> from hydpy import round_
        >>> model.rconcmodel.sequences.logs.quh = 1.0, 3.0, 0.0, 2.0, 1.0, 0.0
        >>> model.sequences.fluxes.pr = 0.0
        >>> model.calc_q10_v1()
        >>> fluxes.q10
        q10(1.0)
        """

    def _get_rconcmodel_waterbalance(
        self, initial_conditions: ConditionsModel
    ) -> float:
        r"""Get the water balance of the rconc submodel if used."""
        if self.rconcmodel:
            return self.rconcmodel.get_waterbalance(
                initial_conditions["model.rconcmodel"]
            )
        return 0.0


class Main_RConcModel_V2(modeltools.AdHocModel):
    """Base class for HydPy-H models that use submodels that comply with the
    |RConcModel_V1| interface."""

    rconcmodel_routingstore: modeltools.SubmodelProperty
    rconcmodel_directflow: modeltools.SubmodelProperty
    rconcmodel_routingstore_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    rconcmodel_directflow_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    rconcmodel_routingstore_typeid = modeltools.SubmodelTypeIDProperty()
    rconcmodel_directflow_typeid = modeltools.SubmodelTypeIDProperty()

    @importtools.prepare_submodel(
        "rconcmodel_routingstore", rconcinterfaces.RConcModel_V1
    )
    def add_rconcmodel_routingstore_v1(
        self, rconcmodel: rconcinterfaces.RConcModel_V1, /, *, refresh: bool
    ) -> None:
        """Initialise the given submodel that follows the |RConcModel_V1| interface and
        is responsible for calculating the runoff concentration.

        >>> from hydpy.models.gland_gr4 import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> with model.add_rconcmodel_routingstore_v1("rconc_uh"):
        ...     uh([0.3, 0.5, 0.2])
        ...     logs.quh.shape = 3
        ...     logs.quh = 1.0, 3.0, 0.0
        >>> model.sequences.fluxes.pr9 = 0.0
        >>> model.calc_q9_v1()
        >>> fluxes.q9
        q9(1.0)
        """

    @importtools.prepare_submodel(
        "rconcmodel_directflow", rconcinterfaces.RConcModel_V1
    )
    def add_rconcmodel_directflow_v1(
        self, rconcmodel: rconcinterfaces.RConcModel_V1, /, *, refresh: bool
    ) -> None:
        """Initialise the given submodel that follows the |RConcModel_V1| interface and
        is responsible for calculating the runoff concentration.

        >>> from hydpy.models.gland_gr4 import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> with model.add_rconcmodel_directflow_v1("rconc_uh"):
        ...     uh([0.3, 0.5, 0.2])
        ...     logs.quh.shape = 3
        ...     logs.quh = 1.0, 3.0, 0.0
        >>> model.sequences.fluxes.pr1 = 0.0
        >>> model.calc_q1_v1()
        >>> fluxes.q1
        q1(1.0)
        """

    def _get_rconcmodel_waterbalance_routingstore(
        self, initial_conditions: ConditionsModel
    ) -> float:
        r"""Get the water balance of the rconc submodel if used."""
        if self.rconcmodel_routingstore:
            return self.rconcmodel_routingstore.get_waterbalance(
                initial_conditions["model.rconcmodel_routingstore"]
            )
        return 0.0

    def _get_rconcmodel_waterbalance_directflow(
        self, initial_conditions: ConditionsModel
    ) -> float:
        r"""Get the water balance of the rconc submodel if used."""
        if self.rconcmodel_directflow:
            return self.rconcmodel_directflow.get_waterbalance(
                initial_conditions["model.rconcmodel_directflow"]
            )
        return 0.0
