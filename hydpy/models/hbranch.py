# -*- coding: utf-8 -*-
"""Christoph Tyralla, 6 February 2017."""

# import...
# ...from standard library
from __future__ import division, print_function
import sys
# ...third party
import numpy
# ...HydPy specific...
from hydpy.core import objecttools
from hydpy.core import modeltools
from hydpy.core import parametertools
from hydpy.core import sequencetools
from hydpy.core import devicetools
from hydpy import pub
# ...and load the required `magic` functions into the local namespace.
from hydpy.core.magictools import parameterstep
from hydpy.core.magictools import simulationstep
from hydpy.core.magictools import controlcheck
from hydpy.core.magictools import Tester
from hydpy.cythons.modelutils import Cythonizer


###############################################################################
# Parameter definitions
###############################################################################

# Control Parameters ##########################################################

class XPoints(parametertools.MultiParameter):
    """Supporting points for the independent input variable [eg. m³/s]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)

    def __call__(self, *args, **kwargs):
        self.shape = len(args)
        if self.shape[0] < 2:
            raise ValueError('Branching via linear interpolation requires '
                             'at least two supporting points, but for '
                             'parameter `%s` only %d are given.'
                             % (self.name, self.shape[0]))
        parametertools.MultiParameter.__call__(self, *args, **kwargs)
        if min(numpy.diff(self)) <= 0.:
            raise ValueError('The values of parameter `xpoints` must be '
                             'arranged in a strictly monotnously manner, '
                             'which is not the case for the given values '
                             '`%s`.' % ', '.join(str(value) for value in self))

class YPoints(parametertools.MultiParameter):
    """Supporting points for the dependent output variables [eg. m³/s].


    The documentation on method
    :func:`~hydpy.models.hbranch.Model.calc_outputs_v1` gives examples on how
    to set the values of :class:`~hydpy.models.hbranch.YPoints` properly.
    """
    NDIM, TYPE, TIME, SPAN = 2, float, None, (None, None)

    def __call__(self, *args, **kwargs):
        try:
            self.shape = (len(kwargs), self.subpars.xpoints.shape[0])
        except RuntimeError:
            raise RuntimeError('The shape of parameter `ypoints` depends on '
                               'the shape of parameter `xpoints`.  Make sure '
                               'parameter `xpoints` is defined first (and is '
                               'integrated into the hmodel as described in '
                               'the documentation).')
        branched = self.subpars.pars.model.sequences.outlets.branched
        try:
            branched.shape = self.shape[0]
        except RuntimeError:
            if branched.shape[0] != self.shape[0]:
                raise RuntimeError('The number of branches of the hbranch '
                                   'model should not be changed during run '
                                   'time.  If you really need to do this, '
                                   'first initialize a new `branched` '
                                   'sequence and connect it to the '
                                   'respective outlet nodes properly.')
        if self.shape[0] == 0:
            raise ValueError('No branches are defined.  Do this via keyword '
                             'arguments of the same name as the related '
                             'outlet node instances.')
        self.subpars.pars.model.sequences.fluxes.outputs.shape = self.shape[0]
        for (idx, key) in enumerate(sorted(kwargs)):
            value = kwargs[key]
            if ((key not in devicetools.Node.registerednames()) and
                    (pub.timegrids is not None)):
                raise ValueError('Node `%s` does not exist so far.  Hence it '
                                 'is not possible to branch to it.' % key)
            try:
                self[idx] = value
            except ValueError:
                if self.shape[1] != len(value):
                    raise ValueError('Each branch requires the same number of '
                                     'supporting points as given for '
                                     'parameter `xpoints`, which is %d.  But '
                                     'for branch `%s` %d are given.'
                                     % (self.shape[1], key, len(value)))
                else:
                    message = 'The affected keyword argument is `%s`' % key
                    objecttools.augmentexcmessage(suffix=message)
            setattr(self, key, self[idx])
            self.subpars.pars.model.nodenames.append(key)

    def __repr__(self):
        lines = self.commentrepr()
        nodenames = self.subpars.pars.model.nodenames
        for (idx, values) in enumerate(self):
            line = '%s=%s,' % (nodenames[idx], repr(list(values)))
            if not idx:
                lines.append('ypoints('+line)
            else:
                lines.append('        '+line)
        lines[-1] = lines[-1][:-1]+')'
        return '\n'.join(lines)


class ControlParameters(parametertools.SubParameters):
    """Control parameters of hbranch, directly defined by the user.

    Note that the number of supporting points handled parameter
    :class:`~hydpy.models.hbranch.XPoints` and
    :class:`~hydpy.models.hbranch.YPoints` must be identical.  First
    define the values of parameter :class:`~hydpy.models.hbranch.XPoints`,
    then the values  of parameter :class:`~hydpy.models.hbranch.YPoints`.
    """
    _PARCLASSES = (XPoints, YPoints)

# Derived Parameters ##########################################################

class NmbBranches(parametertools.SingleParameter):
    """Number of branches [-]."""
    NDIM, TYPE, TIME, SPAN = 0, int, None, (1, None)

class NmbPoints(parametertools.SingleParameter):
    """Number of supporting points for linear interpolation [-]."""
    NDIM, TYPE, TIME, SPAN = 0, int, None, (2, None)

class DerivedParameters(parametertools.SubParameters):
    """Derived parameters of hbranch, indirectly defined by the user."""
    _PARCLASSES = (NmbBranches, NmbPoints)

# Parameters ##################################################################

class Parameters(parametertools.Parameters):
    """All parameters of the hbranch model."""

    def update(self):
        """Determines the number of branches and number of supporting points
        for convenience."""
        con = self.control
        der = self.derived
        der.nmbbranches = con.ypoints.shape[0]
        der.nmbpoints = con.ypoints.shape[1]

###############################################################################
# Sequence Definitions
###############################################################################

# Flux Sequences ##############################################################

class Input(sequencetools.FluxSequence):
    """Total input [e.g. m³/s]."""
    NDIM, NUMERIC = 0, False

class Outputs(sequencetools.FluxSequence):
    """Branched outputs [e.g. m³/s]."""
    NDIM, NUMERIC = 1, False

    def __repr__(self):
        nodenames = self.subseqs.seqs.model.nodenames
        lines = []
        for (idx, value) in enumerate(self.values):
            line = '%s=%s,' % (nodenames[idx], repr(value))
            if not idx:
                lines.append('outputs('+line)
            else:
                lines.append('        '+line)
        lines[-1] = lines[-1][:-1]+')'
        return '\n'.join(lines)

class FluxSequences(sequencetools.FluxSequences):
    """Flux sequences of the hbranch model."""
    _SEQCLASSES = (Input, Outputs)

# Link Sequences ##############################################################

class Total(sequencetools.LinkSequence):
    """Total input [e.g. m³/s]."""
    NDIM, NUMERIC = 0, False

class InletSequences(sequencetools.LinkSequences):
    """Upstream link sequences of the hbranch model."""
    _SEQCLASSES = (Total,)

class Branched(sequencetools.LinkSequence):
    """Branched outputs [e.g. m³/s]."""
    NDIM, NUMERIC = 1, False

class OutletSequences(sequencetools.LinkSequences):
    """Downstream link sequences of the hbranch model."""
    _SEQCLASSES = (Branched,)

# Sequences ###################################################################

class Sequences(sequencetools.Sequences):
    """All sequences of the hbranch model."""

###############################################################################
# Model
###############################################################################

# Methods #####################################################################

def calc_outputs_v1(self):
    """Performs the actual interpolation or extrapolation.

    Required control parameters:
      :class:`~hydpy.models.hbranch.XPoints`
      :class:`~hydpy.models.hbranch.YPoints`

    Required derived parameter:
      :class:`~hydpy.models.hbranch.NmbPoints`
      :class:`~hydpy.models.hbranch.NmbBranches`

    Required flux sequence:
      :class:`~hydpy.models.hbranch.Input`

    Calculated flux sequence:
      :class:`~hydpy.models.hbranch.Outputs`

    Examples:

        As a simple example, assume a weir directing all discharge into
        `branch1` until the capacity limit of 2 m³/s is reached.  The
        discharge exceeding this threshold is directed into `branch2`:

        >>> from hydpy.models.hbranch import *
        >>> parameterstep()
        >>> xpoints(0., 2., 4.)
        >>> ypoints(branch1=[0., 2., 2.],
        ...         branch2=[0., 0., 2.])
        >>> model.parameters.update()

        Low discharge example (linear interpolation between the first two
        supporting point pairs):

        >>> fluxes.input = 1.
        >>> model.calc_outputs_v1()
        >>> fluxes.outputs
        outputs(branch1=1.0,
                branch2=0.0)

        Medium discharge example (linear interpolation between the second
        two supporting point pairs):

        >>> fluxes.input = 3.
        >>> model.calc_outputs_v1()
        >>> print(fluxes.outputs)
        outputs(branch1=2.0,
                branch2=1.0)

        High discharge example (linear extrapolation beyond the second two
        supporting point pairs):

        >>> fluxes.input = 5.
        >>> model.calc_outputs_v1()
        >>> fluxes.outputs
        outputs(branch1=2.0,
                branch2=3.0)

        Non-monotonous relationships and balance violations are allowed,
        e.g.:

        >>> xpoints(0., 2., 4., 6.)
        >>> ypoints(branch1=[0., 2., 0., 0.],
        ...         branch2=[0., 0., 2., 4.])
        >>> model.parameters.update()
        >>> fluxes.input = 7.
        >>> model.calc_outputs_v1()
        >>> fluxes.outputs
        outputs(branch1=0.0,
                branch2=5.0)

    """
    con = self.parameters.control.fastaccess
    der = self.parameters.derived.fastaccess
    flu = self.sequences.fluxes.fastaccess
    # Search for the index of the two relevant x points...
    for pdx in range(1, der.nmbpoints):
        if con.xpoints[pdx] > flu.input:
            break
    # ...and use it for linear interpolation (or extrapolation).
    for bdx in range(der.nmbbranches):
        flu.outputs[bdx] = (
            (flu.input-con.xpoints[pdx-1]) *
            (con.ypoints[bdx, pdx]-con.ypoints[bdx, pdx-1]) /
            (con.xpoints[pdx]-con.xpoints[pdx-1]) +
            con.ypoints[bdx, pdx-1])

def update_inlets_v1(self):
    """Updates :class:`~hydpy.models.hbranch.Input` based on
    :class:`~hydpy.models.hbranch.Total`."""
    flu = self.sequences.fluxes.fastaccess
    inl = self.sequences.inlets.fastaccess
    flu.input = inl.total[0]

def update_outlets_v1(self):
    """Updates :class:`~hydpy.models.hbranch.Branched` based on
    :class:`~hydpy.models.hbranch.Outputs`."""
    der = self.parameters.derived.fastaccess
    flu = self.sequences.fluxes.fastaccess
    out = self.sequences.outlets.fastaccess
    for bdx in range(der.nmbbranches):
        out.branched[bdx][0] += flu.outputs[bdx]

# Model class #################################################################

class Model(modeltools.Model):
    """The HydPy-H-Branch model.

    Additional attribute:
      * nodenames (:class:`list`): Names of the outlet node names, the
        actual model shall be connected to.
    """
    _RUNMETHODS = (calc_outputs_v1,
                   update_inlets_v1,
                   update_outlets_v1)

    def __init__(self):
        modeltools.Model.__init__(self)
        self.nodenames = []

    def connect(self):
        """Connect the :class:`~hydpy.core.sequencetools.LinkSequence`
        instances handled by the actual model to the
        :class:`~hydpy.core.sequencetools.NodeSequence` instances
        handled by one inlet node and multiple oulet nodes.

        The HydPy-H-Branch model passes multiple output values to different
        outlet nodes.  This requires additional information regarding the
        `direction` of each output value.  Therefore, node names are used
        as keywords.  Assume, the discharge value of `n1` shall be branched
        to `n1a` and `n1b` via element `e1`:

        >>> from hydpy import *
        >>> n1, n1a, n1b = Node('n1'), Node('n1a'), Node('n1b')
        >>> e1 = Element('e1', inlets=n1, outlets=[n1a, n1b])

        Then parameter :class:`YPoints` relates different supporting
        points via its keyword arguments to the respective nodes:

        >>> from hydpy.models.hbranch import *
        >>> parameterstep()
        >>> xpoints(0., 3.)
        >>> ypoints(n1a=[0., 1.], n1b=[0., 2.])

        After doing some preparations which are normally handled by
        :ref:`HydPy` automatically ...

        >>> model.element = e1
        >>> model.parameters.update()
        >>> model.connect()

        ...you can see that an example discharge value handled by the
        :class:`~hydpy.core.devicetools.Node` instance `n1` is properly
        divided:

        >>> n1.sequences.sim = 6.
        >>> model.doit(0)
        >>> print(n1a.sequences.sim, n1b.sequences.sim)
        sim(2.0) sim(4.0)

        """
        nodes = self.element.inlets.slaves
        if len(nodes) == 1:
            double = nodes[0].getdouble_via_exits()
            self.sequences.inlets.total.setpointer(double)
        else:
            RuntimeError('The hbranch model must be connected to exactly one '
                         'inlet node, but its parent element `%s` references '
                         'currently %d inlet nodes.'
                         % (self.element.name, len(nodes)))
        for (idx, name) in enumerate(self.nodenames):
            try:
                double = self.element.outlets[name].getdouble_via_entries()
            except KeyError:
                if name in devicetools.Node.registerednames():
                    RuntimeError('The hbranch model tried to connect to the '
                                 'outlet node `%s`, but its parent element '
                                 '`%s` does not reference this node as an '
                                 'outlet node.' % (name, self.element.name))
                else:
                    RuntimeError('The hbranch model tried to connect to an '
                                 'outlet node named `%s`, which is not '
                                 'initialized yet.' % name)
            self.sequences.outlets.branched.setpointer(double, idx)


tester = Tester()
cythonizer = Cythonizer()
cythonizer.complete()
