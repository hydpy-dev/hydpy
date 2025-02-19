# pylint: disable=missing-docstring, unused-argument

import numpy
from hydpy.core import modeltools
from hydpy.core.typingtools import *

class Simulator:
    def __init__(
        self,
        *,
        premethods: Vector[numpy.generic],
        models: Sequence[modeltools.Model],
        breaks: VectorInt,
        postmethods: Vector[numpy.generic],
        parallel_layers: int,
        threads: int,
        schedule: str,
        chunksize: int,
    ) -> None: ...
    def simulate(self, idx_start: int, idx_end: int) -> None: ...
