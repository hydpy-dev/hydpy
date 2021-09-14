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
from hydpy.models.wland.wland_constants import SEALED


class MOY(parametertools.MOYParameter):
    r"""References the "global" month of the year index array [-]."""


class NUG(parametertools.Parameter):
    r"""Number of groundwater affected hydrological response units [-]."""

    NDIM, TYPE, TIME, SPAN = 0, int, None, (0, None)

    CONTROLPARAMETERS = (wland_control.LT,)

    def update(self):
        r"""Update |NUG| based on :math:`NUG = \Sigma (LT \neq SEALED)`.

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> nu(5)
        >>> lt(SEALED, FIELD, SEALED, CONIFER, SEALED)
        >>> derived.nug.update()
        >>> derived.nug
        nug(2)
        """
        control = self.subpars.pars.control
        self.value = sum(control.lt.values != SEALED)


class AT(parametertools.Parameter):
    r"""Total area [km²]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)

    CONTROLPARAMETERS = (
        wland_control.AL,
        wland_control.AS_,
    )

    def update(self):
        r"""Update |AT| based on :math:`AT = AL + AS`.

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> al(2.0)
        >>> as_(1.0)
        >>> derived.at.update()
        >>> derived.at
        at(3.0)
        """
        control = self.subpars.pars.control
        self.value = control.al + control.as_


class ALR(parametertools.Parameter):
    r"""Relative land area [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)

    CONTROLPARAMETERS = (wland_control.AL,)
    DERIVEDPARAMETERS = (AT,)

    def update(self):
        r"""Update |ALR| based on :math:`ALR = AL / AT`.

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> al(1.4)
        >>> derived.at(2.0)
        >>> derived.alr.update()
        >>> derived.alr
        alr(0.7)
        """
        pars = self.subpars.pars
        self.value = pars.control.al / pars.derived.at


class ASR(parametertools.Parameter):
    r"""Relative surface water area fraction [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)

    CONTROLPARAMETERS = (wland_control.AS_,)
    DERIVEDPARAMTERS = (AT,)

    def update(self):
        r"""Update |ASR| based on :math:`ASR = AS / AT`.

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> as_(0.4)
        >>> derived.at(2.0)
        >>> derived.asr.update()
        >>> derived.asr
        asr(0.2)
        """
        pars = self.subpars.pars
        self.value = pars.control.as_ / pars.derived.at


class AGR(parametertools.Parameter):
    r"""Relative groundwater area [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)

    CONTROLPARAMETERS = (wland_control.AUR,)
    DERIVEDPARAMETERS = (AT,)

    def update(self):
        r"""Update |AGR| based on :math:`AGR = \Sigma AUR_{\overline{SEALED}}`.

        >>> from hydpy.models.wland import *
        >>> parameterstep()
        >>> nu(5)
        >>> lt(SEALED, SOIL, SEALED, FIELD, SEALED)
        >>> aur(0.04, 0.12, 0.2, 0.28, 0.36)
        >>> derived.agr.update()
        >>> derived.agr
        agr(0.4)
        """
        control = self.subpars.pars.control
        self.value = numpy.sum(control.aur.values[control.lt.values != SEALED])


class QF(parametertools.Parameter):
    r"""Factor for converting mm/T to m³/s [T m³ / mm s]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)

    DERIVEDPARAMETERS = (AT,)

    def update(self):
        r"""Update |QF| based on |AT| and the current simulation step size.

        >>> from hydpy.models.wland import *
        >>> simulationstep('1d')
        >>> parameterstep()
        >>> derived.at(10.0)
        >>> derived.qf.update()
        >>> derived.qf
        qf(0.115741)
        """
        der = self.subpars.pars.derived
        self.value = der.at * 1000.0 / hydpy.pub.options.simulationstep.seconds


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
