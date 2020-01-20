
from hydpy.core import modeltools

class PegasusBase:

    def apply_method0(self, x: float) -> float:
        ...

    def find_x(self, xmin: float, xmax: float, xtol: float, ytol: float) \
            -> float:
        ...


class PegasusPython(PegasusBase):

    method0: modeltools.Method
