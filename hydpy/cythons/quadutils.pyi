# pylint: disable=missing-docstring, unused-argument

from hydpy.core import modeltools

class QuadBase:
    def apply_method0(self, x: float, /) -> float: ...
    # positional arguments required for consistency with the cythonized extension class:
    def integrate(  # pylint: disable=too-many-positional-arguments
        self, x0: float, x1: float, nmin: int, nmax: int, tol: float, /
    ) -> float: ...

class QuadPython(QuadBase):
    method0: modeltools.Method
