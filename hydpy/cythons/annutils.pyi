from hydpy.core.typingtools import *

class ANN:
    # required for usage as an "algorithm" by interputils:
    nmb_inputs: int
    nmb_outputs: int
    inputs: NDArray[float_]
    outputs: NDArray[float_]
    output_derivatives: NDArray[float_]
    def calculate_values(self) -> None: ...
    def calculate_derivatives(self, __idx_input: int) -> None: ...
    # algorithm-specific requirements:
    nmb_layers: int
    nmb_neurons: NDArray[float_]
    weights_input: NDArray[float_]
    weights_output: NDArray[float_]
    weights_hidden: NDArray[float_]
    intercepts_hidden: NDArray[float_]
    intercepts_output: NDArray[float_]
    activation: NDArray[float_]
    neurons: NDArray[float_]
