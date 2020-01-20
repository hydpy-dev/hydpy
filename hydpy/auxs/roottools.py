# -*- coding: utf-8 -*-
"""This module specialises class |Submodel| for root-finding problems.

Module |roottools| provides Python interfaces only.  See the
Cython extension module |rootutils| for the actual implementations
of the mathematical algorithms.
"""

# import...
# ...from HydPy
from hydpy.core import modeltools
from hydpy.cythons.autogen import rootutils


class Pegasus(modeltools.Submodel):
    """Root-finder based on the `Pegasus method`_.

    .. _`Pegasus method`: https://link.springer.com/article/10.1007/BF01932959

    The Pegasus method is a root-finding algorithm which sequentially
    decreases its search radius (like the simple bisection algorithm)
    and shows superlinear convergence properties (like the Newton-Raphson
    algorithm).  Our implementation adds a simple "interval widening"
    strategy that comes into play when the given initial interval does not
    contain the root.  This widening should be left for emergencies as
    it might be not always efficient.  So please try to provide to
    initial interval estimates that rather overestimate than underestimate
    the interval width.
    """

    CYTHONBASECLASS = rootutils.PegasusBase
    PYTHONCLASS = rootutils.PegasusPython
    _cysubmodel: rootutils.PegasusBase

    def find_x(self, x0: float, x1: float, xtol: float, ytol: float) -> float:    # ToDo: update tests
        """Find the relevant root within the interval
        :math:`xmin \\leq x \\leq xmax` with an accuracy meeting at least
        one of the absolute tolerance values `xtol` and `ytol`.

        The following examples need to be updated soon:

        >>> from hydpy.models.lland import *
        >>> parameterstep()
        >>> inputs.nied = 2.5
        >>> model.calc_test2_v1()
        >>> inputs.teml
        teml(1.589721)

        >>> inputs.nied = 0.0
        >>> model.calc_test2_v1()
        >>> inputs.teml
        teml(0.0)

        >>> inputs.nied = 200.0
        >>> model.calc_test2_v1()
        >>> inputs.teml
        teml(14.142018)

        >>> inputs.nied = 4.0
        >>> model.calc_test2_v1()
        >>> inputs.teml
        teml(2.0)

        >>> inputs.nied = 16.0
        >>> model.calc_test2_v1()
        >>> inputs.teml
        teml(4.0)
        """
        return self._cysubmodel.find_x(x0, x1, xtol, ytol)

    def apply_method0(self, value: float) -> float:
        """Apply the model method relevant for root-finding."""
        return self._cysubmodel.apply_method(value)
