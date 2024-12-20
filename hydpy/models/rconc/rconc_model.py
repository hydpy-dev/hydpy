# pylint: disable=missing-module-docstring
# imports...
# ...from standard library
# ...from HydPy
from hydpy.core import modeltools
from hydpy.core.typingtools import *
from hydpy.cythons import modelutils
from hydpy.models.rconc import rconc_control
from hydpy.models.rconc import rconc_derived
from hydpy.models.rconc import rconc_fluxes
from hydpy.models.rconc import rconc_logs
from hydpy.models.rconc import rconc_states


class Determine_Outflow_V1(modeltools.Method):
    r"""Calculate the unit hydrograph output (convolution).

    Examples:

        Prepare a unit hydrograph with only three ordinates representing a fast
        catchment response compared to the selected simulation step size:

        >>> from hydpy.models.rconc import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> control.uh.shape = 3
        >>> control.uh = 0.3, 0.5, 0.2
        >>> logs.quh.shape = 3
        >>> logs.quh = 1.0, 3.0, 0.0

        Without new input, the actual output is simply the first value stored in the
        logging sequence and the values of the logging sequence shift to the left:

        >>> fluxes.inflow = 0.0
        >>> model.determine_outflow_v1()
        >>> fluxes.outflow
        outflow(1.0)
        >>> logs.quh
        quh(3.0, 0.0, 0.0)

        With a new input of 4 mm, the actual output consists of the first value stored
        in the logging sequence and the input value multiplied with the first unit
        hydrograph ordinate.  The updated logging sequence values result from
        multiplying input values and the remaining ordinates:

        >>> fluxes.inflow = 4.0
        >>> model.determine_outflow_v1()
        >>> fluxes.outflow
        outflow(4.2)
        >>> logs.quh
        quh(2.0, 0.8, 0.0)

        The following example demonstrates the updating of a non-empty logging
        sequence:

        >>> fluxes.inflow = 4.0
        >>> model.determine_outflow_v1()
        >>> fluxes.outflow
        outflow(3.2)
        >>> logs.quh
        quh(2.8, 0.8, 0.0)

        A unit hydrograph consisting of one ordinate routes the received input
        directly:

        >>> control.uh.shape = 1
        >>> control.uh = 1.0
        >>> fluxes.inflow = 0.0
        >>> logs.quh.shape = 1
        >>> logs.quh = 0.0
        >>> model.determine_outflow_v1()
        >>> fluxes.outflow
        outflow(0.0)
        >>> logs.quh
        quh(0.0)
        >>> fluxes.inflow = 4.0
        >>> model.determine_outflow_v1()
        >>> fluxes.outflow
        outflow(4.0)
        >>> logs.quh
        quh(0.0)
    """

    CONTROLPARAMETERS = (rconc_control.UH,)
    DERIVEDPARAMETERS = ()
    REQUIREDSEQUENCES = (rconc_fluxes.Inflow,)
    UPDATEDSEQUENCES = (rconc_logs.QUH,)
    RESULTSEQUENCES = (rconc_fluxes.Outflow,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        flu.outflow = con.uh[0] * flu.inflow + log.quh[0]
        for jdx in range(1, len(con.uh)):
            log.quh[jdx - 1] = con.uh[jdx] * flu.inflow + log.quh[jdx]


class Determine_Outflow_V2(modeltools.Method):
    r"""Calculate the linear storage cascade output (state-space approach).

    Basic equations:
        :math:`Outflow = KSC \cdot SC`

        :math:`\frac{dSC}{dt} = Inflow - Outflow`

    Note that the given base equations only hold for one single linear storage, while
    |Determine_Outflow_V2| supports a cascade of linear storages.  Also, the equations
    do not reflect the possibility of increasing numerical accuracy by decreasing the
    internal simulation step size.

    Examples:

        If the number of storages is zero, |Determine_Outflow_V2| routes the received
        input directly:

        >>> from hydpy.models.rconc import *
        >>> simulationstep("1d")
        >>> parameterstep("1d")
        >>> nmbstorages(0)
        >>> fluxes.inflow = 2.0
        >>> model.determine_outflow_v2()
        >>> fluxes.outflow
        outflow(2.0)

        We solve the underlying ordinary differential equation via the explicit Euler
        method.  Nevertheless, defining arbitrarily high storage coefficients does not
        pose any stability problems due to truncating too-high outflow values:

        >>> control.nmbsteps(1)
        >>> derived.dt.update()
        >>> nmbstorages(5)
        >>> derived.ksc(inf)
        >>> model.determine_outflow_v2()
        >>> fluxes.outflow
        outflow(2.0)

        Increasing the number of internal calculation steps via parameter |NmbSteps|
        results in higher numerical accuracy without violating the water balance:

        >>> derived.ksc(2.0)
        >>> states.sc = 0.0
        >>> model.determine_outflow_v2()
        >>> fluxes.outflow
        outflow(2.0)
        >>> states.sc
        sc(0.0, 0.0, 0.0, 0.0, 0.0)

        >>> control.nmbsteps(10)
        >>> derived.dt.update()
        >>> states.sc = 0.0
        >>> model.determine_outflow_v2()
        >>> fluxes.outflow
        outflow(0.084262)
        >>> states.sc
        sc(0.714101, 0.542302, 0.353323, 0.202141, 0.103872)
        >>> from hydpy import round_
        >>> round_(fluxes.outflow + sum(states.sc))
        2.0

        >>> control.nmbsteps(100)
        >>> derived.dt.update()
        >>> states.sc = 0.0
        >>> model.determine_outflow_v2()
        >>> fluxes.outflow
        outflow(0.026159)
        >>> states.sc
        sc(0.850033, 0.590099, 0.327565, 0.149042, 0.057103)
        >>> round_(fluxes.outflow + sum(states.sc))
        2.0
    """

    CONTROLPARAMETERS = (rconc_control.NmbStorages, rconc_control.NmbSteps)
    DERIVEDPARAMETERS = (rconc_derived.DT, rconc_derived.KSC)
    REQUIREDSEQUENCES = (rconc_fluxes.Inflow,)
    UPDATEDSEQUENCES = (rconc_states.SC,)
    RESULTSEQUENCES = (rconc_fluxes.Outflow,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        sta = model.sequences.states.fastaccess
        if (con.nmbstorages == 0) or modelutils.isinf(der.ksc):
            flu.outflow = flu.inflow
        else:
            flu.outflow = 0.0
            for _ in range(con.nmbsteps):
                sta.sc[0] += der.dt * flu.inflow
                for j in range(con.nmbstorages - 1):
                    d_q = min(der.dt * der.ksc * sta.sc[j], sta.sc[j])
                    sta.sc[j] -= d_q
                    sta.sc[j + 1] += d_q
                j = con.nmbstorages - 1
                d_q = min(der.dt * der.ksc * sta.sc[j], sta.sc[j])
                sta.sc[j] -= d_q
                flu.outflow += d_q


class Set_Inflow_V1(modeltools.Method):
    """Set the runoff concentration input in mm/T."""

    RESULTSEQUENCES = (rconc_fluxes.Inflow,)

    @staticmethod
    def __call__(model: modeltools.Model, inflow: float) -> None:
        flu = model.sequences.fluxes.fastaccess
        flu.inflow = inflow


class Get_Outflow_V1(modeltools.Method):
    """Get the previously calculated runoff concentration output in mm/T.

    Example:

        >>> from hydpy.models.rconc import *
        >>> parameterstep("1d")
        >>> simulationstep("12h")
        >>> retentiontime(3.0)
        >>> fluxes.outflow = 2.0
        >>> model.get_outflow_v1()
        2.0
    """

    REQUIREDSEQUENCES = (rconc_fluxes.Outflow,)

    @staticmethod
    def __call__(model: modeltools.Model) -> float:
        flu = model.sequences.fluxes.fastaccess

        return flu.outflow


class Model(modeltools.AdHocModel):
    """|rconc.DOCNAME.complete|."""

    DOCNAME = modeltools.DocName(short="Rconc")
    __HYDPY_ROOTMODEL__ = False

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = ()
    INTERFACE_METHODS = (
        Set_Inflow_V1,
        Determine_Outflow_V1,
        Determine_Outflow_V2,
        Get_Outflow_V1,
    )
    ADD_METHODS = ()
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()


class Sub_RConcModel(modeltools.AdHocModel):
    """Base class for submodels that comply with the submodel interfaces defined in
    module |rconcinterfaces|."""
