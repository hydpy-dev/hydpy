# pylint: disable=missing-module-docstring, missing-class-docstring
# pylint: disable=missing-function-docstring

from typing import Final

HISTORICAL: Final[int]
FORECAST: Final[int]

class RunSettings:
    @property
    def simulationmode(self) -> int: ...
    def __hydpy__set_simulationmode__(self, value: int, /) -> None: ...
