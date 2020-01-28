# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from standard library
import typing
# ...from site-packages
import numpy
from matplotlib import pyplot
# ...from HydPy
from hydpy.core import modeltools
from hydpy.core import objecttools
from hydpy.cythons import smoothutils
from hydpy.models.lstream import lstream_control
from hydpy.models.lstream import lstream_derived
from hydpy.models.lstream import lstream_solver
from hydpy.models.lstream import lstream_fluxes
from hydpy.models.lstream import lstream_states
from hydpy.models.lstream import lstream_aides
from hydpy.models.lstream import lstream_inlets
from hydpy.models.lstream import lstream_outlets


class Pick_Q_V1(modeltools.Method):
    """Query the current inflow from all inlet nodes.

    Basic equation:
      :math:`QZ = \\sum Q`
    """
    REQUIREDSEQUENCES = (
        lstream_inlets.Q,
    )
    RESULTSEQUENCES = (
        lstream_fluxes.QZ,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        inl = model.sequences.inlets.fastaccess
        flu.qz = 0.
        for idx in range(inl.len_q):
            flu.qz += inl.q[idx][0]


class Calc_QZA_V1(modeltools.Method):
    """Calculate the current inflow into the channel.

    Basic equation:
      :math:`QZA = QZ`
    """
    REQUIREDSEQUENCES = (
        lstream_fluxes.QZ,
    )
    RESULTSEQUENCES = (
        lstream_fluxes.QZA,
    )
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

        >>> from hydpy.models.lstream import *
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
    CONTROLPARAMETERS = (
        lstream_control.GTS,
    )
    DERIVEDPARAMETERS = (
        lstream_derived.HRP,
    )
    REQUIREDSEQUENCES = (
        lstream_states.H,
    )
    RESULTSEQUENCES = (
        lstream_aides.RHM,
    )
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

        >>> from hydpy.models.lstream import *
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
    CONTROLPARAMETERS = (
        lstream_control.GTS,
    )
    DERIVEDPARAMETERS = (
        lstream_derived.HRP,
    )
    REQUIREDSEQUENCES = (
        lstream_states.H,
    )
    RESULTSEQUENCES = (
        lstream_aides.RHMDH,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            aid.rhmdh[i] = smoothutils.smooth_logistic2_derivative2(
                sta.h[i], der.hrp)


class Calc_RHV_V1(modeltools.Method):
    """Regularise the stage with respect to the transition from the
    main channel to both forelands.

    Used auxiliary method:
      |smooth_logistic2|

    Basic equation:
      :math:`RHV = smooth_{logistic2}(H-HM, HRP)`

    Examples:

        >>> from hydpy.models.lstream import *
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
    CONTROLPARAMETERS = (
        lstream_control.GTS,
        lstream_control.HM,
    )
    DERIVEDPARAMETERS = (
        lstream_derived.HRP,
    )
    REQUIREDSEQUENCES = (
        lstream_states.H,
    )
    RESULTSEQUENCES = (
        lstream_aides.RHV,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            aid.rhv[i] = smoothutils.smooth_logistic2(sta.h[i]-con.hm, der.hrp)


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

        >>> from hydpy.models.lstream import *
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
    CONTROLPARAMETERS = (
        lstream_control.GTS,
        lstream_control.HM,
    )
    DERIVEDPARAMETERS = (
        lstream_derived.HRP,
    )
    REQUIREDSEQUENCES = (
        lstream_states.H,
    )
    RESULTSEQUENCES = (
        lstream_aides.RHVDH,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            aid.rhvdh[i] = smoothutils.smooth_logistic2_derivative2(
                sta.h[i]-con.hm, der.hrp)


class Calc_RHLVR_RHRVR_V1(modeltools.Method):
    """Regularise the stage with respect to the transitions from the
    forelands to the outer embankments.

    Used auxiliary method:
      |smooth_logistic2|

    Basic equation:
      :math:`RHVR = smooth_{logistic2}(H-HM-HV, HRP)`

    Examples:

        >>> from hydpy.models.lstream import *
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
    CONTROLPARAMETERS = (
        lstream_control.GTS,
        lstream_control.HM,
    )
    DERIVEDPARAMETERS = (
        lstream_derived.HV,
        lstream_derived.HRP,
    )
    REQUIREDSEQUENCES = (
        lstream_states.H,
    )
    RESULTSEQUENCES = (
        lstream_aides.RHLVR,
        lstream_aides.RHRVR,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            aid.rhlvr[i] = smoothutils.smooth_logistic2(
                sta.h[i]-con.hm-der.hv[0], der.hrp)
            aid.rhrvr[i] = smoothutils.smooth_logistic2(
                sta.h[i]-con.hm-der.hv[1], der.hrp)


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

        >>> from hydpy.models.lstream import *
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
    CONTROLPARAMETERS = (
        lstream_control.GTS,
        lstream_control.HM,
    )
    DERIVEDPARAMETERS = (
        lstream_derived.HRP,
        lstream_derived.HV,
    )
    REQUIREDSEQUENCES = (
        lstream_states.H,
    )
    RESULTSEQUENCES = (
        lstream_aides.RHLVRDH,
        lstream_aides.RHRVRDH,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        sta = model.sequences.states.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            aid.rhlvrdh[i] = smoothutils.smooth_logistic2_derivative2(
                sta.h[i]-con.hm-der.hv[0], der.hrp)
            aid.rhrvrdh[i] = smoothutils.smooth_logistic2_derivative2(
                sta.h[i]-con.hm-der.hv[1], der.hrp)


class Calc_AM_UM_V1(modeltools.Method):
    """Calculate the wetted area and the wetted perimeter of the main channel.

    The main channel is assumed to have identical slopes on both sides.
    Water flowing exactly above the main channel is contributing to |AM|.
    Both theoretical surfaces separating the water above the main channel
    from the water above the forelands are contributing to |UM|.

    Examples:

        Generally, a trapezoid with reflection symmetry is assumed.  Here,
        we set its smaller base (bottom) to a length of 2 meters, its legs
        to an inclination of 1 meter per 4 meters, and its height (depths)
        to 1 meter:

        >>> from hydpy.models.lstream import *
        >>> parameterstep()
        >>> gts(8)
        >>> bm(2.0)
        >>> bnm(4.0)
        >>> derived.bnmf.update()

        First, we show that all calculations agree with the unmodified
        triple trapezoid profile results when setting the smoothing
        parameter |HRP| to zero:

        >>> derived.hrp(0)

        This example deals with normal flow conditions, where water flows
        within the main channel completely (|H| < |HM|, the first five
        channel sections), and with high flow conditions, where water
        flows over the foreland also (|H| > |HM|, the three last channel
        sections):

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

        Second, we repeat both examples with a reasonable smoothing
        parameterisation.  As to be expected, the primary deviations occur
        around the original discontinuities related the channel bottom
        and the transition from the main channel to both forelands:

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
    CONTROLPARAMETERS = (
        lstream_control.GTS,
        lstream_control.BM,
        lstream_control.BNM,
    )
    DERIVEDPARAMETERS = (
        lstream_derived.BNMF,
    )
    REQUIREDSEQUENCES = (
        lstream_aides.RHM,
        lstream_aides.RHV,
    )
    RESULTSEQUENCES = (
        lstream_aides.AM,
        lstream_aides.UM,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            d_temp = aid.rhm[i]-aid.rhv[i]
            aid.am[i] = (
                d_temp*(con.bm+d_temp*con.bnm) +
                aid.rhv[i]*(con.bm+2.*d_temp*con.bnm)
            )
            aid.um[i] = con.bm+2.*d_temp*der.bnmf+2.*aid.rhv[i]


class Calc_AMDH_UMDH_V1(modeltools.Method):
    """Calculate the derivatives of the wetted area and  perimeter of
    the main channel.

    Examples:

        In the following, we repeat the examples of the documentation on
        method |Calc_AM_UM_V1| and check the correctness of the derivatives
        by comparing the results of class |NumericalDifferentiator|:

        >>> from hydpy.models.lstream import *
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
    CONTROLPARAMETERS = (
        lstream_control.GTS,
        lstream_control.BM,
        lstream_control.BNM,
    )
    DERIVEDPARAMETERS = (
        lstream_derived.BNVF,
    )
    REQUIREDSEQUENCES = (
        lstream_aides.RHM,
        lstream_aides.RHMDH,
        lstream_aides.RHV,
        lstream_aides.RHVDH,
    )
    RESULTSEQUENCES = (
        lstream_aides.AMDH,
        lstream_aides.UMDH,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            d_temp1 = aid.rhm[i]-aid.rhv[i]
            d_temp2 = aid.rhmdh[i]-aid.rhvdh[i]
            aid.amdh[i] = (
                con.bnm*d_temp1*d_temp2 +
                2.*con.bnm*d_temp2*aid.rhv[i] +
                (con.bm+con.bnm*d_temp1)*d_temp2 +
                (con.bm+2.*con.bnm*d_temp1)*aid.rhvdh[i]
            )
            aid.umdh[i] = 2.*d_temp2*der.bnmf + 2.*aid.rhvdh[i]


class Calc_ALV_ARV_ULV_URV_V1(modeltools.Method):
    """Calculate the wetted area and wetted perimeter of both forelands.

    Each foreland lies between the main channel and one outer embankment.
    The water flowing exactly above a foreland is contributing to |ALV|
    or |ARV|.  The theoretical surface separating the water above the main
    channel from the water above the foreland is not contributing to |ULV|
    or |URV|, but the surface separating the water above the foreland from
    the water above its outer embankment is contributing to |ULV| and |URV|.

    Examples:

        >>> from hydpy.models.lstream import *
        >>> parameterstep()
        >>> gts(14)
        >>> hm(1.0)

        First, we show that all calculations agree with the unmodified
        triple trapezoid profile results when setting the smoothing
        parameter |HRP| to zero:

        >>> derived.hrp(0)

        This example deals with normal flow conditions, where water flows
        within the main channel completely (|H| < |HM|, the first four channel
        sections); with moderate high flow conditions, where water flows over
        both forelands, but not over their embankments (|HM| < |H| < (|HM| +
        |HV|), channel sections six to eight or twelve for the left and the
        right foreland, respectively), and with extreme high flow conditions,
        where water flows over both forelands and their outer embankments
        ((|HM| + |HV|) < |H|, the last six or two channel sections for the
        left and the right foreland, respectively):

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
        arv(0.0, 0.0, 0.0, 0.0, 0.2, 1.0, 1.8, 2.0, 2.2, 3.0, 3.8, 4.0, 4.2, \
6.0)
        >>> aides.ulv
        ulv(0.0, 0.0, 0.0, 0.0, 0.412311, 2.061553, 3.710795, 4.123106,
            4.223106, 4.623106, 5.023106, 5.123106, 5.223106, 6.123106)
        >>> aides.urv
        urv(2.0, 2.0, 2.0, 2.0, 2.1, 2.5, 2.9, 3.0, 3.1, 3.5, 3.9, 4.0, 4.1, \
5.0)

        Second, we repeat both examples with a reasonable smoothing
        parameterisation.  As to be expected, the primary deviations occur
        around the original discontinuities related the channel bottom
        and the transition from the main channel to both forelands:

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
            5.995113, 6.191875, 6.623066, 7.023106, 7.123106, 7.223106, \
8.123106)
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
    CONTROLPARAMETERS = (
        lstream_control.BV,
        lstream_control.BNV,
    )
    DERIVEDPARAMETERS = (
        lstream_derived.BNVF,
    )
    REQUIREDSEQUENCES = (
        lstream_aides.RHV,
        lstream_aides.RHLVR,
        lstream_aides.RHRVR,
    )
    RESULTSEQUENCES = (
        lstream_aides.ALV,
        lstream_aides.ARV,
        lstream_aides.ULV,
        lstream_aides.URV,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            d_temp = aid.rhv[i] - aid.rhlvr[i]
            aid.alv[i] = (
                d_temp*(con.bv[0]+(d_temp*con.bnv[0]/2.)) +
                aid.rhlvr[i]*(con.bv[0]+d_temp*con.bnv[0]))
            aid.ulv[i] = con.bv[0]+d_temp*der.bnvf[0]+aid.rhlvr[i]
            d_temp = aid.rhv[i] - aid.rhrvr[i]
            aid.arv[i] = (
                d_temp*(con.bv[1]+(d_temp*con.bnv[1]/2.)) +
                aid.rhrvr[i]*(con.bv[1]+d_temp*con.bnv[1]))
            aid.urv[i] = con.bv[1]+d_temp*der.bnvf[1]+aid.rhrvr[i]


class Calc_ALVDH_ARVDH_ULVDH_URVDH_V1(modeltools.Method):
    """Calculate the derivatives of the wetted area and perimeter of
    both forelands.

    Examples:

        In the following, we repeat the examples of the documentation on
        method |Calc_ALV_ARV_ULV_URV_V1| and check the correctness of the
        derivatives by comparing the results of class |NumericalDifferentiator|:

        >>> from hydpy.models.lstream import *
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
    CONTROLPARAMETERS = (
        lstream_control.BV,
        lstream_control.BNV,
    )
    DERIVEDPARAMETERS = (
        lstream_derived.BNVF,
    )
    REQUIREDSEQUENCES = (
        lstream_aides.RHV,
        lstream_aides.RHVDH,
        lstream_aides.RHLVR,
        lstream_aides.RHLVRDH,
        lstream_aides.RHRVR,
        lstream_aides.RHRVRDH,
    )
    RESULTSEQUENCES = (
        lstream_aides.ALVDH,
        lstream_aides.ARVDH,
        lstream_aides.ULVDH,
        lstream_aides.URVDH,
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
                con.bnv[0]*d_temp1*d_temp2/2. +
                con.bnv[0]*d_temp2*aid.rhlvr[i] +
                (con.bnv[0]*d_temp1/2+con.bv[0])*d_temp2 +
                (con.bnv[0]*d_temp1+con.bv[0])*aid.rhlvrdh[i])
            aid.ulvdh[i] = d_temp2*der.bnvf[0]+aid.rhlvrdh[i]
            d_temp1 = aid.rhv[i] - aid.rhrvr[i]
            d_temp2 = aid.rhvdh[i] - aid.rhrvrdh[i]
            aid.arvdh[i] = (
                con.bnv[1]*d_temp1*d_temp2/2. +
                con.bnv[1]*d_temp2*aid.rhrvr[i] +
                (con.bnv[1]*d_temp1/2+con.bv[1])*d_temp2 +
                (con.bnv[1]*d_temp1+con.bv[1])*aid.rhrvrdh[i])
            aid.urvdh[i] = d_temp2*der.bnvf[1]+aid.rhrvrdh[i]


class Calc_ALVR_ARVR_ULVR_URVR_V1(modeltools.Method):
    """Calculate the wetted area and perimeter of both outer embankments.

    Each outer embankment lies beyond its foreland.  The water flowing
    exactly above an embankment is added to |ALVR| and |ARVR|.  The
    theoretical surface separating water above the foreland from the
    water above its embankment is not contributing to |ULVR| and |URVR|.

    Examples:

        >>> from hydpy.models.lstream import *
        >>> parameterstep()
        >>> gts(11)
        >>> hm(1.0)

        First, we show that all calculations agree with the unmodified
        triple trapezoid profile results when the setting the smoothing
        parameter |HRP| to zero:

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

        Second, we repeat both examples with a reasonable smoothing
        parameterisation.  As to be expected, the primary deviations occur
        around the original discontinuities related the channel bottom
        and the transition from the main channel to both forelands:

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
    CONTROLPARAMETERS = (
        lstream_control.GTS,
        lstream_control.HM,
        lstream_control.BNVR,
    )
    DERIVEDPARAMETERS = (
        lstream_derived.HV,
        lstream_derived.BNVRF,
    )
    REQUIREDSEQUENCES = (
        lstream_aides.RHLVR,
        lstream_aides.RHRVR,
    )
    RESULTSEQUENCES = (
        lstream_aides.ALVR,
        lstream_aides.ARVR,
        lstream_aides.ULVR,
        lstream_aides.URVR,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            aid.alvr[i] = aid.rhlvr[i]**2*con.bnvr[0]/2.
            aid.ulvr[i] = aid.rhlvr[i]*der.bnvrf[0]
            aid.arvr[i] = aid.rhrvr[i]**2*con.bnvr[1]/2.
            aid.urvr[i] = aid.rhrvr[i]*der.bnvrf[1]


class Calc_ALVRDH_ARVRDH_ULVRDH_URVRDH_V1(modeltools.Method):
    """Calculate the derivatives of the wetted area and perimeter of
    both outer embankments.

    Examples:

        In the following, we repeat the examples of the documentation on
        method |Calc_ALVR_ARVR_ULVR_URVR_V1| and check the correctness of the
        derivatives by comparing the results of class |NumericalDifferentiator|:

        >>> from hydpy.models.lstream import *
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
    CONTROLPARAMETERS = (
        lstream_control.GTS,
        lstream_control.BNVR,
    )
    DERIVEDPARAMETERS = (
        lstream_derived.BNVRF,
    )
    REQUIREDSEQUENCES = (
        lstream_aides.RHLVR,
        lstream_aides.RHLVRDH,
        lstream_aides.RHRVR,
        lstream_aides.RHRVRDH,
    )
    RESULTSEQUENCES = (
        lstream_aides.ALVRDH,
        lstream_aides.ARVRDH,
        lstream_aides.ULVRDH,
        lstream_aides.URVRDH,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            aid.alvrdh[i] = con.bnvr[0]*aid.rhlvr[i]*aid.rhlvrdh[i]
            aid.ulvrdh[i] = aid.rhlvrdh[i]*der.bnvrf[0]
            aid.arvrdh[i] = con.bnvr[1]*aid.rhrvr[i]*aid.rhrvrdh[i]
            aid.urvrdh[i] = aid.rhrvrdh[i]*der.bnvrf[1]


class Calc_QM_V1(modeltools.Method):
    """Calculate the discharge of the main channel after Manning-Strickler.

    Basic equation:
      :math:`QM = MFM \\cdot \\frac{AM^{5/3}}{UM^{2/3}}`

    Examples:

        Note the handling of zero values for |UM| (in the third subsection):

        >>> from hydpy.models.lstream import *
        >>> parameterstep()
        >>> gts(3)
        >>> derived.mfm(10.0)
        >>> aides.am = 3.0, 0.0, 3.0
        >>> aides.um = 7.0, 7.0, 0.0
        >>> model.calc_qm_v1()
        >>> aides.qm
        qm(17.053102, 0.0, 0.0)
    """
    CONTROLPARAMETERS = (
        lstream_control.GTS,
    )
    DERIVEDPARAMETERS = (
        lstream_derived.MFM,
    )
    REQUIREDSEQUENCES = (
        lstream_aides.AM,
        lstream_aides.UM,
    )
    RESULTSEQUENCES = (
        lstream_aides.QM,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            if aid.um[i] > 0.:
                aid.qm[i] = der.mfm*aid.am[i]**(5./3.)/aid.um[i]**(2./3.)
            else:
                aid.qm[i] = 0.


class Calc_QM_V2(modeltools.Method):
    """Calculate the discharge of the main channel following the kinematic
    wave approach.

    Basic equation:
      :math:`QM = \\frac{QMDH}{AMDH} \\cdot AM`

    Examples:

        Note the handling of zero values for |AMDH| (in the second subsection):

        >>> from hydpy.models.lstream import *
        >>> parameterstep()
        >>> gts(2)
        >>> aides.am = 4.0, 4.0
        >>> aides.qmdh = 3.0, 3.0
        >>> aides.amdh = 2.0, 0.0
        >>> model.calc_qm_v2()
        >>> aides.qm
        qm(6.0, 0.0)
    """
    CONTROLPARAMETERS = (
        lstream_control.GTS,
    )
    REQUIREDSEQUENCES = (
        lstream_aides.AM,
        lstream_aides.QMDH,
        lstream_aides.AMDH,
    )
    RESULTSEQUENCES = (
        lstream_aides.QM,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            if aid.amdh[i] > 0.:
                aid.qm[i] = aid.qmdh[i]/aid.amdh[i]*aid.am[i]
            else:
                aid.qm[i] = 0.


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

        >>> from hydpy.models.lstream import *
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

        >>> from hydpy import NumericalDifferentiator
        >>> NumericalDifferentiator(
        ...     xsequence=states.h,
        ...     ysequences=[aides.qm],
        ...     methods=[model.calc_rhm_v1,
        ...              model.calc_rhv_v1,
        ...              model.calc_am_um_v1,
        ...              model.calc_qm_v1],
        ...     dx=1e-8)()
        d_qm/d_h: 0.000024, 94.123561

        Second, we show that zero values for |AM| or |UM| result in zero
        values for |QMDH|:

        >>> aides.am = 1.0, 0.0
        >>> aides.um = 0.0, 1.0
        >>> model.calc_qmdh_v1()
        >>> aides.qmdh
        qmdh(0.0, 0.0)
    """
    CONTROLPARAMETERS = (
        lstream_control.GTS,
    )
    DERIVEDPARAMETERS = (
        lstream_derived.MFM,
    )
    REQUIREDSEQUENCES = (
        lstream_aides.AM,
        lstream_aides.AMDH,
        lstream_aides.UM,
        lstream_aides.UMDH,
    )
    RESULTSEQUENCES = (
        lstream_aides.QMDH,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            if (aid.am[i] > 0.) and (aid.um[i] > 0.):
                aid.qmdh[i] = der.mfm * (
                    5.*aid.am[i]**(2./3.)*aid.amdh[i]/(3.*aid.um[i]**(2./3.)) -
                    2.*aid.am[i]**(5./3.)*aid.umdh[i]/(3.*aid.um[i]**(5./3.)))
            else:
                aid.qmdh[i] = 0.


class Calc_QLV_QRV_V1(modeltools.Method):
    """Calculate the discharge of both forelands after Manning-Strickler.

    Basic equation:
      :math:`QV = MFV \\cdot \\frac{AV^{5/3}}{UV^{2/3}}`

    Examples:

        Note the handling of zero values for |ULV| and |URV| (in the second
        subsection):

        >>> from hydpy.models.lstream import *
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
    CONTROLPARAMETERS = (
        lstream_control.GTS,
    )
    DERIVEDPARAMETERS = (
        lstream_derived.MFV,
    )
    REQUIREDSEQUENCES = (
        lstream_aides.ALV,
        lstream_aides.ARV,
        lstream_aides.ULV,
        lstream_aides.URV,
    )
    RESULTSEQUENCES = (
        lstream_aides.QLV,
        lstream_aides.QRV,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            if aid.ulv[i] > 0.:
                aid.qlv[i] = der.mfv[0]*aid.alv[i]**(5./3.)/aid.ulv[i]**(2./3.)
            else:
                aid.qlv[i] = 0.
            if aid.urv[i] > 0:
                aid.qrv[i] = der.mfv[1]*aid.arv[i]**(5./3.)/aid.urv[i]**(2./3.)
            else:
                aid.qrv[i] = 0.


class Calc_QLV_QRV_V2(modeltools.Method):
    """Calculate the discharge of both forelands following the kinematic
    wave approach.

    Basic equation:
      :math:`QV = \\frac{QVDH}{AVDH} \\cdot AV`

    Examples:

        Note the handling of zero values for |ALVDH| and |ARVDH| (in the
        second subsection):

        >>> from hydpy.models.lstream import *
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
    CONTROLPARAMETERS = (
        lstream_control.GTS,
    )
    REQUIREDSEQUENCES = (
        lstream_aides.ALV,
        lstream_aides.ARV,
        lstream_aides.ALVDH,
        lstream_aides.ARVDH,
        lstream_aides.QLVDH,
        lstream_aides.QRVDH,
    )
    RESULTSEQUENCES = (
        lstream_aides.QLV,
        lstream_aides.QRV,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            if aid.alvdh[i] > 0.:
                aid.qlv[i] = aid.qlvdh[i]/aid.alvdh[i]*aid.alv[i]
            else:
                aid.qlv[i] = 0.
            if aid.arvdh[i] > 0.:
                aid.qrv[i] = aid.qrvdh[i]/aid.arvdh[i]*aid.arv[i]
            else:
                aid.qrv[i] = 0.


class Calc_QLVDH_QRVDH_V1(modeltools.Method):
    """Calculate the derivative of the discharge of both forelands with
    respect to the stage following method |Calc_QLV_QRV_V1|.

    Basic equation:
      :math:`QVDH = MFV \\cdot
      \\frac{5 \\cdot  AV^{2/3} \\cdot AVDH}{3 \\cdot UV^{2/3}} -
      \\frac{2 \\cdot  AV^{5/3} \\cdot UVDH}{3 \\cdot UV^{5/3}}`

    Examples:

        First, we apply the class |NumericalDifferentiator| to validate the
        calculated derivatives:

        >>> from hydpy.models.lstream import *
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
    CONTROLPARAMETERS = (
        lstream_control.GTS,
    )
    DERIVEDPARAMETERS = (
        lstream_derived.MFV,
    )
    REQUIREDSEQUENCES = (
        lstream_aides.ALV,
        lstream_aides.ALVDH,
        lstream_aides.ARV,
        lstream_aides.ARVDH,
        lstream_aides.ULV,
        lstream_aides.ULVDH,
        lstream_aides.URV,
        lstream_aides.URVDH,
    )
    RESULTSEQUENCES = (
        lstream_aides.QLVDH,
        lstream_aides.QRVDH,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            if (aid.alv[i] > 0.) and (aid.ulv[i] > 0.):
                aid.qlvdh[i] = der.mfv[0] * (
                    5.*aid.alv[i]**(2./3.)*aid.alvdh[i]/(
                        3.*aid.ulv[i]**(2./3.)) -
                    2.*aid.alv[i]**(5./3.)*aid.ulvdh[i]/(
                        3.*aid.ulv[i]**(5./3.)))
            else:
                aid.qlvdh[i] = 0.
            if (aid.arv[i] > 0.) and (aid.urv[i] > 0.):
                aid.qrvdh[i] = der.mfv[1] * (
                    5.*aid.arv[i]**(2./3.)*aid.arvdh[i]/(
                        3.*aid.urv[i]**(2./3.)) -
                    2.*aid.arv[i]**(5./3.)*aid.urvdh[i]/(
                        3.*aid.urv[i]**(5./3.))
                )
            else:
                aid.qrvdh[i] = 0.


class Calc_QLVR_QRVR_V1(modeltools.Method):
    """Calculate the discharge of both outer embankments after
    Manning-Strickler.

    Basic equation:
      :math:`QVR = MFV \\cdot \\frac{AVR^{5/3}}{UVR^{2/3}}`

    Examples:

        Note the handling of zero values for |ULVR| and |URVR| (in the second
        subsection):

        >>> from hydpy.models.lstream import *
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
    CONTROLPARAMETERS = (
        lstream_control.GTS,
    )
    DERIVEDPARAMETERS = (
        lstream_derived.MFV,
    )
    REQUIREDSEQUENCES = (
        lstream_aides.ALVR,
        lstream_aides.ARVR,
        lstream_aides.ULVR,
        lstream_aides.URVR,
    )
    RESULTSEQUENCES = (
        lstream_aides.QLVR,
        lstream_aides.QRVR,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            if aid.ulvr[i] > 0.:
                aid.qlvr[i] = \
                    der.mfv[0]*aid.alvr[i]**(5./3.)/aid.ulvr[i]**(2./3.)
            else:
                aid.qlvr[i] = 0.
            if aid.urvr[i] > 0.:
                aid.qrvr[i] = \
                    der.mfv[1]*aid.arvr[i]**(5./3.)/aid.urvr[i]**(2./3.)
            else:
                aid.qrvr[i] = 0.


class Calc_QLVR_QRVR_V2(modeltools.Method):
    """Calculate the discharge of both outer embankments following the
    kinematic wave approach.

    Basic equation:
      :math:`QVR = \\frac{QVRDH}{AVRDH} \\cdot AVR`

    Examples:

        Note the handling of zero values for |ALVRDH| and |ARVRDH| (in the
        second subsection):

        >>> from hydpy.models.lstream import *
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
    CONTROLPARAMETERS = (
        lstream_control.GTS,
    )
    DERIVEDPARAMETERS = (
        lstream_derived.MFV,
    )
    REQUIREDSEQUENCES = (
        lstream_aides.ALVR,
        lstream_aides.ARVR,
        lstream_aides.QLVRDH,
        lstream_aides.QRVRDH,
        lstream_aides.ALVRDH,
        lstream_aides.ARVRDH,
    )
    RESULTSEQUENCES = (
        lstream_aides.QLVR,
        lstream_aides.QRVR,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            if aid.alvrdh[i] > 0.:
                aid.qlvr[i] = aid.qlvrdh[i]/aid.alvrdh[i]*aid.alvr[i]
            else:
                aid.qlvr[i] = 0.
            if aid.arvrdh[i] > 0.:
                aid.qrvr[i] = aid.qrvrdh[i]/aid.arvrdh[i]*aid.arvr[i]
            else:
                aid.qrvr[i] = 0.


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

        >>> from hydpy.models.lstream import *
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
    CONTROLPARAMETERS = (
        lstream_control.GTS,
    )
    DERIVEDPARAMETERS = (
        lstream_derived.MFV,
    )
    REQUIREDSEQUENCES = (
        lstream_aides.ALVR,
        lstream_aides.ALVRDH,
        lstream_aides.ARVR,
        lstream_aides.ARVRDH,
        lstream_aides.ULVR,
        lstream_aides.ULVRDH,
        lstream_aides.URVR,
        lstream_aides.URVRDH,
    )
    RESULTSEQUENCES = (
        lstream_aides.QLVRDH,
        lstream_aides.QRVRDH,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            if (aid.alvr[i] > 0.) and (aid.ulvr[i] > 0.):
                aid.qlvrdh[i] = der.mfv[0] * (
                    5.*aid.alvr[i]**(2./3.)*aid.alvrdh[i]/(
                        3.*aid.ulvr[i]**(2./3.)) -
                    2.*aid.alvr[i]**(5./3.)*aid.ulvrdh[i]/(
                        3.*aid.ulvr[i]**(5./3.)))
            else:
                aid.qlvrdh[i] = 0.
            if (aid.arvr[i] > 0.) and (aid.urvr[i] > 0.):
                aid.qrvrdh[i] = der.mfv[1] * (
                    5.*aid.arvr[i]**(2./3.)*aid.arvrdh[i]/(
                        3.*aid.urvr[i]**(2./3.)) -
                    2.*aid.arvr[i]**(5./3.)*aid.urvrdh[i]/(
                        3.*aid.urvr[i]**(5./3.)))
            else:
                aid.qrvrdh[i] = 0.


class Calc_AG_V1(modeltools.Method):
    """Calculate the through wetted of the total cross-sections.

    Basic equation:
      :math:`AG = AM+ALV+ARV+ALVR+ARVR`

    Example:

        >>> from hydpy.models.lstream import *
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
    CONTROLPARAMETERS = (
        lstream_control.GTS,
    )
    REQUIREDSEQUENCES = (
        lstream_aides.AM,
        lstream_aides.ALV,
        lstream_aides.ARV,
        lstream_aides.ALVR,
        lstream_aides.ARVR,
    )
    RESULTSEQUENCES = (
        lstream_aides.AG,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            aid.ag[i] = aid.am[i]+aid.alv[i]+aid.arv[i]+aid.alvr[i]+aid.arvr[i]


class Calc_QG_V1(modeltools.Method):
    """Calculate the discharge of the total cross-section.

    Basic equation:
      :math:`QG = QM+QLV+QRV+QLVR+QRVR`

    Example:

        >>> from hydpy.models.lstream import *
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
    CONTROLPARAMETERS = (
        lstream_control.GTS,
    )
    REQUIREDSEQUENCES = (
        lstream_aides.QM,
        lstream_aides.QLV,
        lstream_aides.QRV,
        lstream_aides.QLVR,
        lstream_aides.QRVR,
    )
    RESULTSEQUENCES = (
        lstream_fluxes.QG,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            flu.qg[i] = aid.qm[i]+aid.qlv[i]+aid.qrv[i]+aid.qlvr[i]+aid.qrvr[i]


class Calc_QG_V2(modeltools.Method):
    """Determine the discharge of each the total cross-section based on an
    artificial neural network describing the relationship between water
    storage in the total channel and discharge.

    Example:

        The following example applies a very simple relationship based
        on a single neuron:

        >>> from hydpy.models.lstream import *
        >>> parameterstep()
        >>> gts(2)
        >>> vg2qg(nmb_inputs=1, nmb_neurons=(1,), nmb_outputs=1,
        ...       weights_input=0.5, weights_output=1.0,
        ...       intercepts_hidden=0.0, intercepts_output=-0.5)

        >>> from hydpy import UnitTest
        >>> test = UnitTest(model,
        ...                 model.calc_qg_v2,
        ...                 last_example=10,
        ...                 parseqs=(states.vg,
        ...                          fluxes.qg))
        >>> test.nexts.vg = numpy.ones((10, 2))
        >>> test.nexts.vg[:, 0] = numpy.arange(0.0, 10.0)
        >>> test.nexts.vg[:, 1] = numpy.arange(10.0, 20.0)
        >>> test()
        | ex. |        vg |                 qg |
        ----------------------------------------
        |   1 | 0.0  10.0 |      0.0  0.493307 |
        |   2 | 1.0  11.0 | 0.122459   0.49593 |
        |   3 | 2.0  12.0 | 0.231059  0.497527 |
        |   4 | 3.0  13.0 | 0.317574  0.498499 |
        |   5 | 4.0  14.0 | 0.380797  0.499089 |
        |   6 | 5.0  15.0 | 0.424142  0.499447 |
        |   7 | 6.0  16.0 | 0.452574  0.499665 |
        |   8 | 7.0  17.0 | 0.470688  0.499797 |
        |   9 | 8.0  18.0 | 0.482014  0.499877 |
        |  10 | 9.0  19.0 | 0.489013  0.499925 |

        For more realistic approximations of measured relationships between
        storage and discharge, we require larger neural networks.
    """
    CONTROLPARAMETERS = (
        lstream_control.VG2QG,
    )
    REQUIREDSEQUENCES = (
        lstream_states.VG,
    )
    RESULTSEQUENCES = (
        lstream_fluxes.QG,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        for i in range(con.gts):
            con.vg2qg.inputs[0] = sta.vg[i]
            con.vg2qg.calculate_values()
            flu.qg[i] = con.vg2qg.outputs[0]


class Calc_WBM_V1(modeltools.Method):
    """Calculate the water table width above the main channel.

    Examples:

        Due to :math:`WBM = \\frac{dAM}{dh}`, we can apply the class
        |NumericalDifferentiator| to validate the calculated water
        table widths:

        >>> from hydpy.models.lstream import *
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
    CONTROLPARAMETERS = (
        lstream_control.GTS,
        lstream_control.BM,
        lstream_control.BNM,
    )
    REQUIREDSEQUENCES = (
        lstream_aides.RHM,
        lstream_aides.RHMDH,
        lstream_aides.RHV,
        lstream_aides.RHVDH,
    )
    RESULTSEQUENCES = (
        lstream_aides.WBM,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            d_temp1 = aid.rhm[i]-aid.rhv[i]
            d_temp2 = aid.rhmdh[i]-aid.rhvdh[i]
            aid.wbm[i] = (
                con.bnm*d_temp1*d_temp2 +
                con.bnm*2.*d_temp2*aid.rhv[i] +
                (con.bm+con.bnm*d_temp1)*d_temp2 +
                (con.bm+con.bnm*2.*d_temp1)*aid.rhvdh[i])


class Calc_WBLV_WBRV_V1(modeltools.Method):
    """Calculate the water table width above both forelands.

    Examples:

        Due to :math:`WBV = \\frac{dAV}{dh}`, we can apply the class
        |NumericalDifferentiator| to validate the calculated water
        table widths:

        >>> from hydpy.models.lstream import *
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
    CONTROLPARAMETERS = (
        lstream_control.GTS,
        lstream_control.BV,
        lstream_control.BNV,
    )
    REQUIREDSEQUENCES = (
        lstream_aides.RHV,
        lstream_aides.RHVDH,
        lstream_aides.RHLVR,
        lstream_aides.RHLVRDH,
        lstream_aides.RHRVR,
        lstream_aides.RHRVRDH,
    )
    RESULTSEQUENCES = (
        lstream_aides.WBLV,
        lstream_aides.WBRV,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            d_temp1 = aid.rhv[i] - aid.rhlvr[i]
            d_temp2 = aid.rhvdh[i] - aid.rhlvrdh[i]
            aid.wblv[i] = (
                con.bnv[0]*d_temp1*d_temp2/2. +
                con.bnv[0]*d_temp2*aid.rhlvr[i] +
                (con.bnv[0]*d_temp1/2.+con.bv[0])*d_temp2 +
                (con.bnv[0]*d_temp1+con.bv[0])*aid.rhlvrdh[i])
            d_temp1 = aid.rhv[i] - aid.rhrvr[i]
            d_temp2 = aid.rhvdh[i] - aid.rhrvrdh[i]
            aid.wbrv[i] = (
                con.bnv[1]*d_temp1*d_temp2/2. +
                con.bnv[1]*d_temp2*aid.rhrvr[i] +
                (con.bnv[1]*d_temp1/2.+con.bv[1])*d_temp2 +
                (con.bnv[1]*d_temp1+con.bv[1])*aid.rhrvrdh[i])


class Calc_WBLVR_WBRVR_V1(modeltools.Method):
    """Calculate the water table width above both outer embankments.

    Examples:

        Due to :math:`WBVR = \\frac{dAVR}{dh}`, we can apply the class
        |NumericalDifferentiator| to validate the calculated water
        table widths:

        >>> from hydpy.models.lstream import *
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
    CONTROLPARAMETERS = (
        lstream_control.GTS,
        lstream_control.BNVR,
    )
    REQUIREDSEQUENCES = (
        lstream_aides.RHLVRDH,
        lstream_aides.RHRVR,
        lstream_aides.RHRVRDH,
    )
    RESULTSEQUENCES = (
        lstream_aides.WBLVR,
        lstream_aides.WBRVR,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            aid.wblvr[i] = con.bnvr[0]*aid.rhlvr[i]*aid.rhlvrdh[i]
            aid.wbrvr[i] = con.bnvr[1]*aid.rhrvr[i]*aid.rhrvrdh[i]


class Calc_WBG_V1(modeltools.Method):
    """Calculate the water level width of the total cross-section.

    Basic equation:
      :math:`WBG = WBM+WLV+WRV+WLVR+WRVR`

    Example:

        >>> from hydpy.models.lstream import *
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
    CONTROLPARAMETERS = (
        lstream_control.GTS,
    )
    REQUIREDSEQUENCES = (
        lstream_aides.WBM,
        lstream_aides.WBLV,
        lstream_aides.WBRV,
        lstream_aides.WBLVR,
        lstream_aides.WBRVR,
    )
    RESULTSEQUENCES = (
        lstream_aides.WBG,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            aid.wbg[i] = \
                aid.wbm[i]+aid.wblv[i]+aid.wbrv[i]+aid.wblvr[i]+aid.wbrvr[i]


class Calc_DH_V1(modeltools.Method):
    """Determine the change in the stage.

    Basic equation:
      :math:`DH = \\frac{QG_{i-1}-QG_i}{WBG \\cdot 1000 \\cdot Laen / GTS}`

    Example:

        >>> from hydpy.models.lstream import *
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
    CONTROLPARAMETERS = (
        lstream_control.Laen,
        lstream_control.GTS,
    )
    REQUIREDSEQUENCES = (
        lstream_fluxes.QZ,
        lstream_fluxes.QG,
        lstream_aides.WBG,
    )
    RESULTSEQUENCES = (
        lstream_fluxes.DH,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        aid = model.sequences.aides.fastaccess
        for i in range(con.gts):
            if i:
                d_qz = flu.qg[i-1]
            else:
                d_qz = flu.qz
            flu.dh[i] = (d_qz-flu.qg[i])/(1000.*con.laen/con.gts*aid.wbg[i])


class Update_H_V1(modeltools.Method):
    """Update the stage.

    Basic equation:
      :math:`\\frac{dH}{dt} = DH`

    Example:

        >>> from hydpy.models.lstream import *
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
    CONTROLPARAMETERS = (
        lstream_control.GTS,
    )
    DERIVEDPARAMETERS = (
        lstream_derived.Sek,
    )
    REQUIREDSEQUENCES = (
        lstream_fluxes.DH,
    )
    UPDATEDSEQUENCES = (
        lstream_states.H,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        for i in range(con.gts):
            new.h[i] = old.h[i] + der.sek*flu.dh[i]


class Update_VG_V1(modeltools.Method):
    """Update the water volume.

    Basic equation:
      :math:`\\frac{dV}{dt} = QG_{i-1}-QG_i`

    Example:

        >>> from hydpy.models.lstream import *
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
    CONTROLPARAMETERS = (
        lstream_control.GTS,
    )
    DERIVEDPARAMETERS = (
        lstream_derived.Sek,
    )
    REQUIREDSEQUENCES = (
        lstream_fluxes.QZA,
        lstream_fluxes.QG,
    )
    UPDATEDSEQUENCES = (
        lstream_states.VG,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        for i in range(con.gts):
            if i:
                new.vg[i] = old.vg[i] + der.sek*(flu.qg[i-1]-flu.qg[i])/1e6
            else:
                new.vg[i] = old.vg[i] + der.sek*(flu.qza-flu.qg[i])/1e6


class Calc_QA_V1(modeltools.Method):
    """Query the actual outflow.

    Example:

        >>> from hydpy.models.lstream import *
        >>> parameterstep()
        >>> gts(3)
        >>> fluxes.qg = 2.0, 3.0, 4.0
        >>> model.calc_qa_v1()
        >>> fluxes.qa
        qa(4.0)
    """
    CONTROLPARAMETERS = (
        lstream_control.GTS,
    )
    REQUIREDSEQUENCES = (
        lstream_fluxes.QG,
    )
    RESULTSEQUENCES = (
        lstream_fluxes.QA,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.qa = flu.qg[con.gts-1]


class Pass_Q_V1(modeltools.Method):
    """Pass the outflow to the outlet node."""
    REQUIREDSEQUENCES = (
        lstream_fluxes.QA,
    )
    RESULTSEQUENCES = (
        lstream_outlets.Q,
    )
    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        out = model.sequences.outlets.fastaccess
        out.q[0] += flu.qa


class Model(modeltools.ELSModel):
    """The HydPy-L-Stream model."""
    SOLVERPARAMETERS = (
        lstream_solver.AbsErrorMax,
        lstream_solver.RelErrorMax,
        lstream_solver.RelDTMin,
        lstream_solver.RelDTMax,
    )
    SOLVERSEQUENCES = ()
    INLET_METHODS = (
        Pick_Q_V1,
    )
    RECEIVER_METHODS = ()
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
    FULL_ODE_METHODS = (
        Update_H_V1,
        Update_VG_V1,
    )
    OUTLET_METHODS = (
        Pass_Q_V1,
    )
    SENDER_METHODS = ()


class ProfileMixin:
    """Mixin class for L-Stream models performing discharge calculations
    based on a triple trapezoid profile."""

    def plot_profile(self, labelformat: str = '%.1f'):
        """Plot the triple trapezoid profile and insert the discharge values
        at some characteristic stages.

        We reuse the second example given in the main documentation on module
        |lstream_v001|:

        >>> from hydpy.models.lstream_v001 import *
        >>> parameterstep('1d')
        >>> simulationstep('30m')
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

        Calling method |ProfileMixin.plot_profile| prepares the profile
        plot and, depending on you `matplotlib` configuration, eventually
        prints it directly on your screen:

        >>> model.plot_profile()

        You can use the `pyplot` API of `matplotlib` to modify the figure
        or to save it to disk (or print it to the screen, in case the
        interactive mode of `matplotlib` is disabled):

        >>> from matplotlib import pyplot
        >>> from hydpy.docs import figs
        >>> pyplot.savefig(figs.__path__[0] + '/lstream_plot_profile.png')
        >>> pyplot.close()

        .. image:: lstream_plot_profile.png
        """

        class _XYs:

            def __init__(self):
                self._xs = [0.]
                self._ys = [0.]

            def __iadd__(self, dxdy):
                self._xs.append(self._xs[-1] + float(dxdy[0]))
                self._ys.append(self._ys[-1] + float(dxdy[1]))
                return self

            def __isub__(self, dxdy):
                self._xs.insert(0, self._xs[0] - float(dxdy[0]))
                self._ys.insert(0, self._ys[0] + float(dxdy[1]))
                return self

            def __call__(self):
                return self._xs, self._ys
        con = self.parameters.control
        der = self.parameters.derived
        hmax = 1.3*(con.hm+max(der.hv))

        xys = _XYs()
        xys += con.bm/2., 0.
        xys -= con.bm/2., 0.
        xys += con.hm*con.bnm, con.hm
        xys -= con.hm*con.bnm, con.hm
        xys += con.bv[1], 0.
        xys -= con.bv[0], 0.
        xys += der.hv[1]*con.bnv[1], der.hv[1]
        xys -= der.hv[0]*con.bnv[0], der.hv[0]
        dh = (hmax-der.hv[1]-con.hm)
        xys += dh*con.bnvr[1], dh
        dh = (hmax-der.hv[0]-con.hm)
        xys -= dh*con.bnvr[0], dh
        xs, ys = xys()
        pyplot.plot(xs, ys, color='r')

        x0, x1 = min(xs), max(xs)
        y0, y1 = min(ys), max(ys)
        dy = (y1-y0)/80.
        hs = [0.,
              con.hm/2.,
              con.hm,
              con.hm+der.hv[0]/2.,
              con.hm+der.hv[0],
              con.hm+der.hv[1]/2.,
              con.hm+der.hv[1],
              (con.hm+der.hv[0]+hmax)/2.,
              (con.hm+der.hv[1]+hmax)/2.,
              hmax]
        temp = []
        for h in hs:
            if h not in temp:
                temp.append(h)
        hs = sorted(temp)
        qs = self.calculate_qgvector(hs)
        for idx, (h, q) in enumerate(zip(hs, qs)):
            pyplot.plot([x0, x1], [h, h], 'b:')
            text = f'{labelformat % q} m³/s'
            if idx % 2:
                pyplot.text(x0, h+dy, text, horizontalalignment='left')
            else:
                pyplot.text(x1, h+dy, text, horizontalalignment='right')

        pyplot.title(f'Profile of model {objecttools.elementphrase(self)}')
        pyplot.ylabel('height above the channel bottom [m]')

    def prepare_hvector(
            self,
            nmb: int = 1000,
            exp: float = 2.0,
            hmin: typing.Optional[float] = None,
            hmax: typing.Optional[float] = None
    ) -> typing.Tuple[float, ...]:
        """Prepare a vector of the stage values.

        The argument `nmb` defines the number of stage values, `exp` defines
        their spacing (1.0 results in equidistant values), and `hmin` and
        `hmax` the lowest and highest water stage, respectively:

        >>> from hydpy.models.lstream_v001 import *
        >>> parameterstep()
        >>> from hydpy import print_values
        >>> print_values(model.prepare_hvector(
        ...     nmb=10, hmin=-1.0, hmax=8, exp=1.0))
        -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0

        When not specified by the user, method
        |lstream_model.ProfileMixin.prepare_hvector| determines `hmin`
        and `hmax` based on the current value of |HM| (-10 % and 300 %,
        respectively) and takes a higher sampling rate in the lower value
        range (by setting `exp` to two):

        >>> hm(6.0)
        >>> print_values(model.prepare_hvector(nmb=10))
        -0.6, -0.37037, 0.318519, 1.466667, 3.074074, 5.140741, 7.666667,
        10.651852, 14.096296, 18.0
        """
        if hmax is None:
            hmin = -0.1*self.parameters.control.hm
        if hmax is None:
            hmax = 3.0*self.parameters.control.hm
        hs = numpy.linspace(0., 1., nmb) ** exp
        hs /= hs[-1]
        hs *= hmax-hmin
        hs += hmin
        return tuple(hs)

    def calculate_qgvector(self, hvector: typing.Iterable[float]) \
            -> typing.Tuple[float, ...]:
        """Calculate the discharge values (in m³/s) corresponding to the
        given stage vector.

        We reuse the second example given in the main documentation on module
        |lstream_v001| also show the results of the similar methods
        |lstream_model.ProfileMixin.calculate_agvector| and
        |lstream_model.ProfileMixin.calculate_vgvector|:

        >>> from hydpy.models.lstream_v001 import *
        >>> parameterstep('1d')
        >>> simulationstep('30m')
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

        >>> from hydpy import print_values
        >>> print_values(model.calculate_qgvector([0.0, 1.0, 2.0]))
        0.033153, 7.745345, 28.436875
        >>> print_values(model.calculate_agvector([0.0, 1.0, 2.0]))
        0.623138, 20.0, 50.0
        >>> print_values(model.calculate_vgvector([0.0, 1.0, 2.0]))
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

    def calculate_agvector(self, hvector: typing.Iterable[float]) \
            -> typing.Tuple[float, ...]:
        """Calculate the wetted cross-section areas (in m²) corresponding
        to the given vector of stage values.

        See the documentation on method
        |lstream_model.ProfileMixin.calculate_qgvector| for an example.
        """
        h_ = self.sequences.states.h.values.copy()
        ag = []
        aid = self.sequences.aides
        try:
            for h in hvector:
                self.sequences.states.h = h
                self.calculate_single_terms()
                ag.append(
                    aid.am[0]+aid.alv[0]+aid.arv[0]+aid.alvr[0]+aid.arvr[0])
            return tuple(ag)
        finally:
            self.sequences.states.h(h_)

    def calculate_vgvector(self, hvector: typing.Iterable[float]) \
            -> typing.Tuple[float, ...]:
        """Calculate the water volume stored within a channel subsection (in
        Mio m³) corresponding to the given vector of stage values.

        See the documentation on method
        |lstream_model.ProfileMixin.calculate_qgvector| for an example.
        """
        con = self.parameters.control
        ags = numpy.array(self.calculate_agvector(hvector))
        return tuple(con.laen/con.gts*1000.*ags/1e6)
