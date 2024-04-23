# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# imports...
# ...from HydPy
from hydpy.core import importtools
from hydpy.core import modeltools
from hydpy.core.typingtools import *
from hydpy.cythons import modelutils
from hydpy.interfaces import petinterfaces

# ...from gland
from hydpy.models.gland import gland_inputs
from hydpy.models.gland import gland_fluxes
from hydpy.models.gland import gland_control
from hydpy.models.gland import gland_states
from hydpy.models.gland import gland_outlets
from hydpy.models.gland import gland_derived
from hydpy.models.gland import gland_logs


class Calc_PET_PETModel_V1(modeltools.Method):
    """Let a submodel that complies with the |PETModel_V1| interface calculate the
    potential evapotranspiration of the land areas.

    Example:

        We use |evap_tw2002| as an example:

        >>> from hydpy.models.gland_gr4 import *
        >>> parameterstep()
        >>> from hydpy import prepare_model
        >>> area(50.)
        >>> with model.add_petmodel_v1("evap_tw2002"):
        ...     hrualtitude(200.0)
        ...     coastfactor(0.6)
        ...     evapotranspirationfactor(1.1)
        ...     with model.add_radiationmodel_v2("meteo_glob_io"):
        ...         inputs.globalradiation = 200.0
        ...     with model.add_tempmodel_v2("meteo_temp_io"):
        ...         temperatureaddend(1.0)
        ...         inputs.temperature = 14.0
        >>> model.calc_pet_v1()
        >>> fluxes.pet
        pet(3.07171)
    """

    RESULTSEQUENCES = (gland_fluxes.PET,)

    @staticmethod
    def __call__(model: modeltools.Model, submodel: petinterfaces.PETModel_V1) -> None:
        flu = model.sequences.fluxes.fastaccess
        submodel.determine_potentialevapotranspiration()
        flu.pet = submodel.get_potentialevapotranspiration(0)


class Calc_PET_V1(modeltools.Method):
    """Let a submodel that complies with the |PETModel_V1| interface calculate the
    potential evapotranspiration."""

    SUBMODELINTERFACES = (petinterfaces.PETModel_V1,)
    SUBMETHODS = (Calc_PET_PETModel_V1,)
    RESULTSEQUENCES = (gland_fluxes.PET,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        if model.petmodel_typeid == 1:
            model.calc_pet_petmodel_v1(cast(petinterfaces.PETModel_V1, model.petmodel))


class Calc_Pn_En_V1(modeltools.Method):
    r"""Calculate net rainfall |Pn| and net evapotranspiration capacity |En|.

    Basic equations:

      .. math::
        Pn = \begin{cases}
        P - PET, En = 0 &|\ P \geq PET \\
        0, En = PET - P &|\ P < PET
        \end{cases}

    Examples:

        Evapotranspiration larger than precipitation:

        >>> from hydpy.models.gland import *
        >>> parameterstep('1d')
        >>> inputs.p = 20.
        >>> fluxes.pet = 30.
        >>> model.calc_pn_en_v1()
        >>> fluxes.en
        en(10.0)
        >>> fluxes.pn
        pn(0.0)

        Precipitation larger than evapotranspiration:

        >>> inputs.p = 50.
        >>> fluxes.pet = 10.
        >>> model.calc_pn_en_v1()
        >>> fluxes.en
        en(0.0)
        >>> fluxes.pn
        pn(40.0)
    """

    REQUIREDSEQUENCES = (gland_inputs.P, gland_fluxes.PET)
    RESULTSEQUENCES = (gland_fluxes.Pn, gland_fluxes.En)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess

        if inp.p >= flu.pet:
            flu.pn = inp.p - flu.pet
            flu.en = 0.0
        else:
            flu.pn = 0.0
            flu.en = flu.pet - inp.p


class Calc_PS_V1(modeltools.Method):
    r"""Calculate part of net rainfall |Pn| filling the production store in mm.

    Basic equation:

      :math:`Ps = \frac{
      x1\left(1-\left(\frac{S}{x1}\right)^{2}\right ) \cdot
      tanh \left( \frac{Pn }{x1} \right)}
      {1 + \frac{S}{x1}\cdot tanh \left( \frac{Pn}{x1} \right)}`

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

    REQUIREDSEQUENCES = (gland_fluxes.Pn, gland_states.S)
    CONTROLPARAMETERS = (gland_control.X1,)

    RESULTSEQUENCES = (gland_fluxes.Ps,)

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


class Calc_Es_V1(modeltools.Method):
    r"""Calculate actual evaporation rate from production store.

    Basic equations:

      .. math ::
        ws = tanh\left(\frac{En}{x1}\right), \quad sr = \frac{S}{x1} \\
        Es = \frac{S \cdot (2-sr) \cdot ws}{1+(1-sr) \cdot ws}

    Examples:

        Production store almost full, no rain: |Es| reaches almost |En|:

        >>> from hydpy.models.gland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> x1(300.)
        >>> fluxes.en = 2.
        >>> states.s = 270.
        >>> model.calc_es_v1()
        >>> fluxes.es
        es(1.978652)

        Production store almost empty, no rain: |Es| reaches almost 0:

        >>> states.s = 10.
        >>> model.calc_es_v1()
        >>> fluxes.es
        es(0.13027)
    """

    REQUIREDSEQUENCES = (gland_fluxes.En, gland_states.S)
    CONTROLPARAMETERS = (gland_control.X1,)

    RESULTSEQUENCES = (gland_fluxes.Es,)

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
    """Update the production store based on filling and evapoation from production
    store.

    Basic equations:

      :math:`S = S - Es + Ps`

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

    REQUIREDSEQUENCES = (gland_fluxes.Ps, gland_fluxes.Es)
    UPDATEDSEQUENCES = (gland_states.S,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        sta.s = sta.s - flu.es + flu.ps


class Calc_Perc_V1(modeltools.Method):
    r"""Calculate percolation from the production store.

    Basic equations:

      :math:`Perc = S \cdot \left( 1-\left(1+\left(\frac{4 \cdot S}
      {9 \cdot X1}\right )^{4}\right )^{-1/4}\right )`

    Examples:

        >>> from hydpy.models.gland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')

        Producion store is almost full (maximum percolation 0.009 |S|):

        >>> x1(300.)
        >>> states.s = 268.
        >>> model.calc_perc_v1()
        >>> fluxes.perc
        perc(1.639555)

        Producion store is almost empty:

        >>> x1(300.)
        >>> states.s = 50.
        >>> model.calc_perc_v1()
        >>> fluxes.perc
        perc(0.000376)
    """

    CONTROLPARAMETERS = (gland_control.X1,)

    UPDATEDSEQUENCES = (gland_states.S,)

    RESULTSEQUENCES = (gland_fluxes.Perc,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        con = model.parameters.control.fastaccess
        flu.perc = sta.s * (
            1.0 - (1.0 + (4.0 / 9.0 * sta.s / con.x1) ** 4.0) ** (-0.25)
        )


class Update_S_V2(modeltools.Method):
    """Update the production store according to percolation.

    Basic equations:

      :math:`S = S - Perc`

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
    """Calculate actual evaporation (only for output).

    Basic equations:

      :math:`AE = PET - En + Es`

    Examples:

        >>> from hydpy.models.gland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> fluxes.pet = 10.
        >>> fluxes.en = 2.
        >>> fluxes.es = 1.978652
        >>> model.calc_ae_v1()
        >>> fluxes.ae
        ae(9.978652)
    """

    REQUIREDSEQUENCES = (gland_fluxes.PET, gland_fluxes.En, gland_fluxes.Es)
    RESULTSEQUENCES = (gland_fluxes.AE,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.ae = flu.pet - flu.en + flu.es


class Calc_Pr_V1(modeltools.Method):
    """Calculate total quantity |Pr| of water reaching the routing functions.

    Basic equation:

      :math:`Pr = Perc + (Pn - Ps)`

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

    REQUIREDSEQUENCES = (gland_fluxes.Ps, gland_fluxes.Pn, gland_fluxes.Perc)

    RESULTSEQUENCES = (gland_fluxes.Pr,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.pr = flu.perc + flu.pn - flu.ps


class Calc_PrUH1_PrUH2_V1(modeltools.Method):
    r"""Splitting |Pr| into |PrUH1| and |PrUH2|.

    Basic equations:

      :math:`PrUH1 = 0.9 \cdot Pr`

      :math:`PrUH2 = 1 - PrUH1`

    Examples:

        Example production store nearly full, no rain:

        >>> from hydpy.models.gland import *
        >>> parameterstep('1d')
        >>> fluxes.pr = 10.0
        >>> model.calc_pruh1_pruh2_v1()
        >>> fluxes.pruh1
        pruh1(9.0)
        >>> fluxes.pruh2
        pruh2(1.0)
    """

    REQUIREDSEQUENCES = (gland_fluxes.Pr,)
    RESULTSEQUENCES = (gland_fluxes.PrUH1, gland_fluxes.PrUH2)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.pruh1 = 0.9 * flu.pr
        flu.pruh2 = flu.pr - flu.pruh1


class Calc_Q9_V1(modeltools.Method):
    """Calculate the unit hydrograph |UH1| output (convolution) with |PrUH1| as input.

    Examples:

        Prepare a unit hydrograph with only three ordinates:

        >>> from hydpy.models.gland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> simulationstep('1d')
        >>> x4(3)
        >>> derived.uh1.update()
        >>> derived.uh1
        uh1(0.06415, 0.298737, 0.637113)
        >>> logs.quh1 = 1.0, 3.0, 0.0

        Without new input, the actual output is simply the first value
        stored in the logging sequence and the values of the logging
        sequence are shifted to the left:

        >>> fluxes.pruh1 = 0.0
        >>> model.calc_q9_v1()
        >>> fluxes.q9
        q9(1.0)
        >>> logs.quh1
        quh1(3.0, 0.0, 0.0)

        With an new input of 4mm, the actual output consists of the first
        value stored in the logging sequence and the input value
        multiplied with the first unit hydrograph ordinate.  The updated
        logging sequence values result from the multiplication of the
        input values and the remaining ordinates:

        >>> fluxes.pruh1 = 3.6
        >>> model.calc_q9_v1()
        >>> fluxes.q9
        q9(3.23094)
        >>> logs.quh1
        quh1(1.075454, 2.293605, 0.0)

        In the next example we set the memory to zero (no input in the past), and
        apply a single input signal:

        >>> logs.quh1 = 0.0, 0.0, 0.0
        >>> fluxes.pruh1 = 3.6
        >>> model.calc_q9_v1()
        >>> fluxes.q9
        q9(0.23094)
        >>> fluxes.pruh1 = 0.0
        >>> model.calc_q9_v1()
        >>> fluxes.q9
        q9(1.075454)
        >>> model.calc_q9_v1()
        >>> fluxes.q9
        q9(2.293605)
        >>> model.calc_q9_v1()
        >>> fluxes.q9
        q9(0.0)

        A unit hydrograph with only one ordinate results in the direct
        routing of the input, remember, only 90% of pr enters UH1:

        >>> x4(0.8)
        >>> derived.uh1.update()
        >>> derived.uh1
        uh1(1.0)
        >>> logs.quh1 = 0
        >>> fluxes.pruh1 = 3.6
        >>> model.calc_q9_v1()
        >>> fluxes.q9
        q9(3.6)
    """

    DERIVEDPARAMETERS = (gland_derived.UH1,)
    REQUIREDSEQUENCES = (gland_fluxes.PrUH1,)
    UPDATEDSEQUENCES = (gland_logs.QUH1,)
    RESULTSEQUENCES = (gland_fluxes.Q9,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        flu.q9 = der.uh1[0] * flu.pruh1 + log.quh1[0]
        for jdx in range(1, len(der.uh1)):
            log.quh1[jdx - 1] = der.uh1[jdx] * flu.pruh1 + log.quh1[jdx]


class Calc_Q1_V1(modeltools.Method):
    """Calculate the unit hydrograph |UH2| output (convolution). Input to the unit
    hydrograph |UH2| is |PrUH2|.

    Examples:

        Prepare a unit hydrograph with six ordinates:

        >>> from hydpy.models.gland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> simulationstep('1d')
        >>> x4(3)
        >>> derived.uh2.update()
        >>> derived.uh2
        uh2(0.032075, 0.149369, 0.318556, 0.318556, 0.149369, 0.032075)
        >>> logs.quh2 = 1.0, 3.0, 0.0, 2.0, 1.0, 0.0

        Without new input, the actual output is simply the first value
        stored in the logging sequence and the values of the logging
        sequence are shifted to the left:

        >>> fluxes.pruh2 = 0.0
        >>> model.calc_q1_v1()
        >>> fluxes.q1
        q1(1.0)
        >>> logs.quh2
        quh2(3.0, 0.0, 2.0, 1.0, 0.0, 0.0)

        With an new input of 4mm, the actual output consists of the first
        value stored in the logging sequence and the input value
        multiplied with the first unit hydrograph ordinate.  The updated
        logging sequence values result from the multiplication of the
        input values and the remaining ordinates:

        >>> fluxes.pruh2 = 0.4
        >>> model.calc_q1_v1()
        >>> fluxes.q1
        q1(3.01283)
        >>> logs.quh2
        quh2(0.059747, 2.127423, 1.127423, 0.059747, 0.01283, 0.0)

        In the next example we set the memory to zero (no input in the past), and
        apply a single input signal:

        >>> logs.quh2 = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        >>> fluxes.pruh2 = 0.4
        >>> model.calc_q1_v1()
        >>> fluxes.q1
        q1(0.01283)
        >>> fluxes.pruh2 = 0.0
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

    DERIVEDPARAMETERS = (gland_derived.UH2,)
    REQUIREDSEQUENCES = (gland_fluxes.PrUH2,)
    UPDATEDSEQUENCES = (gland_logs.QUH2,)
    RESULTSEQUENCES = (gland_fluxes.Q1,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        flu.q1 = der.uh2[0] * flu.pruh2 + log.quh2[0]
        for jdx in range(1, len(der.uh2)):
            log.quh2[jdx - 1] = der.uh2[jdx] * flu.pruh2 + log.quh2[jdx]


class Calc_QUH2_V1(modeltools.Method):
    """Calculate the unit hydrograph UH2 output (convolution).

    This is the version for the GR5 model. The input is 100% of Pr.

    Examples:

        Prepare a unit hydrograph with only six ordinates:

        >>> from hydpy.models.gland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> simulationstep('1d')
        >>> x4(3)
        >>> derived.uh2.update()
        >>> derived.uh2
        uh2(0.032075, 0.149369, 0.318556, 0.318556, 0.149369, 0.032075)
        >>> logs.quh2 = 3.0, 3.0, 0.0, 2.0, 4.0, 0.0

        Without new input, the actual output is simply the first value
        stored in the logging sequence and the values of the logging
        sequence are shifted to the left.

        >>> fluxes.pr = 0.0
        >>> model.calc_quh2_v1()
        >>> fluxes.qoutuh2
        qoutuh2(3.0)
        >>> logs.quh2
        quh2(3.0, 0.0, 2.0, 4.0, 0.0, 0.0)

        With an new input of 2mm, the actual output consists of the first
        value stored in the logging sequence and the input value
        multiplied with the first unit hydrograph ordinate.  The updated
        logging sequence values result from the multiplication of the
        input values and the remaining ordinates:

        >>> fluxes.pr = 2.0
        >>> model.calc_quh2_v1()
        >>> fluxes.qoutuh2
        qoutuh2(3.06415)
        >>> logs.quh2
        quh2(0.298737, 2.637113, 4.637113, 0.298737, 0.06415, 0.0)
    """

    DERIVEDPARAMETERS = (gland_derived.UH2,)
    REQUIREDSEQUENCES = (gland_fluxes.Pr,)
    UPDATEDSEQUENCES = (gland_logs.QUH2,)
    RESULTSEQUENCES = (gland_fluxes.QOutUH2,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        flu.qoutuh2 = der.uh2[0] * flu.pr + log.quh2[0]
        for jdx in range(1, len(der.uh2)):
            log.quh2[jdx - 1] = der.uh2[jdx] * flu.pr + log.quh2[jdx]


class Calc_Q1_Q9_V2(modeltools.Method):
    r"""Calculate |Q1| and |Q9| by splittung |QOutUH2|. This is the version for the GR5
    model.

    Basic equations:

      :math:`Q9 = 0.9 \cdot QUH2`

      :math:`Q1 = QUH2 - Q9`

    Example:

        >>> from hydpy.models.gland import *
        >>> parameterstep('1d')
        >>> simulationstep('1d')
        >>> fluxes.qoutuh2 = 10.0
        >>> model.calc_q1_q9_v2()
        >>> fluxes.q1
        q1(1.0)
        >>> fluxes.q9
        q9(9.0)
    """

    REQUIREDSEQUENCES = (gland_fluxes.QOutUH2,)
    RESULTSEQUENCES = (gland_fluxes.Q1, gland_fluxes.Q9)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.q1 = 0.1 * flu.qoutuh2
        flu.q9 = 0.9 * flu.qoutuh2


class Calc_F_V1(modeltools.Method):
    r"""Calculate the groundwater exchange term |F| used in GR4.

    Basic equations:

      :math:`F = X2 \cdot \left (\frac{R}{X3}\right )^{7/2}`

    Examples:

        Groundwater exchange is high when the routing storage is almost full (|R| close
        to |X3|):

        >>> from hydpy.models.gland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> x2(1.02)
        >>> x3(100.)
        >>> states.r = 95.
        >>> model.calc_f_v1()
        >>> fluxes.f
        f(0.852379)

        Groundwater exchange is high when the routing storage is almost empty (|R|
        close to 0):

        >>> from hydpy.models.gland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> x2(1.02)
        >>> x3(100.)
        >>> states.r = 5.
        >>> model.calc_f_v1()
        >>> fluxes.f
        f(0.000029)
    """

    CONTROLPARAMETERS = (gland_control.X2, gland_control.X3)

    UPDATEDSEQUENCES = (gland_states.R,)
    RESULTSEQUENCES = (gland_fluxes.F,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        con = model.parameters.control.fastaccess
        flu.f = con.x2 * (sta.r / con.x3) ** 3.5


class Calc_F_V2(modeltools.Method):
    r"""Calculate groundwater exchange term |F| used in GR5 and GR6

    Basic equations:

      :math:`F = X2 \cdot \left (\frac{R}{X3} - X5 \right )`

    Examples:

        >>> from hydpy.models.gland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> x2(-0.163)
        >>> x3(100.)
        >>> x5(0.104)
        >>> states.r = 95.
        >>> model.calc_f_v2()
        >>> fluxes.f
        f(-0.137898)
    """

    CONTROLPARAMETERS = (gland_control.X2, gland_control.X3, gland_control.X5)

    UPDATEDSEQUENCES = (gland_states.R,)

    RESULTSEQUENCES = (gland_fluxes.F,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        con = model.parameters.control.fastaccess
        flu.f = con.x2 * (sta.r / con.x3 - con.x5)


class Update_R_V1(modeltools.Method):
    """Update level of the non-linear routing store |R| used in GR4 and GR5.

    Basic equations:

      :math:`R = max(0; R + Q9 + F)`

    Examples:

        >>> from hydpy.models.gland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> fluxes.q9 = 20.
        >>> fluxes.f = -0.137898
        >>> states.r = 95.
        >>> model.update_r_v1()
        >>> states.r
        r(114.862102)
    """

    REQUIREDSEQUENCES = (gland_fluxes.Q9, gland_fluxes.F)
    UPDATEDSEQUENCES = (gland_states.R,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        sta.r = max(0.0, sta.r + flu.q9 + flu.f)


class Update_R_V2(modeltools.Method):
    r"""Update level of the non-linear routing store |R| used in GR6.

    Basic equations:

      :math:`R = max(0; R + 0.6 \cdot Q9 + F)`

    Examples:

        >>> from hydpy.models.gland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> fluxes.q9 = 20.
        >>> fluxes.f = -0.137898
        >>> states.r = 95.
        >>> model.update_r_v2()
        >>> states.r
        r(106.862102)
    """

    REQUIREDSEQUENCES = (gland_fluxes.Q9, gland_fluxes.F)
    UPDATEDSEQUENCES = (gland_states.R,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        sta.r = max(0.0, sta.r + 0.6 * flu.q9 + flu.f)


class Calc_Qr_V1(modeltools.Method):
    r"""Calculate the outflow |Qr| of the reservoir.

    Basic equations:

      :math:`Qr = R \cdot \left( 1 - \left[1 + \left( \frac{R}{X3} \right)^{4}
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
    RESULTSEQUENCES = (gland_fluxes.Qr,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        con = model.parameters.control.fastaccess
        flu.qr = sta.r * (1 - (1 + (sta.r / con.x3) ** 4) ** (-0.25))


class Update_R_V3(modeltools.Method):
    """Update the non-linear routing store R according to its outflow.

    Basic equation:

      :math:`R = R - Qr`

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

    REQUIREDSEQUENCES = (gland_fluxes.Qr,)
    UPDATEDSEQUENCES = (gland_states.R,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        sta.r = sta.r - flu.qr


class Update_R2_V1(modeltools.Method):
    r"""Update Exponential Routing Store.

    Basic equation:

      :math:`R2 = R2 + 0.4 \cdot Q9 \cdot F`

    Examples:

        >>> from hydpy.models.gland import *
        >>> from hydpy import pub
        >>> parameterstep('1d')
        >>> fluxes.q9 = 10.
        >>> fluxes.f = -0.5
        >>> states.r2 = 40.
        >>> model.update_r2_v1()
        >>> states.r2
        r2(43.5)
    """

    REQUIREDSEQUENCES = (gland_fluxes.Q9, gland_fluxes.F)
    UPDATEDSEQUENCES = (gland_states.R2,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        sta.r2 = sta.r2 + 0.4 * flu.q9 + flu.f


class Calc_Qr2_R2_V1(modeltools.Method):
    r"""Calculates the exponential store of the GR6 version.

    Basic equations:

      .. math::
        ar = Max(-33.0, Min(33.0, R2 / X6))
        \\
        Qr = \begin{cases}
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

        For very small values of |R2|, |Qr2| goes toward 0

        >>> states.r2 = -50.
        >>> model.calc_qr2_r2_v1()
        >>> fluxes.qr2
        qr2(0.000067)
        >>> states.r2
        r2(-50.000067)
    """

    CONTROLPARAMETERS = (gland_control.X6,)
    UPDATEDSEQUENCES = (gland_states.R2,)
    RESULTSEQUENCES = (gland_fluxes.Qr2,)

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


class Calc_Qd_V1(modeltools.Method):
    """Calculate direct flow component.

    Basic equations:

      :math:`Qd = max(0; Q1 + F)`

    Examples:

        Positive groundwater exchange:

        >>> from hydpy.models.gland import *
        >>> parameterstep('1d')
        >>> fluxes.q1 = 20
        >>> fluxes.f = 20
        >>> model.calc_qd_v1()
        >>> fluxes.qd
        qd(40.0)

        Negative groundwater exchange:

        >>> fluxes.f = -10
        >>> model.calc_qd_v1()
        >>> fluxes.qd
        qd(10.0)

        Negative groundwater exchange exceeding outflow of unit hydrograph:
        >>> fluxes.f = -30
        >>> model.calc_qd_v1()
        >>> fluxes.qd
        qd(0.0)
    """

    REQUIREDSEQUENCES = (gland_fluxes.Q1, gland_fluxes.F)

    RESULTSEQUENCES = (gland_fluxes.Qd,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.qd = max(0, flu.q1 + flu.f)


class Calc_Qt_V1(modeltools.Method):
    """Calculate total flow.

    Basic equations:

      :math:`Qt = Qr + Qd`


    Examples:

        >>> from hydpy.models.gland import *
        >>> parameterstep('1d')
        >>> fluxes.qr = 20
        >>> fluxes.qd = 10
        >>> model.calc_qt_v1()
        >>> fluxes.qt
        qt(30.0)
    """

    REQUIREDSEQUENCES = (gland_fluxes.Qr, gland_fluxes.Qd)

    RESULTSEQUENCES = (gland_fluxes.Qt,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.qt = flu.qr + flu.qd


class Calc_Qt_V3(modeltools.Method):
    """Calculate total flow (GR6 model version).

    Basic equations:

      :math:`Qt = Qr + Qr2 + Qd`

    Examples:

        >>> from hydpy.models.gland import *
        >>> parameterstep('1d')
        >>> fluxes.qr = 20.
        >>> fluxes.qr2 = 10.
        >>> fluxes.qd = 10.
        >>> model.calc_qt_v3()
        >>> fluxes.qt
        qt(40.0)
    """

    REQUIREDSEQUENCES = (gland_fluxes.Qr, gland_fluxes.Qr2, gland_fluxes.Qd)

    RESULTSEQUENCES = (gland_fluxes.Qt,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.qt = flu.qr + flu.qr2 + flu.qd


class Pass_Q_V1(modeltools.Method):
    r"""Update the outlet link sequence.

    Basic equation:
      :math:`Q = QFactor \cdot QT`
    """

    DERIVEDPARAMETERS = (gland_derived.QFactor,)
    REQUIREDSEQUENCES = (gland_fluxes.Qt,)
    RESULTSEQUENCES = (gland_outlets.Q,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        out = model.sequences.outlets.fastaccess
        out.q[0] += der.qfactor * flu.qt


class Model(modeltools.AdHocModel):
    """The G-Land base model."""

    INLET_METHODS = (Calc_PET_V1,)
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        Calc_Pn_En_V1,
        Calc_PS_V1,
        Calc_Es_V1,
        Update_S_V1,
        Calc_Perc_V1,
        Update_S_V2,
        Calc_AE_V1,
        Calc_Pr_V1,
        Calc_PrUH1_PrUH2_V1,
        Calc_Q9_V1,
        Calc_Q1_V1,
        Calc_QUH2_V1,
        Calc_Q1_Q9_V2,
        Calc_F_V1,
        Calc_F_V2,
        Update_R_V1,
        Update_R_V3,
        Update_R_V2,
        Calc_Qr_V1,
        Update_R_V3,
        Update_R2_V1,
        Calc_Qr2_R2_V1,
        Update_R_V2,
        Calc_Qd_V1,
        Calc_Qt_V1,
        Calc_Qt_V3,
    )
    ADD_METHODS = (Calc_PET_PETModel_V1,)
    OUTLET_METHODS = (Pass_Q_V1,)
    SENDER_METHODS = ()
    SUBMODELINTERFACES = (petinterfaces.PETModel_V1,)
    SUBMODELS = ()

    petmodel = modeltools.SubmodelProperty(petinterfaces.PETModel_V1)
    petmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    petmodel_typeid = modeltools.SubmodelTypeIDProperty()


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
        >>> with model.add_petmodel_v1("evap_tw2002"):
        ...     evapotranspirationfactor(1.5)

        >>> etf = model.petmodel.parameters.control.evapotranspirationfactor
        >>> etf
        evapotranspirationfactor(1.5)
        """
        control = self.parameters.control
        petmodel.prepare_nmbzones(1)
        petmodel.prepare_subareas(control.area.value)
