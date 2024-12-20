# pylint: disable=missing-docstring

from hydpy.core.typingtools import *

class PPoly:
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
    nmb_ps: int
    nmb_x0s: int
    nmb_cs: VectorInt
    x0s: VectorFloat
    cs: MatrixFloat
