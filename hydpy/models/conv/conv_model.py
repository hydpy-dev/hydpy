# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# imports...
# ...from site-packages
# ...from HydPy
from hydpy.core import devicetools
from hydpy.core import modeltools
from hydpy.core import objecttools
from hydpy.cythons import modelutils
from hydpy.models.conv import conv_control
from hydpy.models.conv import conv_derived
from hydpy.models.conv import conv_fluxes
from hydpy.models.conv import conv_inlets
from hydpy.models.conv import conv_outlets


class Pick_Inputs_V1(modeltools.Method):
    """Pick the input from all inlet nodes."""

    DERIVEDPARAMETERS = (conv_derived.NmbInputs,)
    REQUIREDSEQUENCES = (conv_inlets.Inputs,)
    RESULTSEQUENCES = (conv_fluxes.Inputs,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        inl = model.sequences.inlets.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for idx in range(der.nmbinputs):
            flu.inputs[idx] = inl.inputs[idx][0]


class Calc_Outputs_V1(modeltools.Method):
    """Perform a simple proximity-based interpolation.

    Examples:

        With complete input data, method |Calc_Outputs_V1| performs the
        most simple nearest-neighbour approach:

        >>> from hydpy.models.conv import *
        >>> parameterstep()
        >>> maxnmbinputs.value = 1
        >>> derived.nmboutputs(3)
        >>> derived.proximityorder.shape = (3, 1)
        >>> derived.proximityorder([[0], [1], [0]])
        >>> fluxes.inputs.shape = 2
        >>> fluxes.inputs = 1.0, 2.0
        >>> model.calc_outputs_v1()
        >>> fluxes.outputs
        outputs(1.0, 2.0, 1.0)

        With incomplete data, it subsequently checks the second-nearest
        location, the third-nearest location, and so on, until it finds
        an actual value.  Parameter |MaxNmbInputs| defines the maximum
        number of considered locations:

        >>> fluxes.inputs = 1.0, nan
        >>> model.calc_outputs_v1()
        >>> fluxes.outputs
        outputs(1.0, nan, 1.0)

        >>> maxnmbinputs.value = 2
        >>> derived.proximityorder.shape = (3, 2)
        >>> derived.proximityorder([[0, 1], [1, 0], [0, 1]])
        >>> model.calc_outputs_v1()
        >>> fluxes.outputs
        outputs(1.0, 1.0, 1.0)
    """

    CONTROLPARAMETERS = (conv_control.MaxNmbInputs,)
    DERIVEDPARAMETERS = (
        conv_derived.NmbOutputs,
        conv_derived.ProximityOrder,
    )
    REQUIREDSEQUENCES = (conv_fluxes.Inputs,)
    RESULTSEQUENCES = (conv_fluxes.Outputs,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for idx_out in range(der.nmboutputs):
            for idx_try in range(con.maxnmbinputs):
                idx_in = der.proximityorder[idx_out, idx_try]
                flu.outputs[idx_out] = flu.inputs[idx_in]
                if not modelutils.isnan(flu.outputs[idx_out]):
                    break


class Calc_Outputs_V2(modeltools.Method):
    """Perform a simple inverse distance weighted interpolation.

    Examples:

        With complete input data, method |Calc_Outputs_V2| performs the
        most simple inverse distance weighted approach:

        >>> from hydpy.models.conv import *
        >>> parameterstep()

        >>> maxnmbinputs.value = 4
        >>> derived.nmboutputs(3)
        >>> derived.proximityorder.shape = 3, 4
        >>> derived.proximityorder([[0, 2, 1, 3],
        ...                         [1, 0, 2, 3],
        ...                         [0, 2, 1, 3]])
        >>> derived.weights.shape = 3, 4
        >>> derived.weights([[inf, inf, 0.05, 0.000053],
        ...                  [0.5, 0.029412, 0.029412, 0.000052],
        ...                  [0.5, 0.5, 0.1, 0.000053]])

        >>> fluxes.inputs.shape = 4
        >>> fluxes.inputs = 1.0, 5.0, 3.0, 6.0
        >>> model.calc_outputs_v2()
        >>> fluxes.outputs
        outputs(2.0, 4.684331, 2.272907)

        With incomplete data, it subsequently skips all missing values.
        Parameter |MaxNmbInputs| defines the maximum number of considered
        locations:

        >>> fluxes.inputs = nan, 5.0, nan, 6.0
        >>> model.calc_outputs_v2()
        >>> fluxes.outputs
        outputs(5.001059, 5.000104, 5.00053)

        With just one considered location, method |Calc_Outputs_V2|
        calculates the same results as the nearest-neighbour approach
        implemented by method |Calc_Outputs_V1|:

        >>> maxnmbinputs.value = 1
        >>> derived.proximityorder.shape = 3, 1
        >>> derived.proximityorder([[0],
        ...                         [1],
        ...                         [0]])
        >>> derived.weights.shape = 3, 1
        >>> derived.weights([[inf],
        ...                  [0.5],
        ...                  [0.5]])
        >>> model.calc_outputs_v2()
        >>> fluxes.outputs
        outputs(nan, 5.0, nan)
    """

    CONTROLPARAMETERS = (conv_control.MaxNmbInputs,)
    DERIVEDPARAMETERS = (
        conv_derived.NmbOutputs,
        conv_derived.ProximityOrder,
        conv_derived.Weights,
    )
    REQUIREDSEQUENCES = (conv_fluxes.Inputs,)
    RESULTSEQUENCES = (conv_fluxes.Outputs,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for idx_out in range(der.nmboutputs):
            d_sumweights = 0.0
            d_sumvalues = 0.0
            d_sumvalues_inf = 0.0
            counter_inf = 0
            for idx_try in range(con.maxnmbinputs):
                idx_in = der.proximityorder[idx_out, idx_try]
                if not modelutils.isnan(flu.inputs[idx_in]):
                    if modelutils.isinf(der.weights[idx_out, idx_try]):
                        d_sumvalues_inf += flu.inputs[idx_in]
                        counter_inf += 1
                    else:
                        d_sumweights += der.weights[idx_out, idx_try]
                        d_sumvalues += (
                            der.weights[idx_out, idx_try] * flu.inputs[idx_in]
                        )
            if counter_inf:
                flu.outputs[idx_out] = d_sumvalues_inf / counter_inf
            elif d_sumweights:
                flu.outputs[idx_out] = d_sumvalues / d_sumweights
            else:
                flu.outputs[idx_out] = modelutils.nan


class Pass_Outputs_V1(modeltools.Method):
    """Pass the output to all outlet nodes."""

    DERIVEDPARAMETERS = (conv_derived.NmbOutputs,)
    REQUIREDSEQUENCES = (conv_fluxes.Outputs,)
    RESULTSEQUENCES = (conv_outlets.Outputs,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        out = model.sequences.outlets.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for idx in range(der.nmboutputs):
            out.outputs[idx][0] = flu.outputs[idx]


class Model(modeltools.AdHocModel):
    """The HydPy-Conv model."""

    INLET_METHODS = (Pick_Inputs_V1,)
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        Calc_Outputs_V1,
        Calc_Outputs_V2,
    )
    ADD_METHODS = ()
    OUTLET_METHODS = (Pass_Outputs_V1,)
    SENDER_METHODS = ()
    SUBMODELS = ()

    def connect(self):
        """Connect the |InletSequence| and |OutletSequence| objects of
        the actual model to the |NodeSequence| objects handled by an
        arbitrary number of inlet and outlet nodes.

        To application models derived from |conv_model.Model|, you first
        need to define an |Element| connected with an arbitrary number of
        inlet and outlet nodes:

        >>> from hydpy import Element
        >>> conv = Element("conv",
        ...                inlets=["in1", "in2"],
        ...                outlets=["out1", "out2", "out3"])

        Second, you must define the coordinates of the inlet and outlet
        nodes via parameter |InputCoordinates| and |OutputCoordinates|,
        respectively.  In both cases, use the names of the |Node| objects
        as keyword arguments to pass the corresponding coordinates:

        >>> from hydpy.models.conv_v001 import *
        >>> parameterstep()
        >>> inputcoordinates(
        ...     in1=(0.0, 3.0),
        ...     in2=(2.0, -1.0))
        >>> outputcoordinates(
        ...     out1=(0.0, 3.0),
        ...     out2=(3.0, -2.0),
        ...     out3=(1.0, 2.0))
        >>> maxnmbinputs()
        >>> parameters.update()

        |conv| passes the current values of the inlet nodes correctly to
        the outlet nodes (note that node `in1` works with simulated values
        while node `in2` works with observed values, as we set its
        |Node.deploymode| to `obs`):

        >>> conv.model = model
        >>> conv.inlets.in1.sequences.sim = 1.0
        >>> conv.inlets.in2.deploymode = "obs"
        >>> conv.inlets.in2.sequences.obs = 2.0
        >>> model.simulate(0)
        >>> conv.outlets.out1.sequences.sim
        sim(1.0)
        >>> conv.outlets.out2.sequences.sim
        sim(2.0)
        >>> conv.outlets.out3.sequences.sim
        sim(1.0)

        When you forget a node (or misspell its name), you get the
        following error message:

        >>> outputcoordinates(
        ...     out1=(0.0, 3.0),
        ...     out2=(3.0, -2.0))
        >>> maxnmbinputs()
        >>> parameters.update()
        >>> conv.model = model
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to connect model `conv_v001` of element \
`conv`, the following error occurred: The node handled by control parameter \
outputcoordinates (out1 and out2) are not the same as the outlet nodes \
handled by element conv (out1, out2, and out3).
        """
        try:
            for coordinates, sequence, nodes in (
                (
                    self.parameters.control.inputcoordinates,
                    self.sequences.inlets.inputs,
                    self.element.inlets,
                ),
                (
                    self.parameters.control.outputcoordinates,
                    self.sequences.outlets.outputs,
                    self.element.outlets,
                ),
            ):
                if nodes == devicetools.Nodes(coordinates.nodes):
                    sequence.shape = len(coordinates)
                    for idx, node in enumerate(coordinates.nodes):
                        sequence.set_pointer(
                            node.get_double(sequence.subseqs.name), idx
                        )
                else:
                    parameternodes = objecttools.enumeration(coordinates.nodes)
                    elementnodes = objecttools.enumeration(nodes)
                    raise RuntimeError(
                        f"The node handled by control parameter "
                        f"{coordinates.name} ({parameternodes}) are not the "
                        f"same as the {sequence.subseqs.name[:-1]} nodes "
                        f"handled by element {self.element.name} "
                        f"({elementnodes})."
                    )
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to connect model " f"{objecttools.elementphrase(self)}"
            )
