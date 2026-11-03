# pylint: disable=missing-docstring, unused-argument

from hydpy.auxs.interptools import InterpAlgorithm
from hydpy.core.typingtools import *

class SimpleInterpolator:
    nmb_inputs: int
    nmb_outputs: int
    algorithm_type: int
    inputs: FastAccessVector[float]
    outputs: FastAccessVector[float]
    output_derivatives: FastAccessVector[float]
    def __init__(self, algorithm: InterpAlgorithm) -> None: ...
    def calculate_values(self) -> None: ...
    def calculate_derivatives(self, idx: int, /) -> None: ...

class SeasonalInterpolator:
    nmb_inputs: int
    nmb_outputs: int
    nmb_algorithms: int
    algorithm_types: FastAccessVector[int]
    ratios: FastAccessMatrix[float]
    inputs: FastAccessVector[float]
    outputs: FastAccessVector[float]
    def __init__(self, algorithms: Sequence[InterpAlgorithm]) -> None: ...
    def calculate_values(self, idx: int, /) -> None: ...
