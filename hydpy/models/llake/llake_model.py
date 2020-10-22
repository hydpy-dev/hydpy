# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# imports...
# ...from HydPy
from hydpy.core import modeltools
from hydpy.models.llake import llake_control
from hydpy.models.llake import llake_derived
from hydpy.models.llake import llake_fluxes
from hydpy.models.llake import llake_states
from hydpy.models.llake import llake_aides
from hydpy.models.llake import llake_inlets
from hydpy.models.llake import llake_outlets


class Solve_DV_DT_V1(modeltools.Method):
    """Solve the differential equation of HydPy-L.

    At the moment, HydPy-L only implements a simple numerical solution of
    its underlying ordinary differential equation.  To increase the accuracy
    (or sometimes even to prevent instability) of this approximation, one
    can set the value of parameter |MaxDT| to a value smaller than the actual
    simulation step size.  Method |Solve_DV_DT_V1| then applies the methods
    related to the numerical approximation multiple times and aggregates
    the results.

    Note that the order of convergence is one only.  It is hard to tell how
    short the internal simulation step needs to be to ensure a certain degree
    of accuracy.  In most cases one hour or very often even one day should be
    sufficient to gain acceptable results.  However, this strongly depends on
    the given water stage-volume-discharge relationship.  Hence it seems
    advisable to always define a few test waves and apply the llake model with
    different |MaxDT| values.  Afterwards, select a |MaxDT| value  lower than
    one which results in acceptable approximations for all test waves.  The
    computation time of the llake mode per substep is rather small, so always
    include a safety factor.

    Of course, an adaptive step size determination would be much more
    convenient...

    Note that method |Solve_DV_DT_V1| calls the versions of `calc_vq`,
    `interp_qa` and `calc_v_qa` selected by the respective application model.
    Hence, also their parameter and sequence specifications need to be
    considered.

    Basic equation:
      :math:`\\frac{dV}{dt}= QZ - QA(V)`
    """

    DERIVEDPARAMETERS = (llake_derived.NmbSubsteps,)
    UPDATEDSEQUENCES = (llake_states.V,)
    RESULTSEQUENCES = (
        llake_aides.V,
        llake_fluxes.QA,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        aid = model.sequences.aides.fastaccess
        flu.qa = 0.0
        aid.v = old.v
        for _ in range(der.nmbsubsteps):
            model.calc_vq()
            model.interp_qa()
            model.calc_v_qa()
            flu.qa += aid.qa
        flu.qa /= der.nmbsubsteps
        new.v = aid.v


class Calc_VQ_V1(modeltools.Method):
    """Calculate the auxiliary term.

    Basic equation:
      :math:`VQ = 2 \\cdot V + \\frac{Seconds}{NmbSubsteps} \\cdot QZ`

    Example:

        The following example shows that the auxiliary term `vq` does not
        depend on the (outer) simulation step size but on the (inner)
        calculation step size defined by parameter `maxdt`:

        >>> from hydpy.models.llake import *
        >>> parameterstep('1d')
        >>> simulationstep('12h')
        >>> maxdt('6h')
        >>> derived.seconds.update()
        >>> derived.nmbsubsteps.update()
        >>> fluxes.qz = 2.
        >>> aides.v = 1e5
        >>> model.calc_vq_v1()
        >>> aides.vq
        vq(243200.0)
    """

    DERIVEDPARAMETERS = (
        llake_derived.Seconds,
        llake_derived.NmbSubsteps,
    )
    REQUIREDSEQUENCES = (
        llake_aides.V,
        llake_fluxes.QZ,
    )
    RESULTSEQUENCES = (llake_aides.VQ,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        aid = model.sequences.aides.fastaccess
        aid.vq = 2.0 * aid.v + der.seconds / der.nmbsubsteps * flu.qz


class Interp_QA_V1(modeltools.Method):
    """Calculate the lake outflow based on linear interpolation.

    Examples:

        In preparation for the following examples, define a short simulation
        time period with a simulation step size of 12 hours and initialize
        the required model object:

        >>> from hydpy import pub
        >>> pub.timegrids = '2000.01.01','2000.01.04', '12h'
        >>> from hydpy.models.llake import *
        >>> parameterstep()

        Next, for the sake of brevity, define a test function:

        >>> def test(*vqs):
        ...     for vq in vqs:
        ...         aides.vq(vq)
        ...         model.interp_qa_v1()
        ...         print(repr(aides.vq), repr(aides.qa))

        The following three relationships between the auxiliary term `vq` and
        the tabulated discharge `q` are taken as examples.  Each one is valid
        for one of the first three days in January and is defined via five
        nodes:

        >>> n(5)
        >>> derived.toy.update()
        >>> derived.vq(_1_1_6=[0., 1., 2., 2., 3.],
        ...            _1_2_6=[0., 1., 2., 2., 3.],
        ...            _1_3_6=[0., 1., 2., 3., 4.])
        >>> q(_1_1_6=[0., 0., 0., 0., 0.],
        ...   _1_2_6=[0., 2., 5., 6., 9.],
        ...   _1_3_6=[0., 2., 1., 3., 2.])

        In the first example, discharge does not depend on the actual value
        of the auxiliary term and is always zero:

        >>> model.idx_sim = pub.timegrids.init['2000.01.01']
        >>> test(0., .75, 1., 4./3., 2., 7./3., 3., 10./3.)
        vq(0.0) qa(0.0)
        vq(0.75) qa(0.0)
        vq(1.0) qa(0.0)
        vq(1.333333) qa(0.0)
        vq(2.0) qa(0.0)
        vq(2.333333) qa(0.0)
        vq(3.0) qa(0.0)
        vq(3.333333) qa(0.0)

        The seconds example demonstrates that relationships are allowed to
        contain jumps, which is the case for the (`vq`,`q`) pairs (2,6) and
        (2,7).  Also it demonstrates that when the highest `vq` value is
        exceeded linear extrapolation based on the two highest (`vq`,`q`)
        pairs is performed:

        >>> model.idx_sim = pub.timegrids.init['2000.01.02']
        >>> test(0., .75, 1., 4./3., 2., 7./3., 3., 10./3.)
        vq(0.0) qa(0.0)
        vq(0.75) qa(1.5)
        vq(1.0) qa(2.0)
        vq(1.333333) qa(3.0)
        vq(2.0) qa(5.0)
        vq(2.333333) qa(7.0)
        vq(3.0) qa(9.0)
        vq(3.333333) qa(10.0)

        The third example shows that the relationships do not need to be
        arranged monotonously increasing.  Particualarly for the extrapolation
        range, this could result in negative values of `qa`, which is avoided
        by setting it to zero in such cases:

        >>> model.idx_sim = pub.timegrids.init['2000.01.03']
        >>> test(.5, 1.5, 2.5, 3.5, 4.5, 10.)
        vq(0.5) qa(1.0)
        vq(1.5) qa(1.5)
        vq(2.5) qa(2.0)
        vq(3.5) qa(2.5)
        vq(4.5) qa(1.5)
        vq(10.0) qa(0.0)

    """

    CONTROLPARAMETERS = (
        llake_control.N,
        llake_control.Q,
    )
    DERIVEDPARAMETERS = (
        llake_derived.TOY,
        llake_derived.VQ,
    )
    REQUIREDSEQUENCES = (llake_aides.VQ,)
    RESULTSEQUENCES = (llake_aides.QA,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        aid = model.sequences.aides.fastaccess
        idx = der.toy[model.idx_sim]
        for jdx in range(1, con.n):
            if der.vq[idx, jdx] >= aid.vq:
                break
        aid.qa = (aid.vq - der.vq[idx, jdx - 1]) * (
            con.q[idx, jdx] - con.q[idx, jdx - 1]
        ) / (der.vq[idx, jdx] - der.vq[idx, jdx - 1]) + con.q[idx, jdx - 1]
        aid.qa = max(aid.qa, 0.0)


class Calc_V_QA_V1(modeltools.Method):
    """Update the stored water volume based on the equation of continuity.

    Note that for too high outflow values, which would result in overdraining
    the lake, the outflow is trimmed.

    Basic Equation:
      :math:`\\frac{dV}{dt}= QZ - QA`

    Examples:

        Prepare a lake model with an initial storage of 100.000 m³ and an
        inflow of 2 m³/s and a (potential) outflow of 6 m³/s:

        >>> from hydpy.models.llake import *
        >>> parameterstep()
        >>> simulationstep('12h')
        >>> maxdt('6h')
        >>> derived.seconds.update()
        >>> derived.nmbsubsteps.update()
        >>> aides.v = 1e5
        >>> fluxes.qz = 2.
        >>> aides.qa = 6.

        Through calling method `calc_v_qa_v1` three times with the same inflow
        and outflow values, the storage is emptied after the second step and
        outflow is equal to inflow after the third step:

        >>> model.calc_v_qa_v1()
        >>> aides.v
        v(13600.0)
        >>> aides.qa
        qa(6.0)
        >>> model.new2old()
        >>> model.calc_v_qa_v1()
        >>> aides.v
        v(0.0)
        >>> aides.qa
        qa(2.62963)
        >>> model.new2old()
        >>> model.calc_v_qa_v1()
        >>> aides.v
        v(0.0)
        >>> aides.qa
        qa(2.0)

        Note that the results of method |Calc_V_QA_V1| are not based
        depend on the (outer) simulation step size but on the (inner)
        calculation step size defined by parameter `maxdt`.
    """

    DERIVEDPARAMETERS = (
        llake_derived.NmbSubsteps,
        llake_derived.Seconds,
    )
    REQUIREDSEQUENCES = (llake_fluxes.QZ,)
    UPDATEDSEQUENCES = (
        llake_aides.QA,
        llake_aides.V,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        aid = model.sequences.aides.fastaccess
        aid.qa = min(aid.qa, flu.qz + der.nmbsubsteps / der.seconds * aid.v)
        aid.v = max(aid.v + der.seconds / der.nmbsubsteps * (flu.qz - aid.qa), 0.0)


class Interp_W_V1(modeltools.Method):
    """Calculate the actual water stage based on linear interpolation.

    Examples:

        Prepare a model object:

        >>> from hydpy.models.llake import *
        >>> parameterstep('1d')
        >>> simulationstep('12h')

        For the sake of brevity, define a test function:

        >>> def test(*vs):
        ...     for v in vs:
        ...         states.v.new = v
        ...         model.interp_w_v1()
        ...         print(repr(states.v), repr(states.w))

        Define a simple `w`-`v` relationship consisting of three nodes and
        calculate the water stages for different volumes:

        >>> n(3)
        >>> v(0., 2., 4.)
        >>> w(-1., 1., 2.)

        Perform the interpolation for a few test points:

        >>> test(0., .5, 2., 3., 4., 5.)
        v(0.0) w(-1.0)
        v(0.5) w(-0.5)
        v(2.0) w(1.0)
        v(3.0) w(1.5)
        v(4.0) w(2.0)
        v(5.0) w(2.5)

        The reference water stage of the relationship can be selected
        arbitrarily.  Even negative water stages are returned, as is
        demonstrated by the first two calculations.  For volumes outside
        the range of the (`v`,`w`) pairs, the outer two highest pairs are
        used for linear extrapolation.
    """

    CONTROLPARAMETERS = (
        llake_control.N,
        llake_control.V,
        llake_control.W,
    )
    REQUIREDSEQUENCES = (llake_states.V,)
    RESULTSEQUENCES = (llake_states.W,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        new = model.sequences.states.fastaccess_new
        for jdx in range(1, con.n):
            if con.v[jdx] >= new.v:
                break
        new.w = (new.v - con.v[jdx - 1]) * (con.w[jdx] - con.w[jdx - 1]) / (
            con.v[jdx] - con.v[jdx - 1]
        ) + con.w[jdx - 1]


class Interp_V_V1(modeltools.Method):
    """Calculate the actual water volume based on linear interpolation.

    Examples:

        Prepare a model object:

        >>> from hydpy.models.llake import *
        >>> parameterstep('1d')
        >>> simulationstep('12h')

        For the sake of brevity, define a test function:

        >>> def test(*ws):
        ...     for w in ws:
        ...         states.w.new = w
        ...         model.interp_v_v1()
        ...         print(repr(states.w), repr(states.v))

        Define a simple `v`-`w` relationship consisting of three nodes and
        calculate the water stages for different volumes:

        >>> n(3)
        >>> w(-1., 1., 2.)
        >>> v(0., 2., 4.)

        Perform the interpolation for a few test points:

        >>> test(-1., -.5, 1., 1.5, 2., 2.5)
        w(-1.0) v(0.0)
        w(-0.5) v(0.5)
        w(1.0) v(2.0)
        w(1.5) v(3.0)
        w(2.0) v(4.0)
        w(2.5) v(5.0)

        The reference water stage of the relationship can be selected
        arbitrarily, hence even the negative water contained in the given
        example is allowed.  For volumes outside the range of the (`w`,`v`)
        pairs, the outer two highest pairs are used for linear extrapolation.
    """

    CONTROLPARAMETERS = (
        llake_control.N,
        llake_control.V,
        llake_control.W,
    )
    REQUIREDSEQUENCES = (llake_states.W,)
    RESULTSEQUENCES = (llake_states.V,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        new = model.sequences.states.fastaccess_new
        for jdx in range(1, con.n):
            if con.w[jdx] >= new.w:
                break
        new.v = (new.w - con.w[jdx - 1]) * (con.v[jdx] - con.v[jdx - 1]) / (
            con.w[jdx] - con.w[jdx - 1]
        ) + con.v[jdx - 1]


class Corr_DW_V1(modeltools.Method):
    """Adjust the water stage drop to the highest value allowed and correct
    the associated fluxes.

    Note that method |Corr_DW_V1| calls the method `interp_v` of the
    respective application model.  Hence the requirements of the actual
    `interp_v` need to be considered additionally.

    Basic Restriction:
      :math:`W_{old} - W_{new} \\leq MaxDW`

    Examples:

        In preparation for the following examples, define a short simulation
        time period with a simulation step size of 12 hours and initialize
        the required model object:

        >>> from hydpy import pub
        >>> pub.timegrids = '2000.01.01', '2000.01.04', '12h'
        >>> from hydpy.models.llake import *
        >>> parameterstep('1d')
        >>> derived.toy.update()
        >>> derived.seconds.update()

        Select the first half of the second day of January as the simulation
        step relevant for the following examples:

        >>> model.idx_sim = pub.timegrids.init['2000.01.02']

        The following tests are based on method |Interp_V_V1| for the
        interpolation of the stored water volume based on the corrected
        water stage:

        >>> model.interp_v = model.interp_v_v1

        For the sake of simplicity, the underlying `w`-`v` relationship is
        assumed to be linear:

        >>> n(2.)
        >>> w(0., 1.)
        >>> v(0., 1e6)

        The maximum drop in water stage for the first half of the second
        day of January is set to 0.4 m/d.  Note that, due to the difference
        between the parameter step size and the simulation step size, the
        actual value used for calculation is 0.2 m/12h:

        >>> maxdw(_1_1_18=.1,
        ...       _1_2_6=.4,
        ...       _1_2_18=.1)
        >>> maxdw
        maxdw(toy_1_1_18_0_0=0.1,
              toy_1_2_6_0_0=0.4,
              toy_1_2_18_0_0=0.1)
        >>> from hydpy import round_
        >>> round_(maxdw.value[2])
        0.2

        Define old and new water stages and volumes in agreement with the
        given linear relationship:

        >>> states.w.old = 1.
        >>> states.v.old = 1e6
        >>> states.w.new = .9
        >>> states.v.new = 9e5

        Also define an inflow and an outflow value.  Note the that the latter
        is set to zero, which is inconsistent with the actual water stage drop
        defined above, but done for didactic reasons:

        >>> fluxes.qz = 1.
        >>> fluxes.qa = 0.

        Calling the |Corr_DW_V1| method does not change the values of
        either of following sequences, as the actual drop (0.1 m/12h) is
        smaller than the allowed drop (0.2 m/12h):

        >>> model.corr_dw_v1()
        >>> states.w
        w(0.9)
        >>> states.v
        v(900000.0)
        >>> fluxes.qa
        qa(0.0)

        Note that the values given above are not recalculated, which can
        clearly be seen for the lake outflow, which is still zero.

        Through setting the new value of the water stage to 0.6 m, the actual
        drop (0.4 m/12h) exceeds the allowed drop (0.2 m/12h). Hence the
        water stage is trimmed and the other values are recalculated:

        >>> states.w.new = .6
        >>> model.corr_dw_v1()
        >>> states.w
        w(0.8)
        >>> states.v
        v(800000.0)
        >>> fluxes.qa
        qa(5.62963)

        Through setting the maximum water stage drop to zero, method
        |Corr_DW_V1| is effectively disabled.  Regardless of the actual
        change in water stage, no trimming or recalculating is performed:

        >>> maxdw.toy_01_02_06 = 0.
        >>> states.w.new = .6
        >>> model.corr_dw_v1()
        >>> states.w
        w(0.6)
        >>> states.v
        v(800000.0)
        >>> fluxes.qa
        qa(5.62963)
    """

    CONTROLPARAMETERS = (llake_control.MaxDW,)
    DERIVEDPARAMETERS = (
        llake_derived.TOY,
        llake_derived.Seconds,
    )
    REQUIREDSEQUENCES = (llake_fluxes.QZ,)
    UPDATEDSEQUENCES = (
        llake_states.W,
        llake_states.V,
        llake_fluxes.QA,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        old = model.sequences.states.fastaccess_old
        new = model.sequences.states.fastaccess_new
        idx = der.toy[model.idx_sim]
        if (con.maxdw[idx] > 0.0) and ((old.w - new.w) > con.maxdw[idx]):
            new.w = old.w - con.maxdw[idx]
            model.interp_v()
            flu.qa = flu.qz + (old.v - new.v) / der.seconds


class Modify_QA_V1(modeltools.Method):
    """Add water to or remove water from the calculated lake outflow.

    Basic Equation:
      :math:`QA = QA* - Verzw`

    Examples:
        In preparation for the following examples, define a short simulation
        time period with a simulation step size of 12 hours and initialize
        the required model object:

        >>> from hydpy import pub
        >>> pub.timegrids = '2000.01.01', '2000.01.04', '12h'
        >>> from hydpy.models.llake import *
        >>> parameterstep('1d')
        >>> derived.toy.update()

        Select the first half of the second day of January as the simulation
        step relevant for the following examples:

        >>> model.idx_sim = pub.timegrids.init['2000.01.02']

        Assume that, in accordance with previous calculations, the original
        outflow value is 3 m³/s:

        >>> fluxes.qa = 3.0

        Prepare the shape of parameter `verzw` (usually, this is done
        automatically when calling parameter `n`):

        >>> verzw.shape = (None,)

        Set the value of the abstraction on the first half of the second
        day of January to 2 m³/s:

        >>> verzw(_1_1_18=0.0,
        ...       _1_2_6=2.0,
        ...       _1_2_18=0.0)

        In the first example `verzw` is simply subtracted from `qa`:

        >>> model.modify_qa_v1()
        >>> fluxes.qa
        qa(1.0)

        In the second example `verzw` exceeds `qa`, resulting in a zero
        outflow value:

        >>> model.modify_qa_v1()
        >>> fluxes.qa
        qa(0.0)

        The last example demonstrates, that "negative abstractions" are
        allowed, resulting in an increase in simulated outflow:

        >>> verzw.toy_1_2_6 = -2.0
        >>> model.modify_qa_v1()
        >>> fluxes.qa
        qa(2.0)
    """

    CONTROLPARAMETERS = (llake_control.Verzw,)
    DERIVEDPARAMETERS = (llake_derived.TOY,)
    UPDATEDSEQUENCES = (llake_fluxes.QA,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        idx = der.toy[model.idx_sim]
        flu.qa = max(flu.qa - con.verzw[idx], 0.0)


class Pick_Q_V1(modeltools.Method):
    """Update the inlet link sequence.

    Basic equation:
      :math:`QZ = \\sum Q`
    """

    REQUIREDSEQUENCES = (llake_inlets.Q,)
    RESULTSEQUENCES = (llake_fluxes.QZ,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        inl = model.sequences.inlets.fastaccess
        flu.qz = 0.0
        for idx in range(inl.len_q):
            flu.qz += inl.q[idx][0]


class Pass_Q_V1(modeltools.Method):
    """Update the outlet link sequence.

    Basic equation:
      :math:`Q = QA`
    """

    REQUIREDSEQUENCES = (llake_fluxes.QA,)
    RESULTSEQUENCES = (llake_outlets.Q,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        out = model.sequences.outlets.fastaccess
        out.q[0] += flu.qa


class Model(modeltools.AdHocModel):
    """Base model for HydPy-L-Lake."""

    INLET_METHODS = (Pick_Q_V1,)
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        Solve_DV_DT_V1,
        Interp_W_V1,
        Corr_DW_V1,
        Modify_QA_V1,
    )
    ADD_METHODS = (
        Interp_V_V1,
        Calc_VQ_V1,
        Interp_QA_V1,
        Calc_V_QA_V1,
    )
    OUTLET_METHODS = (Pass_Q_V1,)
    SENDER_METHODS = ()
    SUBMODELS = ()
