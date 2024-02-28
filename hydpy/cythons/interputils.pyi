from typing import Sequence, Tuple, Union

from typing import Sequence, Tuple, Union

from hydpy.auxs.interptools import InterpAlgorithm
from hydpy.cythons.annutils import ANN
from hydpy.cythons.ppolyutils import PPoly
from hydpy.core.typingtools import *

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
