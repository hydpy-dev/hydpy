# -*- coding: utf-8 -*-

# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import modeltools
from hydpy.cythons import modelutils


def calc_qref_v1(self):
    """Determine the reference discharge within the given space-time intervall.

    Required state sequences:
      :class:`~hydpy.model.lstream.lstream_states.QZ`
      :class:`~hydpy.model.lstream.lstream_states.QA`

    Calculated flux sequence:
      :class:`~hydpy.model.lstream.lstream_fluxes.QRef`

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
      :class:`~hydpy.model.lstream.lstream_derived.Sek`

    Required flux sequences:
      :class:`~hydpy.model.lstream.lstream_fluxes.A`
      :class:`~hydpy.model.lstream.lstream_fluxes.QRef`

    Calculated flux sequence:
      :class:`~hydpy.model.lstream.lstream_fluxes.RK`

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

        Second, for negative values or zero values of
        :class:`~hydpy.model.lstream.lstream_fluxes.A` or
        :class:`~hydpy.model.lstream.lstream_fluxes.QRef`, the value of
        :class:`~hydpy.model.lstream.lstream_fluxes.RK` is set to zero:

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
    contributing to :class:`~hydpy.model.lstream.lstream_fluxes.AM`.
    Both theoretical surfaces seperating water above the main channel
    from water above both forelands are contributing to
    :class:`~hydpy.model.lstream.lstream_fluxes.UM`.

    Required control parameters:
      :class:`~hydpy.model.lstream.lstream_control.HM`
      :class:`~hydpy.model.lstream.lstream_control.BM`
      :class:`~hydpy.model.lstream.lstream_control.BNM`

    Required flux sequence:
      :class:`~hydpy.model.lstream.lstream_fluxes.H`

    Calculated flux sequence:
      :class:`~hydpy.model.lstream.lstream_fluxes.AM`
      :class:`~hydpy.model.lstream.lstream_fluxes.UM`

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
        (:class:`~hydpy.model.lstream.lstream_fluxes.H` <
        :class:`~hydpy.model.lstream.lstream_control.HM`):

        >>> fluxes.h = .5
        >>> model.calc_am_um_v1()
        >>> fluxes.am
        am(2.0)
        >>> fluxes.um
        um(6.123106)

        The second example deals with high flow conditions, where water flows
        over the foreland also:
        (:class:`~hydpy.model.lstream.lstream_fluxes.H` >
        :class:`~hydpy.model.lstream.lstream_control.HM`):

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
        not beeing larger than zero (empty channel):

        >>> fluxes.h = 0.
        >>> hm(1.)
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

def calc_qm_v1(self):
    """Calculate the discharge of the main channel after Manning-Strickler.

    Required control parameters:
      :class:`~hydpy.model.lstream.lstream_control.EKM`
      :class:`~hydpy.model.lstream.lstream_control.SKM`
      :class:`~hydpy.model.lstream.lstream_control.Gef`

    Required flux sequence:
      :class:`~hydpy.model.lstream.lstream_fluxes.AM`
      :class:`~hydpy.model.lstream.lstream_fluxes.UM`

    Calculated flux sequence:
      :class:`~hydpy.model.lstream.lstream_fluxes.QM`

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
    outer embankment and that water flowing exactly above the a foreland
    is contributing to :class:`~hydpy.model.lstream.lstream_fluxes.AV`.
    The theoretical surface seperating water above the main channel from
    water above the foreland is not contributing to
    :class:`~hydpy.model.lstream.lstream_fluxes.UV`, but the surface
    seperating water above the foreland from water above its outer embankment
    is contributing to :class:`~hydpy.model.lstream.lstream_fluxes.UV`.

    Required control parameters:
      :class:`~hydpy.model.lstream.lstream_control.HM`
      :class:`~hydpy.model.lstream.lstream_control.BV`
      :class:`~hydpy.model.lstream.lstream_control.BNV`

    Required derived parameter:
      :class:`~hydpy.model.lstream.lstream_derived.HV`

    Required flux sequence:
      :class:`~hydpy.model.lstream.lstream_fluxes.H`

    Calculated flux sequence:
      :class:`~hydpy.model.lstream.lstream_fluxes.AV`
      :class:`~hydpy.model.lstream.lstream_fluxes.UV`

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
        (:class:`~hydpy.model.lstream.lstream_fluxes.H` <
        :class:`~hydpy.model.lstream.lstream_control.HM`):

        >>> fluxes.h = .5
        >>> model.calc_av_uv_v1()
        >>> fluxes.av
        av(0.0, 0.0)
        >>> fluxes.uv
        uv(0.0, 0.0)

        The second example deals with moderate high flow conditions, where
        water flows over both forelands, but not over their embankments:
        (:class:`~hydpy.model.lstream.lstream_control.HM` <
        :class:`~hydpy.model.lstream.lstream_fluxes.H` <
        (:class:`~hydpy.model.lstream.lstream_control.HM` +
        :class:`~hydpy.model.lstream.lstream_derived.HV`)):

        >>> fluxes.h = 1.5
        >>> model.calc_av_uv_v1()
        >>> fluxes.av
        av(1.5, 1.5)
        >>> fluxes.uv
        uv(4.061553, 4.061553)

        The third example deals with extreme high flow conditions, where
        water flows over the both foreland and their outer embankments:
        ((:class:`~hydpy.model.lstream.lstream_control.HM` +
        :class:`~hydpy.model.lstream.lstream_derived.HV`) <
        :class:`~hydpy.model.lstream.lstream_fluxes.H`):

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
      :class:`~hydpy.model.lstream.lstream_control.EKV`
      :class:`~hydpy.model.lstream.lstream_control.SKV`
      :class:`~hydpy.model.lstream.lstream_control.Gef`

    Required flux sequence:
      :class:`~hydpy.model.lstream.lstream_fluxes.AV`
      :class:`~hydpy.model.lstream.lstream_fluxes.UV`

    Calculated flux sequence:
      :class:`~hydpy.model.lstream.lstream_fluxes.QV`

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
    water flowing exactly above the a embankment is added to
    :class:`~hydpy.model.lstream.lstream_fluxes.AVR`.
    The theoretical surface seperating water above the foreland from water
    above its embankment is not contributing to
    :class:`~hydpy.model.lstream.lstream_fluxes.UVR`.

    Required control parameters:
      :class:`~hydpy.model.lstream.lstream_control.HM`
      :class:`~hydpy.model.lstream.lstream_control.BNVR`

    Required derived parameter:
      :class:`~hydpy.model.lstream.lstream_derived.HV`

    Required flux sequence:
      :class:`~hydpy.model.lstream.lstream_fluxes.H`

    Calculated flux sequence:
      :class:`~hydpy.model.lstream.lstream_fluxes.AVR`
      :class:`~hydpy.model.lstream.lstream_fluxes.UVR`

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
        (:class:`~hydpy.model.lstream.lstream_control.HM` <
        :class:`~hydpy.model.lstream.lstream_fluxes.H` <
        (:class:`~hydpy.model.lstream.lstream_control.HM` +
        :class:`~hydpy.model.lstream.lstream_derived.HV`)):

        >>> fluxes.h = 1.5
        >>> model.calc_avr_uvr_v1()
        >>> fluxes.avr
        avr(0.0, 0.0)
        >>> fluxes.uvr
        uvr(0.0, 0.0)

        The second example deals with extreme high flow conditions, where
        water flows over the both foreland and their outer embankments:
        ((:class:`~hydpy.model.lstream.lstream_control.HM` +
        :class:`~hydpy.model.lstream.lstream_derived.HV`) <
        :class:`~hydpy.model.lstream.lstream_fluxes.H`):

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
      :class:`~hydpy.model.lstream.lstream_control.EKV`
      :class:`~hydpy.model.lstream.lstream_control.SKV`
      :class:`~hydpy.model.lstream.lstream_control.Gef`

    Required flux sequence:
      :class:`~hydpy.model.lstream.lstream_fluxes.AVR`
      :class:`~hydpy.model.lstream.lstream_fluxes.UVR`

    Calculated flux sequence:
      :class:`~hydpy.model.lstream.lstream_fluxes.QVR`

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
    """Calculate the discharge of the total cross section.

    Method :func:`calc_qg_v1` applies the actual versions of all methods
    for calculating the flown through areas, wetted perimeters and discharges
    of the different cross section compartments.  Hence its requirements
    might be different for various application models.
    """
    flu = self.sequences.fluxes.fastaccess
    self.calc_am_um()
    self.calc_qm()
    self.calc_av_uv()
    self.calc_qv()
    self.calc_avr_uvr()
    self.calc_qvr()
    flu.qg = flu.qm+flu.qv[0]+flu.qv[1]+flu.qvr[0]+flu.qvr[1]

def calc_hmin_qmin_hmax_qmax_v1(self):
    """Determine an starting interval for iteration methods as the one
    implemented in method :func:`calc_h_v1`.

    The resulting interval is determined in a manner, that on the
    one hand :math:`Qmin \\leq QRef \\leq Qmax` is fulfilled and on the
    other hand the results of method :func:`calc_qg_v1` are continuous
    for :math:`Hmin \\leq H \\leq Hmax`.

    Required control parameter:
      :class:`~hydpy.model.lstream.lstream_control.HM`

    Required derived paramters:
      :class:`~hydpy.model.lstream.lstream_derived.HV`
      :class:`~hydpy.model.lstream.lstream_derived.QM`
      :class:`~hydpy.model.lstream.lstream_derived.QV`

    Required flux sequence:
      :class:`~hydpy.model.lstream.lstream_fluxes.QRef`

    Calculated aide sequences:
      :class:`~hydpy.model.lstream.lstream_aides.HMin`
      :class:`~hydpy.model.lstream.lstream_aides.HMax`
      :class:`~hydpy.model.lstream.lstream_aides.QMin`
      :class:`~hydpy.model.lstream.lstream_aides.QMax`

    Besides the mentioned required parameters and sequences, those of the
    actual method for calculating the discharge of the total cross section
    might be required.  This is the case whenever water flows on both outer
    embankments.  In such occasions no previously determined upper boundary
    values are available and method :func:`calc_hmin_qmin_hmax_qmax_v1` needs
    to increase the value of :math:`HMax` successively until the condition
    :math:`QG \\leq QMax` is met.
    """
    con = self.parameters.control.fastaccess
    der = self.parameters.derived.fastaccess
    flu = self.sequences.fluxes.fastaccess
    aid = self.sequences.aides.fastaccess
    if flu.qref <= der.qm:
        aid.hmin = 0.
        aid.qmin = 0.
        aid.hmax = con.hm
        aid.qmax = der.qm
    elif flu.qref <= min(der.qv):
        aid.hmin = con.hm
        aid.qmin = der.qm
        aid.hmax = con.hm+min(der.hv)
        aid.qmax = min(der.qv)
    elif flu.qref < max(der.qv):
        aid.hmin = con.hm+min(der.hv)
        aid.qmin = min(der.qv)
        aid.hmax = con.hm+max(der.hv)
        aid.qmax = max(der.qv)
    else:
        flu.h = con.hm+max(der.hv)
        aid.hmin = flu.h
        aid.qmin = flu.qg
        while True:
            flu.h *= 2.
            self.calc_qg()
            if flu.qg < flu.qref:
                aid.hmin = flu.h
                aid.qmin = flu.qg
            else:
                aid.hmax = flu.h
                aid.qmax = flu.qg
                break

def calc_h_v1(self):
    """Approximate the water stage resulting in a certain reference discarge
    with the Pegasus iteration method.

    Required control parameters:
      :class:`~hydpy.model.lstream.lstream_control.QTol`
      :class:`~hydpy.model.lstream.lstream_control.HTol`

    Required flux sequence:
      :class:`~hydpy.model.lstream.lstream_fluxes.QRef`

    Calculated aide sequences:
      :class:`~hydpy.model.lstream.lstream_aides.HMin`
      :class:`~hydpy.model.lstream.lstream_aides.HMax`
      :class:`~hydpy.model.lstream.lstream_aides.QMin`
      :class:`~hydpy.model.lstream.lstream_aides.QMax`

    Calculated flux sequence:
      :class:`~hydpy.model.lstream.lstream_fluxes.H`

    Besides the parameters and sequences given above, those of the
    actual method for calculating the discharge of the total cross section
    are required.

    Examples:
        Essentially, the Pegasus method is a root finding algorithm which
        sequentially decreases its search radius (like the simple bisection
        algorithm) and shows superlinear convergence properties (like the
        Newton-Raphson algorithm).  Ideally, its convergence should be proved
        for each application model to be derived from HydPy-L-Stream.
        The following examples focus on the methods
        :func:`calc_hmin_qmin_hmax_qmax_v1` and :func:`calc_qg_v1`
        (including their submethods) only:

        >>> from hydpy.models.lstream import *
        >>> parameterstep()
        >>> model.calc_hmin_qmin_hmax_qmax = model.calc_hmin_qmin_hmax_qmax_v1
        >>> model.calc_qg = model.calc_qg_v1
        >>> model.calc_qm = model.calc_qm_v1
        >>> model.calc_av_uv = model.calc_av_uv_v1
        >>> model.calc_qv = model.calc_qv_v1
        >>> model.calc_avr_uvr = model.calc_avr_uvr_v1
        >>> model.calc_qvr = model.calc_qvr_v1

        Define the geometry and roughness values for the first test channel:

        >>> bm(2.)
        >>> bnm(4.)
        >>> hm(1.)
        >>> bv(.5, 10.)
        >>> bbv(1., 2.)
        >>> bnv(1., 8.)
        >>> bnvr(20.)
        >>> ekm(1.)
        >>> skm(20.)
        >>> ekv(1.)
        >>> skv(60., 80.)
        >>> gef(.01)

        Set the error tolerances of the iteration small enough, not to
        compromise the shown first six decimal places of the following results:

        >>> qtol(1e-10)
        >>> htol(1e-10)

        Derive the required secondary parameters:

        >>> derived.hv.update()
        >>> derived.qm.update()
        >>> derived.qv.update()

        Define a test function, accepting a reference discharge and printing
        both the approximated water stage and the related discharge value:

        >>> def test(qref):
        ...     fluxes.qref = qref
        ...     model.calc_hmin_qmin_hmax_qmax()
        ...     model.calc_h()
        ...     print(repr(fluxes.h))
        ...     print(repr(fluxes.qg))

        Zero discharge and the following discharge values are related to the
        only discontinuities of the given root finding problem:

        >>> derived.qm
        qm(8.399238)
        >>> derived.qv
        qv(154.463234, 23.073584)

        The related water stages are the ones (directly or indirectly)
        defined above:

        >>> test(0.)
        h(0.0)
        qg(0.0)
        >>> test(derived.qm)
        h(1.0)
        qg(8.399238)
        >>> test(derived.qv.left)
        h(2.0)
        qg(154.463234)
        >>> test(derived.qv.right)
        h(1.25)
        qg(23.073584)

        Test some intermediate water stages, inundating the only the main
        channel, the main channel along with the right foreland, and the
        main channel along with both forelands respectively:

        >>> test(6.)
        h(0.859452)
        qg(6.0)
        >>> test(10.)
        h(1.047546)
        qg(10.0)
        >>> test(100)
        h(1.77455)
        qg(100.0)

        Finally, test two extreme water stages, inundating both outer
        foreland embankments:

        >>> test(200.)
        h(2.152893)
        qg(200.0)
        >>> test(2000.)
        h(4.240063)
        qg(2000.0)

        There is a potential risk of the implemented iteration method to fail
        for special channel geometries.  To test such cases in a more
        condensed manner, the following test methods evaluates different water
        stages automatically in accordance with the example above.  An error
        message is printed only, the estimated discharge does not approximate
        the reference discharge with six decimal places:

        >>> def test():
        ...     derived.hv.update()
        ...     derived.qm.update()
        ...     derived.qv.update()
        ...     qm, qv = derived.qm, derived.qv
        ...     for qref in [0., qm, qv.left, qv.right,
        ...                  2./3.*qm+1./3.*min(qv),
        ...                  2./3.*min(qv)+1./3.*max(qv),
        ...                  3.*max(qv), 30.*max(qv)]:
        ...         fluxes.qref = qref
        ...         model.calc_hmin_qmin_hmax_qmax()
        ...         model.calc_h()
        ...         if abs(round(fluxes.qg-qref) > 0.):
        ...             print('Error!', 'qref:', qref, 'qg:', fluxes.qg)

        Check for a triangle main channel:

        >>> bm(0.)
        >>> test()
        >>> bm(2.)

        Check for a completely flat main channel:

        >>> hm(0.)
        >>> test()
        >>> hm(1.)

        Check for a nonexistend main channel:

        >>> bm(0.)
        >>> bnm(0.)
        >>> test()
        >>> bm(2.)
        >>> bnm(4.)

        Check for a nonexistend forelands:

        >>> bv(0.)
        >>> bbv(0.)
        >>> test()
        >>> bv(.5, 10.)
        >>> bbv(1., 2.)

        Check for nonexistend outer foreland embankments:

        >>> bnvr(0.)
        >>> test()

        To take the last test as an illustrative example, one can see that
        the given reference discharge is met by the estimated total discharge,
        which consists of components related to the main channel and the
        forelands only:

        >>> fluxes.qref
        qref(3932.452785)
        >>> fluxes.qg
        qg(3932.452785)
        >>> fluxes.qm
        qm(530.074621)
        >>> fluxes.qv
        qv(113.780226, 3288.597937)
        >>> fluxes.qvr
        qvr(0.0, 0.0)
    """
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    aid = self.sequences.aides.fastaccess
    aid.qmin -= flu.qref
    aid.qmax -= flu.qref
    if modelutils.fabs(aid.qmin) < con.qtol:
        flu.h = aid.hmin
        self.calc_qg()
    elif modelutils.fabs(aid.qmax) < con.qtol:
        flu.h = aid.hmax
        self.calc_qg()
    elif modelutils.fabs(aid.hmax-aid.hmin) < con.htol:
        flu.h = (aid.hmin+aid.hmax)/2.
        self.calc_qg()
    else:
        while True:
            flu.h = aid.hmin-aid.qmin*(aid.hmax-aid.hmin)/(aid.qmax-aid.qmin)
            self.calc_qg()
            aid.qtest = flu.qg-flu.qref
            if modelutils.fabs(aid.qtest) < con.qtol:
                return
            elif (((aid.qmax < 0.) and (aid.qtest < 0.)) or
              ((aid.qmax > 0.) and (aid.qtest > 0.))):
                aid.qmin *= aid.qmax/(aid.qmax+aid.qtest)
            else:
                aid.hmin = aid.hmax
                aid.qmin = aid.qmax
            aid.hmax = flu.h
            aid.qmax = aid.qtest
            if modelutils.fabs(aid.hmax-aid.hmin) < con.htol:
                return

def calc_qa_v1(self):
    """Calculate outflow.

    The working equation is the analytical solution of the linear storage
    equation under the assumption of constant change in inflow during
    the simulation time step.

    Required flux sequence:
      :class:`~hydpy.model.lstream.lstream_fluxes.RK`

    Required state sequence:
      :class:`~hydpy.model.lstream.lstream_states.QZ`

    Updated state sequence:
      :class:`~hydpy.model.lstream.lstream_states.QA`

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
    _RUNMETHODS = (update_inlets_v1,
                   calc_qref_v1,
                   calc_hmin_qmin_hmax_qmax_v1,
                   calc_h_v1,
                   calc_rk_v1,
                   calc_qa_v1,
                   update_outlets_v1)
    _ADDMETHODS = (calc_am_um_v1,
                   calc_qm_v1,
                   calc_av_uv_v1,
                   calc_qv_v1,
                   calc_avr_uvr_v1,
                   calc_qvr_v1,
                   calc_qg_v1)
