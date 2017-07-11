# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy import pub
from hydpy.core import parametertools
# ...model specific
from hydpy.models.lland import lland_parameters


class MOY(parametertools.IndexParameter):
    """References the "global" month of the year index array [-]."""
    NDIM, TYPE, TIME, SPAN = 1, int, None, (0, 11)

    def update(self):
        self.setreference(pub.indexer.monthofyear)


class KInz(lland_parameters.LanduseMonthParameter):
    """Interzeptionskapazität bezogen auf die Bodenoberfläche (interception
    capacity normalized to the soil surface area) [mm]."""
    NDIM, TYPE, TIME, SPAN = 2, float, None, (0., None)

    def update(self):
        con = self.subpars.pars.control
        self(con.hinz*con.lai)


class WB(lland_parameters.MultiParameter):
    """Absolute Mindestbodenfeuchte für die Basisabflussentstehung (threshold
       value of absolute soil moisture for base flow generation) [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

    def update(self):
        con = self.subpars.pars.control
        self(con.relwb*con.nfk)


class WZ(lland_parameters.MultiParameter):
    """Absolute Mindestbodenfeuchte für die Interflowentstehung (threshold
       value of absolute soil moisture for interflow generation) [-]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

    def update(self):
        con = self.subpars.pars.control
        self(con.relwz*con.nfk)


class KB(parametertools.SingleParameter):
    """Konzentrationszeit des Basisabflusses (concentration time of baseflow)
    [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

    def update(self):
        con = self.subpars.pars.control
        self(con.eqb*con.tind)


class KI1(parametertools.SingleParameter):
    """Konzentrationszeit des "unteren" Zwischenabflusses (concentration time
    of the first interflow component) [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

    def update(self):
        con = self.subpars.pars.control
        self(con.eqi1*con.tind)


class KI2(parametertools.SingleParameter):
    """Konzentrationszeit des "oberen" Zwischenabflusses" (concentration time
    of the second interflow component) [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

    def update(self):
        con = self.subpars.pars.control
        self(con.eqi2*con.tind)


class KD1(parametertools.SingleParameter):
    """Konzentrationszeit des "langsamen" Direktabflusses (concentration time
    of the slower component of direct runoff) [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

    def update(self):
        con = self.subpars.pars.control
        self(con.eqd1*con.tind)


class KD2(parametertools.SingleParameter):
    """Konzentrationszeit des "schnellen" Direktabflusses (concentration time
    of the faster component of direct runoff) [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

    def update(self):
        con = self.subpars.pars.control
        self(con.eqd2*con.tind)


class QFactor(parametertools.SingleParameter):
    """Factor for converting mm/stepsize to m³/s."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

    def update(self):
        con = self.subpars.pars.control
        self(con.ft*1000./self.simulationstep.seconds)


class DerivedParameters(parametertools.SubParameters):
    """Derived parameters of HydPy-H-Land, indirectly defined by the user."""
    _PARCLASSES = (MOY, KInz, WB, WZ, KB, KI1, KI2, KD1, KD2, QFactor)
