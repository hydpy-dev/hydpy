# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, wildcard-import, unused-wildcard-import
"""
.. _Pegasus method: https://link.springer.com/article/10.1007/BF01932959


.. warning::

    Before using |lstream_v1|, read this documentation carefully.
    |lstream_v1| does not keep the water balance.  This flaw is
    under discussion at the moment and should be fixed within the
    next few weeks.

Version 1 of HydPy-L-Stream (called lstream_v1) implements the Williams
routing method in a similar manner as the LARSIM model used by the
German Federal Institute of Hydrology (BfG).  Essentially, routing is
performed via a simple linear storage in each simulation time step.
But the linear storage coefficient (|RK|) is adapted to the actual
flow conditions at the beginning of each time step, making the approach
nonlinear for instationary inputs.  The storage coefficient is determined
via the Gauckler-Manning-Strickler formula, which is applied on the
`triple trapezoid profile`, shown in the following figure:

.. image:: HydPy-L-Stream_Version-1.png

|RK| depends on the length of the considered channel (|Laen|) and the
mean velocity within the channel. To calculate the velocity based on
the Manning formula, one needs to know the current water stage (|H|).
This water stage is determined by iteration based on the current
reference discharge (|QRef|).  As the relation between |H| and
discharge (|QG|) is discontinuous due to the sharp transitions of the
`triple trapezoid profile`, we decided on an iteration algorithm called
`Pegasus method`_, which is an improved `Regulari Falsi` method that
can be used when the bounds of the search interval are known.  At the
beginning of each simulation interval, we first determine the `highest
section` of the `triple trapozoid profile` containing water (for low flow
conditions, this would be the the main channel).  Then we use its lower
and upper height (in the given example zero and |HM|) as the initial
boundaries and refine them afterwards until the actual water stage |H|
is identified with sufficient accuracy (defined by the tolerance values
|HTol| and |QTol|).  This is much effort for a simple storage routing
method, but due to the superlinear convergence properties of the
`Pegasus method`_ the required computation times seem acceptable.

The above paragraph is a little inaccurate regarding the term `velocity`.
It is well known that a flood wave has usually a considerably higher
velocity than the water itself.  Hence |lstream_v1| should have a
tendency to overestimate travel times.  This is important to note, if
one determines the parameters of |lstream_v1| based on real channel
geometries and roughness coefficients, and should eventually be
compensated through increasing the roughness related calibration
coefficients |EKM| and |EKV|.  However, we took the decision to use
the water velocity, as the same assumption was initially made by the
original LARSIM model.  Later, LARSIM introduced the "dVdQ" option,
allowing to use the actual wave travel time for calculating |RK|.
Maybe the same should also be done for |lstream| through defining
an additional application model.


Integration test:

    The following calculations are performed over a period of 20 hours:

    >>> from hydpy import pub, Timegrid, Timegrids, Nodes, Element
    >>> pub.timegrids = Timegrids(Timegrid('01.01.2000 00:00',
    ...                                    '01.01.2000 20:00',
    ...                                    '1h'))

    Import the model and define the time step size the parameter values
    given below should be related to:

    >>> from hydpy.models.lstream_v1 import *
    >>> parameterstep('1d')

    For testing purposes, the model input shall be retrieved from the nodes
    `input1` and `input2` and the model output shall be passed to node
    `output`.  Firstly, define all nodes:

    >>> nodes = Nodes('input1', 'input2', 'output')

    Secondly, define the element "stream" and build the connections between
    the nodes defined above and the `lstream_v1` model instance:

    >>> stream = Element('stream',
    ...                  inlets=['input1', 'input2'],
    ...                  outlets='output')
    >>> stream.connect(model)

    Prepare a test function object, which sets the initial inflow (|QZ|)
    and outflow (|QA|) to zero before each simulation run:

    >>> from hydpy.core.testtools import IntegrationTest
    >>> IntegrationTest.plotting_options.height = 550
    >>> IntegrationTest.plotting_options.activated=(
    ...     states.qz, states.qa)
    >>> test = IntegrationTest(stream,
    ...                        inits=((states.qz, 0.),
    ...                               (states.qa, 0.)))
    >>> test.dateformat = '%H:%M'

    Define the geometry and roughness values of the test channel:

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
    >>> gef(.02)
    >>> laen(10.)

    Set the error tolerances of the iteration small enough, to not
    compromise the first six decimal places shown in the following
    results (this increases computation times and should not be
    necessary for usual applications of |lstream_v1|):

    >>> qtol(1e-10)
    >>> htol(1e-10)

    Define two flood events, one for each stream inflow:

    >>> nodes.input1.sequences.sim.series = [
    ...                     0., 0., 1., 3., 2., 1., 0., 0., 0., 0.,
    ...                     0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]
    >>> nodes.input2.sequences.sim.series = [
    ...                     0., 1., 5., 9., 8., 5., 3., 2., 1., 0.,
    ...                     0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]

    The following table and figure show all relevant input and output data
    as well as all relevant variables calculated internally.  Note that the
    total sum of all input values (|QZ|) is 41, but the total sum of all
    output values (|QA|) is above 46.  In our opinion, this is due to
    |lstream_v1| not applying the actual correction after Williams for
    adjusting the flow values to changes in the retention coefficient |RK|.
    We hope to be able to fix this flaw soon...

    >>> test('lstream_v1_ex1')
    |  date |     qref |        h |       am |       av |      avr |       ag |       um |       uv |      uvr |       qm |       qv |      qvr |       qg |       rk |   qz |       qa | input1 | input2 |   output |
    ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 00:00 |      0.0 |      0.0 |      0.0 | 0.0  0.0 | 0.0  0.0 |      0.0 |      0.0 | 0.0  0.0 | 0.0  0.0 |      0.0 | 0.0  0.0 | 0.0  0.0 |      0.0 |      0.0 |  0.0 |      0.0 |    0.0 |    0.0 |      0.0 |
    | 01:00 | 0.333333 |  0.16889 | 0.451875 | 0.0  0.0 | 0.0  0.0 | 0.451875 | 3.392702 | 0.0  0.0 | 0.0  0.0 | 0.333333 | 0.0  0.0 | 0.0  0.0 | 0.333333 | 3.765627 |  1.0 | 0.121767 |    0.0 |    1.0 | 0.121767 |
    | 02:00 | 2.373922 |  0.47093 | 1.828958 | 0.0  0.0 | 0.0  0.0 | 1.828958 | 5.883386 | 0.0  0.0 | 0.0  0.0 | 2.373922 | 0.0  0.0 | 0.0  0.0 | 2.373922 | 2.140104 |  6.0 | 1.455232 |    1.0 |    5.0 | 1.455232 |
    | 03:00 | 6.485077 | 0.759892 | 3.829526 | 0.0  0.0 | 0.0  0.0 | 3.829526 | 8.266229 | 0.0  0.0 | 0.0  0.0 | 6.485077 | 0.0  0.0 | 0.0  0.0 | 6.485077 | 1.640316 | 12.0 | 5.037344 |    3.0 |    9.0 | 5.037344 |
    | 04:00 | 9.012448 | 0.883278 | 4.887279 | 0.0  0.0 | 0.0  0.0 | 4.887279 | 9.283699 | 0.0  0.0 | 0.0  0.0 | 9.012448 | 0.0  0.0 | 0.0  0.0 | 9.012448 | 1.506336 | 10.0 | 7.876787 |    2.0 |    8.0 | 7.876787 |
    | 05:00 | 7.958929 | 0.834755 | 4.456775 | 0.0  0.0 | 0.0  0.0 | 4.456775 | 8.883568 | 0.0  0.0 | 0.0  0.0 | 7.958929 | 0.0  0.0 | 0.0  0.0 | 7.958929 | 1.555477 |  6.0 | 7.834286 |    1.0 |    5.0 | 7.834286 |
    | 06:00 | 5.611429 | 0.710593 | 3.440959 | 0.0  0.0 | 0.0  0.0 | 3.440959 | 7.859704 | 0.0  0.0 | 0.0  0.0 | 5.611429 | 0.0  0.0 | 0.0  0.0 | 5.611429 | 1.703349 |  3.0 | 6.288891 |    0.0 |    3.0 | 6.288891 |
    | 07:00 | 3.762964 | 0.588614 | 2.563094 | 0.0  0.0 | 0.0  0.0 | 2.563094 | 6.853835 | 0.0  0.0 | 0.0  0.0 | 3.762964 | 0.0  0.0 | 0.0  0.0 | 3.762964 | 1.892047 |  2.0 | 4.715447 |    0.0 |    2.0 | 4.715447 |
    | 08:00 | 2.571816 | 0.489778 | 1.939089 | 0.0  0.0 | 0.0  0.0 | 1.939089 | 6.038817 | 0.0  0.0 | 0.0  0.0 | 2.571816 | 0.0  0.0 | 0.0  0.0 | 2.571816 | 2.094379 |  1.0 |  3.47966 |    0.0 |    1.0 |  3.47966 |
    | 09:00 |  1.49322 | 0.373702 | 1.306015 | 0.0  0.0 | 0.0  0.0 | 1.306015 | 5.081623 | 0.0  0.0 | 0.0  0.0 |  1.49322 | 0.0  0.0 | 0.0  0.0 |  1.49322 | 2.429528 |  0.0 | 2.462745 |    0.0 |    0.0 | 2.462745 |
    | 10:00 | 0.820915 | 0.274466 | 0.850257 | 0.0  0.0 | 0.0  0.0 | 0.850257 | 4.263303 | 0.0  0.0 | 0.0  0.0 | 0.820915 | 0.0  0.0 | 0.0  0.0 | 0.820915 | 2.877065 |  0.0 | 1.739678 |    0.0 |    0.0 | 1.739678 |
    | 11:00 | 0.579893 | 0.228232 | 0.664823 | 0.0  0.0 | 0.0  0.0 | 0.664823 | 3.882048 | 0.0  0.0 | 0.0  0.0 | 0.579893 | 0.0  0.0 | 0.0  0.0 | 0.579893 | 3.184607 |  0.0 | 1.270855 |    0.0 |    0.0 | 1.270855 |
    | 12:00 | 0.423618 | 0.192604 | 0.533594 | 0.0  0.0 | 0.0  0.0 | 0.533594 | 3.588256 | 0.0  0.0 | 0.0  0.0 | 0.423618 | 0.0  0.0 | 0.0  0.0 | 0.423618 |  3.49892 |  0.0 | 0.954934 |    0.0 |    0.0 | 0.954934 |
    | 13:00 | 0.318311 | 0.164646 | 0.437725 | 0.0  0.0 | 0.0  0.0 | 0.437725 | 3.357705 | 0.0  0.0 | 0.0  0.0 | 0.318311 | 0.0  0.0 | 0.0  0.0 | 0.318311 | 3.819853 |  0.0 | 0.734987 |    0.0 |    0.0 | 0.734987 |
    | 14:00 | 0.244996 | 0.142354 | 0.365767 | 0.0  0.0 | 0.0  0.0 | 0.365767 | 3.173881 | 0.0  0.0 | 0.0  0.0 | 0.244996 | 0.0  0.0 | 0.0  0.0 | 0.244996 | 4.147091 |  0.0 | 0.577506 |    0.0 |    0.0 | 0.577506 |
    | 15:00 | 0.192502 | 0.124327 | 0.310483 | 0.0  0.0 | 0.0  0.0 | 0.310483 | 3.025226 | 0.0  0.0 | 0.0  0.0 | 0.192502 | 0.0  0.0 | 0.0  0.0 | 0.192502 | 4.480221 |  0.0 | 0.461977 |    0.0 |    0.0 | 0.461977 |
    | 16:00 | 0.153992 | 0.109562 | 0.267141 | 0.0  0.0 | 0.0  0.0 | 0.267141 | 2.903475 | 0.0  0.0 | 0.0  0.0 | 0.153992 | 0.0  0.0 | 0.0  0.0 | 0.153992 | 4.818789 |  0.0 | 0.375401 |    0.0 |    0.0 | 0.375401 |
    | 17:00 | 0.125134 |  0.09733 | 0.232553 | 0.0  0.0 | 0.0  0.0 | 0.232553 | 2.802606 | 0.0  0.0 | 0.0  0.0 | 0.125134 | 0.0  0.0 | 0.0  0.0 | 0.125134 | 5.162328 |  0.0 | 0.309291 |    0.0 |    0.0 | 0.309291 |
    | 18:00 | 0.103097 |  0.08709 | 0.204518 | 0.0  0.0 | 0.0  0.0 | 0.204518 |  2.71816 | 0.0  0.0 | 0.0  0.0 | 0.103097 | 0.0  0.0 | 0.0  0.0 | 0.103097 | 5.510384 |  0.0 | 0.257961 |    0.0 |    0.0 | 0.257961 |
    | 19:00 | 0.085987 | 0.078434 | 0.181476 | 0.0  0.0 | 0.0  0.0 | 0.181476 | 2.646786 | 0.0  0.0 | 0.0  0.0 | 0.085987 | 0.0  0.0 | 0.0  0.0 | 0.085987 | 5.862528 |  0.0 | 0.217508 |    0.0 |    0.0 | 0.217508 |

    .. raw:: html

        <iframe
            src="lstream_v1_ex1.html"
            width="100%"
            height="580"
            frameborder=0
        ></iframe>

    In the above example, water flows in the main channel only.  At
    least one example needs to be added, in which also the river
    banks are activated.  This could for example be done by reducing
    channel slope:

    >>> gef(.002)


"""
# import...
# ...from standard library
from __future__ import division, print_function
# ...from HydPy
from hydpy.core.modelimports import *
from hydpy.core import modeltools
from hydpy.core import parametertools
from hydpy.core import sequencetools
# ...from lstream
from hydpy.models.lstream import lstream_model
from hydpy.models.lstream import lstream_control
from hydpy.models.lstream import lstream_derived
from hydpy.models.lstream import lstream_fluxes
from hydpy.models.lstream import lstream_states
from hydpy.models.lstream import lstream_aides
from hydpy.models.lstream import lstream_inlets
from hydpy.models.lstream import lstream_outlets


class Model(modeltools.Model):
    """LARSIM-Stream (Manning) version of HydPy-L-Stream (lstream_v1)."""
    _INLET_METHODS = (lstream_model.pick_q_v1,)
    _RUN_METHODS = (lstream_model.calc_qref_v1,
                    lstream_model.calc_hmin_qmin_hmax_qmax_v1,
                    lstream_model.calc_h_v1,
                    lstream_model.calc_ag_v1,
                    lstream_model.calc_rk_v1,
                    lstream_model.calc_qa_v1)
    _ADD_METHODS = (lstream_model.calc_am_um_v1,
                    lstream_model.calc_qm_v1,
                    lstream_model.calc_av_uv_v1,
                    lstream_model.calc_qv_v1,
                    lstream_model.calc_avr_uvr_v1,
                    lstream_model.calc_qvr_v1,
                    lstream_model.calc_qg_v1)
    _OUTLET_METHODS = (lstream_model.pass_q_v1,)


class ControlParameters(parametertools.SubParameters):
    """Control parameters of lstream_v1, directly defined by the user."""
    _PARCLASSES = (lstream_control.Laen,
                   lstream_control.Gef,
                   lstream_control.HM,
                   lstream_control.BM,
                   lstream_control.BV,
                   lstream_control.BBV,
                   lstream_control.BNM,
                   lstream_control.BNV,
                   lstream_control.BNVR,
                   lstream_control.SKM,
                   lstream_control.SKV,
                   lstream_control.EKM,
                   lstream_control.EKV,
                   lstream_control.QTol,
                   lstream_control.HTol)


class DerivedParameters(parametertools.SubParameters):
    """Derived parameters of lstream_v1, indirectly defined by the user.
    """
    _PARCLASSES = (lstream_derived.HV,
                   lstream_derived.QM,
                   lstream_derived.QV,
                   lstream_derived.Sek)


class FluxSequences(sequencetools.FluxSequences):
    """Flux sequences of LARSIM-ME."""
    _SEQCLASSES = (lstream_fluxes.QRef,
                   lstream_fluxes.H,
                   lstream_fluxes.AM,
                   lstream_fluxes.AV,
                   lstream_fluxes.AVR,
                   lstream_fluxes.AG,
                   lstream_fluxes.UM,
                   lstream_fluxes.UV,
                   lstream_fluxes.UVR,
                   lstream_fluxes.QM,
                   lstream_fluxes.QV,
                   lstream_fluxes.QVR,
                   lstream_fluxes.QG,
                   lstream_fluxes.RK)


class StateSequences(sequencetools.StateSequences):
    """State sequences of lstream_v1."""
    _SEQCLASSES = (lstream_states.QZ,
                   lstream_states.QA)


class AideSequences(sequencetools.AideSequences):
    """Aide sequences of lstream_v1."""
    _SEQCLASSES = (lstream_aides.Temp,
                   lstream_aides.HMin,
                   lstream_aides.HMax,
                   lstream_aides.QMin,
                   lstream_aides.QMax,
                   lstream_aides.QTest)


class InletSequences(sequencetools.LinkSequences):
    """Upstream link sequences of lstream_v1."""
    _SEQCLASSES = (lstream_inlets.Q,)


class OutletSequences(sequencetools.LinkSequences):
    """Downstream link sequences of lstream_v1."""
    _SEQCLASSES = (lstream_outlets.Q,)


autodoc_applicationmodel()

# pylint: disable=invalid-name
tester = Tester()
cythonizer = Cythonizer()
cythonizer.complete()
