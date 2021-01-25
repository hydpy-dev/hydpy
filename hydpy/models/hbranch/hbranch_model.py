# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import modeltools
from hydpy.core import objecttools
from hydpy.models.hbranch import hbranch_control
from hydpy.models.hbranch import hbranch_derived
from hydpy.models.hbranch import hbranch_fluxes
from hydpy.models.hbranch import hbranch_inlets
from hydpy.models.hbranch import hbranch_outlets


class Calc_Outputs_V1(modeltools.Method):
    """Performs the actual interpolation or extrapolation.

    Examples:

        As a simple example, assume a weir directing all discharge into
        `branch1` until the capacity limit of 2 m³/s is reached.  The
        discharge exceeding this threshold is directed into `branch2`:

        >>> from hydpy.models.hbranch import *
        >>> parameterstep()
        >>> xpoints(0., 2., 4.)
        >>> ypoints(branch1=[0., 2., 2.],
        ...         branch2=[0., 0., 2.])
        >>> model.parameters.update()

        Low discharge example (linear interpolation between the first two
        supporting point pairs):

        >>> fluxes.input = 1.
        >>> model.calc_outputs_v1()
        >>> fluxes.outputs
        outputs(branch1=1.0,
                branch2=0.0)

        Medium discharge example (linear interpolation between the second
        two supporting point pairs):

        >>> fluxes.input = 3.
        >>> model.calc_outputs_v1()
        >>> print(fluxes.outputs)
        outputs(branch1=2.0,
                branch2=1.0)

        High discharge example (linear extrapolation beyond the second two
        supporting point pairs):

        >>> fluxes.input = 5.
        >>> model.calc_outputs_v1()
        >>> fluxes.outputs
        outputs(branch1=2.0,
                branch2=3.0)

        Non-monotonous relationships and balance violations are allowed,
        e.g.:

        >>> xpoints(0., 2., 4., 6.)
        >>> ypoints(branch1=[0., 2., 0., 0.],
        ...         branch2=[0., 0., 2., 4.])
        >>> model.parameters.update()
        >>> fluxes.input = 7.
        >>> model.calc_outputs_v1()
        >>> fluxes.outputs
        outputs(branch1=0.0,
                branch2=5.0)

    ToDo Technical checks:

        Note that method the name of sequence |Input| causes a false alarm
        here.  It would be best to use a name not in conflict with Pythons's
        |input| statement:

        >>> from hydpy.core.testtools import check_selectedvariables
        >>> from hydpy.models.hbranch.hbranch_model import Calc_Outputs_V1
        >>> print(check_selectedvariables(Calc_Outputs_V1))
        Possibly erroneously selected (REQUIREDSEQUENCES): Input
    """

    CONTROLPARAMETERS = (
        hbranch_control.XPoints,
        hbranch_control.YPoints,
    )
    DERIVEDPARAMETERS = (
        hbranch_derived.NmbPoints,
        hbranch_derived.NmbBranches,
    )
    REQUIREDSEQUENCES = (hbranch_fluxes.Input,)
    RESULTSEQUENCES = (hbranch_fluxes.Outputs,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        # Search for the index of the two relevant x points...
        for pdx in range(1, der.nmbpoints):
            if con.xpoints[pdx] > flu.input:
                break
        # ...and use it for linear interpolation (or extrapolation).
        for bdx in range(der.nmbbranches):
            flu.outputs[bdx] = (flu.input - con.xpoints[pdx - 1]) * (
                con.ypoints[bdx, pdx] - con.ypoints[bdx, pdx - 1]
            ) / (con.xpoints[pdx] - con.xpoints[pdx - 1]) + con.ypoints[bdx, pdx - 1]


class Pick_Input_V1(modeltools.Method):
    """Updates |Input| based on |Total|.

    Basic equation:
      :math:`Input = \\sum Total`

    ToDo Technical checks:

        Note that method the name of sequence |Input| causes a false alarm
        here.  It would be best to use a name not in conflict with Pythons's
        |input| statement:

        >>> from hydpy.core.testtools import check_selectedvariables
        >>> from hydpy.models.hbranch.hbranch_model import Pick_Input_V1
        >>> print(check_selectedvariables(Pick_Input_V1))
        Possibly erroneously selected (RESULTSEQUENCES): Input
    """

    REQUIREDSEQUENCES = (hbranch_inlets.Total,)
    RESULTSEQUENCES = (hbranch_fluxes.Input,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        inl = model.sequences.inlets.fastaccess
        flu.input = 0.0
        for idx in range(inl.len_total):
            flu.input += inl.total[idx][0]


class Pass_Outputs_V1(modeltools.Method):
    """Updates |Branched| based on |Outputs|.

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

    INLET_METHODS = (Pick_Input_V1,)
    RECEIVER_METHODS = ()
    RUN_METHODS = (Calc_Outputs_V1,)
    ADD_METHODS = ()
    OUTLET_METHODS = (Pass_Outputs_V1,)
    SENDER_METHODS = ()
    SUBMODELS = ()

    def __init__(self):
        super().__init__()
        self.nodenames = []

    def connect(self):
        """Connect the |LinkSequence| instances handled by the actual model
        to the |NodeSequence| instances handled by one inlet node and
        multiple oulet nodes.

        The HydPy-H-Branch model passes multiple output values to different
        outlet nodes.  This requires additional information regarding the
        `direction` of each output value.  Therefore, node names are used
        as keywords.  Assume the discharge values of both nodes `inflow1`
        and `inflow2`  shall be  branched to nodes `outflow1` and `outflow2`
        via element `branch`:

        >>> from hydpy import Element
        >>> branch = Element("branch",
        ...                  inlets=["inflow1", "inflow2"],
        ...                  outlets=["outflow1", "outflow2"])

        Then parameter |YPoints| relates different supporting points via
        its keyword arguments to the respective nodes:

        >>> from hydpy.models.hbranch import *
        >>> parameterstep()
        >>> xpoints(0.0, 3.0)
        >>> ypoints(outflow1=[0.0, 1.0], outflow2=[0.0, 2.0])
        >>> parameters.update()

        After connecting the model with its element the total discharge
        value of nodes `inflow1` and `inflow2` can be properly divided:

        >>> branch.model = model
        >>> branch.inlets.inflow1.sequences.sim = 1.0
        >>> branch.inlets.inflow2.sequences.sim = 5.0
        >>> model.simulate(0)
        >>> branch.outlets.outflow1.sequences.sim
        sim(2.0)
        >>> branch.outlets.outflow2.sequences.sim
        sim(4.0)

        In case of missing (or misspelled) outlet nodes, the following
        error is raised:

        >>> branch.outlets.mutable = True
        >>> del branch.outlets.outflow1
        >>> parameters.update()
        >>> model.connect()
        Traceback (most recent call last):
        ...
        RuntimeError: Model `hbranch` of element `branch` tried to connect \
to an outlet node named `outflow1`, which is not an available outlet node \
of element `branch`.
        """
        nodes = self.element.inlets
        total = self.sequences.inlets.total
        if total.shape != (len(nodes),):
            total.shape = len(nodes)
        for idx, node in enumerate(nodes):
            double = node.get_double("inlets")
            total.set_pointer(double, idx)
        for (idx, name) in enumerate(self.nodenames):
            try:
                outlet = getattr(self.element.outlets, name)
            except AttributeError:
                raise RuntimeError(
                    f"Model {objecttools.elementphrase(self)} tried "
                    f"to connect to an outlet node named `{name}`, "
                    f"which is not an available outlet node of element "
                    f"`{self.element.name}`."
                ) from None
            double = outlet.get_double("outlets")
            self.sequences.outlets.branched.set_pointer(double, idx)
