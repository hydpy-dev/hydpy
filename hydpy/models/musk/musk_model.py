# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import modeltools
from hydpy.cythons import modelutils
from hydpy.auxs import roottools
from hydpy.interfaces import routinginterfaces
from hydpy.core.typingtools import *

from hydpy.models.musk import musk_control
from hydpy.models.musk import musk_derived
from hydpy.models.musk import musk_solver
from hydpy.models.musk import musk_fluxes
from hydpy.models.musk import musk_factors
from hydpy.models.musk import musk_states
from hydpy.models.musk import musk_inlets
from hydpy.models.musk import musk_outlets


class Pick_Inflow_V1(modeltools.Method):
    """Assign the actual value of the inlet sequence to the inflow sequence."""

    REQUIREDSEQUENCES = (musk_inlets.Q,)
    RESULTSEQUENCES = (musk_fluxes.Inflow,)

    @staticmethod
    def __call__(model: modeltools.SegmentModel) -> None:
        inl = model.sequences.inlets.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.inflow = 0.0
        for idx in range(inl.len_q):
            flu.inflow += inl.q[idx][0]


class Update_Discharge_V1(modeltools.Method):
    r"""Assign the inflow to the start point of the first channel segment.

    Example:

        >>> from hydpy.models.musk import *
        >>> parameterstep()
        >>> nmbsegments(3)
        >>> fluxes.inflow = 2.0
        >>> model.update_discharge_v1()
        >>> states.discharge
        discharge(2.0, nan, nan, nan)
    """

    REQUIREDSEQUENCES = (musk_fluxes.Inflow,)
    UPDATEDSEQUENCES = (musk_states.Discharge,)

    @staticmethod
    def __call__(model: modeltools.SegmentModel) -> None:
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        sta.discharge[0] = flu.inflow


class Calc_Discharge_V1(modeltools.Method):
    r"""Apply the routing equation with fixed coefficients.

    Basic equation:
      :math:`Q_{space+1,time+1} =
      Coefficients_0 \cdot Discharge_{space,time+1} +
      Coefficients_1 \cdot Discharge_{space,time} +
      Coefficients_2 \cdot Discharge_{space+1,time}`

    Examples:

        First, define a channel divided into four segments:

        >>> from hydpy.models.musk import *
        >>> parameterstep()
        >>> nmbsegments(4)

        The following coefficients correspond to pure translation without diffusion:

        >>> coefficients(0.0, 1.0, 0.0)

        The initial flow is 2 m³/s:

        >>> states.discharge.old = 2.0
        >>> states.discharge.new = 2.0

        Successive invocations of method |Calc_Discharge_V1| shift the given inflows to
        the next lower endpoints at each time step:

        >>> states.discharge[0] = 5.0
        >>> model.run_segments(model.calc_discharge_v1)
        >>> model.new2old()
        >>> states.discharge
        discharge(5.0, 2.0, 2.0, 2.0, 2.0)

        >>> states.discharge[0] = 8.0
        >>> model.run_segments(model.calc_discharge_v1)
        >>> model.new2old()
        >>> states.discharge
        discharge(8.0, 5.0, 2.0, 2.0, 2.0)

        >>> states.discharge[0] = 6.0
        >>> model.run_segments(model.calc_discharge_v1)
        >>> model.new2old()
        >>> states.discharge
        discharge(6.0, 8.0, 5.0, 2.0, 2.0)

        We repeat the example with strong wave diffusion:

        >>> coefficients(0.5, 0.0, 0.5)

        >>> states.discharge.old = 2.0
        >>> states.discharge.new = 2.0

        >>> states.discharge[0] = 5.0
        >>> model.run_segments(model.calc_discharge_v1)
        >>> model.new2old()
        >>> states.discharge
        discharge(5.0, 3.5, 2.75, 2.375, 2.1875)

        >>> states.discharge[0] = 8.0
        >>> model.run_segments(model.calc_discharge_v1)
        >>> model.new2old()
        >>> states.discharge
        discharge(8.0, 5.75, 4.25, 3.3125, 2.75)

        >>> states.discharge[0] = 6.0
        >>> model.run_segments(model.calc_discharge_v1)
        >>> model.new2old()
        >>> states.discharge
        discharge(6.0, 5.875, 5.0625, 4.1875, 3.46875)
    """

    CONTROLPARAMETERS = (musk_control.Coefficients,)
    UPDATEDSEQUENCES = (musk_states.Discharge,)

    @staticmethod
    def __call__(model: modeltools.SegmentModel) -> None:
        con = model.parameters.control.fastaccess
        new = model.sequences.states.fastaccess_new
        old = model.sequences.states.fastaccess_old
        i = model.idx_segment
        new.discharge[i + 1] = (
            con.coefficients[0] * new.discharge[i]
            + con.coefficients[1] * old.discharge[i]
            + con.coefficients[2] * old.discharge[i + 1]
        )


class Calc_ReferenceDischarge_V1(modeltools.Method):
    r"""Estimate the reference discharge according to :cite:t:`ref-Todini2007`.

    Basic equations (equations 45 and 46):
      :math:`ReferenceDischarge_{next, new} =
      \frac{Discharge_{last, new} + Discharge^*_{next, new}}{2}`

      :math:`Discharge^*_{next, new} = Discharge_{next, old} +
      (Discharge_{last, new} - Discharge_{last, old})`

    Examples:

        The Muskingum-Cunge-Todini method requires an initial guess for the new
        discharge value at the segment endpoint, which other methods have to improve
        later.  However, the final discharge value will still depend on the initial
        estimate.  Hence, :cite:t:`ref-Todini2007` suggests an iterative refinement by
        repeating all relevant methods.  Method |Calc_ReferenceDischarge_V1| plays a
        significant role in controlling this refinement.  It calculates the initial
        estimate as defined in the basic equationsDuring the first run (when the index
        property |Idx_Run| is zero):

        >>> from hydpy.models.musk import *
        >>> parameterstep()
        >>> nmbsegments(1)
        >>> states.discharge.old = 3.0, 2.0
        >>> states.discharge.new = 4.0, 5.0
        >>> model.idx_run = 0
        >>> model.calc_referencedischarge_v1()
        >>> fluxes.referencedischarge
        referencedischarge(3.5)

        However, subsequent runs use the already available estimate calculated in the
        last iteration.:

        >>> model.idx_run = 1
        >>> model.calc_referencedischarge_v1()
        >>> fluxes.referencedischarge
        referencedischarge(4.5)
    """

    REQUIREDSEQUENCES = (musk_states.Discharge,)
    RESULTSEQUENCES = (musk_fluxes.ReferenceDischarge,)

    @staticmethod
    def __call__(model: modeltools.SegmentModel) -> None:
        flu = model.sequences.fluxes.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        i = model.idx_segment
        if model.idx_run == 0:
            est: float = old.discharge[i + 1] + new.discharge[i] - old.discharge[i]
        else:
            est = new.discharge[i + 1]
        flu.referencedischarge[i] = (new.discharge[i] + est) / 2.0


class Return_Discharge_CrossSectionModel_V1(modeltools.Method):
    """Let a submodel that follows the |CrossSectionModel_V1| submodel interface
    calculate the discharge for the given water depth and return it.

    See the documentation on method |Return_ReferenceDischargeError_V1| for an example.
    """

    @staticmethod
    def __call__(
        model: modeltools.SegmentModel,
        wqmodel: routinginterfaces.CrossSectionModel_V1,
        waterdepth: float,
    ) -> float:
        wqmodel.use_waterdepth(waterdepth)
        return wqmodel.get_discharge()


class Return_ReferenceDischargeError_V1(modeltools.Method):
    r"""Calculate the difference between the discharge corresponding to the given water
    depth and the reference discharge.

    Basic equation:
      :math:`Return\_Discharge\_V1(waterdepth) - ReferenceDischarge`

    Example:

        We use the submodel |wq_trapeze_strickler| as an example:

        >>> from hydpy.models.musk_mct import *
        >>> parameterstep()
        >>> nmbsegments(1)
        >>> bottomslope(0.01)
        >>> with model.add_wqmodel_v1("wq_trapeze_strickler"):
        ...     nmbtrapezes(1)
        ...     bottomlevels(0.0)
        ...     bottomwidths(2.0)
        ...     sideslopes(2.0)
        ...     stricklercoefficients(20.0)
        >>> fluxes.referencedischarge = 50.0
        >>> from hydpy import round_
        >>> round_(model.return_referencedischargeerror_v1(3.0))
        14.475285
    """

    SUBMETHODS = (Return_Discharge_CrossSectionModel_V1,)
    REQUIREDSEQUENCES = (musk_fluxes.ReferenceDischarge,)

    @staticmethod
    def __call__(model: modeltools.SegmentModel, waterdepth: float) -> float:
        flu = model.sequences.fluxes.fastaccess
        i = model.idx_segment
        return (
            model.return_discharge_crosssectionmodel_v1(
                cast(routinginterfaces.CrossSectionModel_V1, model.wqmodel), waterdepth
            )
            - flu.referencedischarge[i]
        )


class Calc_ReferenceWaterDepth_V1(modeltools.Method):
    r"""Find the reference water depth via |Pegasus| iteration.

    Examples:

        The following test calculation extends the example of the documentation on
        method |Return_ReferenceDischargeError_V1|.  The first and the last channel
        segments demonstrate that method |Calc_ReferenceWaterDepth_V1| restricts the
        Pegasus search to the lowest water depth of 0 m and the highest water depth of
        1000 m:

        >>> from hydpy.models.musk_mct import *
        >>> parameterstep()
        >>> catchmentarea(100.0)
        >>> nmbsegments(5)
        >>> bottomslope(0.01)
        >>> with model.add_wqmodel_v1("wq_trapeze_strickler"):
        ...     nmbtrapezes(1)
        ...     bottomlevels(0.0)
        ...     bottomwidths(2.0)
        ...     sideslopes(2.0)
        ...     stricklercoefficients(20.0)
        >>> solver.tolerancewaterdepth.update()
        >>> solver.tolerancedischarge.update()
        >>> fluxes.referencedischarge = -10.0, 0.0, 64.475285, 1000.0, 1000000000.0
        >>> model.run_segments(model.calc_referencewaterdepth_v1)
        >>> factors.referencewaterdepth
        referencewaterdepth(0.0, 0.0, 3.0, 9.199035, 1000.0)

        Repeated applications of |Calc_ReferenceWaterDepth_V1| should always yield the
        same results but are often more efficient than the initial calculation because
        they use old reference water depth estimates to gain more precise initial
        search intervals:

        >>> model.run_segments(model.calc_referencewaterdepth_v1)
        >>> factors.referencewaterdepth
        referencewaterdepth(0.0, 0.0, 3.0, 9.199035, 1000.0)

        The Pegasus algorithm stops when the search interval is smaller than the
        tolerance value defined by the |ToleranceWaterDepth| parameter or if the
        difference to the target discharge is less than the tolerance value defined by
        the |ToleranceDischarge| parameter.  By default, the water depth-related
        tolerance is zero; hence, the discharge-related tolerance must stop the
        iteration:

        >>> solver.tolerancewaterdepth
        tolerancewaterdepth(0.0)
        >>> solver.tolerancedischarge
        tolerancedischarge(0.0001)

        Increase at least one parameter to reduce computation time:

        >>> solver.tolerancewaterdepth(0.1)
        >>> factors.referencewaterdepth = nan
        >>> model.run_segments(model.calc_referencewaterdepth_v1)
        >>> factors.referencewaterdepth
        referencewaterdepth(0.0, 0.0, 3.000295, 9.196508, 1000.0)
    """

    SUBMETHODS = (Return_ReferenceDischargeError_V1,)
    SOLVERPARAMETERS = (musk_solver.ToleranceWaterDepth, musk_solver.ToleranceDischarge)
    REQUIREDSEQUENCES = (musk_fluxes.ReferenceDischarge,)
    RESULTSEQUENCES = (musk_factors.ReferenceWaterDepth,)

    @staticmethod
    def __call__(model: modeltools.SegmentModel) -> None:
        sol = model.parameters.solver.fastaccess
        fac = model.sequences.factors.fastaccess
        i = model.idx_segment
        wl: float = fac.referencewaterdepth[i]
        if modelutils.isnan(wl) or modelutils.isinf(wl):
            mn: float = 0.0
            mx: float = 2.0
        elif wl <= 0.001:
            mn, mx = 0.0, 0.01
        else:
            mn, mx = 0.9 * wl, 1.1 * wl
        fac.referencewaterdepth[i] = model.pegasusreferencewaterdepth.find_x(
            mn, mx, 0.0, 1000.0, sol.tolerancewaterdepth, sol.tolerancedischarge, 100
        )


class Calc_WettedArea_SurfaceWidth_Celerity_CrossSectionModel_V1(modeltools.Method):
    """Let a submodel that follows the |CrossSectionModel_V1| interface calculate all
    its properties based on the current reference water level and query the wetted
    area, the surface width, and the celerity."""

    SUBMETHODS = ()
    REQUIREDSEQUENCES = (musk_factors.ReferenceWaterDepth,)
    RESULTSEQUENCES = (
        musk_factors.WettedArea,
        musk_factors.SurfaceWidth,
        musk_factors.Celerity,
    )

    @staticmethod
    def __call__(
        model: modeltools.SegmentModel, wqmodel: routinginterfaces.CrossSectionModel_V1
    ) -> None:
        fac = model.sequences.factors.fastaccess
        i = model.idx_segment
        wqmodel.use_waterdepth(fac.referencewaterdepth[i])
        fac.wettedarea[i] = wqmodel.get_wettedarea()
        fac.surfacewidth[i] = wqmodel.get_surfacewidth()
        fac.celerity[i] = wqmodel.get_celerity()


class Calc_WettedArea_SurfaceWidth_Celerity_V1(modeltools.Method):
    """Let a submodel that follows the |CrossSectionModel_V1| interface calculate all
    its properties based on the current reference water level and query the wetted
    area, the surface width, and the celerity.

    Example:

        We use the submodel |wq_trapeze_strickler| as an example:

        >>> from hydpy.models.musk_mct import *
        >>> parameterstep()
        >>> nmbsegments(3)
        >>> bottomslope(0.01)
        >>> with model.add_wqmodel_v1("wq_trapeze_strickler"):
        ...     nmbtrapezes(1)
        ...     bottomlevels(0.0)
        ...     bottomwidths(2.0)
        ...     sideslopes(0.0)
        ...     stricklercoefficients(20.0)
        >>> factors.referencewaterdepth = 1.0, 2.0, 3.0
        >>> model.run_segments(model.calc_wettedarea_surfacewidth_celerity_v1)
        >>> factors.wettedarea
        wettedarea(2.0, 4.0, 6.0)
        >>> factors.surfacewidth
        surfacewidth(2.0, 2.0, 2.0)
        >>> factors.celerity
        celerity(1.679895, 1.86546, 1.926124)
    """

    SUBMETHODS = (Calc_WettedArea_SurfaceWidth_Celerity_CrossSectionModel_V1,)
    REQUIREDSEQUENCES = (musk_factors.ReferenceWaterDepth,)
    RESULTSEQUENCES = (
        musk_factors.WettedArea,
        musk_factors.SurfaceWidth,
        musk_factors.Celerity,
    )

    @staticmethod
    def __call__(model: modeltools.SegmentModel) -> None:
        if model.wqmodel_typeid == 1:
            model.calc_wettedarea_surfacewidth_celerity_crosssectionmodel_v1(
                cast(routinginterfaces.CrossSectionModel_V1, model.wqmodel)
            )


class Calc_CorrectingFactor_V1(modeltools.Method):
    r"""Calculate the correcting factor according to :cite:t:`ref-Todini2007`.

    Basic equation (equation 49):
      :math:`CorrectingFactor = \frac{Celerity \cdot WettedArea}{ReferenceDischarge}`

    Example:

        The last segment shows that |Calc_CorrectingFactor_V1| prevents zero divisions
        by setting the correcting factor to one when necessary:

        >>> from hydpy.models.musk import *
        >>> parameterstep()
        >>> nmbsegments(3)
        >>> factors.celerity = 1.0
        >>> factors.wettedarea = 2.0, 2.0, 2.0
        >>> fluxes.referencedischarge = 4.0, 2.0, 0.0
        >>> model.run_segments(model.calc_correctingfactor_v1)
        >>> factors.correctingfactor
        correctingfactor(0.5, 1.0, 1.0)
    """

    REQUIREDSEQUENCES = (
        musk_factors.Celerity,
        musk_factors.WettedArea,
        musk_fluxes.ReferenceDischarge,
    )
    RESULTSEQUENCES = (musk_factors.CorrectingFactor,)

    @staticmethod
    def __call__(model: modeltools.SegmentModel) -> None:
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        i = model.idx_segment
        if flu.referencedischarge[i] == 0.0:
            fac.correctingfactor[i] = 1.0
        else:
            fac.correctingfactor[i] = (
                fac.celerity[i] * fac.wettedarea[i] / flu.referencedischarge[i]
            )


class Calc_CourantNumber_V1(modeltools.Method):
    r"""Calculate the Courant number according to :cite:t:`ref-Todini2007`.

    Basic equation (equation 50):
      :math:`CourantNumber =
      \frac{Celerity \cdot Seconds}{CorrectingFactor \cdot 1000 \cdot SegmentLength}`

    Example:

        The last segment shows that |Calc_CourantNumber_V1| prevents zero divisions by
        setting the courant number to zero when necessary:

        >>> from hydpy.models.musk import *
        >>> parameterstep()
        >>> nmbsegments(5)
        >>> derived.seconds(1000.0)
        >>> derived.segmentlength(4.0)
        >>> factors.celerity = 2.0
        >>> factors.correctingfactor = 0.0, 0.5, 1.0, 2.0, inf
        >>> model.run_segments(model.calc_courantnumber_v1)
        >>> states.courantnumber
        courantnumber(0.0, 1.0, 0.5, 0.25, 0.0)
    """

    DERIVEDPARAMETERS = (musk_derived.Seconds, musk_derived.SegmentLength)
    REQUIREDSEQUENCES = (musk_factors.Celerity, musk_factors.CorrectingFactor)
    RESULTSEQUENCES = (musk_states.CourantNumber,)

    @staticmethod
    def __call__(model: modeltools.SegmentModel) -> None:
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        sta = model.sequences.states.fastaccess
        i = model.idx_segment
        if fac.correctingfactor[i] == 0.0:
            sta.courantnumber[i] = 0.0
        else:
            sta.courantnumber[i] = (fac.celerity[i] / fac.correctingfactor[i]) * (
                der.seconds / (1000.0 * der.segmentlength)
            )


class Calc_ReynoldsNumber_V1(modeltools.Method):
    r"""Calculate the cell Reynolds number according to :cite:t:`ref-Todini2007`.

    Basic equation (equation 51):
      :math:`ReynoldsNumber = \frac{ReferenceDischarge}{CorrectingFactor \cdot
      SurfaceWidth \cdot BottomSlope \cdot Celerity \cdot 1000 \cdot SegmentLength}`

    Example:

        The last segment shows that |Calc_ReynoldsNumber_V1| prevents zero divisions by
        setting the cell reynolds number to zero when necessary:

        >>> from hydpy.models.musk import *
        >>> parameterstep()
        >>> nmbsegments(5)
        >>> bottomslope(0.01)
        >>> derived.segmentlength(4.0)
        >>> factors.surfacewidth = 5.0
        >>> factors.celerity = 2.0
        >>> factors.correctingfactor = 0.0, 0.5, 1.0, 2.0, inf
        >>> fluxes.referencedischarge = 10.0
        >>> model.run_segments(model.calc_reynoldsnumber_v1)
        >>> states.reynoldsnumber
        reynoldsnumber(0.0, 0.05, 0.025, 0.0125, 0.0)
    """

    CONTROLPARAMETERS = (musk_control.BottomSlope,)
    DERIVEDPARAMETERS = (musk_derived.SegmentLength,)
    REQUIREDSEQUENCES = (
        musk_fluxes.ReferenceDischarge,
        musk_factors.CorrectingFactor,
        musk_factors.SurfaceWidth,
        musk_factors.Celerity,
    )
    RESULTSEQUENCES = (musk_states.ReynoldsNumber,)

    @staticmethod
    def __call__(model: modeltools.SegmentModel) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        i = model.idx_segment
        denom: float = (
            fac.correctingfactor[i]
            * fac.surfacewidth[i]
            * con.bottomslope
            * fac.celerity[i]
            * (1000.0 * der.segmentlength)
        )
        if denom == 0.0:
            sta.reynoldsnumber[i] = 0.0
        else:
            sta.reynoldsnumber[i] = flu.referencedischarge[i] / denom


class Calc_Coefficient1_Coefficient2_Coefficient3_V1(modeltools.Method):
    r"""Calculate the coefficients of the Muskingum working formula according to
    :cite:t:`ref-Todini2007`.

    Basic equations (equation 52, corrigendum):
      :math:`Coefficient1 = \frac
      {-1 + CourantNumber_{new} + ReynoldsNumber_{new}}
      {1 + CourantNumber_{new} + ReynoldsNumber_{new}}`

      :math:`Coefficient2 = \frac
      {1 + CourantNumber_{old} - ReynoldsNumber_{old}}
      {1 + CourantNumber_{new} + ReynoldsNumber_{new}}
      \cdot \frac{CourantNumber_{new}}{CourantNumber_{old}}`

      :math:`Coefficient3 = \frac
      {1 - CourantNumber_{old} + ReynoldsNumber_{old}}
      {1 + CourantNumber_{new} + ReynoldsNumber_{new}}
      \cdot \frac{CourantNumber_{new}}{CourantNumber_{old}}`

    Examples:

        We make some effort to calculate consistent "old" and "new" Courant and
        Reynolds numbers:

        >>> from hydpy.models.musk import *
        >>> parameterstep()
        >>> nmbsegments(5)
        >>> bottomslope(0.01)
        >>> derived.seconds(1000.0)
        >>> derived.segmentlength(4.0)
        >>> factors.celerity = 2.0
        >>> factors.surfacewidth = 5.0
        >>> factors.correctingfactor = 0.0, 0.5, 1.0, 2.0, inf
        >>> fluxes.referencedischarge = 10.0
        >>> model.run_segments(model.calc_courantnumber_v1)
        >>> model.run_segments(model.calc_reynoldsnumber_v1)
        >>> states.courantnumber.new2old()
        >>> states.reynoldsnumber.new2old()
        >>> fluxes.referencedischarge = 11.0
        >>> model.run_segments(model.calc_courantnumber_v1)
        >>> model.run_segments(model.calc_reynoldsnumber_v1)

        Due to the consistency of its input data,
        |Calc_Coefficient1_Coefficient2_Coefficient3_V1| calculates the three working
        coefficients so that their sum is one:

        >>> model.run_segments(model.calc_coefficient1_coefficient2_coefficient3_v1)
        >>> factors.coefficient1
        coefficient1(-1.0, 0.026764, -0.309329, -0.582591, -1.0)
        >>> factors.coefficient2
        coefficient2(1.0, 0.948905, 0.96563, 0.979228, 1.0)
        >>> factors.coefficient3
        coefficient3(1.0, 0.024331, 0.343699, 0.603363, 1.0)
        >>> from hydpy import print_vector
        >>> print_vector(
        ...     factors.coefficient1 + factors.coefficient2 + factors.coefficient3)
        1.0, 1.0, 1.0, 1.0, 1.0

        Note that the "old" Courant numbers of the first and the last segment are zero.

        >>> print_vector(states.courantnumber.old)
        0.0, 1.0, 0.5, 0.25, 0.0

        To prevent zero divisions, |Calc_Coefficient1_Coefficient2_Coefficient3_V1|
        assumes the ratio between the new and the old Courant number to be one in such
        cases.
    """

    REQUIREDSEQUENCES = (musk_states.CourantNumber, musk_states.ReynoldsNumber)
    UPDATEDSEQUENCES = (
        musk_factors.Coefficient1,
        musk_factors.Coefficient2,
        musk_factors.Coefficient3,
    )

    @staticmethod
    def __call__(model: modeltools.SegmentModel) -> None:
        fac = model.sequences.factors.fastaccess
        new = model.sequences.states.fastaccess_new
        old = model.sequences.states.fastaccess_old
        i = model.idx_segment
        f: float = 1.0 / (1.0 + new.courantnumber[i] + new.reynoldsnumber[i])
        fac.coefficient1[i] = (new.courantnumber[i] + new.reynoldsnumber[i] - 1.0) * f
        if old.courantnumber[i] != 0.0:
            f *= new.courantnumber[i] / old.courantnumber[i]
        fac.coefficient2[i] = (1 + old.courantnumber[i] - old.reynoldsnumber[i]) * f
        fac.coefficient3[i] = (1 - old.courantnumber[i] + old.reynoldsnumber[i]) * f


class Calc_Discharge_V2(modeltools.Method):
    r"""Apply the routing equation with discharge-dependent coefficients.

    Basic equation:
      :math:`Discharge_{next, new} =
      Coefficient0 \cdot Discharge_{last, new} +
      Coefficient1 \cdot Discharge_{last, old} +
      Coefficient2 \cdot Discharge_{next, old}`

    Examples:

        First, we define a channel divided into four segments:

        >>> from hydpy.models.musk import *
        >>> parameterstep()
        >>> nmbsegments(4)

        The following coefficients correspond to pure translation without diffusion:

        >>> factors.coefficient1 = 0.0
        >>> factors.coefficient2 = 1.0
        >>> factors.coefficient3 = 0.0

        The initial flow is 2 m³/s:

        >>> states.discharge.old = 2.0
        >>> states.discharge.new = 2.0

        Successive invocations of method |Calc_Discharge_V2| shift the given inflows to
        the next lower endpoints at each time step:

        >>> states.discharge[0] = 5.0
        >>> model.run_segments(model.calc_discharge_v2)
        >>> model.new2old()
        >>> states.discharge
        discharge(5.0, 2.0, 2.0, 2.0, 2.0)

        >>> states.discharge[0] = 8.0
        >>> model.run_segments(model.calc_discharge_v2)
        >>> model.new2old()
        >>> states.discharge
        discharge(8.0, 5.0, 2.0, 2.0, 2.0)

        >>> states.discharge[0] = 6.0
        >>> model.run_segments(model.calc_discharge_v2)
        >>> model.new2old()
        >>> states.discharge
        discharge(6.0, 8.0, 5.0, 2.0, 2.0)

        We repeat the example with strong wave diffusion:

        >>> factors.coefficient1 = 0.5
        >>> factors.coefficient2 = 0.0
        >>> factors.coefficient3 = 0.5

        >>> states.discharge.old = 2.0
        >>> states.discharge.new = 2.0

        >>> states.discharge[0] = 5.0
        >>> model.run_segments(model.calc_discharge_v2)
        >>> model.new2old()
        >>> states.discharge
        discharge(5.0, 3.5, 2.75, 2.375, 2.1875)

        >>> states.discharge[0] = 8.0
        >>> model.run_segments(model.calc_discharge_v2)
        >>> model.new2old()
        >>> states.discharge
        discharge(8.0, 5.75, 4.25, 3.3125, 2.75)

        >>> states.discharge[0] = 6.0
        >>> model.run_segments(model.calc_discharge_v2)
        >>> model.new2old()
        >>> states.discharge
        discharge(6.0, 5.875, 5.0625, 4.1875, 3.46875)
    """

    REQUIREDSEQUENCES = (
        musk_factors.Coefficient1,
        musk_factors.Coefficient2,
        musk_factors.Coefficient3,
    )
    UPDATEDSEQUENCES = (musk_states.Discharge,)

    @staticmethod
    def __call__(model: modeltools.SegmentModel) -> None:
        fac = model.sequences.factors.fastaccess
        new = model.sequences.states.fastaccess_new
        old = model.sequences.states.fastaccess_old
        i = model.idx_segment
        if new.discharge[i] == old.discharge[i] == old.discharge[i + 1]:
            new.discharge[i + 1] = new.discharge[i]
        else:
            new.discharge[i + 1] = (
                fac.coefficient1[i] * new.discharge[i]
                + fac.coefficient2[i] * old.discharge[i]
                + fac.coefficient3[i] * old.discharge[i + 1]
            )
        new.discharge[i + 1] = max(new.discharge[i + 1], 0.0)


class Calc_Outflow_V1(modeltools.Method):
    r"""Take the discharge at the last segment endpoint as the channel's outflow.

    Basic equation:
      :math:`Outflow =  Discharge_{NmbSegments}`

    Example:

        >>> from hydpy.models.musk import *
        >>> parameterstep()
        >>> nmbsegments(2)
        >>> states.discharge.new = 1.0, 2.0, 3.0
        >>> model.calc_outflow_v1()
        >>> fluxes.outflow
        outflow(3.0)
    """

    CONTROLPARAMETERS = (musk_control.NmbSegments,)
    REQUIREDSEQUENCES = (musk_states.Discharge,)
    RESULTSEQUENCES = (musk_fluxes.Outflow,)

    @staticmethod
    def __call__(model: modeltools.SegmentModel) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess_new
        flu.outflow = sta.discharge[con.nmbsegments]


class Pass_Outflow_V1(modeltools.Method):
    """Pass the channel's outflow to the outlet sequence."""

    REQUIREDSEQUENCES = (musk_fluxes.Outflow,)
    RESULTSEQUENCES = (musk_outlets.Q,)

    @staticmethod
    def __call__(model: modeltools.SegmentModel) -> None:
        flu = model.sequences.fluxes.fastaccess
        out = model.sequences.outlets.fastaccess
        out.q[0] += flu.outflow


class PegasusReferenceWaterDepth(roottools.Pegasus):
    """Pegasus iterator for finding the correct reference water depth."""

    METHODS = (Return_ReferenceDischargeError_V1,)


class Model(modeltools.SegmentModel):
    """|musk.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(short="Musk")
    __HYDPY_ROOTMODEL__ = None

    SOLVERPARAMETERS = (
        musk_solver.NmbRuns,
        musk_solver.ToleranceWaterDepth,
        musk_solver.ToleranceDischarge,
    )
    INLET_METHODS = (Pick_Inflow_V1, Update_Discharge_V1)
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        Calc_Discharge_V1,
        Calc_ReferenceDischarge_V1,
        Calc_ReferenceWaterDepth_V1,
        Calc_WettedArea_SurfaceWidth_Celerity_V1,
        Calc_CorrectingFactor_V1,
        Calc_CourantNumber_V1,
        Calc_ReynoldsNumber_V1,
        Calc_Coefficient1_Coefficient2_Coefficient3_V1,
        Calc_Discharge_V2,
    )
    ADD_METHODS = (
        Return_Discharge_CrossSectionModel_V1,
        Return_ReferenceDischargeError_V1,
        Calc_WettedArea_SurfaceWidth_Celerity_CrossSectionModel_V1,
    )
    OUTLET_METHODS = (Calc_Outflow_V1, Pass_Outflow_V1)
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = (PegasusReferenceWaterDepth,)

    wqmodel = modeltools.SubmodelProperty(routinginterfaces.CrossSectionModel_V1)
    wqmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    wqmodel_typeid = modeltools.SubmodelTypeIDProperty()
