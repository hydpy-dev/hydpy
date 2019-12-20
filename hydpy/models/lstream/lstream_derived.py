# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools
from hydpy.auxs import smoothtools
from hydpy.models.lstream import lstream_control


class Sek(parametertools.SecondsParameter):
    """ Sekunden im Simulationszeitschritt (Number of seconds of the selected
    simulation time step) [s]."""


class HV(parametertools.LeftRightParameter):
    """Höhe Vorländer (height of both forelands) [m]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

    CONTROLPARAMETERS = (
        lstream_control.BBV,
        lstream_control.BNV,
    )

    def update(self):
        """Update value based on :math:`HV=BBV/BNV`.

        Examples:
            >>> from hydpy.models.lstream import *
            >>> parameterstep('1d')
            >>> bbv(left=10., right=40.)
            >>> bnv(left=10., right=20.)
            >>> derived.hv.update()
            >>> derived.hv
            hv(left=1.0, right=2.0)
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


class MFM(parametertools.Parameter):
    """Produkt der zeitkonstanten Terme der Manning-Strickler-Formel für das
    Hauptgerinne (product of the time-constant terms of the Manning-Strickler
    equation, calculated for the main channel) [m^(1/3)/s]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

    CONTROLPARAMETERS = (
        lstream_control.EKM,
        lstream_control.SKM,
        lstream_control.Gef,
    )

    def update(self):
        """Update value based on :math:`MFM=EKM \\cdot SKM \\cdot \\sqrt(Gef)`.

        Examples:
            >>> from hydpy.models.lstream import *
            >>> parameterstep('1d')
            >>> ekm(2.0)
            >>> skm(50.0)
            >>> gef(0.01)
            >>> derived.mfm.update()
            >>> derived.mfm
            mfm(10.0)
        """
        con = self.subpars.pars.control
        self(con.ekm*con.skm*con.gef**.5)


class MFV(parametertools.LeftRightParameter):
    """Produkt der zeitkonstanten Terme der Manning-Strickler-Formel für
    beide Vorländer (product of the time-constant terms of the Manning-Strickler
    equation, calculated for both forelands) [m^(1/3)/s]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

    CONTROLPARAMETERS = (
        lstream_control.EKV,
        lstream_control.SKV,
        lstream_control.Gef,
    )

    def update(self):
        """Update value based on :math:`MFV=EKV \\cdot SKV \\cdot \\sqrt(Gef)`.

        Examples:
            >>> from hydpy.models.lstream import *
            >>> parameterstep('1d')
            >>> ekv(left=2.0, right=4.0)
            >>> skv(left=25.0, right=50)
            >>> gef(0.01)
            >>> derived.mfv.update()
            >>> derived.mfv
            mfv(left=5.0, right=20.0)
        """
        con = self.subpars.pars.control
        self(con.ekv*con.skv*con.gef**.5)


class BNMF(parametertools.Parameter):
    """Hilfsterm zur Berechnung des benetzten Böschungsumfangs im
    Hauptgerinne (auxiliary term for the calculation of the wetted
    perimeter of the slope of the main channel) [m]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

    CONTROLPARAMETERS = (
        lstream_control.BNM,
    )

    def update(self):
        """Update value based on :math:`BNMF= \\sqrt(1+BNM^2)`.

        Examples:
            >>> from hydpy.models.lstream import *
            >>> parameterstep('1d')
            >>> bnm(2.0)
            >>> derived.bnmf.update()
            >>> derived.bnmf
            bnmf(2.236068)
        """
        self((1.+self.subpars.pars.control.bnm**2)**.5)


class BNVF(parametertools.LeftRightParameter):
    """Hilfsterm zur Berechnung des benetzten Böschungsumfangs der Vorländer
    (auxiliary term for the calculation of the wetted perimeter of the slope
    of both forelands) [m]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

    CONTROLPARAMETERS = (
        lstream_control.BNV,
    )

    def update(self):
        """Update value based on :math:`BNVF= \\sqrt(1+BNV^2)`.

        Examples:
            >>> from hydpy.models.lstream import *
            >>> parameterstep('1d')
            >>> bnv(left=2.0, right=3.0)
            >>> derived.bnvf.update()
            >>> derived.bnvf
            bnvf(left=2.236068, right=3.162278)
        """
        self((1.+self.subpars.pars.control.bnv**2)**.5)


class BNVRF(parametertools.LeftRightParameter):
    """Hilfsterm zur Berechnung des benetzten Böschungsumfangs der
    Vorlandränder (auxiliary term for the calculation of the wetted
    perimeter of the slope of both outer embankments) [m]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

    CONTROLPARAMETERS = (
        lstream_control.BNVR,
    )

    def update(self):
        """Update value based on :math:`BNVRF= \\sqrt(1+BNVR^2)`.

        Examples:
            >>> from hydpy.models.lstream import *
            >>> parameterstep('1d')
            >>> bnvr(left=2.0, right=3.0)
            >>> derived.bnvrf.update()
            >>> derived.bnvrf
            bnvrf(left=2.236068, right=3.162278)
        """
        self((1.+self.subpars.pars.control.bnvr**2)**.5)


class HRP(parametertools.Parameter):
    """Wasserstand-Regularisierungs-Parameter zur Verwendung in Verbindung
    mit Regularisierungsfunktion |smooth_logistic2| (regularisation parameter
    for water stage to be used when applying regularisation function
    |smooth_logistic2|) [m]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

    CONTROLPARAMETERS = (
        lstream_control.HR,
    )

    def update(self):
        """Calculate the smoothing parameter value.

        The following example is explained in some detail in module
        |smoothtools|:

        >>> from hydpy.models.lstream import *
        >>> from hydpy.cythons.smoothutils import smooth_logistic2
        >>> from hydpy import round_
        >>> parameterstep()
        >>> hr(0.0)
        >>> derived.hrp.update()
        >>> round_(smooth_logistic2(0.0, derived.hrp))
        0.0
        >>> hr(2.5)
        >>> derived.hrp.update()
        >>> round_(smooth_logistic2(2.5, derived.hrp))
        2.51
        """
        metapar = self.subpars.pars.control.hr.value
        self(smoothtools.calc_smoothpar_logistic2(metapar))
