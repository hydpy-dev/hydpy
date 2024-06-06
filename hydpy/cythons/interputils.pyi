# pylint: disable=missing-docstring, unused-argument

from typing import Sequence, Tuple, Union

from hydpy.auxs.interptools import InterpAlgorithm
from hydpy.core.typingtools import *
from hydpy.cythons.autogen.annutils import ANN
from hydpy.cythons.autogen.ppolyutils import PPoly

class SimpleInterpolator:
    nmb_inputs: int
    nmb_outputs: int
    algorithm: Union[ANN, PPoly]
    inputs: VectorFloat
    outputs: VectorFloat
    def __init__(self, algorithm: InterpAlgorithm) -> None: ...
    def calculate_values(self) -> None: ...
    def calculate_derivatives(self, idx_input: int) -> None: ...

class SeasonalInterpolator:
    nmb_inputs: int
    nmb_outputs: int
    nmb_algorithms: int
    algorithms: Tuple[Union[ANN, PPoly], ...]
    ratios: MatrixFloat
    inputs: VectorFloat
    outputs: VectorFloat
    def __init__(self, algorithms: Sequence[InterpAlgorithm]): ...
    def calculate_values(self, idx_season: int) -> None: ...
