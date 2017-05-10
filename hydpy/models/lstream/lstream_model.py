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

def calc_dam_dum_v1(self):
    """Calculate the changes in the flown through area and the wetted
    perimeter with regard to water stage of the main channel.

    Method :func:`calc_dam_dum_v1` and the following examples rely on the same
    geometrical assumtions described for method :func:`calc_am_um_v1`.

    Required control parameters:
      :class:`~hydpy.model.lstream.lstream_control.HM`
      :class:`~hydpy.model.lstream.lstream_control.BM`
      :class:`~hydpy.model.lstream.lstream_control.BNM`

    Required flux sequence:
      :class:`~hydpy.model.lstream.lstream_fluxes.H`

    Calculated flux sequence:
      :class:`~hydpy.model.lstream.lstream_fluxes.DAM`
      :class:`~hydpy.model.lstream.lstream_fluxes.DUM`

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
        (:class:`~hydpy.model.lstream.lstream_fluxes.H` < 
        :class:`~hydpy.model.lstream.lstream_control.HM`):

        >>> fluxes.h = .5
        >>> model.calc_dam_dum_v1()
        >>> fluxes.dam
        dam(6.0)
        >>> fluxes.dum
        dum(8.246211)

        The second example deals with high flow conditions, where water flows
        over the foreland also:
        (:class:`~hydpy.model.lstream.lstream_fluxes.H` > 
        :class:`~hydpy.model.lstream.lstream_control.HM`):

        >>> fluxes.h = 1.5
        >>> model.calc_dam_dum_v1()
        >>> fluxes.dam
        dam(10.0)
        >>> fluxes.dum
        dum(2.0)

        The third example checks the special case of a main channel with zero
        height:

        >>> hm(0.)
        >>> model.calc_dam_dum_v1()
        >>> fluxes.dam
        dam(2.0)
        >>> fluxes.dum
        dum(2.0)

        The fourth example checks the special case of the actual water stage
        not beeing larger than zero (empty channel):

        >>> fluxes.h = 0.
        >>> hm(1.)
        >>> model.calc_dam_dum_v1()
        >>> fluxes.dam
        dam(2.0)
        >>> fluxes.dum
        dum(8.246211)
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

def calc_dqm_v1(self):
    """Calculate the change in discharge with increasing water stage of the 
    main channel in accordance with the Manning-Strickler equation.
    
    Note that method :func:`calc_dqm_v1` is based on the same assumptions 
    as method :func:`calc_qm_v1`.

    Required control parameters:
      :class:`~hydpy.model.lstream.lstream_control.EKM`
      :class:`~hydpy.model.lstream.lstream_control.SKM`
      :class:`~hydpy.model.lstream.lstream_control.Gef`

    Required flux sequence:
      :class:`~hydpy.model.lstream.lstream_fluxes.AM`
      :class:`~hydpy.model.lstream.lstream_fluxes.UM`
      :class:`~hydpy.model.lstream.lstream_fluxes.DAM`
      :class:`~hydpy.model.lstream.lstream_fluxes.DUM`

    Calculated flux sequence:
      :class:`~hydpy.model.lstream.lstream_fluxes.DQM`

    Basic equation:
      :math:`DQM = EKM \\cdot SKM \\cdot \\frac{AM^{2/3}}{3 \\cdot UM^{5/3}}
      \\cdot (5 \\cdot UM \\cdot DAM - 2 \\cdot AM \\cdot DUM)
      \\cdot \\sqrt{Gef}`
    
    Examples:

        The following the examples are a little more complicated, as they
        are thought to prove that the method :func:`calc_dqm_v1` in fact 
        determines the derivatives of the Manning equation defined in 
        :func:`calc_qm_v1`. 
        
        First, assume certain values defining the channel geometry, slope, 
        and roughness:

        >>> from hydpy.models.lstream import *
        >>> parameterstep()       
        >>> bm(2.)
        >>> bnm(4.)
        >>> hm(1.)
        >>> ekm(2.)
        >>> skm(50.)
        >>> gef(.01)
        
        Secondly, define a function returning the derivative twice.  
        The first value is the result of the analytical solution of the 
        problem defined in :func:`calc_dqm_v1` itself, the second value is 
        a numerical approximation based on a central finite difference 
        calculation directly applied on method :func:`calc_qm_v1`:
        
        >>> def compare(h, dh):
        ...     # Apply the analytical solution.
        ...     fluxes.h = h
        ...     model.calc_am_um_v1()
        ...     model.calc_dam_dum_v1()
        ...     model.calc_dqm_v1()
        ...     # Apply the numerical approximation.
        ...     fluxes.h = h-dh
        ...     model.calc_am_um_v1()
        ...     model.calc_qm_v1()
        ...     q1 = fluxes.qm.value
        ...     fluxes.h = h+dh
        ...     model.calc_am_um_v1()
        ...     model.calc_qm_v1()
        ...     q2 = fluxes.qm.value
        ...     approx = (q2-q1)/(2*dh)
        ...     # (Round and) Return both results.
        ...     return fluxes.dqm, round(approx, 6)

        Thirdly, the equality of the results is checked for two different 
        water stages.  Note that in each case, both the analytical result 
        and its numerical approximation are practically the same.   
        
        >>> compare(0.9999, 1e-6)
        (dqm(94.110762), 94.110762)
        >>> compare(1.0001, 1e-6)
        (dqm(111.201244), 111.201244)
        
        However, because of the discontinuity of the channel geometry at 
        a water stage of one meter, a very tiny increase in the water stage
        results in a huge increase in the derivative.  This is a potential
        problem for the application of related methods that are somehow
        gradient-based.
        
        For zero or negative values of the flown through surface or
        the wetted perimeter:

        >>> fluxes.am = -1.
        >>> fluxes.um = 7.
        >>> model.calc_dqm_v1()
        >>> fluxes.dqm
        dqm(0.0)

        >>> fluxes.am = 3.
        >>> fluxes.um = 0.
        >>> model.calc_dqm_v1()
        >>> fluxes.dqm
        dqm(0.0)
    """
    con = self.parameters.control.fastaccess
    flu = self.sequences.fluxes.fastaccess
    if (flu.am > 0.) and (flu.um > 0.):
        flu.dqm = (con.ekm*con.skm*(flu.am**(2./3.)/(3.*flu.um**(5./3.))) *
                   (5.*flu.um*flu.dam-2.*flu.am*flu.dum)*con.gef**.5)
    else:
        flu.dqm = 0.
      
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

def calc_dav_duv_v1(self):
    """Calculate the changes in the flown through area and the wetted 
    perimeter with regard to water stage of both forelands.

    Method :func:`calc_dav_duv_v1` and the following examples rely on the same
    geometrical assumtions described for method :func:`calc_av_uv_v1`.

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

        The base scenario of the examples of method :func:`calc_av_uv_v1` is
        reused:

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
        >>> model.calc_dav_duv_v1()
        >>> fluxes.dav
        dav(0.0, 0.0)
        >>> fluxes.duv
        duv(0.0, 0.0)

        The second example deals with moderate high flow conditions, where
        water flows over both forelands, but not over their embankments:
        (:class:`~hydpy.model.lstream.lstream_control.HM` < 
        :class:`~hydpy.model.lstream.lstream_fluxes.H` < 
        (:class:`~hydpy.model.lstream.lstream_control.HM` + 
        :class:`~hydpy.model.lstream.lstream_derived.HV`)):

        >>> fluxes.h = 1.5
        >>> model.calc_dav_duv_v1()
        >>> fluxes.dav
        dav(4.0, 4.0)
        >>> fluxes.duv
        duv(4.123106, 4.123106)

        The third example deals with extreme high flow conditions, where
        water flows over the both foreland and their outer embankments:
        ((:class:`~hydpy.model.lstream.lstream_control.HM` + 
        :class:`~hydpy.model.lstream.lstream_derived.HV`) < 
        :class:`~hydpy.model.lstream.lstream_fluxes.H`):

        >>> fluxes.h = 2.5
        >>> model.calc_dav_duv_v1()
        >>> fluxes.dav
        dav(6.0, 6.0)
        >>> fluxes.duv
        duv(1.0, 1.0)

        The forth example assures that zero widths or hights of the forelands
        are handled properly:

        >>> bv.left = 0.
        >>> derived.hv.right = 0.
        >>> model.calc_dav_duv_v1()
        >>> fluxes.dav
        dav(4.0, 2.0)
        >>> fluxes.duv
        duv(1.0, 1.0)
    """
    con = self.parameters.control.fastaccess
    der = self.parameters.derived.fastaccess
    flu = self.sequences.fluxes.fastaccess
    for i in range(2):
        if flu.h <= con.hm:
            flu.dav[i] = 0.
            flu.duv[i] = 0.
        elif flu.h <= (con.hm+der.hv[i]):
            flu.dav[i] = con.bv[i]+(flu.h-con.hm)*con.bnv[i]
            flu.duv[i] = (1.+con.bnv[i]**2)**.5
        else:
            flu.dav[i] = con.bv[i]+der.hv[i]*con.bnv[i]
            flu.duv[i] = 1.
                        
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
    _RUNMETHODS = (calc_qref_v1,
                   calc_rk_v1,
                   calc_qa_v1,
                   update_inlets_v1,
                   update_outlets_v1)
    _ADDMETHODS = (calc_am_um_v1,
                   calc_dam_dum_v1,
                   calc_qm_v1,
                   calc_dqm_v1,
                   calc_av_uv_v1,
                   calc_dav_duv_v1,
                   calc_qv_v1,
                   calc_avr_uvr_v1,
                   calc_qvr_v1)
