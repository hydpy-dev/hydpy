from hydpy.core import modeltools

class QuadBase:
    def apply_method0(
        self,
        x: float,
    ) -> float: ...
    def integrate(
        self,
        x0: float,
        x1: float,
        nmin: int,
        nmax: int,
        tol: float,
    ) -> float: ...

class QuadPython(QuadBase):

    method0: modeltools.Method
