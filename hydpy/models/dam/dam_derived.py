# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from site-packages
import numpy
# ...from HydPy
from hydpy.core import parametertools
from hydpy.auxs import smoothtools


class TOY(parametertools.TOYParameter):
    """References the |Indexer.timeofyear| index array provided by the
     instance of class |Indexer| available in module |pub|. [-]."""


class Seconds(parametertools.SecondsParameter):
    """Length of the actual simulation step size in seconds [s]."""


class RemoteDischargeSmoothPar(parametertools.Parameter):
    """Smoothing parameter to be derived from |RemoteDischargeSafety| [m3/s].
    """
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

    def update(self):
        """Calculate the smoothing parameter values.

        The following example is explained in some detail in module
        |smoothtools|:

        >>> from hydpy import pub
        >>> pub.timegrids = '2000.01.01', '2000.01.03', '1d'
        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> remotedischargesafety(0.0)
        >>> remotedischargesafety.values[1] = 2.5
        >>> derived.remotedischargesmoothpar.update()
        >>> from hydpy.cythons.smoothutils import smooth_logistic1
        >>> from hydpy import round_
        >>> round_(smooth_logistic1(0.1, derived.remotedischargesmoothpar[0]))
        1.0
        >>> round_(smooth_logistic1(2.5, derived.remotedischargesmoothpar[1]))
        0.99
        """
        metapar = self.subpars.pars.control.remotedischargesafety
        self.shape = metapar.shape
        self(tuple(smoothtools.calc_smoothpar_logistic1(mp)
                   for mp in metapar.values))


class NearDischargeMinimumSmoothPar1(parametertools.Parameter):
    """Smoothing parameter to be derived from |NearDischargeMinimumThreshold|
    for smoothing kernel |smooth_logistic1| [m3/s]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

    def update(self):
        """Calculate the smoothing parameter values.

        The following example is explained in some detail in module
        |smoothtools|:

        >>> from hydpy import pub
        >>> pub.timegrids = '2000.01.01', '2000.01.03', '1d'
        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> neardischargeminimumtolerance(0.0)
        >>> neardischargeminimumtolerance.values[1] = 2.5
        >>> derived.neardischargeminimumsmoothpar1.update()
        >>> from hydpy.cythons.smoothutils import smooth_logistic1
        >>> from hydpy import round_
        >>> round_(smooth_logistic1(
        ...     1.0, derived.neardischargeminimumsmoothpar1[0]))
        1.0
        >>> round_(smooth_logistic1(
        ...     2.5, derived.neardischargeminimumsmoothpar1[1]))
        0.99
        """
        metapar = self.subpars.pars.control.neardischargeminimumtolerance
        self.shape = metapar.shape
        self(tuple(smoothtools.calc_smoothpar_logistic1(mp)
                   for mp in metapar.values))


class NearDischargeMinimumSmoothPar2(parametertools.Parameter):
    """Smoothing parameter to be derived from |NearDischargeMinimumThreshold|
    for smoothing kernel |smooth_logistic2| [m3/s]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

    def update(self):
        """Calculate the smoothing parameter values.

        The following example is explained in some detail in module
        |smoothtools|:

        >>> from hydpy import pub
        >>> pub.timegrids = '2000.01.01', '2000.01.03', '1d'
        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> neardischargeminimumtolerance(0.0)
        >>> neardischargeminimumtolerance.values[1] = 2.5
        >>> derived.neardischargeminimumsmoothpar2.update()
        >>> from hydpy.cythons.smoothutils import smooth_logistic2
        >>> from hydpy import round_
        >>> round_(smooth_logistic2(
        ...     0.0, derived.neardischargeminimumsmoothpar2[0]))
        0.0
        >>> round_(smooth_logistic2(
        ...     2.5, derived.neardischargeminimumsmoothpar2[1]))
        2.51
        """
        metapar = self.subpars.pars.control.neardischargeminimumtolerance
        self.shape = metapar.shape
        self(tuple(smoothtools.calc_smoothpar_logistic2(mp)
                   for mp in metapar.values))

class WaterLevelMinimumSmoothPar(parametertools.Parameter):
    """Smoothing parameter to be derived from |WaterLevelMinimumTolerance|
    for smoothing kernel |smooth_logistic1| [m]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

    def update(self):
        """Calculate the smoothing parameter value.

        The following example is explained in some detail in module
        |smoothtools|:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> waterlevelminimumtolerance(0.0)
        >>> derived.waterlevelminimumsmoothpar.update()
        >>> from hydpy.cythons.smoothutils import smooth_logistic1
        >>> from hydpy import round_
        >>> round_(smooth_logistic1(0.1, derived.waterlevelminimumsmoothpar))
        1.0
        >>> waterlevelminimumtolerance(2.5)
        >>> derived.waterlevelminimumsmoothpar.update()
        >>> round_(smooth_logistic1(2.5, derived.waterlevelminimumsmoothpar))
        0.99
        """
        metapar = self.subpars.pars.control.waterlevelminimumtolerance
        self(smoothtools.calc_smoothpar_logistic1(metapar))


class WaterLevelMinimumRemoteSmoothPar(parametertools.Parameter):
    """Smoothing parameter to be derived from
    |WaterLevelMinimumRemoteTolerance| [m]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

    def update(self):
        """Calculate the smoothing parameter value.

        The following example is explained in some detail in module
        |smoothtools|:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> waterlevelminimumremotetolerance(0.0)
        >>> derived.waterlevelminimumremotesmoothpar.update()
        >>> from hydpy.cythons.smoothutils import smooth_logistic1
        >>> from hydpy import round_
        >>> round_(smooth_logistic1(0.1,
        ...        derived.waterlevelminimumremotesmoothpar))
        1.0
        >>> waterlevelminimumremotetolerance(2.5)
        >>> derived.waterlevelminimumremotesmoothpar.update()
        >>> round_(smooth_logistic1(2.5,
        ...        derived.waterlevelminimumremotesmoothpar))
        0.99
        """
        metapar = self.subpars.pars.control.waterlevelminimumremotetolerance
        self(smoothtools.calc_smoothpar_logistic1(metapar))


class WaterLevelRelieveSmoothPar(parametertools.Parameter):
    """Smoothing parameter to be derived from |WaterLevelRelieveTolerance|
    for smoothing kernel |smooth_logistic1| [m3/s]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

    def update(self):
        """Calculate the smoothing parameter values.

        The following example is explained in some detail in module
        |smoothtools|:

        >>> from hydpy import pub
        >>> pub.timegrids = '2000.01.01', '2000.01.03', '1d'
        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> waterlevelrelievetolerance(0.0)
        >>> waterlevelrelievetolerance.values[1] = 2.5
        >>> derived.waterlevelrelievesmoothpar.update()
        >>> from hydpy.cythons.smoothutils import smooth_logistic1
        >>> from hydpy import round_
        >>> round_(smooth_logistic1(
        ...     1.0, derived.waterlevelrelievesmoothpar[0]))
        1.0
        >>> round_(smooth_logistic1(
        ...     2.5, derived.waterlevelrelievesmoothpar[1]))
        0.99
        """
        metapar = self.subpars.pars.control.waterlevelrelievetolerance
        self.shape = metapar.shape
        self(tuple(smoothtools.calc_smoothpar_logistic1(mp)
                   for mp in metapar.values))

class WaterLevelSupplySmoothPar(parametertools.Parameter):
    """Smoothing parameter to be derived from |WaterLevelSupplyTolerance|
    for smoothing kernel |smooth_logistic1| [m3/s]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

    def update(self):
        """Calculate the smoothing parameter values.

        The following example is explained in some detail in module
        |smoothtools|:

        >>> from hydpy import pub
        >>> pub.timegrids = '2000.01.01', '2000.01.03', '1d'
        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> waterlevelsupplytolerance(0.0)
        >>> waterlevelsupplytolerance.values[1] = 2.5
        >>> derived.waterlevelsupplysmoothpar.update()
        >>> from hydpy.cythons.smoothutils import smooth_logistic1
        >>> from hydpy import round_
        >>> round_(smooth_logistic1(
        ...     1.0, derived.waterlevelsupplysmoothpar[0]))
        1.0
        >>> round_(smooth_logistic1(
        ...     2.5, derived.waterlevelsupplysmoothpar[1]))
        0.99
        """
        metapar = self.subpars.pars.control.waterlevelsupplytolerance
        self.shape = metapar.shape
        self(tuple(smoothtools.calc_smoothpar_logistic1(mp)
                   for mp in metapar.values))


class HighestRemoteSmoothPar(parametertools.Parameter):
    """Smoothing parameter to be derived from |HighestRemoteTolerance|
    for smoothing kernel |smooth_min1| [m3/s]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

    def update(self):
        """Calculate the smoothing parameter value.

        The following example is explained in some detail in module
        |smoothtools|:

        >>> from hydpy.models.dam import *
        >>> parameterstep()
        >>> highestremotedischarge(1.0)
        >>> highestremotetolerance(0.0)
        >>> derived.highestremotesmoothpar.update()
        >>> from hydpy.cythons.smoothutils import smooth_min1
        >>> from hydpy import round_
        >>> round_(smooth_min1(-4.0, 1.5, derived.highestremotesmoothpar))
        -4.0
        >>> highestremotetolerance(2.5)
        >>> derived.highestremotesmoothpar.update()
        >>> round_(smooth_min1(-4.0, -1.5, derived.highestremotesmoothpar))
        -4.01

        Note that the example above corresponds to the example on function
        |calc_smoothpar_min1|, due to the value of parameter
        |HighestRemoteDischarge| being 1 m³/s.  Doubling the value of
        |HighestRemoteDischarge| also doubles the value of
        |HighestRemoteSmoothPar| proportional.  This leads to the following
        result:

        >>> highestremotedischarge(2.0)
        >>> derived.highestremotesmoothpar.update()
        >>> round_(smooth_min1(-4.0, 1.0, derived.highestremotesmoothpar))
        -4.02

        This relationship between |HighestRemoteDischarge| and
        |HighestRemoteSmoothPar| prevents from any smoothing when
        the value of |HighestRemoteDischarge| is zero:

        >>> highestremotedischarge(0.0)
        >>> derived.highestremotesmoothpar.update()
        >>> round_(smooth_min1(1.0, 1.0, derived.highestremotesmoothpar))
        1.0

        In addition, |HighestRemoteSmoothPar| is set to zero if
        |HighestRemoteDischarge| is infinity (because no actual value
        will ever come in the vicinit of infinity), which is why no
        value would be changed through smoothing anyway):

        >>> highestremotedischarge(inf)
        >>> derived.highestremotesmoothpar.update()
        >>> round_(smooth_min1(1.0, 1.0, derived.highestremotesmoothpar))
        1.0
        """
        control = self.subpars.pars.control
        if numpy.isinf(control.highestremotedischarge):
            self(0.0)
        else:
            self(control.highestremotedischarge *
                 smoothtools.calc_smoothpar_min1(control.highestremotetolerance)
                 )


class DerivedParameters(parametertools.SubParameters):
    """Derived parameters of the dam model."""
    CLASSES = (TOY,
               Seconds,
               RemoteDischargeSmoothPar,
               NearDischargeMinimumSmoothPar1,
               NearDischargeMinimumSmoothPar2,
               WaterLevelMinimumSmoothPar,
               WaterLevelMinimumRemoteSmoothPar,
               WaterLevelRelieveSmoothPar,
               WaterLevelSupplySmoothPar,
               HighestRemoteSmoothPar)
