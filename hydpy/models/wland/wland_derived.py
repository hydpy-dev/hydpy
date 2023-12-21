# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...

# ...from site-packages
import numpy

# ...from HydPy
import hydpy
from hydpy.core import parametertools
from hydpy.auxs import smoothtools

# ...from lland
from hydpy.models.wland import wland_control
from hydpy.models.wland.wland_constants import SEALED, WATER


class MOY(parametertools.MOYParameter):
    r"""References the "global" month of the year index array [-]."""


class NUL(parametertools.Parameter):
    r"""Number of land-related hydrological response units [-]."""

    NDIM, TYPE, TIME, SPAN = 0, int, None, (0, None)

    CONTROLPARAMETERS = (wland_control.NU,)

    def update(self):
        r"""Update |NUL| based on :math:`NUL = NU - 1`.

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> nu(6)
        >>> derived.nul.update()
        >>> derived.nul
        nul(5)
        """
        self.value = self.subpars.pars.control.nu.value - 1


class NUG(parametertools.Parameter):
    r"""Number of groundwater-affected hydrological response units [-]."""

    NDIM, TYPE, TIME, SPAN = 0, int, None, (0, None)

    CONTROLPARAMETERS = (wland_control.LT,)

    def update(self):
        r"""Update |NUG| based on
        :math:`NUG = \Sigma (LT \neq WATER) \land LT \neq SEALED)`.

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> nu(6)
        >>> lt(SEALED, FIELD, SEALED, CONIFER, SEALED, WATER)
        >>> derived.nug.update()
        >>> derived.nug
        nug(2)
        """
        lt = self.subpars.pars.control.lt.values
        self.value = sum((lt != WATER) * (lt != SEALED))


class ALR(parametertools.Parameter):
    r"""Relative land area [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)

    CONTROLPARAMETERS = (wland_control.AUR,)

    def update(self):
        r"""Update |ALR| based on :math:`ALR = \sum_{i = 1}^{NUL} AUR_i`.

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> nu(3)
        >>> aur(0.5, 0.3, 0.2)
        >>> derived.alr.update()
        >>> derived.alr
        alr(0.8)
        """
        pars = self.subpars.pars
        self.value = numpy.sum(pars.control.aur[:-1])


class ASR(parametertools.Parameter):
    r"""Relative surface water area fraction [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)

    CONTROLPARAMETERS = (wland_control.AUR,)

    def update(self):
        r"""Update |ASR| based on :math:`ASR = AUR_{NU}`.

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> nu(3)
        >>> aur(0.5, 0.3, 0.2)
        >>> derived.asr.update()
        >>> derived.asr
        asr(0.2)
        """
        pars = self.subpars.pars
        self.value = pars.control.aur[-1]


class AGR(parametertools.Parameter):
    r"""Relative groundwater area [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)

    CONTROLPARAMETERS = (wland_control.AUR, wland_control.LT)

    def update(self):
        r"""Update |AGR| based on :math:`AGR = \Sigma AUR_{\overline{SEALED}}`.

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> nu(6)
        >>> lt(SEALED, SOIL, SEALED, FIELD, SEALED, WATER)
        >>> aur(0.02, 0.06, 0.1, 0.14, 0.18, 0.5)
        >>> derived.agr.update()
        >>> derived.agr
        agr(0.2)
        """
        c = self.subpars.pars.control
        self.value = numpy.sum(c.aur.values[:-1][c.lt.values[:-1] != SEALED])


class QF(parametertools.Parameter):
    r"""Factor for converting mm/T to m³/s [T m³ / mm s]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)

    CONTROLPARAMETERS = (wland_control.AT,)

    def update(self):
        r"""Update |QF| based on |AT| and the current simulation step size.

        >>> from hydpy.models.wland import *
        >>> simulationstep('1d')
        >>> parameterstep()
        >>> at(10.0)
        >>> derived.qf.update()
        >>> derived.qf
        qf(0.115741)
        """
        at = self.subpars.pars.control.at.value
        self.value = at * 1000.0 / hydpy.pub.options.simulationstep.seconds


class CD(parametertools.Parameter):
    """Channel depth [mm]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)

    CONTROLPARAMETERS = (wland_control.GL, wland_control.BL)

    def update(self):
        r"""Update |CD| based on :math:`CD = GL - BL`.

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> gl(5.0)
        >>> bl(3.0)
        >>> derived.cd.update()
        >>> derived.cd
        cd(2000.0)
        """
        con = self.subpars.pars.control
        self.value = 1000.0 * (con.gl - con.bl)


class RH1(parametertools.Parameter):
    """Regularisation parameter related to the height of water columns used when
    applying regularisation function |smooth_logistic1| [mm]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)

    CONTROLPARAMETERS = (wland_control.SH,)

    def update(self):
        """Calculate the smoothing parameter value.

        The documentation on module |smoothtools| explains the following
        example in some detail:

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> sh(0.0)
        >>> derived.rh1.update()
        >>> from hydpy.cythons.smoothutils import smooth_logistic1
        >>> from hydpy import round_
        >>> round_(smooth_logistic1(0.1, derived.rh1))
        1.0
        >>> sh(2.5)
        >>> derived.rh1.update()
        >>> round_(smooth_logistic1(2.5, derived.rh1))
        0.99
        """
        metapar = self.subpars.pars.control.sh.value
        self(smoothtools.calc_smoothpar_logistic1(metapar))


class RH2(parametertools.Parameter):
    """Regularisation parameter related to the height of water columns used when
    applying regularisation function |smooth_logistic2| [mm]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)

    CONTROLPARAMETERS = (wland_control.SH,)

    def update(self):
        """Calculate the smoothing parameter value.

        The documentation on module |smoothtools| explains the following
        example in some detail:

        >>> from hydpy.models.wland import *
        >>> from hydpy.cythons.smoothutils import smooth_logistic2
        >>> from hydpy import round_
        >>> parameterstep()
        >>> sh(0.0)
        >>> derived.rh2.update()
        >>> round_(smooth_logistic2(0.0, derived.rh2))
        0.0
        >>> sh(2.5)
        >>> derived.rh2.update()
        >>> round_(smooth_logistic2(2.5, derived.rh2))
        2.51
        """
        metapar = self.subpars.pars.control.sh.value
        self(smoothtools.calc_smoothpar_logistic2(metapar))


class RT2(parametertools.Parameter):
    """Regularisation parameter related to temperature for applying regularisation
    function |smooth_logistic2|) [°C]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)

    CONTROLPARAMETERS = (wland_control.ST,)

    def update(self):
        """Calculate the smoothing parameter value.

        The documentation on module |smoothtools| explains the following
        example in some detail:

        >>> from hydpy.models.wland import *
        >>> from hydpy.cythons.smoothutils import smooth_logistic2
        >>> from hydpy import round_
        >>> parameterstep()
        >>> st(0.0)
        >>> derived.rt2.update()
        >>> round_(smooth_logistic2(0.0, derived.rt2))
        0.0
        >>> st(2.5)
        >>> derived.rt2.update()
        >>> round_(smooth_logistic2(2.5, derived.rt2))
        2.51
        """
        metapar = self.subpars.pars.control.st.value
        self(smoothtools.calc_smoothpar_logistic2(metapar))
