# -*- coding: utf-8 -*-

# import...
# ...from HydPy
from hydpy.core import parametertools


class Laen(parametertools.SingleParameter):
    """Flusslänge (channel length) [km]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)


class Gef(parametertools.SingleParameter):
    """Sohlgefälle (channel slope) [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)


class HM(parametertools.SingleParameter):
    """Höhe Hauptgerinne (height of the main channel) [m]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)


class BM(parametertools.SingleParameter):
    """Sohlbreite Hauptgerinne (bed width of the main channel) [m]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)


class BNM(parametertools.SingleParameter):
    """Böschungsneigung Hauptgerinne (slope of both main channel embankments)
    [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)


class BV(parametertools.LeftRightParameter):
    """Sohlbreite Vorländer (bed widths of both forelands) [m]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)


class BBV(parametertools.LeftRightParameter):
    """Breite Vorlandböschungen (width of both foreland embankments) [m]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)


class BNV(parametertools.LeftRightParameter):
    """Böschungsneigung Vorländer (slope of both foreland embankments) [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)


class BNVR(parametertools.LeftRightParameter):
    """Böschungsneigung Vorlandränder (slope of both outer embankments) [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)


class SKM(parametertools.SingleParameter):
    """Rauigkeitsbeiwert Hauptgerinne (roughness coefficient of the main
    channel) [m^(1/3)/s]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)


class SKV(parametertools.LeftRightParameter):
    """Rauigkeitsbeiwert Vorländer (roughness coefficient of the both
    forelands) [m^(1/3)/s]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)


class EKM(parametertools.SingleParameter):
    """Kalibrierfaktor Hauptgerinne (calibration factor for the main
    channel) [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)


class EKV(parametertools.LeftRightParameter):
    """Kalibrierfaktor Vorländer (calibration factor for both forelands) [m].
    """
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)


class QTol(parametertools.SingleParameter):
    """Approximationstoleranz Abfluss (discharge related stopping criterion
    for root-finding algorithms) [m³/s]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)
    INIT = 1e-6


class HTol(parametertools.SingleParameter):
    """Approximationstoleranz Wasserstand (water stage related stopping
    criterion for root-finding algorithms) [m]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)
    INIT = 1e-6


class ControlParameters(parametertools.SubParameters):
    """Control parameters HydPy-L-Stream, directly defined by the user."""
    CLASSES = (Laen,
               Gef,
               HM,
               BM,
               BV,
               BBV,
               BNM,
               BNV,
               BNVR,
               SKM,
               SKV,
               EKM,
               EKV,
               QTol,
               HTol)
