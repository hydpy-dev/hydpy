# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import modeltools
from hydpy.core import objecttools
from hydpy.core.typingtools import *
from hydpy.models.hbranch import hbranch_control
from hydpy.models.hbranch import hbranch_derived
from hydpy.models.hbranch import hbranch_fluxes
from hydpy.models.hbranch import hbranch_inlets
from hydpy.models.hbranch import hbranch_outlets


class Pick_OriginalInput_V1(modeltools.Method):
    r"""Update |OriginalInput| based on |Total|.

    Basic equation:
      :math:`OriginalInput = \sum Total`
    """

    REQUIREDSEQUENCES = (hbranch_inlets.Total,)
    RESULTSEQUENCES = (hbranch_fluxes.OriginalInput,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        inl = model.sequences.inlets.fastaccess
        flu.originalinput = 0.0
        for idx in range(inl.len_total):
            flu.originalinput += inl.total[idx][0]


class Calc_AdjustedInput_V1(modeltools.Method):
    """Adjust the original input data.

    Basic equation:
        :math:`AdjustedInput = max(OriginalInput + Delta, Minimum)`

    Examples:

        The degree of the input adjustment may vary monthly.  Hence, we need to define
        a concrete initialisation period for the following examples:

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-03-30", "2000-04-03", "1d"
        >>> from hydpy.models.hbranch import *
        >>> parameterstep()
        >>> derived.moy.update()

        Negative |Delta| values correspond to decreasing input:

        >>> delta.mar = -1.0
        >>> minimum(0.0)
        >>> model.idx_sim = pub.timegrids.init["2000-03-31"]
        >>> fluxes.originalinput = 1.5
        >>> model.calc_adjustedinput_v1()
        >>> fluxes.adjustedinput
        adjustedinput(0.5)

        The adjusted input values are never smaller than the threshold value defined
        by parameter |Minimum|:

        >>> minimum(1.0)
        >>> model.calc_adjustedinput_v1()
        >>> fluxes.adjustedinput
        adjustedinput(1.0)

        Positive |Delta| values correspond to increasing input:

        >>> model.idx_sim = pub.timegrids.init["2000-04-01"]
        >>> delta.apr = 1.0
        >>> fluxes.originalinput = 0.5
        >>> model.calc_adjustedinput_v1()
        >>> fluxes.adjustedinput
        adjustedinput(1.5)
    """

    CONTROLPARAMETERS = (hbranch_control.Delta, hbranch_control.Minimum)
    DERIVEDPARAMETERS = (hbranch_derived.MOY,)
    REQUIREDSEQUENCES = (hbranch_fluxes.OriginalInput,)
    RESULTSEQUENCES = (hbranch_fluxes.AdjustedInput,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.adjustedinput = flu.originalinput + con.delta[der.moy[model.idx_sim]]
        flu.adjustedinput = max(flu.adjustedinput, con.minimum)


class Calc_Outputs_V1(modeltools.Method):
    """Perform the actual interpolation or extrapolation.

    Examples:

        As a simple example, assume a weir directing all discharge into `branch1` until
        reaching the capacity limit of 2 m³/s.  |hbranch_v1| redirects the discharge
        exceeding this threshold to `branch2`:

        >>> from hydpy.models.hbranch import *
        >>> parameterstep()
        >>> xpoints(0.0, 2.0, 4.0)
        >>> ypoints(branch1=[0.0, 2.0, 2.0],
        ...         branch2=[0.0, 0.0, 2.0])
        >>> derived.nmbbranches.update()
        >>> derived.nmbpoints.update()

        Low discharge example (linear interpolation between the first two supporting
        point pairs):

        >>> fluxes.adjustedinput = 1.
        >>> model.calc_outputs_v1()
        >>> fluxes.outputs
        outputs(branch1=1.0,
                branch2=0.0)

        Medium discharge example (linear interpolation between the second two
        supporting point pairs):

        >>> fluxes.adjustedinput = 3.0
        >>> model.calc_outputs_v1()
        >>> print(fluxes.outputs)
        outputs(branch1=2.0,
                branch2=1.0)

        High discharge example (linear extrapolation beyond the second two supporting
        point pairs):

        >>> fluxes.adjustedinput = 5.0
        >>> model.calc_outputs_v1()
        >>> fluxes.outputs
        outputs(branch1=2.0,
                branch2=3.0)

        Non-monotonous relationships and balance violations are allowed:

        >>> xpoints(0.0, 2.0, 4.0, 6.0)
        >>> ypoints(branch1=[0.0, 2.0, 0.0, 0.0],
        ...         branch2=[0.0, 0.0, 2.0, 4.0])
        >>> derived.nmbbranches.update()
        >>> derived.nmbpoints.update()
        >>> fluxes.adjustedinput = 7.0
        >>> model.calc_outputs_v1()
        >>> fluxes.outputs
        outputs(branch1=0.0,
                branch2=5.0)
    """

    CONTROLPARAMETERS = (hbranch_control.XPoints, hbranch_control.YPoints)
    DERIVEDPARAMETERS = (hbranch_derived.NmbPoints, hbranch_derived.NmbBranches)
    REQUIREDSEQUENCES = (hbranch_fluxes.AdjustedInput,)
    RESULTSEQUENCES = (hbranch_fluxes.Outputs,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        # Search for the index of the two relevant x points...
        for pdx in range(1, der.nmbpoints):
            if con.xpoints[pdx] > flu.adjustedinput:
                break
        # ...and use it for linear interpolation (or extrapolation).
        d_x = flu.adjustedinput
        for bdx in range(der.nmbbranches):
            d_x0 = con.xpoints[pdx - 1]
            d_dx = con.xpoints[pdx] - d_x0
            d_y0 = con.ypoints[bdx, pdx - 1]
            d_dy = con.ypoints[bdx, pdx] - d_y0
            flu.outputs[bdx] = (d_x - d_x0) * d_dy / d_dx + d_y0


class Pass_Outputs_V1(modeltools.Method):
    """Update |Branched| based on |Outputs|.

    Basic equation:
      :math:`Branched_i = Outputs_i`
    """

    DERIVEDPARAMETERS = (hbranch_derived.NmbBranches,)
    REQUIREDSEQUENCES = (hbranch_fluxes.Outputs,)
    RESULTSEQUENCES = (hbranch_outlets.Branched,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        out = model.sequences.outlets.fastaccess
        for bdx in range(der.nmbbranches):
            out.branched[bdx][0] += flu.outputs[bdx]


class Model(modeltools.AdHocModel):
    """The HydPy-H-Branch model."""

    INLET_METHODS = (Pick_OriginalInput_V1,)
    RECEIVER_METHODS = ()
    RUN_METHODS = (Calc_AdjustedInput_V1, Calc_Outputs_V1)
    ADD_METHODS = ()
    OUTLET_METHODS = (Pass_Outputs_V1,)
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()

    nodenames: list[str]
    """Names of the output nodes."""

    def __init__(self) -> None:
        super().__init__()
        self.nodenames = []

    def connect(self) -> None:
        """Connect the |LinkSequence| instances handled by the actual model to the
        |NodeSequence| instances handled by one inlet node and multiple oulet nodes.

        The HydPy-H-Branch model passes multiple output values to different outlet
        nodes.  This requires additional information regarding the `direction` of each
        output value.  Therefore, node names are used as keywords.  Assume the
        discharge values of both nodes `inflow1` and `inflow2`  shall be  branched to
        nodes `outflow1` and `outflow2` via element `branch`:

        >>> from hydpy import Element, pub
        >>> branch = Element("branch",
        ...                  inlets=["inflow1", "inflow2"],
        ...                  outlets=["outflow1", "outflow2"])

        Then parameter |YPoints| relates different supporting points via its keyword
        arguments to the respective nodes:

        >>> pub.timegrids = "2000-01-01", "2000-01-02", "1d"
        >>> from hydpy.models.hbranch import *
        >>> parameterstep()
        >>> delta(0.0)
        >>> xpoints(0.0, 3.0)
        >>> ypoints(outflow1=[0.0, 1.0], outflow2=[0.0, 2.0])
        >>> parameters.update()

        After connecting the model with its element the total discharge value of nodes
        `inflow1` and `inflow2` can be properly divided:

        >>> branch.model = model
        >>> branch.inlets.inflow1.sequences.sim = 1.0
        >>> branch.inlets.inflow2.sequences.sim = 5.0
        >>> model.simulate(0)
        >>> branch.outlets.outflow1.sequences.sim
        sim(2.0)
        >>> branch.outlets.outflow2.sequences.sim
        sim(4.0)

        In case of missing (or misspelled) outlet nodes, the following error is raised:

        >>> branch.outlets.remove_device(branch.outlets.outflow1, force=True)
        >>> parameters.update()
        >>> model.connect()
        Traceback (most recent call last):
        ...
        RuntimeError: Model `hbranch` of element `branch` tried to connect to an \
outlet node named `outflow1`, which is not an available outlet node of element `branch`.
        """
        nodes = self.element.inlets
        total = self.sequences.inlets.total
        if total.shape != (len(nodes),):
            total.shape = len(nodes)
        for idx, node in enumerate(nodes):
            double = node.get_double("inlets")
            total.set_pointer(double, idx)
        for idx, name in enumerate(self.nodenames):
            try:
                outlet = getattr(self.element.outlets, name)
            except AttributeError:
                raise RuntimeError(
                    f"Model {objecttools.elementphrase(self)} tried to connect to an "
                    f"outlet node named `{name}`, which is not an available outlet "
                    f"node of element `{self.element.name}`."
                ) from None
            double = outlet.get_double("outlets")
            self.sequences.outlets.branched.set_pointer(double, idx)
