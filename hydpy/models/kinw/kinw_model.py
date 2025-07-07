# pylint: disable=missing-module-docstring

# import...
# ...from site-packages
import numpy

# ...from HydPy
from hydpy.auxs import roottools
from hydpy.core import exceptiontools
from hydpy.core import modeltools
from hydpy.core import objecttools
from hydpy.core.typingtools import *
from hydpy.cythons import smoothutils
from hydpy.models.kinw import kinw_control
from hydpy.models.kinw import kinw_derived
from hydpy.models.kinw import kinw_fixed
from hydpy.models.kinw import kinw_solver
from hydpy.models.kinw import kinw_fluxes
from hydpy.models.kinw import kinw_factors
from hydpy.models.kinw import kinw_states
from hydpy.models.kinw import kinw_aides
from hydpy.models.kinw import kinw_inlets
from hydpy.models.kinw import kinw_outlets

if TYPE_CHECKING:
    from matplotlib import pyplot
else:
    pyplot = exceptiontools.OptionalImport("pyplot", ["matplotlib.pyplot"], locals())


class Pick_Q_V1(modeltools.Method):
    r"""Query the current inflow from all inlet nodes.

    Basic equation:
      :math:`QZ = \sum Q`

    Example:

        >>> from hydpy.models.kinw import *
        >>> parameterstep()
        >>> inlets.q.shape = 2
        >>> inlets.q = 2.0, 4.0
        >>> model.pick_q_v1()
        >>> fluxes.qz
        qz(6.0)
    """

    REQUIREDSEQUENCES = (kinw_inlets.Q,)
    RESULTSEQUENCES = (kinw_fluxes.QZ,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        inl = model.sequences.inlets.fastaccess
        flu.qz = 0.0
        for idx in range(inl.len_q):
            flu.qz += inl.q[idx]


class Pick_Inflow_V1(modeltools.Method):
    r"""Sum up the current inflow from all inlet nodes.

    Basic equation:
      :math:`Inflow = \sum Q`

    Example:

        >>> from hydpy.models.kinw import *
        >>> parameterstep()
        >>> inlets.q.shape = 2
        >>> inlets.q = 2.0, 4.0
        >>> model.pick_inflow_v1()
        >>> fluxes.inflow
        inflow(6.0)
    """

    REQUIREDSEQUENCES = (kinw_inlets.Q,)
    RESULTSEQUENCES = (kinw_fluxes.Inflow,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        inl = model.sequences.inlets.fastaccess
        flu = model.sequences.fluxes.fastaccess

        flu.inflow = 0.0
        for idx in range(inl.len_q):
            flu.inflow += inl.q[idx]


class Calc_QZA_V1(modeltools.Method):
    """Calculate the current inflow into the channel.

    Basic equation:
      :math:`QZA = QZ`
    """

    REQUIREDSEQUENCES = (kinw_fluxes.QZ,)
    RESULTSEQUENCES = (kinw_fluxes.QZA,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.qza = flu.qz


class Calc_RHM_V1(modeltools.Method):
    """Regularise the stage with respect to the channel bottom.

    Used auxiliary method:
      |smooth_logistic2|

    Basic equation:
      :math:`RHM = smooth_{logistic2}(H, HRP)`

    Examples:

        >>> from hydpy.models.kinw import *
        >>> parameterstep()
        >>> gts(5)
        >>> states.h = -1.0, -0.1, 0.0, 0.1, 1.0

        >>> hr(0.0)
        >>> derived.hrp.update()
        >>> model.calc_rhm_v1()
        >>> aides.rhm
        rhm(0.0, 0.0, 0.0, 0.1, 1.0)

        >>> hr(0.1)
        >>> derived.hrp.update()
        >>> model.calc_rhm_v1()
        >>> aides.rhm
        rhm(0.0, 0.01, 0.040983, 0.11, 1.0)
    """

    CONTROLPARAMETERS = (kinw_control.GTS,)
    DERIVEDPARAMETERS = (kinw_derived.HRP,)
    REQUIREDSEQUENCES = (kinw_states.H,)
    RESULTSEQUENCES = (kinw_aides.RHM,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            aid.rhm[i] = smoothutils.smooth_logistic2(sta.h[i], der.hrp)


class Calc_RHMDH_V1(modeltools.Method):
    """Calculate the derivative of the stage regularised with respect
    to the channel bottom.

    Used auxiliary method:
      |smooth_logistic2_derivative2|

    Basic equation:
      :math:`RHMDH = smooth_{logistic2'}(H, HRP)`

    Examples:

        We apply the class |NumericalDifferentiator| to validate the
        calculated derivatives:

        >>> from hydpy.models.kinw import *
        >>> parameterstep()
        >>> gts(5)
        >>> states.h = -1.0, -0.1, 0.0, 0.1, 1.0

        >>> hr(0.0)
        >>> derived.hrp.update()
        >>> model.calc_rhmdh_v1()
        >>> aides.rhmdh
        rhmdh(0.0, 0.0, 1.0, 1.0, 1.0)

        >>> from hydpy import NumericalDifferentiator
        >>> numdiff = NumericalDifferentiator(
        ...     xsequence=states.h,
        ...     ysequences=[aides.rhm],
        ...     methods=[model.calc_rhm_v1])
        >>> numdiff()
        d_rhm/d_h: 0.0, 0.0, 1.0, 1.0, 1.0

        >>> hr(0.1)
        >>> derived.hrp.update()
        >>> model.calc_rhmdh_v1()
        >>> aides.rhmdh
        rhmdh(0.0, 0.155602, 0.5, 0.844398, 1.0)

        >>> numdiff()
        d_rhm/d_h: 0.0, 0.155602, 0.5, 0.844398, 1.0
    """

    CONTROLPARAMETERS = (kinw_control.GTS,)
    DERIVEDPARAMETERS = (kinw_derived.HRP,)
    REQUIREDSEQUENCES = (kinw_states.H,)
    RESULTSEQUENCES = (kinw_aides.RHMDH,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            aid.rhmdh[i] = smoothutils.smooth_logistic2_derivative2(sta.h[i], der.hrp)


class Calc_RHV_V1(modeltools.Method):
    """Regularise the stage with respect to the transition from the
    main channel to both forelands.

    Used auxiliary method:
      |smooth_logistic2|

    Basic equation:
      :math:`RHV = smooth_{logistic2}(H-HM, HRP)`

    Examples:

        >>> from hydpy.models.kinw import *
        >>> parameterstep()
        >>> gts(5)
        >>> hm(1.0)
        >>> hr(0.1)
        >>> derived.hrp.update()
        >>> states.h = 0.0, 0.9, 1.0, 1.1, 2.0
        >>> model.calc_rhv_v1()
        >>> aides.rhv
        rhv(0.0, 0.01, 0.040983, 0.11, 1.0)
    """

    CONTROLPARAMETERS = (kinw_control.GTS, kinw_control.HM)
    DERIVEDPARAMETERS = (kinw_derived.HRP,)
    REQUIREDSEQUENCES = (kinw_states.H,)
    RESULTSEQUENCES = (kinw_aides.RHV,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            aid.rhv[i] = smoothutils.smooth_logistic2(sta.h[i] - con.hm, der.hrp)


class Calc_RHVDH_V1(modeltools.Method):
    """Calculate the derivative of the stage regularised with respect
    to the transition from the main channel to both forelands.

    Used auxiliary method:
      |smooth_logistic2_derivative2|

    Basic equation:
      :math:`RHVDH = smooth_{logistic2'}(H-HM, HRP)`

    Examples:

        We apply the class |NumericalDifferentiator| to validate the
        calculated derivatives:

        >>> from hydpy.models.kinw import *
        >>> parameterstep()
        >>> gts(5)
        >>> hm(1.0)
        >>> states.h = 0.0, 0.9, 1.0, 1.1, 2.0

        >>> hr(0.0)
        >>> derived.hrp.update()
        >>> model.calc_rhvdh_v1()
        >>> aides.rhvdh
        rhvdh(0.0, 0.0, 1.0, 1.0, 1.0)

        >>> from hydpy import NumericalDifferentiator
        >>> numdiff = NumericalDifferentiator(
        ...     xsequence=states.h,
        ...     ysequences=[aides.rhv],
        ...     methods=[model.calc_rhv_v1])
        >>> numdiff()
        d_rhv/d_h: 0.0, 0.0, 1.0, 1.0, 1.0

        >>> hr(0.1)
        >>> derived.hrp.update()
        >>> model.calc_rhvdh_v1()
        >>> aides.rhvdh
        rhvdh(0.0, 0.155602, 0.5, 0.844398, 1.0)

        >>> numdiff()
        d_rhv/d_h: 0.0, 0.155602, 0.5, 0.844398, 1.0
    """

    CONTROLPARAMETERS = (kinw_control.GTS, kinw_control.HM)
    DERIVEDPARAMETERS = (kinw_derived.HRP,)
    REQUIREDSEQUENCES = (kinw_states.H,)
    RESULTSEQUENCES = (kinw_aides.RHVDH,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            aid.rhvdh[i] = smoothutils.smooth_logistic2_derivative2(
                sta.h[i] - con.hm, der.hrp
            )


class Calc_RHLVR_RHRVR_V1(modeltools.Method):
    """Regularise the stage with respect to the transitions from the
    forelands to the outer embankments.

    Used auxiliary method:
      |smooth_logistic2|

    Basic equation:
      :math:`RHVR = smooth_{logistic2}(H-HM-HV, HRP)`

    Examples:

        >>> from hydpy.models.kinw import *
        >>> parameterstep()
        >>> gts(6)
        >>> hm(1.0)
        >>> hr(0.1)
        >>> derived.hv(left=1.0, right=1.1)
        >>> derived.hrp.update()
        >>> states.h = 1.0, 1.9, 2.0, 2.1, 2.2, 3.0
        >>> model.calc_rhlvr_rhrvr_v1()
        >>> aides.rhlvr
        rhlvr(0.0, 0.01, 0.040983, 0.11, 0.201974, 1.0)
        >>> aides.rhrvr
        rhrvr(0.0, 0.001974, 0.01, 0.040983, 0.11, 0.9)
    """

    CONTROLPARAMETERS = (kinw_control.GTS, kinw_control.HM)
    DERIVEDPARAMETERS = (kinw_derived.HV, kinw_derived.HRP)
    REQUIREDSEQUENCES = (kinw_states.H,)
    RESULTSEQUENCES = (kinw_aides.RHLVR, kinw_aides.RHRVR)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            aid.rhlvr[i] = smoothutils.smooth_logistic2(
                sta.h[i] - con.hm - der.hv[0], der.hrp
            )
            aid.rhrvr[i] = smoothutils.smooth_logistic2(
                sta.h[i] - con.hm - der.hv[1], der.hrp
            )


class Calc_RHLVRDH_RHRVRDH_V1(modeltools.Method):
    """Calculate the derivative of the stage regularised with respect
    to the transition from the forelands to the outer embankments.

    Used auxiliary method:
      |smooth_logistic2_derivative2|

    Basic equation:
      :math:`RHVDH = smooth_{logistic2'}(H-HM-HV, HRP)`

    Examples:

        We apply the class |NumericalDifferentiator| to validate the
        calculated derivatives:

        >>> from hydpy.models.kinw import *
        >>> parameterstep()
        >>> gts(8)
        >>> hm(1.0)
        >>> derived.hv(left=1.0, right=2.0)
        >>> states.h = 1.0, 1.9, 2.0, 2.1, 2.9, 3.0, 3.1, 4.0

        >>> hr(0.0)
        >>> derived.hrp.update()
        >>> model.calc_rhlvrdh_rhrvrdh_v1()
        >>> aides.rhlvrdh
        rhlvrdh(0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0)
        >>> aides.rhrvrdh
        rhrvrdh(0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0)

        >>> from hydpy import NumericalDifferentiator
        >>> numdiff = NumericalDifferentiator(
        ...     xsequence=states.h,
        ...     ysequences=[aides.rhlvr, aides.rhrvr],
        ...     methods=[model.calc_rhlvr_rhrvr_v1])
        >>> numdiff()
        d_rhlvr/d_h: 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0
        d_rhrvr/d_h: 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0

        >>> hr(0.1)
        >>> derived.hrp.update()
        >>> model.calc_rhlvrdh_rhrvrdh_v1()
        >>> aides.rhlvrdh
        rhlvrdh(0.0, 0.155602, 0.5, 0.844398, 1.0, 1.0, 1.0, 1.0)
        >>> aides.rhrvrdh
        rhrvrdh(0.0, 0.0, 0.0, 0.0, 0.155602, 0.5, 0.844398, 1.0)

        >>> numdiff()
        d_rhlvr/d_h: 0.0, 0.155602, 0.5, 0.844398, 1.0, 1.0, 1.0, 1.0
        d_rhrvr/d_h: 0.0, 0.0, 0.0, 0.0, 0.155602, 0.5, 0.844398, 1.0
    """

    CONTROLPARAMETERS = (kinw_control.GTS, kinw_control.HM)
    DERIVEDPARAMETERS = (kinw_derived.HRP, kinw_derived.HV)
    REQUIREDSEQUENCES = (kinw_states.H,)
    RESULTSEQUENCES = (kinw_aides.RHLVRDH, kinw_aides.RHRVRDH)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            aid.rhlvrdh[i] = smoothutils.smooth_logistic2_derivative2(
                sta.h[i] - con.hm - der.hv[0], der.hrp
            )
            aid.rhrvrdh[i] = smoothutils.smooth_logistic2_derivative2(
                sta.h[i] - con.hm - der.hv[1], der.hrp
            )


class Calc_AM_UM_V1(modeltools.Method):
    """Calculate the wetted area and the wetted perimeter of the main channel.

    The main channel is assumed to have identical slopes on both sides.  Water flowing
    exactly above the main channel contributes to |AM|.  Both theoretical surfaces
    separating the water above the main channel from the water above the forelands
    contribute to |UM|.

    Examples:

        Generally, a trapezoid with reflection symmetry is assumed.  Here, we set its
        smaller base (bottom) to a length of 2 meters, its legs to an inclination of
        1 meter per 4 meters, and its height (depths) to 1 meter:

        >>> from hydpy.models.kinw import *
        >>> parameterstep()
        >>> gts(8)
        >>> bm(2.0)
        >>> bnm(4.0)
        >>> derived.bnmf.update()

        First, we show that all calculations agree with the unmodified triple trapezoid
        profile results when setting the smoothing parameter |HRP| to zero:

        >>> derived.hrp(0)

        This example deals with normal flow conditions, where water flows within the
        main channel completely (|H| < |HM|, the first five channel sections), and
        with high flow conditions, where water flows over the foreland also
        (|H| > |HM|, the three last channel sections):

        >>> hm(1.0)
        >>> states.h = 0.0, 0.1, 0.5, 0.9, 1.0, 1.1, 1.5, 2.0
        >>> model.calc_rhm_v1()
        >>> model.calc_rhv_v1()
        >>> model.calc_am_um_v1()
        >>> aides.am
        am(0.0, 0.24, 2.0, 5.04, 6.0, 7.0, 11.0, 16.0)
        >>> aides.um
        um(2.0, 2.824621, 6.123106, 9.42159, 10.246211, 10.446211, 11.246211,
           12.246211)

        The next example checks the special case of a channel with zero height:

        >>> hm(0.0)
        >>> model.calc_rhm_v1()
        >>> model.calc_rhv_v1()
        >>> model.calc_am_um_v1()
        >>> aides.am
        am(0.0, 0.2, 1.0, 1.8, 2.0, 2.2, 3.0, 4.0)
        >>> aides.um
        um(2.0, 2.2, 3.0, 3.8, 4.0, 4.2, 5.0, 6.0)

        Second, we repeat both examples with a reasonable smoothing parameterisation.
        The primary deviations occur around the original discontinuities related to
        the channel bottom and the main channel's transition to both forelands:

        >>> hr(0.1)
        >>> derived.hrp.update()

        >>> hm(1.0)
        >>> states.h = 0.0, 0.1, 0.5, 0.9, 1.0, 1.1, 1.5, 2.0
        >>> model.calc_rhm_v1()
        >>> model.calc_rhv_v1()
        >>> model.calc_am_um_v1()
        >>> aides.am
        am(0.088684, 0.2684, 2.000075, 5.0396, 5.993282, 6.9916, 10.99995, 16.0)
        >>> aides.um
        um(2.337952, 2.907083, 6.123131, 9.359128, 9.990225, 10.383749,
           11.246133, 12.246211)

        >>> hm(0.0)
        >>> model.calc_rhm_v1()
        >>> model.calc_rhv_v1()
        >>> model.calc_am_um_v1()
        >>> aides.am
        am(0.081965, 0.22, 1.000025, 1.8, 2.0, 2.2, 3.0, 4.0)
        >>> aides.um
        um(2.081965, 2.22, 3.000025, 3.8, 4.0, 4.2, 5.0, 6.0)
    """

    CONTROLPARAMETERS = (kinw_control.GTS, kinw_control.BM, kinw_control.BNM)
    DERIVEDPARAMETERS = (kinw_derived.BNMF,)
    REQUIREDSEQUENCES = (kinw_aides.RHM, kinw_aides.RHV)
    RESULTSEQUENCES = (kinw_aides.AM, kinw_aides.UM)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            d_temp = aid.rhm[i] - aid.rhv[i]
            aid.am[i] = d_temp * (con.bm + d_temp * con.bnm) + aid.rhv[i] * (
                con.bm + 2.0 * d_temp * con.bnm
            )
            aid.um[i] = con.bm + 2.0 * d_temp * der.bnmf + 2.0 * aid.rhv[i]


class Calc_AMDH_UMDH_V1(modeltools.Method):
    """Calculate the derivatives of the wetted area and  perimeter of
    the main channel.

    Examples:

        In the following, we repeat the examples of the documentation on method
        |Calc_AM_UM_V1| and check the derivatives' correctness by comparing the
        results of class |NumericalDifferentiator|:

        >>> from hydpy.models.kinw import *
        >>> parameterstep()
        >>> gts(8)
        >>> bm(2.0)
        >>> bnm(4.0)

        >>> derived.bnmf.update()
        >>> derived.hrp(0)

        >>> hm(1.0)
        >>> states.h = 0.0, 0.1, 0.5, 0.9, 1.0, 1.1, 1.5, 2.0
        >>> model.calc_rhm_v1()
        >>> model.calc_rhmdh_v1()
        >>> model.calc_rhv_v1()
        >>> model.calc_rhvdh_v1()
        >>> model.calc_amdh_umdh_v1()
        >>> aides.amdh
        amdh(2.0, 2.8, 6.0, 9.2, 10.0, 10.0, 10.0, 10.0)
        >>> aides.umdh
        umdh(8.246211, 8.246211, 8.246211, 8.246211, 2.0, 2.0, 2.0, 2.0)

        >>> from hydpy import NumericalDifferentiator
        >>> numdiff = NumericalDifferentiator(
        ...     xsequence=states.h,
        ...     ysequences=[aides.am, aides.um],
        ...     methods=[model.calc_rhm_v1,
        ...              model.calc_rhv_v1,
        ...              model.calc_am_um_v1])
        >>> numdiff()
        d_am/d_h: 2.0, 2.8, 6.0, 9.2, 10.0, 10.0, 10.0, 10.0
        d_um/d_h: 8.246211, 8.246211, 8.246211, 8.246211, 2.0, 2.0, 2.0, 2.0

        >>> hm(0.0)
        >>> model.calc_rhm_v1()
        >>> model.calc_rhmdh_v1()
        >>> model.calc_rhv_v1()
        >>> model.calc_rhvdh_v1()
        >>> model.calc_amdh_umdh_v1()
        >>> aides.amdh
        amdh(2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0)
        >>> aides.umdh
        umdh(2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0)
        >>> numdiff()
        d_am/d_h: 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0
        d_um/d_h: 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0

        >>> hr(0.1)
        >>> derived.hrp.update()

        >>> hm(1.0)
        >>> model.calc_rhm_v1()
        >>> model.calc_rhmdh_v1()
        >>> model.calc_rhv_v1()
        >>> model.calc_rhvdh_v1()
        >>> model.calc_amdh_umdh_v1()
        >>> aides.amdh
        amdh(1.163931, 2.431865, 5.998826, 9.18755, 9.836069, 10.05693,
             10.000749, 10.0)
        >>> aides.umdh
        umdh(4.123105, 6.963079, 8.243132, 7.274283, 5.123105, 2.971926,
             2.001327, 2.0)

        >>> numdiff()
        d_am/d_h: 1.163931, 2.431865, 5.998826, 9.18755, 9.836069, 10.05693, \
10.000749, 10.0
        d_um/d_h: 4.123105, 6.963079, 8.243132, 7.274283, 5.123105, 2.971926, \
2.001327, 2.0
    """

    CONTROLPARAMETERS = (kinw_control.GTS, kinw_control.BM, kinw_control.BNM)
    DERIVEDPARAMETERS = (kinw_derived.BNMF,)
    REQUIREDSEQUENCES = (
        kinw_aides.RHM,
        kinw_aides.RHMDH,
        kinw_aides.RHV,
        kinw_aides.RHVDH,
    )
    RESULTSEQUENCES = (kinw_aides.AMDH, kinw_aides.UMDH)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            d_temp1 = aid.rhm[i] - aid.rhv[i]
            d_temp2 = aid.rhmdh[i] - aid.rhvdh[i]
            aid.amdh[i] = (
                con.bnm * d_temp1 * d_temp2
                + 2.0 * con.bnm * d_temp2 * aid.rhv[i]
                + (con.bm + con.bnm * d_temp1) * d_temp2
                + (con.bm + 2.0 * con.bnm * d_temp1) * aid.rhvdh[i]
            )
            aid.umdh[i] = 2.0 * d_temp2 * der.bnmf + 2.0 * aid.rhvdh[i]


class Calc_ALV_ARV_ULV_URV_V1(modeltools.Method):
    """Calculate the wetted area and wetted perimeter of both forelands.

    Each foreland lies between the main channel and one outer embankment. The water
    flowing exactly above a foreland is contributing to |ALV| or |ARV|.  The
    theoretical surface separating the water above the main channel from the water
    above the foreland is not contributing to |ULV| or |URV|. On the other hand, the
    surface separating the water above the foreland from the water above its outer
    embankment is contributing to |ULV| and |URV|.

    Examples:

        >>> from hydpy.models.kinw import *
        >>> parameterstep()
        >>> gts(14)
        >>> hm(1.0)

        First, we show that all calculations agree with the unmodified triple trapezoid
        profile results when setting the smoothing parameter |HRP| to zero:

        >>> derived.hrp(0)

        This example deals with normal flow conditions, where water flows within the
        main channel completely (|H| < |HM|, the first four channel sections); with
        moderate high flow conditions, where water flows over both forelands, but not
        over their embankments (|HM| < |H| < (|HM| + |HV|), channel sections six to
        eight or twelve for the left and the right foreland, respectively), and with
        extreme high flow conditions, where water flows over both forelands and their
        outer embankments ((|HM| + |HV|) < |H|, the last six or two channel sections
        for the left and the right foreland, respectively):

        >>> bv(left=2.0, right=3.0)
        >>> bnv(left=4.0, right=5.0)
        >>> derived.bnvf.update()
        >>> derived.hv(left=1.0, right=2.0)

        >>> states.h = (0.0, 0.5, 0.9, 1.0, 1.1, 1.5, 1.9,
        ...             2.0, 2.1, 2.5, 2.9, 3.0, 3.1, 4.0)
        >>> model.calc_rhm_v1()
        >>> model.calc_rhv_v1()
        >>> model.calc_rhlvr_rhrvr_v1()
        >>> model.calc_alv_arv_ulv_urv_v1()
        >>> aides.alv
        alv(0.0, 0.0, 0.0, 0.0, 0.22, 1.5, 3.42, 4.0, 4.6, 7.0, 9.4, 10.0, 10.6,
            16.0)
        >>> aides.arv
        arv(0.0, 0.0, 0.0, 0.0, 0.325, 2.125, 4.725, 5.5, 6.325, 10.125, 14.725,
            16.0, 17.3, 29.0)
        >>> aides.ulv
        ulv(2.0, 2.0, 2.0, 2.0, 2.412311, 4.061553, 5.710795, 6.123106,
            6.223106, 6.623106, 7.023106, 7.123106, 7.223106, 8.123106)
        >>> aides.urv
        urv(3.0, 3.0, 3.0, 3.0, 3.509902, 5.54951, 7.589118, 8.09902, 8.608921,
            10.648529, 12.688137, 13.198039, 13.298039, 14.198039)

        The next example proves the correct handling of forelands with zero
        widths and heights:

        >>> bv(left=0.0, right=2.0)
        >>> bnv(4.0)
        >>> derived.hv(left=1.0, right=0.0)
        >>> model.calc_rhv_v1()
        >>> model.calc_rhlvr_rhrvr_v1()
        >>> model.calc_alv_arv_ulv_urv_v1()
        >>> aides.alv
        alv(0.0, 0.0, 0.0, 0.0, 0.02, 0.5, 1.62, 2.0, 2.4, 4.0, 5.6, 6.0, 6.4,
            10.0)
        >>> aides.arv
        arv(0.0, 0.0, 0.0, 0.0, 0.2, 1.0, 1.8, 2.0, 2.2, 3.0, 3.8, 4.0, 4.2, 6.0)
        >>> aides.ulv
        ulv(0.0, 0.0, 0.0, 0.0, 0.412311, 2.061553, 3.710795, 4.123106,
            4.223106, 4.623106, 5.023106, 5.123106, 5.223106, 6.123106)
        >>> aides.urv
        urv(2.0, 2.0, 2.0, 2.0, 2.1, 2.5, 2.9, 3.0, 3.1, 3.5, 3.9, 4.0, 4.1, 5.0)

        Second, we repeat both examples with a reasonable smoothing parameterisation.
        The primary deviations occur around the original discontinuities related to
        the channel bottom and the main channel's transition to both forelands:

        >>> hr(0.1)
        >>> derived.hrp.update()

        >>> bv(left=2.0, right=3.0)
        >>> bnv(left=4.0, right=5.0)
        >>> derived.hv(left=1.0, right=2.0)
        >>> model.calc_rhv_v1()
        >>> model.calc_rhlvr_rhrvr_v1()
        >>> model.calc_alv_arv_ulv_urv_v1()
        >>> aides.alv
        alv(0.0, 0.000025, 0.0202, 0.085324, 0.2442, 1.50005, 3.4198, 3.996641,
            4.5958, 6.999975, 9.4, 10.0, 10.6, 16.0)
        >>> aides.arv
        arv(0.0, 0.000038, 0.03025, 0.127147, 0.36025, 2.125069, 4.725, 5.5,
            6.325, 10.125, 14.72475, 15.995801, 17.29475, 29.0)
        >>> aides.ulv
        ulv(2.0, 2.000052, 2.041231, 2.168976, 2.453542, 4.061565, 5.679564,
            5.995113, 6.191875, 6.623066, 7.023106, 7.123106, 7.223106, 8.123106)
        >>> aides.urv
        urv(3.0, 3.000064, 3.05099, 3.208971, 3.560892, 5.549574, 7.589118,
            8.09902, 8.608921, 10.648478, 12.647147, 13.03005, 13.257049,
            14.198039)

        >>> bv(left=0.0, right=2.0)
        >>> bnv(4.0)
        >>> derived.hv(left=1.0, right=0.0)
        >>> model.calc_rhm_v1()
        >>> model.calc_rhv_v1()
        >>> model.calc_rhlvr_rhrvr_v1()
        >>> model.calc_alv_arv_ulv_urv_v1()
        >>> aides.alv
        alv(0.0, 0.0, 0.0002, 0.003359, 0.0242, 0.500025, 1.6198, 1.996641,
            2.3958, 3.999975, 5.6, 6.0, 6.4, 10.0)
        >>> aides.arv
        arv(0.0, 0.000025, 0.02, 0.081965, 0.22, 1.000025, 1.8, 2.0, 2.2, 3.0,
            3.8, 4.0, 4.2, 6.0)
        >>> aides.ulv
        ulv(0.0, 0.000052, 0.041231, 0.168976, 0.453542, 2.061565, 3.679564,
            3.995113, 4.191875, 4.623066, 5.023106, 5.123106, 5.223106, \
6.123106)
        >>> aides.urv
        urv(2.0, 2.000013, 2.01, 2.040983, 2.11, 2.500013, 2.9, 3.0, 3.1, 3.5,
            3.9, 4.0, 4.1, 5.0)
    """

    CONTROLPARAMETERS = (kinw_control.GTS, kinw_control.BV, kinw_control.BNV)
    DERIVEDPARAMETERS = (kinw_derived.BNVF,)
    REQUIREDSEQUENCES = (kinw_aides.RHV, kinw_aides.RHLVR, kinw_aides.RHRVR)
    RESULTSEQUENCES = (kinw_aides.ALV, kinw_aides.ARV, kinw_aides.ULV, kinw_aides.URV)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            d_temp = aid.rhv[i] - aid.rhlvr[i]
            aid.alv[i] = d_temp * (con.bv[0] + (d_temp * con.bnv[0] / 2.0)) + aid.rhlvr[
                i
            ] * (con.bv[0] + d_temp * con.bnv[0])
            aid.ulv[i] = con.bv[0] + d_temp * der.bnvf[0] + aid.rhlvr[i]
            d_temp = aid.rhv[i] - aid.rhrvr[i]
            aid.arv[i] = d_temp * (con.bv[1] + (d_temp * con.bnv[1] / 2.0)) + aid.rhrvr[
                i
            ] * (con.bv[1] + d_temp * con.bnv[1])
            aid.urv[i] = con.bv[1] + d_temp * der.bnvf[1] + aid.rhrvr[i]


class Calc_ALVDH_ARVDH_ULVDH_URVDH_V1(modeltools.Method):
    """Calculate the derivatives of the wetted area and perimeter of
    both forelands.

    Examples:

        In the following, we repeat the examples of the documentation on method
        |Calc_ALV_ARV_ULV_URV_V1| and check the derivatives' correctness by comparing
        the results of class |NumericalDifferentiator|:

        >>> from hydpy.models.kinw import *
        >>> parameterstep()
        >>> gts(13)
        >>> hm(1.0)
        >>> bv(left=2.0, right=3.0)
        >>> bnv(left=4.0, right=5.0)
        >>> derived.bnvf.update()
        >>> derived.hv(left=1.0, right=2.0)

        >>> derived.hrp(0)

        >>> states.h = (1.0, 1.5, 1.9, 2.0, 2.1, 2.5, 3.0,
        ...             3.5, 3.9, 4.0, 4.1, 4.5, 5.0)
        >>> model.calc_rhv_v1()
        >>> model.calc_rhvdh_v1()
        >>> model.calc_rhlvr_rhrvr_v1()
        >>> model.calc_rhlvrdh_rhrvrdh_v1()
        >>> model.calc_alvdh_arvdh_ulvdh_urvdh_v1()
        >>> aides.alvdh
        alvdh(2.0, 4.0, 5.6, 6.0, 6.0, 6.0, 6.0, 6.0, 6.0, 6.0, 6.0, 6.0, 6.0)
        >>> aides.arvdh
        arvdh(3.0, 5.5, 7.5, 8.0, 8.5, 10.5, 13.0, 13.0, 13.0, 13.0, 13.0, 13.0,
              13.0)
        >>> aides.ulvdh
        ulvdh(4.123106, 4.123106, 4.123106, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
              1.0, 1.0, 1.0)
        >>> aides.urvdh
        urvdh(5.09902, 5.09902, 5.09902, 5.09902, 5.09902, 5.09902, 1.0, 1.0,
              1.0, 1.0, 1.0, 1.0, 1.0)

        >>> from hydpy import NumericalDifferentiator
        >>> numdiff = NumericalDifferentiator(
        ...     xsequence=states.h,
        ...     ysequences=[aides.alv, aides.arv, aides.ulv, aides.urv],
        ...     methods=[model.calc_rhv_v1,
        ...              model.calc_rhlvr_rhrvr_v1,
        ...              model.calc_alv_arv_ulv_urv_v1])
        >>> numdiff()
        d_alv/d_h: 2.0, 4.0, 5.6, 6.0, 6.0, 6.0, 6.0, 6.0, 6.0, 6.0, 6.0, 6.0, \
6.0
        d_arv/d_h: 3.0, 5.5, 7.5, 8.0, 8.5, 10.5, 13.0, 13.0, 13.0, 13.0, \
13.0, 13.0, 13.0
        d_ulv/d_h: 4.123106, 4.123106, 4.123106, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, \
1.0, 1.0, 1.0, 1.0
        d_urv/d_h: 5.09902, 5.09902, 5.09902, 5.09902, 5.09902, 5.09902, 1.0, \
1.0, 1.0, 1.0, 1.0, 1.0, 1.0

        >>> bv(left=0.0, right=2.0)
        >>> bnv(4.0)
        >>> derived.bnvf.update()
        >>> derived.hv(left=1.0, right=0.0)
        >>> model.calc_rhv_v1()
        >>> model.calc_rhvdh_v1()
        >>> model.calc_rhlvr_rhrvr_v1()
        >>> model.calc_rhlvrdh_rhrvrdh_v1()
        >>> model.calc_alvdh_arvdh_ulvdh_urvdh_v1()
        >>> aides.alvdh
        alvdh(0.0, 2.0, 3.6, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0)
        >>> aides.arvdh
        arvdh(2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0)
        >>> aides.ulvdh
        ulvdh(4.123106, 4.123106, 4.123106, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
              1.0, 1.0, 1.0)
        >>> aides.urvdh
        urvdh(1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0)
        >>> numdiff()
        d_alv/d_h: 0.0, 2.0, 3.6, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0, \
4.0
        d_arv/d_h: 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, \
2.0
        d_ulv/d_h: 4.123106, 4.123106, 4.123106, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, \
1.0, 1.0, 1.0, 1.0
        d_urv/d_h: 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, \
1.0

        >>> hr(0.1)
        >>> derived.hrp.update()

        >>> bv(left=2.0, right=3.0)
        >>> bnv(left=4.0, right=5.0)
        >>> derived.bnvf.update()
        >>> derived.hv(left=1.0, right=2.0)

        >>> model.calc_rhv_v1()
        >>> model.calc_rhvdh_v1()
        >>> model.calc_rhlvr_rhrvr_v1()
        >>> model.calc_rhlvrdh_rhrvrdh_v1()
        >>> model.calc_alvdh_arvdh_ulvdh_urvdh_v1()
        >>> aides.alvdh
        alvdh(1.081965, 3.9992, 5.593775, 5.918034, 6.028465, 6.000375, 6.0,
              6.0, 6.0, 6.0, 6.0, 6.0, 6.0)
        >>> aides.arvdh
        arvdh(1.602457, 5.498894, 7.499998, 8.0, 8.5, 10.5, 12.897543,
              13.000468, 13.000001, 13.0, 13.0, 13.0, 13.0)
        >>> aides.ulvdh
        ulvdh(2.061553, 4.121566, 3.637142, 2.561553, 1.485963, 1.000664, 1.0,
              1.0, 1.0, 1.0, 1.0, 1.0, 1.0)
        >>> aides.urvdh
        urvdh(2.54951, 5.097936, 5.099018, 5.099019, 5.099018, 5.098149,
              3.04951, 1.000871, 1.000001, 1.0, 1.0, 1.0, 1.0)

        >>> numdiff()
        d_alv/d_h: 1.081965, 3.9992, 5.593775, 5.918034, 6.028465, 6.000375, \
6.0, 6.0, 6.0, 6.0, 6.0, 6.0, 6.0
        d_arv/d_h: 1.602457, 5.498894, 7.499998, 8.0, 8.5, 10.5, 12.897543, \
13.000468, 13.000001, 13.0, 13.0, 13.0, 13.0
        d_ulv/d_h: 2.061553, 4.121566, 3.637142, 2.561553, 1.485963, 1.000664, \
1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0
        d_urv/d_h: 2.54951, 5.097936, 5.099018, 5.099019, 5.099018, 5.098149, \
3.04951, 1.000871, 1.000001, 1.0, 1.0, 1.0, 1.0
    """

    CONTROLPARAMETERS = (kinw_control.GTS, kinw_control.BV, kinw_control.BNV)
    DERIVEDPARAMETERS = (kinw_derived.BNVF,)
    REQUIREDSEQUENCES = (
        kinw_aides.RHV,
        kinw_aides.RHVDH,
        kinw_aides.RHLVR,
        kinw_aides.RHLVRDH,
        kinw_aides.RHRVR,
        kinw_aides.RHRVRDH,
    )
    RESULTSEQUENCES = (
        kinw_aides.ALVDH,
        kinw_aides.ARVDH,
        kinw_aides.ULVDH,
        kinw_aides.URVDH,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            d_temp1 = aid.rhv[i] - aid.rhlvr[i]
            d_temp2 = aid.rhvdh[i] - aid.rhlvrdh[i]
            aid.alvdh[i] = (
                con.bnv[0] * d_temp1 * d_temp2 / 2.0
                + con.bnv[0] * d_temp2 * aid.rhlvr[i]
                + (con.bnv[0] * d_temp1 / 2 + con.bv[0]) * d_temp2
                + (con.bnv[0] * d_temp1 + con.bv[0]) * aid.rhlvrdh[i]
            )
            aid.ulvdh[i] = d_temp2 * der.bnvf[0] + aid.rhlvrdh[i]
            d_temp1 = aid.rhv[i] - aid.rhrvr[i]
            d_temp2 = aid.rhvdh[i] - aid.rhrvrdh[i]
            aid.arvdh[i] = (
                con.bnv[1] * d_temp1 * d_temp2 / 2.0
                + con.bnv[1] * d_temp2 * aid.rhrvr[i]
                + (con.bnv[1] * d_temp1 / 2 + con.bv[1]) * d_temp2
                + (con.bnv[1] * d_temp1 + con.bv[1]) * aid.rhrvrdh[i]
            )
            aid.urvdh[i] = d_temp2 * der.bnvf[1] + aid.rhrvrdh[i]


class Calc_ALVR_ARVR_ULVR_URVR_V1(modeltools.Method):
    """Calculate the wetted area and perimeter of both outer embankments.

    Each outer embankment lies beyond its foreland.  The water flowing exactly above
    an embankment adds to |ALVR| and |ARVR|.  The theoretical surface separating water
    above the foreland from the water above its embankment is not contributing to
    |ULVR| and |URVR|.

    Examples:

        >>> from hydpy.models.kinw import *
        >>> parameterstep()
        >>> gts(11)
        >>> hm(1.0)

        First, we show that all calculations agree with the unmodified triple trapezoid
        profile results when the setting the smoothing parameter |HRP| to zero:

        >>> derived.hrp(0)

        This example deals with moderate high flow conditions, where
        water flows over the forelands, but not over their outer embankments
        (|HM| < |H| < (|HM| + |HV|), the first four or eight channel sections
        for the left and the right outer embankment, respectively); the second
        example deals with extreme high flow conditions, where water flows
        both over the foreland and their outer embankments ((|HM| + |HV|) < |H|,
        the last seven or three channel sections for the left and the right
        outer embankment, respectively):

        >>> states.h = 1.0, 1.5, 1.9, 2.0, 2.1, 2.5, 2.9, 3.0, 3.1, 3.5, 4.0
        >>> bnvr(left=4.0, right=5.0)
        >>> derived.bnvrf.update()
        >>> derived.hv(left=1.0, right=2.0)
        >>> model.calc_rhlvr_rhrvr_v1()
        >>> model.calc_alvr_arvr_ulvr_urvr_v1()
        >>> aides.alvr
        alvr(0.0, 0.0, 0.0, 0.0, 0.02, 0.5, 1.62, 2.0, 2.42, 4.5, 8.0)
        >>> aides.arvr
        arvr(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.025, 0.625, 2.5)
        >>> aides.ulvr
        ulvr(0.0, 0.0, 0.0, 0.0, 0.412311, 2.061553, 3.710795, 4.123106,
             4.535416, 6.184658, 8.246211)
        >>> aides.urvr
        urvr(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.509902, 2.54951, 5.09902)

        The next example checks the special cases of a vertical outer embankment
        (left side) and zero-height foreland (right side):

        >>> bnvr(left=0.0, right=5.0)
        >>> derived.bnvrf.update()
        >>> derived.hv(left=1.0, right=0.0)
        >>> model.calc_rhlvr_rhrvr_v1()
        >>> model.calc_alvr_arvr_ulvr_urvr_v1()
        >>> aides.alvr
        alvr(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        >>> aides.arvr
        arvr(0.0, 0.625, 2.025, 2.5, 3.025, 5.625, 9.025, 10.0, 11.025, 15.625,
             22.5)
        >>> aides.ulvr
        ulvr(0.0, 0.0, 0.0, 0.0, 0.1, 0.5, 0.9, 1.0, 1.1, 1.5, 2.0)
        >>> aides.urvr
        urvr(0.0, 2.54951, 4.589118, 5.09902, 5.608921, 7.648529, 9.688137,
             10.198039, 10.707941, 12.747549, 15.297059)

        Second, we repeat both examples with a reasonable smoothing parameterisation.
        The primary deviations occur around the original discontinuities related to
        the channel bottom and the main channel's transition to both forelands:

        >>> hr(0.1)
        >>> derived.hrp.update()
        >>> bnvr(left=4.0, right=5.0)
        >>> derived.bnvrf.update()
        >>> derived.hv(left=1.0, right=2.0)
        >>> model.calc_rhlvr_rhrvr_v1()
        >>> model.calc_alvr_arvr_ulvr_urvr_v1()
        >>> aides.alvr
        alvr(0.0, 0.0, 0.0002, 0.003359, 0.0242, 0.500025, 1.62, 2.0, 2.42, 4.5,
             8.0)
        >>> aides.arvr
        arvr(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.00025, 0.004199, 0.03025, 0.625031,
             2.5)
        >>> aides.ulvr
        ulvr(0.0, 0.000052, 0.041231, 0.168976, 0.453542, 2.061605, 3.710795,
             4.123106, 4.535416, 6.184658, 8.246211)
        >>> aides.urvr
        urvr(0.0, 0.0, 0.0, 0.0, 0.0, 0.000064, 0.05099, 0.208971, 0.560892,
             2.549574, 5.09902)

        >>> bnvr(left=0.0, right=5.0)
        >>> derived.bnvrf.update()
        >>> derived.hv(left=1.0, right=0.0)
        >>> model.calc_rhlvr_rhrvr_v1()
        >>> model.calc_alvr_arvr_ulvr_urvr_v1()
        >>> aides.alvr
        alvr(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        >>> aides.arvr
        arvr(0.004199, 0.625031, 2.025, 2.5, 3.025, 5.625, 9.025, 10.0, 11.025,
             15.625, 22.5)
        >>> aides.ulvr
        ulvr(0.0, 0.000013, 0.01, 0.040983, 0.11, 0.500013, 0.9, 1.0, 1.1, 1.5,
             2.0)
        >>> aides.urvr
        urvr(0.208971, 2.549574, 4.589118, 5.09902, 5.608921, 7.648529,
             9.688137, 10.198039, 10.707941, 12.747549, 15.297059)
    """

    CONTROLPARAMETERS = (kinw_control.GTS, kinw_control.BNVR)
    DERIVEDPARAMETERS = (kinw_derived.BNVRF,)
    REQUIREDSEQUENCES = (kinw_aides.RHLVR, kinw_aides.RHRVR)
    RESULTSEQUENCES = (
        kinw_aides.ALVR,
        kinw_aides.ARVR,
        kinw_aides.ULVR,
        kinw_aides.URVR,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            aid.alvr[i] = aid.rhlvr[i] ** 2 * con.bnvr[0] / 2.0
            aid.ulvr[i] = aid.rhlvr[i] * der.bnvrf[0]
            aid.arvr[i] = aid.rhrvr[i] ** 2 * con.bnvr[1] / 2.0
            aid.urvr[i] = aid.rhrvr[i] * der.bnvrf[1]


class Calc_ALVRDH_ARVRDH_ULVRDH_URVRDH_V1(modeltools.Method):
    """Calculate the derivatives of the wetted area and perimeter of
    both outer embankments.

    Examples:

        In the following, we repeat the examples of the documentation on method
        |Calc_ALVR_ARVR_ULVR_URVR_V1| and check the derivatives' correctness by
        comparing the results of class |NumericalDifferentiator|:

        >>> from hydpy.models.kinw import *
        >>> parameterstep()
        >>> gts(11)
        >>> hm(1.0)

        >>> derived.hrp(0)

        >>> states.h = 1.0, 1.5, 1.9, 2.0, 2.1, 2.5, 2.9, 3.0, 3.1, 3.5, 4.0
        >>> bnvr(left=4.0, right=5.0)
        >>> derived.bnvrf.update()
        >>> derived.hv(left=1.0, right=2.0)
        >>> model.calc_rhlvr_rhrvr_v1()
        >>> model.calc_rhlvrdh_rhrvrdh_v1()
        >>> model.calc_alvrdh_arvrdh_ulvrdh_urvrdh_v1()
        >>> aides.alvrdh
        alvrdh(0.0, 0.0, 0.0, 0.0, 0.4, 2.0, 3.6, 4.0, 4.4, 6.0, 8.0)
        >>> aides.arvrdh
        arvrdh(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 2.5, 5.0)
        >>> aides.ulvrdh
        ulvrdh(0.0, 0.0, 0.0, 4.123106, 4.123106, 4.123106, 4.123106, 4.123106,
               4.123106, 4.123106, 4.123106)
        >>> aides.urvrdh
        urvrdh(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 5.09902, 5.09902, 5.09902,
               5.09902)

        >>> from hydpy import NumericalDifferentiator
        >>> numdiff = NumericalDifferentiator(
        ...     xsequence=states.h,
        ...     ysequences=[aides.alvr, aides.arvr, aides.ulvr, aides.urvr],
        ...     methods=[model.calc_rhlvr_rhrvr_v1,
        ...              model.calc_alvr_arvr_ulvr_urvr_v1])
        >>> numdiff()
        d_alvr/d_h: 0.0, 0.0, 0.0, 0.0, 0.4, 2.0, 3.6, 4.0, 4.4, 6.0, 8.0
        d_arvr/d_h: 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 2.5, 5.0
        d_ulvr/d_h: 0.0, 0.0, 0.0, 4.123106, 4.123106, 4.123106, 4.123106, \
4.123106, 4.123106, 4.123106, 4.123106
        d_urvr/d_h: 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 5.09902, 5.09902, \
5.09902, 5.09902

        >>> bnvr(left=0.0, right=5.0)
        >>> derived.bnvrf.update()
        >>> derived.hv(left=1.0, right=0.0)
        >>> model.calc_rhlvr_rhrvr_v1()
        >>> model.calc_rhlvrdh_rhrvrdh_v1()
        >>> model.calc_alvrdh_arvrdh_ulvrdh_urvrdh_v1()
        >>> aides.alvrdh
        alvrdh(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        >>> aides.arvrdh
        arvrdh(0.0, 2.5, 4.5, 5.0, 5.5, 7.5, 9.5, 10.0, 10.5, 12.5, 15.0)
        >>> aides.ulvrdh
        ulvrdh(0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0)
        >>> aides.urvrdh
        urvrdh(5.09902, 5.09902, 5.09902, 5.09902, 5.09902, 5.09902, 5.09902,
               5.09902, 5.09902, 5.09902, 5.09902)

        >>> numdiff()
        d_alvr/d_h: 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        d_arvr/d_h: 0.0, 2.5, 4.5, 5.0, 5.5, 7.5, 9.5, 10.0, 10.5, 12.5, 15.0
        d_ulvr/d_h: 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0
        d_urvr/d_h: 5.09902, 5.09902, 5.09902, 5.09902, 5.09902, 5.09902, \
5.09902, 5.09902, 5.09902, 5.09902, 5.09902

        >>> hr(0.1)
        >>> derived.hrp.update()
        >>> bnvr(left=4.0, right=5.0)
        >>> derived.bnvrf.update()
        >>> derived.hv(left=1.0, right=2.0)
        >>> model.calc_rhlvr_rhrvr_v1()
        >>> model.calc_rhlvrdh_rhrvrdh_v1()
        >>> model.calc_alvrdh_arvrdh_ulvrdh_urvrdh_v1()
        >>> aides.alvrdh
        alvrdh(0.0, 0.0, 0.006224, 0.081965, 0.371535, 1.999625, 3.599999, 4.0,
               4.4, 6.0, 8.0)
        >>> aides.arvrdh
        arvrdh(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.00778, 0.102457, 0.464419,
               2.499532, 5.0)
        >>> aides.ulvrdh
        ulvrdh(0.0, 0.000876, 0.641565, 2.061553, 3.48154, 4.12223, 4.123105,
               4.123105, 4.123106, 4.123106, 4.123106)
        >>> aides.urvrdh
        urvrdh(0.0, 0.0, 0.0, 0.0, 0.000001, 0.001083, 0.79342, 2.54951,
               4.305599, 5.097936, 5.099019)

        >>> numdiff()
        d_alvr/d_h: 0.0, 0.0, 0.006224, 0.081965, 0.371535, 1.999625, \
3.599999, 4.0, 4.4, 6.0, 8.0
        d_arvr/d_h: 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.00778, 0.102457, \
0.464419, 2.499532, 5.0
        d_ulvr/d_h: 0.0, 0.000876, 0.641565, 2.061553, 3.48154, 4.12223, \
4.123105, 4.123105, 4.123106, 4.123106, 4.123106
        d_urvr/d_h: 0.0, 0.0, 0.0, 0.0, 0.000001, 0.001083, 0.79342, \
2.54951, 4.305599, 5.097936, 5.099019
    """

    CONTROLPARAMETERS = (kinw_control.GTS, kinw_control.BNVR)
    DERIVEDPARAMETERS = (kinw_derived.BNVRF,)
    REQUIREDSEQUENCES = (
        kinw_aides.RHLVR,
        kinw_aides.RHLVRDH,
        kinw_aides.RHRVR,
        kinw_aides.RHRVRDH,
    )
    RESULTSEQUENCES = (
        kinw_aides.ALVRDH,
        kinw_aides.ARVRDH,
        kinw_aides.ULVRDH,
        kinw_aides.URVRDH,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            aid.alvrdh[i] = con.bnvr[0] * aid.rhlvr[i] * aid.rhlvrdh[i]
            aid.ulvrdh[i] = aid.rhlvrdh[i] * der.bnvrf[0]
            aid.arvrdh[i] = con.bnvr[1] * aid.rhrvr[i] * aid.rhrvrdh[i]
            aid.urvrdh[i] = aid.rhrvrdh[i] * der.bnvrf[1]


class Calc_QM_V1(modeltools.Method):
    """Calculate the discharge of the main channel after Manning-Strickler.

    Basic equation:
      :math:`QM = MFM \\cdot \\frac{AM^{5/3}}{UM^{2/3}}`

    Examples:

        Note the handling of zero values for |UM| (in the third subsection):

        >>> from hydpy.models.kinw import *
        >>> parameterstep()
        >>> gts(3)
        >>> derived.mfm(10.0)
        >>> aides.am = 3.0, 0.0, 3.0
        >>> aides.um = 7.0, 7.0, 0.0
        >>> model.calc_qm_v1()
        >>> aides.qm
        qm(17.053102, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (kinw_control.GTS,)
    DERIVEDPARAMETERS = (kinw_derived.MFM,)
    REQUIREDSEQUENCES = (kinw_aides.AM, kinw_aides.UM)
    RESULTSEQUENCES = (kinw_aides.QM,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            if aid.um[i] > 0.0:
                aid.qm[i] = (
                    der.mfm * aid.am[i] ** (5.0 / 3.0) / aid.um[i] ** (2.0 / 3.0)
                )
            else:
                aid.qm[i] = 0.0


class Calc_QM_V2(modeltools.Method):
    """Calculate the discharge of the main channel following the kinematic
    wave approach.

    Basic equation:
      :math:`QM = \\frac{QMDH}{AMDH} \\cdot AM`

    Examples:

        Note the handling of zero values for |AMDH| (in the second subsection):

        >>> from hydpy.models.kinw import *
        >>> parameterstep()
        >>> gts(2)
        >>> aides.am = 4.0, 4.0
        >>> aides.qmdh = 3.0, 3.0
        >>> aides.amdh = 2.0, 0.0
        >>> model.calc_qm_v2()
        >>> aides.qm
        qm(6.0, 0.0)
    """

    CONTROLPARAMETERS = (kinw_control.GTS,)
    REQUIREDSEQUENCES = (kinw_aides.AM, kinw_aides.QMDH, kinw_aides.AMDH)
    RESULTSEQUENCES = (kinw_aides.QM,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            if aid.amdh[i] > 0.0:
                aid.qm[i] = aid.qmdh[i] / aid.amdh[i] * aid.am[i]
            else:
                aid.qm[i] = 0.0


class Calc_QMDH_V1(modeltools.Method):
    """Calculate the derivative of the discharge of the main channel
    following method |Calc_QM_V1|.

    Basic equation:
      :math:`QMDH = MFM \\cdot
      \\frac{5 \\cdot  AM^{2/3} \\cdot AMDH}{3 \\cdot UM^{2/3}} -
      \\frac{2 \\cdot  AM^{5/3} \\cdot UMDH}{3 \\cdot UM^{5/3}}`

    Examples:

        First, we apply the class |NumericalDifferentiator| to validate the
        calculated derivatives:

        >>> from hydpy.models.kinw import *
        >>> parameterstep()
        >>> gts(2)
        >>> bm(2.0)
        >>> bnm(4.0)
        >>> hm(2.0)
        >>> derived.mfm(10.0)
        >>> derived.hrp(0.0)
        >>> derived.bnmf.update()
        >>> states.h = 0.0, 1.0
        >>> model.calc_rhm_v1()
        >>> model.calc_rhmdh_v1()
        >>> model.calc_rhv_v1()
        >>> model.calc_rhvdh_v1()
        >>> model.calc_am_um_v1()
        >>> model.calc_amdh_umdh_v1()
        >>> model.calc_qmdh_v1()
        >>> aides.qmdh
        qmdh(0.0, 94.12356)

        >>> from hydpy import NumericalDifferentiator,pub
        >>> numdiff = NumericalDifferentiator(
        ...     xsequence=states.h,
        ...     ysequences=[aides.qm],
        ...     methods=[model.calc_rhm_v1,
        ...              model.calc_rhv_v1,
        ...              model.calc_am_um_v1,
        ...              model.calc_qm_v1],
        ...     dx=1e-8)
        >>> with pub.options.reprdigits(5):
        ...     numdiff()
        d_qm/d_h: 0.00002, 94.12356

        Second, we show that zero values for |AM| or |UM| result in zero
        values for |QMDH|:

        >>> aides.am = 1.0, 0.0
        >>> aides.um = 0.0, 1.0
        >>> model.calc_qmdh_v1()
        >>> aides.qmdh
        qmdh(0.0, 0.0)
    """

    CONTROLPARAMETERS = (kinw_control.GTS,)
    DERIVEDPARAMETERS = (kinw_derived.MFM,)
    REQUIREDSEQUENCES = (kinw_aides.AM, kinw_aides.AMDH, kinw_aides.UM, kinw_aides.UMDH)
    RESULTSEQUENCES = (kinw_aides.QMDH,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            if (aid.am[i] > 0.0) and (aid.um[i] > 0.0):
                aid.qmdh[i] = der.mfm * (
                    5.0
                    * aid.am[i] ** (2.0 / 3.0)
                    * aid.amdh[i]
                    / (3.0 * aid.um[i] ** (2.0 / 3.0))
                    - 2.0
                    * aid.am[i] ** (5.0 / 3.0)
                    * aid.umdh[i]
                    / (3.0 * aid.um[i] ** (5.0 / 3.0))
                )
            else:
                aid.qmdh[i] = 0.0


class Calc_QLV_QRV_V1(modeltools.Method):
    """Calculate the discharge of both forelands after Manning-Strickler.

    Basic equation:
      :math:`QV = MFV \\cdot \\frac{AV^{5/3}}{UV^{2/3}}`

    Examples:

        Note the handling of zero values for |ULV| and |URV| (in the second
        subsection):

        >>> from hydpy.models.kinw import *
        >>> parameterstep()
        >>> gts(2)
        >>> derived.mfv(left=10.0, right=18.0)
        >>> aides.alv = 3.0, 3.0
        >>> aides.arv = 4.0, 4.0
        >>> aides.ulv = 7.0, 0.0
        >>> aides.urv = 8.0, 0.0
        >>> model.calc_qlv_qrv_v1()
        >>> aides.qlv
        qlv(17.053102, 0.0)
        >>> aides.qrv
        qrv(45.357158, 0.0)
    """

    CONTROLPARAMETERS = (kinw_control.GTS,)
    DERIVEDPARAMETERS = (kinw_derived.MFV,)
    REQUIREDSEQUENCES = (kinw_aides.ALV, kinw_aides.ARV, kinw_aides.ULV, kinw_aides.URV)
    RESULTSEQUENCES = (kinw_aides.QLV, kinw_aides.QRV)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            if aid.ulv[i] > 0.0:
                aid.qlv[i] = (
                    der.mfv[0] * aid.alv[i] ** (5.0 / 3.0) / aid.ulv[i] ** (2.0 / 3.0)
                )
            else:
                aid.qlv[i] = 0.0
            if aid.urv[i] > 0:
                aid.qrv[i] = (
                    der.mfv[1] * aid.arv[i] ** (5.0 / 3.0) / aid.urv[i] ** (2.0 / 3.0)
                )
            else:
                aid.qrv[i] = 0.0


class Calc_QLV_QRV_V2(modeltools.Method):
    """Calculate the discharge of both forelands following the kinematic
    wave approach.

    Basic equation:
      :math:`QV = \\frac{QVDH}{AVDH} \\cdot AV`

    Examples:

        Note the handling of zero values for |ALVDH| and |ARVDH| (in the
        second subsection):

        >>> from hydpy.models.kinw import *
        >>> parameterstep()
        >>> gts(2)
        >>> aides.alv = 3.0, 3.0
        >>> aides.arv = 5.0, 5.0
        >>> aides.qlvdh = 4.0, 4.0
        >>> aides.qrvdh = 6.0, 6.0
        >>> aides.alvdh = 2.0, 0.0
        >>> aides.arvdh = 4.0, 0.0
        >>> model.calc_qlv_qrv_v2()
        >>> aides.qlv
        qlv(6.0, 0.0)
        >>> aides.qrv
        qrv(7.5, 0.0)
    """

    CONTROLPARAMETERS = (kinw_control.GTS,)
    REQUIREDSEQUENCES = (
        kinw_aides.ALV,
        kinw_aides.ARV,
        kinw_aides.ALVDH,
        kinw_aides.ARVDH,
        kinw_aides.QLVDH,
        kinw_aides.QRVDH,
    )
    RESULTSEQUENCES = (kinw_aides.QLV, kinw_aides.QRV)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            if aid.alvdh[i] > 0.0:
                aid.qlv[i] = aid.qlvdh[i] / aid.alvdh[i] * aid.alv[i]
            else:
                aid.qlv[i] = 0.0
            if aid.arvdh[i] > 0.0:
                aid.qrv[i] = aid.qrvdh[i] / aid.arvdh[i] * aid.arv[i]
            else:
                aid.qrv[i] = 0.0


class Calc_QLVDH_QRVDH_V1(modeltools.Method):
    """Calculate the derivative of both forelands' discharge with respect to the stage
    following method |Calc_QLV_QRV_V1|.

    Basic equation:
      :math:`QVDH = MFV \\cdot
      \\frac{5 \\cdot  AV^{2/3} \\cdot AVDH}{3 \\cdot UV^{2/3}} -
      \\frac{2 \\cdot  AV^{5/3} \\cdot UVDH}{3 \\cdot UV^{5/3}}`

    Examples:

        First, we apply the class |NumericalDifferentiator| to validate the
        calculated derivatives:

        >>> from hydpy.models.kinw import *
        >>> parameterstep()
        >>> gts(2)
        >>> hm(1.0)
        >>> bv(left=2.0, right=3.0)
        >>> bnv(left=4.0, right=5.0)
        >>> derived.bnvf.update()
        >>> derived.hv(left=1.0, right=2.0)
        >>> derived.mfv(left=10.0, right=18.0)
        >>> derived.hrp(0.0)
        >>> states.h = 0.5, 1.5
        >>> model.calc_rhv_v1()
        >>> model.calc_rhvdh_v1()
        >>> model.calc_rhlvr_rhrvr_v1()
        >>> model.calc_rhlvrdh_rhrvrdh_v1()
        >>> model.calc_alv_arv_ulv_urv_v1()
        >>> model.calc_alvdh_arvdh_ulvdh_urvdh_v1()
        >>> model.calc_qlvdh_qrvdh_v1()
        >>> aides.qlvdh
        qlvdh(0.0, 29.091363)
        >>> aides.qrvdh
        qrvdh(0.0, 74.651886)

        >>> from hydpy import NumericalDifferentiator
        >>> numdiff = NumericalDifferentiator(
        ...     xsequence=states.h,
        ...     ysequences=[aides.qlv, aides.qrv],
        ...     methods=[model.calc_rhv_v1,
        ...              model.calc_rhlvr_rhrvr_v1,
        ...              model.calc_alv_arv_ulv_urv_v1,
        ...              model.calc_qlv_qrv_v1])()
        d_qlv/d_h: 0.0, 29.091363
        d_qrv/d_h: 0.0, 74.651886

        Second, we show that zero values for |ALV| or |ULV| as well as for
        |ARV| or |URV| result in zero values for |QLVDH| or |QRVDH|,
        respectively:

        >>> aides.alv = 1.0, 0.0
        >>> aides.ulv = 0.0, 1.0
        >>> aides.arv = 1.0, 0.0
        >>> aides.urv = 0.0, 1.0
        >>> model.calc_qlvdh_qrvdh_v1()
        >>> aides.qlvdh
        qlvdh(0.0, 0.0)
        >>> aides.qrvdh
        qrvdh(0.0, 0.0)
    """

    CONTROLPARAMETERS = (kinw_control.GTS,)
    DERIVEDPARAMETERS = (kinw_derived.MFV,)
    REQUIREDSEQUENCES = (
        kinw_aides.ALV,
        kinw_aides.ALVDH,
        kinw_aides.ARV,
        kinw_aides.ARVDH,
        kinw_aides.ULV,
        kinw_aides.ULVDH,
        kinw_aides.URV,
        kinw_aides.URVDH,
    )
    RESULTSEQUENCES = (kinw_aides.QLVDH, kinw_aides.QRVDH)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            if (aid.alv[i] > 0.0) and (aid.ulv[i] > 0.0):
                aid.qlvdh[i] = der.mfv[0] * (
                    5.0
                    * aid.alv[i] ** (2.0 / 3.0)
                    * aid.alvdh[i]
                    / (3.0 * aid.ulv[i] ** (2.0 / 3.0))
                    - 2.0
                    * aid.alv[i] ** (5.0 / 3.0)
                    * aid.ulvdh[i]
                    / (3.0 * aid.ulv[i] ** (5.0 / 3.0))
                )
            else:
                aid.qlvdh[i] = 0.0
            if (aid.arv[i] > 0.0) and (aid.urv[i] > 0.0):
                aid.qrvdh[i] = der.mfv[1] * (
                    5.0
                    * aid.arv[i] ** (2.0 / 3.0)
                    * aid.arvdh[i]
                    / (3.0 * aid.urv[i] ** (2.0 / 3.0))
                    - 2.0
                    * aid.arv[i] ** (5.0 / 3.0)
                    * aid.urvdh[i]
                    / (3.0 * aid.urv[i] ** (5.0 / 3.0))
                )
            else:
                aid.qrvdh[i] = 0.0


class Calc_QLVR_QRVR_V1(modeltools.Method):
    """Calculate the discharge of both outer embankments after
    Manning-Strickler.

    Basic equation:
      :math:`QVR = MFV \\cdot \\frac{AVR^{5/3}}{UVR^{2/3}}`

    Examples:

        Note the handling of zero values for |ULVR| and |URVR| (in the second
        subsection):

        >>> from hydpy.models.kinw import *
        >>> parameterstep()
        >>> gts(2)
        >>> derived.mfv(left=10.0, right=1.2)
        >>> aides.alvr = 3.0, 3.0
        >>> aides.arvr = 4.0, 4.0
        >>> aides.ulvr = 7.0, 0.0
        >>> aides.urvr = 8.0, 0.0
        >>> model.calc_qlvr_qrvr_v1()
        >>> aides.qlvr
        qlvr(17.053102, 0.0)
        >>> aides.qrvr
        qrvr(3.023811, 0.0)
    """

    CONTROLPARAMETERS = (kinw_control.GTS,)
    DERIVEDPARAMETERS = (kinw_derived.MFV,)
    REQUIREDSEQUENCES = (
        kinw_aides.ALVR,
        kinw_aides.ARVR,
        kinw_aides.ULVR,
        kinw_aides.URVR,
    )
    RESULTSEQUENCES = (kinw_aides.QLVR, kinw_aides.QRVR)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            if aid.ulvr[i] > 0.0:
                aid.qlvr[i] = (
                    der.mfv[0] * aid.alvr[i] ** (5.0 / 3.0) / aid.ulvr[i] ** (2.0 / 3.0)
                )
            else:
                aid.qlvr[i] = 0.0
            if aid.urvr[i] > 0.0:
                aid.qrvr[i] = (
                    der.mfv[1] * aid.arvr[i] ** (5.0 / 3.0) / aid.urvr[i] ** (2.0 / 3.0)
                )
            else:
                aid.qrvr[i] = 0.0


class Calc_QLVR_QRVR_V2(modeltools.Method):
    """Calculate the discharge of both outer embankments following the
    kinematic wave approach.

    Basic equation:
      :math:`QVR = \\frac{QVRDH}{AVRDH} \\cdot AVR`

    Examples:

        Note the handling of zero values for |ALVRDH| and |ARVRDH| (in the
        second subsection):

        >>> from hydpy.models.kinw import *
        >>> parameterstep()
        >>> gts(2)
        >>> aides.alvr = 3.0, 3.0
        >>> aides.arvr = 5.0, 5.0
        >>> aides.qlvrdh = 4.0, 4.0
        >>> aides.qrvrdh = 6.0, 6.0
        >>> aides.alvrdh = 2.0, 0.0
        >>> aides.arvrdh = 4.0, 0.0
        >>> model.calc_qlvr_qrvr_v2()
        >>> aides.qlvr
        qlvr(6.0, 0.0)
        >>> aides.qrvr
        qrvr(7.5, 0.0)
    """

    CONTROLPARAMETERS = (kinw_control.GTS,)
    REQUIREDSEQUENCES = (
        kinw_aides.ALVR,
        kinw_aides.ARVR,
        kinw_aides.QLVRDH,
        kinw_aides.QRVRDH,
        kinw_aides.ALVRDH,
        kinw_aides.ARVRDH,
    )
    RESULTSEQUENCES = (kinw_aides.QLVR, kinw_aides.QRVR)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            if aid.alvrdh[i] > 0.0:
                aid.qlvr[i] = aid.qlvrdh[i] / aid.alvrdh[i] * aid.alvr[i]
            else:
                aid.qlvr[i] = 0.0
            if aid.arvrdh[i] > 0.0:
                aid.qrvr[i] = aid.qrvrdh[i] / aid.arvrdh[i] * aid.arvr[i]
            else:
                aid.qrvr[i] = 0.0


class Calc_QLVRDH_QRVRDH_V1(modeltools.Method):
    """Calculate the derivative of the discharge over the outer embankments
    with respect to the stage following method |Calc_QLVR_QRVR_V1|.

    Basic equation:
      :math:`QVRDH = MFVR \\cdot
      \\frac{5 \\cdot  AVR^{2/3} \\cdot AVRDH}{3 \\cdot UVR^{2/3}} -
      \\frac{2 \\cdot  AVR{5/3} \\cdot UVRDH}{3 \\cdot UVR^{5/3}}`

    Examples:

        First, we apply the class |NumericalDifferentiator| to validate the
        calculated derivatives:

        >>> from hydpy.models.kinw import *
        >>> parameterstep()
        >>> gts(2)
        >>> hm(1.0)
        >>> bnvr(left=4.0, right=5.0)
        >>> derived.bnvrf.update()
        >>> derived.hv(left=1.0, right=2.0)
        >>> derived.mfv(left=10.0, right=18.0)
        >>> derived.hrp(0.0)
        >>> states.h = 1.5, 3.5
        >>> model.calc_rhlvr_rhrvr_v1()
        >>> model.calc_rhlvrdh_rhrvrdh_v1()
        >>> model.calc_alvr_arvr_ulvr_urvr_v1()
        >>> model.calc_alvrdh_arvrdh_ulvrdh_urvrdh_v1()
        >>> model.calc_qlvrdh_qrvrdh_v1()
        >>> aides.qlvrdh
        qlvrdh(0.0, 64.717418)
        >>> aides.qrvrdh
        qrvrdh(0.0, 23.501747)

        >>> from hydpy import NumericalDifferentiator
        >>> NumericalDifferentiator(
        ...     xsequence=states.h,
        ...     ysequences=[aides.qlvr, aides.qrvr],
        ...     methods=[model.calc_rhlvr_rhrvr_v1,
        ...              model.calc_alvr_arvr_ulvr_urvr_v1,
        ...              model.calc_qlvr_qrvr_v1])()
        d_qlvr/d_h: 0.0, 64.717418
        d_qrvr/d_h: 0.0, 23.501747

        Second, we show that zero values for |ALVR| or |ULVR| as well as for
        |ARVR| or |URVR| result in zero values for |QLVRDH| or |QRVRDH|,
        respectively:

        >>> aides.alvr = 1.0, 0.0
        >>> aides.ulvr = 0.0, 1.0
        >>> aides.arvr = 1.0, 0.0
        >>> aides.urvr = 0.0, 1.0
        >>> model.calc_qlvrdh_qrvrdh_v1()
        >>> aides.qlvrdh
        qlvrdh(0.0, 0.0)
        >>> aides.qrvrdh
        qrvrdh(0.0, 0.0)
    """

    CONTROLPARAMETERS = (kinw_control.GTS,)
    DERIVEDPARAMETERS = (kinw_derived.MFV,)
    REQUIREDSEQUENCES = (
        kinw_aides.ALVR,
        kinw_aides.ALVRDH,
        kinw_aides.ARVR,
        kinw_aides.ARVRDH,
        kinw_aides.ULVR,
        kinw_aides.ULVRDH,
        kinw_aides.URVR,
        kinw_aides.URVRDH,
    )
    RESULTSEQUENCES = (kinw_aides.QLVRDH, kinw_aides.QRVRDH)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            if (aid.alvr[i] > 0.0) and (aid.ulvr[i] > 0.0):
                aid.qlvrdh[i] = der.mfv[0] * (
                    5.0
                    * aid.alvr[i] ** (2.0 / 3.0)
                    * aid.alvrdh[i]
                    / (3.0 * aid.ulvr[i] ** (2.0 / 3.0))
                    - 2.0
                    * aid.alvr[i] ** (5.0 / 3.0)
                    * aid.ulvrdh[i]
                    / (3.0 * aid.ulvr[i] ** (5.0 / 3.0))
                )
            else:
                aid.qlvrdh[i] = 0.0
            if (aid.arvr[i] > 0.0) and (aid.urvr[i] > 0.0):
                aid.qrvrdh[i] = der.mfv[1] * (
                    5.0
                    * aid.arvr[i] ** (2.0 / 3.0)
                    * aid.arvrdh[i]
                    / (3.0 * aid.urvr[i] ** (2.0 / 3.0))
                    - 2.0
                    * aid.arvr[i] ** (5.0 / 3.0)
                    * aid.urvrdh[i]
                    / (3.0 * aid.urvr[i] ** (5.0 / 3.0))
                )
            else:
                aid.qrvrdh[i] = 0.0


class Calc_AG_V1(modeltools.Method):
    """Calculate the through wetted of the total cross-sections.

    Basic equation:
      :math:`AG = AM+ALV+ARV+ALVR+ARVR`

    Example:

        >>> from hydpy.models.kinw import *
        >>> parameterstep()
        >>> gts(2)
        >>> aides.am = 0.0, 1.0
        >>> aides.alv = 2.0, 4.0
        >>> aides.arv = 3.0, 5.0
        >>> aides.alvr = 6.0, 8.0
        >>> aides.arvr = 7.0, 9.0
        >>> model.calc_ag_v1()
        >>> aides.ag
        ag(18.0, 27.0)
    """

    CONTROLPARAMETERS = (kinw_control.GTS,)
    REQUIREDSEQUENCES = (
        kinw_aides.AM,
        kinw_aides.ALV,
        kinw_aides.ARV,
        kinw_aides.ALVR,
        kinw_aides.ARVR,
    )
    RESULTSEQUENCES = (kinw_aides.AG,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            aid.ag[i] = aid.am[i] + aid.alv[i] + aid.arv[i] + aid.alvr[i] + aid.arvr[i]


class Calc_QG_V1(modeltools.Method):
    """Calculate the discharge of the total cross-section.

    Basic equation:
      :math:`QG = QM + QLV + QRV + QLVR + QRVR`

    Example:

        >>> from hydpy.models.kinw import *
        >>> parameterstep()
        >>> gts(2)
        >>> aides.qm = 0.0, 1.0
        >>> aides.qlv = 2.0, 4.0
        >>> aides.qrv = 3.0, 5.0
        >>> aides.qlvr = 6.0, 8.0
        >>> aides.qrvr = 7.0, 9.0
        >>> model.calc_qg_v1()
        >>> fluxes.qg
        qg(18.0, 27.0)
    """

    CONTROLPARAMETERS = (kinw_control.GTS,)
    REQUIREDSEQUENCES = (
        kinw_aides.QM,
        kinw_aides.QLV,
        kinw_aides.QRV,
        kinw_aides.QLVR,
        kinw_aides.QRVR,
    )
    RESULTSEQUENCES = (kinw_fluxes.QG,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            flu.qg[i] = aid.qm[i] + aid.qlv[i] + aid.qrv[i] + aid.qlvr[i] + aid.qrvr[i]


class Calc_QG_V2(modeltools.Method):
    r"""Calculate the discharge of the total cross-section based on an interpolated
    flow velocity.

    Basic equation:
      :math:`QG = EK \cdot \frac{1000 \cdot V_{interpolated} \cdot VG \cdot GTS}{Laen}`

    Example:

        For simplicity, we define a linear between flow velocity and water storage:

        >>> from hydpy.models.kinw import *
        >>> parameterstep()
        >>> gts(2)
        >>> laen(10.0)
        >>> ek(0.5)
        >>> vg2fg(PPoly.from_data(xs=[0.0, 1.0], ys=[0.0, 1.0]))
        >>> from hydpy import UnitTest
        >>> test = UnitTest(model,
        ...                 model.calc_qg_v2,
        ...                 last_example=3,
        ...                 parseqs=(states.vg,
        ...                          fluxes.qg))
        >>> test.nexts.vg = numpy.empty((4, 2))
        >>> test.nexts.vg[:, 0] = numpy.arange(-1.0, 3.0)
        >>> test.nexts.vg[:, 1] = numpy.arange(3.0, 7.0)
        >>> test()
        | ex. |        vg |            qg |
        -----------------------------------
        |   1 | -1.0  3.0 |   0.0   900.0 |
        |   2 |  0.0  4.0 |   0.0  1600.0 |
        |   3 |  1.0  5.0 | 100.0  2500.0 |

        Our example shows that a linear velocity-volume relationship results in a
        quadratic discharge-volume relationship. Note also that we generally set the
        discharge to zero for negative volumes.

        For more realistic approximations of measured relationships between
        storage and discharge, we require larger neural networks.
    """

    CONTROLPARAMETERS = (
        kinw_control.GTS,
        kinw_control.Laen,
        kinw_control.VG2FG,
        kinw_control.EK,
    )
    REQUIREDSEQUENCES = (kinw_states.VG,)
    RESULTSEQUENCES = (kinw_fluxes.QG,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        sta = model.sequences.states.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for i in range(con.gts):
            con.vg2fg.inputs[0] = sta.vg[i]
            con.vg2fg.calculate_values()
            d_v = max(con.ek * con.vg2fg.outputs[0], 0.0)
            flu.qg[i] = 1000.0 * d_v * sta.vg[i] * con.gts / con.laen


class Calc_WBM_V1(modeltools.Method):
    """Calculate the water table width above the main channel.

    Examples:

        Due to :math:`WBM = \\frac{dAM}{dh}`, we can apply the class
        |NumericalDifferentiator| to validate the calculated water
        table widths:

        >>> from hydpy.models.kinw import *
        >>> parameterstep()
        >>> gts(5)
        >>> bm(4.0)
        >>> bnm(2.0)
        >>> hm(1.0)
        >>> hr(0.0)
        >>> derived.hrp.update()
        >>> states.h = 0.0, 0.9, 1.0, 1.1, 2.0
        >>> model.calc_rhm_v1()
        >>> model.calc_rhmdh_v1()
        >>> model.calc_rhv_v1()
        >>> model.calc_rhvdh_v1()
        >>> model.calc_wbm_v1()
        >>> aides.wbm
        wbm(4.0, 7.6, 8.0, 8.0, 8.0)

        >>> from hydpy import NumericalDifferentiator
        >>> numdiff = NumericalDifferentiator(
        ...     xsequence=states.h,
        ...     ysequences=[aides.am],
        ...     methods=[model.calc_rhm_v1,
        ...              model.calc_rhv_v1,
        ...              model.calc_am_um_v1])
        >>> numdiff()
        d_am/d_h: 4.0, 7.6, 8.0, 8.0, 8.0

        >>> hr(0.1)
        >>> derived.hrp.update()
        >>> model.calc_rhm_v1()
        >>> model.calc_rhmdh_v1()
        >>> model.calc_rhv_v1()
        >>> model.calc_rhvdh_v1()
        >>> model.calc_wbm_v1()
        >>> aides.wbm
        wbm(2.081965, 7.593774, 7.918034, 8.028465, 8.0)

        >>> numdiff()
        d_am/d_h: 2.081965, 7.593774, 7.918034, 8.028465, 8.0
    """

    CONTROLPARAMETERS = (kinw_control.GTS, kinw_control.BM, kinw_control.BNM)
    FIXEDPARAMETERS = (kinw_fixed.WBMin, kinw_fixed.WBReg)
    REQUIREDSEQUENCES = (
        kinw_aides.RHM,
        kinw_aides.RHMDH,
        kinw_aides.RHV,
        kinw_aides.RHVDH,
    )
    RESULTSEQUENCES = (kinw_aides.WBM,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fix = model.parameters.fixed.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            d_temp1 = aid.rhm[i] - aid.rhv[i]
            d_temp2 = aid.rhmdh[i] - aid.rhvdh[i]
            aid.wbm[i] = (
                con.bnm * d_temp1 * d_temp2
                + con.bnm * 2.0 * d_temp2 * aid.rhv[i]
                + (con.bm + con.bnm * d_temp1) * d_temp2
                + (con.bm + con.bnm * 2.0 * d_temp1) * aid.rhvdh[i]
            )
            aid.wbm[i] = smoothutils.smooth_max1(fix.wbmin, aid.wbm[i], fix.wbreg)


class Calc_WBLV_WBRV_V1(modeltools.Method):
    """Calculate the water table width above both forelands.

    Examples:

        Due to :math:`WBV = \\frac{dAV}{dh}`, we can apply the class
        |NumericalDifferentiator| to validate the calculated water
        table widths:

        >>> from hydpy.models.kinw import *
        >>> parameterstep()
        >>> gts(11)
        >>> bm(4.0)
        >>> bnm(2.0)
        >>> derived.bnvf.update()
        >>> hm(1.0)
        >>> bv(left=2.0, right=3.0)
        >>> bbv(left=10., right=40.)
        >>> bnv(left=10., right=20.)
        >>> derived.hv.update()
        >>> derived.hv
        hv(left=1.0, right=2.0)
        >>> hr(0.0)
        >>> derived.hrp.update()
        >>> states.h = 1.0, 1.5, 1.9, 2.0, 2.1, 2.5, 2.9, 3.0, 3.1, 3.5, 4.0
        >>> model.calc_rhv_v1()
        >>> model.calc_rhvdh_v1()
        >>> model.calc_rhlvr_rhrvr_v1()
        >>> model.calc_rhlvrdh_rhrvrdh_v1()
        >>> model.calc_wblv_wbrv_v1()
        >>> aides.wblv
        wblv(2.0, 7.0, 11.0, 12.0, 12.0, 12.0, 12.0, 12.0, 12.0, 12.0, 12.0)
        >>> aides.wbrv
        wbrv(3.0, 13.0, 21.0, 23.0, 25.0, 33.0, 41.0, 43.0, 43.0, 43.0, 43.0)

        >>> from hydpy import NumericalDifferentiator
        >>> numdiff = NumericalDifferentiator(
        ...     xsequence=states.h,
        ...     ysequences=[aides.alv, aides.arv],
        ...     methods=[model.calc_rhv_v1,
        ...              model.calc_rhlvr_rhrvr_v1,
        ...              model.calc_alv_arv_ulv_urv_v1])
        >>> numdiff()
        d_alv/d_h: 2.0, 7.0, 11.0, 12.0, 12.0, 12.0, 12.0, 12.0, 12.0, \
12.0, 12.0
        d_arv/d_h: 3.0, 13.0, 21.0, 23.0, 25.0, 33.0, 41.0, 43.0, 43.0, \
43.0, 43.0

        >>> hr(0.1)
        >>> derived.hrp.update()
        >>> model.calc_rhv_v1()
        >>> model.calc_rhvdh_v1()
        >>> model.calc_rhlvr_rhrvr_v1()
        >>> model.calc_rhlvrdh_rhrvrdh_v1()
        >>> model.calc_wblv_wbrv_v1()
        >>> aides.wblv
        wblv(1.204913, 6.998638, 10.984437, 11.795086, 12.071163, 12.000937,
             12.000002, 12.0, 12.0, 12.0, 12.0)
        >>> aides.wbrv
        wbrv(1.909826, 12.997489, 20.999995, 22.999999, 25.0, 33.0, 40.96888,
             42.590174, 43.142325, 43.001873, 43.000001)

        >>> numdiff()
        d_alv/d_h: 1.204913, 6.998638, 10.984437, 11.795086, 12.071163, \
12.000937, 12.000002, 12.0, 12.0, 12.0, 12.0
        d_arv/d_h: 1.909826, 12.997489, 20.999995, 22.999999, 25.0, 33.0, \
40.96888, 42.590174, 43.142325, 43.001873, 43.000001
    """

    CONTROLPARAMETERS = (kinw_control.GTS, kinw_control.BV, kinw_control.BNV)
    REQUIREDSEQUENCES = (
        kinw_aides.RHV,
        kinw_aides.RHVDH,
        kinw_aides.RHLVR,
        kinw_aides.RHLVRDH,
        kinw_aides.RHRVR,
        kinw_aides.RHRVRDH,
    )
    RESULTSEQUENCES = (kinw_aides.WBLV, kinw_aides.WBRV)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            d_temp1 = aid.rhv[i] - aid.rhlvr[i]
            d_temp2 = aid.rhvdh[i] - aid.rhlvrdh[i]
            aid.wblv[i] = (
                con.bnv[0] * d_temp1 * d_temp2 / 2.0
                + con.bnv[0] * d_temp2 * aid.rhlvr[i]
                + (con.bnv[0] * d_temp1 / 2.0 + con.bv[0]) * d_temp2
                + (con.bnv[0] * d_temp1 + con.bv[0]) * aid.rhlvrdh[i]
            )
            d_temp1 = aid.rhv[i] - aid.rhrvr[i]
            d_temp2 = aid.rhvdh[i] - aid.rhrvrdh[i]
            aid.wbrv[i] = (
                con.bnv[1] * d_temp1 * d_temp2 / 2.0
                + con.bnv[1] * d_temp2 * aid.rhrvr[i]
                + (con.bnv[1] * d_temp1 / 2.0 + con.bv[1]) * d_temp2
                + (con.bnv[1] * d_temp1 + con.bv[1]) * aid.rhrvrdh[i]
            )


class Calc_WBLVR_WBRVR_V1(modeltools.Method):
    """Calculate the water table width above both outer embankments.

    Examples:

        Due to :math:`WBVR = \\frac{dAVR}{dh}`, we can apply the class
        |NumericalDifferentiator| to validate the calculated water
        table widths:

        >>> from hydpy.models.kinw import *
        >>> parameterstep()
        >>> gts(11)
        >>> hm(1.0)
        >>> bnvr(left=4.0, right=5.0)
        >>> derived.bnvrf.update()
        >>> derived.hv(left=1.0, right=2.0)
        >>> hr(0.0)
        >>> derived.hrp.update()
        >>> states.h = 1.0, 1.5, 1.9, 2.0, 2.1, 2.5, 2.9, 3.0, 3.1, 3.5, 4.0
        >>> model.calc_rhlvr_rhrvr_v1()
        >>> model.calc_rhlvrdh_rhrvrdh_v1()
        >>> model.calc_wblvr_wbrvr_v1()
        >>> aides.wblvr
        wblvr(0.0, 0.0, 0.0, 0.0, 0.4, 2.0, 3.6, 4.0, 4.4, 6.0, 8.0)
        >>> aides.wbrvr
        wbrvr(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 2.5, 5.0)

        >>> from hydpy import NumericalDifferentiator
        >>> numdiff = NumericalDifferentiator(
        ...     xsequence=states.h,
        ...     ysequences=[aides.alvr, aides.arvr],
        ...     methods=[model.calc_rhlvr_rhrvr_v1,
        ...              model.calc_alvr_arvr_ulvr_urvr_v1])
        >>> numdiff()
        d_alvr/d_h: 0.0, 0.0, 0.0, 0.0, 0.4, 2.0, 3.6, 4.0, 4.4, 6.0, 8.0
        d_arvr/d_h: 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 2.5, 5.0

        >>> hr(0.1)
        >>> derived.hrp.update()
        >>> model.calc_rhlvr_rhrvr_v1()
        >>> model.calc_rhlvrdh_rhrvrdh_v1()
        >>> model.calc_wblvr_wbrvr_v1()
        >>> aides.wblvr
        wblvr(0.0, 0.0, 0.006224, 0.081965, 0.371535, 1.999625, 3.599999, 4.0,
              4.4, 6.0, 8.0)
        >>> aides.wbrvr
        wbrvr(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.00778, 0.102457, 0.464419,
              2.499532, 5.0)

        >>> numdiff()
        d_alvr/d_h: 0.0, 0.0, 0.006224, 0.081965, 0.371535, 1.999625, \
3.599999, 4.0, 4.4, 6.0, 8.0
        d_arvr/d_h: 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.00778, 0.102457, \
0.464419, 2.499532, 5.0
    """

    CONTROLPARAMETERS = (kinw_control.GTS, kinw_control.BNVR)
    REQUIREDSEQUENCES = (
        kinw_aides.RHLVR,
        kinw_aides.RHLVRDH,
        kinw_aides.RHRVR,
        kinw_aides.RHRVRDH,
    )
    RESULTSEQUENCES = (kinw_aides.WBLVR, kinw_aides.WBRVR)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            aid.wblvr[i] = con.bnvr[0] * aid.rhlvr[i] * aid.rhlvrdh[i]
            aid.wbrvr[i] = con.bnvr[1] * aid.rhrvr[i] * aid.rhrvrdh[i]


class Calc_WBG_V1(modeltools.Method):
    """Calculate the water level width of the total cross-section.

    Basic equation:
      :math:`WBG = WBM+WLV+WRV+WLVR+WRVR`

    Example:

        >>> from hydpy.models.kinw import *
        >>> parameterstep()
        >>> gts(2)
        >>> aides.wbm = 0.0, 1.0
        >>> aides.wblv = 2.0, 4.0
        >>> aides.wbrv = 3.0, 5.0
        >>> aides.wblvr = 6.0, 8.0
        >>> aides.wbrvr = 7.0, 9.0
        >>> model.calc_wbg_v1()
        >>> aides.wbg
        wbg(18.0, 27.0)
    """

    CONTROLPARAMETERS = (kinw_control.GTS,)
    REQUIREDSEQUENCES = (
        kinw_aides.WBM,
        kinw_aides.WBLV,
        kinw_aides.WBRV,
        kinw_aides.WBLVR,
        kinw_aides.WBRVR,
    )
    RESULTSEQUENCES = (kinw_aides.WBG,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            aid.wbg[i] = (
                aid.wbm[i] + aid.wblv[i] + aid.wbrv[i] + aid.wblvr[i] + aid.wbrvr[i]
            )


class Calc_DH_V1(modeltools.Method):
    """Determine the change in the stage.

    Basic equation:
      :math:`DH = \\frac{QG_{i-1}-QG_i}{WBG \\cdot 1000 \\cdot Laen / GTS}`

    Example:

        >>> from hydpy.models.kinw import *
        >>> parameterstep()
        >>> laen(10.0)
        >>> gts(5)
        >>> aides.wbg(3.0, 3.5, 4.0, 3.5, 3.0)
        >>> fluxes.qz = 1.0
        >>> fluxes.qg = 2.0, 3.0, 4.0, 3.0, 2.0
        >>> model.calc_dh_v1()
        >>> fluxes.dh
        dh(-0.000167, -0.000143, -0.000125, 0.000143, 0.000167)
    """

    CONTROLPARAMETERS = (kinw_control.Laen, kinw_control.GTS)
    REQUIREDSEQUENCES = (kinw_fluxes.QZ, kinw_fluxes.QG, kinw_aides.WBG)
    RESULTSEQUENCES = (kinw_fluxes.DH,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            if i:
                d_qz = flu.qg[i - 1]
            else:
                d_qz = flu.qz
            flu.dh[i] = (d_qz - flu.qg[i]) / (1000.0 * con.laen / con.gts * aid.wbg[i])


class Update_H_V1(modeltools.Method):
    """Update the stage.

    Basic equation:
      :math:`\\frac{dH}{dt} = DH`

    Example:

        >>> from hydpy.models.kinw import *
        >>> parameterstep()
        >>> gts(5)
        >>> derived.sek(60*60)
        >>> fluxes.dh = -0.12, -0.1, -0.09, 0.1, 0.12
        >>> fluxes.dh /= 60*60
        >>> states.h(1.0, 1.2, 1.3, 1.2, 1.0)
        >>> model.update_h_v1()
        >>> states.h
        h(0.88, 1.1, 1.21, 1.3, 1.12)
    """

    CONTROLPARAMETERS = (kinw_control.GTS,)
    DERIVEDPARAMETERS = (kinw_derived.Sek,)
    REQUIREDSEQUENCES = (kinw_fluxes.DH,)
    UPDATEDSEQUENCES = (kinw_states.H,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        for i in range(con.gts):
            new.h[i] = old.h[i] + der.sek * flu.dh[i]


class Update_VG_V1(modeltools.Method):
    """Update the water volume.

    Basic equation:
      :math:`\\frac{dV}{dt} = QG_{i-1}-QG_i`

    Example:

        >>> from hydpy.models.kinw import *
        >>> parameterstep()
        >>> gts(5)
        >>> derived.sek(60*60)
        >>> states.vg(1.0, 1.2, 1.3, 1.2, 1.0)
        >>> fluxes.qza = 1.0
        >>> fluxes.qg = 3.0, 2.0, 4.0, 3.0, 5.0
        >>> model.update_vg_v1()
        >>> states.vg
        vg(0.9928, 1.2036, 1.2928, 1.2036, 0.9928)
    """

    CONTROLPARAMETERS = (kinw_control.GTS,)
    DERIVEDPARAMETERS = (kinw_derived.Sek,)
    REQUIREDSEQUENCES = (kinw_fluxes.QZA, kinw_fluxes.QG)
    UPDATEDSEQUENCES = (kinw_states.VG,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        for i in range(con.gts):
            if i:
                new.vg[i] = old.vg[i] + der.sek * (flu.qg[i - 1] - flu.qg[i]) / 1e6
            else:
                new.vg[i] = old.vg[i] + der.sek * (flu.qza - flu.qg[i]) / 1e6


class Calc_QA_V1(modeltools.Method):
    """Query the actual outflow.

    Examples:

        >>> from hydpy.models.kinw import *
        >>> parameterstep()
        >>> gts(3)
        >>> fluxes.qz = 1.0
        >>> fluxes.qg = 2.0, 3.0, 4.0
        >>> model.calc_qa_v1()
        >>> fluxes.qa
        qa(4.0)
        >>> gts(0)
        >>> model.calc_qa_v1()
        >>> fluxes.qa
        qa(1.0)
    """

    CONTROLPARAMETERS = (kinw_control.GTS,)
    REQUIREDSEQUENCES = (kinw_fluxes.QZ, kinw_fluxes.QG)
    RESULTSEQUENCES = (kinw_fluxes.QA,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        if con.gts > 0:
            flu.qa = flu.qg[con.gts - 1]
        else:
            flu.qa = flu.qz


class Update_WaterVolume_V1(modeltools.Method):
    r"""Update the old water volume with the current inflow.

    Examples:

        Method |Update_WaterVolume_V1| uses the value of sequence |kinw_fluxes.Inflow|
        for the first segment and the respective values of sequences
        |kinw_fluxes.InternalFlow| for the remaining segments:

        >>> from hydpy.models.kinw_impl_euler import *
        >>> parameterstep()
        >>> nmbsegments(3)
        >>> derived.seconds(1e6)
        >>> states.watervolume.old = 2.0, 3.0, 4.0
        >>> fluxes.inflow = 1.0
        >>> fluxes.internalflow = 2.0, 3.0
        >>> model.run_segments(model.update_watervolume_v1)
        >>> from hydpy import print_vector
        >>> print_vector(states.watervolume.old)
        3.0, 5.0, 7.0

        Negative inflow values are acceptable, even if they result in negative amounts
        of stored water:

        >>> fluxes.inflow = -4.0
        >>> fluxes.internalflow = -6.0, -6.0
        >>> model.run_segments(model.update_watervolume_v1)
        >>> print_vector(states.watervolume.old)
        -1.0, -1.0, 1.0
    """

    DERIVEDPARAMETERS = (kinw_derived.Seconds,)
    REQUIREDSEQUENCES = (kinw_fluxes.Inflow, kinw_fluxes.InternalFlow)
    UPDATEDSEQUENCES = (kinw_states.WaterVolume,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        old = model.sequences.states.fastaccess_old
        flu = model.sequences.fluxes.fastaccess

        i = model.idx_segment
        q: float = flu.inflow if (i == 0) else flu.internalflow[i - 1]
        old.watervolume[i] += q * der.seconds / 1e6


class Return_InitialWaterVolume_V1(modeltools.Method):
    r"""Calculate and return the initial water volume that agrees with the given
    final water depth following the implicit Euler method.

    Basic equation:
      .. math::
        A \cdot l / n \cdot 10^{-3} + Q \cdot s \cdot 10^{-6}
        \\ \\
        d = waterdepth \\
        A = f_{get\_wettedarea}(d) \\
        l = Length \\
        n = NmbSegments \\
        Q = f_{get\_discharge}(d) \\
        s = Seconds

    Examples:

        The calculated initial volume is the sum of the water volume at the end of the
        simulation step and the outflow during the simulation step:

        >>> from hydpy.models.kinw_impl_euler import *
        >>> parameterstep()
        >>> length(100.0)
        >>> nmbsegments(10)
        >>> derived.seconds(60 * 60 * 24)
        >>> with model.add_wqmodel_v1("wq_trapeze_strickler"):
        ...     nmbtrapezes(1)
        ...     bottomlevels(1.0)
        ...     bottomwidths(20.0)
        ...     sideslopes(0.0)
        ...     bottomslope(0.001)
        ...     stricklercoefficients(30.0)
        >>> from hydpy import round_
        >>> round_(model.return_initialwatervolume_v1(2.0))
        5.008867

        If a segment has zero length, it can, of course, store no water.  Hence, the
        returned value then only comprises the volume of the outflow of the current
        simulation step:

        >>> length(0.0)
        >>> round_(model.return_initialwatervolume_v1(2.0))
        4.608867

        Method |Return_InitialWaterVolume_V1| handles cases where the number of
        segments is zero as if the channel's length is zero (even if it is
        inconsistently set to a larger value):

        >>> length(100.0)
        >>> nmbsegments(0)
        >>> round_(model.return_initialwatervolume_v1(2.0))
        4.608867
    """

    CONTROLPARAMETERS = (kinw_control.Length, kinw_control.NmbSegments)
    DERIVEDPARAMETERS = (kinw_derived.Seconds,)

    @staticmethod
    def __call__(model: modeltools.Model, waterdepth: float) -> float:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess

        model.wqmodel.use_waterdepth(waterdepth)
        sublength = con.length / con.nmbsegments if con.nmbsegments > 0 else 0.0
        return (
            model.wqmodel.get_wettedarea() * sublength / 1e3
            + model.wqmodel.get_discharge() * der.seconds / 1e6
        )


class Return_VolumeError_V1(modeltools.Method):
    r"""Calculate and return the difference between the initial water volume that stems
    from the last simulation step plus the current inflow and the water volume that
    agrees with the given final water depth following the implicit Euler method.

    Basic equation:
      .. math::
        V_1 - V_2
        \\ \\
        V_1 = WaterVolume \\
        V_2 = f_{Return\_InitialWaterVolume\_V1}(waterdepth)

    Examples:

        >>> from hydpy.models.kinw_impl_euler import *
        >>> parameterstep()
        >>> length(100.0)
        >>> nmbsegments(10)
        >>> derived.seconds(60 * 60 * 24)
        >>> with model.add_wqmodel_v1("wq_trapeze_strickler"):
        ...     nmbtrapezes(1)
        ...     bottomlevels(1.0)
        ...     bottomwidths(20.0)
        ...     sideslopes(0.0)
        ...     bottomslope(0.001)
        ...     stricklercoefficients(30.0)
        >>> states.watervolume(4.0)
        >>> from hydpy import round_
        >>> round_(model.return_volumeerror_v1(2.0))
        -1.008867

        For a given water depth of zero, |Return_VolumeError_V1| simply returns the
        value of |InitialWaterVolume| to safe computation efforts:

        >>> round_(model.return_volumeerror_v1(0.0))
        4.0

        The following example shows that this simplification is correct:

        >>> round_(model.return_volumeerror_v1(1e-6))
        4.0
    """

    CONTROLPARAMETERS = (kinw_control.Length, kinw_control.NmbSegments)
    DERIVEDPARAMETERS = (kinw_derived.Seconds,)
    REQUIREDSEQUENCES = (kinw_states.WaterVolume,)
    SUBMETHODS = (Return_InitialWaterVolume_V1,)

    @staticmethod
    def __call__(model: modeltools.Model, waterdepth: float) -> float:
        old = model.sequences.states.fastaccess_old

        v: float = old.watervolume[model.idx_segment]
        if waterdepth == 0.0:
            return v
        return v - model.return_initialwatervolume_v1(waterdepth)


class PegasusImplicitEuler(roottools.Pegasus):
    """Pegasus iterator for determining the water level at the end of a simulation
    step."""

    METHODS = (Return_VolumeError_V1,)


class Calc_WaterDepth_V1(modeltools.Method):
    r"""Determine the new water depth based on the implicit Euler method.

    Examples:

        Compared to other (explicit) routing methods, the iterative approach of method
        |Update_WaterDepth_V1| to determine the final water depth for each river
        segment iteratively leads to high efficiency and (theoretically) absolute
        stability for short channel segments (namely, stiff problems with a high
        Courant number).  However, be aware that the accuracy of this iteration affects
        the overall simulation.  We begin demonstrating this with a single trapezoid
        and default numerical values:

        >>> from hydpy.models.kinw_impl_euler import *
        >>> parameterstep()
        >>> length(100.0)
        >>> nmbsegments(1)
        >>> with model.add_wqmodel_v1("wq_trapeze_strickler"):
        ...     nmbtrapezes(1)
        ...     bottomlevels(1.0)
        ...     bottomwidths(20.0)
        ...     sideslopes(0.0)
        ...     bottomslope(0.001)
        ...     stricklercoefficients(30.0)
        >>> derived.seconds(60 * 60 * 24)
        >>> derived.nmbdiscontinuities.update()
        >>> derived.finaldepth2initialvolume.update()
        >>> solver.watervolumetolerance.update()
        >>> solver.waterdepthtolerance.update()
        >>> model.idx_segment = 0

        The following test function prints the resulting water depth for several
        initial volumes and also prints the water volume-related error tolerance
        (internally calculated as
        :math:`WaterVolumeTolerance \cdot InitialWaterVolume`) and the actual error:

        >>> from hydpy import print_vector
        >>> def check_search_algorithm():
        ...     print("volume", "depth", "tolerance", "error")
        ...     for target_volume in (0.0, 0.1, 1.0, 2.0, 5.0, 10.0, 100.0):
        ...         states.watervolume.old = target_volume
        ...         model.calc_waterdepth_v1()
        ...         depth = factors.waterdepth.values[0]
        ...         volume = model.return_initialwatervolume_v1(depth)
        ...         tolerance = solver.watervolumetolerance * target_volume
        ...         error = target_volume - volume
        ...         print_vector([target_volume, depth, tolerance, error])

        All required and achieved accuracies are below the printed precisions:

        >>> check_search_algorithm()
        volume depth tolerance error
        0.0, 0.0, 0.0, 0.0
        0.1, 0.045296, 0.0, 0.0
        1.0, 0.356485, 0.0, 0.0
        2.0, 0.632911, 0.0, 0.0
        5.0, 1.312357, 0.0, 0.0
        10.0, 2.244486, 0.0, 0.0
        100.0, 13.729876, 0.0, 0.0

        If one wishes to improve accuracy or speed up the computation, it is preferable
        to decrease or increase |WaterVolumeTolerance|.  Here, we increase it and
        observe that higher numerical errors result:

        >>> solver.watervolumetolerance(1e-4)
        >>> check_search_algorithm()
        volume depth tolerance error
        0.0, 0.0, 0.0, 0.0
        0.1, 0.045296, 0.00001, 0.0
        1.0, 0.356498, 0.0001, -0.000042
        2.0, 0.632912, 0.0002, -0.000004
        5.0, 1.312356, 0.0005, 0.000004
        10.0, 2.244563, 0.001, -0.000447
        100.0, 13.729886, 0.01, -0.000091

        Alternatively, one can modify the solver parameter |WaterDepthTolerance|, whose
        value is used without any modification:

        >>> solver.watervolumetolerance(0.0)
        >>> solver.waterdepthtolerance(1e-2)
        >>> check_search_algorithm()
        volume depth tolerance error
        0.0, 0.0, 0.0, 0.0
        0.1, 0.045296, 0.0, 0.0
        1.0, 0.356498, 0.0, -0.000042
        2.0, 0.632912, 0.0, -0.000004
        5.0, 1.312356, 0.0, 0.000004
        10.0, 2.244563, 0.0, -0.000447
        100.0, 13.729876, 0.0, 0.0

        Now, we define a profile geometry consisting of 3 stacked trapezes:

        >>> with model.add_wqmodel_v1("wq_trapeze_strickler"):
        ...     nmbtrapezes(3)
        ...     bottomlevels(1.0, 3.0, 5.0)
        ...     bottomwidths(20.0)
        ...     sideslopes(0.0, 0.0, 0.0)
        ...     bottomslope(0.001)
        ...     stricklercoefficients(30.0)
        >>> derived.nmbdiscontinuities.update()
        >>> derived.finaldepth2initialvolume.update()
        >>> solver.watervolumetolerance.update()
        >>> solver.waterdepthtolerance.update()

        Method |Update_WaterDepth_V1| uses the relevant bottom depths of these trapezes
        as boundaries for the Pegasus method so that the corresponding discontinuities
        cannot slow down its convergence:

        >>> check_search_algorithm()
        volume depth tolerance error
        0.0, 0.0, 0.0, 0.0
        0.1, 0.045296, 0.0, 0.0
        1.0, 0.356503, 0.0, -0.000059
        2.0, 0.632918, 0.0, -0.000027
        5.0, 1.312357, 0.0, 0.0
        10.0, 2.170538, 0.0, 0.0
        100.0, 7.624652, 0.0, -0.000004

        In the last example, the default tolerance values result in practically likely
        irrelevant but still recognisable inaccuracies.  The following example shows
        that decreasing the water depth-related tolerance reduces these errors:

        >>> solver.waterdepthtolerance(0.0)
        >>> check_search_algorithm()
        volume depth tolerance error
        0.0, 0.0, 0.0, 0.0
        0.1, 0.045296, 0.0, 0.0
        1.0, 0.356485, 0.0, 0.0
        2.0, 0.632911, 0.0, 0.0
        5.0, 1.312357, 0.0, 0.0
        10.0, 2.170538, 0.0, 0.0
        100.0, 7.624652, 0.0, 0.0
    """

    CONTROLPARAMETERS = (kinw_control.Length, kinw_control.NmbSegments)
    DERIVEDPARAMETERS = (
        kinw_derived.Seconds,
        kinw_derived.NmbDiscontinuities,
        kinw_derived.FinalDepth2InitialVolume,
    )
    SOLVERPARAMETERS = (
        kinw_solver.WaterVolumeTolerance,
        kinw_solver.WaterDepthTolerance,
    )
    REQUIREDSEQUENCES = (kinw_states.WaterVolume,)
    RESULTSEQUENCES = (kinw_factors.WaterDepth,)
    SUBMODELS = (PegasusImplicitEuler,)
    SUBMETHODS = (Return_VolumeError_V1,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        sol = model.parameters.solver.fastaccess
        old = model.sequences.states.fastaccess_old
        fac = model.sequences.factors.fastaccess

        i = model.idx_segment
        d0: float = 0.0
        if der.nmbdiscontinuities == 0:
            d1: float = 10.0
        else:
            for j in range(der.nmbdiscontinuities):
                d1 = der.finaldepth2initialvolume[j, 0]
                if old.watervolume[i] <= der.finaldepth2initialvolume[j, 1]:
                    break
                d0 = d1
            else:
                d1 = d0 + 10.0

        tol: float = old.watervolume[i] * sol.watervolumetolerance

        fac.waterdepth[i] = model.pegasusimpliciteuler.find_x(
            d0, d1, 0.0, 1000.0, sol.waterdepthtolerance, tol, 1000
        )


class Update_WaterVolume_V2(modeltools.Method):
    r"""Calculate the new water volume that agrees with the previously calculated final
    water depth.

    Basic equation:
      .. math::
        V = A \cdot l / n \cdot 10^{-3}
        \\ \\
        V = WaterVolume \\
        A = f_{get\_wettedarea}(D) \\
        l = Length \\
        n = NmbSegments

    Examples:

        Note that, usually, the W-Q submodel must have been processed with the correct
        final water depth beforehand so that it can provide the related wetted area:

        >>> from hydpy.models.kinw_impl_euler import *
        >>> parameterstep()
        >>> length(100.0)
        >>> nmbsegments(1)
        >>> with model.add_wqmodel_v1("wq_trapeze_strickler"):
        ...     nmbtrapezes(1)
        ...     bottomlevels(1.0)
        ...     sideslopes(0.0)
        >>> model.wqmodel.sequences.factors.wettedarea = 2.0
        >>> model.idx_segment = 0
        >>> model.update_watervolume_v2()
        >>> states.watervolume
        watervolume(0.2)

        For zero water depths or channel lengths, |Update_WaterVolume_V2| sets the
        final water volume to zero (independent of the submodel's currentl wetted
        area):

        >>> model.wqmodel.sequences.factors.wettedarea = -999.0
        >>> factors.waterdepth = 0.0
        >>> model.update_watervolume_v2()
        >>> states.watervolume
        watervolume(0.0)
        >>> factors.waterdepth = 1.0
        >>> length(0.0)
        >>> model.update_watervolume_v2()
        >>> states.watervolume
        watervolume(0.0)
    """

    CONTROLPARAMETERS = (kinw_control.Length, kinw_control.NmbSegments)
    REQUIREDSEQUENCES = (kinw_factors.WaterDepth,)
    UPDATEDSEQUENCES = (kinw_states.WaterVolume,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        new = model.sequences.states.fastaccess_new
        fac = model.sequences.factors.fastaccess

        i = model.idx_segment
        if (fac.waterdepth[i] == 0.0) or (con.length == 0.0):
            new.watervolume[i] = 0.0
        else:
            new.watervolume[i] = (
                model.wqmodel.get_wettedarea() * con.length / con.nmbsegments / 1e3
            )


class Pass_Q_V1(modeltools.Method):
    """Pass the outflow to the outlet node.

    Example:

        >>> from hydpy.models.kinw import *
        >>> parameterstep()
        >>> fluxes.qa = 2.0
        >>> model.pass_q_v1()
        >>> outlets.q
        q(2.0)
    """

    REQUIREDSEQUENCES = (kinw_fluxes.QA,)
    RESULTSEQUENCES = (kinw_outlets.Q,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        out = model.sequences.outlets.fastaccess
        out.q = flu.qa


class Return_QF_V1(modeltools.Method):
    """Calculate and return the "error" between the actual discharge and the
    discharge corresponding to the given water stage.

    Basic equation:
      :math:`Q(H) - QG_0`

    Method |Return_QF_V1| is a helper function not intended for performing
    simulation runs but for easing the implementation of method
    |kinw_williams.Model.calculate_characteristiclength| of application model
    |kinw_williams| (and similar functionalities).  More specifically, it
    defines the target function for the iterative root search triggered by
    method |Return_H_V1|.

    While method |Return_QF_V1| performs discharge calculations for all
    stream subsections, it evaluates only those of the first subsection.
    Accordingly, to avoid wasting computation time, one should not initialise
    more than one subsection before calling method |Return_QF_V1| (or methods
    |Return_H_V1| or |kinw_williams.Model.calculate_characteristiclength|).

    Example:

        We reuse the example given in the main documentation on module |kinw_williams|:

        >>> from hydpy.models.kinw import *
        >>> parameterstep("1d")
        >>> simulationstep("30m")

        >>> gts(1)
        >>> laen(100.0)
        >>> gef(0.00025)
        >>> bm(15.0)
        >>> bnm(5.0)
        >>> skm(1.0/0.035)
        >>> hm(6.0)
        >>> bv(100.0)
        >>> bbv(20.0)
        >>> bnv(10.0)
        >>> bnvr(100.0)
        >>> skv(10.0)
        >>> ekm(1.0)
        >>> ekv(1.0)
        >>> hr(0.1)
        >>> parameters.update()

        A water stage of 1 m results in a discharge of 7.7 m³/s:

        >>> states.h = 1.0
        >>> model.calc_rhm_v1()
        >>> model.calc_rhmdh_v1()
        >>> model.calc_rhv_v1()
        >>> model.calc_rhvdh_v1()
        >>> model.calc_rhlvr_rhrvr_v1()
        >>> model.calc_rhlvrdh_rhrvrdh_v1()
        >>> model.calc_am_um_v1()
        >>> model.calc_alv_arv_ulv_urv_v1()
        >>> model.calc_alvr_arvr_ulvr_urvr_v1()
        >>> model.calc_qm_v1()
        >>> model.calc_qlv_qrv_v1()
        >>> model.calc_qlvr_qrvr_v1()
        >>> model.calc_ag_v1()
        >>> model.calc_qg_v1()
        >>> fluxes.qg
        qg(7.745345)

        The calculated |QG| value serves as the "true" value.  Now, when
        passing stage values of 0.5 and 1.0 m, method |Return_QF_V1|
        calculates the corresponding discharge values and returns the
        "errors" -5.5 m³/s (a stage of 0.5 m results in a too-small discharge
        value) and 0.0 m³/s  (1.0 m is the "true" stage), respectively:

        >>> from hydpy import round_
        >>> round_(model.return_qf_v1(0.5))
        -5.474691
        >>> round_(model.return_qf_v1(1.0))
        0.0

        Note that method |Return_QF_V1| does not overwrite the first
        entry of |QG|, which would complicate its application within
        an iterative approach.

    Technical checks:

        Note that method |Return_QF_V1| calculates the value of sequence |QG|
        temporarily and resets it afterwards, and calculates all other values of the
        mentioned sequences without resetting:

        >>> from hydpy.core.testtools import check_selectedvariables
        >>> from hydpy.models.kinw.kinw_model import Return_QF_V1
        >>> print(check_selectedvariables(Return_QF_V1))
        Definitely missing: qg
        Possibly missing (REQUIREDSEQUENCES):
            Calc_RHM_V1: H
            Calc_RHMDH_V1: H
            Calc_RHV_V1: H
            Calc_RHVDH_V1: H
            Calc_RHLVR_RHRVR_V1: H
            Calc_RHLVRDH_RHRVRDH_V1: H
            Calc_AM_UM_V1: RHM and RHV
            Calc_ALV_ARV_ULV_URV_V1: RHV, RHLVR, and RHRVR
            Calc_ALVR_ARVR_ULVR_URVR_V1: RHLVR and RHRVR
            Calc_QM_V1: AM and UM
            Calc_QLV_QRV_V1: ALV, ARV, ULV, and URV
            Calc_QLVR_QRVR_V1: ALVR, ARVR, ULVR, and URVR
            Calc_AG_V1: AM, ALV, ARV, ALVR, and ARVR
            Calc_QG_V1: QM, QLV, QRV, QLVR, and QRVR
        Possibly missing (RESULTSEQUENCES):
            Calc_QG_V1: QG
    """

    SUBMETHODS = (
        Calc_RHM_V1,
        Calc_RHMDH_V1,
        Calc_RHV_V1,
        Calc_RHVDH_V1,
        Calc_RHLVR_RHRVR_V1,
        Calc_RHLVRDH_RHRVRDH_V1,
        Calc_AM_UM_V1,
        Calc_ALV_ARV_ULV_URV_V1,
        Calc_ALVR_ARVR_ULVR_URVR_V1,
        Calc_QM_V1,
        Calc_QLV_QRV_V1,
        Calc_QLVR_QRVR_V1,
        Calc_AG_V1,
        Calc_QG_V1,
    )
    CONTROLPARAMETERS = (
        kinw_control.GTS,
        kinw_control.HM,
        kinw_control.BM,
        kinw_control.BNM,
        kinw_control.BV,
        kinw_control.BNV,
        kinw_control.BNVR,
    )
    DERIVEDPARAMETERS = (
        kinw_derived.HV,
        kinw_derived.HRP,
        kinw_derived.BNMF,
        kinw_derived.BNVF,
        kinw_derived.BNVRF,
        kinw_derived.MFM,
        kinw_derived.MFV,
    )
    RESULTSEQUENCES = (
        kinw_states.H,
        kinw_aides.RHM,
        kinw_aides.RHMDH,
        kinw_aides.RHV,
        kinw_aides.RHVDH,
        kinw_aides.RHLVR,
        kinw_aides.RHRVR,
        kinw_aides.RHLVRDH,
        kinw_aides.RHRVRDH,
        kinw_aides.AM,
        kinw_aides.UM,
        kinw_aides.ALV,
        kinw_aides.ARV,
        kinw_aides.ULV,
        kinw_aides.URV,
        kinw_aides.ALVR,
        kinw_aides.ARVR,
        kinw_aides.ULVR,
        kinw_aides.URVR,
        kinw_aides.QM,
        kinw_aides.QLV,
        kinw_aides.QRV,
        kinw_aides.QLVR,
        kinw_aides.QRVR,
        kinw_aides.AG,
    )

    @staticmethod
    def __call__(model: modeltools.Model, h: float) -> float:
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        d_qg = flu.qg[0]
        sta.h[0] = h
        model.calc_rhm_v1()
        model.calc_rhmdh_v1()
        model.calc_rhv_v1()
        model.calc_rhvdh_v1()
        model.calc_rhlvr_rhrvr_v1()
        model.calc_rhlvrdh_rhrvrdh_v1()
        model.calc_am_um_v1()
        model.calc_alv_arv_ulv_urv_v1()
        model.calc_alvr_arvr_ulvr_urvr_v1()
        model.calc_qm_v1()
        model.calc_qlv_qrv_v1()
        model.calc_qlvr_qrvr_v1()
        model.calc_ag_v1()
        model.calc_qg_v1()
        d_error = flu.qg[0] - d_qg
        flu.qg[0] = d_qg
        return d_error


class Return_H_V1(modeltools.Method):
    """Calculate and return the water stage corresponding to the current
    discharge value.

    Method |Return_H_V1| is a helper function not for performing simulation runs but
    for easing the implementation of method
    |kinw_williams.Model.calculate_characteristiclength| of application model
    |kinw_williams| (or similar functionalities).  It performs a root search by
    applying the |Pegasus| method implemented in module `rootutils` on the target
    method |Return_QF_V1|.  Hence, please see the additional application notes in the
    documentation on method |Return_QF_V1|.

    Example:

        We recreate the exact parameterisation as in the example of the
        documentation on method |Return_QF_V1|:

        >>> from hydpy.models.kinw import *
        >>> simulationstep("30m")
        >>> parameterstep()

        >>> gts(1)
        >>> laen(100.0)
        >>> gef(0.00025)
        >>> bm(15.0)
        >>> bnm(5.0)
        >>> skm(1.0/0.035)
        >>> hm(6.0)
        >>> bv(100.0)
        >>> bbv(20.0)
        >>> bnv(10.0)
        >>> bnvr(100.0)
        >>> skv(10.0)
        >>> ekm(1.0)
        >>> ekv(1.0)
        >>> hr(0.1)
        >>> parameters.update()

        For a given discharge value of 7.7 m³/s (discussed in the documentation
        on method |Return_QF_V1|), method |Return_H_V1| correctly determines
        the water stage of 1 m:

        >>> fluxes.qg = 7.745345
        >>> from hydpy import print_vector, round_
        >>> round_(model.return_h_v1())
        1.0

        To evaluate our implementation's reliability, we search for water stages
        covering an extensive range of discharge values.  The last printed column
        shows that method |Return_H_V1| finds the correct water stage in all cases:

        >>> import numpy
        >>> for q in [0.0]+list(numpy.logspace(-6, 6, 13)):
        ...     fluxes.qg = q
        ...     h = model.return_h_v1()
        ...     states.h = h
        ...     model.calc_rhm_v1()
        ...     model.calc_rhmdh_v1()
        ...     model.calc_rhv_v1()
        ...     model.calc_rhvdh_v1()
        ...     model.calc_rhlvr_rhrvr_v1()
        ...     model.calc_rhlvrdh_rhrvrdh_v1()
        ...     model.calc_am_um_v1()
        ...     model.calc_alv_arv_ulv_urv_v1()
        ...     model.calc_alvr_arvr_ulvr_urvr_v1()
        ...     model.calc_qm_v1()
        ...     model.calc_qlv_qrv_v1()
        ...     model.calc_qlvr_qrvr_v1()
        ...     model.calc_ag_v1()
        ...     model.calc_qg_v1()
        ...     error = fluxes.qg[0]-q
        ...     print_vector([q, h, error])
        0.0, -10.0, 0.0
        0.000001, -0.390737, 0.0
        0.00001, -0.308934, 0.0
        0.0001, -0.226779, 0.0
        0.001, -0.143209, 0.0
        0.01, -0.053833, 0.0
        0.1, 0.061356, 0.0
        1.0, 0.310079, 0.0
        10.0, 1.150307, 0.0
        100.0, 3.717833, 0.0
        1000.0, 9.108276, 0.0
        10000.0, 18.246131, 0.0
        100000.0, 37.330632, 0.0
        1000000.0, 81.363979, 0.0

        Due to smoothing the water stage with respect to the channel bottom, small
        discharge values result in negative water stages.  The lowest allowed stage
        is -10 m.

        Through setting the regularisation parameter |HR| to zero (which we do not
        recommend), method |Return_H_V1| should return the non-negative water stages
        agreeing with the original, discontinuous Manning-Strickler equation:

        >>> hr(0.0)
        >>> parameters.update()
        >>> for q in [0.0]+list(numpy.logspace(-6, 6, 13)):
        ...     fluxes.qg = q
        ...     h = model.return_h_v1()
        ...     states.h = h
        ...     model.calc_rhm_v1()
        ...     model.calc_rhmdh_v1()
        ...     model.calc_rhv_v1()
        ...     model.calc_rhvdh_v1()
        ...     model.calc_rhlvr_rhrvr_v1()
        ...     model.calc_rhlvrdh_rhrvrdh_v1()
        ...     model.calc_am_um_v1()
        ...     model.calc_alv_arv_ulv_urv_v1()
        ...     model.calc_alvr_arvr_ulvr_urvr_v1()
        ...     model.calc_qm_v1()
        ...     model.calc_qlv_qrv_v1()
        ...     model.calc_qlvr_qrvr_v1()
        ...     model.calc_ag_v1()
        ...     model.calc_qg_v1()
        ...     error = fluxes.qg[0]-q
        ...     print_vector([q, h, error])
        0.0, 0.0, 0.0
        0.000001, 0.00008, 0.0
        0.00001, 0.000317, 0.0
        0.0001, 0.001263, 0.0
        0.001, 0.005027, 0.0
        0.01, 0.019992, 0.0
        0.1, 0.079286, 0.0
        1.0, 0.31039, 0.0
        10.0, 1.150307, 0.0
        100.0, 3.717833, 0.0
        1000.0, 9.108276, 0.0
        10000.0, 18.246131, 0.0
        100000.0, 37.330632, 0.0
        1000000.0, 81.363979, 0.0
    """

    SUBMETHODS = (Return_QF_V1,)
    CONTROLPARAMETERS = (
        kinw_control.GTS,
        kinw_control.HM,
        kinw_control.BM,
        kinw_control.BNM,
        kinw_control.BV,
        kinw_control.BNV,
        kinw_control.BNVR,
    )
    DERIVEDPARAMETERS = (
        kinw_derived.HV,
        kinw_derived.HRP,
        kinw_derived.BNMF,
        kinw_derived.BNVF,
        kinw_derived.BNVRF,
        kinw_derived.MFM,
        kinw_derived.MFV,
    )
    RESULTSEQUENCES = (
        kinw_states.H,
        kinw_aides.RHM,
        kinw_aides.RHMDH,
        kinw_aides.RHV,
        kinw_aides.RHVDH,
        kinw_aides.RHLVR,
        kinw_aides.RHRVR,
        kinw_aides.RHLVRDH,
        kinw_aides.RHRVRDH,
        kinw_aides.AM,
        kinw_aides.UM,
        kinw_aides.ALV,
        kinw_aides.ARV,
        kinw_aides.ULV,
        kinw_aides.URV,
        kinw_aides.ALVR,
        kinw_aides.ARVR,
        kinw_aides.ULVR,
        kinw_aides.URVR,
        kinw_aides.QM,
        kinw_aides.QLV,
        kinw_aides.QRV,
        kinw_aides.QLVR,
        kinw_aides.QRVR,
        kinw_aides.AG,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> float:
        con = model.parameters.control.fastaccess
        return model.pegasush.find_x(0.0, 2.0 * con.hm, -10.0, 1000.0, 0.0, 1e-10, 1000)


class PegasusH(roottools.Pegasus):
    """Pegasus iterator for finding the correct water stage."""

    METHODS = (Return_QF_V1,)


class Model(modeltools.ELSModel):
    """|kinw.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(short="KinW")
    __HYDPY_ROOTMODEL__ = None

    SOLVERPARAMETERS = (
        kinw_solver.AbsErrorMax,
        kinw_solver.RelErrorMax,
        kinw_solver.RelDTMin,
        kinw_solver.RelDTMax,
        kinw_solver.WaterVolumeTolerance,
        kinw_solver.WaterDepthTolerance,
    )
    SOLVERSEQUENCES = ()
    INLET_METHODS = (Pick_Q_V1, Pick_Inflow_V1)
    OBSERVER_METHODS = ()
    RECEIVER_METHODS = ()
    ADD_METHODS = (
        Return_QF_V1,
        Return_H_V1,
        Update_WaterVolume_V1,
        Return_InitialWaterVolume_V1,
        Return_VolumeError_V1,
        Calc_WaterDepth_V1,
        Update_WaterVolume_V2,
        Calc_InternalFlow_Outflow_V1,
    )
    PART_ODE_METHODS = (
        Calc_RHM_V1,
        Calc_RHMDH_V1,
        Calc_RHV_V1,
        Calc_RHVDH_V1,
        Calc_RHLVR_RHRVR_V1,
        Calc_RHLVRDH_RHRVRDH_V1,
        Calc_AM_UM_V1,
        Calc_AMDH_UMDH_V1,
        Calc_ALV_ARV_ULV_URV_V1,
        Calc_ALVDH_ARVDH_ULVDH_URVDH_V1,
        Calc_ALVR_ARVR_ULVR_URVR_V1,
        Calc_ALVRDH_ARVRDH_ULVRDH_URVRDH_V1,
        Calc_QM_V1,
        Calc_QMDH_V1,
        Calc_QM_V2,
        Calc_QLV_QRV_V1,
        Calc_QLVDH_QRVDH_V1,
        Calc_QLV_QRV_V2,
        Calc_QLVR_QRVR_V1,
        Calc_QLVRDH_QRVRDH_V1,
        Calc_QLVR_QRVR_V2,
        Calc_AG_V1,
        Calc_QG_V1,
        Calc_QG_V2,
        Calc_QA_V1,
        Calc_WBM_V1,
        Calc_WBLV_WBRV_V1,
        Calc_WBLVR_WBRVR_V1,
        Calc_WBG_V1,
        Calc_DH_V1,
    )
    FULL_ODE_METHODS = (Update_H_V1, Update_VG_V1)
    OUTLET_METHODS = (Pass_Q_V1,)
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = (PegasusH, PegasusImplicitEuler)


class BaseModelProfile(modeltools.ELSModel):
    """Base class for |kinw.DOCNAME.long| models performing discharge calculations
    based on a triple trapezoid profile."""

    def plot_profile(self, labelformat: str = "%.1f"):
        """Plot the triple trapezoid profile and insert the discharge values at some
        distinct stages.

        We reuse the second example given in the main documentation on module
        |kinw_williams|:

        >>> from hydpy.models.kinw_williams import *
        >>> parameterstep("1d")
        >>> simulationstep("30m")
        >>> laen(100.0)
        >>> gef(0.00025)
        >>> bm(15.0)
        >>> bnm(5.0)
        >>> skm(1.0/0.035)
        >>> hm(6.0)
        >>> bv(100.0)
        >>> bbv(20.0)
        >>> bnv(10.0)
        >>> bnvr(100.0)
        >>> skv(10.0)
        >>> ekm(1.0)
        >>> ekv(1.0)
        >>> hr(0.1)
        >>> gts(1)
        >>> parameters.update()

        Calling method |BaseModelProfile.plot_profile| prepares the profile plot and,
        depending on your `matplotlib` configuration, eventually prints it directly on
        your screen:

        >>> model.plot_profile()
        >>> from hydpy.core.testtools import save_autofig
        >>> save_autofig("kinw_plot_profile.png")

        .. image:: kinw_plot_profile.png
        """

        class _XYs:
            def __init__(self):
                self._xs = [0.0]
                self._ys = [0.0]

            def __iadd__(self, dxdy):
                self._xs.append(self._xs[-1] + dxdy[0])
                self._ys.append(self._ys[-1] + dxdy[1])
                return self

            def __isub__(self, dxdy):
                self._xs.insert(0, self._xs[0] - dxdy[0])
                self._ys.insert(0, self._ys[0] + dxdy[1])
                return self

            def __call__(self) -> tuple[list[float], list[float]]:
                return self._xs, self._ys

        con = self.parameters.control
        der = self.parameters.derived
        hmax = 1.3 * (con.hm + max(der.hv.value))

        xys = _XYs()
        xys += con.bm / 2.0, 0.0
        xys -= con.bm / 2.0, 0.0
        xys += con.hm * con.bnm, con.hm
        xys -= con.hm * con.bnm, con.hm
        xys += con.bv[1], 0.0
        xys -= con.bv[0], 0.0
        xys += der.hv[1] * con.bnv[1], der.hv[1]
        xys -= der.hv[0] * con.bnv[0], der.hv[0]
        dh = hmax - der.hv[1] - con.hm
        xys += dh * con.bnvr[1], dh
        dh = hmax - der.hv[0] - con.hm
        xys -= dh * con.bnvr[0], dh
        xs, ys = xys()
        pyplot.plot(xs, ys, color="r")

        x0, x1 = min(xs), max(xs)
        y0, y1 = min(ys), max(ys)
        dy = (y1 - y0) / 80.0
        hs = [
            0.0,
            con.hm / 2.0,
            con.hm,
            con.hm + der.hv[0] / 2.0,
            con.hm + der.hv[0],
            con.hm + der.hv[1] / 2.0,
            con.hm + der.hv[1],
            (con.hm + der.hv[0] + hmax) / 2.0,
            (con.hm + der.hv[1] + hmax) / 2.0,
            hmax,
        ]
        temp = []
        for h in hs:
            if h not in temp:
                temp.append(h)
        hs = sorted(temp)
        qs = self.calculate_qgvector(hs)
        for idx, (h, q) in enumerate(zip(hs, qs)):
            pyplot.plot([x0, x1], [h, h], "b:")
            text = f"{labelformat % q} m³/s"
            if idx % 2:
                pyplot.text(x0, h + dy, text, horizontalalignment="left")
            else:
                pyplot.text(x1, h + dy, text, horizontalalignment="right")

        pyplot.title(f"Profile of model {objecttools.elementphrase(self)}")
        pyplot.ylabel("height above the channel bottom [m]")

    def prepare_hvector(
        self,
        nmb: int = 1000,
        exp: float = 2.0,
        hmin: float | None = None,
        hmax: float | None = None,
    ) -> tuple[float, ...]:
        """Prepare a vector of the stage values.

        The argument `nmb` defines the number of stage values, `exp` defines their
        spacing (1.0 results in equidistant values), and `hmin` and `hmax` the lowest
        and highest water stage, respectively:

        >>> from hydpy.models.kinw_williams import *
        >>> parameterstep()
        >>> from hydpy import print_vector
        >>> print_vector(model.prepare_hvector(
        ...     nmb=10, hmin=-1.0, hmax=8, exp=1.0))
        -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0

        When not specified by the user, method
        |kinw_model.BaseModelProfile.prepare_hvector| determines `hmin` and `hmax`
        based on the current value of |HM| (-10 % and 300 %, respectively) and takes a
        higher sampling rate in the lower value range (by setting `exp` to two):

        >>> hm(6.0)
        >>> print_vector(model.prepare_hvector(nmb=10))
        -0.6, -0.37037, 0.318519, 1.466667, 3.074074, 5.140741, 7.666667,
        10.651852, 14.096296, 18.0
        """
        if hmin is None:
            hmin = -0.1 * self.parameters.control.hm
        if hmax is None:
            hmax = 3.0 * self.parameters.control.hm
        hs = numpy.linspace(0.0, 1.0, nmb) ** exp
        hs /= hs[-1]
        hs *= hmax - hmin
        hs += hmin
        return tuple(hs)

    def calculate_qgvector(self, hvector: Iterable[float]) -> tuple[float, ...]:
        """Calculate the discharge values (in m³/s) corresponding to the
        given stage vector.

        We reuse the second example given in the main documentation on module
        |kinw_williams| also show the results of the similar methods
        |kinw_model.BaseModelProfile.calculate_agvector| and
        |kinw_model.BaseModelProfile.calculate_vgvector|:

        >>> from hydpy.models.kinw_williams import *
        >>> parameterstep("1d")
        >>> simulationstep("30m")
        >>> laen(100.0)
        >>> gef(0.00025)
        >>> bm(15.0)
        >>> bnm(5.0)
        >>> skm(1.0/0.035)
        >>> hm(6.0)
        >>> bv(100.0)
        >>> bbv(20.0)
        >>> bnv(10.0)
        >>> bnvr(100.0)
        >>> skv(10.0)
        >>> ekm(1.0)
        >>> ekv(1.0)
        >>> hr(0.1)
        >>> gts(2)
        >>> parameters.update()

        >>> from hydpy import print_vector
        >>> print_vector(model.calculate_qgvector([0.0, 1.0, 2.0]))
        0.033153, 7.745345, 28.436875
        >>> print_vector(model.calculate_agvector([0.0, 1.0, 2.0]))
        0.623138, 20.0, 50.0
        >>> print_vector(model.calculate_vgvector([0.0, 1.0, 2.0]))
        0.031157, 1.0, 2.5
        """
        h_ = self.sequences.states.h.values.copy()
        qg = []
        try:
            for h in hvector:
                self.sequences.states.h = h
                self.calculate_single_terms()
                qg.append(self.sequences.fluxes.qg[0])
            return tuple(qg)
        finally:
            self.sequences.states.h(h_)

    def calculate_agvector(self, hvector: Iterable[float]) -> tuple[float, ...]:
        """Calculate the wetted cross-section areas (in m²) corresponding to the given
        vector of stage values.

        See the documentation on method
        |kinw_model.BaseModelProfile.calculate_qgvector| for an example.
        """
        h_ = self.sequences.states.h.values.copy()
        ag = []
        aid = self.sequences.aides
        try:
            for h in hvector:
                self.sequences.states.h = h
                self.calculate_single_terms()
                ag.append(
                    aid.am[0] + aid.alv[0] + aid.arv[0] + aid.alvr[0] + aid.arvr[0]
                )
            return tuple(ag)
        finally:
            self.sequences.states.h(h_)

    def calculate_vgvector(self, hvector: Iterable[float]) -> tuple[float, ...]:
        """Calculate the water volume stored within a channel subsection (in Mio m³)
        corresponding to the given vector of stage values.

        See the documentation on method
        |kinw_model.BaseModelProfile.calculate_qgvector| for an example.
        """
        con = self.parameters.control
        ags = numpy.array(self.calculate_agvector(hvector))
        return tuple(con.laen / con.gts * 1000.0 * ags / 1e6)
