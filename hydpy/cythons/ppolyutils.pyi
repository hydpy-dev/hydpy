from numpy import float_, int_
from numpy.typing import NDArray

class PPoly:
    # required for usage as an "algorithm" by interputils:
    nmb_inputs: int
    nmb_outputs: int
    inputs: NDArray[float_]
    outputs: NDArray[float_]
    output_derivatives: NDArray[float_]
    def calculate_values(self) -> None: ...
    def calculate_derivatives(self, __idx_input: int) -> None: ...
    # algorithm-specific requirements:
    nmb_x0s: int
    nmb_cs: NDArray[int_]
    ps: NDArray[float_]
    cs: NDArray[float_]
