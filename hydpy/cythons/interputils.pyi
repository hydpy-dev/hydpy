# pylint: disable=missing-docstring, unused-argument

from hydpy.auxs.interptools import InterpAlgorithm
from hydpy.core.typingtools import *

if TYPE_CHECKING:
    from hydpy.cythons.annutils import ANN
    from hydpy.cythons.ppolyutils import PPoly
else:
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
    def calculate_derivatives(self, idx: int, /) -> None: ...

class SeasonalInterpolator:
    nmb_inputs: int
    nmb_outputs: int
    nmb_algorithms: int
    algorithms: tuple[Union[ANN, PPoly], ...]
    ratios: MatrixFloat
    inputs: VectorFloat
    outputs: VectorFloat
    def __init__(self, algorithms: Sequence[InterpAlgorithm]): ...
    def calculate_values(self, idx: int, /) -> None: ...
