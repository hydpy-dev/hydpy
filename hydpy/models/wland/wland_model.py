# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import modeltools
from hydpy.cythons import modelutils
from hydpy.cythons.autogen import smoothutils
from hydpy.models.wland import wland_control
from hydpy.models.wland import wland_derived
from hydpy.models.wland import wland_fixed
from hydpy.models.wland import wland_solver
from hydpy.models.wland import wland_inputs
from hydpy.models.wland import wland_fluxes
from hydpy.models.wland import wland_states
from hydpy.models.wland import wland_aides
from hydpy.models.wland import wland_outlets
from hydpy.models.wland.wland_constants import SEALED


class Calc_FXS_V1(modeltools.Method):
    r"""Query the current surface water supply/extraction.

    Basic equation:
      .. math::
        FXS_{fluxes} = \begin{cases}
        0 &|\ FXS_{inputs} = 0
        \\
        \frac{FXS_{inputs}}{ASR} &|\ FXS_{inputs} \neq 0 \land ASR > 0
        \\
        inf &|\ FXS_{inputs} \neq 0 \land ASR = 0
        \end{cases}

    Examples:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> derived.asr(0.5)
        >>> inputs.fxs = 2.0
        >>> model.calc_fxs_v1()
        >>> fluxes.fxs
        fxs(4.0)
        >>> derived.asr(0.0)
        >>> model.calc_fxs_v1()
        >>> fluxes.fxs
        fxs(inf)
        >>> inputs.fxs = 0.0
        >>> model.calc_fxs_v1()
        >>> fluxes.fxs
        fxs(0.0)
    """

    DERIVEDPARAMETERS = (wland_derived.ASR,)
    REQUIREDSEQUENCES = (wland_inputs.FXS,)
    RESULTSEQUENCES = (wland_fluxes.FXS,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        if inp.fxs == 0.0:
            flu.fxs = 0.0
        elif der.asr > 0.0:
            flu.fxs = inp.fxs / der.asr
        else:
            flu.fxs = modelutils.inf


class Calc_FXG_V1(modeltools.Method):
    r"""Query the current seepage/extraction.

    Basic equation:
      .. math::
        FXG_{fluxes} = \begin{cases}
        0 &|\ FXG_{inputs} = 0
        \\
        \frac{FXG_{inputs}}{AGR} &|\ FXG_{inputs} \neq 0 \land AGR > 0
        \\
        inf &|\ FXG_{inputs} \neq 0 \land AGR = 0
        \end{cases}

    Examples:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> derived.alr(0.5)
        >>> derived.agr(0.8)
        >>> inputs.fxg = 2.0
        >>> model.calc_fxg_v1()
        >>> fluxes.fxg
        fxg(5.0)
        >>> derived.agr(0.0)
        >>> model.calc_fxg_v1()
        >>> fluxes.fxg
        fxg(inf)
        >>> inputs.fxg = 0.0
        >>> model.calc_fxg_v1()
        >>> fluxes.fxg
        fxg(0.0)
    """

    DERIVEDPARAMETERS = (
        wland_derived.ALR,
        wland_derived.AGR,
    )
    REQUIREDSEQUENCES = (wland_inputs.FXG,)
    RESULTSEQUENCES = (wland_fluxes.FXG,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        if inp.fxg == 0.0:
            flu.fxg = 0.0
        else:
            d_ra = der.alr * der.agr
            if d_ra > 0.0:
                flu.fxg = inp.fxg / d_ra
            else:
                flu.fxg = modelutils.inf


class Calc_PC_V1(modeltools.Method):
    r"""Calculate the corrected precipitation.

    Basic equation:
      :math:`PC = CP \cdot P`

    Examples:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> cp(1.2)
        >>> inputs.p = 2.0
        >>> model.calc_pc_v1()
        >>> fluxes.pc
        pc(2.4)
    """

    CONTROLPARAMETERS = (wland_control.CP,)
    REQUIREDSEQUENCES = (wland_inputs.P,)
    RESULTSEQUENCES = (wland_fluxes.PC,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.pc = con.cp * inp.p


class Calc_PETL_V1(modeltools.Method):
    r"""Adjust the potential evapotranspiration of the land areas.

    Basic equation:
      :math:`PETL = CETP \cdot CPETL \cdot PET`

    Examples:

        >>> from hydpy import pub, UnitTest
        >>> pub.timegrids = '2000-03-30', '2000-04-03', '1d'
        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> nu(2)
        >>> lt(FIELD, DECIDIOUS)
        >>> cpet(0.8)
        >>> cpetl.field_mar = 1.25
        >>> cpetl.field_apr = 1.5
        >>> cpetl.decidious_mar = 1.75
        >>> cpetl.decidious_apr = 2.0
        >>> derived.moy.update()
        >>> inputs.pet = 2.0
        >>> model.idx_sim = pub.timegrids.init['2000-03-31']
        >>> model.calc_petl_v1()
        >>> fluxes.petl
        petl(2.0, 2.8)
        >>> model.idx_sim = pub.timegrids.init['2000-04-01']
        >>> model.calc_petl_v1()
        >>> fluxes.petl
        petl(2.4, 3.2)

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (
        wland_control.NU,
        wland_control.LT,
        wland_control.CPET,
        wland_control.CPETL,
    )
    DERIVEDPARAMETERS = (wland_derived.MOY,)
    REQUIREDSEQUENCES = (wland_inputs.PET,)
    RESULTSEQUENCES = (wland_fluxes.PETL,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nu):
            d_cpetl = con.cpetl[con.lt[k] - SEALED, der.moy[model.idx_sim]]
            flu.petl[k] = con.cpet * d_cpetl * inp.pet


class Calc_PES_V1(modeltools.Method):
    r"""Adapt the potential evaporation for the surface water area.

    Basic equation:
      :math:`PES = CETP \cdot CPES \cdot PET`

    Examples:

        >>> from hydpy import pub, UnitTest
        >>> pub.timegrids = '2000-03-30', '2000-04-03', '1d'
        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> cpet(0.8)
        >>> cpes.mar = 1.25
        >>> cpes.apr = 1.5
        >>> derived.moy.update()
        >>> inputs.pet = 2.0
        >>> model.idx_sim = pub.timegrids.init['2000-03-31']
        >>> model.calc_pes_v1()
        >>> fluxes.pes
        pes(2.0)
        >>> model.idx_sim = pub.timegrids.init['2000-04-01']
        >>> model.calc_pes_v1()
        >>> fluxes.pes
        pes(2.4)

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (
        wland_control.CPET,
        wland_control.CPES,
    )
    DERIVEDPARAMETERS = (wland_derived.MOY,)
    REQUIREDSEQUENCES = (wland_inputs.PET,)
    RESULTSEQUENCES = (wland_fluxes.PES,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        d_cpes = con.cpes[der.moy[model.idx_sim]]
        flu.pes = con.cpet * d_cpes * inp.pet


class Calc_TF_V1(modeltools.Method):
    r"""Calculate the total amount of throughfall.

    Basic equation (discontinuous):
      .. math::
        TF = \begin{cases}
        P &|\ IC > IT
        \\
        0 &|\ IC < IT
        \end{cases}

    Examples:

        >>> from hydpy import pub, UnitTest
        >>> pub.timegrids = '2000-03-30', '2000-04-03', '1d'
        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> nu(1)
        >>> lt(FIELD)
        >>> ih(0.2)
        >>> lai.field_mar = 5.0
        >>> lai.field_apr = 10.0
        >>> derived.moy.update()
        >>> fluxes.pc = 5.0
        >>> test = UnitTest(
        ...     model=model,
        ...     method=model.calc_tf_v1,
        ...     last_example=6,
        ...     parseqs=(states.ic, fluxes.tf),
        ... )
        >>> test.nexts.ic = -4.0, 0.0, 1.0, 2.0, 3.0, 7.0

        Without smoothing:

        >>> sh(0.0)
        >>> derived.rh1.update()
        >>> model.idx_sim = pub.timegrids.init['2000-03-31']
        >>> test()
        | ex. |   ic |  tf |
        --------------------
        |   1 | -4.0 | 0.0 |
        |   2 |  0.0 | 0.0 |
        |   3 |  1.0 | 2.5 |
        |   4 |  2.0 | 5.0 |
        |   5 |  3.0 | 5.0 |
        |   6 |  7.0 | 5.0 |

        With smoothing:

        >>> sh(1.0)
        >>> derived.rh1.update()
        >>> model.idx_sim = pub.timegrids.init['2000-04-01']
        >>> test()
        | ex. |   ic |      tf |
        ------------------------
        |   1 | -4.0 |     0.0 |
        |   2 |  0.0 | 0.00051 |
        |   3 |  1.0 |    0.05 |
        |   4 |  2.0 |     2.5 |
        |   5 |  3.0 |    4.95 |
        |   6 |  7.0 |     5.0 |

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (
        wland_control.NU,
        wland_control.LT,
        wland_control.LAI,
        wland_control.IH,
    )
    DERIVEDPARAMETERS = (
        wland_derived.MOY,
        wland_derived.RH1,
    )
    REQUIREDSEQUENCES = (
        wland_fluxes.PC,
        wland_states.IC,
    )
    RESULTSEQUENCES = (wland_fluxes.TF,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nu):
            d_lai = con.lai[con.lt[k] - SEALED, der.moy[model.idx_sim]]
            flu.tf[k] = flu.pc * smoothutils.smooth_logistic1(
                sta.ic[k] - con.ih * d_lai, der.rh1
            )


class Calc_EI_V1(modeltools.Method):
    r"""Calculate the interception evaporation.

    Basic equation (discontinuous):
      .. math::
        EI = \begin{cases}
        PETL &|\ IC > 0
        \\
        0 &|\ IC < 0
        \end{cases}

    Examples:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> nu(1)
        >>> fluxes.petl = 5.0
        >>> from hydpy import UnitTest
        >>> test = UnitTest(
        ...     model=model,
        ...     method=model.calc_ei_v1,
        ...     last_example=9,
        ...     parseqs=(states.ic, fluxes.ei)
        ... )
        >>> test.nexts.ic= -4.0, -3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0

        Without smoothing:

        >>> sh(0.0)
        >>> derived.rh1.update()
        >>> test()
        | ex. |   ic |  ei |
        --------------------
        |   1 | -4.0 | 0.0 |
        |   2 | -3.0 | 0.0 |
        |   3 | -2.0 | 0.0 |
        |   4 | -1.0 | 0.0 |
        |   5 |  0.0 | 2.5 |
        |   6 |  1.0 | 5.0 |
        |   7 |  2.0 | 5.0 |
        |   8 |  3.0 | 5.0 |
        |   9 |  4.0 | 5.0 |

        With smoothing:

        >>> sh(1.0)
        >>> derived.rh1.update()
        >>> test()
        | ex. |   ic |       ei |
        -------------------------
        |   1 | -4.0 |      0.0 |
        |   2 | -3.0 | 0.000005 |
        |   3 | -2.0 |  0.00051 |
        |   4 | -1.0 |     0.05 |
        |   5 |  0.0 |      2.5 |
        |   6 |  1.0 |     4.95 |
        |   7 |  2.0 |  4.99949 |
        |   8 |  3.0 | 4.999995 |
        |   9 |  4.0 |      5.0 |
    """

    CONTROLPARAMETERS = (wland_control.NU,)
    REQUIREDSEQUENCES = (
        wland_fluxes.PETL,
        wland_states.IC,
    )
    RESULTSEQUENCES = (
        wland_fluxes.EI,
        wland_derived.RH1,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nu):
            flu.ei[k] = flu.petl[k] * (smoothutils.smooth_logistic1(sta.ic[k], der.rh1))


class Calc_FR_V1(modeltools.Method):
    r"""Determine the fraction between rainfall and total precipitation.

    Basic equation:
      :math:`FR = \frac{T- \left( TT - TI / 2 \right)}{TI}`

    Restriction:
      :math:`0 \leq FR \leq 1`

    Examples:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> tt(1.0)
        >>> ti(4.0)
        >>> from hydpy import UnitTest
        >>> test = UnitTest(
        ...     model=model,
        ...     method=model.calc_fr_v1,
        ...     last_example=9,
        ...     parseqs=(inputs.t, aides.fr)
        ... )
        >>> test.nexts.t = -3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0
        >>> test()
        | ex. |    t |   fr |
        ---------------------
        |   1 | -3.0 |  0.0 |
        |   2 | -2.0 |  0.0 |
        |   3 | -1.0 |  0.0 |
        |   4 |  0.0 | 0.25 |
        |   5 |  1.0 |  0.5 |
        |   6 |  2.0 | 0.75 |
        |   7 |  3.0 |  1.0 |
        |   8 |  4.0 |  1.0 |
        |   9 |  5.0 |  1.0 |
    """

    CONTROLPARAMETERS = (
        wland_control.TT,
        wland_control.TI,
    )
    REQUIREDSEQUENCES = (wland_inputs.T,)
    RESULTSEQUENCES = (wland_aides.FR,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        aid = model.sequences.aides.fastaccess
        if inp.t >= (con.tt + con.ti / 2.0):
            aid.fr = 1.0
        elif inp.t <= (con.tt - con.ti / 2.0):
            aid.fr = 0.0
        else:
            aid.fr = (inp.t - (con.tt - con.ti / 2.0)) / con.ti


class Calc_RF_V1(modeltools.Method):
    r"""Calculate the liquid amount of throughfall (rainfall).

    Basic equation:
      :math:`RF = FR \cdot TF`

    Example:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> nu(1)
        >>> fluxes.tf = 2.0
        >>> aides.fr = 0.8
        >>> model.calc_rf_v1()
        >>> fluxes.rf
        rf(1.6)
    """

    CONTROLPARAMETERS = (wland_control.NU,)
    REQUIREDSEQUENCES = (
        wland_fluxes.TF,
        wland_aides.FR,
    )
    RESULTSEQUENCES = (wland_fluxes.RF,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        aid = model.sequences.aides.fastaccess
        for k in range(con.nu):
            flu.rf[k] = aid.fr * flu.tf[k]


class Calc_SF_V1(modeltools.Method):
    r"""Calculate the frozen amount of throughfall (snowfall).

    Basic equation:
      :math:`SF = (1-FR) \cdot TF`

    Example:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> nu(1)
        >>> fluxes.tf = 2.0
        >>> aides.fr = 0.8
        >>> model.calc_sf_v1()
        >>> fluxes.sf
        sf(0.4)
    """

    CONTROLPARAMETERS = (wland_control.NU,)
    REQUIREDSEQUENCES = (
        wland_fluxes.TF,
        wland_aides.FR,
    )
    RESULTSEQUENCES = (wland_fluxes.SF,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        aid = model.sequences.aides.fastaccess
        for k in range(con.nu):
            flu.sf[k] = (1.0 - aid.fr) * flu.tf[k]


class Calc_PM_V1(modeltools.Method):
    r"""Calculate the potential snowmelt.

    Basic equation (discontinous):
      :math:`PM = max \left( DDF \cdot (T - DDT), 0 \right)`

    Examples:

        >>> from hydpy.models.wland import *
        >>> simulationstep('12h')
        >>> parameterstep('1d')
        >>> nu(1)
        >>> ddf(4.0)
        >>> ddt(1.0)
        >>> from hydpy import UnitTest
        >>> test = UnitTest(
        ...     model=model,
        ...     method=model.calc_pm_v1,
        ...     last_example=11,
        ...     parseqs=(inputs.t, fluxes.pm)
        ... )
        >>> test.nexts.t = -4.0, -3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0

        Without smoothing:

        >>> st(0.0)
        >>> derived.rt2.update()
        >>> test()
        | ex. |    t |   pm |
        ---------------------
        |   1 | -4.0 |  0.0 |
        |   2 | -3.0 |  0.0 |
        |   3 | -2.0 |  0.0 |
        |   4 | -1.0 |  0.0 |
        |   5 |  0.0 |  0.0 |
        |   6 |  1.0 |  0.0 |
        |   7 |  2.0 |  2.0 |
        |   8 |  3.0 |  4.0 |
        |   9 |  4.0 |  6.0 |
        |  10 |  5.0 |  8.0 |
        |  11 |  6.0 | 10.0 |

        With smoothing:

        >>> st(1.0)
        >>> derived.rt2.update()
        >>> test()
        | ex. |    t |       pm |
        -------------------------
        |   1 | -4.0 |      0.0 |
        |   2 | -3.0 | 0.000001 |
        |   3 | -2.0 | 0.000024 |
        |   4 | -1.0 | 0.000697 |
        |   5 |  0.0 |     0.02 |
        |   6 |  1.0 | 0.411048 |
        |   7 |  2.0 |     2.02 |
        |   8 |  3.0 | 4.000697 |
        |   9 |  4.0 | 6.000024 |
        |  10 |  5.0 | 8.000001 |
        |  11 |  6.0 |     10.0 |
    """

    CONTROLPARAMETERS = (
        wland_control.NU,
        wland_control.DDF,
        wland_control.DDT,
    )
    DERIVEDPARAMETERS = (wland_derived.RT2,)
    REQUIREDSEQUENCES = (wland_inputs.T,)
    RESULTSEQUENCES = (wland_fluxes.PM,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nu):
            flu.pm[k] = con.ddf[k] * smoothutils.smooth_logistic2(
                inp.t - con.ddt, der.rt2
            )


class Calc_AM_V1(modeltools.Method):
    r"""Calculate the actual snowmelt.

    Basic equation (discontinous):
      .. math::
        AM = \begin{cases}
        PM &|\ SP > 0
        \\
        0 &|\ SP < 0
        \end{cases}

    Examples:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> nu(1)
        >>> fluxes.pm = 2.0
        >>> from hydpy import UnitTest
        >>> test = UnitTest(
        ...     model=model,
        ...     method=model.calc_am_v1,
        ...     last_example=9,
        ...     parseqs=(states.sp, fluxes.am)
        ... )
        >>> test.nexts.sp = -4.0, -3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0

        Without smoothing:

        >>> sh(0.0)
        >>> derived.rh1.update()
        >>> test()
        | ex. |   sp |  am |
        --------------------
        |   1 | -4.0 | 0.0 |
        |   2 | -3.0 | 0.0 |
        |   3 | -2.0 | 0.0 |
        |   4 | -1.0 | 0.0 |
        |   5 |  0.0 | 1.0 |
        |   6 |  1.0 | 2.0 |
        |   7 |  2.0 | 2.0 |
        |   8 |  3.0 | 2.0 |
        |   9 |  4.0 | 2.0 |

        With smoothing:

        >>> sh(1.0)
        >>> derived.rh1.update()
        >>> test()
        | ex. |   sp |       am |
        -------------------------
        |   1 | -4.0 |      0.0 |
        |   2 | -3.0 | 0.000002 |
        |   3 | -2.0 | 0.000204 |
        |   4 | -1.0 |     0.02 |
        |   5 |  0.0 |      1.0 |
        |   6 |  1.0 |     1.98 |
        |   7 |  2.0 | 1.999796 |
        |   8 |  3.0 | 1.999998 |
        |   9 |  4.0 |      2.0 |
    """

    CONTROLPARAMETERS = (wland_control.NU,)
    DERIVEDPARAMETERS = (wland_derived.RH1,)
    REQUIREDSEQUENCES = (
        wland_fluxes.PM,
        wland_states.SP,
    )
    RESULTSEQUENCES = (wland_fluxes.AM,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for k in range(con.nu):
            flu.am[k] = flu.pm[k] * smoothutils.smooth_logistic1(sta.sp[k], der.rh1)


class Calc_PS_V1(modeltools.Method):
    r"""Calculate the precipitation entering the surface water reservoir.

    Basic equation:
      :math:`PS = PC`

    Example:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> fluxes.pc = 3.0
        >>> model.calc_ps_v1()
        >>> fluxes.ps
        ps(3.0)
    """

    REQUIREDSEQUENCES = (wland_fluxes.PC,)
    RESULTSEQUENCES = (wland_fluxes.PS,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.ps = flu.pc


class Calc_W_V1(modeltools.Method):
    r"""Calculate the wetness index.

    Basic equation:
      :math:`W = cos \left(
      \frac{max(min(DV, CW), 0) \cdot Pi}{CW} \right) \cdot \frac{1}{2} + \frac{1}{2}`

    Examples:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> cw(200.0)
        >>> from hydpy import UnitTest
        >>> test = UnitTest(
        ...     model=model,
        ...     method=model.calc_w_v1,
        ...     last_example=11,
        ...     parseqs=(states.dv, aides.w)
        ... )
        >>> test.nexts.dv = (
        ...     -50.0, -5.0, 0.0, 5.0, 50.0, 100.0, 150.0, 195.0, 200.0, 205.0, 250.0)
        >>> test()
        | ex. |    dv |        w |
        --------------------------
        |   1 | -50.0 |      1.0 |
        |   2 |  -5.0 |      1.0 |
        |   3 |   0.0 |      1.0 |
        |   4 |   5.0 | 0.998459 |
        |   5 |  50.0 | 0.853553 |
        |   6 | 100.0 |      0.5 |
        |   7 | 150.0 | 0.146447 |
        |   8 | 195.0 | 0.001541 |
        |   9 | 200.0 |      0.0 |
        |  10 | 205.0 |      0.0 |
        |  11 | 250.0 |      0.0 |
    """

    CONTROLPARAMETERS = (wland_control.CW,)
    FIXEDPARAMETERS = (wland_fixed.Pi,)
    REQUIREDSEQUENCES = (wland_states.DV,)
    RESULTSEQUENCES = (wland_aides.W,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fix = model.parameters.fixed.fastaccess
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess
        aid.w = 0.5 + 0.5 * modelutils.cos(
            max(min(sta.dv, con.cw), 0.0) * fix.pi / con.cw
        )


class Calc_PV_V1(modeltools.Method):
    r"""Calculate the rainfall (and snowmelt) entering the vadose zone.

    Basic equation:
      .. math::
        PV = \Sigma \left ( \frac{AUR}{AGR} \cdot (RF + AM) \cdot \begin{cases}
        0 &|\ LT = SEALED
        \\
        1-W &|\ LT \neq SEALED
        \end{cases}  \right )

    Example:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> nu(3)
        >>> lt(FIELD, SOIL, SEALED)
        >>> aur(0.7, 0.2, 0.1)
        >>> derived.agr.update()
        >>> fluxes.rf = 3.0, 2.0, 1.0
        >>> fluxes.am = 1.0, 2.0, 3.0
        >>> aides.w = 0.75
        >>> model.calc_pv_v1()
        >>> fluxes.pv
        pv(1.0)
    """

    CONTROLPARAMETERS = (
        wland_control.NU,
        wland_control.LT,
        wland_control.AUR,
    )
    DERIVEDPARAMETERS = (wland_derived.AGR,)
    REQUIREDSEQUENCES = (
        wland_fluxes.RF,
        wland_fluxes.AM,
        wland_aides.W,
    )
    RESULTSEQUENCES = (wland_fluxes.PV,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        aid = model.sequences.aides.fastaccess
        flu.pv = 0.0
        for k in range(con.nu):
            if con.lt[k] != SEALED:
                flu.pv += (1.0 - aid.w) * con.aur[k] / der.agr * (flu.rf[k] + flu.am[k])


class Calc_PQ_V1(modeltools.Method):
    r"""Calculate the rainfall (and snowmelt) entering the quickflow reservoir.

    Basic equation:
      .. math::
        PQ = \Sigma \left( AUR \cdot (RF + AM) \cdot \begin{cases}
        1 &|\ LT = SEALED
        \\
        W &|\ LT \neq SEALED
        \end{cases} \right)

    Example:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> nu(3)
        >>> lt(FIELD, SOIL, SEALED)
        >>> aur(0.6, 0.3, 0.1)
        >>> fluxes.rf = 3.0, 2.0, 1.0
        >>> fluxes.am = 1.0, 2.0, 2.0
        >>> aides.w = 0.75
        >>> model.calc_pq_v1()
        >>> fluxes.pq
        pq(3.0)
    """

    CONTROLPARAMETERS = (
        wland_control.NU,
        wland_control.LT,
        wland_control.AUR,
    )
    REQUIREDSEQUENCES = (
        wland_fluxes.RF,
        wland_fluxes.AM,
        wland_aides.W,
    )
    RESULTSEQUENCES = (wland_fluxes.PQ,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        aid = model.sequences.aides.fastaccess
        flu.pq = 0.0
        for k in range(con.nu):
            d_pq = con.aur[k] * (flu.rf[k] + flu.am[k])
            if con.lt[k] != SEALED:
                d_pq *= aid.w
            flu.pq += d_pq


class Calc_Beta_V1(modeltools.Method):
    r"""Calculate the evapotranspiration reduction factor.

    Basic equations:
      :math:`Beta = \frac{1 - x}{1 + x} \cdot \frac{1}{2} + \frac{1}{2}`

      :math:`x = exp \left( Zeta1 \cdot (DV - Zeta2) \right)`

    Examples:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> zeta1(0.02)
        >>> zeta2(400.0)
        >>> from hydpy import UnitTest
        >>> test = UnitTest(
        ...     model=model,
        ...     method=model.calc_beta_v1,
        ...     last_example=12,
        ...     parseqs=(states.dv, aides.beta)
        ... )
        >>> test.nexts.dv = (
        ...     -100.0, 0.0, 100.0, 200.0, 300.0, 400.0,
        ...     500.0, 600.0, 700.0, 800.0, 900.0, 100000.0
        ... )
        >>> test()
        | ex. |       dv |     beta |
        -----------------------------
        |   1 |   -100.0 | 0.999955 |
        |   2 |      0.0 | 0.999665 |
        |   3 |    100.0 | 0.997527 |
        |   4 |    200.0 | 0.982014 |
        |   5 |    300.0 | 0.880797 |
        |   6 |    400.0 |      0.5 |
        |   7 |    500.0 | 0.119203 |
        |   8 |    600.0 | 0.017986 |
        |   9 |    700.0 | 0.002473 |
        |  10 |    800.0 | 0.000335 |
        |  11 |    900.0 | 0.000045 |
        |  12 | 100000.0 |      0.0 |
    """

    CONTROLPARAMETERS = (
        wland_control.Zeta1,
        wland_control.Zeta2,
    )
    REQUIREDSEQUENCES = (wland_states.DV,)
    RESULTSEQUENCES = (wland_aides.Beta,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess
        d_temp = con.zeta1 * (sta.dv - con.zeta2)
        if d_temp > 700.0:
            aid.beta = 0.0
        else:
            d_temp = modelutils.exp(d_temp)
            aid.beta = 0.5 + 0.5 * (1.0 - d_temp) / (1.0 + d_temp)


class Calc_ETV_V1(modeltools.Method):
    r"""Calculate the actual evapotranspiration from the vadose zone.

    Basic equation:
      .. math::
        ETV = \Sigma \left( \frac{AUR}{AGR} \cdot (PETL -  EI) \cdot \begin{cases}
        0 &|\ LT = SEALED
        \\
        Beta  &|\ LT \neq SEALED
        \end{cases}  \right)

    Example:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> nu(3)
        >>> lt(FIELD, SOIL, SEALED)
        >>> aur(0.4, 0.4, 0.2)
        >>> derived.agr.update()
        >>> fluxes.petl = 5.0
        >>> fluxes.ei = 1.0, 3.0, 2.0
        >>> aides.beta = 0.75
        >>> model.calc_etv_v1()
        >>> fluxes.etv
        etv(2.25)
    """

    CONTROLPARAMETERS = (
        wland_control.NU,
        wland_control.LT,
        wland_control.AUR,
    )
    DERIVEDPARAMETERS = (wland_derived.AGR,)
    REQUIREDSEQUENCES = (
        wland_fluxes.PETL,
        wland_fluxes.EI,
        wland_aides.Beta,
    )
    RESULTSEQUENCES = (wland_fluxes.ETV,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        aid = model.sequences.aides.fastaccess
        flu.etv = 0.0
        for k in range(con.nu):
            if con.lt[k] != SEALED:
                flu.etv += aid.beta * con.aur[k] / der.agr * (flu.petl[k] - flu.ei[k])


class Calc_ES_V1(modeltools.Method):
    r"""Calculate the actual evaporation from the surface water reservoir.

    Basic equation (discontinous):
      .. math::
        ES = \begin{cases}
        PES &|\ HS > 0
        \\
        0 &|\ HS \leq 0
        \end{cases}

    Examples:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> fluxes.pes = 5.0
        >>> from hydpy import UnitTest
        >>> test = UnitTest(
        ...     model=model,
        ...     method=model.calc_es_v1,
        ...     last_example=9,
        ...     parseqs=(states.hs, fluxes.es)
        ... )
        >>> test.nexts.hs = -4.0, -3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0

        Without smoothing:

        >>> sh(0.0)
        >>> derived.rh1.update()
        >>> test()
        | ex. |   hs |  es |
        --------------------
        |   1 | -4.0 | 0.0 |
        |   2 | -3.0 | 0.0 |
        |   3 | -2.0 | 0.0 |
        |   4 | -1.0 | 0.0 |
        |   5 |  0.0 | 2.5 |
        |   6 |  1.0 | 5.0 |
        |   7 |  2.0 | 5.0 |
        |   8 |  3.0 | 5.0 |
        |   9 |  4.0 | 5.0 |

        With smoothing:

        >>> sh(1.0)
        >>> derived.rh1.update()
        >>> test()
        | ex. |   hs |       es |
        -------------------------
        |   1 | -4.0 |      0.0 |
        |   2 | -3.0 | 0.000005 |
        |   3 | -2.0 |  0.00051 |
        |   4 | -1.0 |     0.05 |
        |   5 |  0.0 |      2.5 |
        |   6 |  1.0 |     4.95 |
        |   7 |  2.0 |  4.99949 |
        |   8 |  3.0 | 4.999995 |
        |   9 |  4.0 |      5.0 |
    """
    DERIVEDPARAMETERS = (wland_derived.RH1,)
    REQUIREDSEQUENCES = (
        wland_fluxes.PES,
        wland_states.HS,
    )
    RESULTSEQUENCES = (wland_fluxes.ES,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        flu.es = flu.pes * smoothutils.smooth_logistic1(sta.hs, der.rh1)


class Calc_ET_V1(modeltools.Method):
    r"""Calculate the total actual evapotranspiration.

    Basic equation:
      :math:`ET = ALR \cdot \bigl( \Sigma (AUR \cdot EI) + AGR \cdot ETV \bigl ) +
      ASR \cdot ES`

    Example:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> nu(2)
        >>> aur(0.8, 0.2)
        >>> derived.alr(0.8)
        >>> derived.asr(0.2)
        >>> derived.agr(0.5)
        >>> fluxes.ei = 0.5, 3.0
        >>> fluxes.etv = 2.0
        >>> fluxes.es = 3.0
        >>> model.calc_et_v1()
        >>> fluxes.et
        et(2.2)
    """

    CONTROLPARAMETERS = (
        wland_control.NU,
        wland_control.AUR,
    )
    DERIVEDPARAMETERS = (
        wland_derived.ALR,
        wland_derived.ASR,
        wland_derived.AGR,
    )
    REQUIREDSEQUENCES = (
        wland_fluxes.EI,
        wland_fluxes.ETV,
        wland_fluxes.ES,
    )
    RESULTSEQUENCES = (wland_fluxes.ET,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        d_ei = 0.0
        for k in range(con.nu):
            d_ei += con.aur[k] * flu.ei[k]
        flu.et = der.alr * (d_ei + der.agr * flu.etv) + der.asr * flu.es


class Calc_DVEq_V1(modeltools.Method):
    r"""Calculate the equilibrium storage deficit of the vadose zone.

    Basic equation (discontinuous):
      .. math::
        DVEq =
        \begin{cases}
          DG &|\ DG \leq 0
          \\
          0 &|\ 0 < DG \leq PsiAE
          \\
          ThetaS \cdot \left( DG - \frac{DG^{1-1/b}}{(1-1/b) \cdot PsiAE^{-1/B}} -
          \frac{PsiAE}{1-B} \right) &|\ PsiAE < DG
        \end{cases}

    Examples:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> thetas(0.4)
        >>> psiae(300.0)
        >>> b(5.0)
        >>> from hydpy import UnitTest
        >>> test = UnitTest(
        ...     model=model,
        ...     method=model.calc_dveq_v1,
        ...     last_example=11,
        ...     parseqs=(states.dg, aides.dveq)
        ... )
        >>> test.nexts.dg = (
        ...     -50.0, -1.0, 0.0, 1.0, 50.0, 100.0,
        ...     200.0, 400.0, 800.0, 1600.0, 3200.0,
        ... )

        Without smoothing:

        >>> sh(0.0)
        >>> derived.rh1.update()
        >>> test()
        | ex. |     dg |       dveq |
        -----------------------------
        |   1 |  -50.0 |      -50.0 |
        |   2 |   -1.0 |       -1.0 |
        |   3 |    0.0 |        0.0 |
        |   4 |    1.0 |        0.0 |
        |   5 |   50.0 |        0.0 |
        |   6 |  100.0 |        0.0 |
        |   7 |  200.0 |        0.0 |
        |   8 |  400.0 |   1.182498 |
        |   9 |  800.0 |  21.249634 |
        |  10 | 1600.0 |  97.612368 |
        |  11 | 3200.0 | 313.415248 |

        With smoothing:

        >>> sh(1.0)
        >>> derived.rh1.update()
        >>> test()
        | ex. |     dg |       dveq |
        -----------------------------
        |   1 |  -50.0 |      -50.0 |
        |   2 |   -1.0 |  -1.002187 |
        |   3 |    0.0 |  -0.150844 |
        |   4 |    1.0 |  -0.002187 |
        |   5 |   50.0 |        0.0 |
        |   6 |  100.0 |        0.0 |
        |   7 |  200.0 |        0.0 |
        |   8 |  400.0 |   1.182498 |
        |   9 |  800.0 |  21.249634 |
        |  10 | 1600.0 |  97.612368 |
        |  11 | 3200.0 | 313.415248 |
    """

    CONTROLPARAMETERS = (
        wland_control.ThetaS,
        wland_control.PsiAE,
        wland_control.B,
    )
    DERIVEDPARAMETERS = (
        wland_derived.NUG,
        wland_derived.RH1,
    )
    REQUIREDSEQUENCES = (wland_states.DG,)
    RESULTSEQUENCES = (wland_aides.DVEq,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess
        if der.nug:
            if sta.dg <= con.psiae:
                aid.dveq = smoothutils.smooth_min1(sta.dg, 0.0, der.rh1)
            else:
                aid.dveq = con.thetas * (
                    sta.dg
                    - sta.dg ** (1.0 - 1.0 / con.b)
                    / (1.0 - 1.0 / con.b)
                    / con.psiae ** (-1.0 / con.b)
                    - con.psiae / (1.0 - con.b)
                )
        else:
            aid.dveq = modelutils.nan


class Calc_CDG_V1(modeltools.Method):
    r"""Calculate the change in the groundwater depth due to percolation and
    capillary rise.

    Basic equation:
      :math:`CDG = \frac{DV-DVEq}{CV}`

    Example:

        >>> from hydpy.models.wland import *
        >>> simulationstep('12h')
        >>> parameterstep('1d')
        >>> cv(10.0)
        >>> states.dv = 100.0
        >>> aides.dveq = 80.0
        >>> model.calc_cdg_v1()
        >>> fluxes.cdg
        cdg(1.0)
    """

    CONTROLPARAMETERS = (wland_control.CV,)
    DERIVEDPARAMETERS = (wland_derived.NUG,)
    REQUIREDSEQUENCES = (
        wland_states.DV,
        wland_aides.DVEq,
    )
    RESULTSEQUENCES = (wland_fluxes.CDG,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess
        if der.nug:
            flu.cdg = (sta.dv - aid.dveq) / con.cv
        else:
            flu.cdg = 0.0


class Calc_FGS_V1(modeltools.Method):
    r"""Calculate the groundwater drainage or surface water infiltration.

    For large-scale ponding, |wland| and `WALRUS`_ calculate |FGS| differently
    (even for discontinuous parameterisations).  The `WALRUS`_  model redistributes
    water instantaneously in such cases (see :cite:`ref-Brauer2014`, section 5.11),
    which relates to infinitely high flow velocities and cannot be handled by the
    numerical integration algorithm underlying |wland|.  Hence, we instead introduce
    the parameter |CGF|.  Setting it to a value larger zero increases the flow
    velocity with increasing large-scale ponding.  The larger the value of |CGF|,
    the stronger the functional similarity of both approaches.  But note that very
    high values can result in increased computation times.

    Basic equations (discontinous):
      :math:`Gradient = CD - DG - HS`

      :math:`ContactSurface = max \left( CD - DG, HS \right)`

      :math:`Excess = max \left( -DG, HS - CD, 0 \right)`

      :math:`Conductivity = \frac{1 + CGF \cdot Excess}{CG}`

      :math:`FGS = Gradient \cdot ContactSurface \cdot Conductivity`

    Examples:

        >>> from hydpy.models.wland import *
        >>> simulationstep('12h')
        >>> parameterstep('1d')
        >>> cd(600.0)
        >>> cg(10000.0)
        >>> states.hs = 300.0
        >>> from hydpy import UnitTest
        >>> test = UnitTest(model=model,
        ...                 method=model.calc_fgs_v1,
        ...                 last_example=15,
        ...                 parseqs=(states.dg, states.hs, fluxes.fgs))
        >>> test.nexts.dg = (
        ...     -100.0, -1.0, 0.0, 1.0, 100.0, 200.0, 290.0, 299.0,
        ...     300.0, 301.0, 310.0, 400.0, 500.0, 600.0, 700.0)

        Without smoothing and without increased conductivity for large-scale ponding:

        >>> cgf(0.0)
        >>> sh(0.0)
        >>> derived.rh2.update()
        >>> test()
        | ex. |     dg |    hs |     fgs |
        ----------------------------------
        |   1 | -100.0 | 300.0 |    14.0 |
        |   2 |   -1.0 | 300.0 | 9.04505 |
        |   3 |    0.0 | 300.0 |     9.0 |
        |   4 |    1.0 | 300.0 | 8.95505 |
        |   5 |  100.0 | 300.0 |     5.0 |
        |   6 |  200.0 | 300.0 |     2.0 |
        |   7 |  290.0 | 300.0 |   0.155 |
        |   8 |  299.0 | 300.0 | 0.01505 |
        |   9 |  300.0 | 300.0 |     0.0 |
        |  10 |  301.0 | 300.0 |  -0.015 |
        |  11 |  310.0 | 300.0 |   -0.15 |
        |  12 |  400.0 | 300.0 |    -1.5 |
        |  13 |  500.0 | 300.0 |    -3.0 |
        |  14 |  600.0 | 300.0 |    -4.5 |
        |  15 |  700.0 | 300.0 |    -6.0 |

        Without smoothing but with increased conductivity for large-scale ponding:

        >>> cgf(0.1)
        >>> test()
        | ex. |     dg |    hs |      fgs |
        -----------------------------------
        |   1 | -100.0 | 300.0 |    294.0 |
        |   2 |   -1.0 | 300.0 | 10.85406 |
        |   3 |    0.0 | 300.0 |      9.0 |
        |   4 |    1.0 | 300.0 |  8.95505 |
        |   5 |  100.0 | 300.0 |      5.0 |
        |   6 |  200.0 | 300.0 |      2.0 |
        |   7 |  290.0 | 300.0 |    0.155 |
        |   8 |  299.0 | 300.0 |  0.01505 |
        |   9 |  300.0 | 300.0 |      0.0 |
        |  10 |  301.0 | 300.0 |   -0.015 |
        |  11 |  310.0 | 300.0 |    -0.15 |
        |  12 |  400.0 | 300.0 |     -1.5 |
        |  13 |  500.0 | 300.0 |     -3.0 |
        |  14 |  600.0 | 300.0 |     -4.5 |
        |  15 |  700.0 | 300.0 |     -6.0 |

        With smoothing and with increased conductivity for large-scale ponding:

        >>> sh(1.0)
        >>> derived.rh2.update()
        >>> test()
        | ex. |     dg |    hs |      fgs |
        -----------------------------------
        |   1 | -100.0 | 300.0 |    294.0 |
        |   2 |   -1.0 | 300.0 | 10.87215 |
        |   3 |    0.0 | 300.0 | 9.369944 |
        |   4 |    1.0 | 300.0 |  8.97296 |
        |   5 |  100.0 | 300.0 |      5.0 |
        |   6 |  200.0 | 300.0 |      2.0 |
        |   7 |  290.0 | 300.0 |    0.155 |
        |   8 |  299.0 | 300.0 |  0.01505 |
        |   9 |  300.0 | 300.0 |      0.0 |
        |  10 |  301.0 | 300.0 |   -0.015 |
        |  11 |  310.0 | 300.0 |    -0.15 |
        |  12 |  400.0 | 300.0 |     -1.5 |
        |  13 |  500.0 | 300.0 |     -3.0 |
        |  14 |  600.0 | 300.0 |     -4.5 |
        |  15 |  700.0 | 300.0 |     -6.0 |
    """

    CONTROLPARAMETERS = (
        wland_control.CD,
        wland_control.CG,
        wland_control.CGF,
    )
    DERIVEDPARAMETERS = (
        wland_derived.NUG,
        wland_derived.RH2,
    )
    REQUIREDSEQUENCES = (
        wland_states.DG,
        wland_states.HS,
    )
    RESULTSEQUENCES = (wland_fluxes.FGS,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        if der.nug:
            d_gradient = con.cd - sta.dg - sta.hs
            d_contactsurface = smoothutils.smooth_max1(con.cd - sta.dg, sta.hs, der.rh2)
            d_excess = smoothutils.smooth_max2(-sta.dg, sta.hs - con.cd, 0.0, der.rh2)
            d_conductivity = (1.0 + con.cgf * d_excess) / con.cg
            flu.fgs = d_gradient * d_contactsurface * d_conductivity
        else:
            flu.fgs = 0.0


class Calc_FQS_V1(modeltools.Method):
    r"""Calculate the quickflow.

    Basic equation:
      :math:`FQS = \frac{HQ}{CQ}`

    Example:

        >>> from hydpy.models.wland import *
        >>> simulationstep('12h')
        >>> parameterstep('1d')
        >>> cq(10.0)
        >>> states.hq = 100.0
        >>> model.calc_fqs_v1()
        >>> fluxes.fqs
        fqs(5.0)
    """

    CONTROLPARAMETERS = (
        wland_control.NU,
        wland_control.CQ,
    )
    REQUIREDSEQUENCES = (wland_states.HQ,)
    RESULTSEQUENCES = (wland_fluxes.FQS,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        if con.nu:
            flu.fqs = sta.hq / con.cq
        else:
            flu.fqs = 0.0


class Calc_RH_V1(modeltools.Method):
    r"""Calculate the runoff height.

    Basic equation (discontinuous):
      :math:`RH = CS \cdot \left( \frac{max(HS-HSMin, 0)}{CD-HSMin} \right) ^ {XS}`

    Examples:

        >>> from hydpy.models.wland import *
        >>> simulationstep('12h')
        >>> parameterstep('1d')
        >>> cs(2.0)
        >>> cd(5.0)
        >>> hsmin(2.0)
        >>> xs(2.0)
        >>> from hydpy import UnitTest
        >>> test = UnitTest(
        ...     model=model,
        ...     method=model.calc_rh_v1,
        ...     last_example=11,
        ...     parseqs=(states.hs, fluxes.rh)
        ... )
        >>> test.nexts.hs = 0.0, 1.0, 1.9, 2.0, 2.1, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0

        Without smoothing:

        >>> sh(0.0)
        >>> derived.rh2.update()
        >>> test()
        | ex. |  hs |       rh |
        ------------------------
        |   1 | 0.0 |      0.0 |
        |   2 | 1.0 |      0.0 |
        |   3 | 1.9 |      0.0 |
        |   4 | 2.0 |      0.0 |
        |   5 | 2.1 | 0.001111 |
        |   6 | 3.0 | 0.111111 |
        |   7 | 4.0 | 0.444444 |
        |   8 | 5.0 |      1.0 |
        |   9 | 6.0 | 1.777778 |
        |  10 | 7.0 | 2.777778 |
        |  11 | 8.0 |      4.0 |

        With smoothing:

        >>> sh(0.1)
        >>> derived.rh2.update()
        >>> test()
        | ex. |  hs |       rh |
        ------------------------
        |   1 | 0.0 |      0.0 |
        |   2 | 1.0 |      0.0 |
        |   3 | 1.9 | 0.000011 |
        |   4 | 2.0 | 0.000187 |
        |   5 | 2.1 | 0.001344 |
        |   6 | 3.0 | 0.111111 |
        |   7 | 4.0 | 0.444444 |
        |   8 | 5.0 |      1.0 |
        |   9 | 6.0 | 1.777778 |
        |  10 | 7.0 | 2.777778 |
        |  11 | 8.0 |      4.0 |
    """

    CONTROLPARAMETERS = (
        wland_control.CS,
        wland_control.CD,
        wland_control.HSMin,
        wland_control.XS,
    )
    DERIVEDPARAMETERS = (wland_derived.RH2,)
    REQUIREDSEQUENCES = (wland_states.HS,)
    RESULTSEQUENCES = (wland_fluxes.RH,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        d_hs = smoothutils.smooth_logistic2(sta.hs - con.hsmin, der.rh2)
        flu.rh = con.cs * (d_hs / (con.cd - con.hsmin)) ** con.xs


class Update_IC_V1(modeltools.Method):
    r"""Update the interception storage.

    Basic equation:
      :math:`\frac{dIC}{dt} = PC - TF - EI`

    Example:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> nu(1)
        >>> fluxes.pc = 2.0
        >>> fluxes.tf = 1.0
        >>> fluxes.ei = 3.0
        >>> states.ic.old = 4.0
        >>> model.update_ic_v1()
        >>> states.ic
        ic(2.0)
    """

    CONTROLPARAMETERS = (wland_control.NU,)
    REQUIREDSEQUENCES = (
        wland_fluxes.PC,
        wland_fluxes.TF,
        wland_fluxes.EI,
    )
    UPDATEDSEQUENCES = (wland_states.IC,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        for k in range(con.nu):
            new.ic[k] = old.ic[k] + (flu.pc - flu.tf[k] - flu.ei[k])


class Update_SP_V1(modeltools.Method):
    r"""Update the storage deficit.

    Basic equation:
      :math:`\frac{dSP}{dt} = SF - AM`

    Example:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> nu(1)
        >>> fluxes.sf = 1.0
        >>> fluxes.am = 2.0
        >>> states.sp.old = 3.0
        >>> model.update_sp_v1()
        >>> states.sp
        sp(2.0)
    """

    CONTROLPARAMETERS = (wland_control.NU,)
    REQUIREDSEQUENCES = (
        wland_fluxes.SF,
        wland_fluxes.AM,
    )
    UPDATEDSEQUENCES = (wland_states.SP,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        for k in range(con.nu):
            new.sp[k] = old.sp[k] + (flu.sf[k] - flu.am[k])


class Update_DV_V1(modeltools.Method):
    r"""Update the storage deficit of the vadose zone.

    Basic equation:
      :math:`\frac{dDV}{dt} = -(FXG + PV - ETV - FGS)`

    Example:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> fluxes.fxg = 1.0
        >>> fluxes.pv = 2.0
        >>> fluxes.etv = 3.0
        >>> fluxes.fgs = 4.0
        >>> states.dv.old = 5.0
        >>> model.update_dv_v1()
        >>> states.dv
        dv(9.0)
    """
    DERIVEDPARAMETERS = (wland_derived.NUG,)
    REQUIREDSEQUENCES = (
        wland_fluxes.FXG,
        wland_fluxes.PV,
        wland_fluxes.ETV,
        wland_fluxes.FGS,
    )
    UPDATEDSEQUENCES = (wland_states.DV,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        if der.nug:
            new.dv = old.dv - (flu.fxg + flu.pv - flu.etv - flu.fgs)
        else:
            new.dv = modelutils.nan


class Update_DG_V1(modeltools.Method):
    r"""Update the groundwater depth.

    Basic equations:
      :math:`\frac{dDG}{dt} = CDG`

    Example:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> states.dg.old = 2.0
        >>> fluxes.cdg = 3.0
        >>> model.update_dg_v1()
        >>> states.dg
        dg(5.0)
    """
    DERIVEDPARAMETERS = (wland_derived.NUG,)
    REQUIREDSEQUENCES = (wland_fluxes.CDG,)
    UPDATEDSEQUENCES = (wland_states.DG,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        if der.nug:
            new.dg = old.dg + flu.cdg
        else:
            new.dg = modelutils.nan


class Update_HQ_V1(modeltools.Method):
    r"""Update the level of the quickflow reservoir.

    Basic equations:
      :math:`\frac{dHQ}{dt} = PQ - FQS`

    Example:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> states.hq.old = 2.0
        >>> fluxes.pq = 3.0
        >>> fluxes.fqs = 4.0
        >>> model.update_hq_v1()
        >>> states.hq
        hq(1.0)
    """

    REQUIREDSEQUENCES = (
        wland_fluxes.PQ,
        wland_fluxes.FQS,
    )
    UPDATEDSEQUENCES = (wland_states.HQ,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        new.hq = old.hq + (flu.pq - flu.fqs)


class Update_HS_V1(modeltools.Method):
    r"""Update the surface water level.

    Basic equations:
      :math:`\frac{dHS}{dt} = PS - ETS + FXS
      + \frac{ALR \cdot \left(AGR \cdot FGS + FQS \right) - RH}{ASR}`

    Example:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> derived.alr(0.8)
        >>> derived.asr(0.2)
        >>> derived.agr(1.0)
        >>> states.hs.old = 2.0
        >>> fluxes.fxs = 3.0
        >>> fluxes.ps = 4.0
        >>> fluxes.es = 5.0
        >>> fluxes.fgs = 6.0
        >>> fluxes.fqs = 7.0
        >>> fluxes.rh = 8.0
        >>> model.update_hs_v1()
        >>> states.hs
        hs(16.0)
    """

    DERIVEDPARAMETERS = (
        wland_derived.ALR,
        wland_derived.ASR,
        wland_derived.AGR,
    )
    REQUIREDSEQUENCES = (
        wland_fluxes.FXS,
        wland_fluxes.PS,
        wland_fluxes.ES,
        wland_fluxes.FGS,
        wland_fluxes.FQS,
        wland_fluxes.RH,
    )
    UPDATEDSEQUENCES = (wland_states.HS,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        new.hs = (
            old.hs
            + (flu.fxs + flu.ps - flu.es)
            - flu.rh / der.asr
            + der.alr / der.asr * flu.fqs
            + (der.alr * der.agr) / der.asr * flu.fgs
        )


class Calc_R_V1(modeltools.Method):
    r"""Calculate the runoff in m³/s.

    Basic equation:
       :math:`R = QF \cdot RH`

    Example:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> derived.qf(2.0)
        >>> fluxes.rh = 3.0
        >>> model.calc_r_v1()
        >>> fluxes.r
        r(6.0)
    """

    DERIVEDPARAMETERS = (wland_derived.QF,)
    REQUIREDSEQUENCES = (wland_fluxes.RH,)
    RESULTSEQUENCES = (wland_fluxes.R,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.r = der.qf * flu.rh


class Pass_R_V1(modeltools.Method):
    r"""Update the outlet link sequence.

    Basic equation:
       :math:`Q = R`
    """

    REQUIREDSEQUENCES = (wland_fluxes.R,)
    RESULTSEQUENCES = (wland_outlets.Q,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        out = model.sequences.outlets.fastaccess
        out.q[0] += flu.r


class Model(modeltools.ELSModel):
    """The *HydPy-W-Land* model."""

    SOLVERPARAMETERS = (
        wland_solver.AbsErrorMax,
        wland_solver.RelErrorMax,
        wland_solver.RelDTMin,
        wland_solver.RelDTMax,
    )
    SOLVERSEQUENCES = ()
    INLET_METHODS = (
        Calc_FR_V1,
        Calc_PM_V1,
    )
    RECEIVER_METHODS = ()
    ADD_METHODS = ()
    PART_ODE_METHODS = (
        Calc_FXS_V1,
        Calc_FXG_V1,
        Calc_PC_V1,
        Calc_PETL_V1,
        Calc_PES_V1,
        Calc_TF_V1,
        Calc_EI_V1,
        Calc_SF_V1,
        Calc_RF_V1,
        Calc_AM_V1,
        Calc_PS_V1,
        Calc_W_V1,
        Calc_PV_V1,
        Calc_PQ_V1,
        Calc_Beta_V1,
        Calc_ETV_V1,
        Calc_ES_V1,
        Calc_FQS_V1,
        Calc_FGS_V1,
        Calc_RH_V1,
        Calc_DVEq_V1,
        Calc_CDG_V1,
    )
    FULL_ODE_METHODS = (
        Update_IC_V1,
        Update_SP_V1,
        Update_DV_V1,
        Update_DG_V1,
        Update_HQ_V1,
        Update_HS_V1,
    )
    OUTLET_METHODS = (
        Calc_ET_V1,
        Calc_R_V1,
        Pass_R_V1,
    )
    SENDER_METHODS = ()
    SUBMODELS = ()
