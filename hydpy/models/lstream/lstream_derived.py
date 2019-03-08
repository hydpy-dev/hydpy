# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools


class HV(parametertools.LeftRightParameter):
    """Höhe Vorländer (height of both forelands) [m]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

    def update(self):
        """Update value based on :math:`HV=BBV/BNV`.

        Required Parameters:
            |BBV|
            |BNV|

        Examples:
            >>> from hydpy.models.lstream import *
            >>> parameterstep('1d')
            >>> bbv(left=10., right=40.)
            >>> bnv(left=10., right=20.)
            >>> derived.hv.update()
            >>> derived.hv
            hv(1.0, 2.0)
            >>> bbv(left=10., right=0.)
            >>> bnv(left=0., right=20.)
            >>> derived.hv.update()
            >>> derived.hv
            hv(0.0)
        """
        con = self.subpars.pars.control
        self(0.)
        for idx in range(2):
            if (con.bbv[idx] > 0.) and (con.bnv[idx] > 0.):
                self.values[idx] = con.bbv[idx]/con.bnv[idx]


class QM(parametertools.Parameter):
    """Bordvoller Abfluss Hauptgerinne (maximum discharge of the main channel)
    [m³/s]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

    def update(self):
        """Update value based on the actual |calc_qg_v1| method.

        Required derived parameter:
            |H|

        Note that the value of parameter |lstream_derived.QM| is directly
        related to the value of parameter |HM| and indirectly related to
        all parameters values relevant for method |calc_qg_v1|. Hence the
        complete paramter (and sequence) requirements might differ for
        various application models.

        For examples, see the documentation on method ToDo.
        """
        mod = self.subpars.pars.model
        con = mod.parameters.control
        flu = mod.sequences.fluxes
        flu.h = con.hm
        mod.calc_qg()
        self(flu.qg)


class QV(parametertools.LeftRightParameter):
    """Bordvoller Abfluss Vorländer (maximum discharge of both forelands)
    [m³/s]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

    def update(self):
        """Update value based on the actual |calc_qg_v1| method.

        Required derived parameter:
            |HV|

        Note that the values of parameter |lstream_derived.QV| are
        directly related to the values of parameter |HV| and indirectly
        related to all parameters values relevant for method |calc_qg_v1|.
        Hence the complete paramter (and sequence) requirements might
        differ for various application models.

        For examples, see the documentation on method ToDo.
        """
        mod = self.subpars.pars.model
        con = mod.parameters.control
        der = self.subpars
        flu = mod.sequences.fluxes
        self(0.)
        for idx in range(2):
            flu.h = con.hm+der.hv[idx]
            mod.calc_qg()
            self[idx] = flu.qg


class Sek(parametertools.Parameter):
    """ Sekunden im Simulationszeitschritt (Number of seconds of the selected
    simulation time step) [T]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

    def update(self):
        """Update value based on |Parameter.simulationstep|.

        Example:
            >>> from hydpy.models.lstream import *
            >>> parameterstep()
            >>> simulationstep('1d')
            >>> derived.sek.update()
            >>> derived.sek
            sek(86400.0)
        """
        self(self.simulationstep.seconds)


class DerivedParameters(parametertools.SubParameters):
    """Derived parameters of HydPy-L-Stream, indirectly defined by the user."""
    CLASSES = (HV,
               QM,
               QV,
               Sek)
