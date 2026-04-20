# pylint: disable=missing-module-docstring

from hydpy.core import exceptiontools
from hydpy.core.typingtools import *
from hydpy.models.tm import tm_parameters


class A(tm_parameters.Parameter0D):
    """Catchment area [km²]."""

    SPAN = (0.0, None)


class Psi(tm_parameters.Parameter0D):
    """Runoff coefficient [-]."""

    SPAN = (0.0, 1.0)


class KPerc(tm_parameters.Parameter0D):
    """Percolation coefficient [1/T]."""

    TIME = True
    SPAN = (0.0, 1.0)

    def trim(self, lower: TrimHook = None, upper: TrimHook = None) -> bool:
        r"""Trim based on :math:`0 \leq KPerc \leq 1 - KU`.

        >>> from hydpy.models.tm import *
        >>> simulationstep("2h")
        >>> parameterstep("1h")

        >>> kperc(-1.0)
        >>> kperc
        kperc(0.0)

        >>> kperc(1.0)
        >>> kperc
        kperc(0.5)

        >>> kperc(0.4)
        >>> kperc
        kperc(0.4)

        >>> ku.value = 0.6
        >>> kperc(0.4)
        >>> kperc
        kperc(0.2)
        """
        ku = self.subpars.ku
        if (upper is None) and exceptiontools.attrready(ku, "value"):
            upper = 1.0 - ku.value
        return super().trim(lower, upper)


class KU(tm_parameters.Parameter0D):
    """Upper layer storage coefficient [1/T]."""

    TIME = True
    SPAN = (0.0, 1.0)

    def trim(self, lower: TrimHook = None, upper: TrimHook = None) -> bool:
        r"""Trim based on :math:`0 \leq KU \leq 1 - KPerc`.

        >>> from hydpy.models.tm import *
        >>> simulationstep("2h")
        >>> parameterstep("1h")

        >>> ku(-1.0)
        >>> ku
        ku(0.0)

        >>> ku(1.0)
        >>> ku
        ku(0.5)

        >>> ku(0.4)
        >>> ku
        ku(0.4)

        >>> kperc.value = 0.6
        >>> ku(0.4)
        >>> ku
        ku(0.2)
        """
        kperc = self.subpars.kperc
        if (upper is None) and exceptiontools.attrready(kperc, "value"):
            upper = 1.0 - kperc.value
        return super().trim(lower, upper)


class SMax(tm_parameters.Parameter0D):
    """Upper layer storage capacity [mm]."""

    SPAN = (0.0, None)


class KL(tm_parameters.Parameter0D):
    """Lower layer storage coefficient [1/T]."""

    TIME = True
    SPAN = (0.0, 1.0)
