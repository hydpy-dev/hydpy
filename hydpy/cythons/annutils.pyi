# pylint: disable=missing-docstring

from hydpy.core.typingtools import *

class ANN:
    # required for usage as an "algorithm" by interputils:
    nmb_inputs: int
    nmb_outputs: int
    inputs: VectorFloat
    outputs: VectorFloat
    output_derivatives: VectorFloat
    def calculate_values(self) -> None: ...
    def calculate_derivatives(  # pylint: disable=unused-argument
        self, idx: int, /
    ) -> None: ...
    # algorithm-specific requirements:
    nmb_layers: int
    nmb_neurons: VectorInt
    weights_input: MatrixFloat
    weights_output: MatrixFloat
    weights_hidden: TensorFloat
    intercepts_hidden: MatrixFloat
    intercepts_output: VectorFloat
    activation: MatrixInt
    neurons: MatrixFloat
