# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy import pub
from hydpy.core import parametertools
from hydpy.auxs import smoothtools


class TOY(parametertools.IndexParameter):
    """References the "global" time of the year index array [-]."""
    NDIM, TYPE, TIME, SPAN = 1, int, None, (0, None)

    def update(self):
        self.setreference(pub.indexer.timeofyear)


class Seconds(parametertools.SingleParameter):
    """Length of the actual simulation step size in seconds [s]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

    def update(self):
        self.value = self.simulationstep.seconds


class RemoteDischargeSmoothPar(parametertools.MultiParameter):
    """Smoothing parameter to be derived from
    :class:`~hydpy.models.dam.dam_control.RemoteDischargeSavety` [m3/s].

    The following example is explained in some detail in module
    :mod:`~hydpy.auxs.smoothtools`:

    >>> from hydpy import pub
    >>> from hydpy.core.timetools import Timegrids, Timegrid
    >>> pub.timegrids = Timegrids(Timegrid('2000.01.01',
    ...                                    '2000.01.03',
    ...                                    '1d'))
    >>> from hydpy.models.dam import *
    >>> parameterstep()
    >>> remotedischargesavety(0.0)
    >>> remotedischargesavety.values[1] = 2.5
    >>> derived.remotedischargesmoothpar.update()
    >>> from hydpy.cythons.smoothutils import smooth_logistic1
    >>> from hydpy.core.objecttools import round_
    >>> round_(smooth_logistic1(0.1, derived.remotedischargesmoothpar[0]))
    1.0
    >>> round_(smooth_logistic1(2.5, derived.remotedischargesmoothpar[1]))
    0.99
    """
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

    def update(self):
        metapars = self.subpars.pars.control.remotedischargesavety
        self.shape = metapars.shape
        for idx, metapar in enumerate(metapars.values):
            self.values[idx] = smoothtools.calc_smoothpar_logistic1(metapar)


class NearDischargeMinimumSmoothPar1(parametertools.MultiParameter):
    """Smoothing parameter to be derived from
    :class:`~hydpy.models.dam.dam_control.NearDischargeMinimumThreshold`
    for smoothing kernel :func:`~hydpy.cythons.smoothutils.smooth_logistic1`
    [m3/s].

    The following example is explained in some detail in module
    :mod:`~hydpy.auxs.smoothtools`:

    >>> from hydpy import pub
    >>> from hydpy.core.timetools import Timegrids, Timegrid
    >>> pub.timegrids = Timegrids(Timegrid('2000.01.01',
    ...                                    '2000.01.03',
    ...                                    '1d'))
    >>> from hydpy.models.dam import *
    >>> parameterstep()
    >>> neardischargeminimumtolerance(0.0)
    >>> neardischargeminimumtolerance.values[1] = 2.5
    >>> derived.neardischargeminimumsmoothpar1.update()
    >>> from hydpy.cythons.smoothutils import smooth_logistic1
    >>> from hydpy.core.objecttools import round_
    >>> round_(smooth_logistic1(1.0, derived.neardischargeminimumsmoothpar1[0]))
    1.0
    >>> round_(smooth_logistic1(2.5, derived.neardischargeminimumsmoothpar1[1]))
    0.99
    """
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

    def update(self):
        metapars = self.subpars.pars.control.neardischargeminimumtolerance
        self.shape = metapars.shape
        for idx, metapar in enumerate(metapars.values):
            self.values[idx] = smoothtools.calc_smoothpar_logistic1(metapar)


class NearDischargeMinimumSmoothPar2(parametertools.MultiParameter):
    """Smoothing parameter to be derived from
    :class:`~hydpy.models.dam.dam_control.NearDischargeMinimumThreshold`
    for smoothing kernel :func:`~hydpy.cythons.smoothutils.smooth_logistic2`
    [m3/s].

    The following example is explained in some detail in module
    :mod:`~hydpy.auxs.smoothtools`:

    >>> from hydpy import pub
    >>> from hydpy.core.timetools import Timegrids, Timegrid
    >>> pub.timegrids = Timegrids(Timegrid('2000.01.01',
    ...                                    '2000.01.03',
    ...                                    '1d'))
    >>> from hydpy.models.dam import *
    >>> parameterstep()
    >>> neardischargeminimumtolerance(0.0)
    >>> neardischargeminimumtolerance.values[1] = 2.5
    >>> derived.neardischargeminimumsmoothpar2.update()
    >>> from hydpy.cythons.smoothutils import smooth_logistic2
    >>> from hydpy.core.objecttools import round_
    >>> round_(smooth_logistic2(0.0, derived.neardischargeminimumsmoothpar2[0]))
    0.0
    >>> round_(smooth_logistic2(2.5, derived.neardischargeminimumsmoothpar2[1]))
    2.51
    """
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

    def update(self):
        metapars = self.subpars.pars.control.neardischargeminimumtolerance
        self.shape = metapars.shape
        for idx, metapar in enumerate(metapars.values):
            self.values[idx] = smoothtools.calc_smoothpar_logistic2(metapar)


class WaterLevelMinimumSmoothPar(parametertools.SingleParameter):
    """Smoothing parameter to be derived from
    :class:`~hydpy.models.dam.dam_control.WaterLevelMinimumTolerance` [m].

    The following example is explained in some detail in module
    :mod:`~hydpy.auxs.smoothtools`:

    >>> from hydpy.models.dam import *
    >>> parameterstep()
    >>> waterlevelminimumtolerance(0.0)
    >>> derived.waterlevelminimumsmoothpar.update()
    >>> from hydpy.cythons.smoothutils import smooth_logistic1
    >>> from hydpy.core.objecttools import round_
    >>> round_(smooth_logistic1(0.1, derived.waterlevelminimumsmoothpar))
    1.0
    >>> waterlevelminimumtolerance(2.5)
    >>> derived.waterlevelminimumsmoothpar.update()
    >>> round_(smooth_logistic1(2.5, derived.waterlevelminimumsmoothpar))
    0.99
    """
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

    def update(self):
        metapar = self.subpars.pars.control.waterlevelminimumtolerance
        self.value = smoothtools.calc_smoothpar_logistic1(metapar)


class WaterLevelMinimumRemoteSmoothPar(parametertools.SingleParameter):
    """Smoothing parameter to be derived from
    :class:`~hydpy.models.dam.dam_control.WaterLevelMinimumRemoteTolerance`
    [m].

    The following example is explained in some detail in module
    :mod:`~hydpy.auxs.smoothtools`:

    >>> from hydpy.models.dam import *
    >>> parameterstep()
    >>> waterlevelminimumremotetolerance(0.0)
    >>> derived.waterlevelminimumremotesmoothpar.update()
    >>> from hydpy.cythons.smoothutils import smooth_logistic1
    >>> from hydpy.core.objecttools import round_
    >>> round_(smooth_logistic1(0.1, derived.waterlevelminimumremotesmoothpar))
    1.0
    >>> waterlevelminimumremotetolerance(2.5)
    >>> derived.waterlevelminimumremotesmoothpar.update()
    >>> round_(smooth_logistic1(2.5, derived.waterlevelminimumremotesmoothpar))
    0.99
    """
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

    def update(self):
        metapar = self.subpars.pars.control.waterlevelminimumremotetolerance
        self.value = smoothtools.calc_smoothpar_logistic1(metapar)


class DerivedParameters(parametertools.SubParameters):
    """Derived parameters of the dam model."""
    _PARCLASSES = (TOY,
                   Seconds,
                   RemoteDischargeSmoothPar,
                   NearDischargeMinimumSmoothPar1,
                   NearDischargeMinimumSmoothPar2,
                   WaterLevelMinimumSmoothPar,
                   WaterLevelMinimumRemoteSmoothPar)
