# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import modeltools
from hydpy.core import devicetools


def calc_outputs_v1(self):
    """Performs the actual interpolation or extrapolation.

    Required control parameters:
      :class:`~hydpy.models.hbranch.XPoints`
      :class:`~hydpy.models.hbranch.YPoints`

    Required derived parameter:
      :class:`~hydpy.models.hbranch.hbranch_derived.NmbPoints`
      :class:`~hydpy.models.hbranch.hbranch_derived.NmbBranches`

    Required flux sequence:
      :class:`~hydpy.models.hbranch.hbranch_fluxes.Input`

    Calculated flux sequence:
      :class:`~hydpy.models.hbranch.hbranch_fluxes.Outputs`

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


def pick_input_v1(self):
    """Updates :class:`~hydpy.models.hbranch.Input` based on
    :class:`~hydpy.models.hbranch.Total`."""
    flu = self.sequences.fluxes.fastaccess
    inl = self.sequences.inlets.fastaccess
    flu.input = inl.total[0]


def pass_outputs_v1(self):
    """Updates :class:`~hydpy.models.hbranch.Branched` based on
    :class:`~hydpy.models.hbranch.Outputs`."""
    der = self.parameters.derived.fastaccess
    flu = self.sequences.fluxes.fastaccess
    out = self.sequences.outlets.fastaccess
    for bdx in range(der.nmbbranches):
        out.branched[bdx][0] += flu.outputs[bdx]


class Model(modeltools.Model):
    """The HydPy-H-Branch model.

    Additional attribute:
      * nodenames (:class:`list`): Names of the outlet node names, the
        actual model shall be connected to.
    """
    _INLET_METHODS = (pick_input_v1,)
    _RUN_METHODS = (calc_outputs_v1,)
    _OUTLET_METHODS = (pass_outputs_v1,)

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
