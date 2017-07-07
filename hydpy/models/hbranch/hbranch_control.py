# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...from site-packages
import numpy
# ...HydPy specific
from hydpy import pub
from hydpy.core import parametertools
from hydpy.core import devicetools
from hydpy.core import objecttools


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
