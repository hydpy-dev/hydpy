# pylint: disable=missing-module-docstring

# import...
# ...from site-packages
import numpy

# ...from HydPy
from hydpy.core import parametertools
from hydpy.auxs import smoothtools
from hydpy.models.kinw import kinw_control


class Sek(parametertools.SecondsParameter):
    """Sekunden im Simulationszeitschritt (Number of seconds of the selected
    simulation time step) [s]."""


class Seconds(parametertools.SecondsParameter):
    """The length of the actual simulation step size in seconds [s]."""


class HV(parametertools.LeftRightParameter):
    """Höhe Vorländer (height of both forelands) [m]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)

    CONTROLPARAMETERS = (kinw_control.BBV, kinw_control.BNV)

    def update(self):
        """Update based on :math:`HV=BBV/BNV`.

        Examples:
            >>> from hydpy.models.kinw import *
            >>> parameterstep("1d")
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
        self(0.0)
        for idx in range(2):
            if (con.bbv[idx] > 0.0) and (con.bnv[idx] > 0.0):
                self.values[idx] = con.bbv[idx] / con.bnv[idx]


class MFM(parametertools.Parameter):
    """Produkt der zeitkonstanten Terme der Manning-Strickler-Formel für das
    Hauptgerinne (product of the time-constant terms of the Manning-Strickler
    equation, calculated for the main channel) [m^(1/3)/s]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)

    CONTROLPARAMETERS = (kinw_control.EKM, kinw_control.SKM, kinw_control.Gef)

    def update(self):
        """Update based on :math:`MFM=EKM \\cdot SKM \\cdot \\sqrt{Gef}`.

        Examples:
            >>> from hydpy.models.kinw import *
            >>> parameterstep("1d")
            >>> ekm(2.0)
            >>> skm(50.0)
            >>> gef(0.01)
            >>> derived.mfm.update()
            >>> derived.mfm
            mfm(10.0)
        """
        con = self.subpars.pars.control
        self(con.ekm * con.skm * con.gef**0.5)


class MFV(parametertools.LeftRightParameter):
    """Produkt der zeitkonstanten Terme der Manning-Strickler-Formel für
    beide Vorländer (product of the time-constant terms of the Manning-Strickler
    equation, calculated for both forelands) [m^(1/3)/s]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)

    CONTROLPARAMETERS = (kinw_control.EKV, kinw_control.SKV, kinw_control.Gef)

    def update(self):
        """Update based on :math:`MFV=EKV \\cdot SKV \\cdot \\sqrt{Gef}`.

        Examples:
            >>> from hydpy.models.kinw import *
            >>> parameterstep("1d")
            >>> ekv(left=2.0, right=4.0)
            >>> skv(left=25.0, right=50)
            >>> gef(0.01)
            >>> derived.mfv.update()
            >>> derived.mfv
            mfv(left=5.0, right=20.0)
        """
        con = self.subpars.pars.control
        self(con.ekv * con.skv * con.gef**0.5)


class BNMF(parametertools.Parameter):
    """Hilfsterm zur Berechnung des benetzten Böschungsumfangs im
    Hauptgerinne (auxiliary term for the calculation of the wetted
    perimeter of the slope of the main channel) [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)

    CONTROLPARAMETERS = (kinw_control.BNM,)

    def update(self):
        """Update based on :math:`BNMF= \\sqrt{1+BNM^2}`.

        Examples:
            >>> from hydpy.models.kinw import *
            >>> parameterstep("1d")
            >>> bnm(2.0)
            >>> derived.bnmf.update()
            >>> derived.bnmf
            bnmf(2.236068)
        """
        self((1.0 + self.subpars.pars.control.bnm**2) ** 0.5)


class BNVF(parametertools.LeftRightParameter):
    """Hilfsterm zur Berechnung des benetzten Böschungsumfangs der Vorländer
    (auxiliary term for the calculation of the wetted perimeter of the slope
    of both forelands) [m]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)

    CONTROLPARAMETERS = (kinw_control.BNV,)

    def update(self):
        """Update based on :math:`BNVF= \\sqrt{1+BNV^2}`.

        Examples:
            >>> from hydpy.models.kinw import *
            >>> parameterstep("1d")
            >>> bnv(left=2.0, right=3.0)
            >>> derived.bnvf.update()
            >>> derived.bnvf
            bnvf(left=2.236068, right=3.162278)
        """
        self((1.0 + self.subpars.pars.control.bnv**2) ** 0.5)


class BNVRF(parametertools.LeftRightParameter):
    """Hilfsterm zur Berechnung des benetzten Böschungsumfangs der
    Vorlandränder (auxiliary term for the calculation of the wetted
    perimeter of the slope of both outer embankments) [m]."""

    NDIM, TYPE, TIME, SPAN = 1, float, None, (0.0, None)

    CONTROLPARAMETERS = (kinw_control.BNVR,)

    def update(self):
        """Update based on :math:`BNVRF= \\sqrt(1+BNVR^2)`.

        Examples:
            >>> from hydpy.models.kinw import *
            >>> parameterstep("1d")
            >>> bnvr(left=2.0, right=3.0)
            >>> derived.bnvrf.update()
            >>> derived.bnvrf
            bnvrf(left=2.236068, right=3.162278)
        """
        self((1.0 + self.subpars.pars.control.bnvr**2) ** 0.5)


class HRP(parametertools.Parameter):
    """Wasserstand-Regularisierungs-Parameter zur Verwendung in Verbindung
    mit Regularisierungsfunktion |smooth_logistic2| (regularisation parameter
    for water stage to be used when applying regularisation function
    |smooth_logistic2|) [m]."""

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)

    CONTROLPARAMETERS = (kinw_control.HR,)

    def update(self):
        """Calculate the smoothing parameter value.

        The documentation on module |smoothtools| explains the following
        example in some detail:

        >>> from hydpy.models.kinw import *
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


class NmbDiscontinuities(parametertools.Parameter):
    """Number of points of discontinuity in the rating curve [-]."""

    NDIM, TYPE, TIME, SPAN = 0, int, None, (0, None)

    def update(self):
        """Take the number of discontinuities from the available cross-section
        submodel.

        >>> from hydpy.models.kinw_impl_euler import *
        >>> parameterstep()
        >>> with model.add_wqmodel_v1("wq_trapeze_strickler"):
        ...     nmbtrapezes(2)
        ...     bottomlevels(1.0, 3.0)
        ...     bottomslope(0.01)
        ...     sideslopes(2.0, 4.0)
        >>> derived.nmbdiscontinuities.update()
        >>> derived.nmbdiscontinuities
        nmbdiscontinuities(1)
        """
        if (model := self.subpars.pars.model).__HYDPY_ROOTMODEL__:
            self(len(model.wqmodel.get_depths_of_discontinuity()))


class FinalDepth2InitialVolume(parametertools.Parameter):
    """A pair of the final water depth and the corresponding initial water volume
    according to the implicit Euler method for each point of discontinuity in the
    rating curve [m and million m³]."""

    NDIM, TYPE, TIME, SPAN = 2, float, None, (0.0, None)

    def update(self):
        """Use the methods |CrossSectionModel_V1.get_depths_of_discontinuity| and
        |Return_InitialWaterVolume_V1| to determine the final water depths and the
        corresponding initial water volumes.

        >>> from hydpy.models.kinw_impl_euler import *
        >>> parameterstep()
        >>> length(100.0)
        >>> nmbsegments(10)
        >>> derived.seconds(60 * 60 * 24)
        >>> with model.add_wqmodel_v1("wq_trapeze_strickler"):
        ...     nmbtrapezes(3)
        ...     bottomlevels(1.0, 3.0, 5.0)
        ...     bottomwidths(20.0)
        ...     sideslopes(0.0, 0.0, 0.0)
        ...     bottomslope(0.001)
        ...     stricklercoefficients(30.0)
        >>> derived.nmbdiscontinuities.update()
        >>> derived.finaldepth2initialvolume.update()
        >>> derived.finaldepth2initialvolume
        finaldepth2initialvolume([[2.0, 5.008867],
                                  [4.0, 19.01208]])
        """
        parameters = self.subpars.pars
        if (model := parameters.model).__HYDPY_ROOTMODEL__:
            self.shape = (self.subpars.nmbdiscontinuities.value, 2)
            self.values = numpy.nan
            if self.shape[0] > 0:
                for i, d in enumerate(model.wqmodel.get_depths_of_discontinuity()):
                    self.values[i, :] = d, model.return_initialwatervolume(d)
