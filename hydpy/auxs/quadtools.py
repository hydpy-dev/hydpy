# -*- coding: utf-8 -*-
"""This module specialises class |Submodel| for quadrature problems.

Module |quadtools| provides Python interfaces only.  See the Cython extension module
`quadutils` for the actual implementations of the mathematical algorithms.
"""

# import...

# ...from HydPy
from hydpy.core import modeltools
from hydpy.core.typingtools import *

if TYPE_CHECKING:
    from hydpy.cythons import quadutils
else:
    from hydpy.cythons.autogen import quadutils


class Quad(modeltools.Submodel):
    """Numerical solver for quadrature problems based on the Gauss-Lobatto
    quadrature."""

    CYTHONBASECLASS = quadutils.QuadBase  # pylint: disable=used-before-assignment
    PYTHONCLASS = quadutils.QuadPython
    _cysubmodel: quadutils.QuadBase

    def integrate(
        self,
        x0: float,
        x1: float,
        nmin: int,
        nmax: int,
        tol: float,
    ) -> float:
        """Repeatedly integrate the target function within the interval
        :math:`x0 \\leq x \\leq x1` until the estimated accuracy is smaller than
        `tol` using at least `xmin` and at most `xmax` number of nodes.

        The algorithm underlying |Quad| works acceptable, but should be improvable
        both regarding accuracy and efficiency.  We postpone this and provide
        example calculations afterwards.  Please see the documentation on method
        |wland_model.Calc_DVEq_V1| to see |Quad| in action until then.
        """
        return self._cysubmodel.integrate(x0, x1, nmin, nmax, tol)

    def apply_method0(self, value: float) -> float:
        """Apply the model method to be integrated.

        For example, submodel |wland_model.QuadDVEq_V1| integrates method
        |wland_model.Return_DVH_V1|:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> thetas(0.4)
        >>> psiae(300.0)
        >>> b(5.0)
        >>> sh(0.0)
        >>> derived.rh1.update()
        >>> from hydpy import round_
        >>> round_(model.return_dvh_v1(600.0))
        0.05178
        >>> round_(model.quaddveq_v1.apply_method0(600.0))
        0.05178
        """
        return self._cysubmodel.apply_method0(value)
