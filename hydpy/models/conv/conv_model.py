# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# imports...
# ...from site-packages
# ...from HydPy
from hydpy.core import devicetools
from hydpy.core import modeltools
from hydpy.core import objecttools
from hydpy.core.typingtools import *
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


class Return_Mean_V1(modeltools.Method):
    """Return the arithmetic mean value for the given vector.

    Examples:

        Method |Return_Mean_V1| requires two vectors and one integer value.  The
        first vector (in the following examples: |conv_fluxes.Inputs|)  handles the
        data to be averaged.  The second vector (|conv_fluxes.Outputs|) serves as
        a mask.  Method |Return_Mean_V1| takes only those vector positions into
        account, where the value of the mask vector is not |numpy.nan|. The integer
        value defines the length of both vectors:

        >>> from hydpy.models.conv import *
        >>> parameterstep()
        >>> fluxes.inputs.shape = 3
        >>> fluxes.outputs.shape = 3
        >>> fluxes.inputs = 0.0, 1.0, 5.0
        >>> fluxes.outputs = 9.9, 9.9, 9.9
        >>> model.return_mean_v1(fluxes.inputs.values, fluxes.outputs.values, 3)
        2.0
        >>> fluxes.outputs = nan, 9.9, nan
        >>> model.return_mean_v1(fluxes.inputs.values, fluxes.outputs.values, 3)
        1.0
        >>> fluxes.outputs = nan, nan, nan
        >>> model.return_mean_v1(fluxes.inputs.values, fluxes.outputs.values, 3)
        nan
    """

    @staticmethod
    def __call__(
        model: modeltools.Model,
        values: Vector[float],
        mask: Vector[float],
        number: int,
    ) -> float:
        counter = 0
        d_result = 0.0
        for idx in range(number):
            if not modelutils.isnan(mask[idx]):
                counter += 1
                d_result += values[idx]
        if counter > 0:
            return d_result / counter
        return modelutils.nan


class Calc_ActualConstant_ActualFactor_V1(modeltools.Method):
    """Calculate the linear regression coefficients |ActualConstant| and
    |ActualFactor| for modelling the relationship between |conv_fluxes.Inputs|
    (dependent variable) and |Heights| (independent variable).

    Examples:

        First, we calculate both regression coefficients for a small data set
        consisting of only three data points:

        >>> from hydpy.models.conv import *
        >>> parameterstep()
        >>> inputheights.shape = 3
        >>> inputheights.values = 1.0, 2.0, 3.0
        >>> minnmbinputs(3)
        >>> derived.nmbinputs(3)
        >>> fluxes.inputs = 2.0, 3.0, 5.0
        >>> model.calc_actualconstant_actualfactor_v1()
        >>> fluxes.actualconstant
        actualconstant(0.333333)
        >>> fluxes.actualfactor
        actualfactor(1.5)

        In the last example, the required number of data points (|MinNmbInputs|)
        exactly agrees with the available number of data points.  In the next
        example, we insert a |numpy.nan| value into the |conv_fluxes.Inputs|
        array to reduce the number of available data points to two.  Then,
        |Calc_ActualConstant_ActualFactor_V1| falls back to the default values
        provided by the control parameters |DefaultConstant| and |DefaultFactor|:

        >>> fluxes.inputs = 2.0, nan, 5.0
        >>> defaultconstant(0.0)
        >>> defaultfactor(1.0)
        >>> model.calc_actualconstant_actualfactor_v1()
        >>> fluxes.actualconstant
        actualconstant(0.0)
        >>> fluxes.actualfactor
        actualfactor(1.0)

        If we lower our data requirements, method |Calc_ActualConstant_ActualFactor_V1|
        uses the remaining two data points to calculate the coefficients:

        >>> minnmbinputs(2)
        >>> model.calc_actualconstant_actualfactor_v1()
        >>> fluxes.actualconstant
        actualconstant(0.5)
        >>> fluxes.actualfactor
        actualfactor(1.5)

        The following two examples deal with a perfect and a non-existing linear
        relationship:

        >>> fluxes.inputs = 2.0, 4.0, 6.0
        >>> model.calc_actualconstant_actualfactor_v1()
        >>> fluxes.actualconstant
        actualconstant(0.0)
        >>> fluxes.actualfactor
        actualfactor(2.0)

        >>> fluxes.inputs = 1.0, 4.0, 1.0
        >>> model.calc_actualconstant_actualfactor_v1()
        >>> fluxes.actualconstant
        actualconstant(2.0)
        >>> fluxes.actualfactor
        actualfactor(0.0)

        In case all values of the independent variable are the same, method
        |Calc_ActualConstant_ActualFactor_V1| again uses the provided default values:

        >>> inputheights.values = 1.0, 1.0, 1.0
        >>> model.calc_actualconstant_actualfactor_v1()
        >>> fluxes.actualconstant
        actualconstant(0.0)
        >>> fluxes.actualfactor
        actualfactor(1.0)
    """

    CONTROLPARAMETERS = (
        conv_control.InputHeights,
        conv_control.MinNmbInputs,
        conv_control.DefaultConstant,
        conv_control.DefaultFactor,
    )
    DERIVEDPARAMETERS = (conv_derived.NmbInputs,)
    REQUIREDSEQUENCES = (conv_fluxes.Inputs,)
    RESULTSEQUENCES = (
        conv_fluxes.ActualConstant,
        conv_fluxes.ActualFactor,
    )

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        counter = 0
        for idx in range(der.nmbinputs):
            if not modelutils.isnan(flu.inputs[idx]):
                counter += 1
                if counter == con.minnmbinputs:
                    break
        else:
            flu.actualfactor = con.defaultfactor
            flu.actualconstant = con.defaultconstant
            return
        d_mean_height = model.return_mean_v1(
            con.inputheights, flu.inputs, der.nmbinputs
        )
        d_mean_inputs = model.return_mean_v1(flu.inputs, flu.inputs, der.nmbinputs)
        d_nominator = 0.0
        d_denominator = 0.0
        for idx in range(der.nmbinputs):
            if not modelutils.isnan(flu.inputs[idx]):
                d_temp = con.inputheights[idx] - d_mean_height
                d_nominator += d_temp * (flu.inputs[idx] - d_mean_inputs)
                d_denominator += d_temp * d_temp
        if d_denominator > 0.0:
            flu.actualfactor = d_nominator / d_denominator
            flu.actualconstant = d_mean_inputs - flu.actualfactor * d_mean_height
        else:
            flu.actualfactor = con.defaultfactor
            flu.actualconstant = con.defaultconstant
        return


class Calc_InputPredictions_V1(modeltools.Method):
    r"""Predict the values of the input nodes based on a linear model.

    Basic equation:
       :math:`InputPredictions = ActualConstant + ActualFactor \cdot InputHeights`

    Example:

        >>> from hydpy.models.conv import *
        >>> parameterstep()
        >>> inputheights.shape = 2
        >>> inputheights.values = 1.0, 2.0
        >>> derived.nmbinputs(2)
        >>> fluxes.actualconstant(1.0)
        >>> fluxes.actualfactor(2.0)
        >>> model.calc_inputpredictions_v1()
        >>> fluxes.inputpredictions
        inputpredictions(3.0, 5.0)
    """

    CONTROLPARAMETERS = (conv_control.InputHeights,)
    DERIVEDPARAMETERS = (conv_derived.NmbInputs,)
    REQUIREDSEQUENCES = (
        conv_fluxes.ActualConstant,
        conv_fluxes.ActualFactor,
    )
    RESULTSEQUENCES = (conv_fluxes.InputPredictions,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for idx in range(der.nmbinputs):
            flu.inputpredictions[idx] = (
                flu.actualconstant + flu.actualfactor * con.inputheights[idx]
            )


class Calc_OutputPredictions_V1(modeltools.Method):
    r"""Predict the values of the output nodes based on a linear model.

    Basic equation:
       :math:`OutputPredictions = ActualConstant + ActualFactor \cdot OutputHeights`

    Example:

        >>> from hydpy.models.conv import *
        >>> parameterstep()
        >>> outputheights.shape = 2
        >>> outputheights.values = 1.0, 2.0
        >>> derived.nmboutputs(2)
        >>> fluxes.actualconstant(1.0)
        >>> fluxes.actualfactor(2.0)
        >>> model.calc_outputpredictions_v1()
        >>> fluxes.outputpredictions
        outputpredictions(3.0, 5.0)
    """

    CONTROLPARAMETERS = (conv_control.OutputHeights,)
    DERIVEDPARAMETERS = (conv_derived.NmbOutputs,)
    REQUIREDSEQUENCES = (
        conv_fluxes.ActualConstant,
        conv_fluxes.ActualFactor,
    )
    RESULTSEQUENCES = (conv_fluxes.OutputPredictions,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for idx in range(der.nmboutputs):
            flu.outputpredictions[idx] = (
                flu.actualconstant + flu.actualfactor * con.outputheights[idx]
            )


class Calc_InputResiduals_V1(modeltools.Method):
    r"""Determine the residuals at the input nodes.

    Basic equation:
       :math:`InputResiduals = Inputs - InputPredictions`

    Example:

        >>> from hydpy.models.conv import *
        >>> parameterstep()
        >>> derived.nmbinputs(2)
        >>> fluxes.inputs = 1.0, 2.0
        >>> fluxes.inputpredictions = 0.0, 4.0
        >>> model.calc_inputresiduals_v1()
        >>> fluxes.inputresiduals
        inputresiduals(1.0, -2.0)
    """

    CONTROLPARAMETERS = ()
    DERIVEDPARAMETERS = (conv_derived.NmbInputs,)
    REQUIREDSEQUENCES = (
        conv_fluxes.Inputs,
        conv_fluxes.InputPredictions,
    )
    RESULTSEQUENCES = (conv_fluxes.InputResiduals,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for idx in range(der.nmbinputs):
            flu.inputresiduals[idx] = flu.inputs[idx] - flu.inputpredictions[idx]


class Interpolate_InverseDistance_V1(modeltools.Method):
    """Perform a simple inverse distance weighted interpolation.

    See the documentation on method |Calc_Outputs_V2| for further information.
    """

    CONTROLPARAMETERS = (conv_control.MaxNmbInputs,)
    DERIVEDPARAMETERS = (
        conv_derived.NmbOutputs,
        conv_derived.ProximityOrder,
        conv_derived.Weights,
    )
    REQUIREDSEQUENCES = ()
    RESULTSEQUENCES = ()

    @staticmethod
    def __call__(model: modeltools.Model, inputs: Vector, outputs: Vector) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        for idx_out in range(der.nmboutputs):
            d_sumweights = 0.0
            d_sumvalues = 0.0
            d_sumvalues_inf = 0.0
            counter_inf = 0
            for idx_try in range(con.maxnmbinputs):
                idx_in = der.proximityorder[idx_out, idx_try]
                if not modelutils.isnan(inputs[idx_in]):
                    if modelutils.isinf(der.weights[idx_out, idx_try]):
                        d_sumvalues_inf += inputs[idx_in]
                        counter_inf += 1
                    else:
                        d_sumweights += der.weights[idx_out, idx_try]
                        d_sumvalues += der.weights[idx_out, idx_try] * inputs[idx_in]
            if counter_inf:
                outputs[idx_out] = d_sumvalues_inf / counter_inf
            elif d_sumweights:
                outputs[idx_out] = d_sumvalues / d_sumweights
            else:
                outputs[idx_out] = modelutils.nan


class Calc_Outputs_V2(modeltools.Method):
    """Perform a simple inverse distance weighted interpolation based on the original
    data supplied by the input nodes.

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
    SUBMETHODS = (Interpolate_InverseDistance_V1,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        model.interpolate_inversedistance_v1(flu.inputs, flu.outputs)


class Calc_OutputResiduals_V1(modeltools.Method):
    """Perform a simple inverse distance weighted interpolation based on the
    residuals previously determined for the input nodes.

    Example:

        See the documentation on method |Calc_Outputs_V2| for further information,
        from which we take the following (first) example:

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

        >>> fluxes.inputresiduals.shape = 4
        >>> fluxes.inputresiduals = 1.0, 5.0, 3.0, 6.0
        >>> model.calc_outputresiduals_v1()
        >>> fluxes.outputresiduals
        outputresiduals(2.0, 4.684331, 2.272907)
    """

    CONTROLPARAMETERS = (conv_control.MaxNmbInputs,)
    DERIVEDPARAMETERS = (
        conv_derived.NmbOutputs,
        conv_derived.ProximityOrder,
        conv_derived.Weights,
    )
    REQUIREDSEQUENCES = (conv_fluxes.InputResiduals,)
    RESULTSEQUENCES = (conv_fluxes.OutputResiduals,)
    SUBMETHODS = (Interpolate_InverseDistance_V1,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        flu = model.sequences.fluxes.fastaccess
        model.interpolate_inversedistance_v1(flu.inputresiduals, flu.outputresiduals)


class Calc_Outputs_V3(modeltools.Method):
    r"""Calculate the values of the output nodes by combining the initial predictions
    with the interpolated residuals.

    Basic equation:
       :math:`Outputs = OutputPredictions - OutputResiduals`

    Examples:

        >>> from hydpy.models.conv import *
        >>> parameterstep()
        >>> derived.nmboutputs(2)
        >>> fluxes.outputpredictions = 1.0, 2.0
        >>> fluxes.outputresiduals = 3.0, -4.0
        >>> model.calc_outputs_v3()
        >>> fluxes.outputs
        outputs(4.0, -2.0)
    """

    CONTROLPARAMETERS = ()
    DERIVEDPARAMETERS = (conv_derived.NmbOutputs,)
    REQUIREDSEQUENCES = (
        conv_fluxes.OutputPredictions,
        conv_fluxes.OutputResiduals,
    )
    RESULTSEQUENCES = (conv_fluxes.Outputs,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for idx in range(der.nmboutputs):
            flu.outputs[idx] = flu.outputpredictions[idx] + flu.outputresiduals[idx]


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
        Calc_ActualConstant_ActualFactor_V1,
        Calc_InputPredictions_V1,
        Calc_OutputPredictions_V1,
        Calc_InputResiduals_V1,
        Calc_Outputs_V1,
        Calc_Outputs_V2,
        Calc_OutputResiduals_V1,
        Calc_Outputs_V3,
    )
    ADD_METHODS = (
        Return_Mean_V1,
        Interpolate_InverseDistance_V1,
    )
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

        Second, you must define the inlet and outlet nodes' coordinates via
        parameter |InputCoordinates| and |OutputCoordinates|, respectively.
        In both cases, use the names of the |Node| objects as keyword arguments
        to pass the corresponding coordinates:

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
