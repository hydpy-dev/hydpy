# pylint: disable=missing-docstring, unused-argument

from hydpy.core import modeltools

class PegasusBase:
    def apply_method0(self, x: float, /) -> float: ...
    # positional arguments required for consistency with the cythonized extension class:
    def find_x(  # pylint: disable=too-many-positional-arguments
        self,
        x0: float,
        x1: float,
        xmin: float,
        xmax: float,
        xtol: float,
        ytol: float,
        itermax: int,
        /,
    ) -> float: ...

class PegasusPython(PegasusBase):
    method0: modeltools.Method
