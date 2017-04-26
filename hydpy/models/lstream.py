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
    channel) [m⅓/s]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

class SKV(parametertools.LeftRightParameter):
    """Rauigkeitsbeiwert Vorländer (roughness coefficient of the both
    forelands) [m⅓/s]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

class EKM(parametertools.SingleParameter):
    """Kalibrierfaktor Hauptgerinne (calibration factor for the main
    channel) [-]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)

class EKV(parametertools.LeftRightParameter):
    """Kalibrierfaktor Vorländer (calibration factor for both forelands) [m].
    """
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

class MaxF(parametertools.SingleParameter):
    """Abbruchkriterium Newton-Raphson-Iteration (stopping criterion for the
    Newton iteration method) [m³/s]."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (0., None)
    INIT = 1e-6

class ControlParameters(parametertools.SubParameters):
    """Control parameters HydPy-L-Stream, directly defined by the user."""
    _PARCLASSES = (Len, Gef, HM, BM, BV, BBV, BNM, BNV, BNVR,
                   SKM, SKV, EKM, EKV, MaxF)
# Derived Parameters ##########################################################

class HV(parametertools.LeftRightParameter):
    """Höhe Vorländer (height of both forelands) [m]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0., None)

    def update(self):
        """Update value based on :math:`HV=BBV/BNV`.

        Required Parameters:
            :class:`BBV`
            :class:`BNV`

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
        for idx in range(2):
            if (con.bbv[idx] > 0.) and (con.bnv[idx] > 0.):
                self[idx] = con.bbv[idx]/con.bnv[idx]
            else:
                self[idx] = 0.

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
    """Derived parameters of HydPy-L-Stream, indirectly defined by the user."""
    _PARCLASSES = (HV, Sek)

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

class AV(sequencetools.LeftRightSequence):
    """Durchflossene Fläche Vorländer (flown through area of both forelands)
    [m²]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)

class AVR(sequencetools.LeftRightSequence):
    """Durchflossene Fläche Vorlandränder (flown through area of both outer
    embankments) [m²]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)

class AG(sequencetools.FluxSequence):
    """Durchflossene Fläche gesamt  (total flown through area) [m²]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class UM(sequencetools.FluxSequence):
    """Benetzter Umfang Hauptgerinne (wetted perimeter of the
    main channel) [m]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class UV(sequencetools.LeftRightSequence):
    """Benetzter Umfang Vorländer (wetted perimeter of both forelands) [m]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)

class UVR(sequencetools.LeftRightSequence):
    """Benetzter Umfang Vorlandränder (wetted perimeter of both outer
    embankments) [m]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)

class UG(sequencetools.FluxSequence):
    """Durchflossene Fläche gesamt  (total wetted perimeter) [m]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class DAM(sequencetools.FluxSequence):
    """Ableitung von :class:`AM` (derivative of :class:`AM`) [m²/m]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class DAV(sequencetools.LeftRightSequence):
    """Ableitung von :class:`AV` (derivative of :class:`AV`) [m²/m]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)

class DAVR(sequencetools.LeftRightSequence):
    """Ableitung von :class:`AVR` (derivative of :class:`AVR`) [m²/m]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)

class DAG(sequencetools.FluxSequence):
    """Ableitung von :class:`AG` (derivative of :class:`AG`) [m²/m]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class DUM(sequencetools.FluxSequence):
    """Ableitung von :class:`UM` (derivative of :class:`UM`) [m/m]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class DUV(sequencetools.LeftRightSequence):
    """Ableitung von :class:`UV` (derivative of :class:`UV`) [m/m]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)

class DUVR(sequencetools.LeftRightSequence):
    """Ableitung von :class:`UVR` (derivative of :class:`UVR`) [m/m]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)

class DUG(sequencetools.FluxSequence):
    """Ableitung von :class:`UG` (derivative of :class:`UG`) [m/m]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class QM(sequencetools.FluxSequence):
    """Durchfluss Hauptgerinne (discharge of the main channel) [m³]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class QV(sequencetools.LeftRightSequence):
    """Durchfluss Voränder (discharge of both forelands) [m³]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)

class QVR(sequencetools.LeftRightSequence):
    """Durchfluss Vorlandränder (discharge of both outer embankment) [m³]."""
    NDIM, NUMERIC, SPAN = 1, False, (1., None)

class QG(sequencetools.FluxSequence):
    """Durchfluss gesamt  (total discharge) [m³]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class DQM(sequencetools.FluxSequence):
    """Ableitung von :class:`QM` (derivative of :class:`QM`) [m³/m²]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class DQV(sequencetools.LeftRightSequence):
    """Ableitung von :class:`QV` (derivative of :class:`QV`) [m³/m²]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)

class DQVR(sequencetools.LeftRightSequence):
    """Ableitung von :class:`QVR` (derivative of :class:`QVR`) [m³/m²]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)

class DQG(sequencetools.FluxSequence):
    """Ableitung von :class:`QG` (derivative of :class:`QG`) [m³/m²]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class RK(sequencetools.FluxSequence):
    """Schwerpunktlaufzeit (traveling time) [s]."""
    NDIM, NUMERIC, SPAN = 0, False, (0., None)

class FluxSequences(sequencetools.FluxSequences):
    """Flux sequences of HydPy-L-Stream."""
    _SEQCLASSES = (QRef, H,
                   AM, AV, AVR, AG, UM, UV, UVR, UG,
                   DAM, DAV, DAVR, DAG, DUM, DUV, DUVR, DUG,
                   QM, QV, QVR, QG, DQM, DQV, DQVR, DQG,
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
    """All sequences of HydPy-L-Stream."""

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

        The third example checks the special case of a main channel with zero
        height:

        >>> hm(0.)
        >>> model.calc_am_um_v1()
        >>> fluxes.am
        am(3.0)
        >>> fluxes.um
        um(5.0)

        The fourth example checks the special case of the actual water stage
        not beeing larger than zero (empty channel, note the):

        >>> fluxes.h = 0.
        >>> model.calc_am_um_v1()
        >>> fluxes.am
        am(0.0)
        >>> fluxes.um
        um(0.0)
    """
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    if flu.h <= 0.:
        flu.am = 0.
        flu.um = 0.
    elif flu.h < con.hm:
        flu.am = flu.h*(con.bm+flu.h*con.bnm)
        flu.um = con.bm+2.*flu.h*(1.+con.bnm**2)**.5
    else:
        flu.am = (con.hm*(con.bm+con.hm*con.bnm) +
                  ((flu.h-con.hm)*(con.bm+2.*con.hm*con.bnm)))
        flu.um = (con.bm)+(2.*con.hm*(1.+con.bnm**2)**.5)+(2*(flu.h-con.hm))

def calc_dam_dum_v1(self):
    """Calculate the the changes in the flown through area and the wetted
    perimeter with regard to water stage changes of the main channel.

    Method :func:`calc_dam_dum_v1` and the following examples rely on the same
    geometrical assumtions described for method :func:`calc_am_um_v1`.

    Required control parameters:
      :class:`HM`
      :class:`BM`
      :class:`BNM`

    Required flux sequence:
      :class:`H`

    Calculated flux sequence:
      :class:`DAM`
      :class:`DUM`

    Examples:

        The base scenario of the examples of method :func:`calc_am_um_v1` is
        reused:

        >>> from hydpy.models.lstream import *
        >>> parameterstep()
        >>> bm(2.)
        >>> bnm(4.)
        >>> hm(1.)

        The first example deals with normal flow conditions, where water flows
        within the main channel completely:
        (:class:`H` < :class:`HM`):

        >>> fluxes.h = .5
        >>> model.calc_dam_dum_v1()
        >>> fluxes.dam
        dam(6.0)
        >>> fluxes.dum
        dum(6.123106)

        The second example deals with high flow conditions, where water flows
        over the foreland also:
        (:class:`H` > :class:`HM`):

        >>> fluxes.h = 1.5
        >>> model.calc_dam_dum_v1()
        >>> fluxes.dam
        dam(10.0)
        >>> fluxes.dum
        dum(11.246211)

        The third example checks the special case of a main channel with zero
        height:

        >>> hm(0.)
        >>> model.calc_dam_dum_v1()
        >>> fluxes.dam
        dam(3.0)
        >>> fluxes.dum
        dum(5.0)

        The fourth example checks the special case of the actual water stage
        not beeing larger than zero (empty channel, note the):

        >>> fluxes.h = -1.
        >>> model.calc_dam_dum_v1()
        >>> fluxes.dam
        dam(0.0)
        >>> fluxes.dum
        dum(0.0)
    """
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    if flu.h < con.hm:
        flu.dam = con.bm+2.*flu.h*con.bnm
        flu.dum = 2.*(1.+con.bnm**2)**.5
    else:
        flu.dam = con.bm+2.*con.hm*con.bnm
        flu.dum = 2.

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

def calc_av_uv_v1(self):
    """Calculate the flown through area and the wetted perimeter of both
    forelands.

    Note that the each foreland lies between the main channel and one
    outer embankment and that water flowing exactly above the a foreland is
    contributing to :class:`AV`. The theoretical surface seperating water
    above the main channel from water above the foreland is not contributing
    to :class:`UV`, but the surface seperating water above the foreland
    from water above its outer embankment is contributing to :class:`UV`.

    Required control parameters:
      :class:`HM`
      :class:`BV`
      :class:`BNV`

    Required derived parameter:
      :class:`HV`

    Required flux sequence:
      :class:`H`

    Calculated flux sequence:
      :class:`AV`
      :class:`UV`

    Examples:

        Generally, right trapezoids are assumed.  Here, for simplicity, both
        forelands are assumed to be symmetrical.  Their smaller bases (bottoms)
        hava a length of 2 meters, their non-vertical legs show an inclination
        of 1 meter per 4 meters, and their height (depths) is 1 meter.  Both
        forelands lie 1 meter above the main channels bottom.

        >>> from hydpy.models.lstream import *
        >>> parameterstep()
        >>> hm(1.)
        >>> bv(2.)
        >>> bnv(4.)
        >>> derived.hv(1.)

        The first example deals with normal flow conditions, where water flows
        within the main channel completely:
        (:class:`H` < :class:`HM`):

        >>> fluxes.h = .5
        >>> model.calc_av_uv_v1()
        >>> fluxes.av
        av(0.0, 0.0)
        >>> fluxes.uv
        uv(0.0, 0.0)

        The second example deals with moderate high flow conditions, where
        water flows over both forelands, but not over their embankments:
        (:class:`HM` < :class:`H` < :class:`HM` + :class:`HV`):

        >>> fluxes.h = 1.5
        >>> model.calc_av_uv_v1()
        >>> fluxes.av
        av(1.5, 1.5)
        >>> fluxes.uv
        uv(4.061553, 4.061553)

        The third example deals with extreme high flow conditions, where
        water flows over the both foreland and their outer embankments:
        (:class:`HM` + :class:`HV` < :class:`H`):

        >>> fluxes.h = 2.5
        >>> model.calc_av_uv_v1()
        >>> fluxes.av
        av(7.0, 7.0)
        >>> fluxes.uv
        uv(6.623106, 6.623106)

        The forth example assures that zero widths or hights of the forelands
        are handled properly:

        >>> bv.left = 0.
        >>> derived.hv.right = 0.
        >>> model.calc_av_uv_v1()
        >>> fluxes.av
        av(4.0, 3.0)
        >>> fluxes.uv
        uv(4.623106, 3.5)
    """
    con = self.parameters.control.fastaccess
    der = self.parameters.derived.fastaccess
    flu = self.sequences.fluxes.fastaccess
    for i in range(2):
        if flu.h <= con.hm:
            flu.av[i] = 0.
            flu.uv[i] = 0.
        elif flu.h <= (con.hm+der.hv[i]):
            flu.av[i] = (flu.h-con.hm)*(con.bv[i]+(flu.h-con.hm)*con.bnv[i]/2.)
            flu.uv[i] = con.bv[i]+(flu.h-con.hm)*(1.+con.bnv[i]**2)**.5
        else:
            flu.av[i] = (der.hv[i]*(con.bv[i]+der.hv[i]*con.bnv[i]/2.) +
                         ((flu.h-(con.hm+der.hv[i])) *
                          (con.bv[i]+der.hv[i]*con.bnv[i])))
            flu.uv[i] = ((con.bv[i])+(der.hv[i]*(1.+con.bnv[i]**2)**.5) +
                         (flu.h-(con.hm+der.hv[i])))

def calc_qv_v1(self):
    """Calculate the discharge of both forelands after Manning-Strickler.

    Required control parameters:
      :class:`EKV`
      :class:`SKV`
      :class:`Gef`

    Required flux sequence:
      :class:`AV`
      :class:`UV`

    Calculated flux sequence:
      :class:`QV`

    Examples:

        For appropriate strictly positive values:

        >>> from hydpy.models.lstream import *
        >>> parameterstep()
        >>> ekv(2.)
        >>> skv(50.)
        >>> gef(.01)
        >>> fluxes.av = 3.
        >>> fluxes.uv = 7.
        >>> model.calc_qv_v1()
        >>> fluxes.qv
        qv(17.053102, 17.053102)

        For zero or negative values of the flown through surface or
        the wetted perimeter:

        >>> fluxes.av = -1., 3.
        >>> fluxes.uv = 7., 0.
        >>> model.calc_qv_v1()
        >>> fluxes.qv
        qv(0.0, 0.0)
    """
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    for i in range(2):
        if (flu.av[i] > 0.) and (flu.uv[i] > 0.):
            flu.qv[i] = (con.ekv[i]*con.skv[i] *
                         flu.av[i]**(5./3.)/flu.uv[i]**(2./3.)*con.gef**.5)
        else:
            flu.qv[i] = 0.

def calc_avr_uvr_v1(self):
    """Calculate the flown through area and the wetted perimeter of both
    outer embankments.

    Note that each outer embankment lies beyond its foreland and that all
    water flowing exactly above the a embankment is added to :class:`AVR`.
    The theoretical surface seperating water above the foreland from water
    above its embankment is not contributing to :class:`UVR`.

    Required control parameters:
      :class:`HM`
      :class:`BNVR`

    Required derived parameter:
      :class:`HV`

    Required flux sequence:
      :class:`H`

    Calculated flux sequence:
      :class:`AVR`
      :class:`UVR`

    Examples:

        Generally, right trapezoids are assumed.  Here, for simplicity, both
        forelands are assumed to be symmetrical.  Their smaller bases (bottoms)
        hava a length of 2 meters, their non-vertical legs show an inclination
        of 1 meter per 4 meters, and their height (depths) is 1 meter.  Both
        forelands lie 1 meter above the main channels bottom.

        Generally, a triangles are assumed, with the vertical side
        seperating the foreland from its outer embankment.  Here, for
        simplicity, both forelands are assumed to be symmetrical.  Their
        inclinations are 1 meter per 4 meters and their lowest point is
        1 meter above the forelands bottom and 2 meters above the main
        channels bottom:

        >>> from hydpy.models.lstream import *
        >>> parameterstep()
        >>> hm(1.)
        >>> bnvr(4.)
        >>> derived.hv(1.)

        The first example deals with moderate high flow conditions, where
        water flows over the forelands, but not over their outer embankments:
        (:class:`HM` < :class:`H` < :class:`HM` + :class:`HV`):

        >>> fluxes.h = 1.5
        >>> model.calc_avr_uvr_v1()
        >>> fluxes.avr
        avr(0.0, 0.0)
        >>> fluxes.uvr
        uvr(0.0, 0.0)

        The second example deals with extreme high flow conditions, where
        water flows over the both foreland and their outer embankments:
        (:class:`HM` + :class:`HV` < :class:`H`):

        >>> fluxes.h = 2.5
        >>> model.calc_avr_uvr_v1()
        >>> fluxes.avr
        avr(0.5, 0.5)
        >>> fluxes.uvr
        uvr(2.061553, 2.061553)
    """
    con = self.parameters.control.fastaccess
    der = self.parameters.derived.fastaccess
    flu = self.sequences.fluxes.fastaccess
    for i in range(2):
        if flu.h <= (con.hm+der.hv[i]):
            flu.avr[i] = 0.
            flu.uvr[i] = 0.
        else:
            flu.avr[i] = (flu.h-(con.hm+der.hv[i]))**2*con.bnvr[i]/2.
            flu.uvr[i] = (flu.h-(con.hm+der.hv[i]))*(1.+con.bnvr[i]**2)**.5

def calc_qvr_v1(self):
    """Calculate the discharge of both outer embankments after
    Manning-Strickler.

    Required control parameters:
      :class:`EKV`
      :class:`SKV`
      :class:`Gef`

    Required flux sequence:
      :class:`AVR`
      :class:`UVR`

    Calculated flux sequence:
      :class:`QVR`

    Examples:

        For appropriate strictly positive values:

        >>> from hydpy.models.lstream import *
        >>> parameterstep()
        >>> ekv(2.)
        >>> skv(50.)
        >>> gef(.01)
        >>> fluxes.avr = 3.
        >>> fluxes.uvr = 7.
        >>> model.calc_qvr_v1()
        >>> fluxes.qvr
        qvr(17.053102, 17.053102)

        For zero or negative values of the flown through surface or
        the wetted perimeter:

        >>> fluxes.avr = -1., 3.
        >>> fluxes.uvr = 7., 0.
        >>> model.calc_qvr_v1()
        >>> fluxes.qvr
        qvr(0.0, 0.0)
    """
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    for i in range(2):
        if (flu.avr[i] > 0.) and (flu.uvr[i] > 0.):
            flu.qvr[i] = (con.ekv[i]*con.skv[i] *
                          flu.avr[i]**(5./3.)/flu.uvr[i]**(2./3.)*con.gef**.5)
        else:
            flu.qvr[i] = 0.

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
        self.calc_av_uv_v1()
        self.calc_qv_v1()
        self.calc_avr_vr_v1()
        self.calc_qvr_v1()
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
                   calc_av_uv_v1,
                   calc_qv_v1,
                   calc_avr_uvr_v1,
                   calc_qvr_v1)


tester = Tester()
cythonizer = Cythonizer()
cythonizer.complete()
