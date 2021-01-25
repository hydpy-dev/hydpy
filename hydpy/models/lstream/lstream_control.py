# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from standard library
import itertools

# ...from HydPy
from hydpy.auxs import anntools
from hydpy.core import parametertools


class Laen(parametertools.Parameter):
    """Flusslänge (channel length) [km]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class Gef(parametertools.Parameter):
    """Sohlgefälle (channel slope) [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class GTS(parametertools.Parameter):
    """Anzahl Gewässerteilstrecken (number of channel subsections) [-].

    Calling the parameter |GTS| prepares the shape of all 1-dimensional
    sequences for which each entry corresponds to an individual channel
    subsection:

    >>> from hydpy.models.lstream import *
    >>> parameterstep()
    >>> gts(3)
    >>> states.h
    h(nan, nan, nan)
    """

    NDIM, TYPE, TIME, SPAN = 0, int, None, (1, None)

    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)
        seqs = self.subpars.pars.model.sequences
        for seq in itertools.chain(seqs.fluxes, seqs.states, seqs.aides):
            if seq.NDIM:
                seq.shape = self.value


class HM(parametertools.Parameter):
    """Höhe Hauptgerinne (height of the main channel) [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class BM(parametertools.Parameter):
    """Sohlbreite Hauptgerinne (bed width of the main channel) [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class BNM(parametertools.Parameter):
    """Böschungsneigung Hauptgerinne (slope of both main channel embankments)
    [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class BV(parametertools.LeftRightParameter):
    """Sohlbreite Vorländer (bed widths of both forelands) [m]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)


class BBV(parametertools.LeftRightParameter):
    """Breite Vorlandböschungen (width of both foreland embankments) [m]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)


class BNV(parametertools.LeftRightParameter):
    """Böschungsneigung Vorländer (slope of both foreland embankments) [-]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)


class BNVR(parametertools.LeftRightParameter):
    """Böschungsneigung Vorlandränder (slope of both outer embankments) [-]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)


class SKM(parametertools.Parameter):
    """Rauigkeitsbeiwert Hauptgerinne (roughness coefficient of the main
    channel) [m^(1/3)/s]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class SKV(parametertools.LeftRightParameter):
    """Rauigkeitsbeiwert Vorländer (roughness coefficient of both
    forelands) [m^(1/3)/s]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)


class EKM(parametertools.Parameter):
    """Kalibrierfaktor Hauptgerinne (calibration factor for the main
    channel) [-]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class EKV(parametertools.LeftRightParameter):
    """Kalibrierfaktor Vorländer (calibration factor for both forelands) [m]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)


class HR(parametertools.Parameter):
    """Allgemeiner Glättungsparameter für den Wasserstand (general smoothing
    parameter for the water stage) [mm]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class VG2QG(anntools.ANN):
    """Künstliches Neuronales Netz zur Abbildung der Abhängigkeit des
    Abflusses einer Gewässerteilstrecke von deren aktuller Wasserspeicherung
    (artificial neural network describing the relationship between
    total discharge and water storage of individual channel subsections [-]."""

    XLABEL = "vg [million m³]"
    YLABEL = "qg [m³/s]"
