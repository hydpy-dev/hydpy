# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from site-packages
import numpy
# ...from HydPy
from hydpy import pub
from hydpy.core import devicetools
from hydpy.core import exceptiontools
from hydpy.core import objecttools
from hydpy.core import parametertools


class XPoints(parametertools.Parameter):
    """Supporting points for the independent input variable [eg. m³/s].

    There must be at least two supporting points, and they must be
    strictly monotonous.  If not, the following errors are raised:

    >>> from hydpy.models.hbranch import *
    >>> parameterstep()
    >>> xpoints(1.0, 2.0)
    >>> xpoints
    xpoints(1.0, 2.0)

    >>> xpoints(1.0)
    Traceback (most recent call last):
    ...
    ValueError: Branching via linear interpolation requires at least \
two supporting points, but parameter `xpoints` of element `?` \
received 1 value(s).

    >>> xpoints(1.0, 2.0, 2.0, 3.0)
    Traceback (most recent call last):
    ...
    ValueError: The values of parameter `xpoints` of element `?` must be \
arranged strictly monotonous, which is not the case for the given values \
`1.0, 2.0, 2.0, and 3.0`.
    """
    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)

    def __call__(self, *args, **kwargs):
        # pylint: disable=unsubscriptable-object
        # due to a pylint bug (see https://github.com/PyCQA/pylint/issues/870)
        self.shape = len(args)
        if self.shape[0] < 2:
            raise ValueError(
                f'Branching via linear interpolation requires '
                f'at least two supporting points, but '
                f'parameter {objecttools.elementphrase(self)} '
                f'received {self.shape[0]} value(s).')
        super().__call__(*args, **kwargs)
        if min(numpy.diff(self)) <= 0.:
            raise ValueError(
                f'The values of parameter {objecttools.elementphrase(self)} '
                f'must be arranged strictly monotonous, which is '
                f'not the case for the given values '
                f'`{objecttools.enumeration(self)}`.')


class YPoints(parametertools.Parameter):
    """Supporting points for the dependent output variables [eg. m³/s].

    Setting the values of parameter |YPoints| correctly requires consistency
    both with the values of parameter |XPoints| and the currently available
    |Node| objects.  Read two following error messages to see what can go
    wrong, and how to prepare parameter |YPoints| correctly.

    .. testsetup::

        >>> from hydpy import reverse_model_wildcard_import
        >>> reverse_model_wildcard_import()

    >>> from hydpy.models.hbranch import *
    >>> parameterstep('1d')
    >>> ypoints
    ypoints(?)

    Parameter |XPoints| must be prepared first:

    >>> ypoints(1.0, 2.0)
    Traceback (most recent call last):
    ...
    RuntimeError: The shape of parameter `ypoints` of element `?` depends \
on the shape of parameter `xpoints`, which has not been defined so far.

    >>> xpoints(1.0, 2.0, 3.0)

    The names of the |Node| objects the |hbranch| model is supposed to
    branch to must be supplied as keyword arguments:

    >>> ypoints(1.0, 2.0)
    Traceback (most recent call last):
    ...
    ValueError: For parameter `ypoints` of element `?` no branches are \
defined.  Do this via keyword arguments as explained in the documentation.

    The number of x and y supporting points must agree for all branches:

    >>> ypoints(branch1=[1.0, 2.0],
    ...         branch2=[2.0, 4.0])
    Traceback (most recent call last):
    ...
    ValueError: Each branch requires the same number of supporting points \
as given for parameter `xpoints`, which is 3, but for branch `branch1` of \
parameter `ypoints` of element `?` 2 values are given.

    >>> xpoints(1.0, 2.0)

    When working in an actual project (indicated by an predefined project
    name) each branch name must correspond to a |Node| name:

    >>> from hydpy import pub, Nodes
    >>> pub.projectname = 'test'
    >>> nodes = Nodes('branch1')
    >>> ypoints(branch1=[1.0, 2.0],
    ...         branch2=[2.0, 4.0])
    Traceback (most recent call last):
    ...
    RuntimeError: Parameter `ypoints` of element `?` is supposed to branch \
to node `branch2`, but such a node is not available.

    A general exception message for some unexpected errors:

    >>> nodes = Nodes('branch1', 'branch2')
    >>> ypoints(branch1=[1.0, 2.0],
    ...         branch2='xy')
    Traceback (most recent call last):
    ...
    ValueError: While trying to set the values for branch `branch2` of \
parameter `ypoints` of element `?`, the following error occurred: \
could not convert string to float: 'xy'

    Changing the number of branches during runtime might result in erroneous
    connections to the |Node| objects:

    >>> ypoints(branch1=[1.0, 2.0],
    ...         branch2=[2.0, 4.0])
    >>> ypoints
    ypoints(branch1=[1.0, 2.0],
            branch2=[2.0, 4.0])
    >>> ypoints(branch1=[1.0, 2.0])
    Traceback (most recent call last):
    ...
    RuntimeError: The number of branches of the hbranch model should not be \
changed during run time.  If you really need to do this, first initialize a \
new `branched` sequence and connect it to the respective outlet nodes properly.
    """
    NDIM, TYPE, TIME, SPAN = 2, float, None, (None, None)

    def __call__(self, *args, **kwargs):
        try:
            shape = (len(kwargs), self.subpars.xpoints.shape[0])
        except exceptiontools.AttributeNotReady:
            raise RuntimeError(
                f'The shape of parameter {objecttools.elementphrase(self)} '
                f'depends on the shape of parameter `xpoints`, which has '
                f'not been defined so far.'
            ) from None
        if shape[0] == 0:
            raise ValueError(
                f'For parameter {objecttools.elementphrase(self)} ' 
                f'no branches are defined.  Do this via keyword '
                f'arguments as explained in the documentation.'
            )
        branched = self.subpars.pars.model.sequences.outlets.branched
        if (branched.shape[0] != 0) and (branched.shape[0] != shape[0]):
            raise RuntimeError(
                'The number of branches of the hbranch model should not '
                'be changed during run time.  If you really need to do '
                'this, first initialize a new `branched` sequence and '
                'connect it to the respective outlet nodes properly.'
            )
        self.shape = shape
        self.values = numpy.nan
        for idx, (key, value) in enumerate(sorted(kwargs.items())):
            if key not in devicetools.Node.query_all():
                try:
                    pub.projectname
                except RuntimeError:
                    pass
                else:
                    raise RuntimeError(
                        f'Parameter {objecttools.elementphrase(self)} is '
                        f'supposed to branch to node `{key}`, but such a '
                        f'node is not available.'
                    )
            try:
                self.values[idx] = value
            except BaseException:
                if shape[1] != len(value):
                    raise ValueError(
                        f'Each branch requires the same number of supporting '
                        f'points as given for parameter `xpoints`, which is '
                        f'{shape[1]}, but for branch `{key}` of parameter '
                        f'{objecttools.elementphrase(self)} {len(value)} '
                        f'values are given.'
                    ) from None
                objecttools.augment_excmessage(
                    f'While trying to set the values for branch `{key}` '
                    f'of parameter {objecttools.elementphrase(self)}'
                )
        if branched.shape == (0,):
            branched.shape = shape[0]
        self.subpars.pars.model.sequences.fluxes.outputs.shape = shape[0]
        self.subpars.pars.model.nodenames.clear()
        for idx, key in enumerate(sorted(kwargs.keys())):
            setattr(self, key, self.values[idx])
            self.subpars.pars.model.nodenames.append(key)

    def __repr__(self):
        try:
            lines = self.commentrepr
            nodenames = self.subpars.pars.model.nodenames
            for (idx, values) in enumerate(self):
                line = '%s=%s,' % (nodenames[idx], repr(list(values)))
                if not idx:
                    lines.append('ypoints('+line)
                else:
                    lines.append('        '+line)
            lines[-1] = lines[-1][:-1]+')'
            return '\n'.join(lines)
        except BaseException:
            return 'ypoints(?)'
