# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import modeltools
from hydpy.core import parametertools
from hydpy.core import sequencetools
from hydpy.cythons import modelutils
# Load the required `magic` functions into the local namespace.
from hydpy.core.magictools import parameterstep
from hydpy.core.magictools import simulationstep
from hydpy.core.magictools import controlcheck
from hydpy.core.magictools import Tester
from hydpy.cythons.modelutils import Cythonizer


###############################################################################
# Parameter definitions
###############################################################################

class Len(parametertools.SingleParameter):
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

class BL(parametertools.SingleParameter):
    """Breite linkes Vorland (width of the left foreland) [m]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

class BR(parametertools.SingleParameter):
    """Breite rechtes Vorland (width of the right foreland) [m]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

class BBL(parametertools.SingleParameter):
    """Breite linke Böschung (width of the left embankment) [m]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

class BBR(parametertools.SingleParameter):
    """Breite rechte Böschung (width of the right embankment) [m]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

class BNM(parametertools.SingleParameter):
    """Böschungsneigung Hauptgerinne (slope of both main channel banks) [m]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

class BNL(parametertools.SingleParameter):
    """Neigung linkes Vorland (slope of the left foreland) [m]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

class BNR(parametertools.SingleParameter):
    """Neigung rechtes Vorland (slope of the right foreland) [m]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

class BNVRL(parametertools.SingleParameter):
    """Neigung linke Böschung (slope of the left embankment) [m]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

class BNVRR(parametertools.SingleParameter):
    """Neigung rechte Böschung (slope of the right embankment) [m]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

class SKM(parametertools.SingleParameter):
    """Rauigkeitsbeiwert Hauptgerinne (roughness coefficient of the main
    channel) [m]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

class SKL(parametertools.SingleParameter):
    """Rauigkeitsbeiwert Vorland und Böschung links (roughness coefficient of
    the left foreland and embankment) [m]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

class SKR(parametertools.SingleParameter):
    """Rauigkeitsbeiwert Vorland und Böschung rechts (roughness coefficient of
    the right foreland and embankment) [m]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

class EKM(parametertools.SingleParameter):
    """Kalibrierfaktor Hauptgerinne (calibration factor for the main
    channel) [m]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

class EKL(parametertools.SingleParameter):
    """Kalibrierfaktor Vorland und Böschung links (calibration factor for
    the left foreland and embankment) [m]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

class EKR(parametertools.SingleParameter):
    """Kalibrierfaktor Vorland und Böschung rechts (calibration factor for
    the right foreland and embankment) [m]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

class MaxF(parametertools.SingleParameter):
    """Abbruchkriterium Newton-Raphson-Iteration (stopping criterion for the
    Newton iteration method) [m]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)
    INIT = 1e-6

class ControlParameters(parametertools.SubParameters):
    """Control parameters of hstream, directly defined by the user."""
    _PARCLASSES = (Len, Gef, HM, BM, BL, BR, BBL, BBR, BNM, BNL, BNR,
                   BNVRL, BNVRR, SKM, SKL, SKR, EKM, EKL, EKR, MaxF)
# Derived Parameters ##########################################################

class HL(parametertools.SingleParameter):
    """Höhe linkes Vorland (height of the left foreland) [m]."""
    NDIM, TYPE, TIME, SPAN = 0, float, False, (0., None)

    def update(self):
        """Update value based on :math:`HL=BBL/BNL`.

        Required Parameters:
            :class:`BBL`
            :class:`BNL`

        Examples:
            >>> from hydpy.models.lstream import *
            >>> parameterstep('1d')
            >>> bbl(10.)
            >>> bnl(10.)
            >>> derived.hl.update()
            >>> derived.hl
            hl(1.0)
            >>> bbl(0.)
            >>> bnl(0.)
            >>> derived.hl.update()
            >>> derived.hl
            hl(0.0)
        """
        con = self.subpars.pars.control
        if (con.bbl > 0.) and (con.bnl > 0.):
            self(con.bbl/con.bnl)
        else:
            self(0.)

class HR(parametertools.SingleParameter):
    """Höhe rechtes Vorland (height of the right foreland) [m]."""
    NDIM, TYPE, TIME, SPAN = 0, float, False, (0., None)

    def update(self):
        """Update value based on :math:`HL=BBR/BNR`.

        Required Parameters:
            :class:`BBR`
            :class:`BNR`

        Examples:
            >>> from hydpy.models.lstream import *
            >>> parameterstep('1d')
            >>> bbr(10.)
            >>> bnr(10.)
            >>> derived.hr.update()
            >>> derived.hr
            hr(1.0)
            >>> bbr(0.)
            >>> bnr(0.)
            >>> derived.hr.update()
            >>> derived.hr
            hr(0.0)
        """
        con = self.subpars.pars.control
        if (con.bbr > 0.) and (con.bnr > 0.):
            self(con.bbr/con.bnr)
        else:
            self(0.)

class Sek(parametertools.SingleParameter):
    """ Sekunden im Simulationszeitschritt (Number of seconds of the selected
    simulation time step) [T]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

    def update(self):
        """Update value based on :math:`HL=BBR/BNR`.

        Required Parameters:
            :class:`BBR`
            :class:`BNR`

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
    """Derived parameters of hstream, indirectly defined by the user."""
    _PARCLASSES = (HL, HR, Sek)

# Parameter container #########################################################

class Parameters(parametertools.Parameters):
    """All parameters of HydPy-L-Stream."""


###############################################################################
# Sequence Definitions
###############################################################################

# State Sequences #############################################################

class QZ(sequencetools.StateSequence):
    """Zufluss in Gerinnestrecke (inflow into the channel) [m³/s]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class QA(sequencetools.StateSequence):
    """Abfluss aus Gerinnestrecke (outflow out of the channel) [m³/s]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class StateSequences(sequencetools.StateSequences):
    """State sequences of HydPy-L-Stream."""
    _SEQCLASSES = (QZ, QA)

# Aide Sequences ##############################################################

class Temp(sequencetools.AideSequence):
    """Temporäre Variable (temporary variable) [-]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class AideSequences(sequencetools.AideSequences):
    """Aide sequences of HydPy-L-Stream."""
    _SEQCLASSES = (Temp,)

# Flux Sequences ##############################################################

class QRef(sequencetools.FluxSequence):
    """Referenzabfluss (reference flow) [m³/s]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class H(sequencetools.FluxSequence):
    """Wasserstand (water stage) [m]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class AM(sequencetools.FluxSequence):
    """Durchflossene Fläche Hauptgerinne (flown through area of the
    main channel) [m²]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class AL(sequencetools.FluxSequence):
    """Durchflossene Fläche linkes Vorland (flown through area of the
    left foreland) [m²]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class AR(sequencetools.FluxSequence):
    """Durchflossene Fläche rechtes Vorland (flown through area of the
    right foreland) [m²]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class AVRL(sequencetools.FluxSequence):
    """Durchflossene Fläche linke Böschung (flown through area of the
    left embankment) [m²]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class AVRR(sequencetools.FluxSequence):
    """Durchflossene Fläche rechte Böschung (flown through area of the
    right embankment) [m²]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class AG(sequencetools.FluxSequence):
    """Durchflossene Fläche gesamt  (total flown through area) [m²]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class UM(sequencetools.FluxSequence):
    """Benetzter Umfang Hauptgerinne (wetted perimeter of the
    main channel) [m²]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class UL(sequencetools.FluxSequence):
    """Benetzter Umfang linkes Vorland (wetted perimeter of the
    left foreland) [m²]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class UR(sequencetools.FluxSequence):
    """Benetzter Umfang rechtes Vorland (wetted perimeter of the
    right foreland) [m²]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class UVRL(sequencetools.FluxSequence):
    """Benetzter Umfanglinke Böschung (wetted perimeter of the
    left embankment) [m²]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class UVRR(sequencetools.FluxSequence):
    """Benetzter Umfang rechte Böschung (wetted perimeter of the
    right embankment) [m²]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class UG(sequencetools.FluxSequence):
    """Durchflossene Fläche gesamt  (total wetted perimeter) [m²]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class DAM(sequencetools.FluxSequence):
    """Ableitung von :class:`AM` (derivative of :class:`AM`) [m²]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class DAL(sequencetools.FluxSequence):
    """Ableitung von :class:`AL` (derivative of :class:`AL`) [m²]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class DAR(sequencetools.FluxSequence):
    """Ableitung von :class:`AR` (derivative of :class:`AR`) [m²]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class DAVRL(sequencetools.FluxSequence):
    """Ableitung von :class:`AVRL` (derivative of :class:`AVRL`) [m²]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class DAVRR(sequencetools.FluxSequence):
    """Ableitung von :class:`AVRR` (derivative of :class:`AVRR`) [m²]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class DAG(sequencetools.FluxSequence):
    """Ableitung von :class:`AG` (derivative of :class:`AG`) [m²]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class DUM(sequencetools.FluxSequence):
    """Ableitung von :class:`UM` (derivative of :class:`UM`) [m²]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class DUL(sequencetools.FluxSequence):
    """Ableitung von :class:`UL` (derivative of :class:`UL`) [m²]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class DUR(sequencetools.FluxSequence):
    """Ableitung von :class:`UR` (derivative of :class:`UR`) [m²]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class DUVRL(sequencetools.FluxSequence):
    """Ableitung von :class:`UVRL` (derivative of :class:`UVRL`) [m²]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class DUVRR(sequencetools.FluxSequence):
    """Ableitung von :class:`UVRR` (derivative of :class:`UVRR`) [m²]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class DUG(sequencetools.FluxSequence):
    """Ableitung von :class:`UG` (derivative of :class:`UG`) [m²]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class QM(sequencetools.FluxSequence):
    """Durchfluss Hauptgerinne (discharge of the main channel) [m²]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class QL(sequencetools.FluxSequence):
    """Durchfluss linkes Vorland (discharge of the left foreland) [m²]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class QR(sequencetools.FluxSequence):
    """Durchfluss rechtes Vorland (discharge of the right foreland) [m²]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class QVRL(sequencetools.FluxSequence):
    """Durchfluss linke Böschung (discharge of the left embankment) [m²]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class QVRR(sequencetools.FluxSequence):
    """Durchfluss rechte Böschung (discharge of the right embankment) [m²]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class QG(sequencetools.FluxSequence):
    """Durchfluss gesamt  (total discharge) [m²]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class DQM(sequencetools.FluxSequence):
    """Ableitung von :class:`QM` (derivative of :class:`QM`) [m²]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class DQL(sequencetools.FluxSequence):
    """Ableitung von :class:`QL` (derivative of :class:`QL`) [m²]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class DQR(sequencetools.FluxSequence):
    """Ableitung von :class:`QR` (derivative of :class:`QR`) [m²]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class DQVRL(sequencetools.FluxSequence):
    """Ableitung von :class:`QVRL` (derivative of :class:`QVRL`) [m²]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class DQVRR(sequencetools.FluxSequence):
    """Ableitung von :class:`QVRR` (derivative of :class:`QVRR`) [m²]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class DQG(sequencetools.FluxSequence):
    """Ableitung von :class:`QG` (derivative of :class:`QG`) [m²]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class RK(sequencetools.FluxSequence):
    """Schwerpunktlaufzeit (traveling time) [s]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class FluxSequences(sequencetools.FluxSequences):
    """Flux sequences of HydPy-L-Stream."""
    _SEQCLASSES = (QRef, H,
                   AM, AL, AR, AVRL, AVRR, AG,
                   UM, UL, UR, UVRL, UVRR, UG,
                   DAM, DAL, DAR, DAVRL, DAVRR, DAG,
                   DUM, DUL, DUR, DUVRL, DUVRR, DUG,
                   QM, QL, QR, QVRL, QVRR, QG,
                   DQM, DQL, DQR, DQVRL, DQVRR, DQG,
                   RK)

# Link Sequences ##############################################################

class Q(sequencetools.LinkSequence):
    """Abfluss (runoff) [m³/s]."""
    NDIM, NUMERIC = 0, False

class InletSequences(sequencetools.LinkSequences):
    """Upstream link sequences of HydPy-L-Stream."""
    _SEQCLASSES = (Q,)

class OutletSequences(sequencetools.LinkSequences):
    """Downstream link sequences of HydPy-L-Stream."""
    _SEQCLASSES = (Q,)

# Sequence container ##########################################################

class Sequences(sequencetools.Sequences):
    """All sequences of the hstream model."""

###############################################################################
# Model
###############################################################################

# Methods #####################################################################

def calc_qref_v1(self):
    """Determine the reference discharge within the given space-time intervall.

    Required state sequences:
      :class:`QZ`
      :class:`QA`

    Calculated flux sequence:
      :class:`QRef`

    Basic equation:
      :math:`QRef = \\frac{QZ_{new}+QZ_{old}+QA_{old}}{3}`

    Example:

        >>> from hydpy.models.lstream import *
        >>> parameterstep()
        >>> states.qz.new = 3.
        >>> states.qz.old = 2.
        >>> states.qa.old = 1.
        >>> model.calc_qref_v1()
        >>> fluxes.qref
        qref(2.0)
    """
    new = self.sequences.states.fastaccess_new
    old = self.sequences.states.fastaccess_old
    flu = self.sequences.fluxes.fastaccess
    flu.qref = (new.qz+old.qz+old.qa)/3.

def calc_rk_v1(self):
    """Determine the actual traveling time of the water (not of the wave!).

    Required derived parameter:
      :class:`Sek`

    Required flux sequences:
      :class:`A`
      :class:`QRef`

    Calculated flux sequence:
      :class:`RK`

    Basic equation:
      :math:`RK = \\frac{Len \\cdot A}{QRef}`

    Examples:

        First, note that the traveling time is determined in the unit of the
        actual simulation step size:

        >>> from hydpy.models.lstream import *
        >>> parameterstep()
        >>> len(25.)
        >>> derived.sek(24*60*60)
        >>> fluxes.ag = 10.
        >>> fluxes.qref = 1.
        >>> model.calc_rk_v1()
        >>> fluxes.rk
        rk(2.893519)

        Second, for negative values or zero values of :class:`A` or
        :class:`QRef`, the value of :class:`RK` is set to zero:

        >>> fluxes.ag = 0.
        >>> fluxes.qref = 1.
        >>> model.calc_rk_v1()
        >>> fluxes.rk
        rk(0.0)

        >>> fluxes.ag = 0.
        >>> fluxes.qref = 1.
        >>> model.calc_rk_v1()
        >>> fluxes.rk
        rk(0.0)

    """
    con = self.parameters.control.fastaccess
    der = self.parameters.derived.fastaccess
    flu = self.sequences.fluxes.fastaccess
    if (flu.ag > 0.) and (flu.qref > 0.):
        flu.rk = (1000.*con.len*flu.ag)/(der.sek*flu.qref)
    else:
        flu.rk = 0.

def calc_am_um_v1(self):
    """Calculate the flown through area and the wetted perimeter
    of the main channel.

    Note that the main channel is assumed to have identical slopes on
    both sides and that water flowing exactly above the main channel is
    contributing to :class:`AM`.  Both theoretical surfaces seperating
    water above the main channel from water above both forelands are
    contributing to :class:`UM`.

    Required control parameters:
      :class:`HM`
      :class:`BM`
      :class:`BNM`

    Required flux sequence:
      :class:`H`

    Calculated flux sequence:
      :class:`AM`
      :class:`UM`

    Examples:

        Generally, a trapezoid with reflection symmetry is assumed.  Here its
        smaller base (bottom) has a length of 2 meters, its legs show an
        inclination of 1 meter per 4 meters, and its height (depths) is 1
        meter:

        >>> from hydpy.models.lstream import *
        >>> parameterstep()
        >>> bm(2.)
        >>> bnm(4.)
        >>> hm(1.)

        The first example deals with normal flow conditions, where water flows
        within the main channel completely:
        (:class:`H` < :class:`HM`):

        >>> fluxes.h = .5
        >>> model.calc_am_um_v1()
        >>> fluxes.am
        am(2.0)
        >>> fluxes.um
        um(6.123106)

        The second example deals with high flow conditions, where water flows
        over the foreland also:
        (:class:`H` > :class:`HM`):

        >>> fluxes.h = 1.5
        >>> model.calc_am_um_v1()
        >>> fluxes.am
        am(11.0)
        >>> fluxes.um
        um(11.246211)
    """
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    if flu.h <= 0.:
        flu.am = 0.
    elif flu.h < con.hm:
        flu.am = flu.h*(con.bm+flu.h*con.bnm)
        flu.um = con.bm+2.*flu.h*(1.+con.bnm**2)**.5
    else:
        flu.am = (con.hm*(con.bm+con.hm*con.bnm) +
                  ((flu.h-con.hm)*(con.bm+2.*con.hm*con.bnm)))
        flu.um = (con.bm)+(2.*con.hm*(1.+con.bnm**2)**.5)+(2*(flu.h-con.hm))

def calc_qm_v1(self):
    """Calculate the discharge of the main channel after Manning-Strickler.

    Required control parameters:
      :class:`EKM`
      :class:`SKM`
      :class:`Gef`

    Required flux sequence:
      :class:`AM`
      :class:`UM`

    Calculated flux sequence:
      :class:`QM`

    Examples:

        For appropriate strictly positive values:

        >>> from hydpy.models.lstream import *
        >>> parameterstep()
        >>> ekm(2.)
        >>> skm(50.)
        >>> gef(.01)
        >>> fluxes.am = 3.
        >>> fluxes.um = 7.
        >>> model.calc_qm_v1()
        >>> fluxes.qm
        qm(17.053102)

        For zero or negative values of the flown through surface or
        the wetted perimeter:

        >>> fluxes.am = -1.
        >>> fluxes.um = 7.
        >>> model.calc_qm_v1()
        >>> fluxes.qm
        qm(0.0)

        >>> fluxes.am = 3.
        >>> fluxes.um = 0.
        >>> model.calc_qm_v1()
        >>> fluxes.qm
        qm(0.0)
    """
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    if (flu.am > 0.) and (flu.um > 0.):
        flu.qm = con.ekm*con.skm*flu.am**(5./3.)/flu.um**(2./3.)*con.gef**.5
    else:
        flu.qm = 0.

def calc_al_ul_v1(self):
    """Calculate the flown through area and the wetted perimeter
    of the left foreland.

    Note that the left foreland lies between the left embankment and the
    main channel and that water flowing exactly above the left foreland is
    contributing to :class:`AL`. The theoretical surface seperating water
    above the main channel from water above the foreland is not contributing
    to :class:`UL`, but the surface seperating water above the foreland
    from water above its embankment is contributing to :class:`UL`.

    Required control parameters:
      :class:`HM`
      :class:`BL`
      :class:`BNL`

    Required derived parameter:
      :class:`HL`

    Required flux sequence:
      :class:`H`

    Calculated flux sequence:
      :class:`AL`
      :class:`UL`

    Examples:

        Generally, a right trapezoid is assumed.  Here its smaller base
        (bottom) has a length of 2 meters, its non-vertical leg shows an
        inclination of 1 meter per 4 meters, and its height (depths) is 1
        meter.  The foreland lies 1 meter above the main channels bottom:

        >>> from hydpy.models.lstream import *
        >>> parameterstep()
        >>> hm(1.)
        >>> bl(2.)
        >>> bnl(4.)
        >>> derived.hl(1.)

        The first example deals with normal flow conditions, where water flows
        within the main channel completely:
        (:class:`H` < :class:`HM`):

        >>> fluxes.h = .5
        >>> model.calc_al_ul_v1()
        >>> fluxes.al
        al(0.0)
        >>> fluxes.ul
        ul(0.0)

        The second example deals with moderate high flow conditions, where
        water flows over the left foreland, but not over its embankment:
        (:class:`HM` < :class:`H` < :class:`HM` + :class:`HL`):

        >>> fluxes.h = 1.5
        >>> model.calc_al_ul_v1()
        >>> fluxes.al
        al(1.5)
        >>> fluxes.ul
        ul(4.061553)

        The third example deals with extreme high flow conditions, where
        water flows over the left foreland and its embankment:
        (:class:`HM` + :class:`HL` < :class:`H`):

        >>> fluxes.h = 2.5
        >>> model.calc_al_ul_v1()
        >>> fluxes.al
        al(7.0)
        >>> fluxes.ul
        ul(6.623106)
    """
    con = self.parameters.control.fastaccess
    der = self.parameters.derived.fastaccess
    flu = self.sequences.fluxes.fastaccess
    if flu.h <= con.hm:
        flu.al = 0.
        flu.ul = 0.
    elif flu.h <= (con.hm+der.hl):
        flu.al = (flu.h-con.hm)*(con.bl+(flu.h-con.hm)*con.bnl/2.)
        flu.ul = con.bl+(flu.h-con.hm)*(1.+con.bnl**2)**.5
    else:
        flu.al = (der.hl*(con.bl+der.hl*con.bnl/2.) +
                  ((flu.h-(con.hm+der.hl))*(con.bl+der.hl*con.bnl)))
        flu.ul = (con.bl)+(der.hl*(1.+con.bnl**2)**.5)+(flu.h-(con.hm+der.hl))

def calc_ql_v1(self):
    """Calculate the discharge of the left foreland after Manning-Strickler.

    Required control parameters:
      :class:`EKL`
      :class:`SKL`
      :class:`Gef`

    Required flux sequence:
      :class:`AL`
      :class:`UL`

    Calculated flux sequence:
      :class:`QL`

    Examples:

        For appropriate strictly positive values:

        >>> from hydpy.models.lstream import *
        >>> parameterstep()
        >>> ekl(2.)
        >>> skl(50.)
        >>> gef(.01)
        >>> fluxes.al = 3.
        >>> fluxes.ul = 7.
        >>> model.calc_ql_v1()
        >>> fluxes.ql
        ql(17.053102)

        For zero or negative values of the flown through surface or
        the wetted perimeter:

        >>> fluxes.al = -1.
        >>> fluxes.ul = 7.
        >>> model.calc_ql_v1()
        >>> fluxes.ql
        ql(0.0)

        >>> fluxes.al = 3.
        >>> fluxes.ul = 0.
        >>> model.calc_ql_v1()
        >>> fluxes.ql
        ql(0.0)
    """
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    if (flu.al > 0.) and (flu.ul > 0.):
        flu.ql = con.ekl*con.skl*flu.al**(5./3.)/flu.ul**(2./3.)*con.gef**.5
    else:
        flu.ql = 0.

def calc_ar_ur_v1(self):
    """Calculate the flown through area and the wetted perimeter
    of the left foreland.

    Note that the right foreland lies between the right embankment and
    the main channel and that water flowing exactly above right foreland
    is contributing to :class:`AR`.  The theoretical surface seperating water
    above the main channel from water above the foreland is not contributing
    to :class:`UR`, but the surface seperating water above the foreland
    from water above its embankment is contributing to :class:`UR`.

    Required control parameters:
      :class:`HM`
      :class:`BR`
      :class:`BNR`

    Required derived parameter:
      :class:`HR`

    Required flux sequence:
      :class:`H`

    Calculated flux sequence:
      :class:`AR`
      :class:`UR`

    Examples:

        Generally, a right trapezoid is assumed.  Here its smaller base
        (bottom) has a length of 2 meters, its non-vertical leg shows an
        inclination of 1 meter per 4 meters, and its height (depths) is 1
        meter.  The foreland lies 1 meter above the main channels bottom:

        >>> from hydpy.models.lstream import *
        >>> parameterstep()
        >>> hm(1.)
        >>> br(2.)
        >>> bnr(4.)
        >>> derived.hr(1.)

        The first example deals with normal flow conditions, where water flows
        within the main channel completely:
        (:class:`H` < :class:`HM`):

        >>> fluxes.h = .5
        >>> model.calc_ar_ur_v1()
        >>> fluxes.ar
        ar(0.0)
        >>> fluxes.ur
        ur(0.0)

        The second example deals with moderate high flow conditions, where
        water flows over the right foreland, but not over its embankment:
        (:class:`HM` < :class:`H` < :class:`HM` + :class:`HR`):

        >>> fluxes.h = 1.5
        >>> model.calc_ar_ur_v1()
        >>> fluxes.ar
        ar(1.5)
        >>> fluxes.ur
        ur(4.061553)

        The third example deals with extreme high flow conditions, where
        water flows over the right foreland and its embankment:
        (:class:`HM` + :class:`HR` < :class:`H`):

        >>> fluxes.h = 2.5
        >>> model.calc_ar_ur_v1()
        >>> fluxes.ar
        ar(7.0)
        >>> fluxes.ur
        ur(6.623106)
    """
    con = self.parameters.control.fastaccess
    der = self.parameters.derived.fastaccess
    flu = self.sequences.fluxes.fastaccess
    if flu.h <= con.hm:
        flu.ar = 0.
        flu.ur = 0.
    elif flu.h <= (con.hm+der.hr):
        flu.ar = (flu.h-con.hm)*(con.br+(flu.h-con.hm)*con.bnr/2.)
        flu.ur = con.br+(flu.h-con.hm)*(1.+con.bnr**2)**.5
    else:
        flu.ar = (der.hr*(con.br+der.hr*con.bnr/2.) +
                  ((flu.h-(con.hm+der.hr))*(con.br+der.hr*con.bnr)))
        flu.ur = (con.br)+(der.hr*(1.+con.bnr**2)**.5)+(flu.h-(con.hm+der.hr))

def calc_qr_v1(self):
    """Calculate the discharge of the right foreland after Manning-Strickler.

    Required control parameters:
      :class:`EKR`
      :class:`SKR`
      :class:`Gef`

    Required flux sequence:
      :class:`AR`
      :class:`UR`

    Calculated flux sequence:
      :class:`QR`

    Examples:

        For appropriate strictly positive values:

        >>> from hydpy.models.lstream import *
        >>> parameterstep()
        >>> ekr(2.)
        >>> skr(50.)
        >>> gef(.01)
        >>> fluxes.ar = 3.
        >>> fluxes.ur = 7.
        >>> model.calc_qr_v1()
        >>> fluxes.qr
        qr(17.053102)

        For zero or negative values of the flown through surface or
        the wetted perimeter:

        >>> fluxes.ar = -1.
        >>> fluxes.ur = 7.
        >>> model.calc_qr_v1()
        >>> fluxes.qr
        qr(0.0)

        >>> fluxes.ar = 3.
        >>> fluxes.ur = 0.
        >>> model.calc_qr_v1()
        >>> fluxes.qr
        qr(0.0)
    """
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    if (flu.ar > 0.) and (flu.ur > 0.):
        flu.qr = con.ekr*con.skr*flu.ar**(5./3.)/flu.ur**(2./3.)*con.gef**.5
    else:
        flu.qr = 0.

def calc_avrl_uvrl_v1(self):
    """Calculate the flown through area and the wetted perimeter of the
    left river embankment.

    Note that the left embankment lies beyond the left foreland and that all
    water flowing exactly above the left embankment is added to :class:`AVRL`.
    The theoretical surface seperating water above the foreland from water
    above its embankment is not contributing to :class:`UVRL`.

    Required control parameters:
      :class:`HM`
      :class:`BNVRL`

    Required derived parameter:
      :class:`HL`

    Required flux sequence:
      :class:`H`

    Calculated flux sequence:
      :class:`AVRL`
      :class:`UVRL`

    Examples:

        Generally, a simple triangle is assumed, with a vertical side
        seperating foreland and embankment.  Here the embankments
        inclination is 1 meter per 4 meters and its lowest point is
        1 meter above the forelands bottom and 2 meters above the main
        channels bottom:

        >>> from hydpy.models.lstream import *
        >>> parameterstep()
        >>> hm(1.)
        >>> bnvrl(4.)
        >>> derived.hl(1.)

        The first example deals with moderate high flow conditions, where
        water flows over the left foreland, but not over its embankment:
        (:class:`HM` < :class:`H` < :class:`HM` + :class:`HL`):

        >>> fluxes.h = 1.5
        >>> model.calc_avrl_uvrl_v1()
        >>> fluxes.avrl
        avrl(0.0)
        >>> fluxes.uvrl
        uvrl(0.0)

        The second example deals with extreme high flow conditions, where
        water flows over the left foreland and its embankment:
        (:class:`HM` + :class:`HL` < :class:`H`):

        >>> fluxes.h = 2.5
        >>> model.calc_avrl_uvrl_v1()
        >>> fluxes.avrl
        avrl(0.5)
        >>> fluxes.uvrl
        uvrl(2.061553)
    """
    con = self.parameters.control.fastaccess
    der = self.parameters.derived.fastaccess
    flu = self.sequences.fluxes.fastaccess
    if flu.h <= (con.hm+der.hl):
        flu.avrl = 0.
        flu.uvrl = 0.
    else:
        flu.avrl = (flu.h-(con.hm+der.hl))**2*con.bnvrl/2.
        flu.uvrl = (flu.h-(con.hm+der.hl))*(1.+con.bnvrl**2)**.5

def calc_qvrl_v1(self):
    """Calculate the discharge of the left embankment after Manning-Strickler.

    Required control parameters:
      :class:`EKL`
      :class:`SKL`
      :class:`Gef`

    Required flux sequence:
      :class:`AVRL`
      :class:`UVRL`

    Calculated flux sequence:
      :class:`QVRL`

    Examples:

        For appropriate strictly positive values:

        >>> from hydpy.models.lstream import *
        >>> parameterstep()
        >>> ekl(2.)
        >>> skl(50.)
        >>> gef(.01)
        >>> fluxes.avrl = 3.
        >>> fluxes.uvrl = 7.
        >>> model.calc_qvrl_v1()
        >>> fluxes.qvrl
        qvrl(17.053102)

        For zero or negative values of the flown through surface or
        the wetted perimeter:

        >>> fluxes.avrl = -1.
        >>> fluxes.uvrl = 7.
        >>> model.calc_qvrl_v1()
        >>> fluxes.qvrl
        qvrl(0.0)

        >>> fluxes.avrl = 3.
        >>> fluxes.uvrl = 0.
        >>> model.calc_qvrl_v1()
        >>> fluxes.qvrl
        qvrl(0.0)
    """
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    if (flu.avrl > 0.) and (flu.uvrl > 0.):
        flu.qvrl = (con.ekl*con.skl*flu.avrl**(5./3.)/flu.uvrl**(2./3.) *
                    con.gef**.5)
    else:
        flu.qvrl = 0.

def calc_avrr_uvrr_v1(self):
    """Calculate the flown through area and the wetted perimeter
    of the right foreland.

    Note that the right embankment lies beyond the right foreland and that all
    water flowing exactly above the right embankment is added to :class:`AVRR`.
    The theoretical surface seperating water above the foreland from water
    above its embankment is not contributing to :class:`UVRR`.

    Required control parameters:
      :class:`HM`
      :class:`BNVRR`

    Required derived parameter:
      :class:`HL`

    Required flux sequence:
      :class:`H`

    Calculated flux sequence:
      :class:`AVRR`
      :class:`UVRR`

    Examples:

        Generally, a simple triangle is assumed, with a vertical side
        seperating foreland and embankment.  Here the embankments
        inclination is 1 meter per 4 meters and its lowest point is
        1 meter above the forelands bottom and 2 meters above the main
        channels bottom:

        >>> from hydpy.models.lstream import *
        >>> parameterstep()
        >>> hm(1.)
        >>> bnvrr(4.)
        >>> derived.hr(1.)

        The first example deals with moderate high flow conditions, where
        water flows over the right foreland, but not over its embankment:
        (:class:`HM` < :class:`H` < :class:`HM` + :class:`HR`):

        >>> fluxes.h = 1.5
        >>> model.calc_avrr_uvrr_v1()
        >>> fluxes.avrr
        avrr(0.0)
        >>> fluxes.uvrr
        uvrr(0.0)

        The second example deals with extreme high flow conditions, where
        water flows over the right foreland and its embankment:
        (:class:`HM` + :class:`HR` < :class:`H`):

        >>> fluxes.h = 2.5
        >>> model.calc_avrr_uvrr_v1()
        >>> fluxes.avrr
        avrr(0.5)
        >>> fluxes.uvrr
        uvrr(2.061553)
    """
    con = self.parameters.control.fastaccess
    der = self.parameters.derived.fastaccess
    flu = self.sequences.fluxes.fastaccess
    if flu.h <= (con.hm+der.hr):
        flu.avrr = 0.
        flu.uvrr = 0.
    else:
        flu.avrr = (flu.h-(con.hm+der.hr))**2*con.bnvrr/2.
        flu.uvrr = (flu.h-(con.hm+der.hr))*(1.+con.bnvrr**2)**.5

def calc_qvrr_v1(self):
    """Calculate the discharge of the right embankment after Manning-Strickler.

    Required control parameters:
      :class:`EKR`
      :class:`SKR`
      :class:`Gef`

    Required flux sequence:
      :class:`AVRR`
      :class:`UVRR`

    Calculated flux sequence:
      :class:`QVRR`

    Examples:

        For appropriate strictly positive values:

        >>> from hydpy.models.lstream import *
        >>> parameterstep()
        >>> ekl(2.)
        >>> skl(50.)
        >>> gef(.01)
        >>> fluxes.avrr = 3.
        >>> fluxes.uvrr = 7.
        >>> model.calc_qvrr_v1()
        >>> fluxes.qvrr
        qvrr(17.053102)

        For zero or negative values of the flown through surface or
        the wetted perimeter:

        >>> fluxes.avrr = -1.
        >>> fluxes.uvrr = 7.
        >>> model.calc_qvrr_v1()
        >>> fluxes.qvrr
        qvrr(0.0)

        >>> fluxes.avrr = 3.
        >>> fluxes.uvrr = 0.
        >>> model.calc_qvrr_v1()
        >>> fluxes.qvrr
        qvrr(0.0)
    """
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    if (flu.avrr > 0.) and (flu.uvrr > 0.):
        flu.qvrr = (con.ekl*con.skl*flu.avrr**(5./3.)/flu.uvrr**(2./3.) *
                    con.gef**.5)
    else:
        flu.qvrr = 0.

def calc_qg_v1(self):
    flu = self.sequences.fluxes.fastaccess
    flu.qg = flu.qm+flu.ql+flu.qr+flu.qvrl+flu.qvrr

def calc_h_v1(self):
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    aid = self.sequences.aides.fastaccess
    aid.f = con.maxf+1.
    self.calc_qref_v1()
    while abs(aid.f) > con.maxf:
        self.calc_am_um_v1()
        self.calc_qm_v1()
        self.calc_al_ul_v1()
        self.calc_ql_v1()
        self.calc_ar_ur_v1()
        self.calc_qr_v1()
        self.calc_avrl_uvrl_v1()
        self.calc_qvrl_v1()
        self.calc_avrr_uvrr_v1()
        self.calc_qvrr_v1()
        aid.f = flu.qg-flu.qref
        flu.h = max(flu.h-aid.f/flu.dqg, 0.)

def calc_qa_v1(self):
    """Calculate outflow.

    The working equation is the analytical solution of the linear storage
    equation under the assumption of constant change in inflow during
    the simulation time step.

    Required flux sequence:
      :class:`RK`

    Required state sequence:
      :class:`QZ`

    Updated state sequence:
      :class:`QA`

    Basic equation:
       :math:`QA_{neu} = QA_{alt} +
       (QZ_{alt}-QA_{alt}) \\cdot (1-exp(-RK^{-1})) +
       (QZ_{neu}-QZ_{alt}) \\cdot (1-KR\\cdot(1-exp(-KR^{-1})))`

    Examples:

        A normal test case:

        >>> from hydpy.models.lstream import *
        >>> parameterstep()
        >>> fluxes.rk(0.1)
        >>> states.qz.old = 2.
        >>> states.qz.new = 4.
        >>> states.qa.old = 3.
        >>> model.calc_qa_v1()
        >>> states.qa
        qa(3.800054)

        First extreme test case (zero division is circumvented):

        >>> fluxes.rk(0.)
        >>> model.calc_qa_v1()
        >>> states.qa
        qa(4.0)

        Second extreme test case (numerical overflow is circumvented):

        >>> fluxes.rk(1e200)
        >>> model.calc_qa_v1()
        >>> states.qa
        qa(5.0)
    """
    flu = self.sequences.fluxes.fastaccess
    old = self.sequences.states.fastaccess_old
    new = self.sequences.states.fastaccess_new
    aid = self.sequences.aides.fastaccess
    if flu.rk <= 0.:
        new.qa = new.qz
    elif flu.rk > 1e200:
        new.qa = old.qa+new.qz-old.qz
    else:
        aid.temp = (1.-modelutils.exp(-1./flu.rk))
        new.qa = (old.qa +
                   (old.qz-old.qa)*aid.temp +
                   (new.qz-old.qz)*(1.-flu.rk*aid.temp))

def update_inlets_v1(self):
    """Update inflow."""
    sta = self.sequences.states.fastaccess
    inl = self.sequences.inlets.fastaccess
    sta.qz = inl.q[0]

def update_outlets_v1(self):
    """Update outflow."""
    sta = self.sequences.states.fastaccess
    out = self.sequences.outlets.fastaccess
    out.q[0] += sta.qa

# Model class #################################################################

class Model(modeltools.Model):
    """The HydPy-H-Stream model."""
    _RUNMETHODS = (calc_qref_v1,
                   calc_rk_v1,
                   calc_qa_v1,
                   update_inlets_v1,
                   update_outlets_v1)
    _ADDMETHODS = (calc_am_um_v1,
                   calc_qm_v1,
                   calc_al_ul_v1,
                   calc_ql_v1,
                   calc_ar_ur_v1,
                   calc_qr_v1,
                   calc_avrl_uvrl_v1,
                   calc_qvrl_v1,
                   calc_avrr_uvrr_v1,
                   calc_qvrr_v1)


tester = Tester()
cythonizer = Cythonizer()
cythonizer.complete()
